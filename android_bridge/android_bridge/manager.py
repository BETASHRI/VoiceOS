"""In-memory command manager for connected Android VoiceOS devices."""

from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Dict, Optional

from android_bridge.protocol import AndroidCommand, AndroidResult


class AndroidDeviceManager:
    """Tracks Android devices and queues commands/results for them."""

    def __init__(self) -> None:
        self._queues: Dict[str, asyncio.Queue[AndroidCommand]] = defaultdict(asyncio.Queue)
        self._results: Dict[str, AndroidResult] = {}
        self._lock = asyncio.Lock()

    async def register(self, device_id: str) -> None:
        if not device_id or not device_id.strip():
            raise ValueError("device_id is required")

        async with self._lock:
            self._queues.setdefault(device_id, asyncio.Queue())

    async def unregister(self, device_id: str) -> None:
        async with self._lock:
            self._queues.pop(device_id, None)
            self._results.pop(device_id, None)

    async def is_registered(self, device_id: str) -> bool:
        async with self._lock:
            return device_id in self._queues

    async def enqueue(self, command: AndroidCommand) -> None:
        if not await self.is_registered(command.device_id):
            raise KeyError(
                f"Android device is not registered: {command.device_id}"
            )

        await self._queues[command.device_id].put(command)

    async def next_command(
        self,
        device_id: str,
        timeout: Optional[float] = None,
    ) -> Optional[AndroidCommand]:
        if not await self.is_registered(device_id):
            raise KeyError(
                f"Android device is not registered: {device_id}"
            )

        queue = self._queues[device_id]

        try:
            if timeout is None:
                return await queue.get()

            return await asyncio.wait_for(queue.get(), timeout=timeout)

        except asyncio.TimeoutError:
            return None

    async def record_result(
        self,
        device_id: str,
        result: AndroidResult,
    ) -> None:
        if not await self.is_registered(device_id):
            raise KeyError(
                f"Android device is not registered: {device_id}"
            )

        self._results[device_id] = result

    async def latest_result(
        self,
        device_id: str,
    ) -> Optional[AndroidResult]:
        return self._results.get(device_id)


android_device_manager = AndroidDeviceManager()
