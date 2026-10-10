import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'bulk_certificates.db'}")

# Storage configuration
STORAGE_DIR = Path(os.getenv("STORAGE_DIR", str(BASE_DIR / "storage" / "certificates")))
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

# Application metadata
APP_TITLE = "Bulk Certificate Generator API"
APP_DESCRIPTION = (
    "Production-ready backend API that accepts bulk certificate generation requests, "
    "processes them asynchronously with failure isolation, and serves generated certificates."
)
APP_VERSION = "1.0.0"

# Defaults
DEFAULT_ORGANIZATION = "Excellence Certification Academy"
DEFAULT_SIGNATORY_NAME = "Director of Certification"
DEFAULT_SIGNATORY_TITLE = "Authorized Representative"
