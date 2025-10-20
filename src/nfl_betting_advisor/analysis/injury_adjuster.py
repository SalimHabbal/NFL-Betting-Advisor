"""Injury adjustments for player-based bets."""
from __future__ import annotations

import logging
from typing import Dict, List, Optional

from ..models import BetLeg

LOGGER = logging.getLogger(__name__)

KEY_DEFENSIVE_POSITIONS = {"CB", "DB", "FS", "SS", "S", "LB", "DE", "DT", "EDGE"}
OFFENSIVE_SKILL_POSITIONS = {"QB", "RB", "WR", "TE"}


class InjuryAdjuster:
    """Adjusts bet probabilities based on injury reports."""

    def __init__(self, injuries: List[Dict]):
        # Caches the raw injury feed for later filtering
        self.injuries = injuries

    def _is_key_defender(self, injury: Dict) -> bool:
        # Identifies defensive players whose absence boosts offensive bets
        return injury.get("Position") in KEY_DEFENSIVE_POSITIONS

    def _is_offensive_star(self, injury: Dict) -> bool:
        # Flags offensive skill players whose injuries hurt their own team's props
        return injury.get("Position") in OFFENSIVE_SKILL_POSITIONS

    def adjust_leg(self, leg: BetLeg, opponent_team: Optional[str] = None) -> Optional[float]:
        """Return the adjustment multiplier for a bet leg."""
        # Skips legs without a baseline probability to avoid compounding None
        if leg.baseline_probability is None:
            LOGGER.debug("Skipping injury adjustment for leg %s: no baseline probability", leg.leg_id)
            return None

        multiplier = 1.0
        adjustments: List[str] = []
        # Scans each injury entry and accumulates multipliers as signals
        for injury in self.injuries:
            team = injury.get("Team")
            if opponent_team and team != opponent_team:
                continue
            if injury.get("Status") in {"Out", "Doubtful"}:
                if self._is_key_defender(injury) and leg.player and leg.player.team != team:
                    multiplier += 0.05
                    adjustments.append(
                        f"Opponent missing key defender {injury.get('Name')} ({injury.get('Position')})"
                    )
                elif self._is_offensive_star(injury) and leg.player and leg.player.team == team:
                    multiplier -= 0.05
                    adjustments.append(
                        f"{leg.player.name}'s teammate {injury.get('Name')} ({injury.get('Position')}) is out"
                    )
        multiplier = max(0.05, multiplier)
        if abs(multiplier - 1.0) > 1e-6:
            # Stores the adjustment notes for downstream rationale reporting
            leg.notes.extend(adjustments)
            adjusted = leg.baseline_probability * multiplier
            leg.notes.append(f"Injury multiplier applied: {multiplier:.2f}")
            return min(max(adjusted, 0.01), 0.99)
        return None
