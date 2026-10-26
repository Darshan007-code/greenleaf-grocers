import csv
import io
from datetime import datetime, date
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, Response
from app.routes.auth import login_required, role_required
from app.models import Product, Supplier, SaleItem
from app.database import db

products_bp = Blueprint('products', __name__)

@products_bp.route('/')
@login_required
@role_required(['admin'])
def index():
    query_str = request.args.get('q', '').strip()
    category = request.args.get('category', '').strip()
    status_filter = request.args.get('status', '').strip()

    products_query = Product.query.filter(Product.is_active == True)

    if query_str:
        products_query = products_query.filter(
            (Product.name.ilike(f'%{query_str}%')) |
            (Product.barcode.ilike(f'%{query_str}%'))
        )

    if category:
        products_query = products_query.filter(Product.category == category)

    if status_filter == 'low_stock':
        products_query = products_query.filter(Product.stock_qty <= Product.reorder_level)
    elif status_filter == 'expired':
        products_query = products_query.filter(Product.expiry_date != None, Product.expiry_date < date.today())
    elif status_filter == 'near_expiry':
        from datetime import timedelta
        products_query = products_query.filter(
            Product.expiry_date != None,
            Product.expiry_date >= date.today(),
            Product.expiry_date <= (date.today() + timedelta(days=15))
        )

    products = products_query.order_by(Product.name.asc()).all()
    categories = db.session.query(Product.category).distinct().order_by(Product.category).all()
    categories = [c[0] for c in categories if c[0]]

    return render_template(
        'products/index.html',
        products=products,
        categories=categories,
        current_category=category,
        query_str=query_str,
        status_filter=status_filter
    )

@products_bp.route('/add', methods=['GET', 'POST'])
@login_required
@role_required(['admin'])
def add():
    suppliers = Supplier.query.order_by(Supplier.name).all()

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        category = request.form.get('category', '').strip()
        unit_price = request.form.get('unit_price', '').strip()
        cost_price = request.form.get('cost_price', '0').strip()
        stock_qty = request.form.get('stock_qty', '0').strip()
        reorder_level = request.form.get('reorder_level', '10').strip()
        expiry_date_str = request.form.get('expiry_date', '').strip()
        barcode = request.form.get('barcode', '').strip() or None
        supplier_id = request.form.get('supplier_id', '').strip() or None

        # Validation
        if not name or not category or not unit_price:
            flash('Name, category, and unit price are required.', 'danger')
            return render_template('products/form.html', suppliers=suppliers, action='Add', product=None)

        try:
            unit_price_val = float(unit_price)
            if unit_price_val < 0:
                flash('Unit price cannot be negative.', 'danger')
                return render_template('products/form.html', suppliers=suppliers, action='Add', product=None)
        except ValueError:
            flash('Invalid unit price value.', 'danger')
            return render_template('products/form.html', suppliers=suppliers, action='Add', product=None)

        try:
            cost_price_val = float(cost_price) if cost_price else 0.0
            if cost_price_val < 0:
                flash('Cost price cannot be negative.', 'danger')
                return render_template('products/form.html', suppliers=suppliers, action='Add', product=None)
        except ValueError:
            flash('Invalid cost price value.', 'danger')
            return render_template('products/form.html', suppliers=suppliers, action='Add', product=None)

        try:
            stock_qty_val = int(stock_qty)
            if stock_qty_val < 0:
                flash('Stock quantity cannot be negative.', 'danger')
                return render_template('products/form.html', suppliers=suppliers, action='Add', product=None)
        except ValueError:
            flash('Stock quantity must be an integer.', 'danger')
            return render_template('products/form.html', suppliers=suppliers, action='Add', product=None)

        try:
            reorder_level_val = int(reorder_level)
            if reorder_level_val < 0:
                flash('Reorder level cannot be negative.', 'danger')
                return render_template('products/form.html', suppliers=suppliers, action='Add', product=None)
        except ValueError:
            flash('Reorder level must be an integer.', 'danger')
            return render_template('products/form.html', suppliers=suppliers, action='Add', product=None)

        expiry_date_val = None
        if expiry_date_str:
            try:
                expiry_date_val = datetime.strptime(expiry_date_str, '%Y-%m-%d').date()
            except ValueError:
                flash('Expiry date must be in YYYY-MM-DD format.', 'danger')
                return render_template('products/form.html', suppliers=suppliers, action='Add', product=None)

        if barcode:
            existing = Product.query.filter_by(barcode=barcode).first()
            if existing:
                flash(f'Barcode "{barcode}" is already assigned to {existing.name}.', 'danger')
                return render_template('products/form.html', suppliers=suppliers, action='Add', product=None)

        product = Product(
            name=name,
            category=category,
            unit_price=unit_price_val,
            cost_price=cost_price_val,
            stock_qty=stock_qty_val,
            reorder_level=reorder_level_val,
            expiry_date=expiry_date_val,
            barcode=barcode,
            supplier_id=int(supplier_id) if supplier_id else None
        )

        db.session.add(product)
        db.session.commit()
        flash(f'Product "{product.name}" added successfully!', 'success')
        return redirect(url_for('products.index'))

    return render_template('products/form.html', suppliers=suppliers, action='Add', product=None)

@products_bp.route('/<int:product_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required(['admin'])
def edit(product_id):
    product = db.get_or_404(Product, product_id)
    suppliers = Supplier.query.order_by(Supplier.name).all()

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        category = request.form.get('category', '').strip()
        unit_price = request.form.get('unit_price', '').strip()
        cost_price = request.form.get('cost_price', '0').strip()
        stock_qty = request.form.get('stock_qty', '0').strip()
        reorder_level = request.form.get('reorder_level', '10').strip()
        expiry_date_str = request.form.get('expiry_date', '').strip()
        barcode = request.form.get('barcode', '').strip() or None
        supplier_id = request.form.get('supplier_id', '').strip() or None

        if not name or not category or not unit_price:
            flash('Name, category, and unit price are required.', 'danger')
            return render_template('products/form.html', suppliers=suppliers, action='Edit', product=product)

        try:
            unit_price_val = float(unit_price)
            if unit_price_val < 0:
                flash('Unit price cannot be negative.', 'danger')
                return render_template('products/form.html', suppliers=suppliers, action='Edit', product=product)
        except ValueError:
            flash('Invalid unit price.', 'danger')
            return render_template('products/form.html', suppliers=suppliers, action='Edit', product=product)

        try:
            cost_price_val = float(cost_price) if cost_price else 0.0
            if cost_price_val < 0:
                flash('Cost price cannot be negative.', 'danger')
                return render_template('products/form.html', suppliers=suppliers, action='Edit', product=product)
        except ValueError:
            flash('Invalid cost price.', 'danger')
            return render_template('products/form.html', suppliers=suppliers, action='Edit', product=product)

        try:
            stock_qty_val = int(stock_qty)
            if stock_qty_val < 0:
                flash('Stock quantity cannot be negative.', 'danger')
                return render_template('products/form.html', suppliers=suppliers, action='Edit', product=product)
        except ValueError:
            flash('Stock quantity must be an integer.', 'danger')
            return render_template('products/form.html', suppliers=suppliers, action='Edit', product=product)

        try:
            reorder_level_val = int(reorder_level)
            if reorder_level_val < 0:
                flash('Reorder level cannot be negative.', 'danger')
                return render_template('products/form.html', suppliers=suppliers, action='Edit', product=product)
        except ValueError:
            flash('Reorder level must be an integer.', 'danger')
            return render_template('products/form.html', suppliers=suppliers, action='Edit', product=product)

        expiry_date_val = None
        if expiry_date_str:
            try:
                expiry_date_val = datetime.strptime(expiry_date_str, '%Y-%m-%d').date()
            except ValueError:
                flash('Expiry date must be YYYY-MM-DD.', 'danger')
                return render_template('products/form.html', suppliers=suppliers, action='Edit', product=product)

        if barcode:
            existing = Product.query.filter(Product.barcode == barcode, Product.product_id != product_id).first()
            if existing:
                flash(f'Barcode "{barcode}" is already assigned to {existing.name}.', 'danger')
                return render_template('products/form.html', suppliers=suppliers, action='Edit', product=product)

        product.name = name
        product.category = category
        product.unit_price = unit_price_val
        product.cost_price = cost_price_val
        product.stock_qty = stock_qty_val
        product.reorder_level = reorder_level_val
        product.expiry_date = expiry_date_val
        product.barcode = barcode
        product.supplier_id = int(supplier_id) if supplier_id else None

        db.session.commit()
        flash(f'Product "{product.name}" updated successfully!', 'success')
        return redirect(url_for('products.index'))

    return render_template('products/form.html', suppliers=suppliers, action='Edit', product=product)

@products_bp.route('/<int:product_id>/delete', methods=['POST'])
@login_required
@role_required(['admin'])
def delete(product_id):
    product = db.get_or_404(Product, product_id)
    # Check if this product has sale items
    has_sales = SaleItem.query.filter_by(product_id=product_id).first()
    if has_sales:
        # Soft delete to preserve historical integrity
        product.is_active = False
        db.session.commit()
        flash(f'Product "{product.name}" was deactivated (preserved historical sales records).', 'info')
    else:
        db.session.delete(product)
        db.session.commit()
        flash(f'Product "{product.name}" deleted successfully.', 'success')

    return redirect(url_for('products.index'))

@products_bp.route('/export')
@login_required
@role_required(['admin'])
def export_csv():
    products = Product.query.filter(Product.is_active == True).order_by(Product.name).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        'Product ID', 'Name', 'Category', 'Unit Price', 'Cost Price',
        'Stock Qty', 'Reorder Level', 'Expiry Date', 'Barcode', 'Supplier Name', 'Status'
    ])

    for p in products:
        status = 'Normal'
        if p.is_expired:
            status = 'Expired'
        elif p.is_near_expiry():
            status = 'Near Expiry'
        elif p.is_low_stock:
            status = 'Low Stock'

        writer.writerow([
            p.product_id,
            p.name,
            p.category,
            f"{p.unit_price:.2f}",
            f"{p.cost_price:.2f}",
            p.stock_qty,
            p.reorder_level,
            p.expiry_date.strftime('%Y-%m-%d') if p.expiry_date else '',
            p.barcode or '',
            p.supplier.name if p.supplier else '',
            status
        ])

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={"Content-Disposition": "attachment;filename=greenleaf_products.csv"}
    )

@products_bp.route('/import', methods=['GET', 'POST'])
@login_required
@role_required(['admin'])
def import_csv():
    if request.method == 'POST':
        if 'csv_file' not in request.files:
            flash('No file selected.', 'danger')
            return redirect(request.url)

        file = request.files['csv_file']
        if file.filename == '' or not file.filename.endswith('.csv'):
            flash('Please upload a valid .csv file.', 'danger')
            return redirect(request.url)

        try:
            stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
            reader = csv.DictReader(stream)
            imported_count = 0
            errors = []

            for row_idx, row in enumerate(reader, start=2):
                name = row.get('name', '').strip()
                category = row.get('category', '').strip()
                unit_price = row.get('unit_price', '').strip()

                if not name or not category or not unit_price:
                    errors.append(f"Row {row_idx}: Missing required name/category/unit_price.")
                    continue

                try:
                    price_val = float(unit_price)
                    if price_val < 0:
                        errors.append(f"Row {row_idx}: Negative unit price.")
                        continue
                except ValueError:
                    errors.append(f"Row {row_idx}: Invalid unit price format.")
                    continue

                cost_val = 0.0
                if row.get('cost_price'):
                    try:
                        cost_val = float(row.get('cost_price'))
                    except ValueError:
                        pass

                qty_val = 0
                if row.get('stock_qty'):
                    try:
                        qty_val = int(row.get('stock_qty'))
                        if qty_val < 0:
                            errors.append(f"Row {row_idx}: Negative stock qty.")
                            continue
                    except ValueError:
                        errors.append(f"Row {row_idx}: Invalid stock qty.")
                        continue

                reorder_val = 10
                if row.get('reorder_level'):
                    try:
                        reorder_val = int(row.get('reorder_level'))
                    except ValueError:
                        pass

                expiry_val = None
                if row.get('expiry_date'):
                    try:
                        expiry_val = datetime.strptime(row.get('expiry_date').strip(), '%Y-%m-%d').date()
                    except ValueError:
                        pass

                barcode_val = row.get('barcode', '').strip() or None
                if barcode_val:
                    dup = Product.query.filter_by(barcode=barcode_val).first()
                    if dup:
                        barcode_val = None  # Clear duplicate or skip

                new_prod = Product(
                    name=name,
                    category=category,
                    unit_price=price_val,
                    cost_price=cost_val,
                    stock_qty=qty_val,
                    reorder_level=reorder_val,
                    expiry_date=expiry_val,
                    barcode=barcode_val
                )
                db.session.add(new_prod)
                imported_count += 1

            db.session.commit()
            if errors:
                flash(f'Imported {imported_count} products with {len(errors)} skipped rows: {"; ".join(errors[:3])}', 'warning')
            else:
                flash(f'Successfully imported {imported_count} products from CSV!', 'success')
            return redirect(url_for('products.index'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error reading CSV file: {str(e)}', 'danger')

    return render_template('products/import.html')

# API Endpoints for POS Search and Barcode Scanner
@products_bp.route('/api/search')
@login_required
def api_search():
    q = request.args.get('q', '').strip()
    category = request.args.get('category', '').strip()

    query = Product.query.filter(Product.is_active == True)
    if q:
        query = query.filter(
            (Product.name.ilike(f'%{q}%')) |
            (Product.barcode.ilike(f'%{q}%'))
        )
    if category:
        query = query.filter(Product.category == category)

    products = query.order_by(Product.name).limit(50).all()
    return jsonify([p.to_dict() for p in products])

@products_bp.route('/api/barcode/<barcode>')
@login_required
def api_barcode(barcode):
    barcode = barcode.strip()
    product = Product.query.filter(
        Product.barcode == barcode,
        Product.is_active == True
    ).first()

    if not product:
        return jsonify({'error': 'Product not found'}), 404

    return jsonify(product.to_dict())
