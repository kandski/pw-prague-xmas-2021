import argparse
import datetime
import json
from typing import Dict

import requests
from collections import namedtuple
from json import JSONEncoder

CARRIER_NAME = "REGIOJET"
DATETIME_SUPPORTED_FORMATS = ["%d-%m-%Y", "%Y-%m-%d"]
SEARCH_CURRENCY = "EUR"

Request = namedtuple("request", "src dst date")
SOLD_OUT = "sold_out"


class Scraper:
    def __init__(self, request: Request):
        self._locations_map = None
        self.request = request

    def _get_locations_map(self) -> Dict[str, int]:
        response = requests.get(
            "https://brn-ybus-pubapi.sa.cz/restapi/consts/locations"
        )
        locations = response.json()
        locations_map = {}
        for location in locations:
            for city in location["cities"]:
                locations_map[city["name"]] = city["id"]
                for alias in city["aliases"]:
                    locations_map[alias] = city["id"]
        return locations_map

    @property
    def locations_map(self):
        if not self._locations_map:
            self._locations_map = self._get_locations_map()
        return self._locations_map

    def _load_data(self, request: Request) -> dict:
        params = {
            "departureDate": request.date.strftime("%Y-%m-%d"),
            "fromLocationId": self.locations_map[request.src],
            "fromLocationType": "CITY",
            "locale": "cs",
            "tariffs": "REGULAR",
            "toLocationId": self.locations_map[request.dst],
            "toLocationType": "CITY",
        }

        response = requests.get(
            "https://brn-ybus-pubapi.sa.cz/restapi/routes/search/simple",
            params=params,
            headers={"X-Currency": SEARCH_CURRENCY},
        )
        return response.json()

    def _check_data(self, data: dict):
        msg = data.get("message")
        if msg:
            if "departureDate.invalid" in msg or "arrivalDate.invalid" in msg:
                raise Exception("invalid date")

            raise Exception("unhandled error")

        if not data["routes"]:
            raise Exception("no routes in response")

    def _parse_data(self, data):
        time_format = "%Y-%m-%dT%H:%M:%S.000%z"

        result = []

        for trip in data["routes"]:
            departure_time = datetime.datetime.strptime(
                trip["departureTime"], time_format
            )
            arrival_time = datetime.datetime.strptime(trip["arrivalTime"], time_format)

            if not trip["bookable"]:
                fare = SOLD_OUT
            else:
                fare = {
                    "amount": float(trip["priceFrom"]),
                    "currency": SEARCH_CURRENCY,
                }

            result.append(
                {
                    "departure_datetime": departure_time,
                    "arrival_datetime": arrival_time,
                    "source": self.request.src,
                    "destination": self.request.dst,
                    "type": trip["vehicleTypes"][0],
                    "free_seats": trip["freeSeatsCount"],
                    "carrier": CARRIER_NAME,
                    "fare": fare,
                }
            )
        return result

    def scrape(self):
        raw_response = self._load_data(self.request)
        self._check_data(raw_response)
        return self._parse_data(raw_response)


def date_type(date_string):
    for fmt in DATETIME_SUPPORTED_FORMATS:
        try:
            return datetime.datetime.strptime(date_string, fmt)
        except ValueError:
            pass

    msg = f"date {date_string} doesn't match formats {DATETIME_SUPPORTED_FORMATS}"
    raise NotImplementedError(msg)


def parse_input_request() -> Request:
    parser = argparse.ArgumentParser()

    parser.add_argument("src")
    parser.add_argument("dst")
    parser.add_argument("date", type=date_type)

    args = parser.parse_args()

    return Request(args.src, args.dst, args.date)


class CustomJSONEncoder(JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime.datetime):
            return datetime.datetime.isoformat(o)
        # Let the base class default method raise the TypeError
        return JSONEncoder.default(self, o)


def main():
    request = parse_input_request()
    result = Scraper(request).scrape()
    print(json.dumps(result, indent=2, cls=CustomJSONEncoder))
