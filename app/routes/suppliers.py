from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.routes.auth import login_required, role_required
from app.models import Supplier, Product
from app.database import db

suppliers_bp = Blueprint('suppliers', __name__)

@suppliers_bp.route('/')
@login_required
@role_required(['admin'])
def index():
    suppliers = Supplier.query.order_by(Supplier.name.asc()).all()
    return render_template('suppliers/index.html', suppliers=suppliers)

@suppliers_bp.route('/add', methods=['GET', 'POST'])
@login_required
@role_required(['admin'])
def add():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        contact_person = request.form.get('contact_person', '').strip()
        phone = request.form.get('phone', '').strip()
        email = request.form.get('email', '').strip()
        address = request.form.get('address', '').strip()

        if not name:
            flash('Supplier name is required.', 'danger')
            return render_template('suppliers/form.html', action='Add', supplier=None)

        supplier = Supplier(
            name=name,
            contact_person=contact_person,
            phone=phone,
            email=email,
            address=address
        )
        db.session.add(supplier)
        db.session.commit()
        flash(f'Supplier "{supplier.name}" added successfully!', 'success')
        return redirect(url_for('suppliers.index'))

    return render_template('suppliers/form.html', action='Add', supplier=None)

@suppliers_bp.route('/<int:supplier_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required(['admin'])
def edit(supplier_id):
    supplier = db.get_or_404(Supplier, supplier_id)

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        contact_person = request.form.get('contact_person', '').strip()
        phone = request.form.get('phone', '').strip()
        email = request.form.get('email', '').strip()
        address = request.form.get('address', '').strip()

        if not name:
            flash('Supplier name is required.', 'danger')
            return render_template('suppliers/form.html', action='Edit', supplier=supplier)

        supplier.name = name
        supplier.contact_person = contact_person
        supplier.phone = phone
        supplier.email = email
        supplier.address = address

        db.session.commit()
        flash(f'Supplier "{supplier.name}" updated successfully!', 'success')
        return redirect(url_for('suppliers.index'))

    return render_template('suppliers/form.html', action='Edit', supplier=supplier)

@suppliers_bp.route('/<int:supplier_id>/delete', methods=['POST'])
@login_required
@role_required(['admin'])
def delete(supplier_id):
    supplier = db.get_or_404(Supplier, supplier_id)
    # Check if products are tied to this supplier
    products = Product.query.filter_by(supplier_id=supplier_id).all()
    for p in products:
        p.supplier_id = None

    db.session.delete(supplier)
    db.session.commit()
    flash(f'Supplier "{supplier.name}" removed.', 'success')
    return redirect(url_for('suppliers.index'))
