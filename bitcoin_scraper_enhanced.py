from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from fake_useragent import UserAgent
import pandas as pd
from datetime import datetime
import os
import logging
import time

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

options = Options()
options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920,1080")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
ua = UserAgent()
options.add_argument(f"user-agent={ua.random}")

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

URL = "https://coinmarketcap.com/currencies/bitcoin/"

def scrape_bitcoin_data():
    """Scrape Bitcoin details from CoinMarketCap."""
    try:
        driver.get(URL)
        wait = WebDriverWait(driver, 20)

        wait.until(EC.presence_of_element_located((By.XPATH, '//span[@data-test="text-cdp-price-display"]')))

        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)

        price = driver.find_element(By.XPATH, '//span[@data-test="text-cdp-price-display"]').text

        try:
            market_cap = driver.find_element(
                By.XPATH, "//dt[.//div[contains(text(),'Market cap')]]/following-sibling::dd//span"
            ).text
        except Exception:
            market_cap = "N/A"

        try:
            volume_24h = driver.find_element(
                By.XPATH, "//dt[.//div[contains(text(),'Volume (24h')]]/following-sibling::dd//span"
            ).text
        except Exception:
            volume_24h = "N/A"

        try:
            circulating_supply = driver.find_element(
                By.XPATH, "//dt[.//div[contains(text(),'Circulating supply')]]/following-sibling::dd//span"
            ).text
        except Exception:
            circulating_supply = "N/A"

        try:
            price_change_24h = driver.find_element(
                By.XPATH, "//p[contains(@class, 'change-text')]"
            ).text
        except Exception:
            price_change_24h = "N/A"

        bullish, bearish = "N/A", "N/A"

        for y in range(0, 4000, 500):
            driver.execute_script(f"window.scrollTo(0, {y});")
            time.sleep(0.8)
            bullish_elems = driver.find_elements(
                By.XPATH, "//span[contains(@class,'cOjBdO') and contains(@class,'ratio')]"
            )
            bearish_elems = driver.find_elements(
                By.XPATH, "//span[contains(@class,'iKkbth') and contains(@class,'ratio')]"
            )
            if bullish_elems or bearish_elems:
                break

        try:
            bullish = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//span[contains(@class,'cOjBdO') and contains(@class,'ratio')]")
                )
            ).text
        except Exception:
            bullish = "N/A"

        try:
            bearish = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//span[contains(@class,'iKkbth') and contains(@class,'ratio')]")
                )
            ).text
        except Exception:
            bearish = "N/A"
        # ---------------------------------------------------------

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        data = {
            "timestamp": timestamp,
            "price": price,
            "market_cap": market_cap,
            "volume_24h": volume_24h,
            "circulating_supply": circulating_supply,
            "price_change_24h": price_change_24h,
            "bullish_sentiment": bullish,
            "bearish_sentiment": bearish,
        }

        logging.info(f"Scraped data: {data}")
        return data

    except Exception as e:
        logging.error(f"Scraping error: {e}")
        return None

def save_to_csv(data):
    """Save scraped data to CSV inside the project folder."""
    project_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(project_dir, "bitcoin_hourly_data_enhanced.csv")

    try:
        df = pd.read_csv(file_path)
    except FileNotFoundError:
        df = pd.DataFrame(columns=[
            "timestamp", "price", "market_cap", "volume_24h",
            "circulating_supply", "price_change_24h",
            "bullish_sentiment", "bearish_sentiment"
        ])

    new_row = pd.DataFrame([data])
    df = pd.concat([df, new_row], ignore_index=True)
    df.to_csv(file_path, index=False)

if __name__ == "__main__":
    logging.info("Starting Bitcoin scraper...")
    try:
        data = scrape_bitcoin_data()
        if data:
            save_to_csv(data)
            logging.info("Data saved successfully.")
        else:
            logging.warning("No data scraped this run.")
    finally:
        driver.quit()
        logging.info("Driver closed successfully.")
