import json
import os
from dataclasses import dataclass
from functools import lru_cache


@dataclass(frozen=True)
class Settings:
    wa_token: str
    wa_phone_number_id: str
    wa_verify_token: str
    wa_app_secret: str
    wa_api_version: str
    anthropic_api_key: str
    model: str
    sheet_id: str
    google_sa: str
    notify_to: tuple
    notify_from: str
    smtp_host: str
    smtp_port: int
    smtp_user: str
    smtp_password: str
    db_path: str
    human_delay: float
    dev_mode: bool

    @property
    def google_sa_info(self):
        raw = self.google_sa.strip()
        if not raw:
            return None
        if raw.startswith("{"):
            return json.loads(raw)
        with open(raw) as f:
            return json.load(f)


@lru_cache
def get_settings() -> Settings:
    e = os.environ.get
    return Settings(
        wa_token=e("WHATSAPP_TOKEN", ""),
        wa_phone_number_id=e("WHATSAPP_PHONE_NUMBER_ID", ""),
        wa_verify_token=e("WHATSAPP_VERIFY_TOKEN", ""),
        wa_app_secret=e("WHATSAPP_APP_SECRET", ""),
        wa_api_version=e("WHATSAPP_API_VERSION", "v25.0"),
        anthropic_api_key=e("ANTHROPIC_API_KEY", ""),
        model=e("CLAUDE_MODEL", "claude-opus-5-5"),
        sheet_id=e("GOOGLE_SHEET_ID", ""),
        google_sa=e("GOOGLE_SERVICE_ACCOUNT_JSON", ""),
        notify_to=tuple(x.strip() for x in e("NOTIFY_TO", "").split(",") if x.strip()),
        notify_from=e("NOTIFY_FROM", e("SMTP_USER", "")),
        smtp_host=e("SMTP_HOST", ""),
        smtp_port=int(e("SMTP_PORT", "587")),
        smtp_user=e("SMTP_USER", ""),
        smtp_password=e("SMTP_PASSWORD", ""),
        db_path=e("DB_PATH", "data/sessions.sqlite3"),
        human_delay=float(e("HUMAN_DELAY_SECONDS", "1.5")),
        dev_mode=e("DEV_MODE", "0") == "1",
    )
