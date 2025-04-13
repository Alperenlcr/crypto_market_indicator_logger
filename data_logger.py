import time
import signal
import requests
from datetime import datetime

from logger import logger
from db_utils import DBUtils, Tables
from btc_receiver import BtcReceiver
from indicator_receiver import IndicatorReceiver


# Define a timeout exception
class TimeoutException(Exception):
    pass

# Signal handler function
def timeout_handler(signum, frame):
    raise TimeoutException("Function execution timed out!")

# Wrapper function with timeout
def run_with_timeout(func, args=(), kwargs=None, timeout=5):
    """
    Runs a function with a timeout.

    :param func: The function to run.
    :param args: Positional arguments for the function.
    :param kwargs: Keyword arguments for the function.
    :param timeout: Timeout in seconds.
    """
    if kwargs is None:
        kwargs = {}

    # Set up the signal handler for SIGALRM
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout)  # Set the alarm

    try:
        func(*args, **kwargs)  # Execute the function
        signal.alarm(0)  # Cancel the alarm if the function completes
    except TimeoutException as e:
        print(e)


class DataLogger:
    """
    This class is responsible for logging data from the BTC receiver and
    Indicator receiver to the database.
    It fetches the current price of Bitcoin and the status of indicators
    and logs them to the database. Runs forever and every minute.
    Database tables primary key is timestamp and YYYY-MM-DD HH:MM:00 format.
    """

    def __init__(self) -> None:
        self.btc_receiver = BtcReceiver()
        self.indicator_receiver = IndicatorReceiver()
        self.db = DBUtils()
        self.tables = Tables

    def format_timestamp(self, ts: datetime) -> datetime:
        """
        Format the timestamp to YYYY-MM-DD HH:MM:00 format.
        This is used to ensure that the timestamp is in the correct format
        for the database.
        """
        return ts.replace(second=0, microsecond=0)

    def interval_to_table(self, interval: str) -> Tables:
        """
        Convert the interval to the corresponding database table.
        This is used to ensure that the data is logged to the correct
        table in the database.
        """
        if interval == "1m":
            return self.tables.INDICATOR_1MIN
        elif interval == "5m":
            return self.tables.INDICATOR_5MIN
        elif interval == "15m":
            return self.tables.INDICATOR_15MIN
        elif interval == "30m":
            return self.tables.INDICATOR_30MIN
        elif interval == "1h":
            return self.tables.INDICATOR_1HOURS
        elif interval == "2h":
            return self.tables.INDICATOR_2HOURS
        elif interval == "4h":
            return self.tables.INDICATOR_4HOURS
        elif interval == "1d":
            return self.tables.INDICATOR_1DAY
        elif interval == "1w":
            return self.tables.INDICATOR_1WEEK
        elif interval == "1M":
            return self.tables.INDICATOR_1MONTH
        else:
            logger.error(f"Invalid interval: {interval}")

    def get_data(self, timeout: int = 50) -> tuple[float | None, dict]:
        """
        Fetches the current price of Bitcoin and the status of indicators.
        If retrieval fails, it returns None for the price and the latest
        known status for fail_limit times. After that, it returns None
        and sends an email to the admin.
        """
        # Set a timeout for the function execution
        run_with_timeout(self.btc_receiver.get_price, timeout=int(timeout*0.2))
        price = self.btc_receiver.get_price()
        # Set a timeout for the function execution
        run_with_timeout(self.indicator_receiver.get_indicators,
                          timeout=int(timeout*0.8))
        indicators = self.indicator_receiver.get_indicators()
        return price, indicators

    def log_data(self) -> None:
        """
        Fetches the current price of Bitcoin and the status of indicators
        and logs them to the database.
        """
        # wait until next minute start
        print(11, datetime.now())
        while datetime.now().second > 5:
            time.sleep(0.01)
        print(22, datetime.now())
        # check internet connection
        try:
            requests.get("https://www.google.com", timeout=5)
        except requests.ConnectionError:
            logger.error("No internet connection.")
            print("No internet connection.")
            time.sleep(5)
            return
        st_ = datetime.now()
        formatted_ts = self.format_timestamp(datetime.now())
        price, indicators = self.get_data()
        print(f"Price: {price}, Indicators: {indicators}")

        self.db.add_price(formatted_ts, price)

        for interval, status in indicators.items():
            for indicator, t in status.items():
                try:
                    value = float(t[0].replace('−', '-').replace(',', '.'))
                except Exception as e:
                    value = None
                if t[1] not in ['Buy', 'Sell', 'Neutral']:
                    signal_ = None
                else:
                    signal_ = t[1]
                self.db.add_indicator(self.interval_to_table(interval),
                    formatted_ts, indicator, value, signal_)
        loop_time = datetime.now() - st_
        if loop_time.total_seconds() < 5:
            time.sleep(5 - loop_time.total_seconds())


if __name__ == "__main__":
    data_logger = DataLogger()
    while True:
        data_logger.log_data()
