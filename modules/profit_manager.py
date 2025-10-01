import MetaTrader5 as mt5
import time
import threading
from modules.utilities import log_success, log_error, log_info
from modules.mt5_config import TradingConfig
from modules.mt5_manager import MT5Manager
from rich.console import Console

console = Console()

class TakeProfitMonitor(threading.Thread):
    def __init__(self, config: TradingConfig, mt5_manager: MT5Manager, position_open_event: threading.Event):
        """
        Initializes the TakeProfitMonitor thread.

        Args:
            config (TradingConfig): The trading configuration settings.
            mt5_manager (MT5Manager): The MT5 connection manager.
            position_open_event (threading.Event): An event to signal new open positions.
        """
        super().__init__()
        self.config = config
        self.mt5_manager = mt5_manager
        self.position_open_event = position_open_event
        self.is_running = True

    def run(self):
        """
        The main loop for the take-profit monitoring thread.
        It continuously checks for open positions and closes them if the target is reached.
        """
        log_info("Take Profit Monitor thread started.")
        while self.is_running:
            positions = mt5.positions_get(symbol=self.config.symbol)
            
            # Check for existing positions with the strategy's magic ID
            if not positions or not any(p.magic == self.config.strategy_id for p in positions):
                # No relevant position open, wait for the signal from the main thread
                log_info("No open positions found. Take Profit Monitor is sleeping.")
                self.position_open_event.clear()
                self.position_open_event.wait()
                log_info("Take Profit Monitor woken up!")
                continue

            for position in positions:
                if position.magic == self.config.strategy_id:
                    self.monitor_and_close(position)
            
            # Sleep for a short period to prevent excessive API calls
            time.sleep(5)

    def monitor_and_close(self, position):
        """
        Monitors an individual open position and closes it if the take profit price is hit.
        
        Args:
            position (mt5.Position): The open position object.
        """
        symbol_info_tick = mt5.symbol_info_tick(self.config.symbol)
        if symbol_info_tick is None:
            log_error(f"Failed to get tick data for {self.config.symbol}")
            return
            
        current_price = symbol_info_tick.bid if position.type == mt5.ORDER_TYPE_SELL else symbol_info_tick.ask
        
        # Check if the take profit has been hit
        if (position.type == mt5.ORDER_TYPE_BUY and current_price >= position.tp) or \
           (position.type == mt5.ORDER_TYPE_SELL and current_price <= position.tp):
            log_success(f"Take profit hit for position {position.ticket}! Current Price: {current_price:.5f}, Target Price: {position.tp:.5f}")
            self.close_position(position)
        else:
            log_info(f"Position {position.ticket}: Price {current_price:.5f} is not yet at target {position.tp:.5f}. Monitoring...")

    def close_position(self, position):
        """
        Sends a request to close the specified position.
        
        Args:
            position (mt5.Position): The open position object to be closed.
        """
        # Get the current tick data to determine the correct closing price.
        tick = mt5.symbol_info_tick(self.config.symbol)
        if tick is None:
            log_error(f"Failed to get tick data for {self.config.symbol}")
            return
            
        # Determine the closing price and order type based on the position type.
        if position.type == mt5.ORDER_TYPE_BUY:
            close_price = mt5.symbol_info_tick(self.config.symbol).bid 
            close_type = mt5.ORDER_TYPE_SELL
        elif position.type == mt5.ORDER_TYPE_SELL:
            close_price = mt5.symbol_info_tick(self.config.symbol).ask
            close_type = mt5.ORDER_TYPE_BUY
        else:
            log_error(f"Unknown position type: {position.type}")
            return

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "position": position.ticket,
            "symbol": position.symbol,
            "volume": position.volume,
            "type": close_type,
            "price": close_price,
            "deviation": 10,
            "magic": self.config.strategy_id,
            "comment": "Take Profit Close",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }

        result = mt5.order_send(request)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            log_error(f"Failed to close position {position.ticket}, error code: {result.retcode}")
        else:
            log_success(f"Position {position.ticket} successfully closed.")

    def stop(self):
        """
        Stops the take-profit monitor thread gracefully.
        """
        log_info("Stopping Take Profit Monitor thread.")
        self.is_running = False
        self.position_open_event.set() # Wake up the thread if it's sleeping