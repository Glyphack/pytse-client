from pytse_client import Ticker, download

download(symbols="all", write_to_csv=True)
ticker = Ticker("وبملت")
ticker.from_file()
print(ticker.history)
ticker.from_web()
print(ticker.history)
