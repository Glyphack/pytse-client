import pandas as pd


class Ticker:
    def __init__(self):
        self._history = None

    def from_file(self, path):
        self._history = pd.read_csv(path)

    @property
    def history(self):
        return self._history
