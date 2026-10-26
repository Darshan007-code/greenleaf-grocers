from datetime import date, timedelta
from app.models import Product
from app.database import db

def test_product_model_properties(sample_products):
    """Test is_low_stock, is_expired, and is_near_expiry helper properties."""
    apples = sample_products['apples']
    milk = sample_products['milk']
    yogurt = sample_products['yogurt']

    assert apples.is_low_stock is False
    assert apples.is_expired is False

    assert milk.is_low_stock is True  # stock 8 <= reorder 10
    assert milk.is_near_expiry(days=15) is True  # 5 days away

    assert yogurt.is_expired is True
    assert yogurt.days_until_expiry < 0

def test_add_product_valid(client, sample_users):
    """Test successfully adding a product via admin form."""
    client.post('/login', data={'username': 'admin_test', 'password': 'adminpass123'})
    response = client.post('/products/add', data={
        'name': 'Organic Bananas',
        'category': 'Fresh Produce',
        'unit_price': '1.99',
        'cost_price': '0.99',
        'stock_qty': '40',
        'reorder_level': '15',
        'barcode': '999888777666'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Organic Bananas' in response.data

    prod = Product.query.filter_by(barcode='999888777666').first()
    assert prod is not None
    assert prod.unit_price == 1.99

def test_add_product_reject_negative_price(client, sample_users):
    """Test validation rejecting negative unit price."""
    client.post('/login', data={'username': 'admin_test', 'password': 'adminpass123'})
    response = client.post('/products/add', data={
        'name': 'Faulty Item',
        'category': 'Produce',
        'unit_price': '-5.00',
        'stock_qty': '10',
        'reorder_level': '5'
    }, follow_redirects=True)
    assert b'Unit price cannot be negative' in response.data
    assert Product.query.filter_by(name='Faulty Item').first() is None

def test_add_product_reject_negative_stock(client, sample_users):
    """Test validation rejecting negative stock quantity."""
    client.post('/login', data={'username': 'admin_test', 'password': 'adminpass123'})
    response = client.post('/products/add', data={
        'name': 'Negative Stock Item',
        'category': 'Produce',
        'unit_price': '2.50',
        'stock_qty': '-10',
        'reorder_level': '5'
    }, follow_redirects=True)
    assert b'Stock quantity cannot be negative' in response.data

def test_duplicate_barcode_rejected(client, sample_users, sample_products):
    """Test cannot add two products with same barcode."""
    client.post('/login', data={'username': 'admin_test', 'password': 'adminpass123'})
    response = client.post('/products/add', data={
        'name': 'Duplicate Barcode Apple',
        'category': 'Produce',
        'unit_price': '3.50',
        'stock_qty': '10',
        'reorder_level': '5',
        'barcode': '111111111111'  # Already used by apples
    }, follow_redirects=True)
    assert b'already assigned' in response.data

def test_product_search_api(client, sample_users, sample_products):
    """Test product search API returns JSON matches."""
    client.post('/login', data={'username': 'cashier_test', 'password': 'cashierpass123'})
    response = client.get('/products/api/search?q=Milk')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 1
    assert data[0]['name'] == 'Whole Milk'

def test_product_barcode_lookup_api(client, sample_users, sample_products):
    """Test barcode lookup API returns product details."""
    client.post('/login', data={'username': 'cashier_test', 'password': 'cashierpass123'})
    response = client.get('/products/api/barcode/111111111111')
    assert response.status_code == 200
    data = response.get_json()
    assert data['name'] == 'Organic Apples'
