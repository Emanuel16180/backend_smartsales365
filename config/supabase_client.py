# config/supabase_client.py
import os
from supabase import create_client, Client
from django.conf import settings

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL y SUPABASE_KEY deben estar en el .env")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)