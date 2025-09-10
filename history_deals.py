import MetaTrader5 as mt5
from datetime import datetime
import pandas as pd

pd.set_option('display.max_columns', 500)  # number of columns to be displayed
pd.set_option('display.width', 1500)       # max table width to display

# Display data on the MetaTrader 5 package
print("MetaTrader5 package author: ", mt5.__author__)
print("MetaTrader5 package version: ", mt5.__version__)
print()

# Establish connection to the MetaTrader 5 terminal
if not mt5.initialize():
    print("initialize() failed, error code =", mt5.last_error())
    quit()

# Set a practical 'from_date' to avoid 'Invalid argument' errors.
# Adjust this date based on your broker's historical data availability.
# Starting from 2020-01-01 is a common practical choice.
from_date = datetime(2020, 1, 1)
to_date = datetime.now()

# Get ALL deals in history by removing 'group' and 'position' constraints.
# The function will now fetch all deals from 'from_date' to 'to_date'.
all_deals = mt5.history_deals_get(from_date, to_date)

if all_deals is None:
    print(f"No history deals found for the period from {from_date} to {to_date}, error code={mt5.last_error()}")
elif len(all_deals) > 0:
    print(f"Total history deals retrieved: {len(all_deals)}")

    # Display these deals as a table using pandas.DataFrame
    # Check if all_deals is not empty before creating DataFrame
    if all_deals:
        df = pd.DataFrame(list(all_deals), columns=all_deals[0]._asdict().keys())

        # Convert 'time' column to datetime objects
        if 'time' in df.columns:
            df['time'] = pd.to_datetime(df['time'], unit='s')
        
        print("\nDataFrame of All History Deals:")
        print(df)
else:
    print("No history deals found for the specified period.")

# Shut down connection to the MetaTrader 5 terminal
mt5.shutdown()