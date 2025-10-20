"""Parlay evaluation orchestration."""
from __future__ import annotations

import logging
from functools import lru_cache
from typing import Dict, Iterable, Optional

from .analysis.ai_advisor import HeuristicAIAdvisor
from .analysis.historical_analyzer import HistoricalAnalyzer
from .analysis.injury_adjuster import InjuryAdjuster
from .config import APISettings
from .data_sources.odds_api import OddsAPIClient
from .data_sources.sportsdata_api import SportsDataClient
from .models import BetLeg, EvaluationResult, Parlay, Player

LOGGER = logging.getLogger(__name__)


class ParlayEvaluator:
    """Coordinates data fetching, adjustments, and AI scoring."""

    def __init__(self, settings: Optional[APISettings] = None, use_live_data: bool = True):
        self.settings = settings or APISettings.from_env()
        self.use_live_data = use_live_data
        self.odds_client = OddsAPIClient(self.settings)
        self.sportsdata_client = SportsDataClient(self.settings)
        self.advisor = HeuristicAIAdvisor()
        self._player_directory: Dict[str, Player] = {}
        self._injury_adjuster: Optional[InjuryAdjuster] = None

    def _load_players(self) -> None:
        if self._player_directory or not self.use_live_data:
            return
        try:
            players = self.sportsdata_client.get_players()
        except Exception as exc:  # pylint: disable=broad-except
            LOGGER.warning("Failed to load players from SportsDataIO: %s", exc)
            return
        for player in players:
            player_id = str(player.get("PlayerID"))
            name = player.get("Name")
            team = player.get("Team")
            position = player.get("Position", "")
            if not name or not team:
                continue
            self._player_directory[name.lower()] = Player(
                player_id=player_id,
                name=name,
                team=team,
                position=position,
            )

    def _load_injuries(self) -> None:
        if self._injury_adjuster or not self.use_live_data:
            return
        try:
            injuries = self.sportsdata_client.get_injuries()
        except Exception as exc:  # pylint: disable=broad-except
            LOGGER.warning("Failed to load injuries from SportsDataIO: %s", exc)
            injuries = []
        self._injury_adjuster = InjuryAdjuster(injuries)

    def _attach_players(self, legs: Iterable[BetLeg]) -> None:
        self._load_players()
        for leg in legs:
            player_name = leg.metadata.get("player_name") if leg.metadata else None
            if player_name and leg.player is None:
                player = self._player_directory.get(player_name.lower())
                if player:
                    leg.player = player
                else:
                    LOGGER.debug("Player %s not found in directory", player_name)

    @lru_cache(maxsize=16)
    def _get_head_to_head(self, team_a: str, team_b: str) -> Dict[str, int]:
        try:
            return self.sportsdata_client.get_head_to_head_record(team_a, team_b)
        except Exception as exc:  # pylint: disable=broad-except
            LOGGER.warning("Failed to fetch head-to-head record for %s vs %s: %s", team_a, team_b, exc)
            return {team_a: 0, team_b: 0}

    def _apply_adjustments(self, parlay: Parlay) -> None:
        self._attach_players(parlay.legs)
        self._load_injuries()
        for leg in parlay.legs:
            if leg.baseline_probability is None:
                leg.baseline_probability = leg.implied_probability()
            opponent_team = leg.metadata.get("opponent_team") if leg.metadata else None
            target_team = leg.team or (leg.player.team if leg.player else None)
            if self._injury_adjuster and opponent_team:
                adjusted = self._injury_adjuster.adjust_leg(leg, opponent_team=opponent_team)
                if adjusted is not None:
                    leg.adjusted_probability = adjusted
                    leg.baseline_probability = leg.adjusted_probability
            if leg.adjusted_probability is None:
                leg.adjusted_probability = leg.baseline_probability
            if target_team and opponent_team and self.use_live_data:
                record = self._get_head_to_head(target_team, opponent_team)
                historical = HistoricalAnalyzer(record)
                adjusted = historical.adjust_leg(leg, target_team)
                if adjusted is not None:
                    leg.adjusted_probability = adjusted
                    leg.baseline_probability = leg.adjusted_probability
            if self.use_live_data and leg.metadata.get("player_name"):
                self._annotate_market_price(leg)

    def _annotate_market_price(self, leg: BetLeg) -> None:
        try:
            market = leg.metadata.get("market_key") if leg.metadata else None
            best_price = self.odds_client.get_best_player_prop_odds(
                leg.metadata.get("player_name", ""), market=market
            )
        except Exception as exc:  # pylint: disable=broad-except
            LOGGER.debug("Failed to fetch market price for %s: %s", leg.leg_id, exc)
            return
        if not best_price:
            return
        market_odds = best_price.get("price")
        if market_odds is None:
            return
        leg.notes.append(
            "Best price available: {bookmaker} {market} at {price:+d}".format(
                bookmaker=best_price.get("bookmaker", "unknown"),
                market=best_price.get("market", "market"),
                price=int(market_odds),
            )
        )

    def evaluate(self, parlay: Parlay) -> EvaluationResult:
        self._apply_adjustments(parlay)
        return self.advisor.evaluate(parlay)


def build_parlay_from_dict(data: Dict) -> Parlay:
    legs = []
    for entry in data["legs"]:
        leg = BetLeg(
            leg_id=entry["id"],
            description=entry["description"],
            odds_american=entry["odds"],
            market_type=entry.get("market", "custom"),
            team=entry.get("team"),
            baseline_probability=entry.get("baseline_probability"),
            metadata=entry.get("metadata", {}),
        )
        legs.append(leg)
    return Parlay(legs=legs, stake=data.get("stake", 1.0))
