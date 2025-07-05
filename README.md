Disclaimer This project is for educational and research purposes only.

The developer is not affiliated with Autowini.com.

The developer is not responsible for any misuse, abuse, or violation of terms of service.

The code is provided as-is without warranty of any kind.

You are solely responsible for using this tool ethically and legally.

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


