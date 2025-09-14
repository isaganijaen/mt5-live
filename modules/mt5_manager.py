# modules/mt5_manager.py
import MetaTrader5 as mt5
import time
from rich.table import Table
from rich import box
from rich.console import Console

# You'll need a utility file for these, or define them here for simplicity
def log_success(message):
    console.print(f"[bold green]SUCCESS: {message}[/bold green]")
def log_error(message):
    console.print(f"[bold red]ERROR: {message}[/bold red]")
def log_warning(message):
    console.print(f"[bold yellow]WARNING: {message}[/bold yellow]")
def log_info(message):
    console.print(f"[bold blue]INFO: {message}[/bold blue]")

console = Console()

class MT5Manager:
    def __init__(self, login=None, password=None, server=None, max_attempts=5):
        self.login = login
        self.password = password
        self.server = server
        self.max_attempts = max_attempts
        self.mt5_connected = False
        self.connection_attempts = 0

    def connect(self):
        """Initializes connection to the MT5 terminal with retry logic."""
        if self.mt5_connected:
            return True

        if self.connection_attempts > 0:
            time.sleep(2 ** min(self.connection_attempts, 5))  # Exponential backoff

        try:
            log_info("Attempting to initialize MetaTrader 5...")
            if not mt5.initialize():
                self.connection_attempts += 1
                error_code = mt5.last_error()
                log_error(f"MT5 initialize() failed (attempt {self.connection_attempts}/{self.max_attempts}), error code = {error_code}")
                if self.connection_attempts >= self.max_attempts:
                    log_error(f"Max connection attempts ({self.max_attempts}) reached. Exiting.")
                    return False
                return False
            
            if self.login and self.password and self.server:
                authorized = mt5.login(int(self.login), password=self.password, server=self.server)
                if not authorized:
                    self.connection_attempts += 1
                    error_code = mt5.last_error()
                    log_error(f"Failed to connect to account {self.login} (attempt {self.connection_attempts}/{self.max_attempts}), error code: {error_code}")
                    if self.connection_attempts >= self.max_attempts:
                        log_error(f"Max connection attempts ({self.max_attempts}) reached. Exiting.")
                        return False
                    return False
                else:
                    log_success(f"Connected to MT5 account {self.login}")
                    self.connection_attempts = 0
            else:
                log_warning("MT5 account details not provided. Connecting without explicit login.")
            
            log_success(f"MetaTrader5 connected: Version {mt5.version()}")
            self.mt5_connected = True
            return True

        except Exception as e:
            self.connection_attempts += 1
            log_error(f"Exception during MT5 initialization (attempt {self.connection_attempts}/{self.max_attempts}): {e}")
            if self.connection_attempts >= self.max_attempts:
                log_error(f"Max connection attempts ({self.max_attempts}) reached. Exiting.")
                return False
            return False

    def get_account_info(self, account_type="Demo"):
        """Retrieves and displays current account balance and equity."""
        if not self.mt5_connected:
            log_error("MT5 is not connected. Cannot retrieve account info.")
            return None
        
        account_info = mt5.account_info()
        if account_info is None:
            log_error(f"Failed to get account info, error code = {mt5.last_error()}")
            return None
            
        table = Table(title="💰 Account Information", box=box.ROUNDED)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Account", f"{account_info.login}")
        table.add_row("Type", f"{account_type}")
        table.add_row("Balance", f"${account_info.balance:.2f}")
        table.add_row("Equity", f"${account_info.equity:.2f}")
        table.add_row("Margin", f"${account_info.margin:.2f}")
        table.add_row("Free Margin", f"${account_info.margin_free:.2f}")
        
        console.print(table)
        return account_info