import csv
import re
import requests
import time
from pathlib import Path

UA = "Mozilla/5.0 (Linux; Android 10)"
BASE_PAGE = "https://m.karaba.co.kr/?m=sale&s=list&p={page}"
BASE_SAFE = "https://photo5.autosale.co.kr/safe.php?seq={seq}&t=kimko"
CSV_PATH = Path("karaba.csv")

RE_CARD = re.compile(
    r'<a href="[^"]*seq=(\d+)">.*?<div class="cartitle">(.*?)</div>.*?<div class="carinfo">(.*?)</div>.*?<div class="money">(.*?)<span',
    re.DOTALL
)

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
                print(f"[Page {page}] ⚠️Oops..IP blocked..!!!! i know you are poor to buy rotational residental proxies, please run this script locally on your computer, if ip blocked simply turn off and on the router to get a new IP.")
                print(f"[Page {page}] ⏳ hurry up Waiting 60 seconds before retrying... if its beyond increase the sleep time")
                time.sleep(60)
                continue

            return [parse_card(m) for m in RE_CARD.finditer(html)]

        except requests.RequestException as e:
            print(f"[Page {page}] ⚠️ Request error: {e}")
            print(f"[Page {page}] 🔄 Please turn off and on the router to get a new IP.")
            print(f"[Page {page}] ⏳ Waiting 60 seconds before retrying...")
            time.sleep(60)

def load_existing_seqs() -> set:
    if not CSV_PATH.exists():
        return set()
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        return set(row["seq"] for row in csv.DictReader(f))

def save_to_csv(rows: list[dict]):
    file_exists = CSV_PATH.exists()
    with open(CSV_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["seq", "url", "title", "info", "price"])
        if not file_exists:
            writer.writeheader()
        for row in rows:
            writer.writerow(row)

def main():
    existing = load_existing_seqs()
    start_page = 1
    if existing:
        print("🔁 Resuming from last saved page…")
        max_seq = max(map(int, existing))
    else:
        max_seq = 0

    for p in range(start_page, 2751):
        print(f"[Page {p}] Scraping…")
        cards = scrape_page_with_retry(p)
        if not cards:
            print(f"[Page {p}] (empty) – stopping early")
            break
        new_cards = [c for c in cards if c["seq"] not in existing]
        if not new_cards:
            print(f"[Page {p}] All items already saved – skipping")
            continue
        save_to_csv(new_cards)
        print(f"[Page {p}] ✅ Saved {len(new_cards)} new items")
        time.sleep(1)

if __name__ == "__main__":
    main()
