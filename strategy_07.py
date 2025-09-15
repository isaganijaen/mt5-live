# strategy_07.py
import MetaTrader5 as mt5
from dotenv import load_dotenv
import os
import pandas as pd
import time
from datetime import datetime, timedelta
import threading # Import threading module

# Rich imports for beautiful logging
from rich.console import Console
from rich.logging import RichHandler
from rich.table import Table
from rich import box
import modules.mt5_config as mt5_config
from account_list import account_type
from modules.trading_hours_24 import is_trading_hours

#-----------------------------------
# Utilities and Global Variables
#-----------------------------------
from modules.utilities import log_success, log_error, log_warning, log_info
# Import the reusable classes and the new Indicators class
from modules.mt5_config import TradingConfig
from modules.mt5_manager import MT5Manager
from modules.indicators import Indicators
from modules.position_manager import PositionManager # Import the new class


#-------------------------------------
# Library Initialization
#-------------------------------------
console = Console()
load_dotenv()



def wait_until_next_minute():
    """
    Calculates the time until the start of the next minute and sleeps.
    This ensures the script runs exactly at the top of each minute.
    """
    now = datetime.now()
    default_waiting_minute = 1
    # Calculate the time for the next full minute
    next_minute = now.replace(second=0, microsecond=0) + timedelta(minutes=default_waiting_minute)
    
    # Calculate the sleep duration
    sleep_duration = (next_minute - now).total_seconds()
    
    if sleep_duration > 0:
        log_info(f"Sleeping for {sleep_duration:.2f} seconds to align with the next minute.")
        time.sleep(sleep_duration)
    else:
        # If the sleep duration is negative or zero, we've already passed the minute mark.
        # This can happen if the execution takes more than 60 seconds.
        # We just wait for a second and check again.
        log_warning("Execution took longer than a minute. Skipping wait and continuing.")
        time.sleep(1)


#-------------------------------------
# Main Strategy
#-------------------------------------
class M1AverageZone:
    """
    Encapsulates the full logic for the M1 Average Zone Strategy.
    """
    def __init__(self, config, mt5_manager, position_open_event):
        self.config = config
        self.mt5_manager = mt5_manager
        self.position_open_event = position_open_event # Add the event here
        
    def get_data(self):
        """
        Fetches the latest price data from MT5.
        """
        rates = mt5.copy_rates_from_pos(self.config.symbol, mt5.TIMEFRAME_M1, 0, 20000)
        if rates is None:
            log_error(f"Failed to get rates for {self.config.symbol}")
            return None
        
        rates_df = pd.DataFrame(rates)
        rates_df['time'] = pd.to_datetime(rates_df['time'], unit='s')
        return rates_df

    def execute_trade(self, order_type):
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
            price = symbol_info_tick.ask
            sl = price - (self.config.sl_points * symbol_info.point)
            tp = price + (self.config.tp_points * symbol_info.point)
        else:  # mt5.ORDER_TYPE_SELL
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
        
        # Wake up the position manager thread
        self.position_open_event.set()
        return True

    def run(self):
        """
        Main loop for the strategy.
        """
        log_info(f"Starting {self.config.symbol} M1 Average Zone Strategy.")
        
        # Display the configuration
        self.config.display()
        
        # Main trading loop
        while True:
            # Use the new precise timing function
            wait_until_next_minute()

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
            if rates_df is None or len(rates_df) < self.config.ema_200_period + 10:
                log_warning("Not enough data to run indicators. Waiting...")
                continue


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

            ema_20_high = indicator_tools.get_last_ema_value(
                period=self.config.ema_20_period_high,
                price_type='high'
            )        

            ema_20_low = indicator_tools.get_last_ema_value(
                period=self.config.ema_20_period_low,
                price_type='low'
            )     

            ema_7_close = indicator_tools.get_last_ema_value(
                period=self.config.ema_trailing_period,
                price_type='close'
            )                                  
            
            ema_50_close = indicator_tools.get_last_ema_value(
                period=self.config.ema_50_period,
                price_type='close'
            )   

            ema_200_close = indicator_tools.get_last_ema_value(
                period=self.config.ema_200_period,
                price_type='close'
            )               


            # Calculate all distances in points
            points_distance_vs_20_high = abs(current_price - ema_20_high) / point
            points_distance_vs_20_low = abs(current_price - ema_20_low) / point
            points_distance_vs_7_ema_close = abs(current_price - ema_7_close) / point
            points_distance_vs_50_ema_close = abs(current_price - ema_50_close) / point
            points_distance_vs_200_ema_close = abs(current_price - ema_200_close) / point


            # Calculate Candle Ranges
            candle_1h_range = indicator_tools.calculate_candle_range(self.config.symbol,mt5.TIMEFRAME_H1)
            candle_4h_range = indicator_tools.calculate_candle_range(self.config.symbol,mt5.TIMEFRAME_H4)

            print(f"{datetime.now()}")
            self.config.display()
            print(f"\n\nCurrent Price:  {current_price}")
            

            print("\n")
            print(f"=============================================")
            print(f"Indicators")
            print(f"=============================================")
            print(f"Symbol:          {self.config.symbol}")
            print(f"20 EMA High:     {ema_20_high}")
            print(f"20 EMA Low:      {ema_20_low}")
            print(f"7 EMA Close:     {ema_7_close}")
            print(f"50 EMA Close:    {ema_50_close}")
            print(f"200 EMA Close:   {ema_200_close}")
            
            print("\n")
            print(f"=============================================")
            print(f"Metrics")
            print(f"=============================================")            
            print(f"Distance vs 7 EMA Close:      {points_distance_vs_7_ema_close:.2f} Points")
            print(f"Distance vs 20 EMA High:      {points_distance_vs_20_high:.2f} Points")
            print(f"Distance vs 20 EMA Low:       {points_distance_vs_20_low:.2f} Points")
            print(f"Distance vs 50 EMA Close:     {points_distance_vs_50_ema_close:.2f} Points")
            print(f"Distance vs 200 EMA Close:    {points_distance_vs_200_ema_close:.2f} Points")
            print(f"H1 Candle Range:              {candle_1h_range} Points")
            print(f"H4 Candle Range:              {candle_4h_range} Points")


            print("\n")
            

            # Identifying Trend
            if current_price > ema_20_low and ema_20_low > ema_50_close and ema_50_close > ema_200_close:
                trend = 'bullish 🟢'
            elif current_price < ema_20_high and ema_20_high < ema_50_close and ema_50_close < ema_200_close:    
                trend = 'bearish 🟡'
            else:
                trend = 'consolidation 🔵'    

              



            # Candle Range Volatility
            if candle_1h_range <= self.config.max_candle_range_1h_allowed:
                h1_within_range = True
                candle_1h_range_status = 'Allowed 🟢'
            else:
                h1_within_range = False    
                candle_1h_range_status = 'Not Allowed 🔴'


            if candle_4h_range <= self.config.max_candle_range_4h_allowed:
                h4_within_range = True
                candle_4h_range_status = 'Allowed 🟢'
            else:
                h4_within_range = False    
                candle_4h_range_status = 'Not Allowed 🔴'                


            print(f"Trend: {trend}")
            print(f"H1 Candle Range Tradeable: {candle_1h_range_status}")  
            print(f"H4 Candle Range Tradeable: {candle_4h_range_status}\n")     

            
            # The threshold is now a fixed point value, no need to multiply by point
            distance_threshold_in_points = self.config.ema_20_period_distance_threshold
           


            if trend == 'bullish 🟢' and points_distance_vs_20_low <= distance_threshold_in_points and h1_within_range and h4_within_range:
                print("Buying!")
                signal = 'buy'
                log_info("Bullish signal and price is close to 20 EMA Low. Placing BUY order.")
                self.execute_trade(mt5.ORDER_TYPE_BUY)                
            elif trend == 'bearish 🟡' and points_distance_vs_20_high <= distance_threshold_in_points and h1_within_range and h4_within_range:
                print(f"Selling! {self.config.volume}")
                signal = 'sell'
                log_info("Bearish signal and price is close to 20 EMA High. Placing SELL order.")
                self.execute_trade(mt5.ORDER_TYPE_SELL)                
            else:
                # print("Hold!")
                signal = 'hold'
                if trend == 'bullish 🟢':
                    log_info(f"Signal: {signal}")
                    log_info(f"No valid trading signal detected.")
                    log_info(f"Bullish trend but price's distance is too far from 20 EMA Low ({points_distance_vs_20_low:.2f} points)")
                    if not h1_within_range:
                        log_info(f"1H candle range {candle_1h_range} outide the treshold {self.config.max_candle_range_1h_allowed}. Not tradeable")
                    if not h4_within_range:
                        log_info(f"1H candle range {candle_4h_range} outide the treshold {self.config.max_candle_range_4h_allowed}. Not tradeable")                        
                elif trend == 'bearish 🟡':
                    log_info(f"Signal: {signal}")
                    log_info(f"No valid trading signal detected.")
                    log_info(f"Bearish trend but price's distance is too far from 20 EMA High ({points_distance_vs_20_high:.2f} points).")
                    if not h1_within_range:
                        log_info(f"1H candle range {candle_1h_range} outide the treshold {self.config.max_candle_range_1h_allowed}. Not tradeable")
                    if not h4_within_range:
                        log_info(f"1H candle range {candle_4h_range} outide the treshold {self.config.max_candle_range_4h_allowed}. Not tradeable")                         
                else:
                    log_info(f"Signal: {signal}")
                    log_info("No clear trend. Potential consolidation or reversal.")
                

            log_info("Waiting for the next loop...")




#-------------------------------------
# Main Entry Point
#-------------------------------------

def start_strategy():
    """Main function to start the bot."""

    production_status = "LIVE" 
    filename = os.path.basename(__file__)
    description = '1R M1 Average Zone Trading'
    


    log_info("Initializing Strategy 07 System.")
    
    # 1. Define configuration settings, can be from env variables
    config_settings = TradingConfig(
        symbol="GOLDm#",
        filename=filename,
        strategy_id=40 if production_status == 'DEMO' else 7, # if live
        volume=float(0.01) if production_status == 'DEMO' else 0.1, # if live
        deviation=20,
        sl_points=150,
        tp_points=300,
        trailing_activation_points=100, # (3500 = 2x ave. candle range in M1) 2000 points or $0.2 profit | 10 = 1000, 20 = 2000
        trailing_stop_distance=40,
        ema_trailing_period=7,
        ema_20_period_high=20,
        ema_20_period_low=20,
        ema_20_period_distance_threshold=70,
        ema_50_period=50,
        ema_200_period=200,
        max_candle_range_1h_allowed=1100,
        max_candle_range_4h_allowed=1800         
    )

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

    # 3. Instantiate and start the position manager thread
    position_open_event = threading.Event()
    position_manager = PositionManager(config=config_settings, mt5_manager=mt5_manager, position_open_event=position_open_event)
    position_manager.daemon = True # Allows the thread to exit when the main program exits
    position_manager.start()

    # 4. Instantiate the strategy and run it
    my_strategy = M1AverageZone(config=config_settings, mt5_manager=mt5_manager, position_open_event=position_open_event)
    try:
        my_strategy.run()
    except KeyboardInterrupt:
        log_warning("Strategy interrupted by user. Shutting down.")
    finally:
        # 5. Shutdown MT5 connection and stop the position manager
        position_manager.stop()
        mt5.shutdown()
        log_success("MetaTrader5 shutdown.")


if __name__ == "__main__":        
     # 2. Display account info   
    start_strategy()