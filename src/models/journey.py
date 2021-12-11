from datetime import datetime
from dataclasses import dataclass
from pydantic import BaseModel


class Journey(BaseModel):
    origin: str
    destination: str
    departure: datetime
    arrival: datetime

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


@dataclass
class SearchInput:
    origin: str
    destination: str
    departure: datetime
