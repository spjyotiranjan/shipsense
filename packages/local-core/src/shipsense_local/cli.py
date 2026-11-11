"""Cross-platform explicit local lifecycle and inert seed commands."""

import argparse
import asyncio
import json
import os
from pathlib import Path

from botocore.exceptions import ClientError

from shipsense_local.adapters import LocalClients, local_s3
from shipsense_local.config import PROJECT, ROOT, LocalFailure, LocalSettings, load_settings
from shipsense_local.fixtures import CASES, load_fixture, seed_all
from shipsense_local.queue import Envelope, MemoryQueue
from shipsense_local.stack import LocalStack, initialize


async def private_access(settings: LocalSettings, clients: LocalClients) -> None:
    """Exercise actual authorization; 404/transport failure is not a denial pass."""

    def denied(mode: str) -> bool:
        client = local_s3(settings, mode)
        try:
            client.list_objects_v2(
                Bucket="shipsense-denied-probe" if mode == "wrong-bucket" else settings.bucket,
                MaxKeys=1,
            )
        except ClientError as error:
            return bool(error.response["ResponseMetadata"]["HTTPStatusCode"] == 403)
        finally:
            client.close()
        return False

    for mode in ("unsigned", "wrong-key", "wrong-bucket"):
        if not await clients.objects.call(lambda: denied(mode)):
            raise LocalFailure("PRIVATE_ACCESS_BOUNDARY_FAILED")


async def wait_for_services(settings: LocalSettings) -> None:
    async with LocalClients(settings) as clients:
        async with asyncio.timeout(45):
            while not await clients.mongo_probe():
                await asyncio.sleep(0.4)
            while True:
                try:
                    await clients.objects.verify_bucket()
                    break
                except LocalFailure:
                    await asyncio.sleep(0.4)
        await private_access(settings, clients)


async def queue_smoke() -> dict[str, object]:
    queue = MemoryQueue()
    manifest, _ = load_fixture(ROOT / "tests/fixtures/p01", CASES[0])
    first = Envelope(manifest=manifest, sequence=2)
    try:
        queue.enqueue(first)
        duplicate = queue.enqueue(first)
        outcomes = [(await queue.consume_one())["outcome"]]
        for sequence, kind in ((1, "observe"), (3, "poison"), (4, "timeout")):
            queue.enqueue(
                Envelope.model_validate({"manifest": manifest, "sequence": sequence, "kind": kind})
            )
            outcomes.append((await queue.consume_one())["outcome"])
        return {
            "duplicate": duplicate,
            "outcomes": outcomes,
            "effects": 0,
            "restartLosesMessagesAndDeduplication": True,
        }
    finally:
        queue.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("up", "down", "reset", "seed", "check", "queue-smoke"))
    base = Path(os.environ.get("LOCALAPPDATA", str(Path.home() / ".local/state")))
    parser.add_argument("--state-dir", type=Path, default=base / "ShipSense/local-p01")
    parser.add_argument("--confirm-synthetic-reset", choices=(PROJECT,))
    args = parser.parse_args()
    try:
        if args.command == "queue-smoke":
            result: object = asyncio.run(queue_smoke())
        else:
            settings = (
                initialize(args.state_dir)
                if args.command == "up"
                else load_settings(args.state_dir)
            )
            stack = LocalStack(args.state_dir, settings)
            if args.command == "up":
                measurement = stack.up()
                try:
                    asyncio.run(wait_for_services(settings))
                except Exception:
                    # An insecure or failed boot is not left serving by this command.
                    stack.down()
                    raise
                result = {"status": "ready", "privateAccess": "verified", **measurement}
            elif args.command in ("down", "reset"):
                stack.down(reset=args.command == "reset", confirmation=args.confirm_synthetic_reset)
                result = {"status": "stopped", "volumesPreserved": args.command == "down"}
            else:
                stack.validate_ownership()

                async def operation() -> object:
                    async with LocalClients(settings) as clients:
                        if args.command == "seed":
                            return await seed_all(clients)
                        positive = await clients.mongo_probe() and await clients.objects.probe()
                        if not positive:
                            raise LocalFailure("LOCAL_DEPENDENCY_UNAVAILABLE")
                        await private_access(settings, clients)
                        return {"status": "ready", "privateAccess": "verified"}

                result = asyncio.run(operation())
        print(json.dumps(result, sort_keys=True))
        return 0
    except LocalFailure as error:
        print(json.dumps({"error": str(error)}))
        return 2
    except Exception:
        # Libraries, Docker, validation errors and DSNs can contain raw secrets.
        print(json.dumps({"error": "LOCAL_OPERATION_FAILED"}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
