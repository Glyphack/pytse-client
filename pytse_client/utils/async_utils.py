import asyncio
import time
from typing import List


async def run_tasks_with_wait(tasks: List, chunk_size: int, wait_between: int):
    """
    This function runs async tasks chunk by chunk and
    wait after completing each chunk
    """
    chunks = chunk_it(tasks, chunk_size)
    final_result = []
    for chunk in chunks:
        final_result.extend(await asyncio.gather(*chunk))
        time.sleep(wait_between)
    return final_result


def chunk_it(list_to_split, chunk_size):
    list_of_chunks = []
    start_chunk = 0
    end_chunk = start_chunk + chunk_size
    while end_chunk <= len(list_to_split) + chunk_size:
        chunk_ls = list_to_split[start_chunk:end_chunk]
        list_of_chunks.append(chunk_ls)
        start_chunk = start_chunk + chunk_size
        end_chunk = end_chunk + chunk_size
    return list_of_chunks
