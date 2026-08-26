"""Command manager for connected Android VoiceOS devices."""

from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Dict, Optional

from android_bridge.protocol import AndroidCommand, AndroidResult


class AndroidDeviceManager:
    """Tracks Android devices and coordinates commands and results."""

    def __init__(self) -> None:
        self._queues: Dict[str, asyncio.Queue[AndroidCommand]] = defaultdict(
            asyncio.Queue
        )
        self._pending: Dict[str, asyncio.Future[AndroidResult]] = {}
        self._lock = asyncio.Lock()

    async def register(self, device_id: str) -> None:
        if not device_id or not device_id.strip():
            raise ValueError("device_id is required")

        async with self._lock:
            self._queues.setdefault(device_id, asyncio.Queue())

    async def unregister(self, device_id: str) -> None:
        async with self._lock:
            self._queues.pop(device_id, None)

            for command_id, future in list(self._pending.items()):
                if not future.done():
                    future.cancel()
                self._pending.pop(command_id, None)

    async def is_registered(self, device_id: str) -> bool:
        async with self._lock:
            return device_id in self._queues

    async def enqueue(self, command: AndroidCommand) -> None:
        if not await self.is_registered(command.device_id):
            raise KeyError(
                f"Android device is not registered: {command.device_id}"
            )

        async with self._lock:
            self._pending[command.command_id] = asyncio.get_running_loop().create_future()

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

    async def record_result(self, result: AndroidResult) -> None:
        async with self._lock:
            future = self._pending.pop(result.command_id, None)

        if future is not None and not future.done():
            future.set_result(result)

    async def wait_for_result(
        self,
        command_id: str,
        timeout: float = 30.0,
    ) -> AndroidResult:
        async with self._lock:
            future = self._pending.get(command_id)

        if future is None:
            raise KeyError(f"Unknown Android command: {command_id}")

        try:
            return await asyncio.wait_for(future, timeout=timeout)
        finally:
            async with self._lock:
                self._pending.pop(command_id, None)


android_device_manager = AndroidDeviceManager()
