import MetaTrader5 as mt5
import pandas as pd
import sqlite3
import time
from datetime import datetime, timedelta
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.spinner import Spinner
from rich.layout import Layout
from rich.text import Text
from rich import box
import threading

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
        self.countdown = 60
        self.is_counting = False
        
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
            # Changed time column to TEXT to store the string format
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
                    time TEXT PRIMARY KEY,
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
        """Retrieves the timestamp of the last entry in the database.
        
        This method is updated to handle the string-based time format.
        """
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
                    # Convert the string back to a timestamp for comparisons
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
        
        rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)

        if rates is None or len(rates) == 0:
            self.status_message = "No historical data received from MT5"
            return False

        rates_frame = pd.DataFrame(rates)
        # Convert the integer timestamp to a formatted string before saving
        rates_frame['time'] = pd.to_datetime(rates_frame['time'], unit='s').dt.strftime('%Y-%m-%d %H:%M:%S')

        try:
            rates_frame.to_sql(TABLE_NAME, self.conn, if_exists='replace', index=False)
            self.status_message = f"Successfully populated {len(rates_frame)} records"
            return True
        except sqlite3.Error as e:
            self.status_message = f"Error inserting initial data: {e}"
            return False

    def check_and_fill_gaps(self, symbol, timeframe, last_db_timestamp):
        """Checks for and fills any time gaps in the data since the last database entry."""
        if last_db_timestamp is None:
            return

        from_time = datetime.fromtimestamp(last_db_timestamp)
        now = datetime.now()

        rates = mt5.copy_rates_range(symbol, timeframe, from_time, now)

        if rates is None or len(rates) <= 1:
            return

        rates_frame = pd.DataFrame(rates)
        # Convert to integer timestamp for comparison
        rates_frame['time_int'] = pd.to_datetime(rates_frame['time'], unit='s').astype('int64') // 10**9
        
        new_data = rates_frame[rates_frame['time_int'] > last_db_timestamp]

        if not new_data.empty:
            self.status_message = f"Found and filling a gap of {len(new_data)} missing records"
            try:
                # Convert back to formatted string for insertion
                new_data['time'] = pd.to_datetime(new_data['time_int'], unit='s').dt.strftime('%Y-%m-%d %H:%M:%S')
                new_data.drop(columns=['time_int'], inplace=True)
                new_data.to_sql(TABLE_NAME, self.conn, if_exists='append', index=False)
                self.status_message = "Successfully filled the gap"
            except sqlite3.Error as e:
                self.status_message = f"Error filling gap: {e}"

    def get_latest_candlestick(self, symbol, timeframe):
        """Get the latest candlestick from MT5 and format it properly."""
        rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, 1)
        
        if rates is None or len(rates) == 0:
            return None
            
        latest_rate = rates[0]
        
        # Convert numpy array to proper dictionary format
        candlestick_data = {
            'time': int(latest_rate['time']),
            'open': float(latest_rate['open']),
            'high': float(latest_rate['high']),
            'low': float(latest_rate['low']),
            'close': float(latest_rate['close'])
        }
        
        return candlestick_data

    def get_latest_completed_candlestick(self, symbol, timeframe):
        """Get the latest completed candlestick, which is the one before the current one."""
        rates = mt5.copy_rates_from_pos(symbol, timeframe, 1, 1)
        
        if rates is None or len(rates) == 0:
            return None
            
        latest_rate = rates[0]
        
        candlestick_data = {
            'time': int(latest_rate['time']),
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
            # Convert timestamp to 'yyyy-mm-dd hh:mm:ss' string format
            formatted_time = datetime.fromtimestamp(candlestick_data['time']).strftime('%Y-%m-%d %H:%M:%S')

            cursor.execute(f"""
                INSERT OR REPLACE INTO {TABLE_NAME} (time, open, high, low, close)
                VALUES (?, ?, ?, ?, ?)
            """, (
                formatted_time,
                candlestick_data['open'],
                candlestick_data['high'],
                candlestick_data['low'],
                candlestick_data['close']
            ))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            self.status_message = f"Error inserting candlestick: {e}"
            return False

    def countdown_timer(self):
        """Run countdown timer in a separate thread."""
        self.is_counting = True
        self.countdown = 60
        
        while self.countdown > 0 and self.is_counting:
            time.sleep(1)
            self.countdown -= 1
        
        self.is_counting = False

    def create_display_layout(self):
        """Create the Rich display layout."""
        # Status panel
        status_text = Text(self.status_message, style="bold white")
        status_panel = Panel(status_text, title="Status", border_style="blue")
        
        # Countdown panel
        if self.is_counting:
            spinner = Spinner("dots2", text=f"Next update in {self.countdown:02d} seconds")
            countdown_panel = Panel(spinner, title="Countdown", border_style="yellow")
        else:
            countdown_panel = Panel("Ready", title="Countdown", border_style="green")
        
        # Last record panel
        if self.last_record:
            record_table = Table(show_header=True, header_style="bold magenta", box=box.ROUNDED)
            record_table.add_column("Time", style="cyan")
            record_table.add_column("Open", style="green")
            record_table.add_column("High", style="bright_green")
            record_table.add_column("Low", style="red")
            record_table.add_column("Close", style="yellow")
            
            # Use the string directly from the database
            record_table.add_row(
                self.last_record['time'],
                f"{self.last_record['open']:.5f}",
                f"{self.last_record['high']:.5f}",
                f"{self.last_record['low']:.5f}",
                f"{self.last_record['close']:.5f}"
            )
            
            record_panel = Panel(record_table, title="Latest Candlestick", border_style="cyan")
        else:
            record_panel = Panel("No data available", title="Latest Candlestick", border_style="dim")
        
        # Combine all panels
        layout = Layout()
        layout.split_column(
            Layout(status_panel, size=3),
            Layout(countdown_panel, size=3),
            Layout(record_panel)
        )
        
        return layout

    def update_data_realtime(self, symbol, timeframe):
        """Continuously updates the database with new M1 candlesticks every minute."""
        with Live(self.create_display_layout(), refresh_per_second=4, screen=True) as live:
            while True:
                try:
                    # Get the timestamp of the last entry in the database
                    last_db_timestamp = self.get_last_db_timestamp()

                    # Check for and fill any gaps before appending new data
                    self.check_and_fill_gaps(symbol, timeframe, last_db_timestamp)

                    # Calculate wait time to next exact minute boundary
                    now = datetime.now()
                    
                    # Calculate seconds remaining in the current minute
                    seconds_in_current_minute = now.second + (now.microsecond / 1000000.0)
                    
                    # Calculate seconds to wait until the next minute starts (00 seconds)
                    wait_seconds = 60 - seconds_in_current_minute
                    
                    if wait_seconds > 0:
                        next_minute = now.replace(second=0, microsecond=0) + timedelta(minutes=1)
                        self.status_message = f"Waiting for next minute boundary: {next_minute.strftime('%H:%M:%S')}"
                        
                        # Start countdown timer in separate thread
                        self.countdown = int(wait_seconds) + 1  # Add 1 to account for partial seconds
                        timer_thread = threading.Thread(target=self.countdown_timer)
                        timer_thread.start()
                        
                        # Update display while waiting
                        while self.is_counting and wait_seconds > 0:
                            live.update(self.create_display_layout())
                            time.sleep(0.25)
                            now = datetime.now()
                            seconds_in_current_minute = now.second + (now.microsecond / 1000000.0)
                            wait_seconds = 60 - seconds_in_current_minute
                        
                        # Stop the timer thread
                        self.is_counting = False
                        if timer_thread.is_alive():
                            timer_thread.join()

                    # Add a small delay to ensure the minute has fully passed and candle is completed
                    time.sleep(3)

                    # Get the latest COMPLETED candlestick (not the currently forming one)
                    self.status_message = "Fetching latest completed candlestick..."
                    live.update(self.create_display_layout())
                    
                    latest_candlestick = self.get_latest_completed_candlestick(symbol, timeframe)

                    if latest_candlestick is None:
                        self.status_message = "No data received from MT5. Retrying at next minute."
                        live.update(self.create_display_layout())
                        continue

                    latest_timestamp = latest_candlestick['time']

                    # Check if this candlestick is new before inserting
                    if last_db_timestamp is None or latest_timestamp > last_db_timestamp:
                        if self.insert_candlestick(latest_candlestick):
                            self.last_record = latest_candlestick
                            self.last_record['time'] = datetime.fromtimestamp(latest_timestamp).strftime('%Y-%m-%d %H:%M:%S')
                            self.status_message = f"Added new record: {self.last_record['time']}"
                            console.print(f"[green]✓ New completed candle added: {self.last_record['time']}[/green]")
                        else:
                            self.status_message = "Failed to insert new record"
                    else:
                        formatted_time = datetime.fromtimestamp(latest_timestamp).strftime('%Y-%m-%d %H:%M:%S')
                        self.status_message = f"Latest completed candle already in database: {formatted_time}"

                    live.update(self.create_display_layout())

                except KeyboardInterrupt:
                    self.status_message = "Real-time update interrupted by user. Exiting."
                    live.update(self.create_display_layout())
                    console.print("\n[yellow]Real-time update interrupted by user. Exiting.[/yellow]")
                    break
                except Exception as e:
                    self.status_message = f"Error occurred: {e}. Retrying at next minute."
                    live.update(self.create_display_layout())
                    console.print(f"[red]An error occurred: {e}. Retrying at next minute.[/red]")

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
