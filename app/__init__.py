import os
from flask import Flask, render_template, session, g
from app.config import config_by_name
from app.database import db

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])

    # Initialize extensions
    db.init_app(app)

    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.products import products_bp
    from app.routes.billing import billing_bp
    from app.routes.reports import reports_bp
    from app.routes.suppliers import suppliers_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(products_bp, url_prefix='/products')
    app.register_blueprint(billing_bp, url_prefix='/billing')
    app.register_blueprint(reports_bp, url_prefix='/reports')
    app.register_blueprint(suppliers_bp, url_prefix='/suppliers')

    # Custom template filters
    @app.template_filter('currency')
    def currency_filter(value):
        try:
            return f"${float(value):,.2f}"
        except (ValueError, TypeError):
            return "$0.00"

    @app.template_filter('date_format')
    def date_format_filter(value, fmt='%b %d, %Y'):
        if not value:
            return '-'
        if hasattr(value, 'strftime'):
            return value.strftime(fmt)
        return str(value)

    # Context processor to inject user and alert counts
    @app.context_processor
    def inject_global_data():
        from app.models import User, Product
        from datetime import date, timedelta
        
        current_user = None
        user_id = session.get('user_id')
        if user_id:
            current_user = db.session.get(User, user_id)

        # Quick alert badges
        low_stock_count = 0
        near_expiry_count = 0
        if current_user and current_user.is_admin:
            try:
                low_stock_count = Product.query.filter(
                    Product.is_active == True,
                    Product.stock_qty <= Product.reorder_level
                ).count()
                
                target_date = date.today() + timedelta(days=app.config.get('NEAR_EXPIRY_DAYS', 15))
                near_expiry_count = Product.query.filter(
                    Product.is_active == True,
                    Product.expiry_date != None,
                    Product.expiry_date >= date.today(),
                    Product.expiry_date <= target_date
                ).count()
            except Exception:
                pass

        return {
            'current_user': current_user,
            'low_stock_count': low_stock_count,
            'near_expiry_count': near_expiry_count
        }

    # Error Handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_error(e):
        db.session.rollback()
        return render_template('500.html'), 500

    return app
