"""No-effect boundary for metadata aggregates used by future API and tool adapters."""

from collections.abc import Callable
from datetime import datetime
from typing import Annotated, Literal, Protocol
from uuid import UUID

from pydantic import Field, TypeAdapter, ValidationError

from shipsense_domain.authorization import (
    AuthorizationService,
    HiddenResource,
    PrincipalContext,
    before_deadline,
)
from shipsense_domain.models import Contract, ResourceScope


class MetadataIndex(Protocol):
    """Query exact tenant/project/service/environment keys, never aggregate globally."""

    def count(self, scope: ResourceScope) -> int: ...

    def suggestions(self, scope: ResourceScope, prefix: str) -> tuple[str, ...]: ...


class MetadataGateway:
    """Internal only: context and correlation come from the trusted caller, not tool arguments."""

    def __init__(
        self,
        authorization: AuthorizationService,
        index: MetadataIndex,
        clock: Callable[[], datetime],
    ) -> None:
        self._authorization = authorization
        self._index = index
        self._clock = clock

    def _require_read(
        self, context: PrincipalContext, scope: ResourceScope, correlation_id: UUID
    ) -> None:
        result = self._authorization.evaluate(
            context, "metadata.read", scope, self._clock(), correlation_id
        )
        # Do not start retrieval if authority lookup or audit crossed the deadline.
        if not result.allowed or not before_deadline(self._clock(), context.expires_at):
            raise HiddenResource()

    def count(self, context: PrincipalContext, scope: ResourceScope, correlation_id: UUID) -> int:
        self._require_read(context, scope, correlation_id)
        return self._index.count(scope)

    def suggestions(
        self, context: PrincipalContext, scope: ResourceScope, prefix: str, correlation_id: UUID
    ) -> tuple[str, ...]:
        self._require_read(context, scope, correlation_id)
        if not 1 <= len(prefix) <= 120 or not prefix.isprintable():
            raise ValueError("Invalid suggestion prefix.")
        return self._index.suggestions(scope, prefix)


class CountArguments(Contract):
    kind: Literal["count"]


class SuggestArguments(Contract):
    kind: Literal["suggest"]
    prefix: Annotated[str, Field(strict=True, min_length=1, max_length=120)]


_ARGUMENTS = TypeAdapter(Annotated[CountArguments | SuggestArguments, Field(discriminator="kind")])


class MetadataTool:
    """No model integration: only read-only operations over server-pinned scope."""

    def __init__(self, gateway: MetadataGateway) -> None:
        self._gateway = gateway

    def invoke(
        self,
        context: PrincipalContext,
        pinned_scope: ResourceScope,
        correlation_id: UUID,
        arguments: object,
    ) -> int | tuple[str, ...]:
        try:
            parsed = _ARGUMENTS.validate_python(arguments, strict=True)
        except ValidationError:
            raise ValueError("Invalid tool arguments.") from None
        if isinstance(parsed, CountArguments):
            return self._gateway.count(context, pinned_scope, correlation_id)
        return self._gateway.suggestions(context, pinned_scope, parsed.prefix, correlation_id)
