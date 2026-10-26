from datetime import datetime, date, time, timezone
from app.models import Product, Sale, SaleItem, User
from app.database import db

class BillingException(Exception):
    """Custom exception for billing business logic violations."""
    pass

class BillingService:

    @staticmethod
    def generate_invoice_number():
        """Generate unique invoice format: GL-YYYYMMDD-XXXX."""
        today_str = datetime.now(timezone.utc).strftime('%Y%m%d')
        prefix = f"GL-{today_str}-"

        # Find the last invoice with this prefix
        last_sale = Sale.query.filter(Sale.invoice_no.like(f"{prefix}%"))\
            .order_by(Sale.sale_id.desc()).first()

        if last_sale and last_sale.invoice_no:
            try:
                last_seq = int(last_sale.invoice_no.split('-')[-1])
                new_seq = last_seq + 1
            except ValueError:
                new_seq = 1
        else:
            new_seq = 1

        return f"{prefix}{new_seq:04d}"

    @staticmethod
    def process_checkout(user_id, items, discount=0.0, payment_method='Cash', customer_name='Walk-in Customer', customer_phone=None, notes=None):
        """
        Process a complete sale transaction with atomic stock deduction and validation.
        items: list of dicts: [{'product_id': int, 'quantity': int}]
        """
        if not items:
            raise BillingException("The shopping cart is empty. Please add items to proceed.")

        user = db.session.get(User, user_id)
        if not user:
            raise BillingException("Invalid cashier session.")

        try:
            discount = float(discount)
            if discount < 0:
                raise BillingException("Discount cannot be negative.")
        except (ValueError, TypeError):
            raise BillingException("Invalid discount format.")

        subtotal = 0.0
        sale_items_to_create = []

        # Validate each item and check stock availability
        for item in items:
            product_id = item.get('product_id')
            qty = item.get('quantity')

            try:
                qty = int(qty)
            except (ValueError, TypeError):
                raise BillingException(f"Invalid quantity '{qty}' specified for product.")

            if qty <= 0:
                raise BillingException("Item quantities must be positive integers greater than zero.")

            product = db.session.get(Product, product_id)
            if not product or not product.is_active:
                raise BillingException(f"Product ID {product_id} is invalid or inactive.")

            # Validate stock availability
            if qty > product.stock_qty:
                raise BillingException(
                    f"Insufficient stock for '{product.name}'. Requested: {qty}, Available: {product.stock_qty}."
                )

            item_subtotal = round(product.unit_price * qty, 2)
            subtotal += item_subtotal

            # Stage stock deduction
            product.stock_qty -= qty

            sale_items_to_create.append({
                'product': product,
                'product_id': product.product_id,
                'quantity': qty,
                'price': product.unit_price,
                'cost_price': product.cost_price,
                'subtotal': item_subtotal
            })

        subtotal = round(subtotal, 2)
        if discount > subtotal:
            raise BillingException(f"Discount (${discount:.2f}) cannot exceed subtotal (${subtotal:.2f}).")

        total_amount = round(subtotal - discount, 2)
        invoice_no = BillingService.generate_invoice_number()

        now = datetime.now(timezone.utc)
        new_sale = Sale(
            invoice_no=invoice_no,
            sale_date=now.date(),
            sale_time=now.time(),
            sale_timestamp=now,
            user_id=user.user_id,
            customer_name=(customer_name or 'Walk-in Customer').strip(),
            customer_phone=(customer_phone or '').strip() or None,
            payment_method=payment_method or 'Cash',
            subtotal=subtotal,
            discount=discount,
            total_amount=total_amount,
            notes=notes
        )

        db.session.add(new_sale)
        db.session.flush()  # Flush to get sale_id

        for si in sale_items_to_create:
            sale_item = SaleItem(
                sale_id=new_sale.sale_id,
                product_id=si['product_id'],
                quantity=si['quantity'],
                price=si['price'],
                cost_price=si['cost_price'],
                subtotal=si['subtotal']
            )
            db.session.add(sale_item)

        # Commit transaction
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise BillingException(f"Database error while recording sale: {str(e)}")

        return new_sale
