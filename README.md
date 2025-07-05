# 🚗 karaba-car-scraper

A Python script to scrape used car listings from [Karaba (m.karaba.co.kr)](https://m.karaba.co.kr) including details like title, specs, and price. The scraped data is saved to a CSV file. This scraper uses only `requests` and `BeautifulSoup`, no Selenium or browser automation needed.

---

## 📌 Features

- Extracts data from pages 1 to 2750
- Captures:
  - Car title
  - Specs (year, km, transmission)
  - Price
  - Detail link and image
- Saves output as `karaba_listings.csv`
- Efficient and lightweight

---

## 💻 Requirements

- Python 3.7+
- `requests`
- `beautifulsoup4`
- `csv` (standard library)

**Install dependencies:**

pip install requests
pip install beautifulsoup4



**🚀 Usage
Clone the repository:**

git clone https://github.com/your-username/karaba-car-scraper.git

cd karaba-car-scraper

**Run the scraper:**

python3 scraper.py

**The output will be saved as:**

karaba_listings.csv


