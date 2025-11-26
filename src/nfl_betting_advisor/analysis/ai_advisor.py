"""Heuristic AI advisor for parlay evaluation."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from statistics import mean
from typing import Dict, List, Optional

from ..models import BetLeg, EvaluationResult, Parlay
from ..utils import expected_value

LOGGER = logging.getLogger(__name__)


@dataclass
class AnalysisContext:
    """Holds the raw signals and data used for AI analysis."""
    parlay: Parlay
    leg_scores: Dict[str, Dict[str, float]]
    overall_score: float
    expected_value: Optional[float]
    combined_probability: Optional[float]
    rationale: List[str]
    verdict: str


class HeuristicAIAdvisor:
    """A lightweight rules-based advisor that simulates AI judgement."""

    def __init__(self) -> None:
        # Defines weighting for each signal contributing to the final value score
        self.weights = {
            "ev_weight": 0.5,
            "injury_weight": 0.2,
            "history_weight": 0.15,
            "market_weight": 0.15,
        }

    def _score_leg(self, leg: BetLeg) -> Dict[str, float]:
        # Derives implied, baseline, and adjusted probabilities for this leg
        implied_prob = leg.implied_probability()
        baseline = leg.baseline_probability or implied_prob
        adjusted = leg.adjusted_probability or baseline
        # Calculates how much the adjustment changes the value of the leg
        ev_contribution = (adjusted - implied_prob) / implied_prob if implied_prob else 0
        injury_signal = 0.0
        history_signal = 0.0
        market_signal = 0.0
        # Parses notes to gather qualitative signals for each leg
        for note in leg.notes:
            lowered = note.lower()
            if "injury multiplier" in lowered or "missing" in lowered:
                injury_signal += 0.1
            if "historical" in lowered:
                history_signal += 0.1
            if "line movement" in lowered or "best price" in lowered:
                market_signal += 0.05
        return {
            "ev": ev_contribution,
            "injury": injury_signal,
            "history": history_signal,
            "market": market_signal,
            "implied_prob": implied_prob,
            "adjusted_prob": adjusted,
        }

    def evaluate(self, parlay: Parlay) -> EvaluationResult:
        # Collects per-leg scoring context and calculates parlay-wide stats
        leg_scores: Dict[str, Dict[str, float]] = {}
        combined_probability = parlay.combined_probability()
        combined_decimal_odds = parlay.combined_decimal_odds()
        expected_val = (
            expected_value(combined_probability, combined_decimal_odds, parlay.stake)
            if combined_probability is not None
            else None
        )
        value_scores: List[float] = []
        rationale: List[str] = []
        # Scores each leg and builds the narrative rationale
        for leg in parlay.legs:
            scores = self._score_leg(leg)
            leg_scores[leg.leg_id] = scores
            value_score = (
                scores["ev"] * self.weights["ev_weight"]
                + scores["injury"] * self.weights["injury_weight"]
                + scores["history"] * self.weights["history_weight"]
                + scores["market"] * self.weights["market_weight"]
            )
            value_scores.append(value_score)
            rationale.append(
                f"Leg {leg.leg_id} {leg.description}: adjusted probability {scores['adjusted_prob']:.2%}"
            )
            if leg.notes:
                rationale.extend(f"  - {note}" for note in leg.notes)

        overall_score = mean(value_scores) if value_scores else 0
        if expected_val is not None:
            rationale.append(f"Combined expected value: ${expected_val:.2f}")
        if combined_probability is not None:
            rationale.append(f"Parlay hit probability: {combined_probability:.2%}")

        # Converts the aggregated score into a human-readable verdict
        if overall_score > 0.15 and (expected_val or 0) > 0:
            verdict = "Strong Value"
        elif overall_score > 0.05:
            verdict = "Moderate Value"
        elif overall_score < -0.1:
            verdict = "High Risk"
        else:
            verdict = "Neutral"

        LOGGER.debug(
            "Parlay evaluation -> score: %.3f, verdict: %s, expected value: %s",
            overall_score,
            verdict,
            expected_val,
        )

        return EvaluationResult(
            overall_value_score=overall_score,
            verdict=verdict,
            expected_value=expected_val,
            combined_probability=combined_probability,
            rationale=rationale,
            leg_breakdown=leg_scores,
        )

    def get_analysis_context(self, parlay: Parlay) -> AnalysisContext:
        """Returns the raw analysis data without wrapping it in an EvaluationResult."""
        # This reuses the logic from evaluate but returns the intermediate state
        # Ideally, evaluate() should call this, but for minimal refactoring risk,
        # we will duplicate the orchestration logic slightly or have evaluate call this.
        # Let's have evaluate call this to ensure consistency.
        
        leg_scores: Dict[str, Dict[str, float]] = {}
        combined_probability = parlay.combined_probability()
        combined_decimal_odds = parlay.combined_decimal_odds()
        expected_val = (
            expected_value(combined_probability, combined_decimal_odds, parlay.stake)
            if combined_probability is not None
            else None
        )
        value_scores: List[float] = []
        rationale: List[str] = []
        
        for leg in parlay.legs:
            scores = self._score_leg(leg)
            leg_scores[leg.leg_id] = scores
            value_score = (
                scores["ev"] * self.weights["ev_weight"]
                + scores["injury"] * self.weights["injury_weight"]
                + scores["history"] * self.weights["history_weight"]
                + scores["market"] * self.weights["market_weight"]
            )
            value_scores.append(value_score)
            rationale.append(
                f"Leg {leg.leg_id} {leg.description}: adjusted probability {scores['adjusted_prob']:.2%}"
            )
            if leg.notes:
                rationale.extend(f"  - {note}" for note in leg.notes)

        overall_score = mean(value_scores) if value_scores else 0
        
        if overall_score > 0.15 and (expected_val or 0) > 0:
            verdict = "Strong Value"
        elif overall_score > 0.05:
            verdict = "Moderate Value"
        elif overall_score < -0.1:
            verdict = "High Risk"
        else:
            verdict = "Neutral"
            
        return AnalysisContext(
            parlay=parlay,
            leg_scores=leg_scores,
            overall_score=overall_score,
            expected_value=expected_val,
            combined_probability=combined_probability,
            rationale=rationale,
            verdict=verdict
        )
