import pytest
from datetime import date, timedelta
from app import create_app
from app.database import db
from app.models import User, Product, Supplier

@pytest.fixture
def app():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def runner(app):
    return app.test_cli_runner()

@pytest.fixture
def sample_users(app):
    admin = User(username='admin_test', role='admin', full_name='Admin Test')
    admin.set_password('adminpass123')

    cashier = User(username='cashier_test', role='cashier', full_name='Cashier Test')
    cashier.set_password('cashierpass123')

    db.session.add_all([admin, cashier])
    db.session.commit()
    return {'admin': admin, 'cashier': cashier}

@pytest.fixture
def sample_supplier(app):
    supplier = Supplier(
        name='Green Valley Orchards',
        contact_person='Jane Doe',
        phone='(555) 123-9999',
        email='jane@greenvalley.com'
    )
    db.session.add(supplier)
    db.session.commit()
    return supplier

@pytest.fixture
def sample_products(app, sample_supplier):
    today = date.today()
    p1 = Product(
        name='Organic Apples',
        category='Fresh Produce',
        unit_price=3.00,
        cost_price=1.50,
        stock_qty=50,
        reorder_level=10,
        expiry_date=today + timedelta(days=20),
        barcode='111111111111',
        supplier_id=sample_supplier.supplier_id
    )
    p2 = Product(
        name='Whole Milk',
        category='Dairy & Eggs',
        unit_price=4.50,
        cost_price=2.50,
        stock_qty=8,  # Below reorder level (Low stock)
        reorder_level=10,
        expiry_date=today + timedelta(days=5),  # Near expiry
        barcode='222222222222',
        supplier_id=sample_supplier.supplier_id
    )
    p3 = Product(
        name='Past Expired Yogurt',
        category='Dairy & Eggs',
        unit_price=2.00,
        cost_price=1.00,
        stock_qty=5,
        reorder_level=5,
        expiry_date=today - timedelta(days=3),  # Expired
        barcode='333333333333',
        supplier_id=sample_supplier.supplier_id
    )
    db.session.add_all([p1, p2, p3])
    db.session.commit()
    return {'apples': p1, 'milk': p2, 'yogurt': p3}
