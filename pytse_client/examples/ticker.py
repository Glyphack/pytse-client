from pytse_client import Ticker, download

download(symbols="وبملت", write_to_csv=True)  # optional
ticker = Ticker("وبملت")
print(ticker.history)
print(ticker.title)
print(ticker.url)
print(ticker.group_name)
print(ticker.eps)
print(ticker.p_e_ratio)
print(ticker.group_p_e_ratio)
print(ticker.base_volume)
