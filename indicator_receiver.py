import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime, timedelta

from logger import logger
from mail_sender import send_email # type: ignore
from dotenv import load_dotenv


load_dotenv()
P_PATH_TO_DRIVER = os.getenv("P_PATH_TO_DRIVER")


class IndicatorReceiver:
    """
    This class is responsible for receiving indicator data from tradingview
    get_indicators() method will fetch the current status of indicators.
    if retrieval fails, it will return latest known status for fail_limit
    times. after that it will return None. And sends an email to the admin.
    Sends mail only once per day.
    """

    def __init__(self, fail_limit: float = 2) -> None:
        self.fail_limit = fail_limit
        self.fail_count = 0
        self.last_email_sent = None
        self.status_default = self.default_status()
        self.status = self.status_default.copy()
        self.init_selenium()

    def init_selenium(self) -> None:
        """Initialize the Selenium WebDriver"""
        # Set up the Selenium WebDriver
        service = Service(P_PATH_TO_DRIVER)
        options = webdriver.ChromeOptions()
        self.driver = webdriver.Chrome(service=service, options=options)

    def default_status(self) -> dict:
        self.intervals = ['1m', '5m', '15m', '30m', '1h', '2h', '4h', '1d', '1w', '1M']
        self.indicators = [
            'Relative Strength Index (14)',
            'Stochastic %K (14, 3, 3)',
            'Commodity Channel Index (20)',
            'Average Directional Index (14)',
            'Awesome Oscillator',
            'Momentum (10)',
            'MACD Level (12, 26)',
            'Stochastic RSI Fast (3, 3, 14, 14)',
            'Williams Percent Range (14)',
            'Bull Bear Power',
            'Ultimate Oscillator (7, 14, 28)',
            'Exponential Moving Average (10)',
            'Simple Moving Average (10)',
            'Exponential Moving Average (20)',
            'Simple Moving Average (20)',
            'Exponential Moving Average (30)',
            'Simple Moving Average (30)',
            'Exponential Moving Average (50)',
            'Simple Moving Average (50)',
            'Exponential Moving Average (100)',
            'Simple Moving Average (100)',
            'Exponential Moving Average (200)',
            'Simple Moving Average (200)',
            'Ichimoku Base Line (9, 26, 52, 26)',
            'Volume Weighted Moving Average (20)',
            'Hull Moving Average (9)']
        status = {}
        for interval in self.intervals:
            status[interval] = {}
            for indicator in self.indicators:
                # normally this would be a tuple of (value, (buy/sell/neutral))
                status[interval][indicator] = (None, None)
        return status

    def get_indicators(self) -> dict:
        """
        Fetches the current status of Bitcoin indicators in tradingview.
        If retrieval fails, it returns the latest known status for fail_limit times.
        After that, it returns None and sends an email to the admin.
        """
        if self.fail_count >= self.fail_limit:
            # Check if email was sent in the last 24 hours
            if self.last_email_sent is None or \
               datetime.now() - self.last_email_sent > timedelta(days=1):
                # Send email to admin
                if send_email("Indicator Receiver Failed. " +
                            "Failed to fetch indicator data from TradingView."):
                    self.last_email_sent = datetime.now()

        status = self.fetch_indicators_data()
        is_failed = False
        for interval in status:
            for indicator in status[interval]:
                if status[interval][indicator] == None:
                    is_failed = True
                    if self.fail_count >= self.fail_limit:
                        self.status[interval][indicator] = None
                else:
                    self.status[interval][indicator] = status[interval][indicator]
        if is_failed:
            self.fail_count += 1
        else:
            self.fail_count = 0
        return self.status

    def fetch_indicators_data(self) -> dict:
        """Function to fetch indicators data from tradingview"""
        status = self.status_default.copy()
        try:
            # Open the target URL
            url = "https://www.tradingview.com/symbols/BTCUSD/technicals/"
            self.driver.get(url)
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located((By.TAG_NAME, "table")))

            # Iterate over each interval option
            for i in range(len(self.intervals)):
                # Click on the interval button
                interval_buttons = self.driver.find_elements(
                    By.CSS_SELECTOR, '[role="tab"]')
                button = interval_buttons[i]
                self.driver.execute_script("arguments[0].click();", button) 

                # Find tables
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_all_elements_located((By.TAG_NAME, "table"))
                )
                tables = self.driver.find_elements(By.TAG_NAME, "table")
                if len(tables) < 2:
                    logger.error(
                        f"Less than two tables found for interval {self.intervals[i]}.")
                    continue

                # Extract data from the first table - Oscillators
                rows_first_table = tables[0].find_elements(By.TAG_NAME, "tr")
                for row in rows_first_table:
                    cells = row.find_elements(By.TAG_NAME, "td")
                    if cells:
                        if cells[0].text not in self.indicators:
                            logger.error(
                                f"Indicator {cells[0].text} not in the list.")
                            continue
                        status[self.intervals[i]][cells[0].text] = \
                            (cells[1].text, cells[2].text)

                # Extract data from the second table Moving Averages
                rows_second_table = tables[1].find_elements(By.TAG_NAME, "tr")
                for row in rows_second_table:
                    cells = row.find_elements(By.TAG_NAME, "td")
                    if cells:
                        if cells[0].text not in self.indicators:
                            continue
                        status[self.intervals[i]][cells[0].text] = \
                            (cells[1].text, cells[2].text)
        except Exception as e:
            logger.error(f"Error fetching data: {e}")
            print("An error occurred:", str(e))
        return status


if __name__ == "__main__":
    from time import sleep
    indicator_receiver = IndicatorReceiver(fail_limit=3)
    while True:
        status = indicator_receiver.get_indicators()
        if None not in status.values():
            # print("Current BTC indicators:", status)
            print("BTC indicators fetched successfully.")
        else:
            # print("Failed to fetch BTC indicators.", status)
            print("Failed to fetch BTC indicators.")
        sleep(1)
    indicator_receiver.driver.quit()
