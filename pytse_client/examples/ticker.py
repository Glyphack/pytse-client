from pytse_client import Ticker, download

download(symbols="وبملت", write_to_csv=True)  # optional
ticker = Ticker("وبملت")
print(ticker.history)
