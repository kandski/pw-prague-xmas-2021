from typing import Any

from src.scrapers.scraper import Scraper, Request
from src.full_example import Journey, scrape, SearchInput, read_search_input_from_args


def scraper_result_to_journey(scraper_dict: dict[str, Any]) -> Journey:
    return Journey(
        departure=scraper_dict["departure_datetime"],
        arrival=scraper_dict["arrival_datetime"],
        origin=scraper_dict["source"],
        destination=scraper_dict["destination"],
    )


def search_input_to_scraper_request(search_input: SearchInput) -> Request:
    return Request(search_input.origin, search_input.destination, search_input.departure)


def search_journeys(search_input: SearchInput) -> list[Journey]:
    scraper_request = search_input_to_scraper_request(search_input)
    scraper = Scraper(scraper_request)
    scraper_result = scraper.scrape()
    return [scraper_result_to_journey(scraper_journey) for scraper_journey in scraper_result]


if __name__ == "__main__":
    search_input = read_search_input_from_args()
    scrape(search_journeys, search_input)
