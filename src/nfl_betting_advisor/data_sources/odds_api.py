"""Client for interacting with The Odds API."""
from __future__ import annotations

import logging
from typing import Dict, List, Optional

from ..config import APISettings
from ..http_client import http_get

LOGGER = logging.getLogger(__name__)


class OddsAPIClient:
    BASE_URL = "https://api.the-odds-api.com/v4"

    def __init__(self, settings: APISettings):
        self.settings = settings

    def _request(self, endpoint: str, params: Optional[Dict[str, str]] = None) -> Dict:
        url = f"{self.BASE_URL}/{endpoint}"
        query = {
            "apiKey": self.settings.odds_api_key,
            "sport": self.settings.odds_sport_key,
            "region": self.settings.odds_region,
            "markets": self.settings.odds_market,
            "oddsFormat": "american",
        }
        if params:
            query.update(params)
        LOGGER.debug("Requesting %s with %s", url, query)
        data = http_get(url, params=query)
        return data

    def get_events(self) -> List[Dict]:
        return self._request("sports/{sport}/events".format(sport=self.settings.odds_sport_key))

    def get_player_props(self, event_id: Optional[str] = None) -> List[Dict]:
        endpoint = "odds"
        params: Dict[str, str] = {}
        if event_id:
            params["event"] = event_id
        return self._request(endpoint, params=params)

    def get_best_player_prop_odds(self, player_name: str, market: Optional[str] = None) -> Optional[Dict]:
        markets_data = self.get_player_props()
        best_offer: Optional[Dict] = None
        for event in markets_data:
            for bookmaker in event.get("bookmakers", []):
                for market_data in bookmaker.get("markets", []):
                    if market and market_data.get("key") != market:
                        continue
                    for outcome in market_data.get("outcomes", []):
                        outcome_name = outcome.get("description") or outcome.get("name")
                        if not outcome_name:
                            continue
                        if player_name.lower() in outcome_name.lower():
                            odds = int(outcome.get("price", 0))
                            if not best_offer or odds > best_offer["price"]:
                                best_offer = {
                                    "event": event.get("id"),
                                    "bookmaker": bookmaker.get("title"),
                                    "market": market_data.get("key"),
                                    "price": odds,
                                    "outcome": outcome_name,
                                }
        return best_offer
