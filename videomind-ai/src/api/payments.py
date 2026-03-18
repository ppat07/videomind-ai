"""
Payment processing endpoints for VideoMind AI.
Handles Stripe payment intents and webhooks for video processing purchases.
"""
from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime
from pydantic import BaseModel
from typing import Dict, Any
import json
import os

# Import Stripe properly
try:
    import stripe
    print("✅ Stripe imported successfully")
except ImportError as e:
    print(f"❌ Failed to import Stripe: {e}")
    stripe = None

from database import get_database
from models.video import VideoJob, ProcessingTier
from models.subscription import ProSubscriber, ConversionEvent
from config import settings

# Configure Stripe with better error handling
def setup_stripe():
    global stripe
    if not stripe:
        print("❌ Stripe not available")
        return False
    
    try:
        stripe_secret = settings.stripe_secret_key or os.getenv("STRIPE_SECRET_KEY")
        if stripe_secret:
            stripe.api_key = stripe_secret
            print(f"✅ Stripe configured with key: {stripe_secret[:12]}...")
            return True
        else:
            print("❌ No Stripe secret key found")
            return False
    except Exception as e:
        print(f"❌ Stripe setup error: {e}")
        return False

# Setup Stripe on import
stripe_ready = setup_stripe()

router = APIRouter()

# Pricing configuration (in cents)
PRICING_TIERS = {
    ProcessingTier.BASIC: 300,     # $3.00 - transcript + summary + 5 Q&As
    ProcessingTier.DETAILED: 500,  # $5.00 - enhanced + 10 Q&As
    ProcessingTier.BULK: 200,      # $2.00 - bulk discount (5+ videos)
}

class PaymentIntentRequest(BaseModel):
    """Request to create a payment intent."""
    job_id: str
    tier: ProcessingTier
    email: str

class PaymentIntentResponse(BaseModel):
    """Response containing payment intent details."""
    client_secret: str
    amount: int
    currency: str = "usd"

@router.post("/create-payment-intent", response_model=PaymentIntentResponse)
async def create_payment_intent(
    request: PaymentIntentRequest,
    db: Session = Depends(get_database)
):
    """
    Create a Stripe payment intent for video processing.
    
    Args:
        request: Payment intent request with job_id and tier
        db: Database session
        
    Returns:
        PaymentIntentResponse with client_secret for frontend
        
    Raises:
        HTTPException: If Stripe not configured or job not found
    """
    if not settings.stripe_secret_key:
        raise HTTPException(
            status_code=503, 
            detail="Payment processing is not configured"
        )
    
    # Verify job exists
    job = db.query(VideoJob).filter(VideoJob.id == request.job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Get pricing for tier
    amount = PRICING_TIERS.get(request.tier, PRICING_TIERS[ProcessingTier.BASIC])
    
    try:
        # Create Stripe payment intent
        intent = stripe.PaymentIntent.create(
            amount=amount,
            currency="usd",
            metadata={
                "job_id": request.job_id,
                "email": request.email,
                "tier": request.tier.value,
                "service": "video_processing"
            },
            receipt_email=request.email,
            description=f"VideoMind AI - {request.tier.value.title()} video processing"
        )
        
        # Update job with payment intent ID
        job.payment_intent_id = intent.id
        job.cost = amount / 100  # Store in dollars
        db.commit()
        
        return PaymentIntentResponse(
            client_secret=intent.client_secret,
            amount=amount
        )
        
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=f"Payment error: {str(e)}")

@router.post("/create-checkout-session")
async def create_checkout_session(request: Request):
    """Create Stripe checkout session for products."""
    global stripe, stripe_ready
    
    print(f"🔧 Checkout session request - Stripe ready: {stripe_ready}")
    
    if not stripe or not stripe_ready:
        print("❌ Stripe not available or not configured")
        raise HTTPException(status_code=503, detail="Payment system not available")
    
    # Get form data
    form = await request.form()
    price_id = form.get("price_id")
    mode = form.get("mode", "payment")
    
    print(f"📝 Form data - Price ID: {price_id}, Mode: {mode}")
    
    if not price_id:
        raise HTTPException(status_code=400, detail="Price ID required")
    
    try:
        print("🚀 Creating Stripe checkout session...")
        
        # Re-setup Stripe just in case
        stripe_secret = settings.stripe_secret_key or os.getenv("STRIPE_SECRET_KEY")
        if stripe_secret:
            stripe.api_key = stripe_secret
        
        checkout_session = stripe.checkout.Session.create(
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            mode=mode,
            success_url=f"{request.url.scheme}://{request.url.netloc}/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{request.url.scheme}://{request.url.netloc}/checkout",
        )
        
        print(f"✅ Stripe session created: {checkout_session.id}")
        
        # Redirect to Stripe checkout
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url=checkout_session.url, status_code=303)
        
    except Exception as e:
        print(f"❌ Stripe session error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Payment error: {str(e)}")


@router.post("/create-portal-session")
async def create_portal_session(request: Request):
    """Create customer portal session."""
    if not settings.stripe_secret_key:
        raise HTTPException(status_code=503, detail="Payments not configured")
    
    # Get form data
    form = await request.form()
    session_id = form.get("session_id")
    
    if not session_id:
        raise HTTPException(status_code=400, detail="Session ID required")
    
    try:
        # Get the checkout session to find the customer
        checkout_session = stripe.checkout.Session.retrieve(session_id)
        
        # Create portal session
        portal_session = stripe.billing_portal.Session.create(
            customer=checkout_session.customer,
            return_url=f"{request.url.scheme}://{request.url.netloc}",
        )
        
        # Redirect to customer portal
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url=portal_session.url, status_code=303)
        
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=f"Stripe error: {str(e)}")


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_database)
):
    """
    Handle Stripe webhook events for payment processing.
    
    Args:
        request: Raw webhook request from Stripe
        background_tasks: FastAPI background tasks
        db: Database session
        
    Returns:
        Success response for Stripe
        
    Raises:
        HTTPException: If webhook validation fails
    """
    if not settings.stripe_webhook_secret:
        raise HTTPException(
            status_code=503,
            detail="Webhook validation is not configured"
        )
    
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    
    try:
        # Verify webhook signature
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.stripe_webhook_secret
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    # Handle payment success
    if event["type"] == "payment_intent.succeeded":
        background_tasks.add_task(
            handle_payment_success,
            event["data"]["object"],
            db
        )
    
    # Handle payment failure
    elif event["type"] == "payment_intent.payment_failed":
        background_tasks.add_task(
            handle_payment_failure,
            event["data"]["object"],
            db
        )
    
    # Handle checkout session completion (for PDF products and subscriptions)
    elif event["type"] == "checkout.session.completed":
        background_tasks.add_task(
            handle_checkout_completion,
            event["data"]["object"],
            db
        )

    # Handle new subscription
    elif event["type"] == "customer.subscription.created":
        background_tasks.add_task(
            handle_subscription_created,
            event["data"]["object"],
            db
        )

    # Handle subscription cancellation/deletion
    elif event["type"] in ("customer.subscription.deleted", "customer.subscription.updated"):
        background_tasks.add_task(
            handle_subscription_changed,
            event["data"]["object"],
            db
        )

    return {"status": "success"}

async def handle_payment_success(payment_intent: Dict[str, Any], db: Session):
    """
    Handle successful payment by starting video processing.
    
    Args:
        payment_intent: Stripe payment intent object
        db: Database session
    """
    job_id = payment_intent["metadata"].get("job_id")
    if not job_id:
        return
    
    # Update job status to paid and trigger processing
    job = db.query(VideoJob).filter(VideoJob.id == job_id).first()
    if job:
        job.status = "paid"  # Custom status indicating payment received
        db.commit()
        
        # Import here to avoid circular imports
        from services.video_processor import start_processing
        await start_processing(job_id, db)

async def handle_payment_failure(payment_intent: Dict[str, Any], db: Session):
    """
    Handle failed payment by updating job status.
    
    Args:
        payment_intent: Stripe payment intent object
        db: Database session
    """
    job_id = payment_intent["metadata"].get("job_id")
    if not job_id:
        return
    
    job = db.query(VideoJob).filter(VideoJob.id == job_id).first()
    if job:
        job.status = "payment_failed"
        job.error_message = "Payment processing failed"
        db.commit()

async def handle_checkout_completion(session: Dict[str, Any], db: Session):
    """
    Handle completed checkout session for PDF products.
    
    Args:
        session: Stripe checkout session object
        db: Database session
    """
    try:
        # Check if this is a PDF product purchase
        product_type = session.get('metadata', {}).get('product_type')
        if product_type == 'pdf':
            customer_email = session['customer_details']['email']
            customer_name = session['customer_details']['name'] or "Valued Customer"
            amount = session['amount_total'] / 100  # Convert cents to dollars
            
            print(f"📧 PDF purchase detected: {customer_email} paid ${amount}")
            
            # For now, just log the sale - PDF delivery can be implemented later
            # This ensures we capture revenue even without email delivery
            print(f"💰 REVENUE: ${amount} from PDF sale to {customer_email}")
            
            # TODO: Implement actual PDF email delivery
            # send_pdf_via_email(customer_email, customer_name)
            
    except Exception as e:
        print(f"❌ Error processing PDF checkout: {str(e)}")
        # Don't raise exception - we don't want to break the webhook

@router.get("/pricing")
async def get_pricing():
    """
    Get current pricing information for all tiers.
    
    Returns:
        Dict with pricing for each tier in dollars
    """
    return {
        tier.value: {
            "price_usd": f"{amount / 100:.2f}",
            "price_cents": amount,
            "features": get_tier_features(tier)
        }
        for tier, amount in PRICING_TIERS.items()
    }

def get_tier_features(tier: ProcessingTier) -> Dict[str, Any]:
    """Get feature list for a processing tier."""
    features = {
        ProcessingTier.BASIC: [
            "Full transcript with timestamps",
            "AI-generated summary",
            "5 practice Q&As",
            "JSON and PDF downloads"
        ],
        ProcessingTier.DETAILED: [
            "Full transcript with timestamps", 
            "Enhanced AI summary with insights",
            "10 practice Q&As with explanations",
            "Key concept extraction",
            "Learning objectives",
            "JSON, PDF, and text downloads"
        ],
        ProcessingTier.BULK: [
            "Same as Basic tier",
            "Bulk discount for 5+ videos",
            "Priority processing",
            "API access included"
        ]
    }
    return features.get(tier, [])

@router.get("/payment-status/{job_id}")
async def get_payment_status(job_id: str, db: Session = Depends(get_database)):
    """
    Get payment status for a specific job.
    
    Args:
        job_id: Video job identifier
        db: Database session
        
    Returns:
        Payment status information
        
    Raises:
        HTTPException: If job not found
    """
    job = db.query(VideoJob).filter(VideoJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    payment_status = "unpaid"
    if job.payment_intent_id:
        try:
            intent = stripe.PaymentIntent.retrieve(job.payment_intent_id)
            payment_status = intent.status
        except stripe.error.StripeError:
            payment_status = "error"
    
    return {
        "job_id": job_id,
        "payment_status": payment_status,
        "amount": job.cost,
        "tier": job.tier,
        "processing_status": job.status
    }


# ---------------------------------------------------------------------------
# Subscription event handlers
# ---------------------------------------------------------------------------

async def handle_subscription_created(subscription: Dict[str, Any], db: Session):
    """Record a new Pro subscriber when their Stripe subscription is created."""
    try:
        customer_id = subscription.get("customer")
        subscription_id = subscription.get("id")
        status = subscription.get("status", "")

        if not customer_id or status not in ("active", "trialing"):
            return

        # Retrieve customer email from Stripe
        customer = stripe.Customer.retrieve(customer_id)
        email = customer.get("email", "").lower()
        if not email:
            return

        # Upsert subscriber record
        existing = db.query(ProSubscriber).filter(
            ProSubscriber.stripe_subscription_id == subscription_id
        ).first()
        if existing:
            existing.active = True
            existing.cancelled_at = None
        else:
            db.add(ProSubscriber(
                email=email,
                stripe_customer_id=customer_id,
                stripe_subscription_id=subscription_id,
                active=True,
            ))

        # Log conversion event
        db.add(ConversionEvent(email=email, event="subscribed"))
        db.commit()
        print(f"✅ Pro subscriber recorded: {email}")
    except Exception as e:
        print(f"❌ handle_subscription_created error: {e}")


async def handle_subscription_changed(subscription: Dict[str, Any], db: Session):
    """Update subscriber record when a subscription is cancelled or changed."""
    try:
        subscription_id = subscription.get("id")
        status = subscription.get("status", "")
        active = status in ("active", "trialing")

        record = db.query(ProSubscriber).filter(
            ProSubscriber.stripe_subscription_id == subscription_id
        ).first()
        if record:
            record.active = active
            if not active:
                record.cancelled_at = datetime.utcnow()
            db.commit()
            print(f"✅ Subscription {subscription_id} updated: active={active}")
    except Exception as e:
        print(f"❌ handle_subscription_changed error: {e}")


# ---------------------------------------------------------------------------
# Pro status check endpoint
# ---------------------------------------------------------------------------

@router.get("/pro-status")
async def check_pro_status(email: str, db: Session = Depends(get_database)):
    """Check whether an email has an active Pro subscription."""
    email = email.lower().strip()
    subscriber = db.query(ProSubscriber).filter(
        ProSubscriber.email == email,
        ProSubscriber.active == True,  # noqa: E712
    ).first()
    return {"email": email, "is_pro": subscriber is not None}


# ---------------------------------------------------------------------------
# Free tier usage endpoint
# ---------------------------------------------------------------------------

@router.get("/free-usage")
async def get_free_usage(email: str, db: Session = Depends(get_database)):
    """Return how many free videos this email has used this month and the limit."""
    from models.subscription import FreeTierUsage
    from datetime import datetime

    email = email.lower().strip()
    year_month = datetime.utcnow().strftime("%Y-%m")
    FREE_LIMIT = 3

    usage = db.query(FreeTierUsage).filter(
        FreeTierUsage.email == email,
        FreeTierUsage.year_month == year_month,
    ).first()

    used = usage.count if usage else 0
    return {"email": email, "used": used, "limit": FREE_LIMIT, "remaining": max(0, FREE_LIMIT - used)}


# ---------------------------------------------------------------------------
# Anonymous conversion event logging (best-effort, no auth required)
# ---------------------------------------------------------------------------

class EventLogRequest(BaseModel):
    event: str
    email: str = ""
    metadata: str = ""


@router.post("/log-event")
async def log_conversion_event(body: EventLogRequest, db: Session = Depends(get_database)):
    """Log a frontend conversion event (pricing_viewed, etc.)."""
    try:
        db.add(ConversionEvent(
            email=body.email.lower().strip() if body.email else None,
            event=body.event,
            metadata_=body.metadata or None,
        ))
        db.commit()
    except Exception:
        pass  # Never fail on analytics
    return {"ok": True}