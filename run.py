"""Arranque local: python run.py  ->  http://localhost:5000"""

import os

from app import create_app

app = create_app(os.environ.get("APP_ENV", "development"))

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", "5000")))
