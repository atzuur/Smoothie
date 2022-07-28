"""
All weighting functions are of the following basic form:
    Args:
        frames: `int` | number of frames to generate

    Returns:
        `list[float]`: `[w1, w2, ..., wn]` | weights for each frame

Reference:
    https://github.com/siveroo/HFR-Resampler
"""

import math
import warnings as w
from numbers import Number
from typing import Sequence


Vector = Sequence[Number]
"""
Sequence of any length containing numbers

Has to support:
    `len(seq)`, `seq.__getitem__()`, `for i in seq: ...`
"""


def normalize(weights: list):
    """
    Normalize a list of weights to sum to 1
    """
    tot = sum(weights)
    return [weight / tot for weight in weights]


def scale_range(n: int, start: Number, end: Number):
    """
    Returns a list of `n` numbers from `start` to `end`
    >>> result == [start, ..., end]
    >>> len(result) == n
    """
    return [(x * (end - start) / (n - 1)) + start for x in range(n)]


def ascending(frames: int):
    """
    Linear ascending curve
    """
    val = [x for x in range(1, frames + 1)]
    return normalize(val)


def descending(frames: int):
    """
    Linear descending curve
    """
    val = [x for x in range(frames, 0, -1)]
    return normalize(val)


def equal(frames: int):
    """
    Flat curve
    """
    return [1 / frames] * frames


def gaussian(frames: int, apex: Number = 1, std_dev: Number = 1, bound: tuple[float, float] = (0, 2)):
    """
    Args:
        bound: `[a, b]` | x axis vector from `a` to `b`
        apex: `μ`       | the position of the center of the peak, relative to x axis vector
        std_dev: `σ`    | width of the "bell", higher == broader / flatter

    Reference:
        https://en.wikipedia.org/wiki/Gaussian_function
    """
    _warn_bound(bound, "gaussian")

    r = scale_range(frames, bound[0], bound[1]) # x axis vector

    val = [1 / (math.sqrt(2 * math.pi) * std_dev) # normalization
           * math.exp(-((x - apex) / std_dev) ** 2 / 2) # gaussian function
           for x in r]

    return normalize(val)


def gaussian_sym(frames: int, std_dev: Number = 1, bound: tuple[float, float] = (0, 2)):
    """
    Same as `gaussian()` but symmetric;
    the peak (apex) will always be at the center of the curve
    """
    _warn_bound(bound, "gaussian_sym")

    max_abs = max(bound)
    r = scale_range(frames, -max_abs, max_abs)

    val = [1 / (math.sqrt(2 * math.pi) * std_dev)
           * math.exp(-(x / std_dev) ** 2 / 2)
           for x in r]

    return normalize(val)


def pyramid(frames: int):
    """
    Symmetric pyramid function
    """
    half = (frames - 1) / 2
    val = [half - abs(x - half) + 1 for x in range(frames)]

    return normalize(val)


def func_eval(func: str, nums: Vector):
    """
    Run an operation on a sequence of numbers

    Names allowed in `func`:
        - Everything in the `math` module
        - `x`: the current number (frame) in the sequence
        - `frames` (`len(nums)`): number of elements in the sequence (blended frames)
        - The following built-in functions: `sum`, `abs`, `max`, `min`, `len`, `pow`, `range`, `round`
    """

    # math functions + math related builtins
    namespace = {k:v for k, v in math.__dict__.items() if not k.startswith("_")}
    namespace |= {
        'frames': len(nums), # total number of items (frames)
        'x': None, # iterator for nums
        '__builtins__': {
            'sum': sum,
            'abs': abs,
            'max': max,
            'min': min,
            'len': len,
            'pow': pow,
            'range': range,
            'round': round
        }
    }
    # only allow functions specified in namespace
    return eval(f"[({func}) for x in {nums}]", namespace)


def custom(frames: int, func: str = "", bound: tuple[float, float] = (0, 1)):
    """
    Arbitrary custom weighting function
    """
    _warn_bound(bound, func)

    r = scale_range(frames, bound[0], bound[1])
    val = func_eval(func, r)

    return normalize(val)


def divide(frames: int, weights: Vector):
    """
    Stretch the given array (weights) to a specific length (frames)
    Example: `frames = 10; weights = [1, 2]`
    Result: `val == [1, 1, 1, 1, 1, 2, 2, 2, 2, 2]`, then normalize it to
    `[0.0667, 0.0667, 0.0667, 0.0667, 0.0667, 0.1333, 0.1333, 0.1333, 0.1333, 0.1333]`
    """
    r = scale_range(frames, 0, len(weights) - 0.1)
    val = [weights[int(r[x])] for x in range(frames)]

    return normalize(val)


def _warn_bound(bound: tuple, func: str):
    if len(bound) < 2:
        raise ValueError(f"{func}: bound must be a tuple of length 2, got {bound}")
    elif len(bound) > 2:
        w.warn(f"{func}: bound was given as a tuple of length {len(bound)}, only the first two values will be used",
               RuntimeWarning)
