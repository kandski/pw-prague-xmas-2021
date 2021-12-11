from datetime import datetime
from typing import List

import uvicorn

from src.models.journey import SearchInput, Journey

from fastapi import FastAPI

from src.full_example import scrape
from src.full_example_connected_to_scraper import search_journeys

app = FastAPI()


@app.get("/ping")
def ping():
    """hello pythonistas"""
    return 'pong'


@app.get("/search", response_model=List[Journey])
def search(origin: str, destination: str, departure: datetime) -> list[Journey]:
    search_input = {
        "origin": origin,
        "destination": destination,
        "departure": departure
    }
    return scrape(search_journeys, SearchInput(**search_input))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0")
