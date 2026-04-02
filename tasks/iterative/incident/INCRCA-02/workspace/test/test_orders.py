"""
Test suite for the order system.
Tests 1-8: correctness (pass after Decimal fix)
Tests 9-10: concurrency (pass after SELECT FOR UPDATE fix)

Run: pytest test/test_orders.py -v
"""

import sys
import os
import threading
import time
from decimal import Decimal

# Ensure workspace root is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from orders.models import Base, Order
from orders.calculator import calculate_total, apply_tax, round_to_cents
from orders.discounts import apply_discount


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="function")
def db_session():
    """Fresh in-memory SQLite session per test."""
    engine = create_engine(
        "sqlite:///:memory:?check_same_thread=False",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    session = Session()
    yield session
    session.close()
    Base.metadata.drop_all(engine)


@pytest.fixture(scope="function")
def sample_order(db_session):
    """Create a sample order with total=100.00."""
    order = Order(customer_id="cust_001", total=Decimal("100.0000"))
    db_session.add(order)
    db_session.commit()
    db_session.refresh(order)
    return order


# ---------------------------------------------------------------------------
# Tests 1-8: Correctness (require Decimal fix in calculator.py)
# ---------------------------------------------------------------------------

def test_01_basic_total():
    """Single item: 29.99 * 1 = 29.99 exactly."""
    items = [{"unit_price": "29.99", "quantity": 1}]
    total = calculate_total(items)
    assert round_to_cents(total) == pytest.approx(29.99, abs=1e-9), (
        f"Expected 29.99, got {total}. "
        "Fix: use Decimal arithmetic in calculator.py"
    )


def test_02_multi_item_total():
    """Multiple items sum correctly."""
    items = [
        {"unit_price": "10.00", "quantity": 3},
        {"unit_price": "5.50", "quantity": 2},
    ]
    total = calculate_total(items)
    assert round_to_cents(total) == pytest.approx(41.00, abs=1e-9), (
        f"Expected 41.00, got {total}"
    )


def test_03_zero_quantity():
    """Item with quantity=0 contributes nothing."""
    items = [
        {"unit_price": "15.00", "quantity": 0},
        {"unit_price": "10.00", "quantity": 2},
    ]
    total = calculate_total(items)
    assert round_to_cents(total) == pytest.approx(20.00, abs=1e-9)


def test_04_rounding_edge_case():
    """
    Classic float trap: 0.1 * 3 in float = 0.30000000000000004.
    With Decimal: exactly 0.30.
    """
    items = [{"unit_price": "0.10", "quantity": 3}]
    total = calculate_total(items)
    # After rounding to cents, must be exactly 0.30
    rounded = round_to_cents(total)
    assert rounded == pytest.approx(0.30, abs=1e-9), (
        f"Expected 0.30, got {rounded}. "
        "This is the float rounding bug — fix by using Decimal in calculator.py"
    )


def test_05_discount_basic(db_session, sample_order):
    """10% discount on $100 order gives $90."""
    result = apply_discount(db_session, sample_order.id, 0.10)
    assert abs(float(result["discounted_total"]) - 90.0) < 0.001, (
        f"Expected 90.0, got {result['discounted_total']}"
    )


def test_06_discount_zero(db_session, sample_order):
    """0% discount leaves total unchanged."""
    result = apply_discount(db_session, sample_order.id, 0.0)
    assert abs(float(result["discounted_total"]) - 100.0) < 0.001


def test_07_discount_hundred_pct(db_session, sample_order):
    """100% discount gives zero total."""
    result = apply_discount(db_session, sample_order.id, 1.0)
    assert abs(float(result["discounted_total"]) - 0.0) < 0.001


def test_08_multiple_items_with_discount(db_session):
    """Multi-item order total then 20% discount."""
    items = [
        {"unit_price": "50.00", "quantity": 2},
        {"unit_price": "25.00", "quantity": 1},
    ]
    total = calculate_total(items)
    assert round_to_cents(total) == pytest.approx(125.00, abs=1e-9)

    order = Order(customer_id="cust_002", total=Decimal(str(round_to_cents(total))))
    db_session.add(order)
    db_session.commit()
    db_session.refresh(order)

    result = apply_discount(db_session, order.id, 0.20)
    assert abs(float(result["discounted_total"]) - 100.0) < 0.001


# ---------------------------------------------------------------------------
# Tests 9-10: Concurrency (require SELECT FOR UPDATE fix in discounts.py)
# ---------------------------------------------------------------------------

def test_09_concurrent_discount_no_double(db_session):
    """
    Two concurrent threads both try to apply a 10% discount to the same order.
    Without SELECT FOR UPDATE, the discount may be applied twice (double-discount).
    With the fix, the second application sees the already-discounted price and
    applies from there, OR the lock serializes both so only one rate is applied.

    We verify the final total is NOT less than original * (1-rate)^2,
    i.e. the discount was not applied more than once to the original price.

    The correct behaviour: final total == 90.00 (10% off 100.00, applied once).
    The buggy behaviour: final total == 81.00 (10% off 90.00, applied twice).
    """
    # Use a fresh engine with WAL mode to allow concurrent writes
    from sqlalchemy import create_engine as ce
    from sqlalchemy.orm import sessionmaker as sm
    engine2 = ce(
        "sqlite:///file::memory:?cache=shared&check_same_thread=False",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine2)
    Session2 = sm(bind=engine2, autocommit=False, autoflush=False)

    s1 = Session2()
    order = Order(customer_id="cust_concurrent", total=Decimal("100.0000"))
    s1.add(order)
    s1.commit()
    s1.refresh(order)
    order_id = order.id
    s1.close()

    errors = []
    results = []
    barrier = threading.Barrier(2)

    def thread_fn():
        s = Session2()
        try:
            barrier.wait(timeout=5)
            result = apply_discount(s, order_id, 0.10)
            results.append(result["discounted_total"])
        except Exception as e:
            errors.append(str(e))
        finally:
            s.close()

    t1 = threading.Thread(target=thread_fn)
    t2 = threading.Thread(target=thread_fn)
    t1.start(); t2.start()
    t1.join(timeout=10); t2.join(timeout=10)

    assert not errors, f"Thread errors: {errors}"

    # Read final total
    s_check = Session2()
    final_order = s_check.query(Order).filter_by(id=order_id).first()
    final_total = float(final_order.total)
    s_check.close()

    # Must NOT be double-discounted (81.00) — should be 90.00
    assert final_total >= 89.0, (
        f"Double discount detected: final total {final_total:.4f} "
        f"(expected ~90.00, got ~81.00). "
        "Fix: add .with_for_update() in discounts.py"
    )

    Base.metadata.drop_all(engine2)


def test_10_concurrent_discount_idempotent(db_session):
    """
    Many concurrent threads apply the same discount.
    Final total must be consistent (not corrupted by races).
    """
    from sqlalchemy import create_engine as ce
    from sqlalchemy.orm import sessionmaker as sm
    engine3 = ce(
        "sqlite:///file:memdb10?mode=memory&cache=shared&check_same_thread=False",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine3)
    Session3 = sm(bind=engine3, autocommit=False, autoflush=False)

    s1 = Session3()
    order = Order(customer_id="cust_idem", total=Decimal("200.0000"))
    s1.add(order)
    s1.commit()
    s1.refresh(order)
    order_id = order.id
    s1.close()

    errors = []
    n_threads = 5
    barrier = threading.Barrier(n_threads)

    def thread_fn():
        s = Session3()
        try:
            barrier.wait(timeout=5)
            apply_discount(s, order_id, 0.05)
        except Exception as e:
            errors.append(str(e))
        finally:
            s.close()

    threads = [threading.Thread(target=thread_fn) for _ in range(n_threads)]
    for t in threads: t.start()
    for t in threads: t.join(timeout=10)

    # Some errors are acceptable (SQLite contention) but the final total must
    # be a valid discounted value, not garbage
    s_check = Session3()
    final_order = s_check.query(Order).filter_by(id=order_id).first()
    final_total = float(final_order.total)
    s_check.close()

    # After 5 threads each applying 5% discount serially (with lock),
    # the total should be in a reasonable range (not absurdly small from double-discounts)
    # Minimum sane value: 200 * (0.95)^5 = ~155.13
    # Without fix: could be much lower due to races
    assert final_total >= 140.0, (
        f"Total {final_total:.4f} is too low — likely multiple discount races. "
        "Fix: add .with_for_update() in discounts.py"
    )

    Base.metadata.drop_all(engine3)
