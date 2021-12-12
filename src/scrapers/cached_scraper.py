import json
import logging
from datetime import timedelta
from json import JSONDecodeError
from typing import Any

from redis import Redis
from slugify import slugify

from src.models.journey import SearchInput, Journey
from src.scrapers.scraper import Scraper, Request

log = logging.getLogger()


def journey_to_dict(journey: Journey) -> dict:
    return {
        "origin": journey.origin,
        "destination": journey.destination,
        "departure": journey.departure.isoformat(),
        "arrival": journey.arrival.isoformat(),
        "type": journey.type,
        "free_seats": journey.free_seats,
        "carrier": journey.carrier,
        "fare": journey.fare
    }


def serialize_journeys(journeys: list[Journey]) -> str:
    return json.dumps([journey_to_dict(journey) for journey in journeys])


def deserialize_journeys(journeys: str) -> list[Journey]:
    try:
        return [Journey.from_dict(journey) for journey in json.loads(journeys)]
    except JSONDecodeError:
        log.debug("journeys failed to deserialize")
        return []


def scraper_result_to_journey(scraper_dict: dict[str, Any]) -> Journey:
    return Journey(
        departure=scraper_dict["departure_datetime"],
        arrival=scraper_dict["arrival_datetime"],
        origin=scraper_dict["source"],
        destination=scraper_dict["destination"],
        type=scraper_dict['type'],
        free_seats=scraper_dict['free_seats'],
        carrier=scraper_dict['carrier'],
        fare=scraper_dict['fare']
    )


def search_input_to_scraper_request(search_input: SearchInput) -> Request:
    return Request(search_input.origin, search_input.destination, search_input.departure)


def create_redis_key(search_input: SearchInput) -> str:
    key_pattern = "{surname}:journey:{origin}_{destination}_{departure}"
    return key_pattern.format(
        surname="borovicka",
        origin=slugify(search_input.origin),
        destination=slugify(search_input.destination),
        departure=str(search_input.departure.isoformat()),
    )


CACHE_EXPIRATION = timedelta(minutes=1)


def search_journeys(search_input: SearchInput) -> list[Journey]:
    scraper_request = search_input_to_scraper_request(search_input)
    scraper = Scraper(scraper_request)
    scraper_result = scraper.scrape()
    return [scraper_result_to_journey(scraper_journey) for scraper_journey in scraper_result]


def search_journeys_with_cache(redis: Redis, search_input: SearchInput) -> list[Journey]:
    cache_key = create_redis_key(search_input)
    journeys = redis.get(cache_key)

    if journeys is not None:
        log.debug("found in cache")
        return deserialize_journeys(journeys)

    log.debug("nothing in cache, triggering the search")
    searched_journeys = search_journeys(search_input)
    redis.set(cache_key, serialize_journeys(searched_journeys), CACHE_EXPIRATION)
    return searched_journeys


def scrape(search_input: SearchInput) -> list[Journey]:
    redis = Redis(host="redis.pythonweekend.skypicker.com", port=6379, db=0, decode_responses=True)
    journeys = search_journeys_with_cache(redis, search_input)
    if journeys:
        return journeys
    else:
        return search_journeys(search_input)
