
from abc import ABC, abstractmethod


class ISubscriptionModule(ABC):
    """Interface for application-specific subscription modules."""

    @abstractmethod
    def register(self, subscription_manager):
        """Register subscriptions with the given subscription manager."""
        pass