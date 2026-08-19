from __future__ import annotations

from typing import Any, Iterable


class Phase8ContractError(ValueError):
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
        raise Phase8ContractError(
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
        raise Phase8ContractError(
            error_category="invalid_value",
            safe_message=f"{field_name} must be one of: {allowed}.",
        )


def ensure_positive_int(field_name: str, value: int) -> None:
    if not isinstance(value, int) or value <= 0:
        raise Phase8ContractError(
            error_category="invalid_value",
            safe_message=f"{field_name} must be a positive integer.",
        )


def ensure_non_negative_int(field_name: str, value: int) -> None:
    if not isinstance(value, int) or value < 0:
        raise Phase8ContractError(
            error_category="invalid_value",
            safe_message=f"{field_name} must be a non-negative integer.",
        )


def ensure_bool(field_name: str, value: bool) -> None:
    if not isinstance(value, bool):
        raise Phase8ContractError(
            error_category="invalid_value",
            safe_message=f"{field_name} must be a boolean.",
        )


def ensure_tuple_of_non_empty_text(field_name: str, values: tuple[str, ...]) -> None:
    if not isinstance(values, tuple):
        raise Phase8ContractError(
            error_category="invalid_value",
            safe_message=f"{field_name} must be a tuple of non-empty strings.",
        )
    for index, value in enumerate(values):
        ensure_non_empty_text(f"{field_name}[{index}]", value)


def ensure_tuple_of_positive_ints(field_name: str, values: tuple[int, ...]) -> None:
    if not isinstance(values, tuple):
        raise Phase8ContractError(
            error_category="invalid_value",
            safe_message=f"{field_name} must be a tuple of positive integers.",
        )
    for index, value in enumerate(values):
        ensure_positive_int(f"{field_name}[{index}]", value)


def ensure_optional_positive_int(field_name: str, value: int | None) -> None:
    if value is None:
        return
    ensure_positive_int(field_name, value)


def ensure_optional_non_negative_int(field_name: str, value: int | None) -> None:
    if value is None:
        return
    ensure_non_negative_int(field_name, value)


def ensure_at_least_one_present(field_name: str, values: Iterable[object]) -> None:
    if not any(value is not None for value in values):
        raise Phase8ContractError(
            error_category="missing_value",
            safe_message=f"{field_name} must include at least one non-null reference.",
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
                raise Phase8ContractError(
                    error_category="invalid_value",
                    safe_message=f"{field_name} must use non-empty string keys.",
                )
            ensure_json_compatible(f"{field_name}.{key}", item)
        return
    raise Phase8ContractError(
        error_category="invalid_value",
        safe_message=f"{field_name} must contain only JSON-compatible primitives, arrays, or objects.",
    )
