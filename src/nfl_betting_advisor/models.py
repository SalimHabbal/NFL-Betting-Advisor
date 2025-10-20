"""Core data models for the NFL betting advisor."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Dict


@dataclass
class Player:
    """Represents an NFL player relevant to a bet."""

    player_id: str
    name: str
    team: str
    position: str
    is_injured: bool = False
    injury_status: Optional[str] = None


@dataclass
class BetLeg:
    """A single bet leg within a parlay."""

    leg_id: str
    description: str
    odds_american: int
    market_type: str
    team: Optional[str] = None
    player: Optional[Player] = None
    baseline_probability: Optional[float] = None
    adjusted_probability: Optional[float] = None
    notes: List[str] = field(default_factory=list)
    metadata: Dict[str, str] = field(default_factory=dict)

    def implied_probability(self) -> float:
        """Return the implied probability from the American odds."""
        odds = self.odds_american
        if odds == 0:
            raise ValueError("American odds cannot be 0")
        if odds > 0:
            return 100 / (odds + 100)
        return -odds / (-odds + 100)


@dataclass
class Parlay:
    """A parlay consisting of multiple bet legs."""

    legs: List[BetLeg]
    stake: float

    def combined_probability(self) -> Optional[float]:
        """Return the combined probability if all legs have adjusted probabilities."""
        probability = 1.0
        for leg in self.legs:
            if leg.adjusted_probability is None:
                return None
            probability *= leg.adjusted_probability
        return probability

    def combined_decimal_odds(self) -> float:
        decimal_odds = 1.0
        for leg in self.legs:
            implied = leg.implied_probability()
            if implied == 0:
                raise ValueError("Leg implied probability cannot be 0")
            decimal_odds *= 1 / implied
        return decimal_odds

    def potential_payout(self) -> float:
        return self.stake * (self.combined_decimal_odds() - 1)


@dataclass
class EvaluationResult:
    overall_value_score: float
    verdict: str
    expected_value: Optional[float]
    combined_probability: Optional[float]
    rationale: List[str]
    leg_breakdown: Dict[str, Dict[str, float]]
