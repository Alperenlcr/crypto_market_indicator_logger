import requests
from datetime import datetime, timedelta

from logger import logger
from mail_sender import send_email


class BtcReceiver:
    """
    This class is responsible for receiving Bitcoin data from binance api
    get_price() method will fetch the current price of Bitcoin in USD.
    if retrieval fails, it will return latest known price for fail_limit
    times. after that it will return None. And sends an email to the admin.
    Sends mail only once per day.
    """

    def __init__(self, fail_limit: float = 2) -> None:
        self.fail_limit = fail_limit
        self.price = None
        self.fail_count = 0
        self.last_email_sent = None

    def get_price(self) -> float | None:
        """
        Fetches the current price of Bitcoin in USD from Binance API.
        If retrieval fails, it returns the latest known price for fail_limit times.
        After that, it returns None and sends an email to the admin.
        """
        if self.fail_count >= self.fail_limit:
            self.price = None
            # Check if email was sent in the last 24 hours
            if self.last_email_sent is None or \
               datetime.now() - self.last_email_sent > timedelta(days=1):
                # Send email to admin
                if send_email("BTC Receiver Failed. " + 
                           "Failed to fetch Bitcoin data from Binance API."):
                    self.last_email_sent = datetime.now()

        price = self.fetch_bitcoin_data()
        if price == None:
            self.fail_count += 1
        else:
            self.fail_count = 0
            self.price = price
        return self.price

    def fetch_bitcoin_data(self) -> float:
        """Function to fetch Bitcoin data from Binance"""
        price = None
        try:
            # Binance API endpoint for ticker price
            url = "https://api.binance.com/api/v3/ticker/price"
            params = {"symbol": "BTCUSDT"}
            response = requests.get(url, params=params, timeout=5)
            if response.status_code == 200:
                data = response.json()
                price = data["price"]
            else:
                logger.error(
                  f"Failed to fetch data. Status code: {response.status_code}")
        except Exception as e:
            logger.error(f"Error fetching data: {e}")
        return price


if __name__ == "__main__":
    from time import sleep
    btc_receiver = BtcReceiver(fail_limit=3)
    while True:
        price = btc_receiver.get_price()
        if price is not None:
            print(f"Current BTC Price: {price}")
        else:
            print("Failed to fetch BTC Price.", price)
        sleep(1)
