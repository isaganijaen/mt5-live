import MetaTrader5 as mt5
import pandas as pd
import sqlite3
import time
from datetime import datetime
import threading
from rich.console import Console
from rich.table import Table

# --- Configuration ---
DB_NAME = 'market_data.db'
TABLE_NAME = 'gold'
SYMBOL = 'GOLD#'
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
            
            if isinstance(result[0], int):
                return result[0]
            
            if isinstance(result[0], str):
                try:
                    dt_object = datetime.strptime(result[0], '%Y-%m-%d %H:%M:%S')
                    return int(dt_object.timestamp())
                except ValueError:
                    console.print(f"[yellow]Warning: Could not convert database timestamp string '{result[0]}'.[/yellow]")
                    return None
                    
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

    def check_and_fill_gaps(self, symbol, timeframe, last_db_timestamp):
        """Checks for and fills any time gaps in the data since the last database entry."""
        if last_db_timestamp is None:
            return

        from_time = datetime.fromtimestamp(last_db_timestamp)
        now = datetime.now()

        # Fetch all candles since the last DB timestamp, plus one to discard the open candle
        rates = mt5.copy_rates_range(symbol, timeframe, from_time, now)

        if rates is None or len(rates) <= 1:
            return

        # Convert to DataFrame and drop the last (open) candle
        rates_frame = pd.DataFrame(rates)[:-1]
        
        # Keep the raw integer timestamp
        rates_frame['time'] = pd.to_datetime(rates_frame['time'], unit='s').astype('int64') // 10**9
        
        new_data = rates_frame[rates_frame['time'] > last_db_timestamp]

        if not new_data.empty:
            self.status_message = f"Found and filling a gap of {len(new_data)} missing records"
            console.print(f"[yellow]{self.status_message}[/yellow]")
            try:
                new_data[['time', 'open', 'high', 'low', 'close']].to_sql(TABLE_NAME, self.conn, if_exists='append', index=False)
                self.status_message = "Successfully filled the gap"
                console.print(f"[green]✓ {self.status_message}[/green]")
            except sqlite3.Error as e:
                self.status_message = f"Error filling gap: {e}"
                console.print(f"[red]{self.status_message}[/red]")

    def get_latest_completed_candlestick(self, symbol, timeframe):
        """Get the latest completed candlestick from MT5 and format it properly."""
        # Get the second to last candle, which is the last completed one.
        # This is more robust than fetching the last candle and checking its time.
        rates = mt5.copy_rates_from_pos(symbol, timeframe, 1, 1) 
        
        if rates is None or len(rates) == 0:
            return None
            
        latest_rate = rates[0]
        
        # Get the raw timestamp
        original_time = datetime.fromtimestamp(latest_rate['time'])
        
        # Convert numpy array to proper dictionary format
        candlestick_data = {
            'time': int(original_time.timestamp()),
            'open': float(latest_rate['open']),
            'high': float(latest_rate['high']),
            'low': float(latest_rate['low']),
            'close': float(latest_rate['close'])
        }
        
        return candlestick_data

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

    def display_all_data(self):
        """Reads all data from the database, sorts by time, and prints to console."""
        try:
            cursor = self.conn.cursor()
            cursor.execute(f"SELECT * FROM {TABLE_NAME} ORDER BY time ASC")
            all_data = cursor.fetchall()

            if not all_data:
                console.print("[dim]No data to display.[/dim]")
                return

            table = Table(title="Captured Market Data", style="bold magenta")
            table.add_column("Time", style="cyan")
            table.add_column("Open", style="green")
            table.add_column("High", style="bright_green")
            table.add_column("Low", style="red")
            table.add_column("Close", style="yellow")
            
            for row in all_data:
                timestamp = datetime.fromtimestamp(row[0])
                table.add_row(
                    timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                    f"{row[1]:.5f}",
                    f"{row[2]:.5f}",
                    f"{row[3]:.5f}",
                    f"{row[4]:.5f}"
                )
            
            console.print(table)
        except sqlite3.Error as e:
            console.print(f"[red]Error displaying data: {e}[/red]")
        
    def update_data_realtime(self, symbol, timeframe):
        """Continuously updates the database with new M1 candlesticks every minute."""
        while True:
            try:
                # Get the timestamp of the last entry in the database
                last_db_timestamp = self.get_last_db_timestamp()

                # Check for and fill any gaps before appending new data
                self.check_and_fill_gaps(symbol, timeframe, last_db_timestamp)

                # Wait for the next minute boundary + 2 seconds for a total delay of 5 seconds
                now = datetime.now()
                seconds_remaining = 60 - now.second - (now.microsecond / 1000000.0)
                
                # We need to wait for the next minute boundary plus the 2-second delay.
                delay_needed = seconds_remaining + 2
                
                if delay_needed > 0:
                    console.print(f"[dim]Next update in {delay_needed:.1f} seconds...[/dim]", end='\r')
                    time.sleep(delay_needed)
                
                # Get the latest COMPLETED candlestick
                self.status_message = "Fetching latest completed candlestick..."
                console.print(f"[dim]{self.status_message}[/dim]")
                
                # Get the last completed candlestick by starting from position 1, which is the second-to-last candle.
                latest_candlestick = self.get_latest_completed_candlestick(SYMBOL, TIMEFRAME)

                if latest_candlestick is None:
                    self.status_message = "No data received from MT5. Retrying at next minute."
                    console.print(f"[red]{self.status_message}[/red]")
                    continue

                latest_timestamp = latest_candlestick['time']

                # Check if this candlestick is new before inserting
                if last_db_timestamp is None or latest_timestamp > last_db_timestamp:
                    if self.insert_candlestick(latest_candlestick):
                        self.last_record = latest_candlestick
                        self.status_message = f"Added new record: {latest_timestamp}"
                        
                        dt = datetime.fromtimestamp(latest_timestamp)
                        # Print only the newly added candle
                        console.print(f"[green]✓ New completed candle added: Time: {dt.strftime('%Y-%m-%d %H:%M:%S')}, Open: {latest_candlestick['open']:.5f}, High: {latest_candlestick['high']:.5f}, Low: {latest_candlestick['low']:.5f}, Close: {latest_candlestick['close']:.5f}[/green]")
                    else:
                        self.status_message = "Failed to insert new record"
                        console.print(f"[red]{self.status_message}[/red]")
                else:
                    self.status_message = f"Latest completed candle already in database: {latest_timestamp}"
                    dt = datetime.fromtimestamp(latest_timestamp)
                    console.print(f"[yellow]Latest completed candle already in database: {dt.strftime('%Y-%m-%d %H:%M:%S')}[/yellow]")

            except KeyboardInterrupt:
                self.status_message = "Real-time update interrupted by user. Exiting."
                console.print("\n[yellow]Real-time update interrupted by user. Exiting.[/yellow]")
                break
            except Exception as e:
                self.status_message = f"Error occurred: {e}. Retrying at next minute."
                console.print(f"[red]An error occurred: {e}. Retrying at next minute.[/red]")
                time.sleep(10) # Wait a bit before retrying to avoid spamming on a persistent error

def main():
    """Main function to run the market data collection process."""
    collector = MarketDataCollector()
    
    console.print("[bold cyan]Market Data Collector Starting...[/bold cyan]")
    
    # Initialize connection to MT5
    if not mt5.initialize():
        console.print(f"[red]MT5 initialize() failed, error code = {mt5.last_error()}[/red]")
        mt5.shutdown()
        return

    console.print("[green]✓ MT5 connection established[/green]")

    # Create a database connection
    if not collector.create_connection():
        console.print("[red]Failed to create database connection[/red]")
        return

    console.print("[green]✓ Database connection established[/green]")

    # Create the table if it doesn't exist
    if not collector.create_table():
        console.print("[red]Failed to create database table[/red]")
        return

    console.print("[green]✓ Database table ready[/green]")

    try:
        # Check if the table has any data
        last_db_timestamp = collector.get_last_db_timestamp()
        
        if last_db_timestamp is None:
            console.print("[yellow]Table is empty, performing initial population...[/yellow]")
            success = collector.populate_initial_data(SYMBOL, TIMEFRAME, INITIAL_CANDLES_COUNT)
            if not success:
                console.print("[red]Failed to populate initial data. Exiting.[/red]")
                return
            console.print("[green]✓ Initial data population completed[/green]")
        
        # Start the real-time update loop
        console.print("\n[bold green]Starting real-time data collection. Press Ctrl+C to exit.[/bold green]")
        time.sleep(2)  # Give user time to read the message
        collector.update_data_realtime(SYMBOL, TIMEFRAME)

    finally:
        # Clean up connections
        if collector.conn:
            collector.conn.close()
        mt5.shutdown()
        console.print("[cyan]MT5 connection closed. Goodbye![/cyan]")

if __name__ == "__main__":
    main()
