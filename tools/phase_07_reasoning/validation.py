from __future__ import annotations

from typing import Any


class Phase7ContractError(ValueError):
    def __init__(self, *, error_category: str, safe_message: str) -> None:
        self.error_category = error_category
        self.safe_message = safe_message
        super().__init__(safe_message)

    def to_dict(self) -> dict[str, str]:
        return {
            "error_category": self.error_category,
            "message": self.safe_message,
        }


def ensure_non_empty_text(field_name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise Phase7ContractError(
            error_category="invalid_field",
            safe_message=f"{field_name} must be a non-empty string.",
        )


def ensure_optional_non_empty_text(field_name: str, value: str | None) -> None:
    if value is None:
        return
    ensure_non_empty_text(field_name, value)


def ensure_allowed_value(field_name: str, value: str, allowed_values: set[str] | frozenset[str]) -> None:
    if value not in allowed_values:
        allowed = ", ".join(sorted(allowed_values))
        raise Phase7ContractError(
            error_category="invalid_value",
            safe_message=f"{field_name} must be one of: {allowed}.",
        )


def ensure_unique_strings(field_name: str, values: tuple[str, ...]) -> None:
    if len(values) != len(set(values)):
        raise Phase7ContractError(
            error_category="duplicate_value",
            safe_message=f"{field_name} must not contain duplicate values.",
        )


def ensure_positive_int(field_name: str, value: int) -> None:
    if not isinstance(value, int) or value <= 0:
        raise Phase7ContractError(
            error_category="invalid_value",
            safe_message=f"{field_name} must be a positive integer.",
        )


def ensure_non_negative_int(field_name: str, value: int) -> None:
    if not isinstance(value, int) or value < 0:
        raise Phase7ContractError(
            error_category="invalid_value",
            safe_message=f"{field_name} must be a non-negative integer.",
        )


def ensure_bool(field_name: str, value: bool) -> None:
    if not isinstance(value, bool):
        raise Phase7ContractError(
            error_category="invalid_value",
            safe_message=f"{field_name} must be a boolean.",
        )


def ensure_json_compatible(field_name: str, value: Any) -> None:
    if value is None:
        return
    if isinstance(value, (str, int, float, bool)):
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            ensure_json_compatible(f"{field_name}[{index}]", item)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str) or not key:
                raise Phase7ContractError(
                    error_category="invalid_value",
                    safe_message=f"{field_name} must use non-empty string keys.",
                )
            ensure_json_compatible(f"{field_name}.{key}", item)
        return
    raise Phase7ContractError(
        error_category="invalid_value",
        safe_message=f"{field_name} must contain only JSON-compatible primitives, arrays, or objects.",
    )
