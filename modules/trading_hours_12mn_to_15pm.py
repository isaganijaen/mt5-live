# Version: 1.2 (Updated Logic)
import time
from datetime import timedelta, datetime
from rich.console import Console

console = Console()

def is_trading_hours():
    now = datetime.now()
    # %a returns abbreviated weekday name (Mon, Tue, etc.)
    current_day = now.strftime("%a") 
    current_hour = now.hour
    current_minute = now.minute

    # Trading Hours (as per your request):
    # Mon: 06:00 - 15:59
    # Tue-Fri: 00:00 - 15:59
    
    # The end time 15:59 is 3:59 PM.
    END_HOUR = 15
    END_MINUTE = 59

    if current_day == "Sat":
        # Saturday exception: runs only until 5:30 AM (retains original logic)
        if current_hour < 5 or (current_hour == 5 and current_minute <= 30):
            return True
        else:
            return False
    
    elif current_day == "Sun":
        # Sunday: Trading starts at 20:00 (retains original logic)
        if current_hour >= 20:
            return True
        else:
            return False
    
    elif current_day == "Mon":
        # Monday: 06:00 - 15:59
        START_HOUR = 6
        
        # Check if current time is on or after 06:00
        is_after_start = (current_hour > START_HOUR) or \
                         (current_hour == START_HOUR and current_minute >= 0)
        
        # Check if current time is on or before 15:59
        is_before_end = (current_hour < END_HOUR) or \
                        (current_hour == END_HOUR and current_minute <= END_MINUTE)
        
        return is_after_start and is_before_end

    elif current_day in ("Tue", "Wed", "Thu", "Fri"):
        # Tuesday to Friday: 00:00 - 15:59
        START_HOUR = 0
        
        # Check if current time is on or after 00:00 (always True as current_hour >= 0)
        is_after_start = True # Simpler than checking current_hour >= 0
        
        # Check if current time is on or before 15:59
        is_before_end = (current_hour < END_HOUR) or \
                        (current_hour == END_HOUR and current_minute <= END_MINUTE)

        return is_after_start and is_before_end
    
    # Fallback return (should ideally not be reached if all days are covered)
    return False 

# console.log(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
# console.log(datetime.now().strftime("%a"))

# if is_trading_hours(): # Corrected function name
#      console.log("It's within trading hours.")
# else:
#      console.log("It's outside trading hours.")