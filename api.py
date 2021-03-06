import logging
from datetime import datetime

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.custom_logger import setup_logger
from src.models.journey import SearchInput, Journey
from src.scrapers.cached_scraper import scrape

app = FastAPI()

origins = [
    "http://localhost:3000",
    "http://localhost:8080",
    "http://192.168.51.38:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
log = logging.getLogger()
setup_logger(log)


@app.get("/ping")
def ping():
    """hello pythonistas"""
    return 'pong'


@app.get("/search", response_model=list[Journey])
def search(origin: str, destination: str, departure: datetime) -> list[Journey]:
    search_input = {
        "origin": origin,
        "destination": destination,
        "departure": departure
    }
    return scrape(SearchInput(**search_input))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0")
