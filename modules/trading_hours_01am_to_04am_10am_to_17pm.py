# Version: 1.2
import time
from datetime import timedelta, datetime
from rich.console import Console

console = Console()

def is_trading_hours():
    """
    Checks if the current time falls within the specified trading hours.
    
    The trading hours are as follows:
    - Monday: 10:00 - 17:59
    - Tuesday to Friday: 01:00 - 04:59 and 10:00 - 17:59
    - Saturday: 01:00 - 04:30
    - Sunday: No trading
    
    Returns:
        bool: True if within trading hours, False otherwise.
    """
    now = datetime.now()
    current_day = now.strftime("%a")
    current_hour = now.hour
    current_minute = now.minute

    if current_day == "Mon":
        # Check Monday's trading hours: 10:00 to 17:59
        if current_hour >= 10 and current_hour < 18:
            return True
        else:
            return False
            
    elif current_day in ["Tue", "Wed", "Thu", "Fri"]:
        # Check Tuesday to Friday's trading hours:
        # First window: 01:00 to 04:59
        # Second window: 10:00 to 17:59
        if (current_hour >= 1 and current_hour < 5) or (current_hour >= 10 and current_hour < 18):
            return True
        else:
            return False
            
    elif current_day == "Sat":
        # Check Saturday's trading hours: 01:00 to 04:30
        if current_hour >= 1 and current_hour < 4:
            return True
        elif current_hour == 4 and current_minute <= 30:
            return True
        else:
            return False
            
    else:
        # For all other days (Sunday), no trading hours apply.
        return False