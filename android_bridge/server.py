"""WebSocket server for connected Android VoiceOS devices."""

from __future__ import annotations

import asyncio
import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from android_bridge.manager import android_device_manager
from android_bridge.protocol import AndroidResult

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/android", tags=["android"])


@router.websocket("/ws")
async def android_websocket(websocket: WebSocket) -> None:
    """Maintain a persistent connection with an Android VoiceOS client."""

    await websocket.accept()

    device_id = None

    try:
        raw = await websocket.receive_text()
        message = json.loads(raw)

        if message.get("type") != "register":
            await websocket.close(
                code=1008,
                reason="Registration required",
            )
            return

        device_id = str(message.get("device_id", "")).strip()

        if not device_id:
            await websocket.close(
                code=1008,
                reason="device_id required",
            )
            return

        await android_device_manager.register(device_id)

        await websocket.send_json(
            {
                "type": "registered",
                "device_id": device_id,
            }
        )

        logger.info(
            "Android device connected: %s",
            device_id,
        )

        while True:
            command = await android_device_manager.next_command(
                device_id
            )

            if command is None:
                continue

            await websocket.send_json(
                command.to_dict()
            )

            result_raw = await websocket.receive_text()
            result_data = json.loads(result_raw)

            if result_data.get("type") != "result":
                logger.warning(
                    "Unexpected Android message from %s: %s",
                    device_id,
                    result_data,
                )
                continue

            result = AndroidResult(
                success=bool(
                    result_data.get("success", False)
                ),
                intent=str(
                    result_data.get("intent", "")
                ),
                message=str(
                    result_data.get("message", "")
                ),
                result=result_data.get("result"),
                command_id=str(
                    result_data.get("command_id", "")
                ),
            )

            await android_device_manager.record_result(
                result
            )

    except WebSocketDisconnect:
        logger.info(
            "Android device disconnected: %s",
            device_id,
        )

    except Exception:
        logger.exception(
            "Android WebSocket error for device: %s",
            device_id,
        )

    finally:
        if device_id:
            await android_device_manager.unregister(
                device_id
          )
