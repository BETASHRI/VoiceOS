"""Protocol definitions for communication with Android VoiceOS clients."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict
from uuid import uuid4


@dataclass
class AndroidCommand:
    """A command sent from VoiceOS to an Android device."""

    device_id: str
    intent: str
    params: Dict[str, Any] = field(default_factory=dict)
    command_id: str = field(default_factory=lambda: uuid4().hex)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "command",
            "command_id": self.command_id,
            "device_id": self.device_id,
            "intent": self.intent,
            "params": self.params,
        }


@dataclass
class AndroidResult:
    """Result returned by Android after executing a command."""

    success: bool
    intent: str
    message: str = ""
    result: Any = None
    command_id: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "result",
            "command_id": self.command_id,
            "success": self.success,
            "intent": self.intent,
            "message": self.message,
            "result": self.result,
        }
