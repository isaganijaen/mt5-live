# Version: 1.2
import time
from datetime import timedelta, datetime
from rich.console import Console

console = Console()

def is_trading_hours():
    now = datetime.now()
    current_day = now.strftime("%a")
    current_hour = now.hour
    current_minute = now.minute

    # Trading Hours:
    # Mon: 20:00 - Tue: 12:59
    # Tue: 20:00 - Wed: 12:59
    # Wed: 20:00 - Thu: 12:59
    # Thu: 20:00 - Fri: 12:59
    # Fri: 20:00 - Sat: 05:30

    if current_day == "Sat":
        # Saturday exception: runs only until 5:30 AM
        if current_hour < 5 or (current_hour == 5 and current_minute <= 30):
            return True
        else:
            return False
    elif current_day == "Sun":
        # Sunday: Trading starts at 20:00
        if current_hour >= 18:
            return True
        else:
            return False
    else:
        # Weekdays (Mon-Fri):
        # From 20:00 to 23:59 (current day)
        # From 00:00 to 12:59 (next day)
        if (current_hour >= 10) or \
           (current_hour >= 0 and (current_hour < 12 or (current_hour == 12 and current_minute <= 59))):
            return True
        else:
            return False

# console.log(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
# console.log(datetime.now().strftime("%a"))

# if is_trading_hour():
#     console.log("It's within trading hours.")
# else:
#     console.log("It's outside trading hours.")

