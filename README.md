# crypto_market_indicator_logger
This repo aims to collect bitcoin price and 25 indicators data per minute and runs in local server, updates local PostGre server.

# Setup
- Install requirements with `pip3 install -r requirements.txt` (venv preferred).
- Install PostGreSQL with timescaleDB extension to your machine and create server and db.
- Create tables defined below.
- Install chromedriver for selenium. And install/update chrome if needed.
- Get your application password from google security for mail sending.
- Create a .env file: 
```
# Selenium WebDriver
P_PATH_TO_DRIVER = "/path/to/your/chromedriver"

# Email Configuration
P_SENDER_MAIL = "your_email@example.com"
P_PASSWORD = "your_email_password"
P_RECEIVER_MAIL = "receiver_email@example.com"

# Database Configuration
P_DBNAME = "your_database_name"
P_USER = "your_database_user"
P_PASSWORD = "your_database_password"
P_HOST = "your_database_host"
P_PORT = "5432"

# Log File Path
P_LOG_PATH = "/path/to/your/logfile.log"
```
- Can be used with cronjob or systemctl service, depends on purpose. 

# Tables
- btc_price:
```SQL
CREATE TABLE btc_price (
    timestamp TIMESTAMP PRIMARY KEY,
    price NUMERIC
);
```
- intervals = ['1min', '5min', '15min', '30min', '1hours', '2hours', '4hours', '1day' '1week', '1month']
- indicator (create 10 tables):
```SQL
CREATE TABLE indicator_{intervals[i]} (
    timestamp TIMESTAMP,
    indicator_name VARCHAR(50),
    value NUMERIC,
    signal VARCHAR(10),
    PRIMARY KEY (timestamp, indicator_name)
);
```

## Collaboration
Collaborated with [Şevval Bulburu](https://github.com/sevvalbulburu)
