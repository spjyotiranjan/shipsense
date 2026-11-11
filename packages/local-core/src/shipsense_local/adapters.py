"""Bounded private hosted clients; no diagnostic exception details escape."""

import asyncio
import hashlib
import os
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from typing import Any, TypeVar

import boto3
import botocore.session
from botocore import UNSIGNED
from botocore.config import Config

from shipsense_local.config import LocalFailure

T = TypeVar("T")
MAX_OBJECT = 32768


def private_s3(
    endpoint: str, region: str, access_key: str, secret_key: str, *, unsigned: bool = False
) -> Any:
    # Isolate this session from host AWS profiles, files and credential sources.
    variables = {
        name: (None, None, values[2], values[3])
        for name, values in botocore.session.Session.SESSION_VARIABLES.items()
    }
    variables["profile"] = (None, None, None, None)
    variables["config_file"] = (None, None, os.devnull, None)
    variables["credentials_file"] = (None, None, os.devnull, None)
    session = boto3.session.Session(
        botocore_session=botocore.session.Session(session_vars=variables)
    )
    return session.client(
        "s3",
        endpoint_url=endpoint,
        region_name=region,
        verify=True,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        config=Config(
            signature_version=UNSIGNED if unsigned else "s3v4",
            connect_timeout=0.35,
            read_timeout=1.5,
            retries={"total_max_attempts": 1},
            max_pool_connections=4,
            s3={"addressing_style": "path"},
            proxies={},
        ),
    )


class BoundedObjects:
    """At most four running S3 calls, including calls outliving cancellation.

    Admission fails closed rather than accumulating an unbounded executor queue.
    Socket/retry bounds also cap the underlying work after a caller times out.
    """

    def __init__(self, bucket: str, client: Any) -> None:
        self.bucket = bucket
        self._client = client
        self._pool = ThreadPoolExecutor(max_workers=4, thread_name_prefix="shipsense-r2")
        self._slots = asyncio.Semaphore(4)
        self._pending: set[asyncio.Future[Any]] = set()
        self._closed = False

    async def call(self, operation: Callable[[], T]) -> T:
        if self._closed or self._slots.locked():
            raise LocalFailure("STORAGE_UNAVAILABLE")
        await self._slots.acquire()
        future = asyncio.get_running_loop().run_in_executor(self._pool, operation)
        self._pending.add(future)

        def completed(done: asyncio.Future[Any]) -> None:
            self._pending.discard(done)
            self._slots.release()
            if not done.cancelled():
                done.exception()  # Retrieve late failures without logging sensitive details.

        future.add_done_callback(completed)
        try:
            async with asyncio.timeout(2):
                return await asyncio.shield(future)
        except Exception:
            raise LocalFailure("STORAGE_UNAVAILABLE") from None

    async def verify_bucket(self) -> None:
        # Require an existing private bucket; never create it or grant access.
        await self.call(lambda: self._client.head_bucket(Bucket=self.bucket))

    async def probe(self) -> bool:
        try:
            async with asyncio.timeout(1):
                await self.call(lambda: self._client.head_bucket(Bucket=self.bucket))
            return True
        except LocalFailure, TimeoutError:
            return False

    def _read(self, key: str) -> bytes:
        response = self._client.get_object(Bucket=self.bucket, Key=key)
        body = response["Body"]
        try:
            if response["ContentLength"] > MAX_OBJECT:
                raise LocalFailure("OBJECT_TOO_LARGE")
            data: bytes = body.read(MAX_OBJECT + 1)
            if len(data) > MAX_OBJECT:
                raise LocalFailure("OBJECT_TOO_LARGE")
            return data
        finally:
            body.close()

    async def read_verified(self, key: str, checksum: str) -> bytes:
        data = await self.call(lambda: self._read(key))
        if hashlib.sha256(data).hexdigest() != checksum:
            raise LocalFailure("OBJECT_CHECKSUM_MISMATCH")
        return data

    async def close(self) -> None:
        self._closed = True
        if self._pending:
            await asyncio.gather(*self._pending, return_exceptions=True)
        try:
            await asyncio.to_thread(self._client.close)
        finally:
            await asyncio.to_thread(self._pool.shutdown, wait=True, cancel_futures=True)
