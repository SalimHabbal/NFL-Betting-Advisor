# NFL Betting Advisor

A command-line tool for analyzing NFL parlay bets using live odds, injury reports, and historical matchup data. The advisor leverages The Odds API and SportsDataIO to contextualize each bet leg and produces an AI-inspired judgement on the overall value of a parlay.

## Features

- **Hybrid AI Analysis**: Combines deterministic math (for consistency) with **Google Gemini** (for reasoning) to provide professional-grade betting advice.
- **Rich Terminal UI**: Beautiful, color-coded tables and panels for easy reading.
- **Smart Adjustments**:
  - Automatic probability adjustments for key injuries.
  - Historical head-to-head weighting.
- **Live Data**: Integrates with The Odds API and SportsDataIO.

## Quick Start

### 1. Clone & install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

### 2. Configure API keys

The project reads API keys from environment variables. A `.env` file in the project root is supported.

```ini
# .env
ODDS_API_KEY=your_odds_api_key
SPORTSDATA_API_KEY=your_sportsdata_key
GEMINI_API_KEY=your_gemini_key  # Optional: For AI reasoning
```

> **Note**: If you don't provide a `GEMINI_API_KEY`, the tool will fallback to a rules-based heuristic mode.

### 3. Run the advisor

```bash
nfl-betting-advisor --parlay samples/parlay_example.json
```

## Usage Guide

### Command Line Options

- `--parlay <path>`: Path to the parlay JSON file (Required).
- `--stake <amount>`: Override the wager amount.
- `--ai-model <hybrid|heuristic>`: Choose between Gemini LLM (hybrid) or simple rules (heuristic). Default is `hybrid`.
- `--disable-live-data`: Run in offline mode using only data in the JSON file.
- `--verbose`: Enable debug logging.

### Example Output

The tool produces a rich table showing the "Implied Probability" (from the odds) vs the "Adjusted Probability" (from the model), followed by an AI-generated analysis.

```text
Verdict: Strong Value
Value Score: 0.18
Expected Value: $12.50

AI Analysis:
"This is a strong play. Josh Allen has historically dominated the Dolphins defense (Adjusted: +5%), 
and the injury to Miami's starting safety significantly boosts his deep ball potential..."
```

## Parlay Schema Reference

See `samples/parlay_example.json` for a template.

### Team codes

Use official NFL abbreviations (e.g., BUF, MIA, KC, SF).

## Disclaimer

This tool is for informational and entertainment purposes only. Betting involves risk. Use responsibly and within legal jurisdictions.
