"""Client for interacting with SportsDataIO NFL endpoints."""
from __future__ import annotations

import datetime as dt
import logging
from typing import Dict, List, Optional

from ..config import APISettings
from ..http_client import http_get

LOGGER = logging.getLogger(__name__)


class SportsDataClient:
    BASE_URL = "https://api.sportsdata.io/v3/nfl"

    def __init__(self, settings: APISettings):
        self.settings = settings

    def _request(self, endpoint: str, params: Optional[Dict[str, str]] = None) -> Dict:
        url = f"{self.BASE_URL}/{endpoint}"
        headers = {"Ocp-Apim-Subscription-Key": self.settings.sportsdata_api_key}
        LOGGER.debug("Requesting %s with %s", url, params)
        return http_get(url, params=params, headers=headers)

    def get_injuries(self, season: Optional[int] = None) -> List[Dict]:
        season = season or self.settings.sportsdata_season or dt.datetime.now().year
        return self._request(f"scores/json/Injuries/{season}")

    def get_players(self) -> List[Dict]:
        return self._request("scores/json/Players")

    def get_team_game_stats(self, season: Optional[int] = None) -> List[Dict]:
        season = season or self.settings.sportsdata_season or dt.datetime.now().year
        return self._request(f"stats/json/TeamGameStats/{season}")

    def get_team_season_stats(self, season: Optional[int] = None) -> List[Dict]:
        season = season or self.settings.sportsdata_season or dt.datetime.now().year
        return self._request(f"stats/json/TeamSeasonStats/{season}")

    def get_team_records(self, season: Optional[int] = None) -> List[Dict]:
        season = season or self.settings.sportsdata_season or dt.datetime.now().year
        return self._request(f"scores/json/Standings/{season}")

    def get_head_to_head_record(self, team_a: str, team_b: str, lookback_years: int = 5) -> Dict[str, int]:
        current_year = self.settings.sportsdata_season or dt.datetime.now().year
        wins_a = wins_b = 0
        for season in range(current_year - lookback_years, current_year + 1):
            games = self._request(f"scores/json/Scores/{season}")
            for game in games:
                if {game.get("HomeTeam"), game.get("AwayTeam")} == {team_a, team_b}:
                    if game.get("HomeTeam") == team_a:
                        if game.get("HomeScore", 0) > game.get("AwayScore", 0):
                            wins_a += 1
                        else:
                            wins_b += 1
                    else:
                        if game.get("AwayScore", 0) > game.get("HomeScore", 0):
                            wins_a += 1
                        else:
                            wins_b += 1
        return {team_a: wins_a, team_b: wins_b}
