from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from bot.src.grpc.generated.service_pb2 import (
    FeedbackSchemaGRPC,
    FeedbackTypeGRPC,
    CommunicationChannelGRPC,
)


class FeedbackType(str, Enum):
    HELP = "HELP"
    SUGGESTION = "SUGGESTION"
    BUG = "BUG"
    PARTNERSHIP = "PARTNERSHIP"
    OTHER = "OTHER"


class CommunicationChannel(str, Enum):
    EMAIL = "EMAIL"
    TELEGRAM = "TELEGRAM"


class Feedback(BaseModel):
    id: UUID | None = None
    type: FeedbackType
    communication_channel: CommunicationChannel
    contact: str
    message: str

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    @classmethod
    def from_grpc(cls, data: FeedbackSchemaGRPC) -> "Feedback":
        return cls(
            type=FeedbackTypeGRPC.Name(data.type),
            communication_channel=CommunicationChannelGRPC.Name(
                data.communication_channel
            ),
            contact=data.contact,
            message=data.message,
        )
