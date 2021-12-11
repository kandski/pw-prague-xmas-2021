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

    @classmethod
    def from_dict(cls, input_dict):
        return cls(
            origin=input_dict["origin"],
            destination=input_dict["destination"],
            departure=datetime.fromisoformat(input_dict["departure"]),
            arrival=datetime.fromisoformat(input_dict["arrival"]),
        )

@dataclass
class SearchInput:
    origin: str
    destination: str
    departure: datetime
