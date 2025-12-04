"""Tiered LLM routing based on query complexity."""

from dataclasses import dataclass

from support_agent.agent.classifier import Complexity, Intent
from support_agent.config import get_settings


@dataclass
class ModelConfig:
    """Configuration for a specific model tier."""

    model: str
    max_tokens: int
    temperature: float
    description: str


class ModelRouter:
    """Routes queries to appropriate LLM based on complexity."""

    def __init__(self):
        """Initialize model router with settings."""
        self.settings = get_settings()

        # Define model tiers
        self.tiers = {
            Complexity.SIMPLE: ModelConfig(
                model=self.settings.simple_model,
                max_tokens=500,
                temperature=0.3,
                description="Fast model for simple lookups and FAQ responses",
            ),
            Complexity.MEDIUM: ModelConfig(
                model=self.settings.medium_model,
                max_tokens=1000,
                temperature=0.5,
                description="Balanced model for moderate complexity queries",
            ),
            Complexity.COMPLEX: ModelConfig(
                model=self.settings.complex_model,
                max_tokens=2000,
                temperature=0.7,
                description="Advanced model for complex reasoning and escalations",
            ),
        }

        # Intent-based overrides (some intents always need specific tiers)
        self.intent_overrides = {
            Intent.COMPLAINT: Complexity.COMPLEX,
            Intent.REFUND_REQUEST: Complexity.COMPLEX,
            Intent.ESCALATION_REQUEST: Complexity.COMPLEX,
        }

    def get_model_config(
        self,
        complexity: Complexity,
        intent: Intent | None = None,
    ) -> ModelConfig:
        """Get model configuration for given complexity and intent.

        Args:
            complexity: Query complexity level.
            intent: Optional intent for override checking.

        Returns:
            ModelConfig for the appropriate tier.
        """
        # Check for intent-based overrides
        if intent and intent in self.intent_overrides:
            effective_complexity = self.intent_overrides[intent]
            # Only upgrade, never downgrade
            if self._complexity_rank(effective_complexity) > self._complexity_rank(complexity):
                complexity = effective_complexity

        return self.tiers[complexity]

    def _complexity_rank(self, complexity: Complexity) -> int:
        """Get numeric rank for complexity comparison.

        Args:
            complexity: Complexity level.

        Returns:
            Numeric rank (higher = more complex).
        """
        ranks = {
            Complexity.SIMPLE: 1,
            Complexity.MEDIUM: 2,
            Complexity.COMPLEX: 3,
        }
        return ranks.get(complexity, 2)

    def estimate_cost(self, complexity: Complexity, input_tokens: int) -> dict:
        """Estimate cost for a query at given complexity.

        Args:
            complexity: Query complexity.
            input_tokens: Estimated input tokens.

        Returns:
            Cost estimate dictionary.
        """
        # Approximate pricing (as of late 2024)
        pricing = {
            "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},  # per 1K tokens
            "gpt-4o": {"input": 0.0025, "output": 0.01},
        }

        config = self.tiers[complexity]
        model_prices = pricing.get(config.model, pricing["gpt-4o-mini"])

        input_cost = (input_tokens / 1000) * model_prices["input"]
        output_cost = (config.max_tokens / 1000) * model_prices["output"]

        return {
            "model": config.model,
            "input_tokens": input_tokens,
            "max_output_tokens": config.max_tokens,
            "estimated_input_cost": round(input_cost, 6),
            "estimated_output_cost": round(output_cost, 6),
            "estimated_total_cost": round(input_cost + output_cost, 6),
        }

    def get_routing_stats(self) -> dict:
        """Get routing configuration stats.

        Returns:
            Dictionary with routing configuration info.
        """
        return {
            "tiers": {
                complexity.value: {
                    "model": config.model,
                    "max_tokens": config.max_tokens,
                    "temperature": config.temperature,
                    "description": config.description,
                }
                for complexity, config in self.tiers.items()
            },
            "intent_overrides": {
                intent.value: complexity.value
                for intent, complexity in self.intent_overrides.items()
            },
        }
