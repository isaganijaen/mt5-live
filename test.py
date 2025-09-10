import MetaTrader5 as mt5
from modules.trading_hours_24 import is_trading_hours


if not mt5.initialize():
    print("initialize() failed, error code =",mt5.last_error())
    mt5.shutdown()
    quit()
else:
    print("MT5 initialized successfully")
    mt5.shutdown()
    print("MT5 shutdown successfully")