"""Bounded same-process no-effect queue; all state is lost on restart."""

import asyncio
import hashlib
from collections import deque
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

from shipsense_local.config import LocalFailure, local_profile
from shipsense_local.fixtures import Manifest


class Envelope(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    manifest: Manifest
    sequence: Annotated[int, Field(strict=True, ge=0, le=10000)]
    kind: Literal["observe", "poison", "timeout"] = "observe"

    def delivery_id(self) -> str:
        return hashlib.sha256(self.model_dump_json().encode()).hexdigest()


class MemoryQueue:
    def __init__(self, capacity: int = 8) -> None:
        local_profile()
        if not 1 <= capacity <= 32:
            raise LocalFailure("INVALID_QUEUE_CAPACITY")
        self._queue: asyncio.Queue[Envelope] = asyncio.Queue(capacity)
        self._seen: set[str] = set()
        self._sequences: dict[str, int] = {}
        self.attempts: deque[dict[str, str]] = deque(maxlen=128)
        self._closed = False

    async def probe(self) -> bool:
        return not self._closed

    def enqueue(self, envelope: Envelope) -> str:
        if self._closed:
            raise LocalFailure("QUEUE_CLOSED")
        delivery = envelope.delivery_id()
        if delivery in self._seen:
            return "duplicate"
        if len(self._seen) >= 128 or self._queue.full():
            raise LocalFailure("QUEUE_CAPACITY")
        self._queue.put_nowait(envelope)
        self._seen.add(delivery)
        return "queued"

    async def consume_one(self) -> dict[str, str]:
        if self._closed:
            raise LocalFailure("QUEUE_CLOSED")
        try:
            async with asyncio.timeout(0.1):
                envelope = await self._queue.get()
        except TimeoutError:
            raise LocalFailure("QUEUE_EMPTY_TIMEOUT") from None
        stream = str(envelope.manifest.scope())
        try:
            if envelope.kind == "poison":
                outcome = "poison-rejected"
            elif envelope.manifest.is_expired():
                outcome = "expired-rejected"
            elif envelope.sequence <= self._sequences.get(stream, -1):
                outcome = "reordered-rejected"
            else:
                try:
                    async with asyncio.timeout(0.03):
                        if envelope.kind == "timeout":
                            await asyncio.sleep(0.1)
                        # No provider client, evaluator, runbook execution or effects.
                    self._sequences[stream] = envelope.sequence
                    outcome = "observed-no-effects"
                except TimeoutError:
                    outcome = "timed-out"
            attempt = {
                "deliveryId": envelope.delivery_id(),
                "correlationId": envelope.manifest.correlationId,
                "outcome": outcome,
            }
            self.attempts.append(attempt)
            return attempt.copy()
        finally:
            self._queue.task_done()

    def close(self) -> None:
        self._closed = True
        while not self._queue.empty():
            self._queue.get_nowait()
            self._queue.task_done()
        self._seen.clear()
        self._sequences.clear()
