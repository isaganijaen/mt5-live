# original modules/mt5_config.py (can be called mt5_config_v1_0_0.py)
import os
from rich.table import Table
from rich import box
from rich.console import Console

console = Console()

class TradingConfig:
    def __init__(self,  symbol, filename, strategy_id, volume, deviation,  
                 sl_points, tp_points, trailing_activation_points, trailing_stop_distance, entry_guide,
                 trailing_period, 
                 ema_resistance,ema_support,support_resistance_distance_threshold,
                 momentum_consolidation_filter,consolidation_filter,long_term_trend,max_candle_range_1h_allowed,max_candle_range_4h_allowed):

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
        self.entry_guide = entry_guide
        self.trailing_activation_points = trailing_activation_points
        self.trailing_stop_distance = trailing_stop_distance

        # Indicators
        self.trailing_period = trailing_period
        self.ema_resistance = ema_resistance
        self.ema_support = ema_support
        self.support_resistance_distance_threshold = support_resistance_distance_threshold
        self.momentum_consolidation_filter = momentum_consolidation_filter
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
        config_table.add_row("Volume", f"{self.volume}", "Volume")
        config_table.add_row("Stop Loss", f"{self.sl_points} pts", "Fixed stop loss distance")
        config_table.add_row("Take Profit", f"{self.tp_points} pts", "Enhanced take profit target")
        config_table.add_row("Entry Zone",f"{self.support_resistance_distance_threshold} pts","Minimum Price Distance vs S/R")
        config_table.add_row("Support",f"{self.ema_support}","Buy Zone (EMA Low)")
        config_table.add_row("Resistance",f"{self.ema_resistance}","Sell Zone (EMA High)")
        config_table.add_row("Entry Guide",f"{self.entry_guide}","Entry Guide (between S/R)")
        config_table.add_row("Trail Guide",f"{self.trailing_period}","Trailing Indicator (EMA Close)")
        config_table.add_row("Trail Activation", f"{self.trailing_activation_points} pts", "Trailing mechanism trigger points")    
        config_table.add_row("Trailing Stop", f"{self.trailing_stop_distance} pts", "Trailing stop distance")

        config_table.add_row("Momentum Consolidation Filter",f"{self.momentum_consolidation_filter}","Momentum Consolidation Filter (EMA close)")     
        config_table.add_row("Consolidation Filter",f"{self.consolidation_filter}","Consolidation Filter (EMA close)")
        config_table.add_row("Long Term Trend",f"{self.long_term_trend}","Long Term Trend (EMA Close)")
        config_table.add_row("1H Candle Range",f"{self.max_candle_range_1h_allowed}","1H Overbought/Oversold Threshold")
        config_table.add_row("4H Candle Range",f"{self.max_candle_range_4h_allowed}","4H Overbought/Oversold Threshold")

        
        console.print(config_table)