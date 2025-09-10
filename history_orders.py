from datetime import datetime
import MetaTrader5 as mt5
import pandas as pd

pd.set_option('display.max_columns', 500)  # number of columns to be displayed
pd.set_option('display.width', 1500)  # max table width to display

# Display data on the MetaTrader 5 package
print("MetaTrader5 package author: ", mt5.__author__)
print("MetaTrader5 package version: ", mt5.__version__)
print()

# Establish connection to the MetaTrader 5 terminal
if not mt5.initialize():
    print("initialize() failed, error code =", mt5.last_error())
    quit()

# Get all history orders
# Set 'from_date' to a more recent, realistic date.
# For example, the beginning of the current year or a few years back.
# You might need to adjust this based on your broker's historical data availability.
from_date = datetime(2020, 1, 1) # Changed from 1970 to 2020 as a common practical starting point
to_date = datetime.now()

all_history_orders = mt5.history_orders_get(from_date, to_date)

if all_history_orders is None:
    print(f"No history orders found for the period from {from_date} to {to_date}, error code={mt5.last_error()}")
elif len(all_history_orders) > 0:
    print(f"Total history orders retrieved: {len(all_history_orders)}")

    # Display these orders as a table using pandas.DataFrame
    if all_history_orders:
        df = pd.DataFrame(list(all_history_orders), columns=all_history_orders[0]._asdict().keys())

        # Drop specified columns if they exist in the DataFrame
        columns_to_drop = ['time_expiration', 'type_time', 'state', 'position_by_id', 'reason', 'volume_current', 'price_stoplimit', 'sl', 'tp']
        existing_columns_to_drop = [col for col in columns_to_drop if col in df.columns]
        if existing_columns_to_drop:
            df.drop(columns=existing_columns_to_drop, axis=1, inplace=True)
        else:
            print("Warning: None of the specified columns to drop were found in the DataFrame.")

        # Convert timestamp columns to datetime
        if 'time_setup' in df.columns:
            df['time_setup'] = pd.to_datetime(df['time_setup'], unit='s')
        if 'time_done' in df.columns:
            df['time_done'] = pd.to_datetime(df['time_done'], unit='s')

        print("\nDataFrame of All History Orders:")
        print(df)
else:
    print("No history orders found for the specified period.")

# Shut down connection to the MetaTrader 5 terminal
mt5.shutdown()