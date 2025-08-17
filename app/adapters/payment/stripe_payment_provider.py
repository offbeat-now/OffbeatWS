# app/adapters/providers/stripe_payment_provider.py
import stripe
import os
from typing import Optional, Dict
from fastapi import HTTPException, status

from app.ports.providers.payment_provider import PaymentProvider
from app.core.config import get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

class StripePaymentProvider(PaymentProvider):
    """Stripe implementation of PaymentProvider"""
    
    def __init__(self):
        self.settings = get_settings()
        stripe.api_key = self.settings.stripe_secret_key
        self.webhook_secret = self.settings.stripe_webhook_secret
        self.currency = self.settings.stripe_currency.lower()
        
        # Verify configuration
        if not stripe.api_key:
            raise ValueError("Stripe secret key not configured")
    
    async def create_payment_intent(
        self, 
        amount: float, 
        payment_id: str,
        description: str,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """Create a payment intent and return client secret and payment details"""
        try:
            # Convert amount to smallest currency unit (cents for USD)
            amount_in_cents = int(amount * 100)
            
            intent = stripe.PaymentIntent.create(
                amount=amount_in_cents,
                currency=self.currency,
                description=description,
                metadata={
                    "payment_id": payment_id,
                    **({"metadata": metadata} if metadata else {})
                },
                automatic_payment_methods={
                    "enabled": True,
                },
            )
            
            return {
                "client_secret": intent.client_secret,
                "payment_intent_id": intent.id,
                "amount": amount,
                "currency": self.currency,
                "status": intent.status
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating payment intent: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=str(e.user_message) if hasattr(e, 'user_message') else "Payment processing failed"
            )
        except Exception as e:
            logger.error(f"Error creating payment intent: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create payment intent"
            )
    
    async def verify_payment(self, payment_intent_id: str) -> bool:
        """Verify if payment was successful"""
        try:
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            return intent.status == "succeeded"
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error verifying payment: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Error verifying payment: {str(e)}")
            return False
    
    async def initiate_refund(self, payment_intent_id: str) -> bool:
        """Initiate a refund for a payment"""
        try:
            refund = stripe.Refund.create(
                payment_intent=payment_intent_id
            )
            return refund.status == "succeeded"
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error initiating refund: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Error initiating refund: {str(e)}")
            return False
    
    async def handle_webhook(self, payload: bytes, sig_header: str) -> Dict:
        """Handle Stripe webhook events"""
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, self.webhook_secret
            )
            
            # Handle specific event types
            if event.type == 'payment_intent.succeeded':
                payment_intent = event.data.object
                return {
                    "status": "success",
                    "payment_intent_id": payment_intent.id,
                    "amount": payment_intent.amount / 100,  # Convert back to dollars
                    "currency": payment_intent.currency,
                    "metadata": payment_intent.metadata
                }
            elif event.type == 'payment_intent.payment_failed':
                payment_intent = event.data.object
                return {
                    "status": "failed",
                    "payment_intent_id": payment_intent.id,
                    "error": payment_intent.last_payment_error or "Payment failed"
                }
            
            return {"status": "unhandled_event", "event_type": event.type}
            
        except ValueError as e:
            logger.error(f"Invalid Stripe webhook payload: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid payload"
            )
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Invalid Stripe webhook signature: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid signature"
            )
        except Exception as e:
            logger.error(f"Error handling Stripe webhook: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Webhook processing failed"
            )