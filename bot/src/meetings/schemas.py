from pydantic import BaseModel


class MeetCreateResponse(BaseModel):
    hash: str
