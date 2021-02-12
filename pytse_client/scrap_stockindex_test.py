import pytest
import pandas as pd
from .scrap_stockindex import StockIndex



@pytest.fixture
def SI_instance():
    return StockIndex('http://www.tsetmc.com/Loader.aspx?ParTree=15131J&i=32097828799138957')

def test_history_df(SI_instance):
    df = SI_instance.index_history()
    assert isinstance(df, pd.DataFrame)

def test_history_df_correct_shape(SI_instance):
    df = SI_instance.index_history()
    assert (8, 4) == df.shape

def test_currentday_history_df(SI_instance):
    df = SI_instance.current_day_index_history()
    assert isinstance(df, pd.DataFrame)

def test_currentday_history_df_correct_shape(SI_instance):
    df = SI_instance.current_day_index_history()
    assert 5 == df.shape[1]