#!/usr/bin/env python3
"""
Scrape https://m.karaba.co.kr car listings (pages 1–2750) to CSV.

CSV columns:
    seq,title,year,km,transmission,price,image_url,safe_url
"""
import csv
import re
import sys
import time
from html import unescape
from pathlib import Path

import requests

BASE_PAGE = "https://m.karaba.co.kr/?m=sale&s=list&p={page}"
SAFE_URL = "https://photo5.autosale.co.kr/safe.php?seq={seq}&t=kimko"
UA = (
    "Mozilla/5.0 (Linux; Android 10; Pixel 5) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/115.0.0.0 Mobile Safari/537.36"
)

# pre‑compiled regexes for speed
RE_CARD = re.compile(
    r'<a href="/\?m=sale&s=detail&seq=(\d{10})".+?'
    r'<img[^>]+src="([^"]+)"[^>]*>.+?'
    r'<div class="cartitle">(.*?)</div>.+?'
    r'<div class="carinfo">(.*?)</div>.+?'
    r'<div><div class="money">(.*?)</div>',
    re.S,
)
RE_INFO = re.compile(r"(\d{4}).*?([\d,]+)km.*?(Automatic|Manual|CVT|DCT|Stick)", re.I)
RE_PRICE_NUM = re.compile(r"[\d,]+")


def clean_html(text: str) -> str:
    """Strip tags & HTML entities, collapse whitespace."""
    text = re.sub(r"<[^>]+>", "", text)
    return re.sub(r"\s+", " ", unescape(text)).strip()


def parse_card(match: re.Match[str]) -> dict:
    seq, img, raw_title, raw_info, raw_price = match.groups()
    title = clean_html(raw_title)
    info = clean_html(raw_info)
    year = km = transmission = ""

    m = RE_INFO.search(info.replace("ㆍ", " "))
    if m:
        year, km, transmission = m.groups()

    price = RE_PRICE_NUM.search(raw_price)
    price = price.group().replace(",", "") if price else ""

    return {
        "seq": seq,
        "title": title,
        "year": year,
        "km": km,
        "transmission": transmission,
        "price": price,
        "image_url": img,
        "safe_url": SAFE_URL.format(seq=seq),
    }


def scrape_page(page: int) -> list[dict]:
    url = BASE_PAGE.format(page=page)
    resp = requests.get(url, headers={"User-Agent": UA}, timeout=15)
    resp.raise_for_status()
    html = resp.text
    return [parse_card(m) for m in RE_CARD.finditer(html)]


def main() -> None:
    out_file = Path("karaba_listings.csv")
    fieldnames = [
        "seq",
        "title",
        "year",
        "km",
        "transmission",
        "price",
        "image_url",
        "safe_url",
    ]
    with out_file.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        total = 0
        for p in range(1, 2751):
            try:
                cards = scrape_page(p)
            except Exception as e:
                print(f"[Page {p}] ⚠️  error: {e}", file=sys.stderr)
                continue

            if not cards:
                print(f"[Page {p}] (empty) – stopping early")
                break

            writer.writerows(cards)
            total += len(cards)
            print(f"[Page {p}] ✓ {len(cards)} cars (total {total})")
            time.sleep(1.2)  # be polite – adjust if needed

    print(f"\n✅ Finished. Saved {total} rows to {out_file}")


if __name__ == "__main__":
    main()
