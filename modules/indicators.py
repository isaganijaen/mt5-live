import MetaTrader5 as mt5
import pandas as pd
import talib as ta
import numpy as np
from rich.console import Console


#-----------------------------------
# Utilities and Global Variables
#-----------------------------------
from modules.utilities import log_success, log_error, log_warning, log_info

console = Console()
class Indicators:
    """
    A utility class to calculate common technical indicators and
    provide analysis on price relationships.
    """
    def __init__(self, rates_df):
        """
        Initializes the Indicators class with a DataFrame of price rates.
        
        Args:
            rates_df (pd.DataFrame): DataFrame containing price data with 'close', 'high', etc.
        """
        self.rates = rates_df

    def calculate_ema(self, period, price_type='close'):
        """
        Calculates the Exponential Moving Average (EMA).
        
        Args:
            period (int): The period for the EMA calculation.
            price_type (str): The column to use for the calculation ('close', 'high', 'low').
            
        Returns:
            pd.Series: A Series containing the EMA values.
        """
        if price_type not in self.rates.columns:
            raise ValueError(f"Price type '{price_type}' not found in DataFrame.")
        
        return ta.EMA(self.rates[price_type], timeperiod=period)
    

    def calculate_sma(self, period, price_type='close'):
        """
        Calculates the Exponential Moving Average (SMA).
        
        Args:
            period (int): The period for the SNA calculation.
            price_type (str): The column to use for the calculation ('close', 'high', 'low').
            
        Returns:
            pd.Series: A Series containing the EMA values.
        """
        if price_type not in self.rates.columns:
            raise ValueError(f"Price type '{price_type}' not found in DataFrame.")
        
        return ta.SMA(self.rates[price_type], timeperiod=period)    
    

    def calculate_candle_range(self, symbol, timeframe):
        """
        Checks if the current open candle's range (High - Low) is within the specified limit.
        """

        if timeframe == mt5.TIMEFRAME_H1:
            timeframe_str = "H1"
        if timeframe == mt5.TIMEFRAME_H4:
            timeframe_str = "H4"     

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
            
            return candle_range_points


        except Exception as e:
            log_error(f"Exception during candle range check for {symbol} {timeframe_str}: {e}")
            return False  




    def get_last_ema_value(self, period, price_type='close'):
        """
        Gets the last calculated EMA value.
        """
        ema_series = self.calculate_ema(period, price_type)
        return ema_series.iloc[-1]
    

    def get_last_sma_value(self, period, price_type='close'):
        """
        Gets the last calculated SMA value.
        """
        sma_series = self.calculate_sma(period, price_type)
        return sma_series.iloc[-1]




    def get_distance_to_ema(self, period, price_type='close'):
        """
        Calculates the distance of the current price to the EMA in points.
        
        Returns:
            float: The distance in points.
        """
        current_price = self.rates['close'].iloc[-1]
        last_ema = self.get_last_ema_value(period, price_type)
        
        if np.isnan(last_ema):
            return np.nan
            
        distance = abs((current_price - last_ema)) * 10000 # Assuming 4-digit pairs
        return distance
    


    def get_distance_to_sma(self, period, price_type='close'):
        """
        Calculates the distance of the current price to the SMA in points.
        
        Returns:
            float: The distance in points.
        """
        current_price = self.rates['close'].iloc[-1]
        last_sma = self.get_last_sma_value(period, price_type)
        
        if np.isnan(last_sma):
            return np.nan
            
        distance = abs((current_price - last_sma)) * 10000 # Assuming 4-digit pairs
        return distance
    


    
    # def check_price_location(self, short_period, long_period, price_type='close'):
    #     return    
    

    def get_current_price(self):
        current_price = self.rates['close'].iloc[-1]
        return current_price
    
 

    def check_crossover(self, short_period, long_period, price_type='close'):
        """
        Checks for a bullish or bearish crossover between two EMAs.
        
        Args:
            short_period (int): Period for the faster EMA.
            long_period (int): Period for the slower EMA.
            
        Returns:
            str or None: "bullish" for a golden cross, "bearish" for a death cross, or None.
        """
        short_ema = self.calculate_ema(short_period, price_type)
        long_ema = self.calculate_ema(long_period, price_type)

        # Check for a cross-over in the last two periods
        if short_ema.iloc[-2] < long_ema.iloc[-2] and short_ema.iloc[-1] > long_ema.iloc[-1]:
            return "bullish"
        elif short_ema.iloc[-2] > long_ema.iloc[-2] and short_ema.iloc[-1] < long_ema.iloc[-1]:
            return "bearish"
        else:
            return None
