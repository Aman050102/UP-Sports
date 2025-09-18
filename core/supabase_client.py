# core/supabase_client.py
# Single place to create Supabase clients for Django views.
import os
from supabase import create_client, Client

SUPABASE_URL = os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY") or os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")  # server-only (admin)

if not SUPABASE_URL or not (SUPABASE_ANON_KEY or SUPABASE_SERVICE_ROLE_KEY):
    raise RuntimeError("Please set SUPABASE_URL and SUPABASE_ANON_KEY (and optionally SUPABASE_SERVICE_ROLE_KEY)")

# Public client (use this for normal RPC calls like check-in/out)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY or SUPABASE_SERVICE_ROLE_KEY)

# Admin client (service role) – required for admin_set_scan_code
supabase_service: Client | None = None
if SUPABASE_SERVICE_ROLE_KEY:
    supabase_service = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
