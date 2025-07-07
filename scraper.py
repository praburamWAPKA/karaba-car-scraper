import csv, re, json, time, requests, subprocess, tempfile, os
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
    "car_number", "accidents", "features", "image_urls"
]


def restart_tor():
    print("🔁 Restarting Tor...")
    subprocess.run(["systemctl", "restart", "tor"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def wget_fetch(url: str, tmp_path: str) -> bool:
    cmd = ["wget", "-q", "-O", tmp_path, "--timeout=20", "--tries=2", url]
    return subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0


def parse_card(m: re.Match) -> dict:
    seq, title, info, price = m.groups()
    clean = lambda s: re.sub(r"<[^>]+>", "", s).strip().replace("\xa0", " ")
    return {
        "seq": seq,
        "url": BASE_SAFE.format(seq=seq),
        "title": clean(title),
        "info": clean(info),
        "price": re.sub(r"[^\d]", "", price)
    }


def scrape_page_with_retry(page: int) -> list[dict]:
    url = BASE_PAGE.format(page=page)
    while True:
        try:
            html = requests.get(url, headers={"User-Agent": UA}, timeout=15).text
            if "세션에러" in html:
                print(f"[Page {page}] ⚠️ 세션에러 detected. Restarting Tor...")
                restart_tor()
                time.sleep(20)
                continue
            return [parse_card(m) for m in RE_CARD.finditer(html)]
        except requests.RequestException as e:
            print(f"[Page {page}] ⚠️ {e}. Retrying in 60s...")
            time.sleep(60)


def scrape_detail(seq: str) -> dict | None:
    url = BASE_DETAIL.format(seq=seq)
    retries = 5
    tor_wait = 20
    tmp_fd, tmp_path = tempfile.mkstemp(suffix=".html")
    os.close(tmp_fd)

    for attempt in range(1, retries + 1):
        if not wget_fetch(url, tmp_path):
            print(f"[{seq}] ❌ wget failed ({attempt}/{retries})")
            restart_tor()
            time.sleep(tor_wait)
            continue

        with open(tmp_path, encoding="utf-8", errors="ignore") as f:
            html = f.read()

        if "detail_list" not in html or "carinfo" not in html:
            print(f"[{seq}] 🚫 not loaded ({attempt}/{retries})")
            restart_tor()
            time.sleep(tor_wait)
            continue

        soup = BeautifulSoup(html, "html.parser")
        table = soup.select_one("div.detail_list div.carinfo table")
        if not table:
            print(f"[{seq}] 🚫 table missing ({attempt}/{retries})")
            restart_tor()
            time.sleep(tor_wait)
            continue

        car_info = {}
        for row in table.select("tr"):
            tds = row.find_all("td")
            if len(tds) == 3:
                car_info[tds[0].get_text(strip=True)] = tds[2].get_text(strip=True)

        features = [
            span.get_text(strip=True)
            for span in soup.select("table.opouter td.on span")
        ]

        image_urls = []
        for div in soup.select("div.swiper-container.gallery-thumbs div.swiper-slide"):
            style = div.get("style", "")
            match = re.search(r'url\((.*?)\)', style)
            if match:
                image_urls.append(match.group(1))

        extra_imgs = [
            img['src'] for img in soup.select("div#smallimage img")
            if 'noimage' not in img.get('src', '')
        ]
        image_urls.extend(extra_imgs)

        os.remove(tmp_path)
        return {
            "model": car_info.get("Car model", ""),
            "registration_date": car_info.get("Registration Date", ""),
            "transmission": car_info.get("Transmission", ""),
            "color": car_info.get("Color", ""),
            "manufacturer_year": car_info.get("Manufacturer Year", ""),
            "mileage": car_info.get("Mileage (km)", ""),
            "fuel": car_info.get("Fuel", ""),
            "car_number": car_info.get("Car's Mumber", ""),
            "accidents": car_info.get("Accidents", ""),
            "features": ", ".join(features),
            "image_urls": ", ".join(image_urls)
        }

    os.remove(tmp_path)
    print(f"[{seq}] ❌ Failed after {retries} attempts.")
    return None


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


def main():
    existing = load_existing_seqs()
    print(f"📄 CSV already has {len(existing)} rows.")
    start_page = 1

    for p in range(start_page, 2):  # Adjust upper range as needed
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
                print(f"[{card['seq']}] skipped (no detail)")
                continue
            row = {**card, **detail}
            new_rows.append(row)
            existing.add(card["seq"])
            print(json.dumps(row, ensure_ascii=False, indent=2))

        if new_rows:
            save_to_csv(new_rows)
            print(f"[Page {p}] 💾 Wrote {len(new_rows)} rows.")
        else:
            print(f"[Page {p}] All items already saved – skipping.")

        time.sleep(1)


if __name__ == "__main__":
    main()
