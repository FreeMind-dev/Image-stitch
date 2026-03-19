"""
数学工具模块单元测试

测试 gcd、lcm、lcm_multiple 函数的正确性和边界情况。
"""

import pytest
from image_stitch.utils.math_utils import gcd, lcm, lcm_multiple


# ==================== gcd 测试 ====================

class TestGcd:
    """最大公约数函数测试"""

    def test_basic(self):
        """基本最大公约数计算"""
        assert gcd(12, 8) == 4

    def test_coprime(self):
        """互质数的 gcd 为 1"""
        assert gcd(7, 13) == 1

    def test_same_number(self):
        """相同数字的 gcd 为其本身"""
        assert gcd(5, 5) == 5

    def test_one_is_zero(self):
        """其中一个为 0 时，gcd 为另一个数"""
        assert gcd(0, 5) == 5
        assert gcd(5, 0) == 5

    def test_both_zero(self):
        """两个 0 的 gcd 为 0"""
        assert gcd(0, 0) == 0

    def test_one(self):
        """与 1 的 gcd 为 1"""
        assert gcd(1, 100) == 1

    def test_large_numbers(self):
        """大数的 gcd"""
        assert gcd(1000000, 500000) == 500000


# ==================== lcm 测试 ====================

class TestLcm:
    """最小公倍数函数测试"""

    def test_basic(self):
        """基本最小公倍数计算"""
        assert lcm(4, 6) == 12

    def test_coprime(self):
        """互质数的 lcm 为乘积"""
        assert lcm(7, 13) == 91

    def test_same_number(self):
        """相同数字的 lcm 为其本身"""
        assert lcm(5, 5) == 5

    def test_one_is_zero(self):
        """其中一个为 0 时，lcm 为 0"""
        assert lcm(0, 5) == 0
        assert lcm(5, 0) == 0

    def test_both_zero(self):
        """两个 0 的 lcm 为 0"""
        assert lcm(0, 0) == 0

    def test_one_is_multiple(self):
        """一个数是另一个的倍数时，lcm 为较大的数"""
        assert lcm(3, 9) == 9
        assert lcm(9, 3) == 9

    def test_large_numbers(self):
        """大数的 lcm"""
        assert lcm(100, 150) == 300


# ==================== lcm_multiple 测试 ====================

class TestLcmMultiple:
    """多整数最小公倍数函数测试"""

    def test_basic(self):
        """基本多数 lcm 计算"""
        assert lcm_multiple([4, 6, 8]) == 24

    def test_single(self):
        """单个数字的 lcm 为其本身"""
        assert lcm_multiple([7]) == 7

    def test_two_numbers(self):
        """两个数字等价于 lcm"""
        assert lcm_multiple([4, 6]) == lcm(4, 6)

    def test_empty_list(self):
        """空列表返回 0"""
        assert lcm_multiple([]) == 0

    def test_with_one(self):
        """包含 1 不影响结果"""
        assert lcm_multiple([1, 4, 6]) == 12

    def test_all_same(self):
        """全部相同的数"""
        assert lcm_multiple([5, 5, 5]) == 5

    def test_contains_zero(self):
        """包含 0 时结果为 0"""
        assert lcm_multiple([4, 0, 6]) == 0

    def test_three_coprimes(self):
        """三个互质数的 lcm 为乘积"""
        assert lcm_multiple([2, 3, 5]) == 30
