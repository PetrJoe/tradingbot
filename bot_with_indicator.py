import pandas as pd
import numpy as np
import MetaTrader5 as mt5

broker_server = 'your_broker_server'
login = "your_login"
password = 'your_password'


def fetch_historical_data_from_mt5(symbol):
    """Fetch historical data using MetaTrader 5."""
    if not mt5.initialize(login=login, server=broker_server, password=password):
        print("Failed to connect to MetaTrader 5 terminal")
        mt5.shutdown()
        return None
    else:
        print("Connected to MetaTrader 5 terminal")

        # Fetch historical data for the specified symbol
        rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 100)

        mt5.shutdown()
        df = pd.DataFrame(rates)
        # Convert time in seconds into the datetime format
        df['time'] = pd.to_datetime(df['time'], unit='s')
        return df

def moving_average_crossover_strategy(df, short_window=10, long_window=50):
    """Calculate moving averages and generate signals."""
    df['short_mavg'] = df['close'].rolling(window=short_window, min_periods=1).mean()
    df['long_mavg'] = df['close'].rolling(window=long_window, min_periods=1).mean()

    df['signal'] = 0
    df['signal'][short_window:] = np.where(df['short_mavg'][short_window:] > df['long_mavg'][short_window:], 1, 0)
    df['positions'] = df['signal'].diff()

    return df


def stochastic_oscillator(df, k_window=14, d_window=3):
    """Calculate Stochastic Oscillator %K and %D."""
    low_min = df['low'].rolling(window=k_window, min_periods=1).min()
    high_max = df['high'].rolling(window=k_window, min_periods=1).max()

    df['%K'] = ((df['close'] - low_min) / (high_max - low_min)) * 100
    df['%D'] = df['%K'].rolling(window=d_window, min_periods=1).mean()

    return df


def execute_trade(signal, symbol, quantity, df):
    """Execute trade using MetaTrader 5, considering overbought/oversold conditions."""
    if signal == 1 and df.iloc[-1]['%D'] < 20:
        print(f"Placing buy order for {quantity} units of {symbol} (oversold condition)")
        # Place buy order using MT5
    elif signal == -1 and df.iloc[-1]['%D'] > 80:
        print(f"Placing sell order for {quantity} units of {symbol} (overbought condition)")
        # Place sell order using MT5


def main():
    symbol = 'EURUSD'

    df = fetch_historical_data_from_mt5(symbol)

    if df is not None:
        df = stochastic_oscillator(df)
        df_with_signals = moving_average_crossover_strategy(df)

        # Check the last row for the latest signal
        latest_signal = df_with_signals.iloc[-1]['positions']
        execute_trade(latest_signal, symbol, quantity=10, df=df_with_signals)


if __name__ == "__main__":
    main()
