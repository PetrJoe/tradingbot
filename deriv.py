import MetaTrader5 as mt5
import pandas as pd
import numpy as np

# Your MetaTrader 5 login credentials and server
login = 24334468
password = '@5EjRxWn'
server = 'Deriv-Demo'

# Initialize MT5 connection
if not mt5.initialize(login=login, password=password, server=server):
    print(f"Initialize() failed, error code = {mt5.last_error()}")
else:
    print("Successfully connected to MT5")

def atr(df, period=14):
    """Calculate the Average True Range (ATR)."""
    high_low = df['high'] - df['low']
    high_close = np.abs(df['high'] - df['close'].shift())
    low_close = np.abs(df['low'] - df['close'].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = np.max(ranges, axis=1)
    atr = true_range.rolling(period).mean()
    return atr

def lwma(prices, period):
    """Calculate Linear Weighted Moving Average."""
    weights = np.arange(1, period + 1)
    return np.dot(prices, weights) / weights.sum()

def stochastic_oscillator(highs, lows, closes, k_period, d_period):
    """Calculate Stochastic Oscillator (%K and %D)."""
    lowest_low = pd.Series(lows).rolling(window=k_period).min()
    highest_high = pd.Series(highs).rolling(window=k_period).max()
    k_values = 100 * (closes - lowest_low) / (highest_high - lowest_low)
    d_values = k_values.rolling(window=d_period).mean()
    return k_values.iloc[-1], d_values.iloc[-1]

def get_data(symbol, timeframe, bars):
    """Fetch historical data for the symbol."""
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, bars)
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    return df

def check_trading_conditions(symbol):
    """Check if the symbol is tradable and the spread is acceptable."""
    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None or not symbol_info.visible:
        print(f"{symbol} is not available or not visible.")
        if not mt5.symbol_select(symbol, True):
            print(f"Failed to select {symbol}.")
            return False
    # Adjust the spread limit based on your strategy and symbol volatility
    if symbol_info.spread > 20:  # Adjusted value for example purposes
        print(f"Spread for {symbol} is too high.")
        return False
    return True

def check_trade_signals(df, short_lwma_period, long_lwma_period, k_period, d_period, k_buy_threshold, k_sell_threshold):
    """Check for trade signals based on LWMAs and Stochastic Oscillator."""
    df['short_lwma'] = df['close'].rolling(window=short_lwma_period).apply(lambda x: lwma(x, short_lwma_period), raw=True)
    df['long_lwma'] = df['close'].rolling(window=long_lwma_period).apply(lambda x: lwma(x, long_lwma_period), raw=True)
    k, d = stochastic_oscillator(df['high'], df['low'], df['close'], k_period, d_period)
    
    # Buy/Sell signal conditions
    if df['short_lwma'].iloc[-2] < df['long_lwma'].iloc[-2] and df['short_lwma'].iloc[-1] > df['long_lwma'].iloc[-1] and k < d and k < k_buy_threshold:
        return "buy"
    elif df['short_lwma'].iloc[-2] > df['long_lwma'].iloc[-2] and df['short_lwma'].iloc[-1] < df['long_lwma'].iloc[-1] and k > d and k > k_sell_threshold:
        return "sell"
    else:
        return "hold"

def main():
    symbol = "Volatility 10 Index"
    timeframe = mt5.TIMEFRAME_M1  # Adjusted to a minute timeframe for this example
    bars = 100  # Historical data bars

    if not check_trading_conditions(symbol):
        return

    df = get_data(symbol, timeframe, bars)
    df['atr'] = atr(df, 14)  # Example ATR calculation for volatility assessment
    
    # Trading strategy parameters
    short_lwma_period = 5
    long_lwma_period = 20
    k_period = 14
    d_period = 3
    k_buy_threshold = 20
    k_sell_threshold = 80

    signal = check_trade_signals(df, short_lwma_period, long_lwma_period, k_period, d_period, k_buy_threshold, k_sell_threshold)
    print(f"Trade Signal for {symbol}: {signal}")
    # Add your trade execution logic based on the signal here

def place_order(symbol, order_type, atr_value, atr_multiplier=1.5):
    """
    Places an order on the specified symbol using the minimum lot size, with TP and SL based on ATR,
    only if there are no open positions for the same symbol.
    
    :param symbol: Symbol to trade.
    :param order_type: "buy" or "sell".
    :param atr_value: Current ATR value for the symbol.
    :param atr_multiplier: Multiplier for the ATR to set the TP and SL.
    """
    # Check for existing positions for the symbol
    positions = mt5.positions_get(symbol=symbol)
    if positions:
        print(f"An open position for {symbol} already exists. No new orders will be placed.")
        return

    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None:
        print(f"{symbol} not found")
        return

    lot_size = symbol_info.lot_min
    point = symbol_info.point
    price = mt5.symbol_info_tick(symbol).ask if order_type == "buy" else mt5.symbol_info_tick(symbol).bid

    sl_points = atr_value * atr_multiplier
    tp_points = atr_value * atr_multiplier

    sl_price = price - sl_points / point if order_type == "buy" else price + sl_points / point
    tp_price = price + tp_points / point if order_type == "buy" else price - tp_points / point

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": lot_size,
        "type": mt5.ORDER_TYPE_BUY if order_type == "buy" else mt5.ORDER_TYPE_SELL,
        "price": price,
        "sl": sl_price,
        "tp": tp_price,
        "magic": 234000,
        "comment": "Python script open",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    
    result = mt5.order_send(request)
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print(f"Order failed, retcode={result.retcode}")
    else:
        print("Order placed successfully with TP and SL based on ATR")

# Example usage
atr_value = 0.005  # Example ATR value, replace with current ATR for your symbol

# Example: Place a buy order for 'Volatility 10 Index', replace with your symbol
place_order('Volatility 10 Index', 'buy', atr_value, atr_multiplier=1.5)



if __name__ == "__main__":
    main()
    mt5.shutdown()
