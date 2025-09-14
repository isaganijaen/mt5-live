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
    # Mon: 02:00 - 18:00
    # Tue: 02:00 - 18:00
    # Wed: 02:00 - 18:00
    # Thu: 02:00 - 18:00
    # Fri: 02:00 - 18:00
    
    # Check for weekdays (Mon-Fri)
    if current_day in ["Mon", "Tue", "Wed", "Thu", "Fri"]:
        # The market is open from 2:00 AM to 6:00 PM
        if (current_hour > 2 or (current_hour == 2 and current_minute >= 0)) and \
           (current_hour < 18 or (current_hour == 18 and current_minute <= 0)):
            return True
        else:
            return False
    # Check for weekends (Sat, Sun)
    elif current_day in ["Sat", "Sun"]:
        return False
    else:
        # For any other case (shouldn't happen with standard day names)
        return False

# console.log(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
# console.log(datetime.now().strftime("%a"))

if is_trading_hours():
    show = """
    -------------------- TRADING HOURS -------------------
    IS WITHIN TRADING HOURS
    ------------------------------------------------------
"""
    console.log(show)
else:
    show = """
    -------------------- TRADING HOURS -------------------
    OUTSIDE TRADING HOURS
    ------------------------------------------------------
"""
    console.log(show)