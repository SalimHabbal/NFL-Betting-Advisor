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
from .analysis.llm_advisor import GeminiAdvisor
from .ui import RichPresenter

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
    parser.add_argument(
        "--ai-model",
        choices=["heuristic", "hybrid"],
        default="hybrid",
        help="Choose the AI model: 'heuristic' (rules-only) or 'hybrid' (Gemini LLM)",
    )
    return parser.parse_args()


def load_parlay(path: Path, stake_override: float | None = None) -> Parlay:
    # Loads the parlay JSON and optionally overrides the stake value
    data: Dict[str, Any] = json.loads(path.read_text())
    parlay = build_parlay_from_dict(data)
    if stake_override is not None:
        parlay.stake = stake_override
    return parlay


def main() -> None:
    # Orchestrates argument parsing, evaluation, and result display
    args = parse_args()
    _configure_logging(args.verbose)
    
    settings = APISettings.from_env()
    
    # Initialize Evaluator
    evaluator = ParlayEvaluator(settings=settings, use_live_data=not args.disable_live_data)
    
    # Swap out the advisor if Hybrid mode is selected
    if args.ai_model == "hybrid":
        LOGGER.info("Initializing Hybrid AI (Gemini)...")
        evaluator.advisor = GeminiAdvisor()
    
    parlay = load_parlay(args.parlay, args.stake)
    LOGGER.info("Loaded parlay with %d legs and stake %.2f", len(parlay.legs), parlay.stake)
    
    result = evaluator.evaluate(parlay)
    
    # Use Rich UI
    presenter = RichPresenter()
    presenter.display_parlay_evaluation(parlay, result)


if __name__ == "__main__":
    main()
