TEST_PATH=./tests

unit_test:
	poetry run python -m unittest

e2e_test:
	poetry run python 	$(TEST_PATH)/test_download/download_all.py
	poetry run python $(TEST_PATH)/test_ticker/ticker_e2e.py
