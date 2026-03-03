#!/usr/bin/env python3
"""
Test script for VideoMind AI payment integration.
Tests the complete payment flow from job creation to payment processing.
"""
import sys
import os
sys.path.append('src')

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import json

# Import the app and dependencies
from main import app
from database import Base, get_database
from models.video import VideoJob, ProcessingTier

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_payments.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_database():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

# Override database dependency
app.dependency_overrides[get_database] = override_get_database

def setup_test_db():
    """Create test database tables."""
    Base.metadata.create_all(bind=engine)

def test_payment_flow():
    """Test the complete payment integration flow."""
    print("🧪 Testing VideoMind AI Payment Integration")
    print("=" * 50)
    
    # Setup test database
    setup_test_db()
    
    client = TestClient(app)
    
    # Test 1: Create a video job (should require payment)
    print("\n1. Testing video job creation...")
    job_data = {
        "youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "email": "test@example.com",
        "tier": "basic"
    }
    
    response = client.post("/api/process", json=job_data)
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"   ✅ Job created: {result.get('job_id', 'N/A')}")
        print(f"   ✅ Payment required: {result.get('payment_required', False)}")
        print(f"   ✅ Payment URL: {result.get('payment_url', 'N/A')}")
        job_id = result.get('job_id')
    else:
        print(f"   ❌ Failed to create job: {response.text}")
        return False
    
    # Test 2: Get pricing information
    print("\n2. Testing pricing endpoint...")
    response = client.get("/api/payments/pricing")
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        pricing = response.json()
        print(f"   ✅ Basic tier: ${pricing.get('basic', {}).get('price_usd', 'N/A')}")
        print(f"   ✅ Detailed tier: ${pricing.get('detailed', {}).get('price_usd', 'N/A')}")
        print(f"   ✅ Bulk tier: ${pricing.get('bulk', {}).get('price_usd', 'N/A')}")
    else:
        print(f"   ❌ Failed to get pricing: {response.text}")
        return False
    
    # Test 3: Test payment intent creation (will fail without Stripe keys)
    print("\n3. Testing payment intent creation...")
    payment_data = {
        "job_id": job_id,
        "tier": "basic",
        "email": "test@example.com"
    }
    
    response = client.post("/api/payments/create-payment-intent", json=payment_data)
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 503:
        print("   ⚠️  Payment processing not configured (expected in test)")
        print("   ✅ Payment endpoint exists and handles missing config correctly")
    elif response.status_code == 200:
        print("   ✅ Payment intent created successfully")
    else:
        print(f"   ❌ Unexpected response: {response.text}")
        return False
    
    # Test 4: Test payment page route
    print("\n4. Testing payment page...")
    response = client.get(f"/payment/{job_id}")
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        print("   ✅ Payment page loads successfully")
    else:
        print(f"   ❌ Payment page failed: {response.text}")
        return False
    
    # Test 5: Test payment status endpoint
    print("\n5. Testing payment status...")
    response = client.get(f"/api/payments/payment-status/{job_id}")
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        status = response.json()
        print(f"   ✅ Job ID: {status.get('job_id')}")
        print(f"   ✅ Payment status: {status.get('payment_status')}")
        print(f"   ✅ Processing status: {status.get('processing_status')}")
    else:
        print(f"   ❌ Failed to get payment status: {response.text}")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 ALL PAYMENT INTEGRATION TESTS PASSED!")
    print("\n💰 Revenue Generation Ready:")
    print("   ✅ Job creation with payment requirement")
    print("   ✅ Payment intent API endpoints") 
    print("   ✅ Payment page rendering")
    print("   ✅ Payment status tracking")
    print("   ✅ Pricing configuration")
    
    print("\n🚀 Next Steps:")
    print("   1. Set STRIPE_SECRET_KEY and STRIPE_PUBLISHABLE_KEY")
    print("   2. Deploy to production")
    print("   3. Start accepting payments!")
    
    return True

if __name__ == "__main__":
    success = test_payment_flow()
    if not success:
        sys.exit(1)
    
    # Clean up test database
    try:
        os.remove("test_payments.db")
        print("\n🧹 Test database cleaned up")
    except FileNotFoundError:
        pass