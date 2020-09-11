"""
    This example shows how to download and get tse tickers
    client types records specifically (as a 'Pandas DataFrame' object),
    and easily save them in .csv format.
"""
from pytse_client import download_client_types_records

if __name__ == '__main__':
    # Download all tickers clients types at once.
    # This function returns a dictionary.
    records_1 = download_client_types_records("all")

    # Download specific tickers client types records
    records_2 = download_client_types_records(["فولاد", "ذوب"])
    print(records_2["فولاد"])
    print("Fuldad: ", records_2["فولاد"], sep="\n")
    print("Zoob: ", records_2["ذوب"], sep="\n")

    # Download and save tickers client types records
    records_3 = download_client_types_records("فولاد", write_to_csv=True)
    print("Foolad:", records_3["فولاد"], sep="\n")
