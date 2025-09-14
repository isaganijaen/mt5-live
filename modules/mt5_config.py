# modules/mt5_config.py
import os
from rich.table import Table
from rich import box
from rich.console import Console

console = Console()

class TradingConfig:
    def __init__(self, symbol, strategy_id, volume, deviation,  
                 sl_points, tp_points, trailing_activation_points, trailing_stop_distance,
                 ema_trailing_period,
                 ema_20_period_high,ema_20_period_low,ema_20_period_distance_threshold,ema_50_period,ema_200_period,max_candle_range_1h_allowed,max_candle_range_4h_allowed):

        self.symbol = symbol
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
        self.ema_trailing_period = ema_trailing_period
        self.ema_20_period_high = ema_20_period_high
        self.ema_20_period_low = ema_20_period_low
        self.ema_20_period_distance_threshold = ema_20_period_distance_threshold
        self.ema_50_period = ema_50_period
        self.ema_200_period = ema_200_period
        self.max_candle_range_1h_allowed = max_candle_range_1h_allowed
        self.max_candle_range_4h_allowed = max_candle_range_4h_allowed

    def display(self):
        """Displays the configuration in a structured table."""
        config_table = Table(title="⚙️ Trading Configuration", box=box.ROUNDED, show_header=True)
        config_table.add_column("Setting", style="cyan", width=20)
        config_table.add_column("Value", style="green", width=15)
        config_table.add_column("Description", style="dim")
        
        config_table.add_row("Trading Symbol", self.symbol, "Primary trading instrument")
        config_table.add_row("Strategy ID", str(self.strategy_id), "Unique identifier for the strategy")
        # config_table.add_row("Risk Per Trade", f"{self.risk_percent}%", "Percentage of account risked")
        config_table.add_row("Stop Loss", f"{self.sl_points} points", "Fixed stop loss distance")
        config_table.add_row("Take Profit", f"{self.tp_points} points", "Enhanced take profit target")
        config_table.add_row("Trailing Stop", f"{self.trailing_stop_distance} pts", "Distance for trailing stop")
        config_table.add_row("Trail Activation", f"{self.trailing_activation_points} pts", "Profit needed to activate trailing")
        config_table.add_row("Fast Period EMA Low",f"{self.ema_20_period_low}","Buy Zone")
        config_table.add_row("Fast Period EMA High",f"{self.ema_20_period_high}","Sell Zone")
        config_table.add_row("Trail Indicator EMA",f"{self.ema_trailing_period}","EMA Trailing Indicator (Close)")
        config_table.add_row("Price Distance Tresh",f"{self.ema_20_period_distance_threshold}","Minimum Price Distance Threshold vs 20 EMA")
        config_table.add_row("Medium Period EMA",f"{self.ema_50_period}","Consolidation Filter (close)")
        config_table.add_row("Slow Period EMA",f"{self.ema_200_period}","Major Trend Indicator (Close)")
        config_table.add_row("1H Candle Range",f"{self.max_candle_range_1h_allowed}","Max. Alowed 1 Hour Candle Range")
        config_table.add_row("4H Candle Range",f"{self.max_candle_range_4h_allowed}","Max. Alowed 4 Hour Candle Range")

        
        console.print(config_table)