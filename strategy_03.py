#-----------------------------------------
# filename: strategy_03.py
# Previously known as strategy_21.py
# risk management, and trailing stops
# c/o Claude
#-----------------------------------------


# STATUS as of 2025-09-10 08:00 PM
production_status = "DEMO" # DEMO or LIVE



import MetaTrader5 as mt5
import pandas as pd
import time
from datetime import timedelta, datetime, timezone
import logging
import traceback
import os
from dotenv import load_dotenv
import talib  # Import TA-Lib
import numpy as np  # Import numpy for array operations
import sys
import threading
from functools import wraps
from collections import deque
import statistics
from modules.trading_hours_08pm_to_12nn import is_trading_hours # ⚠️ TESTING



# Rich imports for beautiful logging
from rich.console import Console
from rich.logging import RichHandler
from rich.text import Text
from rich.panel import Panel
from rich.table import Table
from rich.progress import track
from rich import box
import rich.traceback

# Install rich traceback for better error display
rich.traceback.install(show_locals=True)

# Initialize Rich console
console = Console()

# Load environment variables from .env file
load_dotenv()

# --- Process Lock to prevent multiple instances ---
def singleton_process():
    """Prevents multiple instances of the same bot from running simultaneously"""
    lock_file = f".{MAGIC_NUMBER_FOR_LOG}.lock"
    if os.path.exists(lock_file):
        try:
            # Check if the process is actually running
            with open(lock_file, 'r') as f:
                pid = int(f.read().strip())
            # On Unix-like systems, we can check if process exists
            if sys.platform != 'win32':
                os.kill(pid, 0)
            else:
                # Windows doesn't have a direct equivalent, so we assume lock is valid
                pass
            console.print(f"[bold red]⚠️  Another instance of this bot (MAGIC_NUMBER: {MAGIC_NUMBER_FOR_LOG}) is already running with PID {pid}. Exiting.[/bold red]")
            sys.exit(1)
        except (OSError, ValueError, ProcessLookupError):
            # Lock file exists but process is dead, remove it
            os.remove(lock_file)
    
    # Create new lock file
    with open(lock_file, 'w') as f:
        f.write(str(os.getpid()))
    
    # Clean up lock file on exit
    def cleanup():
        if os.path.exists(lock_file):
            os.remove(lock_file)
    
    import atexit
    atexit.register(cleanup)

# --- Enhanced Logging Configuration with Rich ---
strategy_id = 3  # Unique identifier for this strategy
MAGIC_NUMBER_FOR_LOG = int(strategy_id)  # Get magic number early for log file name
filename = os.path.basename(__file__)
trade_type = 'trend following'

# Set up singleton process lock before initializing logging
singleton_process()

# Configure logging with Rich handler
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[
        RichHandler(console=console, rich_tracebacks=True, markup=True),
        logging.FileHandler(f"{MAGIC_NUMBER_FOR_LOG}.log", encoding='utf-8')
    ]
)

# Custom logging functions for better visual appeal
def log_success(message):
    console.print(f"[bold green]✅ {message}[/bold green]")

def log_error(message):
    console.print(f"[bold red]❌ {message}[/bold red]")

def log_warning(message):
    console.print(f"[bold yellow]⚠️  {message}[/bold yellow]")

def log_info(message):
    console.print(f"[bold blue]ℹ️  {message}[/bold blue]")

def log_trade(action, symbol, price, sl, tp, magic):
    """Beautiful trade logging"""
    panel = Panel(
        f"[bold cyan]{action}[/bold cyan] {symbol}\n"
        f"💰 Price: [yellow]{price:.2f}[/yellow]\n"
        f"🛑 Stop Loss: [red]{sl:.2f}[/red]\n"
        f"🎯 Take Profit: [green]{tp:.2f}[/green]\n"
        f"🔮 Magic: [magenta]{magic}[/magenta]",
        title="[bold]🚀 TRADE EXECUTED",
        border_style="bright_green",
        box=box.DOUBLE
    )
    console.print(panel)

# --- Performance Monitoring ---
class PerformanceMonitor:
    """Tracks and reports key performance metrics with Rich display"""
    def __init__(self):
        self.trade_count = 0
        self.successful_trades = 0
        self.failed_trades = 0
        self.start_time = datetime.now()
        self.response_times = deque(maxlen=100)  # Keep last 100 response times
        
    def record_trade(self, success):
        self.trade_count += 1
        if success:
            self.successful_trades += 1
        else:
            self.failed_trades += 1
            
    def record_response_time(self, time_ms):
        self.response_times.append(time_ms)
        
    def get_stats(self):
        uptime = datetime.now() - self.start_time
        success_rate = (self.successful_trades / self.trade_count * 100) if self.trade_count > 0 else 0
        avg_response = statistics.mean(self.response_times) if self.response_times else 0
        
        return {
            "uptime": str(uptime).split('.')[0],  # Remove microseconds
            "total_trades": self.trade_count,
            "success_rate": f"{success_rate:.2f}%",
            "avg_response_ms": f"{avg_response:.2f}"
        }
    
    def display_stats(self):
        """Display performance stats in a beautiful table"""
        stats = self.get_stats()
        
        table = Table(title="📊 Performance Metrics", box=box.ROUNDED)
        table.add_column("Metric", style="cyan", no_wrap=True)
        table.add_column("Value", style="magenta")
        
        table.add_row("⏱️ Uptime", stats["uptime"])
        table.add_row("📈 Total Trades", str(stats["total_trades"]))
        table.add_row("✅ Success Rate", stats["success_rate"])
        table.add_row("⚡ Avg Response", f"{stats['avg_response_ms']}ms")
        
        console.print(table)

# Initialize performance monitor
perf_monitor = PerformanceMonitor()

# --- MT5 Configuration ---
symbol = "GOLDm#" if production_status == 'LIVE' else 'GOLD#'
timeframe_m2 = mt5.TIMEFRAME_M2  # 2-minute timeframe for entry signal
timeframe_m15 = mt5.TIMEFRAME_M15  # 15-minute timeframe for trend confluence
volume = 0.1 if production_status == 'LIVE' else 0.01 # Trading lot size
deviation = 20  # Max price deviation in points for order execution

# --- Enhanced Risk Management Configuration ---
RISK_PERCENT = float(os.getenv("RISK_PERCENT", "1.0"))  # Risk 1% of account per trade by default
REWARD_RATIO = float(os.getenv("REWARD_RATIO", "2.0"))  # 2:1 reward/risk ratio
MAX_RISK_PER_TRADE = float(os.getenv("MAX_RISK_PER_TRADE", "100.0"))  # Max $ risk per trade
MIN_ACCOUNT_BALANCE = float(os.getenv("MIN_ACCOUNT_BALANCE", "10.0"))  # Minimum balance to trade

# --- Enhanced SL/TP Configuration ---
SL_POINTS = 300  # Fixed Stop Loss at 300 points
TP_POINTS = 450  # ENHANCED: Take Profit at 1200 points (was 300)
EMA_DISTANCE_THRESHOLD = 130

# --- NEW: Trailing Stop Configuration ---
TRAILING_EMA_PERIOD = 7  # 7 EMA for trailing stop
TRAILING_STOP_DISTANCE = 70  # 70 points distance from 7 EMA
TRAILING_ACTIVATION_POINTS = 300  # Activate trailing stop after 300 points profit
TRAILING_STOP_CHECK_INTERVAL = 10 # Check trailing stop every 10 seconds

MAX_OPEN_TRADES_PER_MAGIC = 1  # Limit to 1 open trade per specific magic number

# --- Magic Number Configuration ---
MAGIC_NUMBER = MAGIC_NUMBER_FOR_LOG  # Use the same magic number for bot logic
log_info(f"Bot instance starting with MAGIC_NUMBER: {MAGIC_NUMBER}")

# --- Strategic Indicator Selection ---
EMA_PERIOD = 20  # Medium-term trend (more reliable than ema for BTC)
EMA_200_PERIOD = 200 # Long-term trend for M2 timeframe
EMA_200_DISTANCE_THRESHOLD = 300 # Price absolute distance from 200 EMA in points

# --- Market Session Configuration ---
TRADING_HOURS_START = int(os.getenv("TRADING_HOURS_START", "20"))  # 8 AM UTC
TRADING_HOURS_END = int(os.getenv("TRADING_HOURS_END", "12"))  # 10 PM UTC

# --- Global variable for MT5 connection status ---
mt5_connected = False
connection_attempts = 0
max_connection_attempts = 5
stop_event = threading.Event()


# --- Enhanced Functions ---
def retry_on_failure(max_retries=3, delay=2):
    """Decorator to retry functions on failure with exponential backoff"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    retries += 1
                    if retries == max_retries:
                        log_error(f"Max retries ({max_retries}) exceeded for {func.__name__}: {str(e)}")
                        raise
                    wait_time = delay * (2 ** (retries - 1))  # Exponential backoff
                    log_warning(f"Attempt {retries}/{max_retries} failed for {func.__name__}: {str(e)}. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
            return None
        return wrapper
    return decorator

def connect_to_mt5():
    """Initializes connection to MetaTrader 5 terminal with retry logic"""
    global mt5_connected, connection_attempts
    
    # Reset connection attempts if we've been disconnected for a while
    if not mt5_connected and connection_attempts > 0:
        time.sleep(2 ** min(connection_attempts, 5))  # Exponential backoff
    
    try:
        log_info("Attempting to initialize MetaTrader 5...")
        if not mt5.initialize():
            connection_attempts += 1
            error_code = mt5.last_error()
            log_error(f"MT5 initialize() failed (attempt {connection_attempts}/{max_connection_attempts}), error code = {error_code}")
            
            if connection_attempts >= max_connection_attempts:
                log_error(f"Max connection attempts ({max_connection_attempts}) reached. Exiting.")
                stop_event.set()
                sys.exit(1)
                
            return False
            
        # Optional: Connect to a specific account if details are provided
        mt5_login = int(os.getenv("MT5_LOGIN", "0"))
        mt5_password = os.getenv("MT5_PASSWORD", "")
        mt5_server = os.getenv("MT5_SERVER", "")
        
        if mt5_login != 0 and mt5_password and mt5_server:
            authorized = mt5.login(mt5_login, password=mt5_password, server=mt5_server)
            if not authorized:
                connection_attempts += 1
                error_code = mt5.last_error()
                log_error(f"Failed to connect to account {mt5_login} (attempt {connection_attempts}/{max_connection_attempts}), error code: {error_code}")
                
                if connection_attempts >= max_connection_attempts:
                    log_error(f"Max connection attempts ({max_connection_attempts}) reached. Exiting.")
                    stop_event.set()
                    sys.exit(1)
                    
                return False
            else:
                log_success(f"Connected to MT5 account {mt5_login}")
                connection_attempts = 0  # Reset on success
        else:
            log_warning("MT5 account details not provided. Connecting without explicit login.")
            
        version = mt5.version()
        log_success(f"MetaTrader5 connected: Version {version}")
        mt5_connected = True
        return True
    except Exception as e:
        connection_attempts += 1
        log_error(f"Exception during MT5 initialization (attempt {connection_attempts}/{max_connection_attempts}): {e}")
        
        if connection_attempts >= max_connection_attempts:
            log_error(f"Max connection attempts ({max_connection_attempts}) reached. Exiting.")
            stop_event.set()
            sys.exit(1)
            
        return False

def get_account_info():
    """Retrieves current account balance and equity"""
    if not mt5_connected:
        log_error("MT5 is not connected. Cannot retrieve account info.")
        return None
    
    try:
        account_info = mt5.account_info()
        if account_info is None:
            log_error(f"Failed to get account info, error code = {mt5.last_error()}")
            return None
            
        # Beautiful account info display
        table = Table(title="💰 Account Information", box=box.ROUNDED)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Balance", f"${account_info.balance:.2f}")
        table.add_row("Equity", f"${account_info.equity:.2f}")
        table.add_row("Margin", f"${account_info.margin:.2f}")
        table.add_row("Free Margin", f"${account_info.margin_free:.2f}")
        
        console.print(table)
        return account_info
    except Exception as e:
        log_error(f"Error getting account info: {e}")
        return None

def calculate_fixed_risk():
    """Sets fixed SL/TP values as per requirements."""
    global SL_POINTS, TP_POINTS
    
    log_info(f"Using enhanced risk: SL={SL_POINTS} points, TP={TP_POINTS} points.")
    return True

def get_ohlc_data(symbol, timeframe, count=20000):
    """
    Retrieves the latest OHLC data from MT5 for a specified timeframe.
    Increased count for indicators.
    Adds retry logic for robustness.
    """
    if not mt5_connected:
        log_error("MT5 is not connected. Cannot retrieve data.")
        return None
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
            if rates is None:
                error_code = mt5.last_error()
                log_warning(f"Error getting rates for {symbol} on {timeframe} (attempt {attempt+1}/{max_retries}), error code = {error_code}")
                
                # If it's the last attempt, return None
                if attempt == max_retries - 1:
                    return None
                
                # Wait before retrying (exponential backoff)
                time.sleep(1 * (2 ** attempt))
                continue
                
            # Convert to a pandas DataFrame for easier analysis
            rates_frame = pd.DataFrame(rates)
            rates_frame['time'] = pd.to_datetime(rates_frame['time'], unit='s')
            rates_frame.set_index('time', inplace=True)
            
            # Sort by time to ensure chronological order
            rates_frame = rates_frame.sort_index()
            
            return rates_frame
        except Exception as e:
            log_error(f"Exception during data retrieval (attempt {attempt+1}/{max_retries}): {e}")
            if attempt == max_retries - 1:
                return None
            time.sleep(1 * (2 ** attempt))
    
    return None

def calculate_technical_indicators(data, ema_period=EMA_PERIOD):
    """Calculates EMA for trend direction. Enhanced to support multiple EMA periods."""
    if data.empty or len(data) < ema_period:
        log_warning(f"Not enough data ({len(data)} bars) to calculate EMA. Need at least {ema_period} bars.")
        return None
    
    close_prices = data['close'].values
    
    ema = talib.SMA(close_prices, timeperiod=ema_period)
    
    latest_ema = ema[~np.isnan(ema)][-1] if ema[~np.isnan(ema)].size > 0 else None
    
    if latest_ema is None:
        log_warning("EMA is None (likely not enough valid data points after initial NaNs).")
        return None
    
    trend_direction = "sideways"
    if close_prices[-1] > latest_ema:
        trend_direction = "bullish"
    elif close_prices[-1] < latest_ema:
        trend_direction = "bearish"
    
    indicators_data = {
        "ema": latest_ema,
        "trend_direction": trend_direction,
        "current_price": close_prices[-1]
    }
    
    log_info(f"Calculated Indicators (EMA{ema_period}): Trend: [bold]{trend_direction}[/bold], EMA={latest_ema:.2f}")
    
    return indicators_data

def calculate_ema_distance(data_m2, indicators_m2, symbol_info):
    """
    Calculates the distance of the current price relative to the 20 ema for M2 timeframe.
    Returns the distance in points.
    """
    if data_m2 is None or data_m2.empty or indicators_m2 is None or 'ema' not in indicators_m2:
        log_warning("Insufficient data or ema not available for ema distance calculation.")
        return None

    current_price = data_m2['close'].iloc[-1]
    latest_ema = indicators_m2['ema']
    point = symbol_info.point

    distance = current_price - latest_ema
    distance_points = round(abs(distance) / point)
    
    log_info(f"Current Price: {current_price:.2f}, EMA: {latest_ema:.2f}. ✅ Distance: [yellow]{distance_points}[/yellow] points")
        
    return distance_points

def determine_trade_signal(indicators_m2, indicators_m15):
    """
    Determines the trade signal based on deterministic rules (price and EMA trend and distance).
    """
    signal = "hold"
    reason = "No clear signal or conflicting trends."
    
    if indicators_m2 is None or indicators_m15 is None:
        reason = "Insufficient indicator data for one or both timeframes."
        log_warning(reason)
        return signal, reason

    m2_trend = indicators_m2.get('trend_direction')
    m15_trend = indicators_m15.get('trend_direction')
    
    # Rule 1: M2 must agree with M15 direction for trend to be valid
    if m2_trend == "bullish" and m15_trend == "bullish":
        signal = "buy"
        reason = "M2 and M15 trends are both bullish (Price above 20 EMA)."
    elif m2_trend == "bearish" and m15_trend == "bearish":
        signal = "sell"
        reason = "M2 and M15 trends are both bearish (Price below 20 EMA)."
    else:
        signal = "hold"
        reason = f"Conflicting trends: M2 is {m2_trend}, M15 is {m15_trend}. Holding."

    # Beautiful signal display
    if signal != "hold":
        panel = Panel(
            f"[bold cyan]{signal.upper()}[/bold cyan]\n{reason}",
            title="🎯 TRADE SIGNAL",
            border_style="bright_blue" if signal == "buy" else "bright_red",
            box=box.DOUBLE
        )
        console.print(panel)
    else:
        log_info(f"Signal: [yellow]{signal.upper()}[/yellow], Reason: {reason}")

    return signal, reason

def get_open_positions_count_by_magic(symbol_filter=None, magic_number=None):
    """
    Returns the number of open positions, filtered by symbol AND magic number.
    This is crucial for managing trades for specific bot instances.
    Adds error handling for MT5 connection issues.
    """
    if not mt5_connected:
        log_warning("MT5 is not connected. Cannot get open positions count.")
        return 0
    
    try:
        positions = mt5.positions_get()
        if positions is None:
            error_code = mt5.last_error()
            log_error(f"Failed to get positions, error code = {error_code}")
            return 0
        
        count = 0
        for pos in positions:
            # Filter by symbol if provided AND by magic_number if provided
            if (symbol_filter is None or pos.symbol == symbol_filter) and \
               (magic_number is None or pos.magic == magic_number):
                count += 1
        return count
    except Exception as e:
        log_error(f"Error getting open positions: {e}")
        return 0

def check_candle_range(symbol, timeframe, max_range_points):
    """
    Checks if the current open candle's range (High - Low) is within the specified limit.
    """

    if timeframe == mt5.TIMEFRAME_H1:
        timeframe_str = "H1"
    if timeframe == mt5.TIMEFRAME_H4:
        timeframe_str = "H4"    

    if not mt5_connected:
        log_error("MT5 is not connected for candle range check.")
        return False

    try:
        # Get the last candle (current open candle)
        rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, 1)
        if rates is None or len(rates) == 0:
            error_code = mt5.last_error()
            log_error(f"Error getting rates for {symbol} {timeframe_str}, error code = {error_code}")
            return False

        current_candle = rates[0]
        high = current_candle['high']
        low = current_candle['low']

        symbol_info = mt5.symbol_info(symbol)
        if not symbol_info:
            log_error(f"Failed to get symbol info for {symbol}")
            return False
        point = symbol_info.point

        candle_range_points = round(abs(high - low) / point)

        if candle_range_points <= max_range_points:
            log_info(f"Candle range for {symbol} {timeframe_str} is {candle_range_points} points (<= {max_range_points}). Tradeable.")
            return True
        else:
            log_info(f"Candle range for {symbol} {timeframe_str} is {candle_range_points} points (> {max_range_points}). Not tradeable.")
            return False

    except Exception as e:
        log_error(f"Exception during candle range check for {symbol} {timeframe_str}: {e}")
        return False

def check_1h_open_candle_range():
    """
    Checks if the current open H1 candle's range is <= 1100 points.
    """
    return check_candle_range(symbol, mt5.TIMEFRAME_H1, 1100)

def check_4h_open_candle_range():
    """
    Checks if the current open H4 candle's range is <= 1800 points.
    """
    return check_candle_range(symbol, mt5.TIMEFRAME_H4, 1800)


def manage_trailing_stop():
    """
    NEW FUNCTION: Manages trailing stop loss based on 7 EMA
    Only activates after the trade has moved 300 points in profit
    """
    if not mt5_connected:
        # Avoid logging this warning repeatedly from the separate thread
        # log_warning("MT5 not connected. Cannot manage trailing stops.")
        return
    
    try:
        positions = mt5.positions_get(symbol=symbol)
        if not positions:
            return
        
        # Get current market data for 7 EMA calculation
        data_m2 = get_ohlc_data(symbol, timeframe_m2)  # Need fewer bars for 7 EMA
        if data_m2 is None or len(data_m2) < TRAILING_EMA_PERIOD:
            log_warning("Insufficient data for trailing stop calculation.")
            return
        
        # Calculate 7 EMA for trailing stop
        trailing_indicators = calculate_technical_indicators(data_m2, ema_period=TRAILING_EMA_PERIOD)
        if not trailing_indicators:
            return
        
        trailing_ema = trailing_indicators['ema']
        symbol_info = mt5.symbol_info(symbol)
        if not symbol_info:
            return
        
        point = symbol_info.point
        tick_info = mt5.symbol_info_tick(symbol)
        if not tick_info:
            return
        
        for position in positions:
            if position.magic != MAGIC_NUMBER:
                continue
            
            entry_price = position.price_open
            position_type = position.type
            current_profit_points = 0
            
            # Use bid price for buy positions, ask for sell positions
            current_price = tick_info.bid if position_type == mt5.POSITION_TYPE_BUY else tick_info.ask
            
            # Calculate current profit in points
            if position_type == mt5.POSITION_TYPE_BUY:
                current_profit_points = (current_price - entry_price) / point
            elif position_type == mt5.POSITION_TYPE_SELL:
                current_profit_points = (entry_price - current_price) / point
            
            # Check if trailing stop should be activated
            if current_profit_points >= TRAILING_ACTIVATION_POINTS:
                # Calculate new trailing stop level
                new_sl = 0.0
                
                if position_type == mt5.POSITION_TYPE_BUY:
                    # For buy positions, trailing stop is below 7 EMA
                    new_sl = trailing_ema - (TRAILING_STOP_DISTANCE * point)
                    # Only move SL up, never down
                    if position.sl == 0 or new_sl > position.sl:
                        should_update = True
                    else:
                        should_update = False
                elif position_type == mt5.POSITION_TYPE_SELL:
                    # For sell positions, trailing stop is above 7 EMA
                    new_sl = trailing_ema + (TRAILING_STOP_DISTANCE * point)
                    # Only move SL down, never up
                    if position.sl == 0 or new_sl < position.sl:
                        should_update = True
                    else:
                        should_update = False
                
                if should_update:
                    # Round to appropriate digits
                    new_sl = round(new_sl, symbol_info.digits)
                    
                    # Update the stop loss
                    request = {
                        "action": mt5.TRADE_ACTION_SLTP,
                        "symbol": symbol,
                        "position": position.ticket,
                        "sl": new_sl,
                        "tp": position.tp,
                    }
                    
                    result = mt5.order_send(request)
                    if result.retcode == mt5.TRADE_RETCODE_DONE:
                        # Beautiful trailing stop notification
                        panel = Panel(
                            f"[bold cyan]Position:[/bold cyan] {position.ticket}\n"
                            f"[bold green]7 EMA:[/bold green] {trailing_ema:.2f}\n"
                            f"[bold yellow]New SL:[/bold yellow] {new_sl:.2f}\n"
                            f"[bold magenta]Profit:[/bold magenta] {current_profit_points:.0f} points",
                            title="🔄 TRAILING STOP UPDATED",
                            border_style="bright_cyan",
                            box=box.DOUBLE
                        )
                        console.print(panel)
                    else:
                        log_error(f"Failed to update trailing stop: {result.comment}")
                        
    except Exception as e:
        log_error(f"Error in trailing stop management: {e}")

# NEW: Trailing stop management function to be run in a separate thread
def start_trailing_stop_manager():
    """Manages the trailing stop in a separate thread, checking at regular intervals."""
    log_info(f"Starting trailing stop manager thread. Checking every {TRAILING_STOP_CHECK_INTERVAL} seconds...")
    while not stop_event.is_set():
        manage_trailing_stop()
        stop_event.wait(TRAILING_STOP_CHECK_INTERVAL)
    log_info("Trailing stop manager thread stopped.")

def execute_trade(symbol, trade_type):
    """Executes a market order in MT5 with calculated SL/TP and the bot's MAGIC_NUMBER."""
    global SL_POINTS, TP_POINTS
    
    # Use fixed risk parameters
    if not calculate_fixed_risk():
        log_error("Failed to set fixed risk parameters. Cannot execute trade.")
        return False
    
    if not mt5_connected:
        log_error("MT5 is not connected. Cannot execute trade.")
        return False
    
    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None:
        log_error(f"Failed to get symbol info for {symbol}, error code = {mt5.last_error()}")
        return False
    
    # Ensure the symbol is selected in Market Watch
    if not mt5.symbol_select(symbol, True):
        log_error(f"Failed to select {symbol} in Market Watch.")
        return False
    
    tick_info = mt5.symbol_info_tick(symbol)
    if tick_info is None:
        log_error(f"Failed to get tick info for {symbol}, error code = {mt5.last_error()}")
        return False
    
    current_price = tick_info.ask if trade_type == mt5.ORDER_TYPE_BUY else tick_info.bid
    point = symbol_info.point  # Value of a point for the symbol
    
    # Calculate SL/TP in price terms
    sl_price = 0.0
    tp_price = 0.0
    
    if trade_type == mt5.ORDER_TYPE_BUY:
        sl_price = current_price - (SL_POINTS * point)
        tp_price = current_price + (TP_POINTS * point)
        # Basic validation: ensure SL is below entry and TP is above entry
        if sl_price >= current_price:
            log_warning(f"Calculated SL price ({sl_price}) is not below entry price ({current_price}). Setting SL to 0.0 (disabled).")
            sl_price = 0.0
        if tp_price <= current_price:
            log_warning(f"Calculated TP price ({tp_price}) is not above entry price ({current_price}). Setting TP to 0.0 (disabled).")
            tp_price = 0.0
    elif trade_type == mt5.ORDER_TYPE_SELL:
        sl_price = current_price + (SL_POINTS * point)
        tp_price = current_price - (TP_POINTS * point)
        # Basic validation: ensure SL is above entry and TP is below entry
        if sl_price <= current_price:
            log_warning(f"Calculated SL price ({sl_price}) is not above entry price ({current_price}). Setting SL to 0.0 (disabled).")
            sl_price = 0.0
        if tp_price >= current_price:
            log_warning(f"Calculated TP price ({tp_price}) is not below entry price ({current_price}). Setting TP to 0.0 (disabled).")
            tp_price = 0.0
    
    # Round SL/TP to appropriate digits for the symbol
    digits = symbol_info.digits
    if sl_price != 0.0:
        sl_price = round(sl_price, digits)
    if tp_price != 0.0:
        tp_price = round(tp_price, digits)
    
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": volume,
        "type": trade_type,
        "price": current_price,
        "deviation": deviation,
        "magic": MAGIC_NUMBER,  # *** Set the MAGIC_NUMBER here! ***
        "comment": f"{production_status}_{filename}_{MAGIC_NUMBER}",  # Add magic number to comment for easier identification
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
        "sl": sl_price,  # Set Stop Loss
        "tp": tp_price,  # Set Take Profit
    }
    
    log_info(f"Attempting to place {trade_type} order for {symbol} (Magic: {MAGIC_NUMBER})")
    
    result = mt5.order_send(request)
    
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        error_messages = {
            10004: "Invalid request",
            10006: "Trade server busy",
            10009: "Market closed",
            10013: "Trade context busy",
            10016: "Timeout",
            10027: "Invalid volume",
            10036: "Invalid price",
            10038: "Invalid stops",
            10041: "Market now closed"
        }
        
        error_msg = error_messages.get(result.retcode, f"Unknown error (code: {result.retcode})")
        log_error(f"Order send failed: {error_msg}, comment = {result.comment}")
        
        if result.request:
            log_error(f"Order request details: {result.request}")
        
        perf_monitor.record_trade(False)
        return False
    else:
        # Beautiful trade execution log
        trade_action = "BUY" if trade_type == mt5.ORDER_TYPE_BUY else "SELL"
        log_trade(trade_action, symbol, current_price, sl_price, tp_price, MAGIC_NUMBER)
        
        perf_monitor.record_trade(True)
        return True

def check_system_health():
    """Checks overall system health before trading"""
    # Check MT5 connection
    if not mt5_connected:
        log_warning("MT5 is not connected. Attempting to reconnect...")
        if not connect_to_mt5():
            return False
    
    # Check account balance
    account_info = get_account_info()
    if not account_info or account_info.balance < MIN_ACCOUNT_BALANCE:
        log_error(f"Account balance ${account_info.balance:.2f} is below minimum required ${MIN_ACCOUNT_BALANCE:.2f}. Stopping trading.")
        return False
    
    # Check for maximum open trades
    open_positions_count = get_open_positions_count_by_magic(symbol_filter=symbol, magic_number=MAGIC_NUMBER)
    if open_positions_count >= MAX_OPEN_TRADES_PER_MAGIC:
        log_info(f"Maximum open trades ({MAX_OPEN_TRADES_PER_MAGIC}) reached for {symbol} with Magic Number {MAGIC_NUMBER}. Skipping new trade placement.")
        return False
    
    # Calculate 20 EMA distance for M2 timeframe
    data_m2 = get_ohlc_data(symbol, timeframe_m2)
    indicators_m2_20ema = calculate_technical_indicators(data_m2, ema_period=EMA_PERIOD)
    symbol_info = mt5.symbol_info(symbol)
    
    if data_m2 is None or indicators_m2_20ema is None or symbol_info is None:
        log_warning("Could not retrieve data, 20 EMA indicators, or symbol info for 20 EMA distance check. Skipping.")
        return False

    ema_20_distance_m2 = calculate_ema_distance(data_m2, indicators_m2_20ema, symbol_info)
                        
    # Check if Price relative to 20 EMA is > EMA_DISTANCE_THRESHOLD. If it is, skip the trade.
    if ema_20_distance_m2 is not None and ema_20_distance_m2 > EMA_DISTANCE_THRESHOLD:
        log_warning(f"Setup not tradable for M2 timeframe. Price is {ema_20_distance_m2} points away from 20 EMA (overbought/oversold). Skipping trade.")
        return False
    
    log_success(f"20 EMA distance for M2 timeframe: {ema_20_distance_m2} points. Within tradable range.")

    # NEW: Calculate 200 EMA distance for M2 timeframe
    indicators_m2_200ema = calculate_technical_indicators(data_m2, ema_period=EMA_200_PERIOD)
    if indicators_m2_200ema is None:
        log_warning("Could not calculate 200 EMA indicators for M2 timeframe. Skipping.")
        return False
    
    ema_200_distance_m2 = calculate_ema_distance(data_m2, indicators_m2_200ema, symbol_info)

    # NEW: Add condition for 200 EMA distance
    if ema_200_distance_m2 is not None and ema_200_distance_m2 < EMA_200_DISTANCE_THRESHOLD:
        log_warning(f"Setup not tradable for M2 timeframe. Price is only {ema_200_distance_m2} points away from 200 EMA (less than {EMA_200_DISTANCE_THRESHOLD} points). Skipping trade.")
        return False
    
    log_success(f"200 EMA distance for M2 timeframe: {ema_200_distance_m2} points. Greater than {EMA_200_DISTANCE_THRESHOLD} points.")

    # Check market hours
    if not is_trading_hours():
        log_info(f"Outside configured trading hours ({TRADING_HOURS_START}:00-{TRADING_HOURS_END}:00 UTC). Skipping analysis.")
        return False
    
    return True

# --- Main Trading Loop ---
def main_loop():
    """Enhanced main trading loop with comprehensive error handling, system checks, and trailing stop management"""
    global mt5_connected
    
    # Beautiful startup banner
    startup_panel = Panel(
        f"[bold cyan]🚀 MT5 TRADING BOT ENHANCED[/bold cyan]\n\n"
        f"[yellow]Symbol:[/yellow] {symbol}\n"
        f"[yellow]Magic Number:[/yellow] {MAGIC_NUMBER}\n"
        f"[yellow]Risk:[/yellow] {RISK_PERCENT}% per trade\n"
        f"[yellow]Stop Loss:[/yellow] {SL_POINTS} points\n"
        f"[yellow]Take Profit:[/yellow] {TP_POINTS} points\n"
        f"[yellow]Trailing Stop:[/yellow] {TRAILING_STOP_DISTANCE} pts from 7 EMA\n"
        f"[yellow]Trailing Activation:[/yellow] {TRAILING_ACTIVATION_POINTS} points profit\n"
        f"[yellow]Trading Hours:[/yellow] {TRADING_HOURS_START}:00-{TRADING_HOURS_END}:00 UTC",
        title="🎯 CONFIGURATION",
        border_style="bright_green",
        box=box.DOUBLE
    )
    console.print(startup_panel)
    
    # Initialize MT5 connection
    if not connect_to_mt5():
        log_error("Failed to connect to MT5 after multiple attempts. Exiting.")
        return
    
    # Set fixed risk parameters initially
    calculate_fixed_risk()

    # START THE SEPARATE THREAD FOR TRAILING STOP MANAGEMENT
    trailing_stop_thread = threading.Thread(target=start_trailing_stop_manager)
    trailing_stop_thread.daemon = True # Daemonize thread
    trailing_stop_thread.start()

    
    log_success("Starting enhanced main trading loop with trailing stop management...")
    
    cycle_count = 0
    
    while not stop_event.is_set():
        try:
            cycle_count += 1
            
            # Beautiful cycle header
            console.print(f"\n[bold magenta]{'='*50}[/bold magenta]")
            console.print(f"[bold cyan]📊 ANALYSIS CYCLE #{cycle_count}[/bold cyan]")
            console.print(f"[bold magenta]{'='*50}[/bold magenta]")
            
            # Check overall system health
            if not check_system_health():
                # Wait a minute before next check if health check failed
                log_info("Waiting 60 seconds before next health check...")
                time.sleep(60)
                continue
            
            # Check H1 and H4 candle ranges
            if not check_1h_open_candle_range():
                log_info("H1 candle range not tradeable. Holding.")
                time.sleep(60)
                continue
            
            if not check_4h_open_candle_range():
                log_info("H4 candle range not tradeable. Holding.")
                time.sleep(60)
                continue

            # Get data for multiple timeframes
            log_info("📈 Fetching market data...")
            data_m2 = get_ohlc_data(symbol, timeframe_m2)
            data_m15 = get_ohlc_data(symbol, timeframe_m15)
            data_h1 = get_ohlc_data(symbol, mt5.TIMEFRAME_H1)
            
            if all(data is not None and not data.empty for data in [data_m2, data_m15]):
                # Calculate technical indicators for all timeframes
                log_info("🧮 Calculating technical indicators...")
                indicators_m2 = calculate_technical_indicators(data_m2)
                indicators_m15 = calculate_technical_indicators(data_m15)
                
                if all([indicators_m2, indicators_m15]):
                    signal, reason = determine_trade_signal(indicators_m2, indicators_m15)
                    
                    if signal == "buy":
                        execute_trade(symbol, mt5.ORDER_TYPE_BUY)
                    elif signal == "sell":
                        execute_trade(symbol, mt5.ORDER_TYPE_SELL)
                    else:
                        log_info("📴 No trade signal. Holding position...")
                else:
                    missing = []
                    if not indicators_m2: missing.append("M2")
                    if not indicators_m15: missing.append("M15")
                    log_warning(f"Could not calculate technical indicators for {', '.join(missing)} timeframe(s). Skipping analysis for this cycle.")
            else:
                missing = []
                if data_m2 is None or data_m2.empty: missing.append("M2")
                if data_m15 is None or data_m15.empty: missing.append("M15")
                log_warning(f"Could not retrieve sufficient OHLC data for {', '.join(missing)} timeframe(s). Skipping analysis for this cycle.")
            
            # Display performance statistics
            perf_monitor.display_stats()
            
            # Calculate time to wait until the next 2-minute candle starts
            now = datetime.now()
            # Calculate minutes until next even 2-minute mark
            minutes_to_next_candle = 2 - (now.minute % 2)
            # Adjust if we are exactly at the start of a candle, to wait for the next full interval
            if minutes_to_next_candle == 2 and now.second == 0 and now.microsecond == 0:
                wait_seconds = 120
            else:
                next_candle_time = now.replace(second=0, microsecond=0) + timedelta(minutes=minutes_to_next_candle)
                wait_seconds = (next_candle_time - now).total_seconds()
            
            # Beautiful waiting message
            wait_panel = Panel(
                f"[bold yellow]⏰ Next candle in {wait_seconds:.0f} seconds[/bold yellow]\n"
                f"[dim]Waiting for optimal entry timing...[/dim]",
                title="⏱️  TIMING",
                border_style="yellow",
                box=box.ROUNDED
            )
            console.print(wait_panel)
            
            time.sleep(wait_seconds)
            
        except KeyboardInterrupt:
            log_info("🛑 Script terminated by user.")
            stop_event.set() # Signal threads to stop
            if mt5_connected:
                mt5.shutdown()
            break
        except Exception as e:
            log_error(f"An unexpected error occurred in the main loop: {e}")
            console.print_exception(show_locals=True)  # Rich traceback
            time.sleep(60)  # Wait a minute before retrying

if __name__ == "__main__":
    try:
        # Beautiful application header
        header = Text("MT5 ENHANCED TRADING BOT", style="bold bright_cyan")
        header.stylize("bold magenta", 0, 3)  # "MT5" in magenta
        
        console.print()
        console.print(Panel(
            header,
            subtitle=f"Magic Number: {MAGIC_NUMBER} | Symbol: {symbol} | Enhanced with Trailing Stop",
            box=box.HEAVY,
            border_style="bright_green"
        ))
        
        # Configuration summary
        config_table = Table(title="⚙️  Bot Configuration", box=box.ROUNDED, show_header=True)
        config_table.add_column("Setting", style="cyan", width=20)
        config_table.add_column("Value", style="green", width=15)
        config_table.add_column("Description", style="dim")
        
        config_table.add_row("Trading Symbol", symbol, "Primary trading instrument")
        config_table.add_row("Risk Per Trade", f"{RISK_PERCENT}%", "Percentage of account risked")
        config_table.add_row("Stop Loss", f"{SL_POINTS} points", "Fixed stop loss distance")
        config_table.add_row("Take Profit", f"{TP_POINTS} points", "Enhanced take profit target")
        config_table.add_row("Trailing Stop", f"{TRAILING_STOP_DISTANCE} pts", "Distance from 7 EMA")
        config_table.add_row("Trail Activation", f"{TRAILING_ACTIVATION_POINTS} pts", "Profit needed to activate trailing")
        config_table.add_row("Max Trades", str(MAX_OPEN_TRADES_PER_MAGIC), "Maximum concurrent positions")
        config_table.add_row("EMA Distance", f"{EMA_DISTANCE_THRESHOLD} pts", "Maximum distance from 20 EMA")
        config_table.add_row("200 EMA Distance", f"{EMA_200_DISTANCE_THRESHOLD} pts", "Minimum distance from 200 EMA for M2")
        
        console.print(config_table)
        console.print()
        
        # Risk warning
        warning_panel = Panel(
            "[bold red]⚠️  RISK WARNING[/bold red]\n\n"
            "Trading involves substantial risk of loss. This bot:\n"
            "• Uses algorithmic trading strategies\n"
            "• Implements trailing stop loss management\n"
            "• Requires constant market monitoring\n"
            "• Past performance doesn't guarantee future results\n\n"
            "[bold yellow]Trade responsibly and never risk more than you can afford to lose.[/bold yellow]",
            title="🚨 DISCLAIMER",
            border_style="bright_red",
            box=box.HEAVY
        )
        console.print(warning_panel)
        
        main_loop()
        
    except Exception as e:
        log_error(f"Critical error in main execution: {e}")
        console.print_exception(show_locals=True)  # Rich traceback
        if mt5_connected:
            mt5.shutdown()
        stop_event.set()
        sys.exit(1)