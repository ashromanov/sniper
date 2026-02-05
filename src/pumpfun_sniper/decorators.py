"""Decorators for timing and logging functions."""

import functools
import time
from collections.abc import Callable, Coroutine
from typing import ParamSpec, TypeVar

from loguru import logger

P = ParamSpec("P")
R = TypeVar("R")


def timed(func: Callable[P, R]) -> Callable[P, R]:
    """Decorator to measure and log synchronous function execution time.

    Args:
        func: Function to wrap.

    Returns:
        Wrapped function with timing.
    """

    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        start = time.perf_counter()
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            elapsed = (time.perf_counter() - start) * 1000
            logger.debug(f"{func.__name__} completed in {elapsed:.2f}ms")

    return wrapper


def async_timed(
    func: Callable[P, Coroutine[object, object, R]],
) -> Callable[P, Coroutine[object, object, R]]:
    """Decorator to measure and log async function execution time.

    Args:
        func: Async function to wrap.

    Returns:
        Wrapped async function with timing.
    """

    @functools.wraps(func)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        start = time.perf_counter()
        try:
            result = await func(*args, **kwargs)
            return result
        finally:
            elapsed = (time.perf_counter() - start) * 1000
            logger.debug(f"{func.__name__} completed in {elapsed:.2f}ms")

    return wrapper
