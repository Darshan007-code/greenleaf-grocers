from flask import Blueprint, render_template, redirect, url_for, session
from app.routes.auth import login_required, role_required
from app.services.analytics import AnalyticsService
from app.models import Sale, Product
from datetime import date, timedelta

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard')
@login_required
@role_required(['admin'])
def index():
    # Compute KPIs
    kpis = AnalyticsService.get_kpis()
    
    # Recent 10 sales
    recent_sales = Sale.query.order_by(Sale.sale_timestamp.desc()).limit(10).all()

    # Low stock preview (first 5)
    low_stock_products = Product.query.filter(
        Product.is_active == True,
        Product.stock_qty <= Product.reorder_level
    ).order_by(Product.stock_qty.asc()).limit(5).all()

    # Near expiry preview (first 5)
    today = date.today()
    target_date = today + timedelta(days=15)
    near_expiry_products = Product.query.filter(
        Product.is_active == True,
        Product.expiry_date != None,
        Product.expiry_date >= today,
        Product.expiry_date <= target_date
    ).order_by(Product.expiry_date.asc()).limit(5).all()

    # Daily trend data for dashboard mini-chart
    daily_sales = AnalyticsService.get_daily_sales()[-14:]  # Last 14 days
    category_sales = AnalyticsService.get_category_sales()[:6]

    return render_template(
        'dashboard/index.html',
        kpis=kpis,
        recent_sales=recent_sales,
        low_stock_products=low_stock_products,
        near_expiry_products=near_expiry_products,
        daily_sales=daily_sales,
        category_sales=category_sales
    )
