import MetaTrader5 as mt5
import pandas as pd

server = 'Deriv-Demo'
login = 24334468
password = '@5EjRxWn'


# Define the symbol and the amount for trading
symbol = 'EURUSD'
lot = 0.1  # Trading volume in lots

def initialize_mt5():
    if not mt5.initialize(login, server, password):
    # if not mt5.initialize(login=login, server=server, password=password):
        print("Failed to initialize MT5 connection")
        mt5.shutdown()
        return False
    else:
        print("MT5 connection initialized successfully")
        return True

def fetch_historical_data_from_mt5(symbol, bars=1000, timeframe=mt5.TIMEFRAME_M5):
    """Fetch historical data using MetaTrader 5."""
    if not initialize_mt5():
        return None

    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, bars)
    mt5.shutdown()

    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    return df

def is_trending(df, window=50):
    """Check if the market is trending based on moving average."""
    df['moving_avg'] = df['close'].rolling(window=window).mean()
    if df['moving_avg'].iloc[-1] > df['moving_avg'].iloc[-2]:
        return "up"
    elif df['moving_avg'].iloc[-1] < df['moving_avg'].iloc[-2]:
        return "down"
    return "sideways"

def execute_trade(action, symbol, lot, take_profit_pips):
    """Place an order in MT5."""
    if not initialize_mt5():
        return

    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None:
        print(f"{symbol} not found, can not call order_check()")
        mt5.shutdown()
        return

    if not symbol_info.visible:
        print(f"{symbol} is not visible, trying to switch on")
        if not mt5.symbol_select(symbol, True):
            print(f"symbol_select({symbol}) failed, exit")
            mt5.shutdown()
            return

    point = symbol_info.point
    price = mt5.symbol_info_tick(symbol).ask if action == 'buy' else mt5.symbol_info_tick(symbol).bid
    take_profit = price + take_profit_pips * point if action == 'buy' else price - take_profit_pips * point

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": lot,
        "type": mt5.ORDER_TYPE_BUY if action == 'buy' else mt5.ORDER_TYPE_SELL,
        "price": price,
        "sl": 0.0,  # Stop loss not set
        "tp": take_profit,
        "deviation": 20,
        "magic": 234000,
        "comment": "python script open",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }

    result = mt5.order_send(request)
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print("Order failed, retcode={}".format(result.retcode))
    else:
        print("Order executed successfully")

    mt5.shutdown()

def main():
    df = fetch_historical_data_from_mt5(symbol)
    if df is not None:
        trend_direction = is_trending(df)
        if trend_direction != "sideways":
            action = "buy" if trend_direction == "up" else "sell"
            execute_trade(action, symbol, lot, take_profit_pips=20)
        else:
            print("Market is not trending, no trade executed.")

if __name__ == "__main__":
    main()
