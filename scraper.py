import csv
import re
import requests
import time
from pathlib import Path
from bs4 import BeautifulSoup

UA = "Mozilla/5.0 (Linux; Android 10)"
BASE_PAGE = "https://m.karaba.co.kr/?m=sale&s=list&p={page}"
BASE_DETAIL = "https://m.karaba.co.kr/?m=sale&s=detail&seq={seq}"
BASE_SAFE = "https://photo5.autosale.co.kr/safe.php?seq={seq}&t=kimko"
CSV_PATH = Path("karaba.csv")

RE_CARD = re.compile(
    r'<a href="[^"]*seq=(\d+)">.*?<div class="cartitle">(.*?)</div>.*?'
    r'<div class="carinfo">(.*?)</div>.*?<div class="money">(.*?)<span',
    re.DOTALL
)

HEADERS = [
    "seq", "url", "title", "info", "price",
    "model", "registration_date", "transmission", "color",
    "manufacturer_year", "mileage", "fuel",
    "car_number", "accidents", "image_urls"
]

# ---------- Scraping functions ----------

def parse_card(match: re.Match) -> dict:
    seq, title, info, price = match.groups()
    title = re.sub(r"<[^>]+>", "", title).strip().replace("\xa0", " ")
    info = re.sub(r"<[^>]+>", "", info).strip().replace("\xa0", " ")
    price = re.sub(r"[^\d]", "", price)
    return {
        "seq": seq,
        "url": BASE_SAFE.format(seq=seq),
        "title": title,
        "info": info,
        "price": price
    }

def scrape_page_with_retry(page: int) -> list[dict]:
    url = BASE_PAGE.format(page=page)
    while True:
        try:
            resp = requests.get(url, headers={"User-Agent": UA}, timeout=15)
            html = resp.text
            if "세션에러" in html:
                print(f"[Page {page}] ⚠️ IP blocked. Waiting 60 seconds to retry...")
                time.sleep(60)
                continue
            return [parse_card(m) for m in RE_CARD.finditer(html)]
        except requests.RequestException as e:
            print(f"[Page {page}] ⚠️ Request error: {e}. Retrying in 60s...")
            time.sleep(60)

def scrape_detail(seq: str) -> dict | None:
    url = BASE_DETAIL.format(seq=seq)
    try:
        r = requests.get(url, headers={"User-Agent": UA}, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")

        # Spec fields
        cells = [td.get_text(strip=True) for td in soup.select("div.detail_list td.inforight")]
        if len(cells) < 9:
            return None
        (model, reg_date, transmission, color, year,
         mileage, fuel, car_number, accidents) = cells[:9]

        # Images from swiper-slide
        image_divs = soup.select("div.swiper-container.gallery-thumbs div.swiper-slide")
        image_urls = []
        for div in image_divs:
            style = div.get("style", "")
            match = re.search(r'url\((.*?)\)', style)
            if match:
                image_urls.append(match.group(1))

        return {
            "model": model,
            "registration_date": reg_date,
            "transmission": transmission,
            "color": color,
            "manufacturer_year": year,
            "mileage": mileage,
            "fuel": fuel,
            "car_number": car_number,
            "accidents": accidents,
            "image_urls": ",".join(image_urls)
        }

    except requests.RequestException as e:
        print(f"[Seq {seq}] ⚠️ Detail fetch failed: {e}")
        return None

# ---------- CSV helpers ----------

def load_existing_seqs() -> set[str]:
    if not CSV_PATH.exists():
        return set()
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        return {row["seq"] for row in csv.DictReader(f)}

def save_to_csv(rows: list[dict]):
    file_exists = CSV_PATH.exists()
    with open(CSV_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=HEADERS)
        if not file_exists:
            writer.writeheader()
        writer.writerows(rows)

# ---------- Main ----------

def main():
    existing = load_existing_seqs()
    print(f"📄 CSV already has {len(existing)} rows.")
    start_page = 1

    for p in range(start_page, 2751):
        print(f"\n[Page {p}] Scraping list...")
        cards = scrape_page_with_retry(p)
        if not cards:
            print(f"[Page {p}] (empty) – stopping.")
            break

        new_rows: list[dict] = []
        for card in cards:
            if card["seq"] in existing:
                continue
            detail = scrape_detail(card["seq"])
            if not detail:
                print(f"[Seq {card['seq']}] skipped (no detail)")
                continue
            row = {**card, **detail}
            new_rows.append(row)
            existing.add(card["seq"])
            print(f"[Seq {card['seq']}] ✅ Captured")

        if new_rows:
            save_to_csv(new_rows)
            print(f"[Page {p}] 💾 Wrote {len(new_rows)} rows.")
        else:
            print(f"[Page {p}] All items already saved – skipping.")

        time.sleep(1)

if __name__ == "__main__":
    main()
