"""
PDF Auto-Delivery System for VideoMind AI
Handles PDF product fulfillment after successful Stripe payments
"""

from fastapi import APIRouter, Request, HTTPException
import stripe
import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from pathlib import Path
import logging
from jinja2 import Template

router = APIRouter()

# Configure Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

# Email configuration
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = os.getenv("SMTP_USER", "noreply@videomind-ai.com") 
SMTP_PASS = os.getenv("SMTP_PASSWORD")

logger = logging.getLogger(__name__)

def create_pdf_from_markdown():
    """Convert markdown to PDF using pandoc or similar"""
    import subprocess
    
    # Read the markdown content
    with open("products/video-ai-training-data-mastery.md", "r") as f:
        content = f.read()
    
    # Use pandoc to convert to PDF (requires pandoc installation)
    try:
        result = subprocess.run([
            "pandoc", 
            "products/video-ai-training-data-mastery.md",
            "-o", "products/video-ai-training-data-mastery.pdf",
            "--pdf-engine=wkhtmltopdf",
            "--css=products/pdf-style.css"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            return "products/video-ai-training-data-mastery.pdf"
        else:
            logger.error(f"PDF generation failed: {result.stderr}")
            return None
    except FileNotFoundError:
        logger.error("pandoc not found. Install with: brew install pandoc wkhtmltopdf")
        return None

def send_pdf_email(customer_email: str, customer_name: str, pdf_path: str):
    """Send PDF via email to customer"""
    
    if not SMTP_PASS:
        logger.error("SMTP password not configured")
        return False
    
    try:
        # Create email message
        msg = MIMEMultipart()
        msg['From'] = SMTP_USER
        msg['To'] = customer_email
        msg['Subject'] = "Your VideoMind AI Training Data Mastery Guide"
        
        # Email body template
        body_template = Template("""
        Hi {{ customer_name }},

        Thank you for purchasing the Video AI Training Data Mastery guide!

        You now have access to:
        ✅ Complete 100+ page guide to video AI training data
        ✅ Ready-to-use code templates and scripts  
        ✅ Legal framework and compliance guidelines
        ✅ Case studies of $100K+ AI model sales
        ✅ Free VideoMind AI trial (10 videos) - Code: MASTERY2026
        ✅ 50% off first month Pro subscription

        Redeem your bonuses at: https://videomind-ai.com/pdf-bonus

        Questions? Reply to this email for direct support.

        Best,
        VideoMind AI Team

        P.S. Watch for our upcoming "AI Video Processing Templates" marketplace launching next month!
        """)
        
        body = body_template.render(customer_name=customer_name)
        msg.attach(MIMEText(body, 'plain'))
        
        # Attach PDF
        if os.path.exists(pdf_path):
            with open(pdf_path, "rb") as f:
                attach = MIMEApplication(f.read(), _subtype='pdf')
                attach.add_header('Content-Disposition', 'attachment', 
                                filename='Video-AI-Training-Data-Mastery.pdf')
                msg.attach(attach)
        
        # Send email
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)
        server.quit()
        
        logger.info(f"PDF delivered successfully to {customer_email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send PDF email: {str(e)}")
        return False

@router.post("/webhook/stripe")
async def handle_stripe_webhook(request: Request):
    """Handle Stripe webhook for successful payments"""
    
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, os.getenv("STRIPE_WEBHOOK_SECRET")
        )
    except ValueError:
        logger.error("Invalid payload")
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        logger.error("Invalid signature")
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    # Handle successful payment
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        
        # Check if this is a PDF purchase
        if session.get('metadata', {}).get('product_type') == 'pdf':
            customer_email = session['customer_details']['email']
            customer_name = session['customer_details']['name'] or "Valued Customer"
            
            # Generate PDF if needed
            pdf_path = "products/video-ai-training-data-mastery.pdf"
            if not os.path.exists(pdf_path):
                pdf_path = create_pdf_from_markdown()
            
            if pdf_path:
                # Send PDF via email
                success = send_pdf_email(customer_email, customer_name, pdf_path)
                
                if success:
                    logger.info(f"PDF product delivered to {customer_email}")
                    
                    # Log revenue
                    amount = session['amount_total'] / 100  # Convert cents to dollars
                    logger.info(f"REVENUE: ${amount} from PDF sale to {customer_email}")
                    
                else:
                    logger.error(f"Failed to deliver PDF to {customer_email}")
            else:
                logger.error("PDF generation failed")
    
    return {"status": "success"}

# Test endpoint for manual PDF generation
@router.post("/admin/generate-pdf")
async def manual_pdf_generation():
    """Manual PDF generation for testing"""
    pdf_path = create_pdf_from_markdown()
    
    if pdf_path:
        return {"status": "success", "pdf_path": pdf_path}
    else:
        raise HTTPException(status_code=500, detail="PDF generation failed")

@router.post("/admin/test-email")  
async def test_email_delivery(email: str = "test@example.com"):
    """Test email delivery system"""
    
    pdf_path = "products/video-ai-training-data-mastery.pdf"
    if not os.path.exists(pdf_path):
        pdf_path = create_pdf_from_markdown()
    
    if pdf_path:
        success = send_pdf_email(email, "Test Customer", pdf_path)
        return {"status": "success" if success else "failed", "email": email}
    else:
        raise HTTPException(status_code=500, detail="PDF not available")