from datetime import datetime, date, timedelta, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from app.database import db

def utc_now():
    return datetime.now(timezone.utc)

class User(db.Model):
    __tablename__ = 'users'

    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='cashier')  # 'admin' or 'cashier'
    full_name = db.Column(db.String(100), nullable=False, default='')
    created_at = db.Column(db.DateTime, default=utc_now)

    # Relationships
    sales = db.relationship('Sale', backref='cashier', lazy=True)

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self) -> bool:
        return self.role.lower() == 'admin'

    def to_dict(self):
        return {
            'user_id': self.user_id,
            'username': self.username,
            'role': self.role,
            'full_name': self.full_name
        }


class Supplier(db.Model):
    __tablename__ = 'suppliers'

    supplier_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(30), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    contact_person = db.Column(db.String(100), nullable=True)
    address = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now)

    # Relationships
    products = db.relationship('Product', backref='supplier', lazy=True)

    def to_dict(self):
        return {
            'supplier_id': self.supplier_id,
            'name': self.name,
            'phone': self.phone,
            'email': self.email,
            'contact_person': self.contact_person,
            'address': self.address,
            'products_count': len(self.products) if self.products else 0
        }


class Product(db.Model):
    __tablename__ = 'products'

    product_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(150), nullable=False, index=True)
    category = db.Column(db.String(80), nullable=False, index=True)
    unit_price = db.Column(db.Float, nullable=False)
    cost_price = db.Column(db.Float, nullable=False, default=0.0)
    stock_qty = db.Column(db.Integer, nullable=False, default=0)
    reorder_level = db.Column(db.Integer, nullable=False, default=10)
    expiry_date = db.Column(db.Date, nullable=True, index=True)
    barcode = db.Column(db.String(50), unique=True, nullable=True, index=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.supplier_id'), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=utc_now)

    # Relationships
    sale_items = db.relationship('SaleItem', backref='product', lazy=True)

    @property
    def is_low_stock(self) -> bool:
        return self.stock_qty <= self.reorder_level

    @property
    def is_expired(self) -> bool:
        if not self.expiry_date:
            return False
        return self.expiry_date < date.today()

    @property
    def days_until_expiry(self):
        if not self.expiry_date:
            return None
        return (self.expiry_date - date.today()).days

    def is_near_expiry(self, days=15) -> bool:
        if not self.expiry_date:
            return False
        diff = (self.expiry_date - date.today()).days
        return 0 <= diff <= days

    def to_dict(self):
        return {
            'product_id': self.product_id,
            'name': self.name,
            'category': self.category,
            'unit_price': float(self.unit_price),
            'cost_price': float(self.cost_price),
            'stock_qty': self.stock_qty,
            'reorder_level': self.reorder_level,
            'expiry_date': self.expiry_date.strftime('%Y-%m-%d') if self.expiry_date else None,
            'barcode': self.barcode,
            'supplier_id': self.supplier_id,
            'supplier_name': self.supplier.name if self.supplier else 'None',
            'is_low_stock': self.is_low_stock,
            'is_expired': self.is_expired,
            'is_near_expiry': self.is_near_expiry(),
            'days_until_expiry': self.days_until_expiry
        }


class Sale(db.Model):
    __tablename__ = 'sales'

    sale_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    invoice_no = db.Column(db.String(30), unique=True, nullable=False, index=True)
    sale_date = db.Column(db.Date, nullable=False, index=True)
    sale_time = db.Column(db.Time, nullable=False)
    sale_timestamp = db.Column(db.DateTime, nullable=False, default=utc_now, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    customer_name = db.Column(db.String(100), default='Walk-in Customer')
    customer_phone = db.Column(db.String(20), nullable=True)
    payment_method = db.Column(db.String(30), default='Cash')  # Cash, Card, UPI
    subtotal = db.Column(db.Float, nullable=False, default=0.0)
    discount = db.Column(db.Float, nullable=False, default=0.0)
    total_amount = db.Column(db.Float, nullable=False, default=0.0)
    notes = db.Column(db.Text, nullable=True)

    # Relationships
    items = db.relationship('SaleItem', backref='sale', cascade='all, delete-orphan', lazy=True)

    def to_dict(self):
        return {
            'sale_id': self.sale_id,
            'invoice_no': self.invoice_no,
            'sale_date': self.sale_date.strftime('%Y-%m-%d'),
            'sale_time': self.sale_time.strftime('%H:%M:%S'),
            'user_id': self.user_id,
            'cashier_name': self.cashier.full_name or self.cashier.username if self.cashier else 'Unknown',
            'customer_name': self.customer_name,
            'payment_method': self.payment_method,
            'subtotal': round(self.subtotal, 2),
            'discount': round(self.discount, 2),
            'total_amount': round(self.total_amount, 2),
            'items_count': len(self.items)
        }


class SaleItem(db.Model):
    __tablename__ = 'sale_items'

    sale_item_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('sales.sale_id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.product_id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)  # Unit price at time of sale
    cost_price = db.Column(db.Float, default=0.0)
    subtotal = db.Column(db.Float, nullable=False)

    def to_dict(self):
        return {
            'sale_item_id': self.sale_item_id,
            'sale_id': self.sale_id,
            'product_id': self.product_id,
            'product_name': self.product.name if self.product else 'Unknown',
            'quantity': self.quantity,
            'price': round(self.price, 2),
            'subtotal': round(self.subtotal, 2)
        }
