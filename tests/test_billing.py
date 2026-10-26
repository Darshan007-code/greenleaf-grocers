import pytest
from app.services.billing_service import BillingService, BillingException
from app.models import Product, Sale, SaleItem
from app.database import db

def test_successful_checkout_and_stock_deduction(app, sample_users, sample_products):
    """Test successful checkout creates sale and decrements product inventory."""
    cashier = sample_users['cashier']
    apples = sample_products['apples']
    initial_stock = apples.stock_qty  # 50

    items = [{'product_id': apples.product_id, 'quantity': 5}]
    sale = BillingService.process_checkout(
        user_id=cashier.user_id,
        items=items,
        discount=1.00,
        payment_method='Cash',
        customer_name='Sarah Jenkins'
    )

    assert sale.sale_id is not None
    assert sale.subtotal == 15.00  # 5 * 3.00
    assert sale.discount == 1.00
    assert sale.total_amount == 14.00
    assert sale.customer_name == 'Sarah Jenkins'

    # Verify inventory was decremented
    updated_apples = db.session.get(Product, apples.product_id)
    assert updated_apples.stock_qty == initial_stock - 5  # 45

def test_prevent_selling_more_than_available_stock(app, sample_users, sample_products):
    """Test overdraw protection: reject purchase when requested qty > available stock."""
    cashier = sample_users['cashier']
    milk = sample_products['milk']  # Stock is 8

    items = [{'product_id': milk.product_id, 'quantity': 10}]  # Requests 10
    with pytest.raises(BillingException) as excinfo:
        BillingService.process_checkout(
            user_id=cashier.user_id,
            items=items
        )

    assert "Insufficient stock" in str(excinfo.value)
    # Ensure stock was not changed
    assert db.session.get(Product, milk.product_id).stock_qty == 8

def test_reject_negative_or_zero_quantity(app, sample_users, sample_products):
    """Test reject negative or zero item quantities."""
    cashier = sample_users['cashier']
    apples = sample_products['apples']

    with pytest.raises(BillingException) as excinfo_neg:
        BillingService.process_checkout(
            user_id=cashier.user_id,
            items=[{'product_id': apples.product_id, 'quantity': -2}]
        )
    assert "must be positive integers" in str(excinfo_neg.value)

    with pytest.raises(BillingException) as excinfo_zero:
        BillingService.process_checkout(
            user_id=cashier.user_id,
            items=[{'product_id': apples.product_id, 'quantity': 0}]
        )
    assert "must be positive integers" in str(excinfo_zero.value)

def test_reject_empty_cart(app, sample_users):
    """Test reject checkout when shopping cart is empty."""
    cashier = sample_users['cashier']
    with pytest.raises(BillingException) as excinfo:
        BillingService.process_checkout(user_id=cashier.user_id, items=[])
    assert "cart is empty" in str(excinfo.value)

def test_discount_cannot_exceed_subtotal(app, sample_users, sample_products):
    """Test reject discount larger than order subtotal."""
    cashier = sample_users['cashier']
    apples = sample_products['apples']

    items = [{'product_id': apples.product_id, 'quantity': 1}]  # subtotal = 3.00
    with pytest.raises(BillingException) as excinfo:
        BillingService.process_checkout(
            user_id=cashier.user_id,
            items=items,
            discount=10.00
        )
    assert "cannot exceed subtotal" in str(excinfo.value)

def test_invoice_number_format(app, sample_users, sample_products):
    """Test invoice number follows format GL-YYYYMMDD-XXXX."""
    cashier = sample_users['cashier']
    apples = sample_products['apples']
    sale = BillingService.process_checkout(
        user_id=cashier.user_id,
        items=[{'product_id': apples.product_id, 'quantity': 1}]
    )
    assert sale.invoice_no.startswith("GL-")
    parts = sale.invoice_no.split("-")
    assert len(parts) == 3
    assert len(parts[1]) == 8  # YYYYMMDD
    assert len(parts[2]) == 4  # 0001

def test_checkout_api_endpoint(client, sample_users, sample_products):
    """Test POS checkout JSON API endpoint."""
    client.post('/login', data={'username': 'cashier_test', 'password': 'cashierpass123'})
    payload = {
        'items': [{'product_id': sample_products['apples'].product_id, 'quantity': 2}],
        'discount': 0.50,
        'payment_method': 'Card',
        'customer_name': 'David Test'
    }
    response = client.post('/billing/api/checkout', json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert 'sale_id' in data
    assert 'invoice_no' in data
    assert data['total_amount'] == 5.50  # 2 * 3.00 - 0.50

def test_pdf_receipt_download(client, sample_users, sample_products):
    """Test downloading PDF receipt for a completed sale."""
    client.post('/login', data={'username': 'cashier_test', 'password': 'cashierpass123'})
    # Create a sale first
    sale = BillingService.process_checkout(
        user_id=sample_users['cashier'].user_id,
        items=[{'product_id': sample_products['apples'].product_id, 'quantity': 1}]
    )
    response = client.get(f'/billing/receipt/{sale.sale_id}/pdf')
    assert response.status_code == 200
    assert response.mimetype == 'application/pdf'
