import io
import csv
from datetime import datetime, date
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, Response, send_file, session
from app.routes.auth import login_required
from app.models import Product, Sale, SaleItem, User
from app.services.billing_service import BillingService, BillingException
from app.services.pdf_service import PDFReceiptGenerator
from app.database import db

billing_bp = Blueprint('billing', __name__)

@billing_bp.route('/')
@billing_bp.route('/pos')
@login_required
def pos():
    # Load categories for quick-filter tabs
    categories = db.session.query(Product.category).filter(Product.is_active == True).distinct().order_by(Product.category).all()
    categories = [c[0] for c in categories if c[0]]

    # Initial popular/available products for display
    products = Product.query.filter(Product.is_active == True, Product.stock_qty > 0).order_by(Product.name).limit(24).all()

    return render_template('billing/pos.html', categories=categories, initial_products=products)

@billing_bp.route('/api/checkout', methods=['POST'])
@login_required
def api_checkout():
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': 'Invalid payload.'}), 400

    items = data.get('items', [])
    discount = data.get('discount', 0.0)
    payment_method = data.get('payment_method', 'Cash')
    customer_name = data.get('customer_name', 'Walk-in Customer')
    customer_phone = data.get('customer_phone')
    notes = data.get('notes')

    user_id = session.get('user_id')

    try:
        sale = BillingService.process_checkout(
            user_id=user_id,
            items=items,
            discount=discount,
            payment_method=payment_method,
            customer_name=customer_name,
            customer_phone=customer_phone,
            notes=notes
        )
        return jsonify({
            'success': True,
            'sale_id': sale.sale_id,
            'invoice_no': sale.invoice_no,
            'total_amount': sale.total_amount,
            'receipt_url': url_for('billing.receipt', sale_id=sale.sale_id),
            'pdf_url': url_for('billing.download_pdf', sale_id=sale.sale_id)
        })
    except BillingException as e:
        return jsonify({'success': False, 'message': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': f'Server error: {str(e)}'}), 500

@billing_bp.route('/receipt/<int:sale_id>')
@login_required
def receipt(sale_id):
    sale = db.get_or_404(Sale, sale_id)
    return render_template('billing/receipt.html', sale=sale)

@billing_bp.route('/receipt/<int:sale_id>/pdf')
@login_required
def download_pdf(sale_id):
    sale = db.get_or_404(Sale, sale_id)
    pdf_buffer = PDFReceiptGenerator.generate_receipt_pdf(sale)
    return send_file(
        pdf_buffer,
        as_attachment=True,
        download_name=f"Invoice_{sale.invoice_no}.pdf",
        mimetype='application/pdf'
    )

@billing_bp.route('/sales')
@login_required
def sales_history():
    query_str = request.args.get('q', '').strip()
    date_filter = request.args.get('date', '').strip()

    sales_query = Sale.query

    if query_str:
        sales_query = sales_query.filter(
            (Sale.invoice_no.ilike(f'%{query_str}%')) |
            (Sale.customer_name.ilike(f'%{query_str}%'))
        )

    if date_filter:
        try:
            filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
            sales_query = sales_query.filter(Sale.sale_date == filter_date)
        except ValueError:
            pass

    sales = sales_query.order_by(Sale.sale_timestamp.desc()).limit(100).all()

    return render_template('billing/sales_list.html', sales=sales, query_str=query_str, date_filter=date_filter)

@billing_bp.route('/receipt/<int:sale_id>/csv')
@login_required
def download_receipt_csv(sale_id):
    sale = db.get_or_404(Sale, sale_id)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['GREENLEAF GROCERS - INVOICE'])
    writer.writerow(['Invoice No', sale.invoice_no])
    writer.writerow(['Date', sale.sale_date.strftime('%Y-%m-%d')])
    writer.writerow(['Time', sale.sale_time.strftime('%H:%M:%S')])
    writer.writerow(['Cashier', sale.cashier.full_name or sale.cashier.username if sale.cashier else ''])
    writer.writerow(['Customer', sale.customer_name])
    writer.writerow(['Payment Method', sale.payment_method])
    writer.writerow([])
    writer.writerow(['Item Description', 'Unit Price', 'Quantity', 'Subtotal'])

    for it in sale.items:
        writer.writerow([
            it.product.name if it.product else 'Item',
            f"{it.price:.2f}",
            it.quantity,
            f"{it.subtotal:.2f}"
        ])

    writer.writerow([])
    writer.writerow(['', '', 'Subtotal', f"{sale.subtotal:.2f}"])
    writer.writerow(['', '', 'Discount', f"{sale.discount:.2f}"])
    writer.writerow(['', '', 'Grand Total', f"{sale.total_amount:.2f}"])

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={"Content-Disposition": f"attachment;filename=Receipt_{sale.invoice_no}.csv"}
    )
