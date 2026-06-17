"""Unit tests for the data-quality rules used by the Silver layer.

These mirror the validation logic in
`databricks/silver/02_silver_transformation.py` and run without a Spark
session so they execute in the Azure DevOps "Unit Tests" stage.
"""
import re

EMAIL_REGEX = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"


def is_valid_email(email):
    return email is not None and re.match(EMAIL_REGEX, email) is not None


def is_valid_order(amount, quantity, customer_exists):
    return amount is not None and amount > 0 and quantity > 0 and customer_exists


def test_valid_email():
    assert is_valid_email("alice@example.com")


def test_null_email_invalid():
    assert not is_valid_email(None)


def test_malformed_email_invalid():
    assert not is_valid_email("frank-invalid-email")
    assert not is_valid_email("a@b")


def test_order_amount_must_be_positive():
    assert not is_valid_order(0, 1, True)
    assert not is_valid_order(-5, 1, True)
    assert is_valid_order(10, 1, True)


def test_order_requires_existing_customer():
    assert not is_valid_order(10, 1, False)


def test_order_quantity_must_be_positive():
    assert not is_valid_order(10, 0, True)
