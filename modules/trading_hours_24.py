# Version: 1.2
import time
from datetime import timedelta, datetime
from rich.console import Console
from rich.panel import Panel
from rich import box

console = Console()

def is_trading_hours():
    now = datetime.now()
    current_day = now.strftime("%a")
    current_hour = now.hour
    current_minute = now.minute

    if current_day == "Sat":
    # Saturday exception: runs only until 5:30 AM
        if current_hour < 4 or (current_hour == 4 and current_minute <= 30):
            return True
        else:
            return False
    # This runs 24/7
    else:
        return True  


if is_trading_hours():
    trading_hour_panel = Panel(        
        f"[bold cyan]\n\n  We Are Currently Running 24/7[/bold cyan]\n\n",
        
        title="⏱️  TRADING HOUR",
        border_style="bright_green",
        box=box.DOUBLE
        )
    console.print(trading_hour_panel)
else:
    trading_hour_panel = Panel(        
        f"[bold cyan]\n\n 🚀 We Are Currently Running 24/7[/bold cyan]\n\n",
        
        title="⏱️  TRADING HOUR",
        border_style="bright_red",
        box=box.DOUBLE
        )
    console.print(trading_hour_panel)

