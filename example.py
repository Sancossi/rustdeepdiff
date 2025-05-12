import json
import time
from functools import wraps

from deepdiff import DeepDiff

from rustdeepdiff import deep_diff


def time_elapsed(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"Time elapsed: {end_time - start_time} seconds")
        return result

    return wrapper


def load_json(path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@time_elapsed
def test_rust_deep_diff():
    # Пример 1: Сравнение словарей
    dict1 = load_json("dict1.json")
    dict2 = load_json("dict2.json")

    diff = deep_diff(dict1, dict2)
    return diff


@time_elapsed
def test_python_deep_diff():
    dict1 = load_json("dict1.json")
    dict2 = load_json("dict2.json")

    diff = DeepDiff(dict1, dict2)
    return diff


diff1 = test_rust_deep_diff()
diff2 = test_python_deep_diff()
