import os
import psycopg2
from enum import Enum
from time import sleep
from psycopg2 import sql
from dotenv import load_dotenv
from datetime import datetime as timestamp

from logger import logger
from mail_sender import send_email


load_dotenv()
P_DBNAME = os.getenv("P_DBNAME")
P_USER = os.getenv("P_USER")
P_PASSWORD = os.getenv("P_PASSWORD")
P_HOST = os.getenv("P_HOST")
P_PORT = os.getenv("P_PORT")


class Tables(Enum):
    BTC_PRICE = "btc_price"
    INDICATOR_1MIN = "indicator_1min"
    INDICATOR_5MIN = "indicator_5min"
    INDICATOR_15MIN = "indicator_15min"
    INDICATOR_30MIN = "indicator_30min"
    INDICATOR_1HOURS = "indicator_1hours"
    INDICATOR_2HOURS = "indicator_2hours"
    INDICATOR_4HOURS = "indicator_4hours"
    INDICATOR_1DAY = "indicator_1day"
    INDICATOR_1WEEK = "indicator_1week"
    INDICATOR_1MONTH = "indicator_1month"


class DBUtils:
    def __init__(self) -> None:
        self.connection = None
        self.connection_attempts = 0
        self.connect()

    def connect(self) -> None:
        try:
            self.connection = psycopg2.connect( dbname = P_DBNAME, user = P_USER,
                                password = P_PASSWORD, host = P_HOST, port = P_PORT)
        except Exception as e:
            print(
                "An error occurred while connecting to the database:", e)
            sleep(1)
            self.connection_attempts += 1
            if self.connection_attempts < 60:
                self.connect()
            else:
                logger.error(
                    "Failed to connect to the database after 60 attempts.")
                send_email(
                  "Database connection failed. Please check the database server.")

    def is_connected(self) -> bool:
        """Check if the connection to the database is established."""
        if self.connection == None:
            return False
        return self.connection.status == psycopg2.extensions.STATUS_READY

    def close(self) -> None:
        if self.connection:
            self.connection.close()

    def add_price(self, timestamp: timestamp, price: float) -> bool:
        """Add the btc price to the btc_price table."""
        try:
            with self.connection.cursor() as cursor:
                query = sql.SQL(
                    "INSERT INTO {} (timestamp, price) VALUES (%s, %s)").format(
                    sql.Identifier(Tables.BTC_PRICE.value))
                cursor.execute(query, (timestamp, price))
            self.connection.commit()
            return True
        except Exception as e:
            if not self.is_connected():
                self.connect()
            print(f"Failed to add price: {e}")
            return False

    def delete_price(self, timestamp: timestamp) -> bool:
        """Delete the btc price from the btc_price table."""
        try:
            with self.connection.cursor() as cursor:
                query = sql.SQL(
                    "DELETE FROM {} WHERE timestamp = %s").format(
                    sql.Identifier(Tables.BTC_PRICE.value))
                cursor.execute(query, (timestamp,))
            self.connection.commit()
            return True
        except Exception as e:
            if not self.is_connected():
                self.connect()
            print(f"Failed to delete price: {e}")
            return False

    def get_price(self, timestamp: timestamp) -> float | None:
        """Get the btc price from the btc_price table."""
        try:
            with self.connection.cursor() as cursor:
                query = sql.SQL(
                    "SELECT price FROM {} WHERE timestamp = %s").format(
                    sql.Identifier(Tables.BTC_PRICE.value))
                cursor.execute(query, (timestamp,))
                result = cursor.fetchone()
            if result:
                return result[0]
            else:
                return None
        except Exception as e:
            if not self.is_connected():
                self.connect()
            print(f"Failed to get price: {e}")
            return None

    def get_all_prices(self) -> list[tuple[timestamp, float]]:
        """Get all btc prices from the btc_price table."""
        try:
            with self.connection.cursor() as cursor:
                query = sql.SQL(
                    "SELECT timestamp, price FROM {}").format(
                    sql.Identifier(Tables.BTC_PRICE.value))
                cursor.execute(query)
                result = cursor.fetchall()
            return result
        except Exception as e:
            if not self.is_connected():
                self.connect()
            print(f"Failed to get all prices: {e}")
            return []

    def add_indicator(self, table: Tables, timestamp: timestamp,
                    indicator_name: str, value: float, signal: str) -> bool:
        """Add the indicator to the specified table."""
        try:
            with self.connection.cursor() as cursor:
                query = sql.SQL(
                    "INSERT INTO {} (timestamp, indicator_name, value, signal) VALUES (%s, %s, %s, %s)").format(
                    sql.Identifier(table.value))
                cursor.execute(query, (timestamp, indicator_name, value, signal))
            self.connection.commit()
            return True
        except Exception as e:
            if not self.is_connected():
                self.connect()
            print(f"Failed to add indicator: {e}")
            return False

    def delete_indicator(self, table: Tables, timestamp: timestamp) -> bool:
        """Delete the indicator from the specified table."""
        try:
            with self.connection.cursor() as cursor:
                query = sql.SQL(
                    "DELETE FROM {} WHERE timestamp = %s").format(
                    sql.Identifier(table.value))
                cursor.execute(query, (timestamp,))
            self.connection.commit()
            return True
        except Exception as e:
            if not self.is_connected():
                self.connect()
            print(f"Failed to delete indicator: {e}")
            return False

    def get_indicator(self, table: Tables, timestamp: timestamp) -> list[tuple[str, float, str]]:
        """Get the indicator from the specified table."""
        try:
            with self.connection.cursor() as cursor:
                query = sql.SQL(
                    "SELECT indicator_name, value, signal FROM {} WHERE timestamp = %s").format(
                    sql.Identifier(table.value))
                cursor.execute(query, (timestamp,))
                result = cursor.fetchall()
            return result
        except Exception as e:
            if not self.is_connected():
                self.connect()
            print(f"Failed to get indicator: {e}")
            return []

    def get_all_indicators(self, table: Tables) -> list[tuple[timestamp, str, float, str]]:
        """Get all indicators from the specified table."""
        try:
            with self.connection.cursor() as cursor:
                query = sql.SQL(
                    "SELECT timestamp, indicator_name, value, signal FROM {}").format(
                    sql.Identifier(table.value))
                cursor.execute(query)
                result = cursor.fetchall()
            return result
        except Exception as e:
            if not self.is_connected():
                self.connect()
            print(f"Failed to get all indicators: {e}")
            return []


if __name__ == "__main__":
    def format_timestamp(ts: timestamp) -> timestamp:
        """YYYY-MM-DD HH:MM:00"""
        return ts.replace(second=0, microsecond=0)

    db = DBUtils()
    # Test adding a price
    test_timestamp = format_timestamp(timestamp.now())
    test_price = 12345.67
    if db.add_price(test_timestamp, test_price):
        print(f"Price {test_price} added successfully.")
    else:
        print("Failed to add price.")
    # Test getting a price
    price = db.get_price(test_timestamp)
    if price is not None:
        print(f"Price at {test_timestamp}: {price}")
    else:
        print("Failed to get price.")
    # Test deleting a price
    if db.delete_price(test_timestamp):
        print(f"Price at {test_timestamp} deleted successfully.")
    else:
        print("Failed to delete price.")
    # Test getting all prices
    all_prices = db.get_all_prices()
    if all_prices:
        print("All prices:")
        for ts, price in all_prices:
            print(f"{ts}: {price}")
    else:
        print("Failed to get all prices.")
    # Test adding an indicator
    test_indicator = "RSI"
    test_value = 70.0
    test_signal = "BUY"
    if db.add_indicator(Tables.INDICATOR_1MIN, test_timestamp,
                        test_indicator, test_value, test_signal):
        print(f"Indicator {test_indicator} added successfully.")
    else:
        print("Failed to add indicator.")
    # Test getting an indicator
    indicator = db.get_indicator(Tables.INDICATOR_1MIN, test_timestamp)
    if indicator:
        print(f"Indicator at {test_timestamp}: {indicator}")
    else:
        print("Failed to get indicator.")
    # Test getting all indicators
    all_indicators = db.get_all_indicators(Tables.INDICATOR_1MIN)
    if all_indicators:
        print("All indicators:")
        for ts, name, value, signal in all_indicators:
            print(f"{ts}: {name}, {value}, {signal}")
    else:
        print("Failed to get all indicators.")
    # Test deleting an indicator
    if db.delete_indicator(Tables.INDICATOR_1MIN, test_timestamp):
        print(f"Indicator at {test_timestamp} deleted successfully.")
    else:
        print("Failed to delete indicator.")

    # Close the database connection
    db.close()
