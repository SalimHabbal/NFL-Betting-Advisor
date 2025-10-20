"""Command-line interface for the NFL betting advisor."""
from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Any, Dict

from .config import APISettings
from .models import Parlay
from .parlay_evaluator import ParlayEvaluator, build_parlay_from_dict

LOGGER = logging.getLogger(__name__)


def _configure_logging(verbose: bool) -> None:
    # Sets the logging level based on the verbose flag
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(levelname)s: %(message)s")


def parse_args() -> argparse.Namespace:
    # Builds the argument parser for the CLI entrypoint
    parser = argparse.ArgumentParser(description="NFL parlay value advisor")
    parser.add_argument(
        "--parlay",
        type=Path,
        required=True,
        help="Path to a parlay definition JSON file",
    )
    parser.add_argument(
        "--stake",
        type=float,
        help="Override the stake amount defined in the parlay file",
    )
    parser.add_argument(
        "--disable-live-data",
        action="store_true",
        help="Skip API calls and only rely on data contained in the parlay file",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )
    return parser.parse_args()


def load_parlay(path: Path, stake_override: float | None = None) -> Parlay:
    # Loads the parlay JSON and optionally overrides the stake value
    data: Dict[str, Any] = json.loads(path.read_text())
    parlay = build_parlay_from_dict(data)
    if stake_override is not None:
        parlay.stake = stake_override
    return parlay


def display_results(result, parlay: Parlay) -> None:
    # Prints a formatted summary of the evaluation results
    print("=" * 60)
    print("Parlay Evaluation")
    print("=" * 60)
    header = f"{'Leg ID':<8} {'Description':<45} {'Imp Prob':>10} {'Adj Prob':>10}"
    print(header)
    print("-" * len(header))
    for leg in parlay.legs:
        breakdown = result.leg_breakdown.get(leg.leg_id, {})
        implied = breakdown.get("implied_prob", 0)
        adjusted = breakdown.get("adjusted_prob", leg.adjusted_probability or 0)
        desc = (leg.description[:42] + "...") if len(leg.description) > 45 else leg.description
        print(f"{leg.leg_id:<8} {desc:<45} {implied:>9.2%} {adjusted:>10.2%}")
    print()
    print(f"Overall Verdict: {result.verdict}")
    print(f"Value Score: {result.overall_value_score:.2f}")
    if result.expected_value is not None:
        print(f"Expected Value: ${result.expected_value:.2f}")
    if result.combined_probability is not None:
        print(f"Combined Hit Probability: {result.combined_probability:.2%}")
    if result.rationale:
        print("\nRationale:")
        for note in result.rationale:
            print(f" - {note}")


def main() -> None:
    # Orchestrates argument parsing, evaluation, and result display
    args = parse_args()
    _configure_logging(args.verbose)
    settings = APISettings.from_env()
    evaluator = ParlayEvaluator(settings=settings, use_live_data=not args.disable_live_data)
    parlay = load_parlay(args.parlay, args.stake)
    LOGGER.info("Loaded parlay with %d legs and stake %.2f", len(parlay.legs), parlay.stake)
    result = evaluator.evaluate(parlay)
    display_results(result, parlay)


if __name__ == "__main__":
    main()
