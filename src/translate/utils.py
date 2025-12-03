
import os
from typing import List, Union, Callable

import tiktoken
from dotenv import load_dotenv
from icecream import ic
from langchain_text_splitters import RecursiveCharacterTextSplitter

import logging


logging.basicConfig(level=logging.DEBUG)

load_dotenv()  # read local .env file

MAX_TOKENS_PER_CHUNK = (
    1000  # if text is more than this many tokens, we'll break it up into
)


def num_tokens_in_string(
    input_str: str, encoding_name: str = "cl100k_base"
) -> int:
    logging.debug(f"Entering num_tokens_in_string with input_str: {input_str[:50]}..., encoding_name: {encoding_name}")
    """
    Calculate the number of tokens in a given string using a specified encoding.

    Args:
        str (str): The input string to be tokenized.
        encoding_name (str, optional): The name of the encoding to use. Defaults to "cl100k_base",
            which is the most commonly used encoder (used by GPT-4).

    Returns:
        int: The number of tokens in the input string.

    Example:
        >>> text = "Hello, how are you?"
        >>> num_tokens = num_tokens_in_string(text)
        >>> print(num_tokens)
        5
    """
    # 显示环境变量TIKTOKEN_CACHE_DIR的值
    # tiktoken_cache_dir = "./tiktoken_cache_dir" 
    # os.environ["TIKTOKEN_CACHE_DIR"] = tiktoken_cache_dir
    encoding = tiktoken.get_encoding(encoding_name)
    num_tokens = len(encoding.encode(input_str))
    return num_tokens



def calculate_chunk_size(token_count: int, token_limit: int) -> int:
    logging.debug(f"Entering calculate_chunk_size with token_count: {token_count}, token_limit: {token_limit}")
    """
    Calculate the chunk size based on the token count and token limit.

    Args:
        token_count (int): The total number of tokens.
        token_limit (int): The maximum number of tokens allowed per chunk.

    Returns:
        int: The calculated chunk size.

    Description:
        This function calculates the chunk size based on the given token count and token limit.
        If the token count is less than or equal to the token limit, the function returns the token count as the chunk size.
        Otherwise, it calculates the number of chunks needed to accommodate all the tokens within the token limit.
        The chunk size is determined by dividing the token limit by the number of chunks.
        If there are remaining tokens after dividing the token count by the token limit,
        the chunk size is adjusted by adding the remaining tokens divided by the number of chunks.

    Example:
        >>> calculate_chunk_size(1000, 500)
        500
        >>> calculate_chunk_size(1530, 500)
        389
        >>> calculate_chunk_size(2242, 500)
        496
    """

    if token_count <= token_limit:
        return token_count

    num_chunks = (token_count + token_limit - 1) // token_limit
    chunk_size = token_count // num_chunks

    remaining_tokens = token_count % token_limit
    if remaining_tokens > 0:
        chunk_size += remaining_tokens // num_chunks

    return chunk_size
