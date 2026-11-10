"""Bounded client lifecycle and same-process no-effect queue readiness."""

import asyncio
from typing import Protocol

from shipsense_local.adapters import BoundedObjects
from shipsense_local.queue import MemoryQueue

from shipsense_api.diagnostics import ReadinessGate


class ReadinessClients(Protocol):
    @property
    def objects(self) -> BoundedObjects: ...

    async def mongo_probe(self) -> bool: ...

    async def close(self) -> None: ...


class DependencyReadiness:
    def __init__(self, clients: ReadinessClients) -> None:
        self.clients = clients
        self.queue = MemoryQueue()
        self.gate = ReadinessGate(
            {
                "mongodb": clients.mongo_probe,
                "storage": clients.objects.probe,
                "queue": self.queue_probe,
            }
        )
        self._closed = False
        self._closing: asyncio.Task[None] | None = None

    async def queue_probe(self) -> bool:
        return not self._closed and await self.queue.probe()

    async def close(self) -> None:
        if self._closing is None:
            self._closed = True
            self.queue.close()
            self._closing = asyncio.create_task(self.clients.close())
        # Do not abandon shielded S3 workers or Mongo pools on caller cancellation.
        try:
            await asyncio.shield(self._closing)
        except asyncio.CancelledError:
            await asyncio.shield(self._closing)
            raise
