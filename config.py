"""Application configuration for the cloud simulator."""

import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent


class Config:
    """Base configuration shared by local and deployed environments."""

    SECRET_KEY = os.environ.get("SECRET_KEY", "cloudsim-local-dev-key")
    DEBUG = os.environ.get("FLASK_DEBUG", "true").lower() == "true"

    DATABASE_PATH = Path(
        os.environ.get("DATABASE_PATH", BASE_DIR / "instance" / "cloud_simulator.db")
    )

    APP_NAME = "CloudSim"
    API_VERSION = "v1"

    INITIAL_NODE_COUNT = int(os.environ.get("INITIAL_NODE_COUNT", 3))
    MIN_NODE_COUNT = int(os.environ.get("MIN_NODE_COUNT", 2))
    MAX_NODE_COUNT = int(os.environ.get("MAX_NODE_COUNT", 8))
    NODE_CAPACITY = int(os.environ.get("NODE_CAPACITY", 100))
    METRICS_HISTORY_LIMIT = int(os.environ.get("METRICS_HISTORY_LIMIT", 36))

    SCALE_UP_THRESHOLD = int(os.environ.get("SCALE_UP_THRESHOLD", 80))
    SCALE_DOWN_THRESHOLD = int(os.environ.get("SCALE_DOWN_THRESHOLD", 20))
    SCALE_UP_CYCLES = int(os.environ.get("SCALE_UP_CYCLES", 2))
    SCALE_DOWN_CYCLES = int(os.environ.get("SCALE_DOWN_CYCLES", 4))
