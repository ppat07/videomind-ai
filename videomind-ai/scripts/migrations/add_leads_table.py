"""
Migration: add `leads` table for email lead capture.
Run: python3 scripts/migrations/add_leads_table.py
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from database import engine
from models.leads import Lead  # noqa: F401 — registers table with Base
from database import Base

Base.metadata.create_all(bind=engine, tables=[Lead.__table__])
print("✅ leads table created (or already exists)")
