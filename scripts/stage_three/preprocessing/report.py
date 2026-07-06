"""Markdown reports for Task12 type casting and schema normalization."""

from __future__ import annotations

import json
from dataclasses import replace
from typing import Any

from scripts.stage_three.preprocessing.fit_transform import PreprocessingTransformResult
from scripts.stage_three.preprocessing.scaling import (
    PreprocessingArtifactRegistrationSummary,
    ScalingTransformResult,
    available_scaling_profiles,
)
from scripts.stage_three.preprocessing.type_casting import TypeCastingResult
from scripts.stage_three.reports.path_utils import build_stage_three_task_report_paths


TASK12_REPORT_FILENAME = "Task12-type-casting-and-schema-normalization.md"
PREVIOUS_REPORT_PATH = "Task11-xy-metadata-traceability-separation.md"
TASK13_REPORT_FILENAME = "Task13-missing-values-and-categorical-encoding.md"
TASK13_PREVIOUS_REPORT_PATH = "Task12-type-casting-and-schema-normalization.md"
TASK14_REPORT_FILENAME = "Task14-scaling-profiles-and-preprocessing-artifacts.md"
TASK14_PREVIOUS_REPORT_PATH = "Task13-missing-values-and-categorical-encoding.md"


def save_type_casting_reports(result: TypeCastingResult) -> TypeCastingResult:
    """Write RU and EN Task12 reports and return the result with report paths."""
    paths = build_stage_three_task_report_paths(TASK12_REPORT_FILENAME, create_dirs=True)
    report_paths = {"ru": str(paths.ru), "en": str(paths.en)}
    payload = {**result.to_dict(), "report_paths": report_paths}
    paths.ru.write_text(_render_ru(payload), encoding="utf-8")
    paths.en.write_text(_render_en(payload), encoding="utf-8")
    return replace(result, report_paths=report_paths)


def save_missing_encoding_reports(result: PreprocessingTransformResult) -> PreprocessingTransformResult:
    """Write RU and EN Task13 reports and return the result with report paths."""
    paths = build_stage_three_task_report_paths(TASK13_REPORT_FILENAME, create_dirs=True)
    report_paths = {"ru": str(paths.ru), "en": str(paths.en)}
    payload = {**result.to_dict(), "report_paths": report_paths}
    paths.ru.write_text(_render_task13(payload), encoding="utf-8")
    paths.en.write_text(_render_task13(payload), encoding="utf-8")
    return replace(result, report_paths=report_paths)


def save_scaling_profile_reports(
    result: ScalingTransformResult,
    *,
    registration_summary: PreprocessingArtifactRegistrationSummary | None = None,
) -> ScalingTransformResult:
    """Write RU and EN Task14 reports and return the result with report paths."""
    paths = build_stage_three_task_report_paths(TASK14_REPORT_FILENAME, create_dirs=True)
    report_paths = {"ru": str(paths.ru), "en": str(paths.en)}
    payload = {
        **result.to_dict(),
        "report_paths": report_paths,
        "registration_summary": registration_summary.to_dict()
        if registration_summary is not None
        else {
            "preprocessing_artifact_ids": [],
            "artifact_path": result.artifact.metadata.get("artifact_path", ""),
            "fitted_on_role": result.artifact.fit_role,
            "profile_name": result.artifact.profile_name,
            "feature_count": result.feature_count,
        },
        "available_profiles": available_scaling_profiles(),
        "feature_count_by_profile": result.artifact.metadata.get("feature_count_by_profile", {}),
    }
    paths.ru.write_text(_render_task14_ru(payload), encoding="utf-8")
    paths.en.write_text(_render_task14_en(payload), encoding="utf-8")
    return replace(result, report_paths=report_paths)


def _render_ru(payload: dict[str, Any]) -> str:
    return (
        "# Task 12 - type-casting-and-schema-normalization\n\n"
        f"- Previous report path: `{PREVIOUS_REPORT_PATH}`\n"
        f"- Status: `{payload['status']}`\n"
        f"- Rows normalized: `{payload['row_count']}`\n"
        f"- Memory before: `{payload['memory_before_bytes']}` bytes\n"
        f"- Memory after: `{payload['memory_after_bytes']}` bytes\n\n"
        "## Dtype Conversions\n\n"
        f"{_conversions(payload)}\n\n"
        "## Rejected Columns\n\n"
        f"{_rejected(payload)}\n\n"
        "## Schema Warnings\n\n"
        f"{_warnings(payload)}\n\n"
        "## Schema Metadata\n\n"
        f"```json\n{_json(payload['schema_metadata'])}\n```\n\n"
        "## Machine-readable Details\n\n"
        f"```json\n{_json(_compact_payload(payload))}\n```\n"
    )


def _render_en(payload: dict[str, Any]) -> str:
    return (
        "# Task 12 - type-casting-and-schema-normalization\n\n"
        f"- Previous report path: `{PREVIOUS_REPORT_PATH}`\n"
        f"- Status: `{payload['status']}`\n"
        f"- Rows normalized: `{payload['row_count']}`\n"
        f"- Memory before: `{payload['memory_before_bytes']}` bytes\n"
        f"- Memory after: `{payload['memory_after_bytes']}` bytes\n\n"
        "## Dtype Conversions\n\n"
        f"{_conversions(payload)}\n\n"
        "## Rejected Columns\n\n"
        f"{_rejected(payload)}\n\n"
        "## Schema Warnings\n\n"
        f"{_warnings(payload)}\n\n"
        "## Schema Metadata\n\n"
        f"```json\n{_json(payload['schema_metadata'])}\n```\n\n"
        "## Machine-readable Details\n\n"
        f"```json\n{_json(_compact_payload(payload))}\n```\n"
    )


def _render_task13(payload: dict[str, Any]) -> str:
    imputer = payload["imputer"]
    encoder = payload["encoder"]
    return (
        "# Task 13 - missing-values-and-categorical-encoding\n\n"
        f"- Previous report path: `{TASK13_PREVIOUS_REPORT_PATH}`\n"
        f"- Fit role: `{payload['fit_role']}`\n"
        f"- Transform role: `{payload['split_role']}`\n"
        f"- Rows transformed: `{payload['row_count']}`\n\n"
        "## Imputer Strategies\n\n"
        f"{_imputer_strategies(imputer)}\n\n"
        "## Encoder Strategies\n\n"
        f"{_encoder_strategies(encoder)}\n\n"
        "## Unknown Category Handling\n\n"
        f"- {encoder['unknown_category_handling']}\n"
        f"- Unknown counts: `{_json(encoder['unknown_counts'])}`\n\n"
        "## Missing Ratios Before/After\n\n"
        f"{_missing_ratios(imputer)}\n\n"
        "## Preprocessing Metadata\n\n"
        f"```json\n{_json(payload['preprocessing_metadata'])}\n```\n\n"
        "## Machine-readable Details\n\n"
        f"```json\n{_json(_compact_task13_payload(payload))}\n```\n"
    )


def _render_task14_ru(payload: dict[str, Any]) -> str:
    summary = payload["registration_summary"]
    return (
        "# Task 14 - scaling-profiles-and-preprocessing-artifacts\n\n"
        f"- Previous report path: `{TASK14_PREVIOUS_REPORT_PATH}`\n"
        f"- Fit role: `{payload['fit_role']}`\n"
        f"- Transform role: `{payload['split_role']}`\n"
        f"- Active scaling profile: `{payload['profile_name']}`\n"
        f"- Scaler statistics location: `{payload['scaler_statistics_location']}`\n"
        f"- Preprocessing artifact IDs: `{_json(summary['preprocessing_artifact_ids'])}`\n\n"
        "## Scaling profiles created\n\n"
        f"{_scaling_profiles(payload['available_profiles'])}\n\n"
        "## Feature count per profile\n\n"
        f"{_feature_count_per_profile(payload)}\n\n"
        "## Scaler columns\n\n"
        f"{_scaler_columns(payload)}\n\n"
        "## Preprocessing artifact registration\n\n"
        f"```json\n{_json(summary)}\n```\n\n"
        "## Machine-readable details\n\n"
        f"```json\n{_json(_compact_task14_payload(payload))}\n```\n"
    )


def _render_task14_en(payload: dict[str, Any]) -> str:
    summary = payload["registration_summary"]
    return (
        "# Task 14 - scaling-profiles-and-preprocessing-artifacts\n\n"
        f"- Previous report path: `{TASK14_PREVIOUS_REPORT_PATH}`\n"
        f"- Fit role: `{payload['fit_role']}`\n"
        f"- Transform role: `{payload['split_role']}`\n"
        f"- Active scaling profile: `{payload['profile_name']}`\n"
        f"- Scaler statistics location: `{payload['scaler_statistics_location']}`\n"
        f"- Preprocessing artifact IDs: `{_json(summary['preprocessing_artifact_ids'])}`\n\n"
        "## Scaling Profiles Created\n\n"
        f"{_scaling_profiles(payload['available_profiles'])}\n\n"
        "## Feature Count Per Profile\n\n"
        f"{_feature_count_per_profile(payload)}\n\n"
        "## Scaler Columns\n\n"
        f"{_scaler_columns(payload)}\n\n"
        "## Preprocessing Artifact Registration\n\n"
        f"```json\n{_json(summary)}\n```\n\n"
        "## Machine-readable Details\n\n"
        f"```json\n{_json(_compact_task14_payload(payload))}\n```\n"
    )


def _conversions(payload: dict[str, Any]) -> str:
    conversions = payload.get("dtype_conversions", [])
    if not conversions:
        return "- `none`"
    return "\n".join(
        "- `{column}`: `{catalog_dtype}` -> `{output_dtype}`; action=`{action}`; memory `{before}` -> `{after}` bytes".format(
            column=item["column"],
            catalog_dtype=item["catalog_dtype"],
            output_dtype=item["output_dtype"],
            action=item["action"],
            before=item["memory_before_bytes"],
            after=item["memory_after_bytes"],
        )
        for item in conversions
    )


def _rejected(payload: dict[str, Any]) -> str:
    rejected = payload.get("rejected_columns", [])
    if not rejected:
        return "- `none`"
    return "\n".join(
        f"- `{item['column']}`: {item['reason']} (catalog_dtype=`{item.get('catalog_dtype')}`)"
        for item in rejected
    )


def _warnings(payload: dict[str, Any]) -> str:
    warnings = payload.get("schema_warnings", [])
    if not warnings:
        return "- `none`"
    return "\n".join(f"- `{item['column']}`: {item['message']}" for item in warnings)


def _compact_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in payload.items()
        if key
        in {
            "status",
            "row_count",
            "typed_columns",
            "dtype_conversions",
            "rejected_columns",
            "schema_warnings",
            "memory_before_bytes",
            "memory_after_bytes",
            "schema_metadata",
            "report_paths",
        }
    }


def _imputer_strategies(imputer: dict[str, Any]) -> str:
    strategies = imputer.get("imputer_strategies", {})
    if not strategies:
        return "- `none`"
    return "\n".join(
        f"- `{column}`: strategy=`{state['strategy']}`, fill=`{state['fill_value']}`, indicator=`{state['add_indicator']}`"
        for column, state in strategies.items()
    )


def _encoder_strategies(encoder: dict[str, Any]) -> str:
    strategies = encoder.get("encoder_strategies", {})
    if not strategies:
        return "- `none`"
    lines = [
        f"- `{column}`: requested=`{state['requested_strategy']}`, applied=`{state['strategy']}`, categories=`{state['category_count']}`"
        for column, state in strategies.items()
    ]
    rejected = encoder.get("rejected_columns", {})
    for column, reason in rejected.items():
        lines.append(f"- `{column}`: rejected, {reason}")
    return "\n".join(lines)


def _missing_ratios(imputer: dict[str, Any]) -> str:
    before = imputer.get("missing_ratios_before", {})
    after = imputer.get("missing_ratios_after", {})
    if not before:
        return "- `none`"
    return "\n".join(
        f"- `{column}`: `{before[column]}` -> `{after.get(column, 0.0)}`"
        for column in before
    )


def _compact_task13_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in payload.items()
        if key
        in {
            "split_role",
            "fit_role",
            "row_count",
            "imputer",
            "encoder",
            "report_paths",
        }
    }


def _scaling_profiles(profiles: dict[str, Any]) -> str:
    if not profiles:
        return "- `none`"
    return "\n".join(
        "- `{name}`: default_scaler=`{default}`, models=`{models}`".format(
            name=name,
            default=profile["default_scaler"],
            models=", ".join(profile["model_families"]),
        )
        for name, profile in profiles.items()
    )


def _feature_count_per_profile(payload: dict[str, Any]) -> str:
    counts = payload.get("feature_count_by_profile") or {}
    if counts:
        return "\n".join(f"- `{profile_name}`: `{counts.get(profile_name, 0)}`" for profile_name in payload["available_profiles"])
    active_profile = payload["profile_name"]
    active_count = payload["feature_count"]
    lines = []
    for profile_name in payload["available_profiles"]:
        count = active_count if profile_name == active_profile else "available"
        lines.append(f"- `{profile_name}`: `{count}`")
    return "\n".join(lines)


def _scaler_columns(payload: dict[str, Any]) -> str:
    columns = payload["scaler"].get("columns", {})
    if not columns:
        return "- `none`"
    return "\n".join(
        f"- `{column}`: strategy=`{state['strategy']}`, center=`{state['center']}`, scale=`{state['scale']}`"
        for column, state in columns.items()
    )


def _compact_task14_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in payload.items()
        if key
        in {
            "split_role",
            "fit_role",
            "profile_name",
            "row_count",
            "feature_count",
            "scaled_columns",
            "scaler_statistics_location",
            "registration_summary",
            "feature_count_by_profile",
            "report_paths",
        }
    }


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True)
