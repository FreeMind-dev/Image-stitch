"""
数学工具模块

提供帧同步所需的数学计算函数。
"""

from math import gcd as _gcd
from typing import List
from functools import reduce


def gcd(a: int, b: int) -> int:
    """
    计算两个整数的最大公约数

    参数:
        a: 第一个整数
        b: 第二个整数

    返回:
        最大公约数
    """
    return _gcd(a, b)


def lcm(a: int, b: int) -> int:
    """
    计算两个整数的最小公倍数

    参数:
        a: 第一个整数
        b: 第二个整数

    返回:
        最小公倍数
    """
    if a == 0 or b == 0:
        return 0
    return abs(a * b) // gcd(a, b)


def lcm_multiple(numbers: List[int]) -> int:
    """
    计算多个整数的最小公倍数

    参数:
        numbers: 整数列表

    返回:
        所有数的最小公倍数

    示例:
        >>> lcm_multiple([4, 6, 8])
        24
    """
    if not numbers:
        return 0
    return reduce(lcm, numbers)
