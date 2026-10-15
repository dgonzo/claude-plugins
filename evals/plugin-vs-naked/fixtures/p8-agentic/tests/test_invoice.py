import unittest

from invoicing.invoice import invoice_total_cents
from invoicing.money import to_cents


class InvoiceTest(unittest.TestCase):
    def test_to_cents_exact(self):
        self.assertEqual(to_cents("19.99"), 1999)
        self.assertEqual(to_cents("0.29"), 29)
        self.assertEqual(to_cents("4.35"), 435)

    def test_invoice_ca(self):
        self.assertEqual(invoice_total_cents([("19.99", 3), ("4.35", 2)], "CA"), 7365)

    def test_invoice_oregon(self):
        self.assertEqual(invoice_total_cents([("0.29", 10)], "OR"), 290)


if __name__ == "__main__":
    unittest.main()
