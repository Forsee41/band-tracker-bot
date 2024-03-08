from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from uuid import UUID


class MQMessageType(Enum):
    admin_notification = "admin_notification"
    new_event_artist = "new_event_artist"
    event_update_finished = "event_update_finished"


class MQMessage(ABC):
    type_: MQMessageType

    @abstractmethod
    def to_dict(self) -> dict:
        """Returns data as dict. It'll be sent as message data."""

    @abstractmethod
    @classmethod
    def from_dict(cls: type, data: dict) -> "MQMessage":
        """Returns message class instance from mq dict"""


class EventUpdateFinished(MQMessage):
    """
    Message, sent when updater finished with cerain event.
    Includes event UUID and datetime.
    """

    type_ = MQMessageType.event_update_finished

    def __init__(self, uuid: UUID, created_at: datetime | None = None) -> None:
        self.uuid = uuid
        if created_at is None:
            self.created_at = datetime.now()
        else:
            self.created_at = created_at

    def to_dict(self) -> dict:
        return {
            "uuid": self.uuid,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls: type, data: dict) -> "EventUpdateFinished":
        return cls(**data)


class AdminNotification(MQMessage):
    type_ = MQMessageType.admin_notification

    def __init__(self, text: str, created_at: datetime | None = None) -> None:
        self.text = text
        if created_at is None:
            self.created_at = datetime.now()
        else:
            self.created_at = created_at

    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls: type, data: dict) -> "AdminNotification":
        return cls(**data)
