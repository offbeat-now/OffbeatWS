# app/ports/providers/payment_provider.py
from abc import ABC, abstractmethod
from typing import Optional

class PaymentProvider(ABC):
    """Abstract payment provider interface"""
    
    @abstractmethod
    async def create_payment_intent(self, amount: float, currency: str, payment_id: str, description: str) -> str:
        """Create a payment intent and return payment URL"""
        pass
    
    @abstractmethod
    async def verify_payment(self, payment_id: str) -> bool:
        """Verify if payment was successful"""
        pass
    
    @abstractmethod
    async def initiate_refund(self, payment_id: str) -> bool:
        """Initiate a refund for a payment"""
        pass