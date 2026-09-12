from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Protocol

from tools.runtime_environment import AppRuntimeConfig

from .asana_adapter import AsanaActionInputError, AsanaExecutionAdapter, _resolve_project_gid
from .contracts import EXECUTION_ATTEMPT_STATUS_FAILED, WorkflowAction
from .execution_types import (
    EXECUTION_FAILURE_ADAPTER_FORBIDDEN,
    NormalizedExecutionResult,
)
from .outlook_adapter import OutlookActionInputError, OutlookExecutionAdapter, _parse_outlook_email_payload


class ProviderExecutionAdapterProtocol(Protocol):
    def availability_failure_code(self, *, action: WorkflowAction) -> str | None: ...

    def execute(self, *, action: WorkflowAction, execution_context: Any, idempotency: Any) -> Any: ...


@dataclass
class EnvironmentGuardedExecutionAdapter:
    delegate: ProviderExecutionAdapterProtocol
    runtime: AppRuntimeConfig
    guard: Callable[[WorkflowAction], bool]

    def availability_failure_code(self, *, action: WorkflowAction) -> str | None:
        delegated_failure = self.delegate.availability_failure_code(action=action)
        if delegated_failure is not None:
            return delegated_failure
        if not self.guard(action):
            return EXECUTION_FAILURE_ADAPTER_FORBIDDEN
        return None

    def execute(self, *, action: WorkflowAction, execution_context: Any, idempotency: Any) -> Any:
        if not self.guard(action):
            return NormalizedExecutionResult(
                adapter_code=action.target_adapter_code,
                attempt_status=EXECUTION_ATTEMPT_STATUS_FAILED,
                response_snapshot={"stage": "provider_safety", "reason": "provider_execution_disabled"},
                failure_code=EXECUTION_FAILURE_ADAPTER_FORBIDDEN,
            )
        return self.delegate.execute(
            action=action,
            execution_context=execution_context,
            idempotency=idempotency,
        )


def guard_outlook_execution_adapter(
    adapter: OutlookExecutionAdapter,
    *,
    runtime: AppRuntimeConfig,
    provider_enabled: bool = True,
) -> EnvironmentGuardedExecutionAdapter:
    return EnvironmentGuardedExecutionAdapter(
        delegate=adapter,
        runtime=runtime,
        guard=lambda action: _is_outlook_action_allowed(action, runtime=runtime, provider_enabled=provider_enabled),
    )


def guard_asana_execution_adapter(
    adapter: AsanaExecutionAdapter,
    *,
    runtime: AppRuntimeConfig,
    provider_enabled: bool = True,
) -> EnvironmentGuardedExecutionAdapter:
    return EnvironmentGuardedExecutionAdapter(
        delegate=adapter,
        runtime=runtime,
        guard=lambda action: _is_asana_action_allowed(
            action,
            runtime=runtime,
            default_project_gid=adapter.config.default_project_gid,
            provider_enabled=provider_enabled,
        ),
    )


def _is_outlook_action_allowed(
    action: WorkflowAction,
    *,
    runtime: AppRuntimeConfig,
    provider_enabled: bool,
) -> bool:
    if not runtime.is_staging:
        return True
    if not provider_enabled:
        return False
    try:
        payload = _parse_outlook_email_payload(action.structured_payload)
    except OutlookActionInputError:
        return True
    return runtime.is_email_recipient_allowed(payload.recipient_email)


def _is_asana_action_allowed(
    action: WorkflowAction,
    *,
    runtime: AppRuntimeConfig,
    default_project_gid: str | None,
    provider_enabled: bool,
) -> bool:
    if not runtime.is_staging:
        return True
    if not provider_enabled:
        return False
    try:
        project_gid = _resolve_project_gid(action, default_project_gid=default_project_gid)
    except AsanaActionInputError:
        return True
    if project_gid is None:
        return True
    return runtime.is_asana_project_allowed(project_gid)
