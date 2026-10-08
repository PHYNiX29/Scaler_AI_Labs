import sys
import os

# Ensure backend root is on path for relative imports in Vercel serverless environment
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from app.utils.seeder import seed_database

app = create_app("production")

with app.app_context():
    try:
        seed_database()
    except Exception as e:
        print(f"Notice: seeder note: {e}")
