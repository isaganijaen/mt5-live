# modules/mt5_config.py
import os
from rich.table import Table
from rich import box
from rich.console import Console

console = Console()

class TradingConfig:
    def __init__(self,  symbol, filename, strategy_id, volume, deviation,  
                 sl_points, tp_points, trailing_activation_points, trailing_stop_distance,
                 trailing_period,
                 ema_resistance,ema_support,support_resistance_distance_threshold,consolidation_filter,long_term_trend,max_candle_range_1h_allowed,max_candle_range_4h_allowed):

        self.symbol = symbol
        self.filename = filename
        self.strategy_id = strategy_id
        self.volume = volume
        self.deviation = deviation

        # Risk Management
        # self.risk_percent = risk_percent
        self.reward_ratio = round(tp_points / sl_points,2)

        # Trade Management
        self.sl_points = sl_points
        self.tp_points = tp_points
        self.trailing_activation_points = trailing_activation_points
        self.trailing_stop_distance = trailing_stop_distance

        # Indicators
        self.trailing_period = trailing_period
        self.ema_resistance = ema_resistance
        self.ema_support = ema_support
        self.support_resistance_distance_threshold = support_resistance_distance_threshold
        self.consolidation_filter = consolidation_filter
        self.long_term_trend = long_term_trend
        self.max_candle_range_1h_allowed = max_candle_range_1h_allowed
        self.max_candle_range_4h_allowed = max_candle_range_4h_allowed

    def display(self):
        """Displays the configuration in a structured table."""
        config_table = Table(title="⚙️ Trading Configuration", box=box.ROUNDED, show_header=True)
        config_table.add_column("Setting", style="cyan")
        config_table.add_column("Value", style="green")
        config_table.add_column("Description", style="dim")
        
        config_table.add_row("Trading Symbol", self.symbol, "Primary trading instrument")
        config_table.add_row("Filename", self.filename, "Filename")
        config_table.add_row("Strategy ID", str(self.strategy_id), "Unique identifier for the strategy")
        config_table.add_row("RRR", f"{self.reward_ratio}", "Risk to Reward Ratio")
        config_table.add_row("Volume", f"{self.volume}%", "Volume")
        config_table.add_row("Stop Loss", f"{self.sl_points} points", "Fixed stop loss distance")
        config_table.add_row("Take Profit", f"{self.tp_points} points", "Enhanced take profit target")
        config_table.add_row("Trailing Stop", f"{self.trailing_stop_distance} pts", "Distance for trailing stop")
        config_table.add_row("Trail Activation", f"{self.trailing_activation_points} pts", "Profit needed to activate trailing")
        config_table.add_row("Fast Period EMA Low",f"{self.ema_support}","Buy Zone")
        config_table.add_row("Fast Period EMA High",f"{self.ema_resistance}","Sell Zone")
        config_table.add_row("Trail Indicator EMA",f"{self.trailing_period}","EMA Trailing Indicator (Close)")
        config_table.add_row("Price Distance Tresh",f"{self.support_resistance_distance_threshold}","Minimum Price Distance Threshold vs 20 EMA")
        config_table.add_row("Medium Period EMA",f"{self.consolidation_filter}","Consolidation Filter (close)")
        config_table.add_row("Slow Period EMA",f"{self.long_term_trend}","Major Trend Indicator (Close)")
        config_table.add_row("1H Candle Range",f"{self.max_candle_range_1h_allowed}","Max. Alowed 1 Hour Candle Range")
        config_table.add_row("4H Candle Range",f"{self.max_candle_range_4h_allowed}","Max. Alowed 4 Hour Candle Range")

        
        console.print(config_table)