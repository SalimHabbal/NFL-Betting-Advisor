"""Configuration utilities for the NFL betting advisor."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


def _load_env_file(path: str = ".env") -> None:
    env_path = Path(path)
    if not env_path.exists():
        return
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


_load_env_file()


@dataclass
class APISettings:
    odds_api_key: str
    sportsdata_api_key: str
    odds_region: str = "us"
    odds_market: str = "player_props"
    odds_sport_key: str = "americanfootball_nfl"
    sportsdata_season: Optional[int] = None

    @classmethod
    def from_env(cls) -> "APISettings":
        odds_key = os.getenv("ODDS_API_KEY", "9c85626ecf9eefc72a33034a22ff7ece")
        sportsdata_key = os.getenv("SPORTSDATA_API_KEY", "c1cb95854588435c9387a968dbdf1d34")
        if not odds_key:
            raise RuntimeError("ODDS_API_KEY must be provided")
        if not sportsdata_key:
            raise RuntimeError("SPORTSDATA_API_KEY must be provided")
        season_value = os.getenv("SPORTSDATA_SEASON")
        season = int(season_value) if season_value else None
        return cls(
            odds_api_key=odds_key,
            sportsdata_api_key=sportsdata_key,
            odds_region=os.getenv("ODDS_API_REGION", "us"),
            odds_market=os.getenv("ODDS_API_MARKET", "player_props"),
            odds_sport_key=os.getenv("ODDS_API_SPORT_KEY", "americanfootball_nfl"),
            sportsdata_season=season,
        )
