TEST_PATH=./tests

unit_test:
	python -m unittest

e2e_test:
	python 	$(TEST_PATH)/test_download/download_all.py
