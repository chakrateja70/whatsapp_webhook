from __future__ import annotations
import os
from dotenv import load_dotenv

load_dotenv(override=True)


class Settings:
    """Application settings loaded from environment variables."""

    def __init__(self):
        self.WEBHOOK_VERIFY_TOKEN: str = self._get_required("WEBHOOK_VERIFY_TOKEN")

        # Routing: phone_number_id → downstream webhook URL
        # Add more pairs here as new services are onboarded.
        self.PPA_PHONE_NUMBER_ID: str = os.getenv("PPA_PHONE_NUMBER_ID", "").strip()
        self.PPA_WEBHOOK_URL: str = os.getenv("PPA_WEBHOOK_URL", "").strip()

        self.APMC_PHONE_NUMBER_ID: str = os.getenv("APMC_PHONE_NUMBER_ID", "").strip()
        self.APMC_WEBHOOK_URL: str = os.getenv("APMC_WEBHOOK_URL", "").strip()

    @staticmethod
    def _get_required(key: str) -> str:
        value = os.getenv(key)
        if not value:
            raise ValueError(
                f"{key} not found in environment variables. Please check your .env file."
            )
        return value


xsettings = Settings()
