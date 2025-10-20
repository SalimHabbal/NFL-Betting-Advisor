# NFL Betting Advisor

A command-line tool for analyzing NFL parlay bets using live odds, injury reports, and historical matchup data. The advisor leverages The Odds API and SportsDataIO to contextualize each bet leg and produces an AI-inspired judgement on the overall value of a parlay.

## Features

- Import parlays from JSON and compute implied probabilities for each leg.
- Optional live data integration with:
  - [The Odds API](https://the-odds-api.com/) for the best available betting lines.
  - [SportsDataIO](https://sportsdata.io/) for player injuries, rosters, and historical team performance.
- Automatic probability adjustments that account for:
  - Key opponent injuries (e.g., missing defensive backs boosting a quarterback prop).
  - Historical head-to-head records (e.g., Team B dominating Team A at home).
- Heuristic AI analysis summarizing value, expected return, and rationale.
- Rich terminal output summarizing leg-by-leg adjustments and the final recommendation.

## Quick Start

### 1. Clone & install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .  # or set PYTHONPATH=src when running modules locally
```

### 2. Configure API keys

The project reads API keys from environment variables. A `.env` file in the project root is supported.

```ini
# .env
ODDS_API_KEY=9c85626ecf9eefc72a33034a22ff7ece
SPORTSDATA_API_KEY=c1cb95854588435c9387a968dbdf1d34
SPORTSDATA_SEASON=2023  # optional override
```

> The repository defaults to the provided demo keys. Replace them with your own production keys for extended usage.

### 3. Prepare a parlay description

Use the sample file under `samples/parlay_example.json` as a template. Each leg can include:

- `id`: unique identifier.
- `description`: human-friendly summary of the bet.
- `odds`: American odds (e.g., `-115` or `110` for +110).
- `team`: shorthand team code for the player or team targeted by the leg.
- `baseline_probability`: your subjective probability before adjustments. If omitted, the implied probability from the odds is used.
- `metadata.player_name`: matches SportsDataIO player records for injury lookups.
- `metadata.opponent_team`: opponent team code to drive historical and injury adjustments.

### 4. Run the advisor

```bash
nfl-betting-advisor --parlay samples/parlay_example.json --verbose
```

Add `--disable-live-data` to operate entirely on the data supplied in the JSON file (no API calls).

## Usage Guide

1. **Prepare environment variables**
   - Copy `.env.example` to `.env` (`cp .env.example .env`).
   - Replace the demo API keys with your personal keys. These are loaded automatically when you run the CLI.
   - Optional: set `SPORTSDATA_SEASON`, `ODDS_API_REGION`, `ODDS_API_MARKET`, or `ODDS_API_SPORT_KEY` to tune the data sources without touching code.

2. **Craft or import a parlay**
   - Start from `samples/parlay_example.json` and adjust each leg’s `description`, `odds`, and optional `baseline_probability`.
   - Include `metadata.player_name` and `metadata.opponent_team` when you want the evaluator to factor in injury reports and opponent history.
   - Add a `stake` field to represent how much you plan to wager; override it at runtime with `--stake` if needed.

3. **Run the CLI**
   ```bash
   nfl-betting-advisor --parlay path/to/parlay.json
   ```
   - Use `--stake 25` to temporarily change the wager amount outlined in the JSON file.
   - Append `--disable-live-data` if you are offline, rate-limited, or experimenting with hypothetical adjustments.
   - Add `--verbose` to surface detailed logging about every adjustment and API call.

4. **Interpret the results**
   - The leg table shows the implied probability from the odds alongside the adjusted probability after accounting for context.
   - `Value Score` reflects how favorable the overall parlay appears; higher positive scores indicate stronger value.
   - `Expected Value` (when available) converts the evaluation into a dollar figure based on the stake.
   - Review the `Rationale` bullets to see which injuries, historical trends, or heuristics influenced the verdict.

## Output

The CLI prints a rich table showing the implied vs. adjusted probabilities for each leg, the combined expected value, and an overall verdict (e.g., *Strong Value*, *Moderate Value*, *Neutral*, *High Risk*). Detailed rationale lines highlight which injuries or historical records influenced the evaluation.

## Extensibility

- Expand `samples/` with your own parlays.
- Implement alternative AI strategies by extending `HeuristicAIAdvisor`.
- Integrate caching or databases if you plan to run large batches of analyses.

## Disclaimer

This tool is for informational and entertainment purposes only. Betting involves risk. Use responsibly and within legal jurisdictions.
