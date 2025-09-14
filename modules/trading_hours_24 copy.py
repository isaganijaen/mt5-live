# Version: 1.2
import time
from datetime import timedelta, datetime
from rich.console import Console
from rich.panel import Panel
from rich import box

console = Console()

def is_trading_hours():
    # This runs 24/7
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
        f"[bold red]\n\n 🚀 We Are Currently Running 24/7[/bold red]\n\n",
        
        title="⏱️  TRADING HOUR",
        border_style="bright_red",
        box=box.DOUBLE
        )
    console.print(trading_hour_panel)

