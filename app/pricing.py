"""Price book lookup. Figures come from config/fees.yaml only and are never calculated or interpolated here."""
from dataclasses import dataclass
from pathlib import Path

import yaml

DEFAULT_PATH = Path(__file__).resolve().parent.parent / "config" / "fees.yaml"


@dataclass(frozen=True)
class Quote:
    monthly: float
    months: int
    lo: int
    hi: int
    gauteng: bool
    generated: str

    @property
    def bracket_label(self):
        return f"R{self.lo:,} - R{self.hi:,}"


class PriceBook:
    def __init__(self, data):
        self.generated = str(data["generated"])
        self.decline_below = int(data["decline_below"])
        self.terms = list(data["terms"])
        self.tables = {True: data["gauteng"], False: data["outside_gauteng"]}
        first = self.tables[True][0][0]
        last = self.tables[True][-1][1]
        self.estimate_from, self.estimate_to = first, last

    def row(self, amount, gauteng):
        rows = self.tables[gauteng]
        for i, row in enumerate(rows):
            lo, hi = row[0], row[1]
            last = i == len(rows) - 1
            if amount >= lo and (amount < hi or (last and amount <= hi)):
                return row
        return None

    def can_quote(self, amount):
        return self.estimate_from <= amount <= self.estimate_to

    def quote(self, amount, gauteng, months):
        """The figure for the bracket the debt falls in, or None if out of range / unknown term."""
        if months not in self.terms:
            return None
        row = self.row(amount, gauteng)
        if row is None:
            return None
        return Quote(row[2 + self.terms.index(months)], months, row[0], row[1], gauteng, self.generated)


def load_pricebook(path=DEFAULT_PATH):
    try:
        with open(path) as f:
            return PriceBook(yaml.safe_load(f))
    except (FileNotFoundError, KeyError, TypeError):
        return None
