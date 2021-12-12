from datetime import datetime
from dataclasses import dataclass
from typing import Union

from pydantic import BaseModel


class Journey(BaseModel):
    origin: str
    destination: str
    departure: datetime
    arrival: datetime
    type: str
    free_seats: int
    carrier: str
    fare: Union[str, dict]

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
            type=input_dict["type"],
            free_seats=input_dict["free_seats"],
            carrier=input_dict["carrier"],
            fare=input_dict["fare"]
        )

@dataclass
class SearchInput:
    origin: str
    destination: str
    departure: datetime
