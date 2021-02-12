import pytest, os.path
from .scrap import MainPageInfo


@pytest.fixture
def mpi_instance():
    return MainPageInfo()

@pytest.fixture
def test_returns_high_transaction_data(mpi_instance):
    headers, rows = mpi_instance.high_transaction_data()
    assert len(headers) == len(rows[0])

def test_returns_effiency_data(mpi_instance):
    headers, rows = mpi_instance.chosen_stock_index_data()
    assert len(headers) == len(rows[0])

def test_makes_file_high_transaction(mpi_instance):
    path = mpi_instance.high_transaction_csv()
    assert os.path.exists(path)
