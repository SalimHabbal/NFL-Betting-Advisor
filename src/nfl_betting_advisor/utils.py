"""Utility helpers for odds conversion and statistics."""
from __future__ import annotations

import math
from typing import Iterable, List


def american_to_decimal(odds: int) -> float:
    if odds == 0:
        raise ValueError("American odds cannot be zero")
    if odds > 0:
        return (odds / 100) + 1
    return (100 / abs(odds)) + 1


def decimal_to_american(decimal: float) -> int:
    if decimal <= 1:
        raise ValueError("Decimal odds must be greater than 1")
    if decimal >= 2:
        return int((decimal - 1) * 100)
    return int(-100 / (decimal - 1))


def combine_probabilities(probabilities: Iterable[float]) -> float:
    total = 1.0
    for prob in probabilities:
        total *= prob
    return total


def expected_value(probability: float, decimal_odds: float, stake: float) -> float:
    return (probability * (decimal_odds - 1) * stake) - ((1 - probability) * stake)


def z_score(values: List[float]) -> List[float]:
    if not values:
        return []
    mean = sum(values) / len(values)
    variance = sum((value - mean) ** 2 for value in values) / len(values)
    std_dev = math.sqrt(variance) if variance > 0 else 1
    return [(value - mean) / std_dev for value in values]
