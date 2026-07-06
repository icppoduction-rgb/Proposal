"""Stage Three preprocessing profile definitions."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


TREE_UNSCALED_PROFILE = "tree_unscaled"
STANDARD_SCALED_PROFILE = "standard_scaled"
ROBUST_SCALED_PROFILE = "robust_scaled"
MINMAX_SCALED_PROFILE = "minmax_scaled"
DL_SCALED_PROFILE = "dl_scaled"

SCALING_PROFILE_NAMES: tuple[str, ...] = (
    TREE_UNSCALED_PROFILE,
    STANDARD_SCALED_PROFILE,
    ROBUST_SCALED_PROFILE,
    MINMAX_SCALED_PROFILE,
    DL_SCALED_PROFILE,
)

DL_ALLOWED_SCALERS = frozenset({"standard", "minmax"})
TREE_MODEL_FAMILIES = ("random_forest", "xgboost")
DL_MODEL_FAMILIES = ("cnn", "lstm")


@dataclass(frozen=True)
class ScalingProfile:
    """Scaling policy for one preprocessing profile."""

    name: str
    default_scaler: str
    description: str
    model_families: tuple[str, ...]
    use_feature_policy: bool = False
    allowed_scalers: tuple[str, ...] = ("none", "standard", "robust", "minmax")
    output_dtype: str = "float32"

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON/report friendly profile description."""
        return asdict(self)


SCALING_PROFILES: dict[str, ScalingProfile] = {
    TREE_UNSCALED_PROFILE: ScalingProfile(
        name=TREE_UNSCALED_PROFILE,
        default_scaler="none",
        description="No numeric scaling for tree baselines that do not require feature scaling.",
        model_families=TREE_MODEL_FAMILIES,
        allowed_scalers=("none",),
    ),
    STANDARD_SCALED_PROFILE: ScalingProfile(
        name=STANDARD_SCALED_PROFILE,
        default_scaler="standard",
        description="Mean/std scaling for models that benefit from centered numeric features.",
        model_families=("linear", "svm", "mlp", "cnn", "lstm"),
        allowed_scalers=("standard",),
    ),
    ROBUST_SCALED_PROFILE: ScalingProfile(
        name=ROBUST_SCALED_PROFILE,
        default_scaler="robust",
        description="Median/IQR scaling for outlier-heavy numeric features.",
        model_families=("linear", "svm", "mlp"),
        allowed_scalers=("robust",),
    ),
    MINMAX_SCALED_PROFILE: ScalingProfile(
        name=MINMAX_SCALED_PROFILE,
        default_scaler="minmax",
        description="Min/max scaling to the [0, 1] range.",
        model_families=("cnn", "lstm", "mlp"),
        allowed_scalers=("minmax",),
    ),
    DL_SCALED_PROFILE: ScalingProfile(
        name=DL_SCALED_PROFILE,
        default_scaler="standard",
        description=(
            "Deep-learning profile. Numeric features use their feature-catalog policy "
            "when it is standard/minmax; other scalable numeric features fall back to standard."
        ),
        model_families=DL_MODEL_FAMILIES,
        use_feature_policy=True,
        allowed_scalers=tuple(sorted(DL_ALLOWED_SCALERS)),
    ),
}


def get_scaling_profile(name: str) -> ScalingProfile:
    """Return a known scaling profile or raise a clear ValueError."""
    normalized = name.strip()
    try:
        return SCALING_PROFILES[normalized]
    except KeyError as exc:
        allowed = ", ".join(SCALING_PROFILE_NAMES)
        raise ValueError(f"unsupported scaling profile={name!r}; allowed values: {allowed}") from exc


def resolve_scaler_for_feature(
    profile_name: str,
    *,
    feature_policy: str | None,
    is_numeric: bool,
) -> str:
    """Resolve the scaler strategy for one feature under a profile."""
    profile = get_scaling_profile(profile_name)
    if not is_numeric or profile.default_scaler == "none":
        return "none"
    if not profile.use_feature_policy:
        return profile.default_scaler
    policy = (feature_policy or "none").strip().lower() or "none"
    if policy in DL_ALLOWED_SCALERS:
        return policy
    if policy == "none":
        return "none"
    return profile.default_scaler
