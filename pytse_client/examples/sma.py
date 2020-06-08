import pytse_client as tse

ticker = tse.Ticker("وبملت")
history = ticker.history


def sma(series, periods: int, ):
    return series.rolling(window=periods, min_periods=periods).mean()


sma_10 = sma(history.close, 10)
sma_20 = sma(history.close, 20)
buy_signals = (
        (sma_10 > sma_20) &
        (sma_20.shift(1) > sma_10.shift(1))
)
print(buy_signals.tail(60))
