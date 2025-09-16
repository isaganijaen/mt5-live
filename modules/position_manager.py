# modules/position_manager.py
import MetaTrader5 as mt5
import time
import pandas as pd
import threading
from modules.utilities import log_success, log_error, log_info, log_warning
from modules.indicators import Indicators
from modules.mt5_config import TradingConfig
from modules.mt5_manager import MT5Manager
from rich.console import Console

console = Console()

class PositionManager(threading.Thread):
    def __init__(self, config: TradingConfig, mt5_manager: MT5Manager, position_open_event: threading.Event):
        super().__init__()
        self.config = config
        self.mt5_manager = mt5_manager
        self.position_open_event = position_open_event
        self.is_running = True

    def run(self):
        """
        The main loop for the position management thread.
        """
        log_info("Position Manager thread started.")
        while self.is_running:
            positions = mt5.positions_get(symbol=self.config.symbol)
            if not positions or not any(p.magic == self.config.strategy_id for p in positions):
                # No relevant position open, wait for the signal from the main thread
                log_info("No open positions found. Position Manager is sleeping.")
                self.position_open_event.clear()
                self.position_open_event.wait()
                log_info("Position Manager woken up!")
                continue

            for position in positions:
                if position.magic == self.config.strategy_id:
                    self.manage_position(position)
            
            # Sleep for a short period to prevent excessive API calls
            time.sleep(10)

    def manage_position(self, position):
        """
        Manages an individual open position by trailing the stop loss.
        """
        symbol_info = mt5.symbol_info(self.config.symbol)
        if symbol_info is None:
            log_error(f"Failed to get symbol info for {self.config.symbol}")
            return

        point = symbol_info.point
        current_profit_currency = position.profit # This is the profit in the account's currency, e.g., USD
        current_profit_points = 0
        
        # Calculate profit in points
        if position.type == mt5.ORDER_TYPE_BUY:
            current_price = mt5.symbol_info_tick(self.config.symbol).ask
            current_profit_points = (current_price - position.price_open) / point
        elif position.type == mt5.ORDER_TYPE_SELL:
            current_price = mt5.symbol_info_tick(self.config.symbol).bid
            current_profit_points = (position.price_open - current_price) / point

        log_info(f"Checking position {position.ticket}.")
        log_info(f"Current profit in currency: {current_profit_currency:.2f}")
        log_info(f"Activation Point: {self.config.trailing_activation_points} | Current profit in points: {current_profit_points:.2f} ")

        # Check if the profit in points is high enough to activate the trailing stop
        if current_profit_points >= self.config.trailing_activation_points:
            log_info(f"Current Profit Points: {current_profit_points:.2f} | Trailing Activation Points: {self.config.trailing_activation_points}")
            log_info("Trailing stop activation threshold reached. Activating trailing stop.")

            # The rest of the logic remains the same
            # Fetch data for EMA calculation
            rates = mt5.copy_rates_from_pos(self.config.symbol, mt5.TIMEFRAME_M1, 0, 1000)
            if rates is None:
                log_error(f"Failed to get rates for {self.config.symbol}")
                return
            rates_df = pd.DataFrame(rates)
            rates_df['time'] = pd.to_datetime(rates_df['time'], unit='s')
            
            indicator_tools = Indicators(rates_df)
            ema_value = indicator_tools.get_last_ema_value(self.config.trailing_period, 'close')
            log_info(f"Current {self.config.trailing_period} EMA value: {ema_value}")
            
            if pd.isna(ema_value):
                log_warning("EMA value is NaN. Skipping stop loss update.")
                return

            if position.type == mt5.ORDER_TYPE_BUY:
                new_sl = ema_value - (self.config.trailing_stop_distance * point)
                if new_sl > position.sl:
                    self.update_sl(position, new_sl)
            elif position.type == mt5.ORDER_TYPE_SELL:
                new_sl = ema_value + (self.config.trailing_stop_distance * point)
                if new_sl < position.sl:
                    self.update_sl(position, new_sl)

    def update_sl(self, position, new_sl):
        """
        Sends an order modification request to update the stop loss.
        """
        request = {
            "action": mt5.TRADE_ACTION_SLTP,
            "position": position.ticket,
            "sl": new_sl,
            "tp": position.tp,
            "magic": self.config.strategy_id,
            "comment": "Trailing SL"
        }
        result = mt5.order_send(request)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            log_error(f"Failed to modify SL for position {position.ticket}, error code: {result.retcode}")
        else:
            log_success(f"Stop loss updated for position {position.ticket} to {new_sl:.5f}")

    def stop(self):
        """
        Stops the position manager thread gracefully.
        """
        log_info("Stopping Position Manager thread.")
        self.is_running = False
        self.position_open_event.set() # Wake up the thread if it's sleeping