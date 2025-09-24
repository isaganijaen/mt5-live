# strategy_07.py
import MetaTrader5 as mt5
from dotenv import load_dotenv
import os
import pandas as pd
import time
import math
from datetime import datetime, timedelta
import threading # Import threading module

# Rich imports for beautiful logging
from rich.console import Console
from rich.logging import RichHandler
from rich.table import Table
from rich import box
# import modules.mt5_config as mt5_config
from modules.mt5_config_v1_1_0 import TradingConfig
from account_list import account_type
from modules.trading_hours_24 import is_trading_hours
from modules.chart_screenshot import screenshot # Import the screenshot class

#-----------------------------------
# Utilities and Global Variables
#-----------------------------------
from modules.utilities import log_success, log_error, log_warning, log_info
# Import the reusable classes and the new Indicators class
from modules.mt5_manager import MT5Manager
from modules.indicators import Indicators
from modules.position_manager import PositionManager # Import the new class
from modules.profit_manager import TakeProfitMonitor # Import the new TakeProfitMonitor class
import mplfinance as mpf

#-------------------------------------
# Library Initialization
#-------------------------------------
console = Console()
load_dotenv()
SCREENSHOTS_DIR = "screenshots/GOLD/"



def wait_until_next_interval(interval_seconds: int = 10):
    """
    Calculates the time until the start of the next exact interval
    and sleeps. This ensures the script runs at the top of each interval.

    Args:
        interval_seconds (int): The desired interval in seconds (e.g., 60 for 1 minute).
    """
    now = datetime.now()
    
    # Get total seconds from the start of the current day
    total_seconds_today = (now - now.replace(hour=0, minute=0, second=0, microsecond=0)).total_seconds()
    
    # Calculate the next timestamp divisible by the interval
    next_timestamp_seconds = math.ceil(total_seconds_today / interval_seconds) * interval_seconds
    
    # Calculate the time for the next interval
    next_interval = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(seconds=next_timestamp_seconds)
    
    # Calculate the sleep duration
    sleep_duration = (next_interval - now).total_seconds()
    
    if sleep_duration > 0:
        log_info(f"Sleeping for {sleep_duration:.2f} seconds to align with the next interval.")
        time.sleep(sleep_duration)
    else:
        log_warning(f"Execution took longer than {interval_seconds} seconds. Skipping wait and continuing.")
        time.sleep(1)


#-------------------------------------
# Main Strategy
#-------------------------------------
class M2AverageZone:
    """
    Encapsulates the full logic for the M2 Average Zone Strategy.
    """
    def __init__(self, config, mt5_manager, position_open_event, screenshot_tool):
        self.config = config
        self.mt5_manager = mt5_manager
        self.position_open_event = position_open_event # Add the event here
        self.screenshot_tool = screenshot_tool # Add the screenshot tool
        
    def get_data(self):
        """
        Fetches the latest price data from MT5.
        """
        rates = mt5.copy_rates_from_pos(self.config.symbol, mt5.TIMEFRAME_M2, 0, 20000)
        if rates is None:
            log_error(f"Failed to get rates for {self.config.symbol}")
            return None
        
        rates_df = pd.DataFrame(rates)
        rates_df['time'] = pd.to_datetime(rates_df['time'], unit='s')
        return rates_df

    def execute_trade(self, order_type, rates_df):
        """
        Executes a trade based on the strategy signal.
        """
        symbol_info_tick = mt5.symbol_info_tick(self.config.symbol)
        symbol_info = mt5.symbol_info(self.config.symbol)
        
        if symbol_info_tick is None or symbol_info is None:
            log_error(f"Failed to get symbol info for {self.config.symbol}.")
            return False

        # Determine the price, SL, and TP based on the order type
        if order_type == mt5.ORDER_TYPE_BUY:
            signal_type = 'BUY'
            price = symbol_info_tick.ask
            sl = price - (self.config.sl_points * symbol_info.point)
            tp = price + (self.config.tp_points * symbol_info.point)
        else:  # mt5.ORDER_TYPE_SELL
            signal_type = 'SELL'
            price = symbol_info_tick.bid
            sl = price + (self.config.sl_points * symbol_info.point)
            tp = price - (self.config.tp_points * symbol_info.point)

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": self.config.symbol,
            "volume": self.config.volume,
            "type": order_type,
            "price": price,
            "deviation": self.config.deviation,
            "magic": self.config.strategy_id,
            "comment": self.config.filename,
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
            "sl": sl,
            "tp": tp,
        }

        result = mt5.order_send(request)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            log_error(f"Failed to send order, error code: {result.retcode}")
            return False
        
        log_success(f"Order sent successfully. Ticket: {result.order} \n")

        order_table = Table(title="Order Confirmation",box=box.ROUNDED, show_header=True)
        order_table.add_column("Details", style="cyan", width=20)
        order_table.add_column("Value", style="green", width=15)

        order_table.add_row("Ticket", f"{result.order}")
        order_table.add_row("Order Type", f"{'Buy' if request['type'] == mt5.ORDER_TYPE_BUY else 'Sell'}")
        order_table.add_row("SL", f"{request['sl'] if 'sl' in request and request['sl'] != 0.0 else 'N/A'}")
        order_table.add_row("TP", f"{request['tp'] if 'tp' in request and request['tp'] != 0.0 else 'N/A'}")
        

        console.print(order_table)
        print("\n")

        # ----------------------------------------------------
        # NEW: Create Chart Screenshot after successful trade
        # ----------------------------------------------------
        try:
            # FIX: Use 'result.order' as a robust alternative for the position ticket
            position_ticket = result.order 
            deal_id = result.deal # The deal ID
            
            # Use the position_ticket as the base filename (as per request for position_id)
            base_filename = f"{position_ticket}.png"
            
            # Call the chart creation function
            self.screenshot_tool.create_trade_chart(
                df=rates_df, 
                signal_type=signal_type, 
                entry_price=price, 
                sl_price=sl, 
                tp_price=tp, 
                position_ticket=position_ticket, 
                deal_id=deal_id, 
                position_id=position_ticket, # Using ticket as ID
                comment="M2_Average_Zone", # A descriptive comment
                filename=base_filename, 
                symbol=self.config.symbol,
                sl_points=self.config.sl_points, 
                tp_points=self.config.tp_points,
                strategy_id=self.config.strategy_id
            )
        except Exception as e:
            log_error(f"Screenshot generation failed: {e}")
        # ----------------------------------------------------        
        
        # Wake up the position manager and take profit monitor threads
        self.position_open_event.set()
        return True

    def run(self):
        """
        Main loop for the strategy.
        """
        log_info(f"Starting {self.config.symbol} M2 Average Zone Strategy.\n")
        
        # Display the configuration
        self.config.display()
        
        # Main trading loop
        while True:
            # Use the new precise timing function
            wait_until_next_interval()

            # Check for existing positions
            positions = mt5.positions_get(symbol=self.config.symbol)
            symbol_info = mt5.symbol_info(self.config.symbol)
            # Retrieve the point size dynamically
            point = symbol_info.point
            # print(f"Point Multiplier:  {point}")
            print("\n\n")

            if positions and any(p.magic == self.config.strategy_id for p in positions):
                log_info(f"Position already exists. Skipping entry signal check.")
                continue

            # Get new data
            rates_df = self.get_data()
            if rates_df is None or len(rates_df) < self.config.long_term_trend + 10:
                log_warning("Not enough data to run indicators. Waiting...")
                continue
            

            # ------------------------------------------------------------------
            # FIX: Calculate and add EMA columns required by chart_screenshot.py
            # ------------------------------------------------------------------
            # Using your configuration periods to calculate the full EMA series:
            
            # 'ema_fast' (e.g., using trailing_period=7)
            rates_df['entry'] = rates_df['close'].ewm(span=self.config.trailing_period, adjust=False).mean()
            rates_df['resistance'] = rates_df['high'].ewm(span=self.config.ema_resistance, adjust=False).mean()
            rates_df['support'] = rates_df['low'].ewm(span=self.config.ema_support, adjust=False).mean()
            
            # 'ema_slow' (e.g., using consolidation_filter=20)
            rates_df['consolidation_filter'] = rates_df['close'].ewm(span=self.config.consolidation_filter, adjust=False).mean()
            
            # 'ema_long' (e.g., using long_term_trend=21)
            rates_df['long_term_trend'] = rates_df['close'].ewm(span=self.config.long_term_trend, adjust=False).mean()
            
            # ------------------------------------------------------------------            


            # Check Trading Hours

            if not is_trading_hours():
                log_warning(f"Outside Trading Hours. Waiting...")
                continue # conutine means ignore succeeding codes and will go back to the main loop.




            # Use the Indicators class
            indicator_tools = Indicators(rates_df)
            
            #-------------------------------------------------------
            # CORE STRATEGY LOGIC
            #-------------------------------------------------------
            
            # Check Indicators' Values
            current_price = indicator_tools.get_current_price()

            ema_resistance_high = indicator_tools.get_last_ema_value(
                period=self.config.ema_resistance,
                price_type='high'
            )        

            ema_support_low = indicator_tools.get_last_ema_value(
                period=self.config.ema_support,
                price_type='low'
            )     

            ema_trailing_period = indicator_tools.get_last_ema_value(
                period=self.config.trailing_period,
                price_type='close'
            )                                  
            

            ema_momentum_consolidation_filter = indicator_tools.get_last_ema_value(
                period=self.config.momentum_consolidation_filter,
                price_type='close'
            )   


            ema_consolidation_filter = indicator_tools.get_last_ema_value(
                period=self.config.consolidation_filter,
                price_type='close'
            )   

            ema_long_term_trend = indicator_tools.get_last_ema_value(
                period=self.config.long_term_trend,
                price_type='close'
            )               


            # Calculate all distances in points
            points_distance_vs_ema_resistance = abs(current_price - ema_resistance_high) / point
            points_distance_vs_ema_support = abs(current_price - ema_support_low) / point
            points_distance_vs_trailing_guide = abs(current_price - ema_trailing_period) / point
            points_distance_vs_momentum_consolidation_guide = abs(current_price - ema_momentum_consolidation_filter) / point
            points_distance_vs_consolidation_guide = abs(current_price - ema_consolidation_filter) / point
            points_distance_vs_long_term_trend_guide = abs(current_price - ema_long_term_trend) / point


            # Calculate Candle Ranges
            candle_1h_range = indicator_tools.calculate_candle_range(self.config.symbol,mt5.TIMEFRAME_H1)
            candle_4h_range = indicator_tools.calculate_candle_range(self.config.symbol,mt5.TIMEFRAME_H4)

            print(f"{datetime.now()}")
            self.config.display()
            print(f"\n\nCurrent Price:  {current_price}")
            

            print("\n")

            #------------------------------------------
            # INDICATORS TABLE
            #------------------------------------------
            config_indicators_table = Table(title="Indicators", box=box.ROUNDED, show_header=True)
            config_indicators_table.add_column("Setting", style="cyan")
            config_indicators_table.add_column("Value", style="green")
            config_indicators_table.add_column("Description", style="dim")           

            config_indicators_table.add_row(f"{self.config.ema_support} Period EMA Low", str(round(ema_support_low,3)), "Support" ) 
            config_indicators_table.add_row(f"{self.config.ema_resistance} Period EMA High", str(round(ema_resistance_high,3)), "Resistance") 
            config_indicators_table.add_row(f"{self.config.trailing_period} Period EMA Close", str(round(ema_trailing_period,3)), "Trailing Guide" ) 
            config_indicators_table.add_row(f"{self.config.consolidation_filter} Period Close", str(round(ema_momentum_consolidation_filter,3)), "Momentum Consolidation Filter" ) 
            config_indicators_table.add_row(f"{self.config.consolidation_filter} Period Close", str(round(ema_consolidation_filter,3)), "Consolidation Filter" ) 
            config_indicators_table.add_row(f"{self.config.long_term_trend} Period EMA Close", str(round(ema_long_term_trend,3)), "Long Term Trend" ) 

            console.print(config_indicators_table)

            print("\n")


            

            # Identifying Trend
            if current_price > ema_support_low and ema_support_low > ema_consolidation_filter and ema_consolidation_filter > ema_long_term_trend:
                trend = 'bullish 🟢'
            elif current_price < ema_resistance_high and ema_resistance_high < ema_consolidation_filter and ema_consolidation_filter < ema_long_term_trend:    
                trend = 'bearish 🟡'
            else:
                trend = 'consolidation 🔵'    

              



            # Candle Range Volatility
            if candle_1h_range <= self.config.max_candle_range_1h_allowed:
                h1_within_range = True
                candle_1h_range_status = 'Within Threshold 🟢'
            else:
                h1_within_range = False    
                candle_1h_range_status = 'Outside Threshold 🔴'


            if candle_4h_range <= self.config.max_candle_range_4h_allowed:
                h4_within_range = True
                candle_4h_range_status = 'Within Threshold 🟢'
            else:
                h4_within_range = False    
                candle_4h_range_status = 'Outside Threshold 🔴'     


            #------------------------------------------
            # METRICS TABLE
            #------------------------------------------            


            config_metrics_table = Table(title="Metrics", box=box.ROUNDED, show_header=True)
            config_metrics_table.add_column("Metrics", style="cyan")
            config_metrics_table.add_column("Value", style="green")
 
            config_metrics_table.add_row(f"Trend", str("Bullish" if trend == 'bullish 🟢' else "Bearish" if trend == 'bearish 🟡' else "Consolidation") ) 
            config_metrics_table.add_row(f"Distance vs Trailing Guide ", f"{points_distance_vs_trailing_guide:.2f} Points")
            config_metrics_table.add_row(f"Distance vs Support ", f"{points_distance_vs_ema_support:.2f} Points")
            config_metrics_table.add_row(f"Distance vs Resistance ", f"{points_distance_vs_ema_resistance:.2f} Points" )
            config_metrics_table.add_row(f"Distance vs Consolidation Filter ", f"{points_distance_vs_consolidation_guide:.2f} Points" )
            config_metrics_table.add_row(f"Distance vs Long Term Trend ", f"{points_distance_vs_long_term_trend_guide:.2f} Points" )
            config_metrics_table.add_row(f"H1 Candle Range", f"{candle_1h_range:.2f} Points" )
            config_metrics_table.add_row(f"H4 Candle Range", f"{candle_4h_range:.2f} Points" )             

            console.print(config_metrics_table)
   
            print("\n")                           


            print(f"Trend: {trend}\n")
            # print(f"H1 Candle Range (Disabled): {candle_1h_range_status}")  
            # print(f"H4 Candle Range (Disabled): {candle_4h_range_status}") 

            #------------------------------------------
            # NOTES TABLE
            #--------------------------------                                                                                                       ----------                  
            print(f"Note: In style of strategy_19 but running in M2 timeframe.")
            # print(f"Difference:")
            # print(f"TP=300 for 1:1 R ✨")
            # print(f"consolidation_filter=40 (instead of 50)")
            # print(f"long_term_trend=NONE (same style of )")

            notes_table = Table(title="📝 NOTE", box=box.ROUNDED, show_header=True)
            notes_table.add_column("Setting", style="cyan")
            notes_table.add_column("Value", style="green")
            notes_table.add_column("Description", style="dim")

            notes_table.add_row("Stop Loss", f"{self.config.sl_points} pts", "Fixed stop loss distance")
            notes_table.add_row("Take Profit", f"{self.config.tp_points} pts", "Enhanced take profit target")
            notes_table.add_row("Entry Zone",f"{self.config.support_resistance_distance_threshold} pts","Minimum Price Distance vs S/R")
            notes_table.add_row("Support",f"{self.config.ema_support}","Buy Zone (EMA Low)")
            notes_table.add_row("Resistance",f"{self.config.ema_resistance}","Sell Zone (EMA High)")
            notes_table.add_row("Trail Activation", f"{self.config.trailing_activation_points} pts", "Trailing mechanism trigger points")    
            notes_table.add_row("Trailing Stop", f"{self.config.trailing_stop_distance} pts", "Trailing stop distance")

            notes_table.add_row("Momentum Consolidation Filter",f"{self.config.momentum_consolidation_filter}","Momentum Consolidation Filter (EMA close)")     
            notes_table.add_row("Consolidation Filter",f"{self.config.consolidation_filter}","Consolidation Filter (EMA close)")
            notes_table.add_row("Long Term Trend",f"{self.config.long_term_trend}","Long Term Trend (EMA Close)")       

            console.print(notes_table)
                 
            print("\n")     
 


            #------------------------------------------
            # Performance TABLE
            #------------------------------------------      

            tbl_performance_review = Table(title="Performance Review", box=box.ROUNDED, show_header=True)
            tbl_performance_review.add_column("Analysis", style="cyan")
            tbl_performance_review.add_row(f"TBD")
            
            # 🔒 Uncomment When Ready
            #console.print(tbl_performance_review)




            #-----------------------------------------------------------------------------
            # METRIC EVALUATION | TRADE EXECUTION 
            #-----------------------------------------------------------------------------
            
            # The threshold is now a fixed point value, no need to multiply by point
            distance_threshold_in_points = self.config.support_resistance_distance_threshold
           
            # Disabling Candle Range threshold for now as trades would be limited on a trending market.
            #if trend == 'bullish 🟢' and points_distance_vs_trailing_guide <= distance_threshold_in_points and h1_within_range and h4_within_range: 
            if trend == 'bullish 🟢' and points_distance_vs_ema_support <= distance_threshold_in_points:            
                print("Buying!")
                signal = 'buy'
                log_info("Bullish signal and price is in Support Zone. Placing BUY order.")
                self.execute_trade(mt5.ORDER_TYPE_BUY,rates_df)
            # Disabling Candle Range threshold for now as trades would be limited on a trending market.
            #elif trend == 'bearish 🟡' and points_distance_vs_trailing_guide <= distance_threshold_in_points and h1_within_range and h4_within_range:     
            elif trend == 'bearish 🟡' and points_distance_vs_ema_resistance <= distance_threshold_in_points:                    
                print(f"Selling! {self.config.volume}")
                signal = 'sell'
                log_info("Bearish signal and price is in Resistance Zone. Placing SELL order.")
                self.execute_trade(mt5.ORDER_TYPE_SELL,rates_df)                
            else:
                # print("Hold!")
                signal = 'hold'
                if trend == 'bullish 🟢':
                    log_info(f"Signal: {signal}")
                    log_info(f"No valid trading signal detected.")
                    log_info(f"Bullish trend but price's distance is too far from Support Zone/Trailing Guide ({points_distance_vs_trailing_guide:.2f} points)")
                    if not h1_within_range:
                        log_info(f"Note: 1H candle range {candle_1h_range} outide the treshold {self.config.max_candle_range_1h_allowed}.")
                    if not h4_within_range:
                        log_info(f"Note: 4H candle range {candle_4h_range} outide the treshold {self.config.max_candle_range_4h_allowed}.")                        
                elif trend == 'bearish 🟡':
                    log_info(f"Signal: {signal}")
                    log_info(f"No valid trading signal detected.")
                    log_info(f"Bearish trend but price's distance is too far from Resistance Zone/Trailing Guide ({points_distance_vs_ema_resistance:.2f} points).")
                    if not h1_within_range:
                        log_info(f"Note: 1H candle range {candle_1h_range} outide the treshold {self.config.max_candle_range_1h_allowed}.")
                    if not h4_within_range:
                        log_info(f"Note: 4H candle range {candle_4h_range} outide the treshold {self.config.max_candle_range_4h_allowed}.")                         
                else:
                    log_info(f"Signal: {signal}")
                    log_info("No clear trend. Potential consolidation or reversal.")
                

            log_info("Waiting for the next loop...")




#-------------------------------------
# Main Entry Point 
#-------------------------------------

# ------- Todo ---------------
# - Check how may were closed > 0.0 but less than target
# - These are Trailing Stopped.
# - Maybe we can reduce the target to 150 points
# - Giving us 1R return.
# - (Will test in separate file)

def start_strategy():
    """Main function to start the bot."""

    production_status = "DEMO" # DEMO or LIVE
    filename = os.path.basename(__file__)
    description = 'M2 Average Zone Trading (2R)'
    
    


    log_info(f"Initializing {description} System.")
    
    # 1. Define configuration settings, can be from env variables
    config_settings = TradingConfig(
        symbol="GOLD#" if production_status == 'DEMO' else "GOLDm#",
        filename=filename,
        strategy_id=67 if production_status == 'DEMO'  else 32, # if LIVE
        volume = 0.01 if production_status == 'DEV' else 0.01 if production_status == 'DEMO' else 0.1, # if LIVE
        deviation=20,
        sl_points=170,
        tp_points=300,
        trailing_activation_points=320, # (3500 = 2x ave. candle range in M2) 2000 points or $0.2 profit | 10 = 1000, 20 = 2000
        trailing_stop_distance=50,
        trailing_period=3,
        ema_resistance=3,
        ema_support=3,
        support_resistance_distance_threshold=70,
        momentum_consolidation_filter=10,
        consolidation_filter=12,
        long_term_trend=21,
        max_candle_range_1h_allowed=1100,
        max_candle_range_4h_allowed=1800         
    )

    # ----------------------------------------------------
    # NEW: Determine the screenshot directory dynamically
    # ----------------------------------------------------
    symbol = config_settings.symbol
    if 'GOLD' in symbol.upper():
        screenshot_dir = "screenshots/GOLD/"
    elif 'BTCUSD' in symbol.upper():
        screenshot_dir = "screenshots/BTCUSD/"
    else:
        # Fallback for other symbols
        screenshot_dir = f"screenshots/{symbol}/"
        
    # Instantiate the screenshot utility
    screenshot_tool = screenshot(SCREENSHOT_DIR=screenshot_dir)
    # ----------------------------------------------------    

    # 2. Instantiate and connect the MT5 manager

     # Change to "LIVE" for live trading

    # print(production_status)

    if production_status == "LIVE":
        login = int(os.getenv("MT5_LOGIN_LIVE"))
        password = os.getenv("MT5_PASSWORD_LIVE")
        server = os.getenv("MT5_SERVER_LIVE")
        act_type = "Live"
 

    
    else:
        login = int(os.getenv("MT5_LOGIN_DEMO"))
        password = os.getenv("MT5_PASSWORD_DEMO")
        server = os.getenv("MT5_SERVER_DEMO")
        act_type = "Demo"



    log_info(f"Attempting to connect with login: {login}, server: {server}")

    mt5_login = login
    mt5_password = password
    mt5_server = server
    
    mt5_manager = MT5Manager(login=mt5_login, password=mt5_password, server=mt5_server)

    
    
    if not mt5_manager.connect():
        log_error("Could not connect to MT5. Exiting.")
        return
    
    mt5_manager.get_account_info(act_type)

    # 3. Instantiate and start the position manager and take profit monitor threads
    position_open_event = threading.Event()
    
    position_manager = PositionManager(config=config_settings, mt5_manager=mt5_manager, position_open_event=position_open_event)
    position_manager.daemon = True # Allows the thread to exit when the main program exits
    position_manager.start()

    take_profit_monitor = TakeProfitMonitor(config=config_settings, mt5_manager=mt5_manager, position_open_event=position_open_event)
    take_profit_monitor.daemon = True
    take_profit_monitor.start()

    # 4. Instantiate the strategy and run it
    my_strategy = M2AverageZone(config=config_settings, mt5_manager=mt5_manager, position_open_event=position_open_event,screenshot_tool=screenshot_tool)
    try:
        my_strategy.run()
    except KeyboardInterrupt:
        log_warning("Strategy interrupted by user. Shutting down.")
    finally:
        # 5. Shutdown MT5 connection and stop the threads
        position_manager.stop()
        take_profit_monitor.stop()
        mt5.shutdown()
        log_success("MetaTrader5 shutdown.")


if __name__ == "__main__":        
     # 2. Display account info   
    start_strategy()
