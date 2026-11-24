import unittest
from src.discount import apply_discount


class TestDiscount(unittest.TestCase):
    def test_ten_percent(self):
        self.assertEqual(apply_discount(100, 10), 90.0)


if __name__ == "__main__":
    unittest.main()
