"""Opt-in synthetic local dependencies owned by one API lifespan.

Configuration is read only. This module never starts services, creates secrets,
seeds data, or grants provider authority. The queue belongs to this API process.
"""

import asyncio
from pathlib import Path

from shipsense_local.adapters import LocalClients
from shipsense_local.config import LocalFailure, load_settings
from shipsense_local.queue import MemoryQueue

from shipsense_api.diagnostics import ReadinessGate


class LocalReadiness:
    def __init__(self, clients: LocalClients) -> None:
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

    @classmethod
    async def open(cls, directory: str) -> "LocalReadiness":
        # An explicit local absolute path only; no CWD or network-share fallback.
        if (
            not directory
            or len(directory) > 1024
            or directory.startswith(("\\\\", "//"))
            or not Path(directory).is_absolute()
        ):
            raise LocalFailure("LOCAL_CONFIG_INVALID")
        settings = await asyncio.to_thread(load_settings, Path(directory))
        clients = LocalClients(settings)
        try:
            return cls(clients)
        except BaseException:
            await clients.close()
            raise

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
