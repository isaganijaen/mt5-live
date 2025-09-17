#-----------------------------------------
# filename: strategy_02.py
# description: 2min 20/200 EMA Trend Trading Strategy -  Fixed 1:2 Risk Reward Ratio
#-----------------------------------------


# STATUS as of 2025-09-10 08:00 PM
production_status = "DEMO" # DEMO or LIVE




import MetaTrader5 as mt5
import pandas as pd
import time
from datetime import timedelta, datetime
import logging
import traceback
import os
from dotenv import load_dotenv
import talib
import numpy as np
import sys
import threading
from functools import wraps
from collections import deque
import statistics
from entries import insert_entry, create_entries_table
from modules.trading_hours_08pm_to_12nn import is_trading_hours

# Load environment variables
load_dotenv()

# --- Process Lock to prevent multiple instances ---
def singleton_process():
    """Prevents multiple instances of the same bot from running simultaneously"""
    lock_file = f".{MAGIC_NUMBER_FOR_LOG}.lock"
    if os.path.exists(lock_file):
        try:
            with open(lock_file, 'r') as f:
                pid = int(f.read().strip())
            if sys.platform != 'win32':
                os.kill(pid, 0)
            logging.critical(f"Another instance of this bot (MAGIC_NUMBER: {MAGIC_NUMBER_FOR_LOG}) is already running with PID {pid}. Exiting.")
            sys.exit(1)
        except (OSError, ValueError, ProcessLookupError):
            os.remove(lock_file)
    
    with open(lock_file, 'w') as f:
        f.write(str(os.getpid()))
    
    def cleanup():
        if os.path.exists(lock_file):
            os.remove(lock_file)
    
    import atexit
    atexit.register(cleanup)

# Bot details
file_name = os.path.basename(__file__)
account_no = 301457236
account_type = 'Live'
server = 'XMGlobal-MT5 6'
strategy_id = 2
strategy_name = '2min 20/200 EMA Trend Trading Strategy'
trade_note = '2025-09-10 08:00 PM Organized live trading. This is previously the strategy_02.py.'


# --- Configuration ---
MAGIC_NUMBER_FOR_LOG = int(strategy_id)
MAGIC_NUMBER = MAGIC_NUMBER_FOR_LOG

# Set up singleton process lock
singleton_process()

# Logging setup
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler(f"{MAGIC_NUMBER}.log", encoding='utf-8'),
                        logging.StreamHandler()
                    ])

# Trading parameters
symbol = "GOLDm#" if production_status == 'LIVE' else 'GOLD#'
timeframe_m2 = mt5.TIMEFRAME_M2
volume = 0.1 if production_status == 'LIVE' else 0.01
deviation = 20

# Risk management
SL_POINTS = 300
TP_POINTS = 600
MAX_OPEN_TRADES_PER_MAGIC = 1

# EMA settings
EMA_PERIOD_20 = 20
EMA_PERIOD_200 = 200
EMA_TRAILING = 7  # For trailing stop

# Distance thresholds (in points)
EMA_20_DISTANCE_THRESHOLD = 130
EMA_200_MIN_DISTANCE_THRESHOLD = 300
EMA_200_DISTANCE_THRESHOLD = 1400

# Trailing stop settings
TRAILING_TRIGGER_POINTS = 300  # Start trailing when profit >= 500 points
TRAILING_OFFSET_POINTS = 50    # Trail 50 points from 21 EMA

# Trading hours
TRADING_HOURS_START = int(os.getenv("TRADING_HOURS_START", "20"))
TRADING_HOURS_END = int(os.getenv("TRADING_HOURS_END", "12"))

# Global variables
mt5_connected = False
trailing_thread = None
stop_trailing = False

# --- Performance Monitor ---
class PerformanceMonitor:
    def __init__(self):
        self.trade_count = 0
        self.successful_trades = 0
        self.failed_trades = 0
        self.start_time = datetime.now()
        self.response_times = deque(maxlen=100)
        
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
            "uptime": str(uptime).split('.')[0],
            "total_trades": self.trade_count,
            "success_rate": f"{success_rate:.2f}%",
            "avg_response_ms": f"{avg_response:.2f}"
        }

perf_monitor = PerformanceMonitor()

# --- MT5 Connection Functions ---
def connect_to_mt5():
    """Initialize MT5 connection"""
    global mt5_connected
    
    try:
        logging.info("Connecting to MetaTrader 5...")
        if not mt5.initialize():
            error_code = mt5.last_error()
            logging.error(f"MT5 initialize() failed, error code = {error_code}")
            return False
            
        # Optional account login
        mt5_login = int(os.getenv("MT5_LOGIN", "0"))
        mt5_password = os.getenv("MT5_PASSWORD", "")
        mt5_server = os.getenv("MT5_SERVER", "")
        
        if mt5_login != 0 and mt5_password and mt5_server:
            authorized = mt5.login(mt5_login, password=mt5_password, server=mt5_server)
            if not authorized:
                error_code = mt5.last_error()
                logging.error(f"Failed to connect to account {mt5_login}, error code: {error_code}")
                return False
            logging.info(f"Connected to MT5 account {mt5_login}")
        
        version = mt5.version()
        logging.info(f"MetaTrader5 connected: Version {version}")
        mt5_connected = True
        return True
        
    except Exception as e:
        logging.error(f"Exception during MT5 initialization: {e}")
        return False

def get_ohlc_data(symbol, timeframe, count=20000):
    """Get OHLC data from MT5"""
    if not mt5_connected:
        logging.error("MT5 is not connected")
        return None
    
    try:
        rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
        if rates is None:
            error_code = mt5.last_error()
            logging.error(f"Error getting rates for {symbol}, error code = {error_code}")
            return None
            
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        df.set_index('time', inplace=True)
        return df.sort_index()
        
    except Exception as e:
        logging.error(f"Exception getting OHLC data: {e}")
        return None

def calculate_emas(data):
    """Calculate 20 EMA, 200 EMA, and 21 EMA"""
    if data.empty or len(data) < EMA_PERIOD_200:
        logging.warning(f"Not enough data for EMA calculation. Need at least {EMA_PERIOD_200} bars.")
        return None
    
    close_prices = data['close'].values
    
    ema_20 = talib.EMA(close_prices, timeperiod=EMA_PERIOD_20)
    ema_200 = talib.EMA(close_prices, timeperiod=EMA_PERIOD_200)
    latest_ema_trailing_stop = talib.EMA(close_prices, timeperiod=EMA_TRAILING)
    
    # Get latest valid values
    latest_ema_20 = ema_20[~np.isnan(ema_20)][-1] if ema_20[~np.isnan(ema_20)].size > 0 else None
    latest_ema_200 = ema_200[~np.isnan(ema_200)][-1] if ema_200[~np.isnan(ema_200)].size > 0 else None
    latest_latest_ema_trailing_stop = latest_ema_trailing_stop[~np.isnan(latest_ema_trailing_stop)][-1] if latest_ema_trailing_stop[~np.isnan(latest_ema_trailing_stop)].size > 0 else None
    
    if any(ema is None for ema in [latest_ema_20, latest_ema_200, latest_latest_ema_trailing_stop]):
        logging.warning("One or more EMAs are None")
        return None
    
    current_price = close_prices[-1]
    
    result = {
        "ema_20": latest_ema_20,
        "ema_200": latest_ema_200,
        "latest_ema_trailing_stop": latest_latest_ema_trailing_stop,
        "current_price": current_price
    }
    
    logging.info(f"EMAs calculated - Price: {current_price:.2f}, 20EMA: {latest_ema_20:.2f}, 200EMA: {latest_ema_200:.2f}, 21EMA: {latest_latest_ema_trailing_stop:.2f}")
    return result

def calculate_distances(indicators):
    """Calculate distances from EMAs in points"""
    if not indicators:
        return None, None
    
    symbol_info = mt5.symbol_info(symbol)
    if not symbol_info:
        logging.error(f"Failed to get symbol info for {symbol}")
        return None, None
    
    point = symbol_info.point
    current_price = indicators['current_price']
    
    distance_20 = round(abs(current_price - indicators['ema_20']) / point)
    distance_200 = round(abs(current_price - indicators['ema_200']) / point)
    
    logging.info(f"Distances - 20EMA: {distance_20} points, 200EMA: {distance_200} points")
    return distance_20, distance_200

def determine_signal(indicators, distance_20, distance_200):
    """Determine trade signal based on conditions"""
    if not indicators or distance_20 is None or distance_200 is None:
        return "hold", "Insufficient data"
    
    current_price = indicators['current_price']
    ema_20 = indicators['ema_20']
    ema_200 = indicators['ema_200']
    
    # Check distance thresholds
    if distance_20 > EMA_20_DISTANCE_THRESHOLD or distance_200 > EMA_200_DISTANCE_THRESHOLD:
        return "hold", f"❌ Distance thresholds not met (20EMA: {distance_20}/{EMA_20_DISTANCE_THRESHOLD}, 200EMA: {distance_200}/{EMA_200_DISTANCE_THRESHOLD})"
    
    if distance_200 < EMA_200_MIN_DISTANCE_THRESHOLD:
        return "hold", f"❌ Current price too close to 200EMA (Distance: {distance_200} < Min Threshold: {EMA_200_MIN_DISTANCE_THRESHOLD})"

    # Buy conditions: Price above both EMAs
    # if current_price > ema_20 and current_price > ema_200: # original
    if current_price > ema_20 and current_price > ema_200 and ema_20 > ema_200: # refined    
        return "buy", "✅ Price above both 20EMA and 200EMA within distance thresholds"
    
    # Sell conditions: Price below both EMAs
    if current_price < ema_20 and current_price < ema_200 and ema_20 < ema_200:
        return "sell", "✅ Price below both 20EMA and 200EMA within distance thresholds"
    
    return "hold", "❌  Price not clearly above or below both EMAs"

def get_open_positions():
    """Get open positions for this magic number"""
    if not mt5_connected:
        return []
    
    try:
        positions = mt5.positions_get(symbol=symbol)
        if positions is None:
            return []
        
        return [pos for pos in positions if pos.magic == MAGIC_NUMBER]
    except Exception as e:
        logging.error(f"Error getting positions: {e}")
        return []

# def is_trading_hours():
#     """Check if current time is within trading hours"""
#     current_hour = datetime.now().hour
#     return TRADING_HOURS_START <= current_hour < TRADING_HOURS_END

# Running 24/7, so trading hours check is redundant
# def is_trading_hours():
#     """Check if current time is within trading hours"""
#     # This will always return True if TRADING_HOURS_START is 0 and TRADING_HOURS_END is 24
#     # return TRADING_HOURS_START < TRADING_HOURS_END
#     return True  # For now, allow 24/7 trading

    


def check_candle_range(symbol, timeframe, max_range_points):
    """
    Checks if the current open candle's range (High - Low) is within the specified limit.
    """

    if timeframe == mt5.TIMEFRAME_H1:
        timeframe_str = "H1"
    if timeframe == mt5.TIMEFRAME_H4:
        timeframe_str = "H4"    

    if not mt5_connected:
        logging.error("MT5 is not connected for candle range check.")
        return False

    try:
        # Get the last candle (current open candle)
        rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, 1)
        if rates is None or len(rates) == 0:
            error_code = mt5.last_error()
            logging.error(f"Error getting rates for {symbol} {timeframe_str}, error code = {error_code}")
            return False

        current_candle = rates[0]
        high = current_candle['high']
        low = current_candle['low']

        symbol_info = mt5.symbol_info(symbol)
        if not symbol_info:
            logging.error(f"Failed to get symbol info for {symbol}")
            return False
        point = symbol_info.point

        candle_range_points = round(abs(high - low) / point)

        if candle_range_points <= max_range_points:
            logging.info(f"Candle range for {symbol} {timeframe_str} is {candle_range_points} points (<= {max_range_points}). Tradeable.")
            
            cs_range_message = f"""
            ============================================
            | {timeframe_str} Candle Size Range Check
            ============================================
            | High: {high}
            | Low: {low}
            | Range: {candle_range_points} points
            | Max Allowed Range: {max_range_points} points
            | Tradeable: {"✅ Yes" if candle_range_points <= max_range_points else "❌ No"}
            """

            print(cs_range_message)
            
            return True
        else:
            logging.info(f"Candle range for {symbol} {timeframe_str} is {candle_range_points} points (> {max_range_points}). Not tradeable.")
            
            cs_range_message = f"""
            ============================================
            | {timeframe_str} Candle Size Range Check
            ============================================
            | High: {high}
            | Low: {low}
            | Range: {candle_range_points} points
            | Max Allowed Range: {max_range_points} points
            | Tradeable: {"✅ Yes" if candle_range_points <= max_range_points else "❌ No"}
            """

            print(cs_range_message)            
            return False

    except Exception as e:
        logging.error(f"Exception during candle range check for {symbol} {timeframe_str}: {e}")            
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


def execute_trade(trade_type, indicators, distance_20, signal):
    """Execute trade order"""
    if not mt5_connected:
        logging.error("MT5 not connected")
        return False
    
    # Check if we already have max positions
    open_positions = get_open_positions()
    if len(open_positions) >= MAX_OPEN_TRADES_PER_MAGIC:
        logging.info(f"Max positions ({MAX_OPEN_TRADES_PER_MAGIC}) already open")
        return False
    
    symbol_info = mt5.symbol_info(symbol)
    if not symbol_info:
        logging.error(f"Failed to get symbol info for {symbol}")
        return False
    
    if not mt5.symbol_select(symbol, True):
        logging.error(f"Failed to select {symbol}")
        return False
    
    tick_info = mt5.symbol_info_tick(symbol)
    if not tick_info:
        logging.error(f"Failed to get tick info for {symbol}")
        return False
    
    current_price = tick_info.ask if trade_type == mt5.ORDER_TYPE_BUY else tick_info.bid
    point = symbol_info.point
    
    # Calculate SL and TP
    if trade_type == mt5.ORDER_TYPE_BUY:
        sl_price = current_price - (SL_POINTS * point)
        tp_price = current_price + (TP_POINTS * point)
    else:  # SELL
        sl_price = current_price + (SL_POINTS * point)
        tp_price = current_price - (TP_POINTS * point)
    
    # Round prices
    digits = symbol_info.digits
    sl_price = round(sl_price, digits)
    tp_price = round(tp_price, digits)
    
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": volume,
        "type": trade_type,
        "price": current_price,
        "deviation": deviation,
        "magic": MAGIC_NUMBER,
        "comment": f"{production_status}_{file_name}_{MAGIC_NUMBER}",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
        "sl": sl_price,
        "tp": tp_price,
    }
    
    trade_type_str = "BUY" if trade_type == mt5.ORDER_TYPE_BUY else "SELL"
    logging.info(f"Executing {trade_type_str} order at {current_price:.2f}, SL: {sl_price:.2f}, TP: {tp_price:.2f}")
    
    result = mt5.order_send(request)
    
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        logging.error(f"Order failed: retcode={result.retcode}, comment={result.comment}")
        perf_monitor.record_trade(False)
        return False
    
    logging.info(f"Order executed successfully. Deal ticket: {result.deal}")
    # Save to database
    entry_data = {
        'file_name': file_name,
        'account_no': account_no,
        'account_type': account_type,
        'server': server,
        'strategy_id': strategy_id,
        'symbol': symbol,
        'trend_timeframe': str(timeframe_m2), # Convert timeframe object to string
        'entry_timeframe': str(timeframe_m2),
        'deviation': deviation,
        'SL_POINTS': SL_POINTS,
        'TP_POINTS': TP_POINTS,
        'EMA_DISTANCE_THRESHOLD': EMA_20_DISTANCE_THRESHOLD,  # Using 20 EMA threshold
        'MAX_OPEN_TRADES_PER_MAGIC': MAX_OPEN_TRADES_PER_MAGIC,
        'EMA_PERIOD': EMA_PERIOD_20,  # Using 20 EMA period
        'TRADING_HOURS_START': TRADING_HOURS_START,
        'TRADING_HOURS_END': TRADING_HOURS_END,
        'latest_ema': indicators['ema_20'],
        'ema_distance_m2': distance_20,
        'signal': signal,
        'trade_type': trade_type_str,
        'current_price': current_price,
        'sl_price': sl_price,
        'tp_price': tp_price,
        'deal_ticket': result.deal,
        'trade_note': trade_note,
        'order_ticket': result.order
    }
    
    if not insert_entry(entry_data):
        logging.error("Failed to save trade to database")
        
    perf_monitor.record_trade(True)
    

    
    return True

def manage_trailing_stops():
    """Manage trailing stops for open positions"""
    global stop_trailing
    
    while not stop_trailing:
        try:
            if not mt5_connected:
                time.sleep(10)
                continue
            
            positions = get_open_positions()
            if not positions:
                time.sleep(10)
                continue
            
            # Get fresh EMA data
            data = get_ohlc_data(symbol, timeframe_m2)
            if data is None:
                time.sleep(10)
                continue
            
            indicators = calculate_emas(data)
            if not indicators:
                time.sleep(10)
                continue
            
            symbol_info = mt5.symbol_info(symbol)
            if not symbol_info:
                time.sleep(10)
                continue
            
            point = symbol_info.point
            latest_ema_trailing_stop = indicators['latest_ema_trailing_stop']
            
            for pos in positions:
                try:
                    tick = mt5.symbol_info_tick(symbol)
                    if not tick:
                        continue
                    
                    current_price = tick.bid if pos.type == mt5.ORDER_TYPE_BUY else tick.ask
                    
                    # Calculate profit in points
                    if pos.type == mt5.ORDER_TYPE_BUY:
                        profit_points = round((current_price - pos.price_open) / point)
                        new_sl = latest_ema_trailing_stop - (TRAILING_OFFSET_POINTS * point)
                        # Only move SL up
                        if profit_points >= TRAILING_TRIGGER_POINTS and new_sl > pos.sl:
                            new_sl = round(new_sl, symbol_info.digits)
                            modify_position_sl(pos.ticket, new_sl, pos.tp)
                            logging.info(f"Trailed BUY SL to {new_sl:.2f} (21EMA: {latest_ema_trailing_stop:.2f})")
                    
                    else:  # SELL
                        profit_points = round((pos.price_open - current_price) / point)
                        new_sl = latest_ema_trailing_stop + (TRAILING_OFFSET_POINTS * point)
                        # Only move SL down
                        if profit_points >= TRAILING_TRIGGER_POINTS and new_sl < pos.sl:
                            new_sl = round(new_sl, symbol_info.digits)
                            modify_position_sl(pos.ticket, new_sl, pos.tp)
                            logging.info(f"Trailed SELL SL to {new_sl:.2f} (21EMA: {latest_ema_trailing_stop:.2f})")
                
                except Exception as e:
                    logging.error(f"Error managing trailing stop for position {pos.ticket}: {e}")
                    continue
            
            time.sleep(10)  # Check every 10 seconds
            
        except Exception as e:
            logging.error(f"Error in trailing stop thread: {e}")
            time.sleep(30)

def modify_position_sl(ticket, new_sl, tp):
    """Modify position stop loss"""
    request = {
        "action": mt5.TRADE_ACTION_SLTP,
        "position": ticket,
        "sl": new_sl,
        "tp": tp,
        "magic": MAGIC_NUMBER,
        "comment": "Trailing SL"
    }
    
    result = mt5.order_send(request)
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        logging.error(f"Failed to modify SL for position {ticket}: {result.comment}")
        return False
    return True

def start_trailing_thread():
    """Start the trailing stop thread"""
    global trailing_thread, stop_trailing
    
    stop_trailing = False
    trailing_thread = threading.Thread(target=manage_trailing_stops, daemon=True)
    trailing_thread.start()
    logging.info("Trailing stop thread started")

def stop_trailing_thread():
    """Stop the trailing stop thread"""
    global stop_trailing
    stop_trailing = True
    if trailing_thread:
        trailing_thread.join(timeout=5)
    logging.info("Trailing stop thread stopped")

# --- Main Trading Loop ---
def main_loop():
    """Main trading loop"""
    global mt5_connected
    
    # Connect to MT5
    if not connect_to_mt5():
        logging.critical("Failed to connect to MT5")
        return
    
    # Start trailing stop thread
    start_trailing_thread()
    
    logging.info("Starting main trading loop...")
    
    try:
        while True:
            try:
                # Check trading hours
                if not is_trading_hours():
                    logging.info(f"Outside trading hours ({TRADING_HOURS_START}:00-{TRADING_HOURS_END}:00)")
                    time.sleep(60)
                    continue
                
                # Get M2 data and calculate EMAs
                data = get_ohlc_data(symbol, timeframe_m2)
                if data is None:
                    logging.warning("Failed to get M2 data")
                    time.sleep(60)
                    continue
                
                indicators = calculate_emas(data)
                if not indicators:
                    logging.warning("Failed to calculate EMAs")
                    time.sleep(60)
                    continue
                
                # Calculate distances
                distance_20, distance_200 = calculate_distances(indicators)
                if distance_20 is None or distance_200 is None:
                    logging.warning("Failed to calculate distances")
                    time.sleep(60)
                    continue
                
                # Determine signal
                signal, reason = determine_signal(indicators, distance_20, distance_200)
                logging.info(f"Signal: {signal.upper()}, Reason: {reason}")
                
                # Check H1 and H4 candle ranges
                if not check_1h_open_candle_range():
                    logging.info("H1 candle range not tradeable. Holding.")
                    time.sleep(60)
                    continue
                
                if not check_4h_open_candle_range():
                    logging.info("H4 candle range not tradeable. Holding.")
                    time.sleep(60)
                    continue

                # Execute trades
                if signal == "buy":
                    execute_trade(mt5.ORDER_TYPE_BUY, indicators, distance_20, signal)
                elif signal == "sell":
                    execute_trade(mt5.ORDER_TYPE_SELL, indicators, distance_20, signal)
                
                # Performance stats
                stats = perf_monitor.get_stats()
                logging.info(f"Performance: {stats['uptime']} uptime, {stats['total_trades']} trades, {stats['success_rate']} success")
                
                # Wait for next 2-minute candle
                now = datetime.now()
                minutes_to_next = 2 - (now.minute % 2)
                if minutes_to_next == 2 and now.second == 0:
                    wait_seconds = 120
                else:
                    next_candle = now.replace(second=0, microsecond=0) + timedelta(minutes=minutes_to_next)
                    wait_seconds = (next_candle - now).total_seconds()
                
                logging.info(f"Waiting {wait_seconds:.0f} seconds for next candle")
                time.sleep(max(wait_seconds, 5))  # Minimum 5 seconds
                
            except Exception as e:
                logging.error(f"Error in main loop: {e}")
                time.sleep(60)
                
    except KeyboardInterrupt:
        logging.info("Script terminated by user")
    finally:
        stop_trailing_thread()
        if mt5_connected:
            mt5.shutdown()

if __name__ == "__main__":
    try:
        # Create database table
        create_entries_table()
        
        logging.info("=" * 50)
        logging.info(f"Starting M2 EMA Trading Bot (Magic: {MAGIC_NUMBER})")
        logging.info(f"Symbol: {symbol}")
        logging.info(f"SL: {SL_POINTS} points, TP: {TP_POINTS} points")
        logging.info(f"Max positions: {MAX_OPEN_TRADES_PER_MAGIC}")
        logging.info(f"Trading hours: {TRADING_HOURS_START}:00-{TRADING_HOURS_END}:00")
        logging.info("=" * 50)
        
        main_loop()
        
    except Exception as e:
        logging.critical(f"Critical error: {e}")
        if mt5_connected:
            mt5.shutdown()
        sys.exit(1)