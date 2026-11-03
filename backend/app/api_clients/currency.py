"""Frankfurter API currency conversion client with caching and offline fallback."""
import logging
import re
import time
from typing import Any

import httpx

logger = logging.getLogger(__name__)

CURRENCY_SYMBOLS: dict[str, str] = {
    "USD": "$",
    "EUR": "€",
    "GBP": "£",
    "INR": "₹",
    "JPY": "¥",
    "CAD": "CA$",
    "AUD": "A$",
    "CHF": "CHF",
    "SGD": "S$",
    "AED": "AED",
    "THB": "฿",
    "IDR": "Rp",
    "MAD": "MAD",
}

SYMBOL_TO_CURRENCY: dict[str, str] = {
    "₹": "INR",
    "$": "USD",
    "€": "EUR",
    "£": "GBP",
    "¥": "JPY",
    "CA$": "CAD",
    "C$": "CAD",
    "A$": "AUD",
    "CHF": "CHF",
    "S$": "SGD",
    "฿": "THB",
    "RP": "IDR",
    "RS": "INR",
    "RS.": "INR",
}

# Reliable market baseline exchange rates (relative to 1.0 USD)
FALLBACK_RATES_FROM_USD: dict[str, float] = {
    "USD": 1.0,
    "EUR": 0.92,
    "GBP": 0.79,
    "INR": 83.5,
    "JPY": 155.0,
    "CAD": 1.36,
    "AUD": 1.52,
    "CHF": 0.90,
    "SGD": 1.35,
    "AED": 3.67,
    "THB": 36.0,
    "IDR": 16000.0,
    "MAD": 10.1,
}


class FrankfurterClient:
    """Client for Frankfurter Currency API (https://api.frankfurter.app)."""

    BASE_URLS = [
        "https://api.frankfurter.app/latest",
        "https://api.frankfurter.dev/v1/latest",
    ]
    CACHE_TTL_SECONDS = 3600  # 1 hour cache

    def __init__(self) -> None:
        self._rates_cache: dict[str, dict[str, float]] = {}
        self._cache_timestamp: dict[str, float] = {}

    def get_rates(self, base: str = "USD") -> tuple[dict[str, float], bool]:
        """Fetch latest exchange rates for the given base currency.

        Returns (rates_dict, is_live).
        """
        base = (base or "USD").upper()
        now = time.time()

        # Check in-memory cache
        if (
            base in self._rates_cache
            and (now - self._cache_timestamp.get(base, 0)) < self.CACHE_TTL_SECONDS
        ):
            return self._rates_cache[base], True

        # Try live Frankfurter endpoints
        for base_url in self.BASE_URLS:
            try:
                with httpx.Client(timeout=3.0) as client:
                    resp = client.get(base_url, params={"from": base})
                    if resp.status_code == 200:
                        data = resp.json()
                        rates = data.get("rates", {})
                        rates[base] = 1.0
                        self._rates_cache[base] = rates
                        self._cache_timestamp[base] = now
                        logger.info("Fetched live Frankfurter exchange rates for %s", base)
                        return rates, True
            except Exception as e:
                logger.debug("Frankfurter live API attempt failed (%s): %s", base_url, e)

        # Fallback rates calculation
        logger.info("Using reliable fallback exchange rates for %s", base)
        usd_rate_of_base = FALLBACK_RATES_FROM_USD.get(base, 1.0)
        rates_from_base: dict[str, float] = {}
        for curr, usd_rate in FALLBACK_RATES_FROM_USD.items():
            # curr_rate_from_base = (usd_rate / usd_rate_of_base)
            rates_from_base[curr] = round(usd_rate / usd_rate_of_base, 4)
        rates_from_base[base] = 1.0

        return rates_from_base, False

    def convert(
        self,
        amount: float | int,
        from_curr: str,
        to_curr: str,
    ) -> dict[str, Any]:
        """Converts an amount from one currency to another."""
        from_curr = (from_curr or "USD").upper()
        to_curr = (to_curr or "USD").upper()
        amount_num = float(amount or 0)

        if from_curr == to_curr or amount_num == 0:
            return {
                "converted_amount": round(amount_num),
                "original_amount": amount_num,
                "from_currency": from_curr,
                "to_currency": to_curr,
                "rate": 1.0,
                "is_live": True,
            }

        rates, is_live = self.get_rates(base=from_curr)
        if to_curr in rates:
            rate = rates[to_curr]
            converted = amount_num * rate
        else:
            # Cross rate via USD fallback
            base_usd = FALLBACK_RATES_FROM_USD.get(from_curr, 1.0)
            target_usd = FALLBACK_RATES_FROM_USD.get(to_curr, 1.0)
            rate = target_usd / base_usd
            converted = amount_num * rate
            is_live = False

        # Apply currency-appropriate rounding
        if to_curr in ("JPY", "IDR"):
            rounded_amount = int(round(converted))
        elif to_curr == "INR":
            rounded_amount = int(round(converted / 10.0) * 10) if converted >= 100 else int(round(converted))
        else:
            rounded_amount = int(round(converted))

        return {
            "converted_amount": rounded_amount,
            "original_amount": amount_num,
            "from_currency": from_curr,
            "to_currency": to_curr,
            "rate": round(rate, 4),
            "is_live": is_live,
        }

    def detect_currency_and_amount(
        self,
        text: Any,
        default_currency: str = "USD",
    ) -> tuple[int | None, str]:
        """Detects numeric amount and source currency from text like '$580', '€450', '₹50,000' or '580 USD'."""
        if text is None:
            return None, default_currency
        if isinstance(text, (int, float)):
            return int(text), default_currency

        s = str(text).strip()
        upper_s = s.upper()

        detected_curr = default_currency
        # 1. Check currency symbols
        for sym, curr in SYMBOL_TO_CURRENCY.items():
            if sym in upper_s:
                detected_curr = curr
                break

        # 2. Check 3-letter currency codes
        for curr in FALLBACK_RATES_FROM_USD:
            if re.search(r"\b" + curr + r"\b", upper_s):
                detected_curr = curr
                break

        # 3. Extract numbers
        cleaned = re.sub(r"[^\d.]+", "", s)
        try:
            val = float(cleaned) if cleaned else None
            return (int(val) if val is not None else None), detected_curr
        except ValueError:
            return None, detected_curr

    def parse_and_convert(
        self,
        price_val: Any,
        target_currency: str,
        default_source_currency: str = "USD",
    ) -> dict[str, Any]:
        """Convenience method to parse price text, convert to target currency, and format."""
        target_currency = (target_currency or "USD").upper()
        amount, src_curr = self.detect_currency_and_amount(price_val, default_source_currency)
        if amount is None or amount <= 0:
            return {
                "converted_amount": None,
                "formatted": "Check availability",
                "target_currency": target_currency,
                "is_live": False,
            }

        res = self.convert(amount, src_curr, target_currency)
        sym = CURRENCY_SYMBOLS.get(target_currency, target_currency + " ")
        fmt = f"{sym}{res['converted_amount']:,}"

        return {
            "converted_amount": res["converted_amount"],
            "formatted": fmt,
            "original_amount": amount,
            "original_currency": src_curr,
            "target_currency": target_currency,
            "rate": res["rate"],
            "is_live": res["is_live"],
        }


currency_client = FrankfurterClient()

