from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

REFERENCE_DATE = date(2026, 9, 21)


@dataclass(frozen=True)
class Order:
    order_id: str
    item: str
    amount: str
    purchased_on: date
    window_days: int = 30

    @property
    def age_days(self) -> int:
        return (REFERENCE_DATE - self.purchased_on).days

    @property
    def within_window(self) -> bool:
        return self.age_days <= self.window_days


DEFAULT_ORDERS: dict[str, Order] = {
    "ORD-1001": Order(
        order_id="ORD-1001",
        item="headphones",
        amount="89.00",
        purchased_on=REFERENCE_DATE - timedelta(days=5),
    ),
    "ORD-2099": Order(
        order_id="ORD-2099",
        item="camera",
        amount="240.00",
        purchased_on=REFERENCE_DATE - timedelta(days=90),
    ),
}

DEFAULT_ORDER_ID = "ORD-1001"
