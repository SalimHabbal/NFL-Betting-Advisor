"""Historical matchup analysis."""
from __future__ import annotations

import logging
from typing import Dict, Optional

from ..models import BetLeg

LOGGER = logging.getLogger(__name__)


class HistoricalAnalyzer:
    """Analyzes historical team performance to adjust probabilities."""

    def __init__(self, head_to_head_record: Dict[str, int]):
        # Stores the win-loss record between two teams for quick lookups
        self.head_to_head_record = head_to_head_record

    def adjust_leg(self, leg: BetLeg, target_team: Optional[str] = None) -> Optional[float]:
        # Skips adjustments when no baseline probability is set
        if leg.baseline_probability is None:
            return None
        # Exits early when no target team or record is available
        if not target_team or target_team not in self.head_to_head_record:
            return None
        # Totals the historical sample size to guard against division by zero
        total_games = sum(self.head_to_head_record.values())
        if total_games == 0:
            return None
        team_wins = self.head_to_head_record.get(target_team, 0)
        win_rate = team_wins / total_games
        baseline = 0.5
        # Calculates a modest multiplier favoring teams with recent dominance
        adjustment = (win_rate - baseline) * 0.3
        multiplier = 1 + adjustment
        if abs(multiplier - 1.0) < 0.01:
            return None
        leg.notes.append(
            f"Historical edge: {target_team} {team_wins}-{total_games - team_wins} over opponent"
        )
        leg.notes.append(f"Historical multiplier applied: {multiplier:.2f}")
        return min(max(leg.baseline_probability * multiplier, 0.01), 0.99)
