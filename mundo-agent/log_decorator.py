import functools
import logging
import time
from typing import Any, Callable

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def log_call(func: Callable) -> Callable:
    """记录函数调用：函数名、参数、耗时。"""

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        arg_repr = ", ".join(
            [repr(a) for a in args] + [f"{k}={v!r}" for k, v in kwargs.items()]
        )
        logger.info("CALL  %s(%s)", func.__name__, arg_repr)

        start = time.perf_counter()
        try:
            result = func(*args, **kwargs)
            return result
        except Exception as exc:
            logger.exception("FAIL  %s -> %s: %s", func.__name__, type(exc).__name__, exc)
            raise
        finally:
            elapsed = time.perf_counter() - start
            logger.info("END   %s  [%.4fs]", func.__name__, elapsed)

    return wrapper


# ---------- 示例 ----------
@log_call
def add(a: int, b: int) -> int:
    return a + b


@log_call
def greet(name: str, greeting: str = "Hello") -> str:
    return f"{greeting}, {name}!"


if __name__ == "__main__":
    add(1, 2)
    greet("Alice", greeting="Hi")
