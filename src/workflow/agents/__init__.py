"""
AI Agents Package - Intelligent workflow analysis and suggestions

This package provides AI-powered agents that analyze workflow processes
and suggest intelligent transitions based on patterns, rules, and context.

Agents:
- BaseAgent: Abstract base class defining agent interface
- GenericAgent: General-purpose agent using heuristics
- PatternAgent: Suggests transitions based on historical patterns
- RuleAgent: Applies business rules for transition suggestions
"""

from .base_agent import BaseAgent
from .generic_agent import GenericAgent
from .pattern_agent import PatternAgent
from .rule_agent import RuleAgent

__all__ = [
    "BaseAgent",
    "GenericAgent",
    "PatternAgent",
    "RuleAgent",
]
