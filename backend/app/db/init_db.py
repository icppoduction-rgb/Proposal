from __future__ import annotations

from sqlalchemy import inspect, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.security import get_password_hash
from cybersec_platform.contracts.api import FeatureFamily, RoleName, SourceType
from cybersec_platform.db import Base, FeatureSchema, Role, User, get_engine
from cybersec_platform.db.session import ensure_database_exists, get_settings


async def init_db() -> None:
    ensure_database_exists()
    engine = get_engine()
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
        await connection.run_sync(_ensure_runtime_columns)


def _ensure_runtime_columns(connection) -> None:
    inspector = inspect(connection)
    existing_columns = {column["name"] for column in inspector.get_columns("datasets")}
    statements = {
        "detected_format": "ALTER TABLE datasets ADD COLUMN detected_format VARCHAR(32)",
        "normalization_profile": "ALTER TABLE datasets ADD COLUMN normalization_profile VARCHAR(64)",
        "normalization_summary": "ALTER TABLE datasets ADD COLUMN normalization_summary JSON",
        "normalization_report_path": "ALTER TABLE datasets ADD COLUMN normalization_report_path VARCHAR(500)",
    }
    for column_name, statement in statements.items():
        if column_name in existing_columns:
            continue
        connection.exec_driver_sql(statement)
    if "normalization_summary" not in existing_columns:
        connection.exec_driver_sql("UPDATE datasets SET normalization_summary = '{}' WHERE normalization_summary IS NULL")


async def seed_defaults(session: AsyncSession) -> None:
    settings = get_settings()
    roles = {}
    for role_name in (RoleName.ADMIN.value, RoleName.ANALYST.value):
        roles[role_name] = await _get_or_create_role(session, role_name)

    result = await session.execute(select(User).where(User.email == settings.default_admin_email))
    user = result.scalar_one_or_none()
    if user is None:
        session.add(
            User(
                email=settings.default_admin_email,
                password_hash=get_password_hash(settings.default_admin_password),
                full_name="Platform Administrator",
                role_id=roles[RoleName.ADMIN.value].id,
            )
        )

    defaults = [
        {
            "name": "dns-network-stateful",
            "version": "1.0.0",
            "source_type": SourceType.NETWORK.value,
            "definition": {
                "name": "dns-network-stateful",
                "version": "1.0.0",
                "source_type": SourceType.NETWORK.value,
                "required_columns": [
                    "a_frequency",
                    "ns_frequency",
                    "cname_frequency",
                    "rr_count",
                    "rr_name_entropy",
                    "rr_name_length",
                    "distinct_ns",
                    "distinct_ip",
                    "distinct_domains",
                    "a_records",
                    "ttl_mean",
                    "ttl_variance",
                ],
                "canonical_mappings": {
                    "event_ts": "event_ts",
                    "entity_id": "entity_id",
                    "rr_name_entropy": "dns_query_entropy",
                },
                "feature_families": [FeatureFamily.NETWORK_FLOW.value, FeatureFamily.DNS.value],
                "mitre_tactics": {"rr_name_entropy": "TA0011", "distinct_domains": "TA0011"},
            },
        },
        {
            "name": "dns-network-stateless",
            "version": "1.0.0",
            "source_type": SourceType.NETWORK.value,
            "definition": {
                "name": "dns-network-stateless",
                "version": "1.0.0",
                "source_type": SourceType.NETWORK.value,
                "required_columns": [
                    "fqdn_count",
                    "subdomain_length",
                    "upper",
                    "lower",
                    "numeric",
                    "entropy",
                    "special",
                    "labels",
                    "labels_max",
                    "labels_average",
                    "longest_word",
                    "len",
                    "subdomain",
                ],
                "canonical_mappings": {"timestamp": "event_ts", "entropy": "dns_query_entropy"},
                "feature_families": [FeatureFamily.NETWORK_FLOW.value, FeatureFamily.DNS.value],
                "mitre_tactics": {"entropy": "TA0011", "fqdn_count": "TA0011"},
            },
        },
        {
            "name": "dns-domain-tabular",
            "version": "1.0.0",
            "source_type": SourceType.NETWORK.value,
            "definition": {
                "name": "dns-domain-tabular",
                "version": "1.0.0",
                "source_type": SourceType.NETWORK.value,
                "required_columns": [
                    "ttl",
                    "asn",
                    "entropy",
                    "len",
                    "longest_word",
                    "numeric_percentage",
                    "page_rank",
                    "name_server_count",
                ],
                "canonical_mappings": {"domain": "entity_id", "creation_date_time": "event_ts"},
                "feature_families": [FeatureFamily.DNS.value, FeatureFamily.NETWORK_FLOW.value],
                "mitre_tactics": {"entropy": "TA0011", "numeric_percentage": "TA0011"},
            },
        },
        {
            "name": "dns-pcap-flow",
            "version": "1.0.0",
            "source_type": SourceType.NETWORK.value,
            "definition": {
                "name": "dns-pcap-flow",
                "version": "1.0.0",
                "source_type": SourceType.NETWORK.value,
                "required_columns": [
                    "packet_count",
                    "byte_total",
                    "mean_packet_size",
                    "mean_inter_arrival_ms",
                    "dns_query_entropy_mean",
                    "communication_frequency",
                    "query_rr_count",
                    "answer_rr_count",
                    "unique_qnames",
                    "ttl_mean",
                    "ttl_max",
                ],
                "canonical_mappings": {"event_ts": "event_ts", "entity_id": "entity_id"},
                "feature_families": [FeatureFamily.DNS.value, FeatureFamily.NETWORK_FLOW.value, FeatureFamily.SEQUENCE.value],
                "mitre_tactics": {"dns_query_entropy_mean": "TA0011", "communication_frequency": "TA0011"},
            },
        },
        {
            "name": "dns-domain-intel",
            "version": "1.0.0",
            "source_type": SourceType.NETWORK.value,
            "definition": {
                "name": "dns-domain-intel",
                "version": "1.0.0",
                "source_type": SourceType.NETWORK.value,
                "required_columns": [
                    "domain_length",
                    "numeric_ratio",
                    "subdomain_depth",
                    "domain_entropy",
                    "hyphen_count",
                ],
                "canonical_mappings": {"domain": "entity_id"},
                "feature_families": [FeatureFamily.DNS.value],
                "mitre_tactics": {"domain_entropy": "TA0011"},
            },
        },
        {
            "name": "host-simulated",
            "version": "1.0.0",
            "source_type": SourceType.HOST.value,
            "definition": {
                "name": "host-simulated",
                "version": "1.0.0",
                "source_type": SourceType.HOST.value,
                "required_columns": ["process_exec_count", "file_access_entropy", "privilege_usage_score"],
                "canonical_mappings": {"event_ts": "event_ts", "entity_id": "entity_id"},
                "feature_families": [FeatureFamily.PROCESS.value, FeatureFamily.FILE_SYSTEM.value, FeatureFamily.PRIVILEGE.value],
                "mitre_tactics": {"process_exec_count": "TA0002", "privilege_usage_score": "TA0004"},
            },
        },
    ]
    for schema_payload in defaults:
        existing = await session.execute(
            select(FeatureSchema).where(
                FeatureSchema.name == schema_payload["name"],
                FeatureSchema.version == schema_payload["version"],
            )
        )
        if existing.scalar_one_or_none() is None:
            session.add(
                FeatureSchema(
                    name=schema_payload["name"],
                    version=schema_payload["version"],
                    source_type=schema_payload["source_type"],
                    definition=schema_payload["definition"],
                )
            )
    await session.commit()


async def _get_or_create_role(session: AsyncSession, role_name: str) -> Role:
    result = await session.execute(select(Role).where(Role.name == role_name))
    role = result.scalar_one_or_none()
    if role is not None:
        return role

    nested = await session.begin_nested()
    try:
        role = Role(name=role_name)
        session.add(role)
        await session.flush()
        await nested.commit()
        return role
    except IntegrityError:
        await nested.rollback()
        result = await session.execute(select(Role).where(Role.name == role_name))
        role = result.scalar_one_or_none()
        if role is None:
            raise
        return role
