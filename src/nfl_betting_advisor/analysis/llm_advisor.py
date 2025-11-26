"""LLM-based advisor using Google Gemini."""
from __future__ import annotations

import logging
import os
from typing import Optional

import google.generativeai as genai
from dotenv import load_dotenv

from ..models import EvaluationResult
from .ai_advisor import AnalysisContext, HeuristicAIAdvisor

LOGGER = logging.getLogger(__name__)

class GeminiAdvisor:
    """Hybrid advisor that uses HeuristicAIAdvisor for math and Gemini for reasoning."""

    def __init__(self, model_name: str = "gemini-1.5-flash"):
        load_dotenv()
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            LOGGER.warning("GEMINI_API_KEY not found. Falling back to heuristic-only mode.")
            self.client = None
        else:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel(model_name)
            self.client = True
        
        self.heuristic_advisor = HeuristicAIAdvisor()

    def _construct_prompt(self, context: AnalysisContext) -> str:
        """Builds the prompt for Gemini using the deterministic analysis context."""
        
        prompt = f"""
You are an expert NFL betting advisor. Your goal is to explain the value of a parlay bet based on PRE-CALCULATED mathematical data.
DO NOT recalculate probabilities. Trust the provided numbers.

PARLAY SUMMARY:
- Verdict: {context.verdict}
- Value Score: {context.overall_score:.2f} (Scale: -1.0 to 1.0)
- Expected Value: ${context.expected_value:.2f}
- Combined Hit Probability: {context.combined_probability:.2%}

LEGS DETAIL:
"""
        for leg in context.parlay.legs:
            scores = context.leg_scores.get(leg.leg_id, {})
            implied = scores.get("implied_prob", 0)
            adjusted = scores.get("adjusted_prob", 0)
            diff = adjusted - implied
            
            prompt += f"\nLeg {leg.leg_id}: {leg.description}\n"
            prompt += f"  - Implied Probability (Odds): {implied:.1%}\n"
            prompt += f"  - Adjusted Probability (Model): {adjusted:.1%}\n"
            prompt += f"  - Difference: {diff:+.1%}\n"
            if leg.notes:
                prompt += "  - Signals:\n"
                for note in leg.notes:
                    prompt += f"    * {note}\n"

        prompt += """
TASK:
Write a concise, professional analysis of this parlay.
1. Start with a clear "Recommendation" (e.g., "This is a strong play because...", "Proceed with caution due to...").
2. Analyze the key legs. Explain WHY the model adjusted the probability (refer to the signals like injuries or history).
3. Mention the Expected Value (EV) and whether it justifies the risk.
4. Keep it under 200 words. Use Markdown formatting (bolding key terms).
"""
        return prompt

    def evaluate(self, parlay) -> EvaluationResult:
        # 1. Run the deterministic math
        context = self.heuristic_advisor.get_analysis_context(parlay)
        
        # 2. If no API key, return the heuristic result directly
        if not self.client:
            return self.heuristic_advisor.evaluate(parlay)

        # 3. Call Gemini
        try:
            prompt = self._construct_prompt(context)
            response = self.model.generate_content(prompt)
            ai_rationale = response.text
        except Exception as exc:
            LOGGER.error("Gemini API failed: %s", exc)
            ai_rationale = "AI Analysis unavailable. Falling back to standard rationale.\n" + "\n".join(context.rationale)

        # 4. Return the result with the AI narrative
        # We replace the list of strings with a single formatted string in the first element for the UI to handle
        return EvaluationResult(
            overall_value_score=context.overall_score,
            verdict=context.verdict,
            expected_value=context.expected_value,
            combined_probability=context.combined_probability,
            rationale=[ai_rationale], # The UI will need to handle this being a long markdown string
            leg_breakdown=context.leg_scores,
        )
