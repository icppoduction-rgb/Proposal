from __future__ import annotations

from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.services.dataset_uploads import DatasetUploadError, get_raw_root
from cybersec_platform.contracts.api import DatasetManifest, FeatureFamily, NormalizationProfile, SourceType
from cybersec_platform.db import Dataset, ManagedDataset, RawFile
from cybersec_platform.ml.normalization import inspect_dataset_source

NETWORK_FEATURE_FAMILIES = {
    FeatureFamily.NETWORK_FLOW.value,
    FeatureFamily.DNS.value,
    FeatureFamily.SEQUENCE.value,
}

HOST_FEATURE_FAMILIES = {
    FeatureFamily.FILE_SYSTEM.value,
    FeatureFamily.PROCESS.value,
    FeatureFamily.PRIVILEGE.value,
    FeatureFamily.USER_ACTIVITY.value,
}

NETWORK_NORMALIZATION_PROFILES = {
    NormalizationProfile.DNS2021_TABULAR_FEATURES.value,
    NormalizationProfile.DNS2021_DOMAIN_LISTS.value,
    NormalizationProfile.DNS_EXF_STATEFUL.value,
    NormalizationProfile.DNS_EXF_STATELESS.value,
    NormalizationProfile.DNS_PCAP_DNS_FLOW.value,
}


def ensure_registered_raw_file_is_available(raw_file: RawFile) -> str:
    target = Path(raw_file.path).resolve()
    raw_root = get_raw_root().resolve()
    if not target.is_relative_to(raw_root):
        raise DatasetUploadError("Raw file is outside of the raw data root", status_code=400)
    if not target.exists() or not target.is_file():
        raise DatasetUploadError("Selected raw file does not exist", status_code=409)
    return str(target)


async def list_managed_datasets(session: AsyncSession) -> list[ManagedDataset]:
    result = await session.execute(select(ManagedDataset).order_by(ManagedDataset.created_at.desc(), ManagedDataset.id.desc()))
    return result.scalars().all()


async def get_managed_dataset(session: AsyncSession, dataset_id: str) -> ManagedDataset | None:
    return await session.get(ManagedDataset, dataset_id)


async def get_linked_dataset_for_managed_dataset(session: AsyncSession, dataset: ManagedDataset) -> Dataset | None:
    result = await session.execute(
        select(Dataset)
        .where(Dataset.name == dataset.name, Dataset.storage_path == dataset.file_path)
        .order_by(Dataset.created_at.desc(), Dataset.id.desc())
    )
    return result.scalars().first()


async def get_managed_dataset_by_name(session: AsyncSession, name: str) -> ManagedDataset | None:
    result = await session.execute(select(ManagedDataset).where(func.lower(ManagedDataset.name) == name.strip().lower()))
    return result.scalar_one_or_none()


async def count_managed_datasets_for_raw_file(session: AsyncSession, raw_file_id: str) -> int:
    result = await session.execute(select(func.count()).select_from(ManagedDataset).where(ManagedDataset.raw_file_id == raw_file_id))
    return int(result.scalar_one())


async def has_managed_datasets(session: AsyncSession) -> bool:
    result = await session.execute(select(ManagedDataset.id).limit(1))
    return result.scalar_one_or_none() is not None


async def referenced_raw_file_ids(session: AsyncSession) -> set[str]:
    result = await session.execute(select(ManagedDataset.raw_file_id))
    return {item for item in result.scalars().all()}


async def delete_managed_dataset(session: AsyncSession, dataset: ManagedDataset) -> None:
    await session.delete(dataset)


async def delete_all_managed_datasets(session: AsyncSession) -> int:
    datasets = await list_managed_datasets(session)
    deleted_count = len(datasets)
    for dataset in datasets:
        await session.delete(dataset)
    return deleted_count


def _infer_source_type(feature_set: list[str], normalization_profile: str) -> SourceType:
    if normalization_profile in NETWORK_NORMALIZATION_PROFILES:
        return SourceType.NETWORK

    normalized_feature_set = set(feature_set)
    if normalized_feature_set & NETWORK_FEATURE_FAMILIES:
        return SourceType.NETWORK
    if normalized_feature_set & HOST_FEATURE_FAMILIES:
        return SourceType.HOST
    return SourceType.HOST


def _coerce_feature_families(feature_set: list[str], source_type: SourceType) -> list[FeatureFamily]:
    normalized: list[FeatureFamily] = []
    seen: set[FeatureFamily] = set()
    for item in feature_set:
        try:
            family = FeatureFamily(item)
        except ValueError:
            continue
        if family in seen:
            continue
        normalized.append(family)
        seen.add(family)

    if normalized:
        return normalized
    if source_type == SourceType.NETWORK:
        return [FeatureFamily.NETWORK_FLOW]
    return [FeatureFamily.PROCESS]


def build_managed_dataset_manifest(dataset: ManagedDataset) -> DatasetManifest:
    inspection = inspect_dataset_source(dataset.file_path)
    source_type = _infer_source_type(dataset.feature_set, inspection.normalization_profile)
    feature_families = _coerce_feature_families(dataset.feature_set, source_type)
    required_columns = inspection.columns or inspection.target_columns or ["entity_id"]

    return DatasetManifest(
        name=dataset.name,
        source_type=source_type,
        description="Managed dataset registry record",
        file_name=Path(dataset.file_path).name,
        required_columns=required_columns,
        label_column="label",
        timestamp_column="event_ts",
        entity_id_column="entity_id",
        attack_stage_column="attack_stage",
        feature_families=feature_families,
        mitre_mapping={},
        lineage={
            "source": "managed_dataset",
            "managed_dataset_id": dataset.id,
            "raw_file_id": dataset.raw_file_id,
        },
    )


async def ensure_legacy_dataset_for_managed_dataset(session: AsyncSession, managed_dataset: ManagedDataset) -> Dataset:
    target = Path(managed_dataset.file_path).resolve()
    raw_root = get_raw_root().resolve()
    if not target.is_relative_to(raw_root):
        raise DatasetUploadError("Raw file is outside of the raw data root", status_code=400)
    if not target.exists() or not target.is_file():
        raise DatasetUploadError("Selected raw file does not exist", status_code=409)
    manifest = build_managed_dataset_manifest(managed_dataset)
    dataset = await get_linked_dataset_for_managed_dataset(session, managed_dataset)

    if dataset is None:
        dataset = Dataset(
            name=manifest.name,
            source_type=manifest.source_type.value,
            description=manifest.description,
            manifest=manifest.model_dump(mode="json"),
            storage_path=managed_dataset.file_path,
            lineage=manifest.lineage,
        )
        session.add(dataset)
        await session.flush()
        return dataset

    dataset.name = manifest.name
    dataset.source_type = manifest.source_type.value
    dataset.description = manifest.description
    dataset.manifest = manifest.model_dump(mode="json")
    dataset.storage_path = managed_dataset.file_path
    dataset.lineage = manifest.lineage
    await session.flush()
    return dataset
