import MetaTrader5 as mt5
import pandas as pd
import sqlite3
import time
from datetime import datetime
from rich.console import Console
from rich.table import Table

# --- Configuration ---
DB_NAME = 'market_data.db'
TABLE_NAME = 'gold'
SYMBOL = 'GOLDm#'
INITIAL_CANDLES_COUNT = 20000
TIMEFRAME = mt5.TIMEFRAME_M1

console = Console()

class MarketDataCollector:
    def __init__(self):
        self.conn = None
        self.last_record = None
        self.status_message = "Initializing..."
        
    def create_connection(self):
        """Create a SQLite database connection and return the connection object."""
        try:
            self.conn = sqlite3.connect(DB_NAME)
            return True
        except sqlite3.Error as e:
            console.print(f"[red]Error connecting to database: {e}[/red]")
            return False

    def create_table(self):
        """Creates the 'gold' table with columns for time, open, high, low, and close."""
        try:
            cursor = self.conn.cursor()
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
                    time INTEGER PRIMARY KEY,
                    open REAL,
                    high REAL,
                    low REAL,
                    close REAL
                );
            """)
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            console.print(f"[red]Error creating table: {e}[/red]")
            return False

    def get_last_db_timestamp(self):
        """Retrieves the timestamp of the last entry in the database."""
        try:
            cursor = self.conn.cursor()
            cursor.execute(f"SELECT MAX(time) FROM {TABLE_NAME}")
            result = cursor.fetchone()
            
            if result[0] is None:
                return None
            
            return result[0]
                    
        except sqlite3.Error as e:
            console.print(f"[red]Error getting last timestamp: {e}[/red]")
            return None

    def populate_initial_data(self, symbol, timeframe, count):
        """Populates the database with the initial set of historical data."""
        self.status_message = f"Populating initial data for {symbol}..."
        console.print(f"[bold white]{self.status_message}[/bold white]")
        
        # We fetch one more than required to discard the open candle
        rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count + 1)
        
        if rates is None or len(rates) <= 1:
            self.status_message = "No historical data received from MT5 or not enough data to get completed candles"
            console.print(f"[red]{self.status_message}[/red]")
            return False

        # Drop the last (open) candle
        rates_frame = pd.DataFrame(rates)[:-1]
        
        # Keep the raw integer timestamp
        rates_frame['time'] = pd.to_datetime(rates_frame['time'], unit='s').astype('int64') // 10**9

        try:
            rates_frame[['time', 'open', 'high', 'low', 'close']].to_sql(TABLE_NAME, self.conn, if_exists='replace', index=False)
            self.status_message = f"Successfully populated {len(rates_frame)} records"
            console.print(f"[green]✓ {self.status_message}[/green]")
            return True
        except sqlite3.Error as e:
            self.status_message = f"Error inserting initial data: {e}"
            console.print(f"[red]{self.status_message}[/red]")
            return False

    def get_latest_completed_candlestick(self, symbol, timeframe):
        """Get the latest completed candlestick from MT5 and format it properly."""
        rates = mt5.copy_rates_from_pos(symbol, timeframe, 1, 1) 
        
        if rates is None or len(rates) == 0:
            return None
            
        latest_rate = rates[0]
        
        original_time = datetime.fromtimestamp(latest_rate['time'])
        
        candlestick_data = {
            'time': int(original_time.timestamp()),
            'open': float(latest_rate['open']),
            'high': float(latest_rate['high']),
            'low': float(latest_rate['low']),
            'close': float(latest_rate['close'])
        }
        
        return candlestick_data

    def get_latest_completed_candlestick_timestamp(self, symbol, timeframe):
        """Get the timestamp of the latest completed candlestick from MT5."""
        rates = mt5.copy_rates_from_pos(symbol, timeframe, 1, 1)
        if rates is None or len(rates) == 0:
            return None
        return int(rates[0]['time'])

    def check_and_fill_gaps(self, symbol, timeframe, last_db_timestamp):
        """Checks for and fills any time gaps in the data since the last database entry."""
        if last_db_timestamp is None:
            return 0

        latest_mt5_timestamp = self.get_latest_completed_candlestick_timestamp(symbol, timeframe)
        
        if latest_mt5_timestamp is None:
            console.print("[dim]Could not retrieve latest MT5 timestamp. Cannot check for gaps.[/dim]")
            return 0

        if last_db_timestamp >= latest_mt5_timestamp:
            console.print("[dim]Database is up to date. No gaps to fill.[/dim]")
            return 0
            
        console.print(f"[yellow]Gap detected: last DB record at {datetime.fromtimestamp(last_db_timestamp).strftime('%Y-%m-%d %H:%M:%S')} vs latest MT5 candle at {datetime.fromtimestamp(latest_mt5_timestamp).strftime('%Y-%m-%d %H:%M:%S')}.[/yellow]")

        # Fetch candles from the timestamp AFTER the last record up to the latest MT5 candle
        from_time = datetime.fromtimestamp(last_db_timestamp + 60)
        to_time = datetime.fromtimestamp(latest_mt5_timestamp)
        
        rates = mt5.copy_rates_range(symbol, timeframe, from_time, to_time)

        if rates is None or len(rates) == 0:
            console.print("[dim]No new completed candles to add for the gap.[/dim]")
            return 0

        rates_frame = pd.DataFrame(rates)
        
        # Keep the raw integer timestamp
        rates_frame['time'] = pd.to_datetime(rates_frame['time'], unit='s').astype('int64') // 10**9
        
        try:
            num_new_records = len(rates_frame)
            self.status_message = f"Found and filling a gap of {num_new_records} missing records"
            console.print(f"[yellow]{self.status_message}[/yellow]")
            rates_frame[['time', 'open', 'high', 'low', 'close']].to_sql(TABLE_NAME, self.conn, if_exists='append', index=False)
            self.status_message = f"Successfully filled the gap with {num_new_records} records"
            console.print(f"[green]✓ {self.status_message}[/green]")
            return num_new_records
        except sqlite3.Error as e:
            self.status_message = f"Error filling gap: {e}"
            console.print(f"[red]{self.status_message}[/red]")
            return 0
        
    def insert_candlestick(self, candlestick_data):
        """Insert a single candlestick into the database."""
        try:
            cursor = self.conn.cursor()
            cursor.execute(f"""
                INSERT OR REPLACE INTO {TABLE_NAME} (time, open, high, low, close)
                VALUES (?, ?, ?, ?, ?)
            """, (
                candlestick_data['time'],
                candlestick_data['open'],
                candlestick_data['high'],
                candlestick_data['low'],
                candlestick_data['close']
            ))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            self.status_message = f"Error inserting candlestick: {e}"
            console.print(f"[red]{self.status_message}[/red]")
            return False

    def update_data_realtime(self, symbol, timeframe):
        """Continuously updates the database with new M1 candlesticks every minute."""
        last_db_timestamp = self.get_last_db_timestamp()
        
        while True:
            try:
                now = datetime.now()
                seconds_to_wait = (60 - now.second) % 60
                
                if seconds_to_wait == 0:
                    time.sleep(60)
                else:
                    time.sleep(seconds_to_wait + 0.02)

                latest_candlestick = self.get_latest_completed_candlestick(symbol, timeframe)
                
                if latest_candlestick:
                    latest_timestamp = latest_candlestick['time']
                    
                    if last_db_timestamp is None or latest_timestamp > last_db_timestamp:
                        self.insert_candlestick(latest_candlestick)
                        last_db_timestamp = latest_timestamp
                        
                        dt = datetime.fromtimestamp(latest_timestamp)
                        console.print(f"[green]✓ New completed candle added: Time: {dt.strftime('%Y-%m-%d %H:%M:%S')}, Close: {latest_candlestick['close']:.5f}[/green]")
                    else:
                        console.print(f"[dim]No new completed candles to add.[/dim]")
                else:
                    console.print(f"[red]Failed to fetch latest completed candle. Retrying...[/red]")
                
            except KeyboardInterrupt:
                self.status_message = "Real-time update interrupted by user. Exiting."
                console.print("\n[yellow]Real-time update interrupted by user. Exiting.[/yellow]")
                break
            except Exception as e:
                self.status_message = f"Error occurred: {e}. Retrying..."
                console.print(f"[red]An error occurred: {e}. Retrying...[/red]")
                time.sleep(10)

def main():
    """Main function to run the market data collection process."""
    collector = MarketDataCollector()
    
    console.print("[bold cyan]Market Data Collector Starting...[/bold cyan]")
    
    if not mt5.initialize():
        console.print(f"[red]MT5 initialize() failed, error code = {mt5.last_error()}[/red]")
        mt5.shutdown()
        return

    console.print("[green]✓ MT5 connection established[/green]")

    if not collector.create_connection():
        console.print("[red]Failed to create database connection[/red]")
        return

    console.print("[green]✓ Database connection established[/green]")

    if not collector.create_table():
        console.print("[red]Failed to create database table[/red]")
        return

    console.print("[green]✓ Database table ready[/green]")

    try:
        last_db_timestamp = collector.get_last_db_timestamp()
        
        if last_db_timestamp is None:
            console.print("[yellow]Table is empty, performing initial population...[/yellow]")
            success = collector.populate_initial_data(SYMBOL, TIMEFRAME, INITIAL_CANDLES_COUNT)
            if not success:
                console.print("[red]Failed to populate initial data. Exiting.[/red]")
                return
            console.print("[green]✓ Initial data population completed[/green]")
        else:
            console.print(f"[yellow]Table is not empty. Checking for data gaps since {datetime.fromtimestamp(last_db_timestamp).strftime('%Y-%m-%d %H:%M:%S')}...[/yellow]")
            collector.check_and_fill_gaps(SYMBOL, TIMEFRAME, last_db_timestamp)
        
        console.print("\n[bold green]Starting real-time data collection. Press Ctrl+C to exit.[/bold green]")
        time.sleep(1)
        collector.update_data_realtime(SYMBOL, TIMEFRAME)

    finally:
        if collector.conn:
            collector.conn.close()
        mt5.shutdown()
        console.print("[cyan]MT5 connection closed. Goodbye![/cyan]")

if __name__ == "__main__":
    main()
