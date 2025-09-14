import MetaTrader5 as mt5
import pandas as pd 
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import datetime

# Global variable for MT5 initialization status
mt5_initialized = False

def initialize_mt5():
    global mt5_initialized
    if not mt5.initialize():
        messagebox.showerror("MT5 Error", "Failed to initialize MT5: {}".format(mt5.last_error()))
        mt5_initialized = False
        return False
    else:
        mt5_initialized = True
        return True

def deinitialize_mt5():
    global mt5_initialized
    if mt5_initialized:
        mt5.shutdown()
        mt5_initialized = False
        #

class MT5TradingApp:
    def __init__(self, master):
        self.master = master
        master.title("MT5 Trading Application")
        master.geometry("800x600")
        master.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.symbols = ["OTHER", "GOLD#", "BTCUSD#", "ETHUSD#", "EURUSD#", "GBPJPY#", "USDJPY#", "USDGBP#"]

        self.create_widgets()
        self.update_open_trades_thread = threading.Thread(target=self.update_open_trades_periodically, daemon=True)
        self.update_open_trades_thread.start()
        self.update_countdown_timer() # Start the countdown timer

    def create_widgets(self):
        # Countdown Timer Label
        self.countdown_label = ttk.Label(self.master, text="02:00", font=("Arial", 36))
        self.countdown_label.pack(pady=10)

        # Input Frame
        input_frame = ttk.LabelFrame(self.master, text="Place Order")
        input_frame.pack(padx=10, pady=10, fill="x")

        # Symbol Dropdown
        ttk.Label(input_frame, text="Symbol:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.symbol_var = tk.StringVar(self.master)
        self.symbol_var.set(self.symbols[1]) # Default to GOLD#
        self.symbol_dropdown = ttk.OptionMenu(input_frame, self.symbol_var, self.symbols[1], *self.symbols, command=self.on_symbol_select)
        self.symbol_dropdown.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        # Manual Symbol Entry
        self.manual_symbol_entry = ttk.Entry(input_frame)
        self.manual_symbol_entry.grid(row=0, column=2, padx=5, pady=5, sticky="ew")
        self.manual_symbol_entry.grid_remove() # Hide by default

        # Volume
        ttk.Label(input_frame, text="Volume:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.volume_entry = ttk.Entry(input_frame)
        self.volume_entry.insert(0, "0.01")
        self.volume_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        # Order Count
        ttk.Label(input_frame, text="Order Count:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.order_count_entry = ttk.Entry(input_frame)
        self.order_count_entry.insert(0, "1")
        self.order_count_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew")

        # SL (Stop Loss)
        ttk.Label(input_frame, text="SL (points):").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.sl_entry = ttk.Entry(input_frame)
        self.sl_entry.grid(row=3, column=1, padx=5, pady=5, sticky="ew")

        # TP (Take Profit)
        ttk.Label(input_frame, text="TP (points):").grid(row=4, column=0, padx=5, pady=5, sticky="w")
        self.tp_entry = ttk.Entry(input_frame)
        self.tp_entry.grid(row=4, column=1, padx=5, pady=5, sticky="ew")

        # Magic Number Input - Added for dynamic magic number
        ttk.Label(input_frame, text="Magic Number:").grid(row=5, column=0, padx=5, pady=5, sticky="w")
        self.magic_number_entry = ttk.Entry(input_frame)
        self.magic_number_entry.insert(0, "777") # Default value to match the original code
        self.magic_number_entry.grid(row=5, column=1, padx=5, pady=5, sticky="ew")
        
        # Buy/Sell Buttons
        button_frame = ttk.Frame(input_frame)
        button_frame.grid(row=6, column=0, columnspan=3, pady=10)
        ttk.Button(button_frame, text="BUY", command=lambda: self.place_order(mt5.ORDER_TYPE_BUY)).pack(side="left", padx=5)
        ttk.Button(button_frame, text="SELL", command=lambda: self.place_order(mt5.ORDER_TYPE_SELL)).pack(side="left", padx=5)
        ttk.Button(button_frame, text="CLOSE ALL TRADES", command=self.close_all_trades).pack(side="left", padx=5)

        # Open Trades Table
        self.trades_frame = ttk.LabelFrame(self.master, text="Open Trades")
        self.trades_frame.pack(padx=10, pady=10, fill="both", expand=True)

        self.trades_table = ttk.Treeview(self.trades_frame, columns=("close_action", "ticket", "symbol", "time", "type", "price", "sl", "tp", "volume"), show="headings")
        self.trades_table.heading("close_action", text="Close")
        self.trades_table.heading("ticket", text="Ticket")
        self.trades_table.heading("symbol", text="Symbol")
        self.trades_table.heading("time", text="Time")
        self.trades_table.heading("type", text="Type")
        self.trades_table.heading("price", text="Price")
        self.trades_table.heading("sl", text="S/L")
        self.trades_table.heading("tp", text="T/P")
        self.trades_table.heading("volume", text="Volume")

        self.trades_table.column("close_action", width=70, anchor="center")
        self.trades_table.column("ticket", width=80, anchor="center")
        self.trades_table.column("symbol", width=100, anchor="center")
        self.trades_table.column("time", width=150, anchor="center")
        self.trades_table.column("type", width=70, anchor="center")
        self.trades_table.column("price", width=100, anchor="center")
        self.trades_table.column("sl", width=80, anchor="center")
        self.trades_table.column("tp", width=80, anchor="center")
        self.trades_table.column("volume", width=70, anchor="center")

        self.trades_table.pack(fill="both", expand=True)

        # Add a scrollbar
        scrollbar = ttk.Scrollbar(self.trades_frame, orient="vertical", command=self.trades_table.yview)
        self.trades_table.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        self.trades_table.bind("<ButtonRelease-1>", self.on_trade_select)

    def on_symbol_select(self, event):
        if self.symbol_var.get() == "OTHER":
            self.manual_symbol_entry.grid()
        else:
            self.manual_symbol_entry.grid_remove()

    def get_current_symbol(self):
        if self.symbol_var.get() == "OTHER":
            return self.manual_symbol_entry.get().strip()
        else:
            return self.symbol_var.get()

    def place_order(self, order_type):
        if not mt5_initialized:
            messagebox.showerror("MT5 Error", "MT5 is not initialized.")
            return

        symbol = self.get_current_symbol()
        if not symbol:
            messagebox.showerror("Input Error", "Please enter a symbol.")
            return

        try:
            volume = float(self.volume_entry.get())
            order_count = int(self.order_count_entry.get())
            # Get the dynamic magic number from the new input box
            magic_number = int(self.magic_number_entry.get())
        except ValueError:
            messagebox.showerror("Input Error", "Volume, Order Count, and Magic Number must be numbers.")
            return

        if volume <= 0 or order_count <= 0:
            messagebox.showerror("Input Error", "Volume and Order Count must be positive numbers.")
            return

        point = mt5.symbol_info(symbol).point
        if point is None:
            messagebox.showerror("MT5 Error", f"Failed to get symbol info for {symbol}. Error: {mt5.last_error()}")
            return

        symbol_info_tick = mt5.symbol_info_tick(symbol)
        if symbol_info_tick is None:
            messagebox.showerror("MT5 Error", f"Failed to get tick info for {symbol}. Error: {mt5.last_error()}")
            return

        sl_points = self.sl_entry.get().strip()
        tp_points = self.tp_entry.get().strip()

        for i in range(order_count):
            symbol_info_tick = mt5.symbol_info_tick(symbol)
            if symbol_info_tick is None:
                messagebox.showerror("MT5 Error", f"Failed to get tick info for {symbol}. Error: {mt5.last_error()}")
                return

            current_price = symbol_info_tick.ask if order_type == mt5.ORDER_TYPE_BUY else symbol_info_tick.bid

            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": volume,
                "type": order_type,
                "price": current_price,
                "deviation": 10,
                "magic": magic_number, # Use the dynamic magic number
                "comment": "Python script order",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }

            if sl_points:
                try:
                    sl_points_val = float(sl_points)
                    if order_type == mt5.ORDER_TYPE_BUY:
                        request["sl"] = current_price - sl_points_val * point
                    else:
                        request["sl"] = current_price + sl_points_val * point
                except ValueError:
                    messagebox.showwarning("Input Warning", "Invalid SL value. SL will not be set for this order.")

            if tp_points:
                try:
                    tp_points_val = float(tp_points)
                    if order_type == mt5.ORDER_TYPE_BUY:
                        request["tp"] = current_price + tp_points_val * point
                    else:
                        request["tp"] = current_price - tp_points_val * point
                except ValueError:
                    messagebox.showwarning("Input Warning", "Invalid TP value. TP will not be set for this order.")

            result = mt5.order_send(request)
            if result is None:
                messagebox.showerror("MT5 Error", f"Order send failed for {symbol}. No response from MT5 terminal. Error: {mt5.last_error()}")
            elif result.retcode != mt5.TRADE_RETCODE_DONE:
                messagebox.showerror("MT5 Error", f"Order send failed for {symbol}, retcode={result.retcode}. Error: {mt5.last_error()}")
            self.update_open_trades()

    def close_all_trades(self):
        if not mt5_initialized:
            messagebox.showerror("MT5 Error", "MT5 is not initialized.")
            return

        open_positions = mt5.positions_get()
        if open_positions is None:
            messagebox.showerror("MT5 Error", f"Failed to get open positions. Error: {mt5.last_error()}")
            return
        if len(open_positions) == 0:
            # No messagebox.showinfo here as per requirement
            return

        for position in open_positions:
            self.close_single_trade(position.ticket, position.symbol, position.volume, "BUY" if position.type == mt5.ORDER_TYPE_BUY else "SELL")
        self.update_open_trades()

    def close_single_trade(self, ticket, symbol, volume, trade_type):
        if not mt5_initialized:
            messagebox.showerror("MT5 Error", "MT5 is not initialized.")
            return

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": volume,
            "type": mt5.ORDER_TYPE_SELL if trade_type == "BUY" else mt5.ORDER_TYPE_BUY,
            "position": ticket,
            "price": mt5.symbol_info_tick(symbol).bid if trade_type == "BUY" else mt5.symbol_info_tick(symbol).ask,
            "deviation": 10,
            "magic": 202306,
            "comment": "Close by Python script",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        result = mt5.order_send(request)
        if result is None:
            messagebox.showerror("MT5 Error", f"Failed to close trade {ticket}. No response from MT5 terminal. Error: {mt5.last_error()}")
        elif result.retcode != mt5.TRADE_RETCODE_DONE:
            messagebox.showerror("MT5 Error", f"Failed to close trade {ticket}. Error: {mt5.last_error()}")
        # No messagebox.showinfo here as per requirement
        self.update_open_trades()

    def update_open_trades(self):
        for item in self.trades_table.get_children():
            self.trades_table.delete(item)

        if not mt5_initialized:
            return

        positions = mt5.positions_get()
        if positions is None:
            # This can happen if MT5 is not connected or there's an issue fetching positions
            # Do not show an error messagebox repeatedly in a periodic update thread
            # Instead, log it or handle it silently if it's expected to be transient
            print(f"Failed to get positions for update. Error: {mt5.last_error()}")
            return

        for pos in positions:
            trade_type = "BUY" if pos.type == mt5.ORDER_TYPE_BUY else "SELL"
            self.trades_table.insert("", "end", values=(
                "Close", # Add "Close" text for the new column at the first index
                pos.ticket,
                pos.symbol,
                pd.to_datetime(pos.time, unit='s'),
                trade_type,
                pos.price_open,
                pos.sl,
                pos.tp,
                pos.volume
            ), iid=pos.ticket) # Use ticket as iid for easy lookup

    def update_open_trades_periodically(self):
        while True:
            # Use after() to schedule the update on the main Tkinter thread
            self.master.after(1000, self.update_open_trades)
            time.sleep(1)

    def update_countdown_timer(self):
        now = datetime.datetime.now()
        
        # Calculate seconds into the current minute
        seconds_into_minute = now.second
        
        # Calculate seconds into the current 2-minute cycle
        seconds_into_2min_cycle = now.minute % 2 * 60 + seconds_into_minute
        
        # Calculate remaining seconds in the current 2-minute cycle
        remaining_seconds = 120 - seconds_into_2min_cycle
        
        # If remaining_seconds is 0 or negative, it means we just passed a 2-minute mark,
        # so the next cycle starts now and we count down from 120 seconds.
        if remaining_seconds <= 0:
            remaining_seconds = 120 + remaining_seconds # Adjust for negative values if any

        minutes = remaining_seconds // 60
        seconds = remaining_seconds % 60
        
        self.countdown_label.config(text=f"{minutes:02d}:{seconds:02d}")
        self.master.after(1000, self.update_countdown_timer) # Update every second

    def on_trade_select(self, event):
        item = self.trades_table.identify_row(event.y)
        column = self.trades_table.identify_column(event.x)

        if item and column == "#1":  # Check if the click is on the "Close" column (index #1)
            values = self.trades_table.item(item, 'values')
            if not values:
                return

            ticket = int(values[1])
            symbol = values[2]
            volume = float(values[8]) # Ensure volume is float
            trade_type = values[4]

            self.close_single_trade(ticket, symbol, volume, trade_type)

    def on_closing(self):
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            deinitialize_mt5()
            self.master.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    if initialize_mt5():
        app = MT5TradingApp(root)
        root.mainloop()
    else:
        messagebox.showerror("Initialization Failed", "MT5 could not be initialized. Exiting application.")
        root.destroy()
