# 🚗 karaba‑car‑scraper

A resilient, **headless** Python scraper that harvests detailed used‑car listings from [Karaba](https://m.karaba.co.kr) and stores them incrementally in a CSV file.
It combines `requests`, `BeautifulSoup`, `wget`, and **Tor** for IP rotation—no Selenium or browser automation required.

> **Disclaimer**
> This project is provided **for educational and research purposes only**.
> The developer is **not affiliated with Karaba , nor responsible for any misuse, abuse, or Terms‑of‑Service violations arising from this code.
> Use it **ethically, responsibly, and legally**.
> The code is supplied *as‑is* without warranty of any kind.

---

## ✨ Key Features

| Feature               | Description                                                                                                        |
| --------------------- | ------------------------------------------------------------------------------------------------------------------ |
| **Page crawler**      | Navigates list pages **1 → 2750** (configurable) and extracts basic card data.                                     |
| **Detail scraper**    | Downloads each car‐detail page via `wget`, then parses a full spec sheet, accidents, features, and **image URLs**. |
| **Tor integration**   | Detects "세션에러" blocks, restarts the system Tor service, waits for a fresh IP, and retries automatically.           |
| **Resumable CSV**     | On startup it reads the existing `karaba.csv` and skips already‑captured `seq` IDs.                                |
| **Lightweight stack** | Pure HTTP + HTML parsing—no JavaScript, browser, or headless Chrome overhead.                                      |
| **Fault tolerance**   | Individual retries (page + detail) with exponential back‑off; fails gracefully after limit.                        |
| **Extensible**        | Clear modular functions (`scrape_page_with_retry`, `scrape_detail`, etc.) for easy maintenance.                    |

---

## 📊 Output Schema (`karaba.csv`)

| Column              | Notes                                                     |
| ------------------- | --------------------------------------------------------- |
| `seq`               | Internal Karaba listing ID                                |
| `url`               | Direct *safe* image proxy URL (`photo5.autosale.co.kr`)   |
| `title`             | Car title (model + trim)                                  |
| `info`              | Short spec line from list card (year / km / transmission) |
| `price`             | Numeric price (KRW) with punctuation removed              |
| `model`             | Exact model field from detail page                        |
| `registration_date` | First registration date                                   |
| `transmission`      | Transmission type                                         |
| `color`             | Exterior colour                                           |
| `manufacturer_year` | Manufacturer’s year                                       |
| `mileage`           | Odometer reading (km)                                     |
| `fuel`              | Fuel type                                                 |
| `car_number`        | Korean license plate number                               |
| `accidents`         | Reported accident history                                 |
| `features`          | Comma‑separated option list                               |
| `image_urls`        | Comma‑separated full‑size image URLs                      |

> **Tip:** Import the CSV into pandas or a database for deeper analysis.

---

## 🖥️ Requirements

* Python **3.8+**
* `requests`
* `beautifulsoup4`
* **System packages**:

  * `tor` (daemon) – for IP rotation
  * `torsocks` – transparent Tor proxy for `wget`
  * `wget` – fast, lightweight downloader

```bash
sudo apt update && sudo apt install tor torsocks wget -y
pip install -r requirements.txt  # installs Python deps
```

`requirements.txt`:

```
beautifulsoup4>=4.12
requests>=2.31
```

---

## 🚀 Quick‑Start

```bash
# 1. Clone repository
$ git clone https://github.com/your‑username/karaba‑car‑scraper.git
$ cd karaba‑car‑scraper

# 2. Start (Tor must be running & reachable via systemd)
$ torsocks python3 scraper.py
```

Logs will stream to stdout.  New rows are appended to **karaba.csv**.

---

## ⚙️ Configuration

| Parameter         | Where           | Default    | Description                        |
| ----------------- | --------------- | ---------- | ---------------------------------- |
| `PAGE_MAX`        | code            | 2750       | Highest list page to crawl.        |
| `UA`              | code            | Mobile     | HTTP User‑Agent header.            |
| `CSV_PATH`        | code            | karaba.csv | Output file path.                  |
| `retries`, `wait` | `scrape_detail` | 5 / 5 s    | Attempts & delay per detail fetch. |

Feel free to edit constants at the top of **scraper.py** or turn them into CLI flags.

---

## 🛠️ Running on a Schedule

Use `cron`, `systemd` timer, or PM2 (*if Node is already on the box*) to execute the script hourly/daily.  The built‑in deduplication ensures only new listings are fetched.

Example crontab (every 6 h):

```
0 */6 * * *  cd /opt/karaba && /usr/bin/python3 scraper.py >> scrape.log 2>&1
```

---

## 🤝 Contributing

Pull requests are welcome!  Please fork the repo and open a PR with clear commit messages.  Bugs / ideas → GitHub Issues.

---

## 📄 License

Released under the **MIT License** – see `LICENSE` for full text.
