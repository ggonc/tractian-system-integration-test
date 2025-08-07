from datetime import datetime
from typing import Literal, TypedDict
from bson import ObjectId


class TracOSWorkorder(TypedDict):
    _id: ObjectId
    number: int
    status: Literal["pending", "in_progress", "completed", "on_hold", "cancelled"]
    title: str
    description: str
    createdAt: datetime
    updatedAt: datetime
    deleted: bool
    deletedAt: datetime | None = None