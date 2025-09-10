import MetaTrader5 as mt5
import pandas as pd
import sqlite3
import time
from datetime import datetime

# --- Configuration ---
DB_NAME = 'market_data.db'
TABLE_NAME = 'gold'
SYMBOL = 'GOLD#'
# The number of candlesticks to capture for the initial population.
INITIAL_CANDLES_COUNT = 20000
# Timeframe is set to M1 (1-minute)
TIMEFRAME = mt5.TIMEFRAME_M1

def create_connection():
    """Create a SQLite database connection and return the connection object."""
    conn = None
    try:
        conn = sqlite3.connect(DB_NAME)
        return conn
    except sqlite3.Error as e:
        print(f"Error connecting to database: {e}")
        return None

def create_table(conn):
    """
    Creates the 'gold' table with columns for time, open, high, low, and close.
    The 'time' column is a primary key to ensure no duplicate entries.
    """
    try:
        cursor = conn.cursor()
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
                time INTEGER PRIMARY KEY,
                open REAL,
                high REAL,
                low REAL,
                close REAL
            );
        """)
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error creating table: {e}")

def get_last_db_timestamp(conn):
    """
    Retrieves the timestamp of the last entry in the database.
    Returns None if the table is empty.
    
    This function now handles cases where the timestamp might be stored as
    a string due to previous errors.
    """
    try:
        cursor = conn.cursor()
        cursor.execute(f"SELECT MAX(time) FROM {TABLE_NAME}")
        result = cursor.fetchone()
        
        if result[0] is None:
            return None
        
        # Check if the result is already an integer (the correct format)
        if isinstance(result[0], int):
            return result[0]
        
        # If it's a string, try to parse it as a datetime and convert to an integer timestamp
        if isinstance(result[0], str):
            try:
                dt_object = datetime.strptime(result[0], '%Y-%m-%d %H:%M:%S')
                return int(dt_object.timestamp())
            except ValueError:
                print(f"Warning: Could not convert database timestamp string '{result[0]}'.")
                return None
                
    except sqlite3.Error as e:
        print(f"Error getting last timestamp: {e}")
        return None

def populate_initial_data(conn, symbol, timeframe, count):
    """
    Populates the database with the initial set of historical data.
    """
    print(f"Populating initial data for {symbol}...")
    # Get the last 'count' candlesticks from MT5 starting from the current position.
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)

    if rates is None or len(rates) == 0:
        print("No historical data received from MT5.")
        return False

    # Convert the received data to a pandas DataFrame
    rates_frame = pd.DataFrame(rates)
    
    # Explicitly convert the 'time' column to integer timestamps (seconds)
    # before writing to the database to ensure data type consistency.
    rates_frame['time'] = pd.to_datetime(rates_frame['time'], unit='s').astype('int64') // 10**9

    # Drop any existing table content and insert the new data
    try:
        rates_frame.to_sql(TABLE_NAME, conn, if_exists='replace', index=False)
        print(f"Successfully populated {len(rates_frame)} records.")
        return True
    except sqlite3.Error as e:
        print(f"Error inserting initial data: {e}")
        return False

def check_and_fill_gaps(conn, symbol, timeframe, last_db_timestamp):
    """
    Checks for and fills any time gaps in the data since the last database entry.
    """
    if last_db_timestamp is None:
        print("Database is empty, no gaps to check.")
        return

    # Convert the last database timestamp back to a datetime object
    from_time = datetime.fromtimestamp(last_db_timestamp)
    now = datetime.now()

    # Get all rates from the last known timestamp up to now
    rates = mt5.copy_rates_range(symbol, timeframe, from_time, now)

    # Check if there are new records to fetch
    if rates is None or len(rates) <= 1:
        return

    # Convert to DataFrame
    rates_frame = pd.DataFrame(rates)
    
    # Convert 'time' column to integer timestamps to match the database's data type
    rates_frame['time'] = pd.to_datetime(rates_frame['time'], unit='s').astype('int64') // 10**9
    
    # Filter out the existing last entry to avoid duplicates
    new_data = rates_frame[rates_frame['time'] > last_db_timestamp]

    if not new_data.empty:
        print(f"Found and filling a gap of {len(new_data)} missing records.")
        # Insert the new data into the table
        try:
            new_data.to_sql(TABLE_NAME, conn, if_exists='append', index=False)
            print("Successfully filled the gap.")
        except sqlite3.Error as e:
            print(f"Error filling gap: {e}")
    else:
        print("No gaps found. Database is up to date.")

def update_data_realtime(conn, symbol, timeframe):
    """
    Continuously updates the database with new M1 candlesticks every minute.
    """
    while True:
        try:
            # Get the timestamp of the last entry in the database.
            last_db_timestamp = get_last_db_timestamp(conn)

            # Check for and fill any gaps before appending new data
            check_and_fill_gaps(conn, symbol, timeframe, last_db_timestamp)

            # Wait for the next minute to get the new candlestick
            now_minute = datetime.now().minute
            while now_minute == datetime.now().minute:
                time.sleep(1) # Wait for the minute to change.

            # Get the very latest M1 candlestick
            rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, 1)

            if rates is None or len(rates) == 0:
                print("No data received from MT5. Retrying in 60 seconds.")
                time.sleep(60)
                continue

            latest_rate = rates[0]
            latest_timestamp = latest_rate['time']

            # Check if this candlestick is new before inserting
            if last_db_timestamp is None or latest_timestamp > last_db_timestamp:
                df_to_insert = pd.DataFrame([latest_rate])
                df_to_insert.to_sql(TABLE_NAME, conn, if_exists='append', index=False)
                print(f"Added new record: {datetime.fromtimestamp(latest_timestamp)}")
            else:
                print("Latest record is already in the database. Waiting for the next minute...")

            time.sleep(60) # Wait for a full minute for the next update

        except KeyboardInterrupt:
            print("Real-time update interrupted by user. Exiting.")
            break
        except Exception as e:
            print(f"An error occurred in the real-time loop: {e}. Retrying in 60 seconds.")
            time.sleep(60)

def main():
    """
    Main function to run the market data collection process.
    """
    # Initialize connection to MT5
    if not mt5.initialize():
        print("initialize() failed, error code =", mt5.last_error())
        mt5.shutdown()
        return

    # Create a database connection
    conn = create_connection()
    if conn is None:
        return

    # Create the table if it doesn't exist
    create_table(conn)

    try:
        # Check if the table has any data
        last_db_timestamp = get_last_db_timestamp(conn)
        
        if last_db_timestamp is None:
            # Table is empty, perform the initial population
            success = populate_initial_data(conn, SYMBOL, TIMEFRAME, INITIAL_CANDLES_COUNT)
            if not success:
                print("Failed to populate initial data. Exiting.")
                return

        # Start the real-time update loop
        print("\nStarting real-time data collection. Press Ctrl+C to exit.")
        update_data_realtime(conn, SYMBOL, TIMEFRAME)

    finally:
        # Clean up connections
        if conn:
            conn.close()
        mt5.shutdown()
        print("MT5 connection closed.")

if __name__ == "__main__":
    main()
