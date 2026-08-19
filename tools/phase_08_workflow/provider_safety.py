from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Protocol

from tools.runtime_environment import AppRuntimeConfig

from .asana_adapter import AsanaActionInputError, AsanaExecutionAdapter, _resolve_project_gid
from .contracts import WorkflowAction
from .execution_types import (
    EXECUTION_FAILURE_ADAPTER_FORBIDDEN,
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
        return self.delegate.execute(
            action=action,
            execution_context=execution_context,
            idempotency=idempotency,
        )


def guard_outlook_execution_adapter(
    adapter: OutlookExecutionAdapter,
    *,
    runtime: AppRuntimeConfig,
) -> EnvironmentGuardedExecutionAdapter:
    return EnvironmentGuardedExecutionAdapter(
        delegate=adapter,
        runtime=runtime,
        guard=lambda action: _is_outlook_action_allowed(action, runtime=runtime),
    )


def guard_asana_execution_adapter(
    adapter: AsanaExecutionAdapter,
    *,
    runtime: AppRuntimeConfig,
) -> EnvironmentGuardedExecutionAdapter:
    return EnvironmentGuardedExecutionAdapter(
        delegate=adapter,
        runtime=runtime,
        guard=lambda action: _is_asana_action_allowed(action, runtime=runtime, default_project_gid=adapter.config.default_project_gid),
    )


def _is_outlook_action_allowed(action: WorkflowAction, *, runtime: AppRuntimeConfig) -> bool:
    if not runtime.is_staging:
        return True
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
) -> bool:
    if not runtime.is_staging:
        return True
    try:
        project_gid = _resolve_project_gid(action, default_project_gid=default_project_gid)
    except AsanaActionInputError:
        return True
    if project_gid is None:
        return True
    return runtime.is_asana_project_allowed(project_gid)
