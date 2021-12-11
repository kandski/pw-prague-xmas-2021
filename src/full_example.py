import json
import logging
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta
from pprint import pprint
from random import randint
from time import sleep
from typing import Callable

from redis import Redis
from slugify import slugify

log = logging.getLogger()


@dataclass
class Journey:
    origin: str
    destination: str
    departure: datetime
    arrival: datetime

    @classmethod
    def from_dict(cls, input_dict):
        return cls(
            origin=input_dict["origin"],
            destination=input_dict["destination"],
            departure=datetime.fromisoformat(input_dict["departure"]),
            arrival=datetime.fromisoformat(input_dict["arrival"]),
        )


def journey_to_dict(journey: Journey) -> dict:
    return {
        "origin": journey.origin,
        "destination": journey.destination,
        "departure": journey.departure.isoformat(),
        "arrival": journey.arrival.isoformat(),
    }


@dataclass
class SearchInput:
    origin: str
    destination: str
    departure: datetime


def generate_random_journey(search_input: SearchInput) -> Journey:
    arrival = search_input.departure + timedelta(hours=randint(1, 12))
    return Journey(
        origin=search_input.origin,
        destination=search_input.destination,
        departure=search_input.departure,
        arrival=arrival,
    )


def search_random_journeys(search_input: SearchInput) -> list[Journey]:
    sleep(3)  # simulating an expensive operation
    return [generate_random_journey(search_input) for _ in range(randint(0, 6))]


def serialize_journeys(journeys: list[Journey]) -> str:
    return json.dumps([journey_to_dict(journey) for journey in journeys])


def deserialize_journeys(journeys: str) -> list[Journey]:
    return [Journey.from_dict(journey) for journey in json.loads(journeys)]


def create_redis_key(search_input: SearchInput) -> str:
    KEY_PATTERN = "{surname}:journey:{origin}_{destination}_{departure}"
    return KEY_PATTERN.format(
        surname="borovicka",
        origin=slugify(search_input.origin),
        destination=slugify(search_input.destination),
        departure=str(search_input.departure.isoformat()),
    )


CACHE_EXPIRATION = timedelta(minutes=1)


def search_journeys_with_cache(
    redis: Redis, search_input: SearchInput, search_journeys: Callable[[SearchInput], list[Journey]]
) -> list[Journey]:
    cache_key = create_redis_key(search_input)
    journeys = redis.get(cache_key)

    if journeys is not None:
        log.debug("found in cache")
        return deserialize_journeys(journeys)

    log.debug("nothing in cache, triggering the search")
    searched_journeys = search_journeys(search_input)
    redis.set(cache_key, serialize_journeys(searched_journeys), CACHE_EXPIRATION)
    return searched_journeys


def read_search_input_from_args() -> SearchInput:
    [origin, destination, departure] = sys.argv[1:]
    return SearchInput(
        origin=origin,
        destination=destination,
        departure=datetime.fromisoformat(departure),
    )


def setup_logger() -> None:
    log.setLevel(logging.DEBUG)
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    handler.setFormatter(formatter)
    log.addHandler(handler)


def scrape(search_journeys: Callable[[SearchInput], list[Journey]], search_input: SearchInput) -> list[Journey]:
    redis = Redis(host="redis.pythonweekend.skypicker.com", port=6379, db=0, decode_responses=True)
    setup_logger()
    journeys = search_journeys_with_cache(redis, search_input, search_journeys)
    return journeys


if __name__ == "__main__":
    search_input = read_search_input_from_args()
    scrape(search_random_journeys, search_input)
