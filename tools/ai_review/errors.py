class AIReviewError(RuntimeError):
    """Base error for the local AI review tool."""


class ConfigurationError(AIReviewError):
    """Raised when local configuration is missing or invalid."""


class ProviderError(AIReviewError):
    """Raised when a provider cannot produce a usable structured response."""


class ContractError(AIReviewError):
    """Raised when data violates a local JSON contract."""
