import io
import csv
from datetime import datetime, date, timedelta
from flask import Blueprint, render_template, request, Response, jsonify
from app.routes.auth import login_required, role_required
from app.services.analytics import AnalyticsService
from app.models import Product
from app.database import db

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/')
@login_required
@role_required(['admin'])
def index():
    # Date range filters
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')

    start_date = None
    end_date = None

    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        except ValueError:
            pass

    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            pass

    # Default to past 30 days if not specified
    if not start_date and not end_date:
        end_date = date.today()
        start_date = end_date - timedelta(days=30)
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')

    kpis = AnalyticsService.get_kpis(start_date, end_date)
    daily_sales = AnalyticsService.get_daily_sales(start_date, end_date)
    monthly_sales = AnalyticsService.get_monthly_sales(months=12)
    top_products_rev = AnalyticsService.get_top_products(start_date, end_date, limit=10, sort_by='revenue')
    top_products_qty = AnalyticsService.get_top_products(start_date, end_date, limit=10, sort_by='quantity')
    category_sales = AnalyticsService.get_category_sales(start_date, end_date)
    slow_movers = AnalyticsService.get_slow_moving_products(days=30)[:15]
    forecast = AnalyticsService.forecast_sales_7_days()

    return render_template(
        'reports/index.html',
        kpis=kpis,
        daily_sales=daily_sales,
        monthly_sales=monthly_sales,
        top_products_rev=top_products_rev,
        top_products_qty=top_products_qty,
        category_sales=category_sales,
        slow_movers=slow_movers,
        forecast=forecast,
        start_date=start_date_str,
        end_date=end_date_str
    )

@reports_bp.route('/low-stock')
@login_required
@role_required(['admin'])
def low_stock():
    products = Product.query.filter(
        Product.is_active == True,
        Product.stock_qty <= Product.reorder_level
    ).order_by(Product.stock_qty.asc()).all()

    total_shortage = sum(max(0, p.reorder_level * 2 - p.stock_qty) for p in products)

    return render_template('reports/low_stock.html', products=products, total_shortage=total_shortage)

@reports_bp.route('/expiry')
@login_required
@role_required(['admin'])
def expiry():
    today = date.today()
    target_date = today + timedelta(days=15)

    expired_products = Product.query.filter(
        Product.is_active == True,
        Product.expiry_date != None,
        Product.expiry_date < today
    ).order_by(Product.expiry_date.asc()).all()

    near_expiry_products = Product.query.filter(
        Product.is_active == True,
        Product.expiry_date != None,
        Product.expiry_date >= today,
        Product.expiry_date <= target_date
    ).order_by(Product.expiry_date.asc()).all()

    total_at_risk_value = sum(p.stock_qty * p.unit_price for p in (expired_products + near_expiry_products))

    return render_template(
        'reports/expiry.html',
        expired_products=expired_products,
        near_expiry_products=near_expiry_products,
        total_at_risk_value=round(total_at_risk_value, 2)
    )

@reports_bp.route('/export/<report_type>')
@login_required
@role_required(['admin'])
def export_report_csv(report_type):
    output = io.StringIO()
    writer = csv.writer(output)

    if report_type == 'daily':
        data = AnalyticsService.get_daily_sales()
        writer.writerow(['Date', 'Revenue ($)', 'Number of Bills', 'Total Quantity Sold'])
        for row in data:
            writer.writerow([row['date'], f"{row['revenue']:.2f}", row['bills'], row['quantity']])
        filename = "greenleaf_daily_sales.csv"

    elif report_type == 'monthly':
        data = AnalyticsService.get_monthly_sales()
        writer.writerow(['Month', 'Revenue ($)', 'Number of Bills', 'Total Quantity Sold'])
        for row in data:
            writer.writerow([row['month'], f"{row['revenue']:.2f}", row['bills'], row['quantity']])
        filename = "greenleaf_monthly_sales.csv"

    elif report_type == 'top-products':
        data = AnalyticsService.get_top_products(limit=50, sort_by='revenue')
        writer.writerow(['Product ID', 'Product Name', 'Category', 'Total Revenue ($)', 'Units Sold', 'Orders Count'])
        for row in data:
            writer.writerow([row['product_id'], row['product_name'], row['category'], f"{row['total_rev']:.2f}", row['total_qty'], row['bill_count']])
        filename = "greenleaf_top_products.csv"

    elif report_type == 'low-stock':
        products = Product.query.filter(
            Product.is_active == True,
            Product.stock_qty <= Product.reorder_level
        ).order_by(Product.stock_qty.asc()).all()
        writer.writerow(['Product ID', 'Name', 'Category', 'Current Stock', 'Reorder Level', 'Suggested Reorder Qty', 'Unit Price ($)', 'Supplier'])
        for p in products:
            reorder_qty = max(10, (p.reorder_level * 2) - p.stock_qty)
            writer.writerow([p.product_id, p.name, p.category, p.stock_qty, p.reorder_level, reorder_qty, f"{p.unit_price:.2f}", p.supplier.name if p.supplier else 'None'])
        filename = "greenleaf_low_stock_report.csv"

    elif report_type == 'expiry':
        today = date.today()
        target_date = today + timedelta(days=15)
        products = Product.query.filter(
            Product.is_active == True,
            Product.expiry_date != None,
            Product.expiry_date <= target_date
        ).order_by(Product.expiry_date.asc()).all()
        writer.writerow(['Product ID', 'Name', 'Category', 'Stock Qty', 'Unit Price ($)', 'Expiry Date', 'Status', 'Days Remaining', 'Total Risk Value ($)'])
        for p in products:
            status = 'Expired' if p.expiry_date < today else 'Near Expiry'
            days_rem = (p.expiry_date - today).days
            writer.writerow([p.product_id, p.name, p.category, p.stock_qty, f"{p.unit_price:.2f}", p.expiry_date.strftime('%Y-%m-%d'), status, days_rem, f"{(p.stock_qty * p.unit_price):.2f}"])
        filename = "greenleaf_expiry_report.csv"

    elif report_type == 'slow-moving':
        data = AnalyticsService.get_slow_moving_products(days=30)
        writer.writerow(['Product ID', 'Name', 'Category', 'Stock Qty', 'Unit Price ($)', 'Inventory Value ($)', 'Units Sold (Past 30d)', 'Revenue (Past 30d)'])
        for row in data:
            writer.writerow([row['product_id'], row['name'], row['category'], row['stock_qty'], f"{row['unit_price']:.2f}", f"{row['inventory_value']:.2f}", row['units_sold_last_30d'], f"{row['revenue_last_30d']:.2f}"])
        filename = "greenleaf_slow_moving_products.csv"

    else:
        return Response("Invalid report type", status=400)

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={"Content-Disposition": f"attachment;filename={filename}"}
    )
