"""Bounded private local clients; no diagnostic exception details escape."""

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
from botocore.exceptions import ClientError
from pymongo import AsyncMongoClient

from shipsense_local.config import LocalFailure, LocalSettings, local_profile

T = TypeVar("T")
MAX_OBJECT = 32768


def local_s3(settings: LocalSettings, mode: str = "authenticated") -> Any:
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
        endpoint_url=settings.s3_endpoint,
        region_name="us-east-1",
        aws_access_key_id=(
            "incorrect-local-identity"
            if mode == "wrong-key"
            else settings.access_key.get_secret_value()
        ),
        aws_secret_access_key=settings.secret_key.get_secret_value(),
        config=Config(
            signature_version=UNSIGNED if mode == "unsigned" else "s3v4",
            connect_timeout=0.35,
            read_timeout=1.5,
            retries={"total_max_attempts": 1},
            max_pool_connections=4,
            s3={"addressing_style": "path"},
            proxies={},
        ),
    )


class PrivateObjects:
    """At most four running S3 calls, including calls outliving cancellation.

    Admission fails closed rather than accumulating an unbounded executor queue.
    Socket/retry bounds also cap the underlying work after a caller times out.
    """

    def __init__(self, settings: LocalSettings) -> None:
        local_profile()
        self.bucket = settings.bucket
        self._client = local_s3(settings)
        self._pool = ThreadPoolExecutor(max_workers=4, thread_name_prefix="local-s3")
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
        # The container precreates only the named synthetic bucket. Application
        # credentials deliberately have no CreateBucket/Admin permission.
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

    async def write_verified(self, key: str, data: bytes, checksum: str) -> None:
        if not data or len(data) > MAX_OBJECT or hashlib.sha256(data).hexdigest() != checksum:
            raise LocalFailure("OBJECT_CHECKSUM_MISMATCH")

        def conditional_write() -> None:
            try:
                self._client.put_object(
                    Bucket=self.bucket,
                    Key=key,
                    Body=data,
                    ContentType="application/json",
                    IfNoneMatch="*",
                )
            except ClientError as error:
                if error.response["ResponseMetadata"]["HTTPStatusCode"] not in (409, 412):
                    raise

        await self.call(conditional_write)
        # Never trust ETag or a successful write as payload-integrity proof.
        await self.read_verified(key, checksum)

    async def close(self) -> None:
        self._closed = True
        if self._pending:
            await asyncio.gather(*self._pending, return_exceptions=True)
        try:
            await asyncio.to_thread(self._client.close)
        finally:
            await asyncio.to_thread(self._pool.shutdown, wait=True, cancel_futures=True)


class LocalClients:
    def __init__(self, settings: LocalSettings) -> None:
        local_profile()
        self.mongo: AsyncMongoClient[dict[str, Any]] = AsyncMongoClient(
            host=settings.mongo_host,
            port=settings.mongo_port,
            username=settings.mongo_user,
            password=settings.mongo_password.get_secret_value(),
            authSource=settings.database,
            serverSelectionTimeoutMS=500,
            connectTimeoutMS=350,
            socketTimeoutMS=500,
            waitQueueTimeoutMS=350,
            maxPoolSize=4,
            retryWrites=False,
            directConnection=True,
            timeoutMS=800,
        )
        self.database = self.mongo[settings.database]
        self.objects = PrivateObjects(settings)

    async def mongo_probe(self) -> bool:
        try:
            async with asyncio.timeout(1):
                # Authenticated application operation; ping alone need not require auth.
                await self.database.fixtures.find_one(
                    {
                        "tenantId": "synthetic-health",
                        "projectId": "synthetic-local",
                        "serviceId": "foundation",
                        "environment": "local",
                        "provider": "synthetic",
                        "providerObjectId": "local-probe",
                        "providerVersion": "p01",
                    },
                    {"_id": 1},
                )
            return True
        except Exception:
            return False

    async def close(self) -> None:
        try:
            await self.objects.close()
        finally:
            await self.mongo.close()

    async def __aenter__(self) -> "LocalClients":
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.close()
