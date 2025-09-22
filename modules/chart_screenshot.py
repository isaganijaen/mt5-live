#---------------------------------------
# Generate Screenshot of a chart
#---------------------------------------

import MetaTrader5 as mt5
import pandas as pd
import time
from datetime import timedelta, datetime, timezone
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
from colorama import Fore, Back, Style, init
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from mplfinance import plot as mpf_plot
import mplfinance as mpf
# from utilities import log_success, log_error, log_warning, log_info

from rich.console import Console
console = Console()

def log_success(message):
    console.print(f"[bold green]✅ {message}[/bold green]")

def log_error(message):
    console.print(f"[bold red]❌ {message}[/bold red]")

def log_warning(message):
    console.print(f"[bold yellow]⚠️  {message}[/bold yellow]")

def log_info(message):
    console.print(f"[bold blue]ℹ️  {message}[/bold blue]")

CHART_BARS_COUNT = 200  # Number of bars to include in chart
#SCREENSHOTS_DIR = "screenshots/GOLD/"

class screenshot:
    def __init__(self, SCREENSHOT_DIR):
        super().__init__()
        self.SCREENSHOT_DIR = SCREENSHOT_DIR
        
    def ensure_screenshots_directory(self):
        """Create screenshots directory if it doesn't exist"""
        if not os.path.exists(self.SCREENSHOT_DIR):
            os.makedirs(self.SCREENSHOT_DIR)
            log_info(f"Created screenshots directory: {self.SCREENSHOT_DIR}")        


    def create_trade_chart(self, df, signal_type, entry_price, sl_price, tp_price, 
                           position_ticket, deal_id, position_id, comment, filename, symbol,
                           sl_points, tp_points,strategy_id):
        """
        Create and save a chart showing the trade entry with EMAs and levels.
        
        Args:
            df: DataFrame with OHLC data and indicators
            signal_type: 'BUY' or 'SELL'
            entry_price: Trade entry price
            sl_price: Stop loss price
            tp_price: Take profit price
            position_ticket: Position ticket number
            deal_id: Deal ID
            position_id: Deal ID
            comment: Trade comment
            filename: Trade comment
            symbol: Symbol
            sl_points:
            tp_points:
            strategy_id:
        """
        self.df = df
        self.signal_type = signal_type
        self.entry_price = entry_price
        self.sl_price = sl_price
        self.tp_price = tp_price
        self.position_ticket = position_ticket
        self.deal_id = deal_id
        self.position_id = position_id
        self.comment = comment
        self.filename = filename
        self.symbol = symbol
        self.sl_points = sl_points
        self.tp_points = tp_points
        self.strategy_id = strategy_id
        # self.SCREENSHOTS_DIR="screenshots/GOLD/" 
        try:
            self.ensure_screenshots_directory()
            
            # Get the last 200 bars for the chart
            chart_df = df.tail(CHART_BARS_COUNT).copy()
            
            if len(chart_df) < 10:
                log_warning(f"Not enough data for chart generation: {len(chart_df)} bars")
                return
                
            # Calculate 200 EMA for the chart
            chart_df['ema_200'] = talib.EMA(df['close'], timeperiod=200).tail(CHART_BARS_COUNT)
            
            # Set up the chart data for mplfinance
            chart_df.set_index('time', inplace=True)
            
            # Create additional plots for EMAs
            apd = [
                mpf.make_addplot(chart_df['entry'], color='orange', width=1.5, label='Entry/Trailing Guide'),
                mpf.make_addplot(chart_df['resistance'], color='red', width=1.5, label='Resistance'),
                mpf.make_addplot(chart_df['support'], color='black', width=1.5, label='support'),
                mpf.make_addplot(chart_df['consolidation_filter'], color='blue', width=1.5, label='Consolidation Filter'),
                mpf.make_addplot(chart_df['long_term_trend'], color='blue', width=1.5, label='Long Term Trend')
            ]
            
            # Create horizontal lines for entry, SL, and TP
            hlines = {
                'hlines': [entry_price, sl_price, tp_price],
                'colors': ['green', 'red', 'blue'],
                'linestyle': '-',
                'linewidths': 2,
                'alpha': 0.8
            }
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
            #base_filename = os.path.splitext(filename)[0]  # Remove .py extension
            # _1_open for database then _2_close for the closing on other app.
            chart_filename = f"{strategy_id}_{position_ticket}_{deal_id}_{timestamp}_1_open.png"
            chart_path = os.path.join(self.SCREENSHOT_DIR, chart_filename)
            
            # Create the chart
            fig, axes = mpf.plot(
                chart_df,
                type='candle',
                style='charles',
                addplot=apd,
                hlines=hlines,
                volume=False,
                title=f'{self.symbol} - {signal_type} Entry at {entry_price:.2f}',
                ylabel='Price',
                ylabel_lower='',
                figsize=(16, 10),
                returnfig=True,
                savefig=chart_path
            )
            
            # Add custom legend and annotations
            ax = axes[0]
            
            # Add legend for EMAs
            from matplotlib.lines import Line2D
            legend_elements = [
                Line2D([0], [0], color='orange', lw=2, label='10 EMA'),
                Line2D([0], [0], color='blue', lw=2, label='50 EMA'), 
                Line2D([0], [0], color='red', lw=2, label='200 EMA'),
                Line2D([0], [0], color='green', lw=2, label=f'Entry: {entry_price:.2f}'),
                Line2D([0], [0], color='red', lw=2, label=f'SL: {sl_price:.2f}'),
                Line2D([0], [0], color='blue', lw=2, label=f'TP: {tp_price:.2f}')
            ]
            ax.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(0, 1))
            
            # Add trade details text box
            trade_info = f"""Trade Details:
    Type: {signal_type}
    Entry: {entry_price:.2f}
    SL: {sl_price:.2f} ({abs(entry_price - sl_price):.0f} points)
    TP: {tp_price:.2f} ({abs(tp_price - entry_price):.0f} points)
    R:R = 1:{self.tp_points/self.sl_points:.1f}
    Position: {position_ticket}
    Deal: {deal_id}
    Time: {timestamp}"""
            
            ax.text(0.02, 0.98, trade_info, transform=ax.transAxes, fontsize=9,
                    verticalalignment='top', horizontalalignment='left',
                    bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
            
            plt.tight_layout()
            plt.close(fig)  # Close to free memory
            
            log_info(f"📊 Trade chart saved: {chart_filename}")
            
        except Exception as e:
            log_error(f"Failed to create trade chart: {e}\n{traceback.format_exc()}")
