import MetaTrader5 as mt5
from datetime import datetime
import pandas as pd
import sqlite3
import time

# --- Database Setup and Connection ---
DB_NAME = 'mt5_trades.db'

def create_connection():
    """Create a SQLite database connection and return the connection object."""
    conn = None
    try:
        conn = sqlite3.connect(DB_NAME)
        return conn
    except sqlite3.Error as e:
        print(f"Error connecting to database: {e}")
        return None

# --- MetaTrader 5 and Pandas Setup ---
pd.set_option('display.max_columns', 500)  # number of columns to be displayed
pd.set_option('display.width', 1500)       # max table width to display

print("MetaTrader5 package author: ", mt5.__author__)
print("MetaTrader5 package version: ", mt5.__version__)
print()

# --- Data Fetching and Saving Functions ---
def fetch_and_save_orders(conn):
    """
    Fetches new order history and saves it to the 'orders' table.
    The function checks the last saved entry to avoid duplicates.
    """
    # Get the latest timestamp from the 'orders' table to prevent duplicates
    query = "SELECT MAX(time_done) FROM orders_live"
    latest_timestamp = None
    try:
        cursor = conn.cursor()
        cursor.execute(query)
        result = cursor.fetchone()[0]
        if result:
            latest_timestamp = pd.to_datetime(result)
    except sqlite3.OperationalError:
        # Table might not exist yet on the first run, so we ignore the error.
        pass

    # Set the starting date for MT5 data retrieval
    from_date = latest_timestamp if latest_timestamp else datetime(2025, 9, 1)
    to_date = datetime.now()
    
    orders = mt5.history_orders_get(from_date, to_date)
    
    if orders is None or len(orders) == 0:
        print("No new history orders found.")
        return

    # Convert to DataFrame
    try:
        df_orders = pd.DataFrame(list(orders), columns=orders[0]._asdict().keys())
        
        # Clean and prepare the DataFrame
        # columns_to_drop = ['time_expiration', 'type_time', 'state', 'position_by_id', 'reason', 'volume_current', 'price_stoplimit', 'sl', 'tp']
        # columns_to_drop = [ 'volume_current']        
        # existing_columns_to_drop = [col for col in columns_to_drop if col in df_orders.columns]
        # if existing_columns_to_drop:
        #     df_orders.drop(columns=existing_columns_to_drop, axis=1, inplace=True)
            
        df_orders['time_setup'] = pd.to_datetime(df_orders['time_setup'], unit='s')
        df_orders['time_done'] = pd.to_datetime(df_orders['time_done'], unit='s')
        
        # Filter out records that are already in the database
        if latest_timestamp:
            df_orders = df_orders[df_orders['time_done'] > latest_timestamp]

        if not df_orders.empty:
            df_orders.to_sql('orders_live', conn, if_exists='append', index=False)
            print(f"Saved {len(df_orders)} new orders to mt5_trades.db -> 'orders_live' table.")
        else:
            print("No new orders to save.")
        
    except Exception as e:
        print(f"An error occurred while processing and saving new orders: {e}")

def fetch_and_save_deals(conn):
    """
    Fetches new deals history and saves it to the 'deals' table.
    The function checks the last saved entry to avoid duplicates.
    """
    # Get the latest timestamp from the 'deals' table to prevent duplicates
    query = "SELECT MAX(time) FROM deals_live"
    latest_timestamp = None
    try:
        cursor = conn.cursor()
        cursor.execute(query)
        result = cursor.fetchone()[0]
        if result:
            latest_timestamp = pd.to_datetime(result)
    except sqlite3.OperationalError:
        # Table might not exist yet on the first run, so we ignore the error.
        pass

    # Set the starting date for MT5 data retrieval
    from_date = latest_timestamp if latest_timestamp else datetime(2025, 9, 1)
    to_date = datetime.now()
    
    deals = mt5.history_deals_get(from_date, to_date)
    
    if deals is None or len(deals) == 0:
        print("No new history deals found.")
        return

    # Convert to DataFrame
    try:
        df_deals = pd.DataFrame(list(deals), columns=deals[0]._asdict().keys())
        
        # Clean and prepare the DataFrame
        df_deals['time'] = pd.to_datetime(df_deals['time'], unit='s')

        # Filter out records that are already in the database
        if latest_timestamp:
            df_deals = df_deals[df_deals['time'] > latest_timestamp]

        if not df_deals.empty:
            df_deals.to_sql('deals_live', conn, if_exists='append', index=False)
            print(f"Saved {len(df_deals)} new deals to mt5_trades.db -> 'deals_live' table.")
        else:
            print("No new deals to save.")
        
    except Exception as e:
        print(f"An error occurred while processing and saving new deals: {e}")

# --- Main Loop ---
if __name__ == "__main__":
    if not mt5.initialize():
        print("initialize() failed, error code =", mt5.last_error())
        quit()
    
    conn = create_connection()
    if conn is None:
        print("Could not establish database connection. Exiting.")
        mt5.shutdown()
        quit()
        
    try:
        print("Starting data retrieval loop. Press Ctrl+C to stop.")
        while True:
            print("-" * 30)
            print(f"Execution started at: {datetime.now()}")
            
            fetch_and_save_orders(conn)
            fetch_and_save_deals(conn)
            
            # The sleep time is set to 2 minutes and 5 seconds (125 seconds)
            sleep_duration = 125
            print(f"Completed. Sleeping for {sleep_duration} seconds until next run.")
            print("-" * 30)
            time.sleep(sleep_duration)

    except KeyboardInterrupt:
        print("\nScript terminated by user.")
    except Exception as e:
        print(f"An unexpected error occurred in the main loop: {e}")
    finally:
        if conn:
            conn.close()
        mt5.shutdown()
        print("MT5 connection shut down.")
        print("Database connection closed.")
