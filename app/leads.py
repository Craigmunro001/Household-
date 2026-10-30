"""Lead records. Google Sheet when configured, otherwise a local JSONL file (dev)."""
import json
import logging
from pathlib import Path

from .content import BANDS, band_key, band_label

log = logging.getLogger("pinnacle.leads")

COLUMNS = [
    "Updated", "Phone", "Name", "Language", "Status", "Qualification", "Debt band", "Debt stated (R)",
    "Marital status", "Province", "Under debt review", "Callback preference", "Consent given", "Notes", "Created",
]
_BAND_LABELS = {band_key(b): band_label(b, "en") for b in BANDS}


def lead_row(s):
    a = s.answers
    return [
        s.updated_at, s.phone, s.name, s.lang, s.status, s.qualification.upper(),
        _BAND_LABELS.get(a.get("debt_band", ""), ""), a.get("debt_amount_stated", ""),
        a.get("marital", ""), a.get("province", ""), a.get("review", ""), a.get("callback", ""),
        s.consent_at, " | ".join(s.notes), s.created_at,
    ]


class GoogleSheetSink:
    def __init__(self, sheet_id, sa_info):
        import gspread

        gc = gspread.service_account_from_dict(sa_info)
        self.ws = gc.open_by_key(sheet_id).sheet1
        if self.ws.row_values(1) != COLUMNS:
            self.ws.update(range_name="A1", values=[COLUMNS])

    def upsert(self, s):
        row = lead_row(s)
        cell = self.ws.find(s.phone, in_column=2)
        if cell:
            self.ws.update(range_name=f"A{cell.row}", values=[row], raw=True)
        else:
            self.ws.append_row(row, value_input_option="RAW")


class JsonlSink:
    def __init__(self, path="data/leads.jsonl"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def upsert(self, s):
        with self.path.open("a") as f:
            f.write(json.dumps(dict(zip(COLUMNS, lead_row(s)))) + "\n")


def make_sink(settings):
    info = settings.google_sa_info
    if settings.sheet_id and info:
        try:
            return GoogleSheetSink(settings.sheet_id, info)
        except Exception:
            log.exception("Google Sheet unavailable, falling back to local file")
    return JsonlSink()
