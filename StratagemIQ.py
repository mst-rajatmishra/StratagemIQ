import tkinter as tk
from tkinter import ttk, simpledialog, messagebox, scrolledtext
import json
from kiteconnect import KiteConnect
from PIL import Image, ImageTk
import threading
import time
import requests
import os
from datetime import datetime
import webbrowser
import ta
import numpy as np
import pandas as pd
from pandas import DataFrame

class StratagemIQ:
    def __init__(self, root):
        self.root = root
        self.root.title("StratagemIQ - Professional Trading Platform")
        self.root.geometry("1400x900")
        
        # Set application icon
        try:
            self.root.iconbitmap('icon.ico')
        except:
            pass

        # Define themes
        self.themes = {
            "dark": {
                "primary": "#1e3a8a",
                "secondary": "#2563eb",
                "accent": "#f97316",
                "background": "#0c1a32",
                "panel": "#1e293b",
                "text": "#e2e8f0",
                "light_text": "#94a3b8",
                "border": "#334155",
                "positive": "#10b981",
                "negative": "#ef4444",
                "header": "#0f172a"
            },
            "light": {
                "primary": "#3b82f6",
                "secondary": "#10b981",
                "accent": "#ef4444",
                "background": "#f8fafc",
                "panel": "#e2e8f0",
                "text": "#1e293b",
                "light_text": "#64748b",
                "border": "#cbd5e1",
                "positive": "#10b981",
                "negative": "#ef4444",
                "header": "#c7d2fe"
            }
        }
        self.current_theme = "dark"
        self.colors = self.themes[self.current_theme]

        # Initialize variables
        self.credentials_list = self.load_credentials_list()
        self.buy_kite_instances = []
        self.sell_kite_instances = []
        self.logo_photo = None
        self.search_entry = None
        self.suggestion_tree = None
        self.notebook = None
        self.stock_trees = []
        self.buy_sell_frame = None
        self.quantity_label = None
        self.quantity_entry = None
        self.remove_button = None
        self.add_account_button = None
        self.account_dropdown = None
        self.result_label = None
        self.stock_prices = {}
        self.subscribed_instruments = [[] for _ in range(10)]  # 10 wishlists
        self.status_var = tk.StringVar(value="Ready")
        self.selected_accounts = []
        self.transaction_log = []
        self.limit_price_entry = None
        self.wishlist_names = [f"Wishlist {i+1}" for i in range(10)]  # Default names
        
        # Strategy variables
        self.strategies = []
        self.active_strategies = []
        self.strategy_thread = None
        self.strategy_running = False
        self.historical_data = {}
        
        # Initialize KiteConnect instances
        for creds in self.credentials_list:
            try:
                buy_kite = KiteConnect(api_key=creds["api_key"])
                sell_kite = KiteConnect(api_key=creds["api_key"])
                buy_kite.set_access_token(creds["access_token"])
                sell_kite.set_access_token(creds["access_token"])
                self.buy_kite_instances.append(buy_kite)
                self.sell_kite_instances.append(sell_kite)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to initialize account {creds['username']}: {str(e)}")

        # Fetch all instruments from Kite API
        self.all_instruments = self.get_all_instruments()
        
        # Create widgets
        self.create_widgets()
        self.update_suggestions()
        self.load_subscribed_instruments()
        self.load_strategies()
        
        # Start price update thread
        self.update_thread = threading.Thread(target=self.update_stock_prices_thread, daemon=True)
        self.update_thread.start()
        
        # Start strategy thread
        self.strategy_thread = threading.Thread(target=self.strategy_execution_thread, daemon=True)
        self.strategy_thread.start()

    def create_widgets(self):
        # Create menu bar
        self.menubar = tk.Menu(self.root)
        self.root.config(menu=self.menubar)
        
        # Theme menu
        theme_menu = tk.Menu(self.menubar, tearoff=0)
        theme_menu.add_command(label="Dark Theme", command=lambda: self.change_theme("dark"))
        theme_menu.add_command(label="Light Theme", command=lambda: self.change_theme("light"))
        self.menubar.add_cascade(label="Themes", menu=theme_menu)
        
        # Create header frame
        self.header_frame = tk.Frame(self.root, bg=self.colors["header"], height=80)
        self.header_frame.pack(fill=tk.X, padx=0, pady=0)
        
        # Logo placeholder
        logo_frame = tk.Frame(self.header_frame, bg=self.colors["header"])
        logo_frame.pack(side=tk.LEFT, padx=20, pady=10)
        
        # Application title with modern font
        self.title_label = tk.Label(self.header_frame, text="STRATAGEMIQ", 
                              font=("Segoe UI", 24, "bold"), 
                              fg="white", bg=self.colors["header"])
        self.title_label.pack(side=tk.LEFT, padx=10, pady=10)
        
        # Tagline
        self.tagline_label = tk.Label(self.header_frame, text="Professional Trading Platform", 
                               font=("Segoe UI", 10), 
                               fg="#94a3b8", bg=self.colors["header"])
        self.tagline_label.pack(side=tk.LEFT, padx=0, pady=0)
        
        # Status bar
        self.status_bar = tk.Label(self.header_frame, textvariable=self.status_var, 
                            font=("Segoe UI", 10), 
                            fg="white", bg=self.colors["header"], anchor="e")
        self.status_bar.pack(side=tk.RIGHT, padx=20, pady=10)
        
        # Create main content frame
        self.main_frame = tk.Frame(self.root, bg=self.colors["background"])
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Left panel for account management
        self.left_panel = tk.Frame(self.main_frame, bg=self.colors["panel"], bd=0, relief=tk.FLAT,
                            highlightbackground=self.colors["border"], highlightthickness=1)
        self.left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 15), pady=5)
        
        # Account management section
        self.account_frame = tk.LabelFrame(self.left_panel, text="ACCOUNT MANAGEMENT", 
                                    font=("Segoe UI", 10, "bold"),
                                    fg=self.colors["light_text"], 
                                    bg=self.colors["panel"], padx=15, pady=15,
                                    labelanchor="n")
        self.account_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Form with modern styling
        form_frame = tk.Frame(self.account_frame, bg=self.colors["panel"])
        form_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Username
        tk.Label(form_frame, text="Username:", fg=self.colors["text"], 
               bg=self.colors["panel"], font=("Segoe UI", 9)).grid(row=0, column=0, sticky="w", pady=5)
        self.username_entry = ttk.Entry(form_frame, width=22, font=("Segoe UI", 9))
        self.username_entry.grid(row=0, column=1, sticky="ew", pady=5, padx=(0, 10))
        
        # API Key
        tk.Label(form_frame, text="API Key:", fg=self.colors["text"], 
               bg=self.colors["panel"], font=("Segoe UI", 9)).grid(row=1, column=0, sticky="w", pady=5)
        self.api_key_entry = ttk.Entry(form_frame, width=22, font=("Segoe UI", 9))
        self.api_key_entry.grid(row=1, column=1, sticky="ew", pady=5, padx=(0, 10))
        
        # API Secret
        tk.Label(form_frame, text="API Secret:", fg=self.colors["text"], 
               bg=self.colors["panel"], font=("Segoe UI", 9)).grid(row=2, column=0, sticky="w", pady=5)
        self.api_secret_entry = ttk.Entry(form_frame, width=22, show="*", font=("Segoe UI", 9))
        self.api_secret_entry.grid(row=2, column=1, sticky="ew", pady=5, padx=(0, 10))
        
        # Access Token
        tk.Label(form_frame, text="Access Token:", fg=self.colors["text"], 
               bg=self.colors["panel"], font=("Segoe UI", 9)).grid(row=3, column=0, sticky="w", pady=5)
        self.access_token_entry = ttk.Entry(form_frame, width=22, show="*", font=("Segoe UI", 9))
        self.access_token_entry.grid(row=3, column=1, sticky="ew", pady=5, padx=(0, 10))
        
        # Add Account button
        self.add_account_button = tk.Button(self.account_frame, text="Add Account", command=self.add_new_account,
                                          bg=self.colors["secondary"], fg="white", 
                                          font=("Segoe UI", 10, "bold"), 
                                          relief=tk.FLAT, padx=10, cursor="hand2")
        self.add_account_button.pack(fill=tk.X, pady=(10, 5), padx=5)
        
        # Separator
        ttk.Separator(self.account_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        
        # Account selection dropdown
        tk.Label(self.account_frame, text="Select Account:", fg=self.colors["text"], 
               bg=self.colors["panel"], font=("Segoe UI", 9)).pack(anchor="w", padx=5)
        
        self.account_dropdown = ttk.Combobox(self.account_frame, values=self.get_account_usernames(), 
                                           width=20, font=("Segoe UI", 9))
        self.account_dropdown.pack(fill=tk.X, padx=5, pady=5)
        self.account_dropdown.current(0) if self.account_dropdown['values'] else None
        
        # Change Access Token button
        self.change_access_token_button = tk.Button(self.account_frame, text="Update Access Token", 
                                                 command=self.change_access_token,
                                                 bg=self.colors["accent"], fg="white", 
                                                 font=("Segoe UI", 10, "bold"), 
                                                 relief=tk.FLAT, padx=10, cursor="hand2")
        self.change_access_token_button.pack(fill=tk.X, pady=5, padx=5)
        
        # Dashboard section
        self.dashboard_frame = tk.LabelFrame(self.left_panel, text="PORTFOLIO DASHBOARD", 
                                      font=("Segoe UI", 10, "bold"),
                                      fg=self.colors["light_text"], 
                                      bg=self.colors["panel"], padx=15, pady=15,
                                      labelanchor="n")
        self.dashboard_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Portfolio value
        tk.Label(self.dashboard_frame, text="Portfolio Value:", fg=self.colors["light_text"], 
               bg=self.colors["panel"], font=("Segoe UI", 9)).pack(anchor="w", pady=(0, 5))
        self.portfolio_value = tk.Label(self.dashboard_frame, text="₹0.00", 
                                      font=("Segoe UI", 16, "bold"), 
                                      fg=self.colors["positive"], bg=self.colors["panel"])
        self.portfolio_value.pack(anchor="w", pady=(0, 15))
        
        # Market status
        tk.Label(self.dashboard_frame, text="Market Status:", fg=self.colors["light_text"], 
               bg=self.colors["panel"], font=("Segoe UI", 9)).pack(anchor="w", pady=(0, 5))
        
        market_frame = tk.Frame(self.dashboard_frame, bg=self.colors["panel"])
        market_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.market_status = tk.Label(market_frame, text="Closed", 
                                    font=("Segoe UI", 10), 
                                    fg=self.colors["negative"], bg=self.colors["panel"])
        self.market_status.pack(side=tk.LEFT)
        
        # Market timings
        self.market_timings_label = tk.Label(market_frame, text="9:15 AM - 3:30 PM", fg=self.colors["light_text"], 
               bg=self.colors["panel"], font=("Segoe UI", 9))
        self.market_timings_label.pack(side=tk.RIGHT)
        
        # Right panel for trading
        self.right_panel = tk.Frame(self.main_frame, bg=self.colors["panel"], bd=0, relief=tk.FLAT,
                              highlightbackground=self.colors["border"], highlightthickness=1)
        self.right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(0, 0), pady=5)
        
        # Create notebook for wishlists
        self.style = ttk.Style()
        self.configure_styles()
        
        self.notebook = ttk.Notebook(self.right_panel)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create context menu for tab renaming
        self.tab_menu = tk.Menu(self.root, tearoff=0)
        self.tab_menu.add_command(label="Rename Tab", command=self.rename_tab)
        self.notebook.bind("<Button-3>", self.show_tab_menu)
        
        # Create 10 wishlist tabs
        self.stock_trees = []
        for i in range(10):
            wishlist_tab = ttk.Frame(self.notebook)
            self.notebook.add(wishlist_tab, text=self.wishlist_names[i])
            
            # Create treeview for stocks
            columns = ("Stock", "Price", "Change", "Volume", "Strategy")
            tree = ttk.Treeview(wishlist_tab, columns=columns, show="headings", height=12)
            
            # Configure columns
            tree.column("Stock", width=150, anchor=tk.W)
            tree.column("Price", width=100, anchor=tk.E)
            tree.column("Change", width=100, anchor=tk.E)
            tree.column("Volume", width=100, anchor=tk.E)
            tree.column("Strategy", width=150, anchor=tk.W)
            
            # Configure headings
            tree.heading("Stock", text="Stock")
            tree.heading("Price", text="Price (₹)")
            tree.heading("Change", text="Change (%)")
            tree.heading("Volume", text="Volume")
            tree.heading("Strategy", text="Strategy")
            
            # Style the treeview
            self.style.configure("Treeview", 
                           background=self.colors["panel"], 
                           fieldbackground=self.colors["panel"], 
                           foreground=self.colors["text"],
                           font=('Segoe UI', 9),
                           rowheight=25,
                           borderwidth=0)
            
            self.style.configure("Treeview.Heading", 
                           background=self.colors["primary"], 
                           foreground="white", 
                           font=("Segoe UI", 9, "bold"),
                           borderwidth=0)
            
            self.style.map("Treeview", 
                     background=[('selected', self.colors["secondary"])])
            
            # Add scrollbar
            scrollbar = ttk.Scrollbar(wishlist_tab, orient=tk.VERTICAL, command=tree.yview)
            tree.configure(yscroll=scrollbar.set)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            # Add right-click menu for strategy assignment
            tree.bind("<Button-3>", self.show_strategy_menu)
            
            self.stock_trees.append(tree)
        
        # Create strategy tab
        strategy_tab = ttk.Frame(self.notebook)
        self.notebook.add(strategy_tab, text="Strategies")
        
        # Strategy management frame
        strategy_frame = tk.Frame(strategy_tab, bg=self.colors["panel"])
        strategy_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Strategy list frame
        strategy_list_frame = tk.LabelFrame(strategy_frame, text="Trading Strategies", 
                                          font=("Segoe UI", 10, "bold"),
                                          fg=self.colors["light_text"], 
                                          bg=self.colors["panel"], padx=10, pady=10)
        strategy_list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Strategy treeview
        columns = ("ID", "Name", "Type", "Status", "Instruments")
        self.strategy_tree = ttk.Treeview(strategy_list_frame, columns=columns, show="headings", height=10)
        
        # Configure columns
        self.strategy_tree.column("ID", width=50, anchor=tk.W)
        self.strategy_tree.column("Name", width=150, anchor=tk.W)
        self.strategy_tree.column("Type", width=150, anchor=tk.W)
        self.strategy_tree.column("Status", width=100, anchor=tk.W)
        self.strategy_tree.column("Instruments", width=200, anchor=tk.W)
        
        # Configure headings
        self.strategy_tree.heading("ID", text="ID")
        self.strategy_tree.heading("Name", text="Name")
        self.strategy_tree.heading("Type", text="Type")
        self.strategy_tree.heading("Status", text="Status")
        self.strategy_tree.heading("Instruments", text="Instruments")
        
        # Style the treeview
        self.strategy_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Strategy controls
        strategy_controls = tk.Frame(strategy_list_frame, bg=self.colors["panel"])
        strategy_controls.pack(fill=tk.X, padx=5, pady=5)
        
        self.add_strategy_button = tk.Button(strategy_controls, text="Add Strategy", command=self.add_strategy,
                                           bg=self.colors["secondary"], fg="white", 
                                           font=("Segoe UI", 10, "bold"), 
                                           relief=tk.FLAT, padx=10, cursor="hand2")
        self.add_strategy_button.pack(side=tk.LEFT, padx=5)
        
        self.edit_strategy_button = tk.Button(strategy_controls, text="Edit Strategy", command=self.edit_strategy,
                                            bg=self.colors["secondary"], fg="white", 
                                            font=("Segoe UI", 10, "bold"), 
                                            relief=tk.FLAT, padx=10, cursor="hand2")
        self.edit_strategy_button.pack(side=tk.LEFT, padx=5)
        
        self.delete_strategy_button = tk.Button(strategy_controls, text="Delete Strategy", command=self.delete_strategy,
                                              bg=self.colors["accent"], fg="white", 
                                              font=("Segoe UI", 10, "bold"), 
                                              relief=tk.FLAT, padx=10, cursor="hand2")
        self.delete_strategy_button.pack(side=tk.LEFT, padx=5)
        
        self.toggle_strategy_button = tk.Button(strategy_controls, text="Enable/Disable", command=self.toggle_strategy,
                                              bg=self.colors["primary"], fg="white", 
                                              font=("Segoe UI", 10, "bold"), 
                                              relief=tk.FLAT, padx=10, cursor="hand2")
        self.toggle_strategy_button.pack(side=tk.LEFT, padx=5)
        
        # Strategy configuration frame
        config_frame = tk.LabelFrame(strategy_frame, text="Strategy Configuration", 
                                   font=("Segoe UI", 10, "bold"),
                                   fg=self.colors["light_text"], 
                                   bg=self.colors["panel"], padx=10, pady=10)
        config_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Strategy type selection
        tk.Label(config_frame, text="Strategy Type:", fg=self.colors["text"], 
               bg=self.colors["panel"], font=("Segoe UI", 9)).grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.strategy_type = ttk.Combobox(config_frame, values=["Moving Average Crossover", "RSI", "MACD"], 
                                        width=25, font=("Segoe UI", 9))
        self.strategy_type.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        self.strategy_type.current(0)
        self.strategy_type.bind("<<ComboboxSelected>>", self.update_strategy_config)
        
        # Strategy name
        tk.Label(config_frame, text="Strategy Name:", fg=self.colors["text"], 
               bg=self.colors["panel"], font=("Segoe UI", 9)).grid(row=0, column=2, padx=5, pady=5, sticky="e")
        self.strategy_name = ttk.Entry(config_frame, width=20, font=("Segoe UI", 9))
        self.strategy_name.grid(row=0, column=3, padx=5, pady=5, sticky="w")
        
        # Parameters frame
        self.parameters_frame = tk.Frame(config_frame, bg=self.colors["panel"])
        self.parameters_frame.grid(row=1, column=0, columnspan=4, padx=5, pady=5, sticky="we")
        
        # Default parameters
        self.create_ma_config()
        
        # Save strategy button
        self.save_strategy_button = tk.Button(config_frame, text="Save Strategy", command=self.save_strategy,
                                            bg=self.colors["secondary"], fg="white", 
                                            font=("Segoe UI", 10, "bold"), 
                                            relief=tk.FLAT, padx=10, cursor="hand2")
        self.save_strategy_button.grid(row=2, column=0, columnspan=4, pady=10)
        
        # Bottom panel for search and trading
        self.bottom_panel = tk.Frame(self.right_panel, bg=self.colors["panel"])
        self.bottom_panel.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # Search frame
        self.search_frame = tk.LabelFrame(self.bottom_panel, text="INSTRUMENT SEARCH", 
                                   font=("Segoe UI", 10, "bold"),
                                   fg=self.colors["light_text"], 
                                   bg=self.colors["panel"], padx=15, pady=15,
                                   labelanchor="n")
        self.search_frame.pack(fill=tk.X, padx=0, pady=0)
        
        # Search controls
        search_controls = tk.Frame(self.search_frame, bg=self.colors["panel"])
        search_controls.pack(fill=tk.X, padx=5, pady=5)
        
        # Search entry
        self.search_entry = ttk.Entry(search_controls, width=40, font=("Segoe UI", 10))
        self.search_entry.pack(side=tk.LEFT, padx=(0, 10), pady=5, fill=tk.X, expand=True)
        self.search_entry.bind('<KeyRelease>', self.update_suggestions)
        
        # Search button
        self.search_button = tk.Button(search_controls, text="Search", command=self.search_instruments,
                                bg=self.colors["secondary"], fg="white", 
                                font=("Segoe UI", 10, "bold"), 
                                relief=tk.FLAT, padx=15, cursor="hand2")
        self.search_button.pack(side=tk.LEFT, padx=(0, 10), pady=5)
        
        # Add/remove buttons
        button_frame = tk.Frame(search_controls, bg=self.colors["panel"])
        button_frame.pack(side=tk.LEFT, padx=10, pady=5)
        
        self.add_button = tk.Button(button_frame, text="Add to Wishlist", command=self.add_selected_to_wishlist,
                             bg=self.colors["secondary"], fg="white", 
                             font=("Segoe UI", 9, "bold"), 
                             relief=tk.FLAT, padx=10, cursor="hand2")
        self.add_button.pack(fill=tk.X, pady=2)
        
        self.remove_button = tk.Button(button_frame, text="Remove Selected", command=self.remove_from_wishlist,
                                     bg=self.colors["accent"], fg="white", 
                                     font=("Segoe UI", 9, "bold"), 
                                     relief=tk.FLAT, padx=10, cursor="hand2")
        self.remove_button.pack(fill=tk.X, pady=2)
        
        # Suggestion treeview frame
        tree_frame = tk.Frame(self.search_frame, bg=self.colors["panel"])
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create detailed suggestion treeview
        columns = ("Symbol", "Name", "Exchange", "Instrument Type")
        self.suggestion_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=4)
        
        # Configure columns
        self.suggestion_tree.column("Symbol", width=120, anchor=tk.W)
        self.suggestion_tree.column("Name", width=200, anchor=tk.W)
        self.suggestion_tree.column("Exchange", width=100, anchor=tk.W)
        self.suggestion_tree.column("Instrument Type", width=120, anchor=tk.W)
        
        # Configure headings
        self.suggestion_tree.heading("Symbol", text="Symbol")
        self.suggestion_tree.heading("Name", text="Name")
        self.suggestion_tree.heading("Exchange", text="Exchange")
        self.suggestion_tree.heading("Instrument Type", text="Instrument Type")
        
        # Style the treeview
        self.style.configure("Suggestion.Treeview", 
                       background=self.colors["panel"], 
                       fieldbackground=self.colors["panel"], 
                       foreground=self.colors["text"],
                       font=('Segoe UI', 9),
                       rowheight=25,
                       borderwidth=0)
        
        self.style.configure("Suggestion.Treeview.Heading", 
                       background=self.colors["primary"], 
                       foreground="white", 
                       font=("Segoe UI", 9, "bold"),
                       borderwidth=0)
        
        self.suggestion_tree.configure(style="Suggestion.Treeview")
        
        # Add scrollbar
        tree_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.suggestion_tree.yview)
        self.suggestion_tree.configure(yscroll=tree_scrollbar.set)
        tree_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.suggestion_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Bind double click to add to wishlist
        self.suggestion_tree.bind("<Double-1>", self.add_to_wishlist_from_tree)
        
        # Trading frame
        self.trade_frame = tk.LabelFrame(self.bottom_panel, text="EXECUTE TRADE", 
                                  font=("Segoe UI", 10, "bold"),
                                  fg=self.colors["light_text"], 
                                  bg=self.colors["panel"], padx=15, pady=15,
                                  labelanchor="n")
        self.trade_frame.pack(fill=tk.X, padx=0, pady=(10, 0))
        
        # Trading controls
        trade_controls = tk.Frame(self.trade_frame, bg=self.colors["panel"])
        trade_controls.pack(fill=tk.X, padx=5, pady=5)
        
        # Quantity entry
        self.quantity_label = tk.Label(trade_controls, text="Quantity:", fg=self.colors["text"], 
               bg=self.colors["panel"], font=("Segoe UI", 9))
        self.quantity_label.grid(row=0, column=0, padx=5, pady=5, sticky="e")
        
        self.quantity_entry = ttk.Entry(trade_controls, width=10, font=("Segoe UI", 9))
        self.quantity_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        self.quantity_entry.insert(0, "1")
        
        # Order type
        self.order_type_label = tk.Label(trade_controls, text="Order Type:", fg=self.colors["text"], 
               bg=self.colors["panel"], font=("Segoe UI", 9))
        self.order_type_label.grid(row=0, column=2, padx=5, pady=5, sticky="e")
        
        self.order_type = ttk.Combobox(trade_controls, values=["MARKET", "LIMIT"], 
                                     width=8, font=("Segoe UI", 9))
        self.order_type.grid(row=0, column=3, padx=5, pady=5, sticky="w")
        self.order_type.current(0)
        self.order_type.bind("<<ComboboxSelected>>", self.toggle_limit_price)
        
        # Limit price (initially hidden)
        self.limit_price_label = tk.Label(trade_controls, text="Limit Price:", 
                                        fg=self.colors["text"], 
                                        bg=self.colors["panel"], 
                                        font=("Segoe UI", 9))
        self.limit_price_entry = ttk.Entry(trade_controls, width=10, 
                                         font=("Segoe UI", 9))
        
        # Buy/Sell buttons
        self.buy_button = tk.Button(trade_controls, text="BUY", command=self.buy_stock,
                                   bg="#10b981", fg="white", 
                                   font=("Segoe UI", 10, "bold"), 
                                   width=8, padx=10, cursor="hand2",
                                   activebackground="#059669")
        self.buy_button.grid(row=0, column=6, padx=10, pady=5)
        
        self.sell_button = tk.Button(trade_controls, text="SELL", command=self.sell_stock,
                                    bg=self.colors["accent"], fg="white", 
                                    font=("Segoe UI", 10, "bold"), 
                                    width=8, padx=10, cursor="hand2",
                                    activebackground="#ea580c")
        self.sell_button.grid(row=0, column=7, padx=10, pady=5)
        
        # Add initial status message
        self.log_transaction("System initialized. Ready to trade.")
        
        # Update market status
        self.update_market_status()

    def show_tab_menu(self, event):
        """Show context menu for tab renaming"""
        tab_index = self.notebook.index(f"@{event.x},{event.y}")
        if tab_index >= 0:
            self.selected_tab_index = tab_index
            self.tab_menu.post(event.x_root, event.y_root)

    def rename_tab(self):
        """Rename the selected tab"""
        new_name = simpledialog.askstring("Rename Tab", 
                                         "Enter new name for this tab:",
                                         parent=self.root)
        if new_name:
            self.wishlist_names[self.selected_tab_index] = new_name
            self.notebook.tab(self.selected_tab_index, text=new_name)
            self.log_transaction(f"Renamed tab {self.selected_tab_index+1} to '{new_name}'")

    def show_strategy_menu(self, event):
        """Show context menu for strategy assignment"""
        # Identify which tree was clicked
        tree = event.widget
        item = tree.identify_row(event.y)
        
        if item:
            # Get the stock symbol
            stock = tree.item(item)["values"][0]
            
            # Create menu
            menu = tk.Menu(self.root, tearoff=0)
            menu.add_command(label="Assign Strategy", 
                            command=lambda: self.assign_strategy(tree, item))
            menu.add_command(label="Remove Strategy", 
                            command=lambda: self.remove_strategy(tree, item))
            menu.post(event.x_root, event.y_root)

    def assign_strategy(self, tree, item):
        """Assign a strategy to an instrument"""
        stock = tree.item(item)["values"][0]
        
        # Get available strategies
        strategy_names = [s["name"] for s in self.strategies]
        if not strategy_names:
            messagebox.showinfo("No Strategies", "Please create a strategy first")
            return
            
        # Create dialog to select strategy
        strategy_name = simpledialog.askstring("Assign Strategy", 
                                              f"Select strategy for {stock}:",
                                              parent=self.root,
                                              initialvalue=strategy_names[0])
        if strategy_name and strategy_name in strategy_names:
            # Update treeview
            values = list(tree.item(item)["values"])
            if len(values) < 5:  # Ensure we have strategy column
                values.append(strategy_name)
            else:
                values[4] = strategy_name
            tree.item(item, values=values)
            
            # Update strategy data
            for strategy in self.strategies:
                if strategy["name"] == strategy_name:
                    if stock not in strategy["instruments"]:
                        strategy["instruments"].append(stock)
                    break
                    
            self.save_strategies()
            self.update_strategy_tree()
            self.log_transaction(f"Assigned '{strategy_name}' to {stock}")

    def remove_strategy(self, tree, item):
        """Remove strategy from an instrument"""
        stock = tree.item(item)["values"][0]
        current_strategy = tree.item(item)["values"][4] if len(tree.item(item)["values"]) > 4 else ""
        
        if not current_strategy:
            messagebox.showinfo("No Strategy", "No strategy assigned to this instrument")
            return
            
        # Update treeview
        values = list(tree.item(item)["values"])
        if len(values) > 4:
            values[4] = ""
            tree.item(item, values=values)
            
        # Update strategy data
        for strategy in self.strategies:
            if stock in strategy["instruments"]:
                strategy["instruments"].remove(stock)
                
        self.save_strategies()
        self.update_strategy_tree()
        self.log_transaction(f"Removed strategy from {stock}")

    def create_ma_config(self):
        """Create configuration for Moving Average strategy"""
        # Clear existing widgets
        for widget in self.parameters_frame.winfo_children():
            widget.destroy()
        
        # Short MA period
        tk.Label(self.parameters_frame, text="Short MA Period:", fg=self.colors["text"], 
               bg=self.colors["panel"], font=("Segoe UI", 9)).grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.short_ma = ttk.Entry(self.parameters_frame, width=10, font=("Segoe UI", 9))
        self.short_ma.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        self.short_ma.insert(0, "20")
        
        # Long MA period
        tk.Label(self.parameters_frame, text="Long MA Period:", fg=self.colors["text"], 
               bg=self.colors["panel"], font=("Segoe UI", 9)).grid(row=0, column=2, padx=5, pady=5, sticky="e")
        self.long_ma = ttk.Entry(self.parameters_frame, width=10, font=("Segoe UI", 9))
        self.long_ma.grid(row=0, column=3, padx=5, pady=5, sticky="w")
        self.long_ma.insert(0, "50")

    def create_rsi_config(self):
        """Create configuration for RSI strategy"""
        # Clear existing widgets
        for widget in self.parameters_frame.winfo_children():
            widget.destroy()
        
        # RSI Period
        tk.Label(self.parameters_frame, text="RSI Period:", fg=self.colors["text"], 
               bg=self.colors["panel"], font=("Segoe UI", 9)).grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.rsi_period = ttk.Entry(self.parameters_frame, width=10, font=("Segoe UI", 9))
        self.rsi_period.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        self.rsi_period.insert(0, "14")
        
        # Overbought level
        tk.Label(self.parameters_frame, text="Overbought Level:", fg=self.colors["text"], 
               bg=self.colors["panel"], font=("Segoe UI", 9)).grid(row=0, column=2, padx=5, pady=5, sticky="e")
        self.overbought = ttk.Entry(self.parameters_frame, width=10, font=("Segoe UI", 9))
        self.overbought.grid(row=0, column=3, padx=5, pady=5, sticky="w")
        self.overbought.insert(0, "70")
        
        # Oversold level
        tk.Label(self.parameters_frame, text="Oversold Level:", fg=self.colors["text"], 
               bg=self.colors["panel"], font=("Segoe UI", 9)).grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.oversold = ttk.Entry(self.parameters_frame, width=10, font=("Segoe UI", 9))
        self.oversold.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        self.oversold.insert(0, "30")

    def create_macd_config(self):
        """Create configuration for MACD strategy"""
        # Clear existing widgets
        for widget in self.parameters_frame.winfo_children():
            widget.destroy()
        
        # Fast EMA
        tk.Label(self.parameters_frame, text="Fast EMA:", fg=self.colors["text"], 
               bg=self.colors["panel"], font=("Segoe UI", 9)).grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.fast_ema = ttk.Entry(self.parameters_frame, width=10, font=("Segoe UI", 9))
        self.fast_ema.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        self.fast_ema.insert(0, "12")
        
        # Slow EMA
        tk.Label(self.parameters_frame, text="Slow EMA:", fg=self.colors["text"], 
               bg=self.colors["panel"], font=("Segoe UI", 9)).grid(row=0, column=2, padx=5, pady=5, sticky="e")
        self.slow_ema = ttk.Entry(self.parameters_frame, width=10, font=("Segoe UI", 9))
        self.slow_ema.grid(row=0, column=3, padx=5, pady=5, sticky="w")
        self.slow_ema.insert(0, "26")
        
        # Signal Period
        tk.Label(self.parameters_frame, text="Signal Period:", fg=self.colors["text"], 
               bg=self.colors["panel"], font=("Segoe UI", 9)).grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.signal_period = ttk.Entry(self.parameters_frame, width=10, font=("Segoe UI", 9))
        self.signal_period.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        self.signal_period.insert(0, "9")

    def update_strategy_config(self, event=None):
        """Update configuration based on selected strategy type"""
        strategy_type = self.strategy_type.get()
        
        if strategy_type == "Moving Average Crossover":
            self.create_ma_config()
        elif strategy_type == "RSI":
            self.create_rsi_config()
        elif strategy_type == "MACD":
            self.create_macd_config()

    def add_strategy(self):
        """Add a new strategy"""
        self.strategy_name.delete(0, tk.END)
        self.strategy_name.insert(0, f"Strategy {len(self.strategies)+1}")
        self.strategy_type.current(0)
        self.update_strategy_config()

    def edit_strategy(self):
        """Edit selected strategy"""
        selected = self.strategy_tree.selection()
        if not selected:
            messagebox.showwarning("Selection Error", "Please select a strategy to edit")
            return
            
        strategy_id = self.strategy_tree.item(selected[0])["values"][0]
        strategy = next((s for s in self.strategies if s["id"] == strategy_id), None)
        
        if strategy:
            self.strategy_name.delete(0, tk.END)
            self.strategy_name.insert(0, strategy["name"])
            
            # Set strategy type
            index = self.strategy_type["values"].index(strategy["type"])
            self.strategy_type.current(index)
            self.update_strategy_config()
            
            # Set parameters
            if strategy["type"] == "Moving Average Crossover":
                self.short_ma.delete(0, tk.END)
                self.short_ma.insert(0, strategy["params"]["short_ma"])
                self.long_ma.delete(0, tk.END)
                self.long_ma.insert(0, strategy["params"]["long_ma"])
            elif strategy["type"] == "RSI":
                self.rsi_period.delete(0, tk.END)
                self.rsi_period.insert(0, strategy["params"]["period"])
                self.overbought.delete(0, tk.END)
                self.overbought.insert(0, strategy["params"]["overbought"])
                self.oversold.delete(0, tk.END)
                self.oversold.insert(0, strategy["params"]["oversold"])
            elif strategy["type"] == "MACD":
                self.fast_ema.delete(0, tk.END)
                self.fast_ema.insert(0, strategy["params"]["fast_ema"])
                self.slow_ema.delete(0, tk.END)
                self.slow_ema.insert(0, strategy["params"]["slow_ema"])
                self.signal_period.delete(0, tk.END)
                self.signal_period.insert(0, strategy["params"]["signal_period"])

    def delete_strategy(self):
        """Delete selected strategy"""
        selected = self.strategy_tree.selection()
        if not selected:
            messagebox.showwarning("Selection Error", "Please select a strategy to delete")
            return
            
        strategy_id = self.strategy_tree.item(selected[0])["values"][0]
        
        # Remove from strategies
        self.strategies = [s for s in self.strategies if s["id"] != strategy_id]
        
        # Remove from active strategies
        self.active_strategies = [s for s in self.active_strategies if s["id"] != strategy_id]
        
        # Remove from wishlist treeviews
        for tree in self.stock_trees:
            for item in tree.get_children():
                values = tree.item(item)["values"]
                if len(values) > 4 and values[4] == strategy_id:
                    values[4] = ""
                    tree.item(item, values=values)
        
        self.save_strategies()
        self.update_strategy_tree()
        self.log_transaction(f"Deleted strategy: {strategy_id}")

    def toggle_strategy(self):
        """Enable/disable selected strategy"""
        selected = self.strategy_tree.selection()
        if not selected:
            messagebox.showwarning("Selection Error", "Please select a strategy to toggle")
            return
            
        strategy_id = self.strategy_tree.item(selected[0])["values"][0]
        strategy = next((s for s in self.strategies if s["id"] == strategy_id), None)
        
        if strategy:
            # Toggle status
            if strategy in self.active_strategies:
                self.active_strategies.remove(strategy)
                strategy["status"] = "Disabled"
            else:
                self.active_strategies.append(strategy)
                strategy["status"] = "Enabled"
                
            self.save_strategies()
            self.update_strategy_tree()
            self.log_transaction(f"{'Enabled' if strategy['status'] == 'Enabled' else 'Disabled'} strategy: {strategy['name']}")

    def save_strategy(self):
        """Save the current strategy configuration"""
        strategy_name = self.strategy_name.get().strip()
        strategy_type = self.strategy_type.get()
        
        if not strategy_name:
            messagebox.showwarning("Input Error", "Please enter a strategy name")
            return
            
        # Get parameters
        params = {}
        if strategy_type == "Moving Average Crossover":
            params = {
                "short_ma": self.short_ma.get().strip(),
                "long_ma": self.long_ma.get().strip()
            }
        elif strategy_type == "RSI":
            params = {
                "period": self.rsi_period.get().strip(),
                "overbought": self.overbought.get().strip(),
                "oversold": self.oversold.get().strip()
            }
        elif strategy_type == "MACD":
            params = {
                "fast_ema": self.fast_ema.get().strip(),
                "slow_ema": self.slow_ema.get().strip(),
                "signal_period": self.signal_period.get().strip()
            }
        
        # Check if we're editing an existing strategy
        selected = self.strategy_tree.selection()
        if selected:
            strategy_id = self.strategy_tree.item(selected[0])["values"][0]
            strategy = next((s for s in self.strategies if s["id"] == strategy_id), None)
            if strategy:
                strategy["name"] = strategy_name
                strategy["type"] = strategy_type
                strategy["params"] = params
        else:
            # Create new strategy
            strategy_id = len(self.strategies) + 1
            strategy = {
                "id": strategy_id,
                "name": strategy_name,
                "type": strategy_type,
                "params": params,
                "status": "Enabled",
                "instruments": []
            }
            self.strategies.append(strategy)
            self.active_strategies.append(strategy)
        
        self.save_strategies()
        self.update_strategy_tree()
        self.log_transaction(f"Saved strategy: {strategy_name}")

    def update_strategy_tree(self):
        """Update the strategy treeview"""
        # Clear existing items
        for item in self.strategy_tree.get_children():
            self.strategy_tree.delete(item)
            
        # Add strategies
        for strategy in self.strategies:
            self.strategy_tree.insert("", tk.END, values=(
                strategy["id"],
                strategy["name"],
                strategy["type"],
                strategy["status"],
                ", ".join(strategy["instruments"])
            ))

    def get_historical_data(self, symbol, days=100):
        """Get historical data for a symbol (simulated)"""
        # In a real implementation, you would fetch this from the broker API
        if symbol not in self.historical_data:
            # Generate random data for simulation
            np.random.seed(42)
            prices = np.cumprod(1 + np.random.normal(0, 0.01, days)) * 100
            dates = pd.date_range(end=datetime.today(), periods=days)
            self.historical_data[symbol] = pd.DataFrame({
                "date": dates,
                "close": prices
            }).set_index("date")
        return self.historical_data[symbol]

    def moving_average_strategy(self, symbol, strategy):
        """Moving Average Crossover strategy"""
        try:
            # Get historical data
            df = self.get_historical_data(symbol)
            
            # Calculate moving averages
            short_ma = int(strategy["params"]["short_ma"])
            long_ma = int(strategy["params"]["long_ma"])
            
            df["SMA_Short"] = talib.SMA(df["close"], timeperiod=short_ma)
            df["SMA_Long"] = talib.SMA(df["close"], timeperiod=long_ma)
            
            # Generate signals
            df["Signal"] = 0
            df["Signal"][short_ma:] = np.where(
                df["SMA_Short"][short_ma:] > df["SMA_Long"][short_ma:], 1, 0)
            df["Position"] = df["Signal"].diff()
            
            # Get last signal
            last_signal = df["Position"].iloc[-1]
            
            if last_signal > 0:
                return "BUY"
            elif last_signal < 0:
                return "SELL"
            else:
                return None
        except Exception as e:
            self.log_transaction(f"Error in MA strategy for {symbol}: {str(e)}")
            return None

    def rsi_strategy(self, symbol, strategy):
        """RSI strategy"""
        try:
            # Get historical data
            df = self.get_historical_data(symbol)
            
            # Calculate RSI
            period = int(strategy["params"]["period"])
            overbought = int(strategy["params"]["overbought"])
            oversold = int(strategy["params"]["oversold"])
            
            df["RSI"] = talib.RSI(df["close"], timeperiod=period)
            
            # Generate signals
            if df["RSI"].iloc[-1] < oversold:
                return "BUY"
            elif df["RSI"].iloc[-1] > overbought:
                return "SELL"
            else:
                return None
        except Exception as e:
            self.log_transaction(f"Error in RSI strategy for {symbol}: {str(e)}")
            return None

    def macd_strategy(self, symbol, strategy):
        """MACD strategy"""
        try:
            # Get historical data
            df = self.get_historical_data(symbol)
            
            # Calculate MACD
            fast_ema = int(strategy["params"]["fast_ema"])
            slow_ema = int(strategy["params"]["slow_ema"])
            signal_period = int(strategy["params"]["signal_period"])
            
            macd, signal, _ = talib.MACD(df["close"], 
                                        fastperiod=fast_ema, 
                                        slowperiod=slow_ema, 
                                        signalperiod=signal_period)
            
            # Generate signals
            if macd.iloc[-1] > signal.iloc[-1] and macd.iloc[-2] <= signal.iloc[-2]:
                return "BUY"
            elif macd.iloc[-1] < signal.iloc[-1] and macd.iloc[-2] >= signal.iloc[-2]:
                return "SELL"
            else:
                return None
        except Exception as e:
            self.log_transaction(f"Error in MACD strategy for {symbol}: {str(e)}")
            return None

    def execute_strategy_signal(self, symbol, action, strategy_name):
        """Execute a trade based on strategy signal"""
        try:
            # Get quantity (for simplicity, using fixed quantity)
            quantity = 1
            
            # Get selected account
            selected_account = self.account_dropdown.get()
            if not selected_account:
                self.log_transaction("No account selected for strategy execution")
                return
                
            # Find the kite instance for the selected account
            kite = None
            for i, creds in enumerate(self.credentials_list):
                if creds["username"] == selected_account:
                    kite = self.buy_kite_instances[i] if action == "BUY" else self.sell_kite_instances[i]
                    break
            
            if not kite:
                self.log_transaction("Failed to find account instance for strategy execution")
                return
                
            # Execute trade
            order_id = kite.place_order(
                exchange="NSE",
                tradingsymbol=symbol,
                transaction_type=action,
                quantity=quantity,
                order_type="MARKET",
                product="MIS",
                variety="regular"
            )
            
            message = f"Strategy '{strategy_name}': {action} order for {quantity} shares of {symbol} placed! Order ID: {order_id}"
            self.log_transaction(message)
        except Exception as e:
            message = f"Error placing strategy order: {str(e)}"
            self.log_transaction(message)

    def strategy_execution_thread(self):
        """Thread for executing trading strategies"""
        while True:
            try:
                # Only run during market hours
                now = datetime.now()
                hour = now.hour
                if not ((9 <= hour < 15) or (hour == 15 and now.minute < 30)):
                    time.sleep(60)
                    continue
                
                # Process active strategies
                for strategy in self.active_strategies:
                    for symbol in strategy["instruments"]:
                        # Get signal based on strategy type
                        signal = None
                        if strategy["type"] == "Moving Average Crossover":
                            signal = self.moving_average_strategy(symbol, strategy)
                        elif strategy["type"] == "RSI":
                            signal = self.rsi_strategy(symbol, strategy)
                        elif strategy["type"] == "MACD":
                            signal = self.macd_strategy(symbol, strategy)
                        
                        # Execute trade if signal generated
                        if signal:
                            self.execute_strategy_signal(symbol, signal, strategy["name"])
                
                # Check every minute
                time.sleep(60)
            except Exception as e:
                self.log_transaction(f"Error in strategy thread: {str(e)}")
                time.sleep(10)

    def configure_styles(self):
        """Configure ttk styles based on current theme"""
        self.style.theme_use('clam')
        self.style.configure("TNotebook", background=self.colors["panel"], borderwidth=0)
        self.style.configure("TNotebook.Tab", 
                           background=self.colors["panel"], 
                           foreground=self.colors["light_text"],
                           padding=[15, 5],
                           font=('Segoe UI', 9, 'bold'))
        self.style.map("TNotebook.Tab", 
                     background=[("selected", self.colors["primary"])],
                     foreground=[("selected", "white")])
        
        self.style.configure("Treeview", 
                           background=self.colors["panel"], 
                           fieldbackground=self.colors["panel"], 
                           foreground=self.colors["text"],
                           font=('Segoe UI', 9),
                           rowheight=25,
                           borderwidth=0)
        
        self.style.configure("Treeview.Heading", 
                           background=self.colors["primary"], 
                           foreground="white", 
                           font=("Segoe UI", 9, "bold"),
                           borderwidth=0)
        
        self.style.map("Treeview", 
                     background=[('selected', self.colors["secondary"])])
        
        # Suggestion tree style
        self.style.configure("Suggestion.Treeview", 
                           background=self.colors["panel"], 
                           fieldbackground=self.colors["panel"], 
                           foreground=self.colors["text"],
                           font=('Segoe UI', 9),
                           rowheight=25,
                           borderwidth=0)
        
        self.style.configure("Suggestion.Treeview.Heading", 
                           background=self.colors["primary"], 
                           foreground="white", 
                           font=("Segoe UI", 9, "bold"),
                           borderwidth=0)

    def change_theme(self, theme_name):
        """Change the application theme"""
        self.current_theme = theme_name
        self.colors = self.themes[theme_name]
        
        # Update all widgets with new colors
        self.update_theme_colors()
        
        # Reconfigure ttk styles
        self.configure_styles()
        
        # Log the theme change
        self.log_transaction(f"Changed theme to {theme_name.capitalize()} Mode")

    def update_theme_colors(self):
        """Update all widgets with current theme colors"""
        # Update root window
        self.root.config(bg=self.colors["background"])
        
        # Update header
        self.header_frame.config(bg=self.colors["header"])
        self.title_label.config(bg=self.colors["header"])
        self.tagline_label.config(bg=self.colors["header"])
        self.status_bar.config(bg=self.colors["header"])
        
        # Update main frame
        self.main_frame.config(bg=self.colors["background"])
        
        # Update left panel
        self.left_panel.config(bg=self.colors["panel"], highlightbackground=self.colors["border"])
        self.account_frame.config(bg=self.colors["panel"], fg=self.colors["light_text"])
        self.dashboard_frame.config(bg=self.colors["panel"], fg=self.colors["light_text"])
        
        # Update right panel
        self.right_panel.config(bg=self.colors["panel"], highlightbackground=self.colors["border"])
        self.bottom_panel.config(bg=self.colors["panel"])
        
        # Update search frame
        self.search_frame.config(bg=self.colors["panel"], fg=self.colors["light_text"])
        
        # Update trade frame
        self.trade_frame.config(bg=self.colors["panel"], fg=self.colors["light_text"])
        
        # Update buttons
        self.add_account_button.config(bg=self.colors["secondary"])
        self.change_access_token_button.config(bg=self.colors["accent"])
        self.search_button.config(bg=self.colors["secondary"])
        self.add_button.config(bg=self.colors["secondary"])
        self.remove_button.config(bg=self.colors["accent"])
        self.buy_button.config(bg="#10b981")
        self.sell_button.config(bg=self.colors["accent"])
        self.add_strategy_button.config(bg=self.colors["secondary"])
        self.edit_strategy_button.config(bg=self.colors["secondary"])
        self.delete_strategy_button.config(bg=self.colors["accent"])
        self.toggle_strategy_button.config(bg=self.colors["primary"])
        self.save_strategy_button.config(bg=self.colors["secondary"])
        
        # Update labels
        self.portfolio_value.config(bg=self.colors["panel"])
        self.market_status.config(bg=self.colors["panel"])
        self.market_timings_label.config(bg=self.colors["panel"], fg=self.colors["light_text"])
        self.quantity_label.config(bg=self.colors["panel"], fg=self.colors["text"])
        self.order_type_label.config(bg=self.colors["panel"], fg=self.colors["text"])
        self.limit_price_label.config(bg=self.colors["panel"], fg=self.colors["text"])
        
        # Update market status colors
        self.update_market_status()

    def toggle_limit_price(self, event=None):
        """Show/hide limit price entry based on order type"""
        if self.order_type.get() == "LIMIT":
            self.limit_price_label.grid(row=0, column=4, padx=(20, 5), pady=5, sticky="e")
            self.limit_price_entry.grid(row=0, column=5, padx=5, pady=5, sticky="w")
        else:
            self.limit_price_label.grid_remove()
            self.limit_price_entry.grid_remove()

    def update_market_status(self):
        """Update market status based on current time"""
        now = datetime.now()
        hour = now.hour
        
        # Market hours: 9:15 AM to 3:30 PM
        if (9 <= hour < 15) or (hour == 15 and now.minute < 30):
            self.market_status.config(text="OPEN", fg=self.colors["positive"])
        else:
            self.market_status.config(text="CLOSED", fg=self.colors["negative"])
        
        # Update every minute
        self.root.after(60000, self.update_market_status)

    def add_new_account(self):
        username = self.username_entry.get().strip()
        api_key = self.api_key_entry.get().strip()
        api_secret = self.api_secret_entry.get().strip()
        access_token = self.access_token_entry.get().strip()

        if username and api_key and api_secret and access_token:
            new_credentials = {
                "username": username,
                "api_key": api_key,
                "api_secret": api_secret,
                "access_token": access_token
            }
            
            try:
                # Test the credentials
                kite = KiteConnect(api_key=api_key)
                kite.set_access_token(access_token)
                profile = kite.profile()
                
                # Add account if credentials are valid
                self.credentials_list.append(new_credentials)
                self.save_credentials_list(self.credentials_list)
                
                # Initialize KiteConnect instances
                buy_kite = KiteConnect(api_key=api_key)
                sell_kite = KiteConnect(api_key=api_key)
                buy_kite.set_access_token(access_token)
                sell_kite.set_access_token(access_token)
                self.buy_kite_instances.append(buy_kite)
                self.sell_kite_instances.append(sell_kite)
                
                # Update UI
                self.account_dropdown['values'] = self.get_account_usernames()
                self.account_dropdown.current(len(self.account_dropdown['values']) - 1)
                
                # Clear fields
                self.username_entry.delete(0, tk.END)
                self.api_key_entry.delete(0, tk.END)
                self.api_secret_entry.delete(0, tk.END)
                self.access_token_entry.delete(0, tk.END)
                
                messagebox.showinfo("Success", f"Account '{username}' added successfully!")
                self.log_transaction(f"Added account: {username}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to add account: {str(e)}")
        else:
            messagebox.showwarning("Input Error", "Please fill in all fields")

    def get_account_usernames(self):
        return [creds["username"] for creds in self.credentials_list]

    def change_access_token(self):
        selected_username = self.account_dropdown.get()
        if not selected_username:
            messagebox.showwarning("Selection Error", "Please select an account first")
            return
            
        new_access_token = simpledialog.askstring("Update Access Token", 
                                                 f"Enter new access token for {selected_username}:",
                                                 parent=self.root)
        
        if new_access_token:
            for creds in self.credentials_list:
                if creds["username"] == selected_username:
                    creds["access_token"] = new_access_token
                    self.save_credentials_list(self.credentials_list)
                    
                    # Update Kite instance
                    index = self.credentials_list.index(creds)
                    if index < len(self.buy_kite_instances):
                        self.buy_kite_instances[index].set_access_token(new_access_token)
                        self.sell_kite_instances[index].set_access_token(new_access_token)
                    
                    messagebox.showinfo("Success", f"Access token updated for {selected_username}")
                    self.log_transaction(f"Updated token for: {selected_username}")
                    break

    def search_instruments(self):
        query = self.search_entry.get().strip().upper()
        if not query:
            messagebox.showwarning("Search Error", "Please enter a search query")
            return
            
        self.update_suggestions()

    def update_suggestions(self, event=None):
        query = self.search_entry.get().strip().upper()
        
        # Clear existing suggestions
        for item in self.suggestion_tree.get_children():
            self.suggestion_tree.delete(item)

        if query:
            # Get matching instruments
            matches = []
            for instrument in self.all_instruments:
                if query in instrument["tradingsymbol"] or query in instrument["name"]:
                    matches.append(instrument)
                    if len(matches) >= 20:  # Limit to 20 results
                        break
            
            # Add to treeview
            for instrument in matches:
                self.suggestion_tree.insert("", tk.END, values=(
                    instrument["tradingsymbol"],
                    instrument["name"],
                    instrument["exchange"],
                    instrument["instrument_type"]
                ))

    def add_selected_to_wishlist(self):
        selected = self.suggestion_tree.selection()
        if not selected:
            messagebox.showwarning("Selection Error", "Please select an instrument from the list")
            return
            
        selected_item = self.suggestion_tree.item(selected[0])
        selected_stock = selected_item["values"][0]  # Get symbol
        self.add_to_wishlist(None, selected_stock)

    def add_to_wishlist_from_tree(self, event):
        """Add to wishlist on double-click"""
        selected = self.suggestion_tree.selection()
        if selected:
            selected_item = self.suggestion_tree.item(selected[0])
            selected_stock = selected_item["values"][0]  # Get symbol
            self.add_to_wishlist(None, selected_stock)

    def add_to_wishlist(self, event, selected_stock=None):
        if selected_stock is None:
            selected = self.suggestion_tree.selection()
            if not selected:
                return
            selected_item = self.suggestion_tree.item(selected[0])
            selected_stock = selected_item["values"][0]  # Get symbol
        
        current_tab = self.notebook.index(self.notebook.select())
        
        # Check if already in wishlist
        tree = self.stock_trees[current_tab]
        for item in tree.get_children():
            if tree.item(item)["values"][0] == selected_stock:
                messagebox.showinfo("Info", f"{selected_stock} is already in this wishlist")
                return
                
        # Add to wishlist
        tree.insert("", tk.END, values=(selected_stock, "0.00", "0.00%", "0", ""))
        self.subscribed_instruments[current_tab].append(selected_stock)
        self.save_subscribed_instruments()
        self.log_transaction(f"Added to wishlist {current_tab+1}: {selected_stock}")

    def remove_from_wishlist(self):
        current_tab = self.notebook.index(self.notebook.select())
        tree = self.stock_trees[current_tab]
        selected_items = tree.selection()
        
        if not selected_items:
            messagebox.showwarning("Selection Error", "Please select an instrument to remove")
            return
            
        for item in selected_items:
            stock = tree.item(item)["values"][0]
            if stock in self.subscribed_instruments[current_tab]:
                self.subscribed_instruments[current_tab].remove(stock)
            tree.delete(item)
        
        self.save_subscribed_instruments()
        self.log_transaction(f"Removed from wishlist {current_tab+1}: {stock}")

    def get_all_instruments(self):
        try:
            url = "https://api.kite.trade/instruments"
            response = requests.get(url)
            data = response.text.splitlines()
            
            if not data:
                return []
                
            headers = data[0].split(",")
            instruments = []
            
            for row in data[1:]:
                values = row.split(",")
                if len(values) == len(headers):
                    instrument = {headers[i]: values[i] for i in range(len(headers))}
                    instruments.append(instrument)
            
            return instruments
        except Exception as e:
            messagebox.showerror("Error", f"Failed to fetch instruments: {str(e)}")
            return []

    def update_stock_prices_thread(self):
        while True:
            try:
                for i in range(len(self.stock_trees)):
                    tree = self.stock_trees[i]
                    subscribed_instruments = self.subscribed_instruments[i]
                    
                    for stock in subscribed_instruments:
                        ltp, change, volume = self.get_stock_data(stock)
                        
                        # Update treeview
                        for item in tree.get_children():
                            if tree.item(item)["values"][0] == stock:
                                # Set color based on change
                                change_value = float(change.strip('%'))
                                change_color = self.colors["positive"] if change_value >= 0 else self.colors["negative"]
                                tree.tag_configure(change_color, foreground=change_color)
                                
                                # Update values, preserving strategy column
                                values = list(tree.item(item)["values"])
                                if len(values) < 5:
                                    values.extend([""] * (5 - len(values)))
                                values[1] = ltp
                                values[2] = change
                                values[3] = volume
                                tree.item(item, values=values, tags=(change_color,))
                                break
                
                # Update portfolio value every 5 seconds
                if self.credentials_list:
                    self.update_portfolio_value()
                
                time.sleep(5)
            except Exception as e:
                print(f"Error in update thread: {str(e)}")
                time.sleep(10)

    def get_stock_data(self, stock):
        try:
            # Use the first account for market data
            if not self.credentials_list:
                return "0.00", "0.00%", "0"
                
            kite = self.buy_kite_instances[0]
            quote = kite.quote(f"NSE:{stock}")
            
            ltp = quote[f"NSE:{stock}"]["last_price"]
            change_pct = quote[f"NSE:{stock}"]["net_change_percentage"]
            volume = quote[f"NSE:{stock}"]["volume"]
            
            return f"{ltp:.2f}", f"{change_pct:.2f}%", f"{volume:,}"
        except Exception as e:
            print(f"Error fetching data for {stock}: {str(e)}")
            return "0.00", "0.00%", "0"

    def update_portfolio_value(self):
        try:
            total_value = 0.0
            
            for kite in self.buy_kite_instances:
                holdings = kite.holdings()
                for holding in holdings:
                    total_value += holding["last_price"] * holding["quantity"]
            
            self.portfolio_value.config(text=f"₹{total_value:,.2f}")
        except:
            # Fail silently if we can't update
            pass

    def buy_stock(self):
        self.execute_trade("BUY")

    def sell_stock(self):
        self.execute_trade("SELL")

    def execute_trade(self, action):
        # Get selected stock
        current_tab = self.notebook.index(self.notebook.select())
        tree = self.stock_trees[current_tab]
        selected_items = tree.selection()
        
        if not selected_items:
            messagebox.showwarning("Selection Error", "Please select an instrument to trade")
            return
            
        stock = tree.item(selected_items[0])["values"][0]
        
        # Get quantity
        quantity = self.quantity_entry.get().strip()
        if not quantity.isdigit() or int(quantity) <= 0:
            messagebox.showwarning("Input Error", "Please enter a valid quantity")
            return
            
        quantity = int(quantity)
        
        # Get order type
        order_type = self.order_type.get()
        
        # Get limit price if applicable
        price = None
        if order_type == "LIMIT":
            price_str = self.limit_price_entry.get().strip()
            if not price_str.replace('.', '', 1).isdigit() or float(price_str) <= 0:
                messagebox.showwarning("Input Error", "Please enter a valid limit price")
                return
            price = float(price_str)
        
        # Get selected accounts
        selected_account = self.account_dropdown.get()
        if not selected_account:
            messagebox.showwarning("Selection Error", "Please select an account")
            return
            
        # Find the kite instance for the selected account
        kite = None
        for i, creds in enumerate(self.credentials_list):
            if creds["username"] == selected_account:
                kite = self.buy_kite_instances[i] if action == "BUY" else self.sell_kite_instances[i]
                break
        
        if not kite:
            messagebox.showerror("Error", "Failed to find account instance")
            return
            
        # Execute trade
        try:
            order_params = {
                "exchange": "NSE",
                "tradingsymbol": stock,
                "transaction_type": action,
                "quantity": quantity,
                "order_type": order_type,
                "product": "MIS",
                "variety": "regular"
            }
            
            # Add price for limit orders
            if order_type == "LIMIT" and price:
                order_params["price"] = price
            
            order_id = kite.place_order(**order_params)
            
            message = f"{action} order for {quantity} shares of {stock} placed successfully! Order ID: {order_id}"
            messagebox.showinfo("Success", message)
            self.log_transaction(message)
        except Exception as e:
            message = f"Error placing {action} order: {str(e)}"
            messagebox.showerror("Error", message)
            self.log_transaction(message)

    def log_transaction(self, message):
        """Log transaction to file"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        
        # Write to log file
        try:
            with open("transactions.log", "a") as log_file:
                log_file.write(log_entry + "\n")
        except Exception as e:
            print(f"Error writing to log file: {str(e)}")
        
        # Print to console for debugging
        print(log_entry)

    def save_credentials_list(self, credentials_list):
        try:
            with open("credentials.json", "w") as file:
                json.dump(credentials_list, file)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save credentials: {str(e)}")

    def load_credentials_list(self):
        try:
            if os.path.exists("credentials.json"):
                with open("credentials.json", "r") as file:
                    return json.load(file)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load credentials: {str(e)}")
        return []

    def save_subscribed_instruments(self):
        try:
            # Save wishlist names along with instruments
            data = {
                "wishlist_names": self.wishlist_names,
                "instruments": self.subscribed_instruments
            }
            with open("wishlists.json", "w") as file:
                json.dump(data, file)
        except Exception as e:
            print(f"Error saving wishlists: {str(e)}")

    def load_subscribed_instruments(self):
        try:
            if os.path.exists("wishlists.json"):
                with open("wishlists.json", "r") as file:
                    data = json.load(file)
                    self.wishlist_names = data.get("wishlist_names", [f"Wishlist {i+1}" for i in range(10)])
                    self.subscribed_instruments = data.get("instruments", [[] for _ in range(10)])
                    
                    # Update tab names
                    for i, name in enumerate(self.wishlist_names):
                        if i < self.notebook.index("end"):
                            self.notebook.tab(i, text=name)
                    
                    # Populate wishlists
                    for i, wishlist in enumerate(self.subscribed_instruments):
                        if i < len(self.stock_trees):
                            tree = self.stock_trees[i]
                            for stock in wishlist:
                                tree.insert("", tk.END, values=(stock, "0.00", "0.00%", "0", ""))
        except Exception as e:
            print(f"Error loading wishlists: {str(e)}")

    def save_strategies(self):
        """Save strategies to file"""
        try:
            with open("strategies.json", "w") as file:
                json.dump({
                    "strategies": self.strategies,
                    "active_strategies": [s["id"] for s in self.active_strategies]
                }, file)
        except Exception as e:
            print(f"Error saving strategies: {str(e)}")

    def load_strategies(self):
        """Load strategies from file"""
        try:
            if os.path.exists("strategies.json"):
                with open("strategies.json", "r") as file:
                    data = json.load(file)
                    self.strategies = data.get("strategies", [])
                    active_ids = data.get("active_strategies", [])
                    self.active_strategies = [s for s in self.strategies if s["id"] in active_ids]
                    
                    # Update strategy status
                    for strategy in self.strategies:
                        strategy["status"] = "Enabled" if strategy in self.active_strategies else "Disabled"
                    
                    self.update_strategy_tree()
        except Exception as e:
            print(f"Error loading strategies: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = StratagemIQ(root)
    root.mainloop()