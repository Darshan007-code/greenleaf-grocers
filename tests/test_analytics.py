from datetime import date, timedelta
from app.services.analytics import AnalyticsService
from app.services.billing_service import BillingService
from app.models import Product, Sale, SaleItem

def test_kpi_calculations_with_sales(app, sample_users, sample_products):
    """Test AnalyticsService KPI output with known sales."""
    cashier = sample_users['cashier']
    apples = sample_products['apples']
    milk = sample_products['milk']

    # Sale 1: 2 Apples ($6.00)
    BillingService.process_checkout(
        user_id=cashier.user_id,
        items=[{'product_id': apples.product_id, 'quantity': 2}],
        discount=0.0
    )

    # Sale 2: 1 Milk ($4.50) with $0.50 discount -> $4.00
    BillingService.process_checkout(
        user_id=cashier.user_id,
        items=[{'product_id': milk.product_id, 'quantity': 1}],
        discount=0.50
    )

    kpis = AnalyticsService.get_kpis()
    assert kpis['total_bills'] == 2
    assert kpis['total_revenue'] == 10.00  # 6.00 + 4.00
    assert kpis['avg_bill_value'] == 5.00  # 10.00 / 2
    # Product milk has stock 7 <= reorder 10, yogurt has stock 5 <= 5 -> at least 2 low-stock
    assert kpis['low_stock_count'] >= 2

def test_daily_sales_aggregation(app, sample_users, sample_products):
    """Test daily revenue and bills aggregation."""
    cashier = sample_users['cashier']
    apples = sample_products['apples']

    BillingService.process_checkout(
        user_id=cashier.user_id,
        items=[{'product_id': apples.product_id, 'quantity': 3}]
    )

    daily = AnalyticsService.get_daily_sales()
    assert len(daily) >= 1
    today_str = date.today().strftime('%Y-%m-%d')
    today_record = [d for d in daily if d['date'] == today_str]
    assert len(today_record) == 1
    assert today_record[0]['revenue'] == 9.00  # 3 * 3.00

def test_top_products_sorting(app, sample_users, sample_products):
    """Test top products ranking by revenue and quantity."""
    cashier = sample_users['cashier']
    apples = sample_products['apples']  # $3.00
    milk = sample_products['milk']      # $4.50

    # Sell 5 apples ($15) and 1 milk ($4.50)
    BillingService.process_checkout(
        user_id=cashier.user_id,
        items=[{'product_id': apples.product_id, 'quantity': 5}]
    )
    BillingService.process_checkout(
        user_id=cashier.user_id,
        items=[{'product_id': milk.product_id, 'quantity': 1}]
    )

    top_rev = AnalyticsService.get_top_products(sort_by='revenue')
    assert len(top_rev) >= 2
    assert top_rev[0]['product_name'] == 'Organic Apples'
    assert top_rev[0]['total_rev'] == 15.00

    top_qty = AnalyticsService.get_top_products(sort_by='quantity')
    assert top_qty[0]['product_name'] == 'Organic Apples'
    assert top_qty[0]['total_qty'] == 5

def test_category_sales_distribution(app, sample_users, sample_products):
    """Test category revenue share percentage."""
    cashier = sample_users['cashier']
    apples = sample_products['apples']  # Fresh Produce: $3.00

    BillingService.process_checkout(
        user_id=cashier.user_id,
        items=[{'product_id': apples.product_id, 'quantity': 2}]
    )

    cats = AnalyticsService.get_category_sales()
    assert len(cats) >= 1
    produce_cat = [c for c in cats if c['category'] == 'Fresh Produce'][0]
    assert produce_cat['total_revenue'] == 6.00
    assert produce_cat['revenue_share'] == 100.0  # Only produce sold

def test_slow_moving_products_detection(app, sample_users, sample_products):
    """Test slow moving products detection for items with no sales."""
    # Yogurt was not sold
    slow_movers = AnalyticsService.get_slow_moving_products(days=30)
    slow_names = [sm['name'] for sm in slow_movers]
    assert 'Past Expired Yogurt' in slow_names
