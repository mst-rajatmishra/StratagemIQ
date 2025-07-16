# ***StratagemIQ***

## Overview

The StratagemIQ App allows users to manage a wishlist of stocks, view real-time stock prices, and execute buy/sell orders using the Kite Connect API. Users can manage multiple accounts and securely store their 

## credentials.

### Features

Multiple Account Management: Add and manage multiple trading accounts.
Real-time Stock Prices: Automatically fetch and display current stock prices.
Blaustocks: Maintain multiple wishlists for different stocks.
Buy/Sell Functionality: Execute buy and sell orders on selected stocks.
User-friendly Interface: Built with Tkinter for an intuitive GUI experience.

## Requirements
```
Python 3
tkinter
PIL (Pillow)
requests
kiteconnect (Kite Connect API)
JSON for data storage
```
## Installation

Ensure Python 3 is installed on your system.
Install the required packages:

```
pip install pillow
pip install requests
pip install requests

```

Getting Started
Clone or download the repository containing the Blaustocks.py file.
Run the application using:

```python Blaustocks.py```

## User Interface Components
```
Account Management:Input fields for username, API Key, API Secret, and Access Token.
Buttons to add a new account or change the access token.
Search Bar: For searching stocks to add to the wishlist.
Wishlist Tabs: Up to 10 separate tabs for managing different wishlists. Each tab displays a list of stocks and their latest prices.
Buy/Sell Frame: Entry for quantity and buttons to execute buy/sell orders.
```
## API Integration
The application uses the Kite Connect API for:
```
Fetching stock prices.
Executing buy/sell orders.
Managing user accounts and credentials.
Data Storage
Credentials: Stored in credentials_list.json.
Wishlists: Each wishlist is stored in a separate JSON file named wishlist_1.json, wishlist_2.json, etc.
Functions Overview
create_widgets(): Initializes GUI components.
add_new_account(): Adds new trading account credentials.
buy_stock(): Places a buy order for the selected stock.
sell_stock(): Places a sell order for the selected stock.
update_stock_prices_thread(): Fetches real-time stock prices in a separate thread.
save_credentials_list(): Saves user credentials to a JSON file.
load_credentials_list(): Loads user credentials from a JSON file.
```
## Error Handling
The application includes error handling for API requests and user inputs to provide feedback via message boxes.

Future Enhancements
Implement additional stock market data analytics.
Introduce notifications for price alerts.
Enable integration with additional trading platforms.
## License
This software is open-source and can be modified and distributed under the terms specified in the accompanying license file.
