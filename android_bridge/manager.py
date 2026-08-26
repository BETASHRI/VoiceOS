"""Manage connected Android VoiceOS devices and pending commands."""

from __future__ import annotations

import asyncio
import logging
from typing import Dict, Optional

from android_bridge.protocol import AndroidCommand, AndroidResult

logger = logging.getLogger(__name__)


class AndroidDeviceManager:
    """Tracks connected Android devices and routes commands/results."""

    def __init__(self) -> None:
        self._devices: Dict[str, asyncio.Queue[AndroidCommand]] = {}
        self._results: Dict[str, AndroidResult] = {}
        self._result_events: Dict[str, asyncio.Event] = {}
        self._lock = asyncio.Lock()

    async def register(self, device_id: str) -> None:
        """Register or replace a connected Android device."""
        async with self._lock:
            self._devices[device_id] = asyncio.Queue()

        logger.info("Registered Android device: %s", device_id)

    async def unregister(self, device_id: str) -> None:
        """Remove a disconnected Android device."""
        async with self._lock:
            self._devices.pop(device_id, None)

        logger.info("Unregistered Android device: %s", device_id)

    async def is_connected(self, device_id: str) -> bool:
        """Return whether an Android device is currently connected."""
        async with self._lock:
            return device_id in self._devices

    async def send_command(self, command: AndroidCommand) -> bool:
        """
        Queue a command for a connected Android device.

        Returns True if the command was queued, otherwise False.
        """
        async with self._lock:
            queue = self._devices.get(command.device_id)

        if queue is None:
            logger.warning(
                "Cannot send command; Android device is not connected: %s",
                command.device_id,
            )
            return False

        await queue.put(command)

        self._result_events[command.command_id] = asyncio.Event()

        logger.info(
            "Queued Android command %s for device %s: %s",
            command.command_id,
            command.device_id,
            command.intent,
        )

        return True

    async def next_command(
        self,
        device_id: str,
    ) -> Optional[AndroidCommand]:
        """Wait for and return the next command for a connected device."""
        async with self._lock:
            queue = self._devices.get(device_id)

        if queue is None:
            return None

        return await queue.get()

    async def record_result(self, result: AndroidResult) -> None:
        """Store a result returned by an Android device."""
        self._results[result.command_id] = result

        event = self._result_events.get(result.command_id)

        if event is not None:
            event.set()

        logger.info(
            "Android command result received: %s success=%s",
            result.command_id,
            result.success,
        )

    async def get_result(
        self,
        command_id: str,
        timeout: Optional[float] = None,
    ) -> Optional[AndroidResult]:
        """
        Wait for a command result.

        Returns None if the result is not received before the timeout.
        """
        if command_id in self._results:
            return self._results[command_id]

        event = self._result_events.get(command_id)

        if event is None:
            return None

        try:
            if timeout is None:
                await event.wait()
            else:
                await asyncio.wait_for(
                    event.wait(),
                    timeout=timeout,
                )
        except asyncio.TimeoutError:
            return None

        return self._results.get(command_id)

    async def send_and_wait(
        self,
        command: AndroidCommand,
        timeout: float = 30.0,
    ) -> Optional[AndroidResult]:
        """
        Send a command to Android and wait for its result.
        """
        queued = await self.send_command(command)

        if not queued:
            return None

        return await self.get_result(
            command.command_id,
            timeout=timeout,
        )

    async def connected_devices(self) -> list[str]:
        """Return the IDs of currently connected Android devices."""
        async with self._lock:
            return list(self._devices.keys())

    async def clear_result(self, command_id: str) -> None:
        """Remove a completed command result from memory."""
        self._results.pop(command_id, None)
        self._result_events.pop(command_id, None)


# Shared manager used by the Android WebSocket server.
android_device_manager = AndroidDeviceManager()
