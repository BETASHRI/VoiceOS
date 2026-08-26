"""Protocol definitions for communication with Android VoiceOS clients."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class AndroidCommand:
    """A command sent from VoiceOS to an Android device."""

    device_id: str
    intent: str
    params: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "device_id": self.device_id,
            "intent": self.intent,
            "params": self.params,
        }


@dataclass
class AndroidResult:
    """Result returned by an Android device after executing a command."""

    success: bool
    intent: str
    message: str = ""
    result: Any = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "intent": self.intent,
            "message": self.message,
            "result": self.result,
        }
