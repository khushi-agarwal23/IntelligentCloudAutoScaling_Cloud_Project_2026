import uvicorn
import os
import sys

# Ensure src/backend is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.config import settings

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    print(f"Starting {settings.PROJECT_NAME} on http://0.0.0.0:{port} ...")
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)
