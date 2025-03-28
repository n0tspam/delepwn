import time
import logging
from googleapiclient.errors import HttpError
from delepwn.utils.output import print_color

def handle_api_ratelimit(func):
    """Decorator to handle API rate limiting with exponential backoff"""
    def wrapper(*args, **kwargs):
        max_retries = 5
        backoff_factor = 2
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except HttpError as e:
                if e.resp.status == 429:
                    sleep_time = backoff_factor ** (attempt + 1)
                    print_color(f"API rate limit exceeded. Retrying in {sleep_time} seconds...", color="yellow")
                    time.sleep(sleep_time)
                else:
                    raise
        print_color("Max retries exceeded for API rate limiting", color="red")
        raise
    return wrapper 