"""
brain - Learned prompt-understanding engine for ModelRouter
------------------------------------------------------------
A self-contained neural analyzer (pure numpy, no external APIs, no keyword rules).

Pipeline:
  text -> hashed subword n-grams (instruction + full-text bags) + structural signals
       -> ensemble of embedding-bag neural networks
       -> task distribution, complexity tier distribution, answer-length distribution
       -> PromptProfile (requirements the router must satisfy)
"""

from .analyzer import PromptAnalyzer, PromptProfile, get_analyzer

__all__ = ["PromptAnalyzer", "PromptProfile", "get_analyzer"]
