import sqlite3
import logging
from datetime import datetime
import os

# Configure logging for entries.py
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler("entries.log", encoding='utf-8'),
                        logging.StreamHandler()
                    ])

DATABASE_NAME = 'mt5_trades.db'

def get_db_connection():
    """Establishes a connection to the SQLite database."""
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        conn.row_factory = sqlite3.Row # This allows accessing columns by name
        logging.info(f"Successfully connected to database: {DATABASE_NAME}")
    except sqlite3.Error as e:
        logging.error(f"Error connecting to database: {e}")
    return conn

def create_entries_table():
    """Creates the 'entries' table if it doesn't exist."""
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    file_name TEXT,
                    account_no INTEGER,
                    account_type TEXT,
                    server TEXT,
                    strategy_id INTEGER,
                    symbol TEXT,
                    trend_timeframe TEXT,
                    entry_timeframe TEXT,
                    deviation INTEGER,
                    SL_POINTS INTEGER,
                    TP_POINTS INTEGER,
                    EMA_DISTANCE_THRESHOLD INTEGER,
                    MAX_OPEN_TRADES_PER_MAGIC INTEGER,
                    EMA_PERIOD INTEGER,
                    TRADING_HOURS_START INTEGER,
                    TRADING_HOURS_END INTEGER,
                    latest_ema REAL,
                    ema_distance_m2 INTEGER,
                    signal TEXT,
                    trade_type TEXT,
                    current_price REAL,
                    sl_price REAL,
                    tp_price REAL,
                    deal_ticket INTEGER,
                    trade_note TEXT,
                    order_ticket INTEGER       
                )
            ''')
            conn.commit()
            logging.info("Table 'entries' checked/created successfully.")
        except sqlite3.Error as e:
            logging.error(f"Error creating table 'entries': {e}")
        finally:
            if conn:
                conn.close()

def insert_entry(data):
    """Inserts a new trade entry into the 'entries' table."""
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO entries (
                    file_name, account_no, account_type, server, strategy_id, symbol,
                    trend_timeframe, entry_timeframe, deviation, SL_POINTS, TP_POINTS,
                    EMA_DISTANCE_THRESHOLD, MAX_OPEN_TRADES_PER_MAGIC, EMA_PERIOD,
                    TRADING_HOURS_START, TRADING_HOURS_END, latest_ema, ema_distance_m2,
                    signal, trade_type, current_price, sl_price, tp_price, deal_ticket,trade_note, order_ticket
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,?,?)
            ''', (
                data.get('file_name'),
                data.get('account_no'),
                data.get('account_type'),
                data.get('server'),
                data.get('strategy_id'),
                data.get('symbol'),
                data.get('trend_timeframe'),
                data.get('entry_timeframe'),
                data.get('deviation'),
                data.get('SL_POINTS'),
                data.get('TP_POINTS'),
                data.get('EMA_DISTANCE_THRESHOLD'),
                data.get('MAX_OPEN_TRADES_PER_MAGIC'),
                data.get('EMA_PERIOD'),
                data.get('TRADING_HOURS_START'),
                data.get('TRADING_HOURS_END'),
                data.get('latest_ema'),
                data.get('ema_distance_m2'),
                data.get('signal'),
                data.get('trade_type'),
                data.get('current_price'),
                data.get('sl_price'),
                data.get('tp_price'),
                data.get('deal_ticket'),
                data.get('trade_note'),
                data.get('order_ticket')
            ))
            conn.commit()
            logging.info(f"Trade entry recorded successfully. Deal Ticket: {data.get('deal_ticket')}")
            return True
        except sqlite3.Error as e:
            logging.error(f"Error inserting trade entry: {e}")
            return False
        finally:
            if conn:
                conn.close()

# Ensure the table is created when this module is imported
create_entries_table()

if __name__ == "__main__":
    # Example usage:
    print("Running entries.py directly. This will ensure the table is created.")
    # You can add a test insertion here if needed
    # test_data = {
    #     'file_name': 'strategy_01.py',
    #     'account_no': 12345,
    #     'account_type': 'Demo',
    #     'server': 'TestServer',
    #     'strategy_id': 1001,
    #     'symbol': 'EURUSD',
    #     'trend_timeframe': 'M15',
    #     'deviation': 10,
    #     'SL_POINTS': 50,
    #     'TP_POINTS': 100,
    #     'EMA_DISTANCE_THRESHOLD': 200,
    #     'MAX_OPEN_TRADES_PER_MAGIC': 1,
    #     'EMA_PERIOD': 20,
    #     'TRADING_HOURS_START': 8,
    #     'TRADING_HOURS_END': 22,
    #     'latest_ema': 1.12345,
    #     'ema_distance_m2': 50,
    #     'signal': 'buy',
    #     'trade_type': 'BUY',
    #     'current_price': 1.12350,
    #     'sl_price': 1.12300,
    #     'tp_price': 1.12450,
    #     'deal_ticket': 12345678
    # }
    # if insert_entry(test_data):
    #     print("Test entry inserted.")
    # else:
    #     print("Failed to insert test entry.")