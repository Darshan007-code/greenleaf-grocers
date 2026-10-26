from datetime import datetime, date, timedelta
import pandas as pd
import numpy as np
from sqlalchemy import func
from app.models import Product, Sale, SaleItem, User, Supplier
from app.database import db

class AnalyticsService:

    @staticmethod
    def get_sales_dataframe(start_date=None, end_date=None):
        """Query sales and sale_items and return as a pandas DataFrame."""
        query = db.session.query(
            Sale.sale_id,
            Sale.invoice_no,
            Sale.sale_date,
            Sale.sale_time,
            Sale.total_amount,
            Sale.discount,
            Sale.payment_method,
            User.username.label('cashier_username'),
            SaleItem.product_id,
            Product.name.label('product_name'),
            Product.category.label('category'),
            SaleItem.quantity,
            SaleItem.price,
            SaleItem.cost_price,
            SaleItem.subtotal
        ).join(SaleItem, Sale.sale_id == SaleItem.sale_id)\
         .join(Product, SaleItem.product_id == Product.product_id)\
         .join(User, Sale.user_id == User.user_id)

        if start_date:
            query = query.filter(Sale.sale_date >= start_date)
        if end_date:
            query = query.filter(Sale.sale_date <= end_date)

        rows = query.all()
        if not rows:
            return pd.DataFrame(columns=[
                'sale_id', 'invoice_no', 'sale_date', 'sale_time', 'total_amount',
                'discount', 'payment_method', 'cashier_username', 'product_id',
                'product_name', 'category', 'quantity', 'price', 'cost_price', 'subtotal'
            ])

        data = [r._asdict() for r in rows]
        df = pd.DataFrame(data)
        df['sale_date'] = pd.to_datetime(df['sale_date'])
        df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce').fillna(0)
        df['subtotal'] = pd.to_numeric(df['subtotal'], errors='coerce').fillna(0.0)
        df['cost_price'] = pd.to_numeric(df['cost_price'], errors='coerce').fillna(0.0)
        df['cogs'] = df['quantity'] * df['cost_price']
        return df

    @staticmethod
    def get_kpis(start_date=None, end_date=None):
        """Compute key business metrics."""
        # Query total sales and distinct orders
        sale_query = db.session.query(Sale)
        if start_date:
            sale_query = sale_query.filter(Sale.sale_date >= start_date)
        if end_date:
            sale_query = sale_query.filter(Sale.sale_date <= end_date)

        sales_list = sale_query.all()
        total_bills = len(sales_list)
        total_revenue = sum(s.total_amount for s in sales_list) if sales_list else 0.0
        avg_bill_value = (total_revenue / total_bills) if total_bills > 0 else 0.0

        # Low-stock count
        low_stock_count = Product.query.filter(
            Product.is_active == True,
            Product.stock_qty <= Product.reorder_level
        ).count()

        # Near-expiry count (within 15 days)
        today = date.today()
        target_expiry = today + timedelta(days=15)
        near_expiry_count = Product.query.filter(
            Product.is_active == True,
            Product.expiry_date != None,
            Product.expiry_date >= today,
            Product.expiry_date <= target_expiry
        ).count()

        # Stock Turnover Calculation:
        # Turnover Ratio = Total COGS / Average Inventory Value
        # Current Inventory Value = sum(stock_qty * unit_price)
        total_inventory_val = db.session.query(
            func.sum(Product.stock_qty * Product.unit_price)
        ).filter(Product.is_active == True).scalar() or 0.0

        df = AnalyticsService.get_sales_dataframe(start_date, end_date)
        if not df.empty and total_inventory_val > 0:
            total_cogs = df['cogs'].sum()
            # If COGS is available and positive, use COGS / Inventory; else sales / inventory
            metric_numerator = total_cogs if total_cogs > 0 else total_revenue
            stock_turnover = round(metric_numerator / total_inventory_val, 2)
        else:
            stock_turnover = 0.0

        # Top Category Share (%)
        top_category_name = "N/A"
        top_category_share = 0.0
        if not df.empty and total_revenue > 0:
            cat_summary = df.groupby('category')['subtotal'].sum()
            if not cat_summary.empty:
                best_cat = cat_summary.idxmax()
                top_category_name = best_cat
                top_category_share = round((cat_summary.max() / cat_summary.sum()) * 100, 1)

        return {
            'total_revenue': round(total_revenue, 2),
            'total_bills': total_bills,
            'avg_bill_value': round(avg_bill_value, 2),
            'stock_turnover': stock_turnover,
            'low_stock_count': low_stock_count,
            'near_expiry_count': near_expiry_count,
            'top_category_name': top_category_name,
            'top_category_share': top_category_share,
            'total_inventory_val': round(total_inventory_val, 2)
        }

    @staticmethod
    def get_daily_sales(start_date=None, end_date=None):
        """Aggregate revenue and bill count per day."""
        df = AnalyticsService.get_sales_dataframe(start_date, end_date)
        if df.empty:
            return []

        # Unique bills per day
        bills_per_day = df.groupby(df['sale_date'].dt.strftime('%Y-%m-%d'))['sale_id'].nunique()
        revenue_per_day = df.groupby(df['sale_date'].dt.strftime('%Y-%m-%d'))['subtotal'].sum()
        qty_per_day = df.groupby(df['sale_date'].dt.strftime('%Y-%m-%d'))['quantity'].sum()

        daily_df = pd.DataFrame({
            'date': revenue_per_day.index,
            'revenue': revenue_per_day.values.round(2),
            'bills': bills_per_day.values,
            'quantity': qty_per_day.values
        }).sort_values('date')

        return daily_df.to_dict(orient='records')

    @staticmethod
    def get_monthly_sales(months=12):
        """Aggregate revenue and sales count by month."""
        df = AnalyticsService.get_sales_dataframe()
        if df.empty:
            return []

        df['year_month'] = df['sale_date'].dt.strftime('%Y-%m')
        monthly_rev = df.groupby('year_month')['subtotal'].sum()
        monthly_bills = df.groupby('year_month')['sale_id'].nunique()
        monthly_qty = df.groupby('year_month')['quantity'].sum()

        result_df = pd.DataFrame({
            'month': monthly_rev.index,
            'revenue': monthly_rev.values.round(2),
            'bills': monthly_bills.values,
            'quantity': monthly_qty.values
        }).sort_values('month').tail(months)

        return result_df.to_dict(orient='records')

    @staticmethod
    def get_top_products(start_date=None, end_date=None, limit=10, sort_by='revenue'):
        """Top selling products sorted by revenue or quantity."""
        df = AnalyticsService.get_sales_dataframe(start_date, end_date)
        if df.empty:
            return []

        grouped = df.groupby(['product_id', 'product_name', 'category']).agg(
            total_qty=('quantity', 'sum'),
            total_rev=('subtotal', 'sum'),
            bill_count=('sale_id', 'nunique')
        ).reset_index()

        grouped['total_rev'] = grouped['total_rev'].round(2)
        sort_col = 'total_rev' if sort_by == 'revenue' else 'total_qty'
        top_df = grouped.sort_values(sort_col, ascending=False).head(limit)

        return top_df.to_dict(orient='records')

    @staticmethod
    def get_category_sales(start_date=None, end_date=None):
        """Category-wise sales distribution with percentages."""
        df = AnalyticsService.get_sales_dataframe(start_date, end_date)
        if df.empty:
            return []

        cat_grouped = df.groupby('category').agg(
            total_revenue=('subtotal', 'sum'),
            total_quantity=('quantity', 'sum')
        ).reset_index()

        total_rev_sum = cat_grouped['total_revenue'].sum()
        total_qty_sum = cat_grouped['total_quantity'].sum()

        cat_grouped['revenue_share'] = (
            (cat_grouped['total_revenue'] / total_rev_sum * 100).round(1)
            if total_rev_sum > 0 else 0
        )
        cat_grouped['quantity_share'] = (
            (cat_grouped['total_quantity'] / total_qty_sum * 100).round(1)
            if total_qty_sum > 0 else 0
        )
        cat_grouped['total_revenue'] = cat_grouped['total_revenue'].round(2)
        cat_grouped = cat_grouped.sort_values('total_revenue', ascending=False)

        return cat_grouped.to_dict(orient='records')

    @staticmethod
    def get_slow_moving_products(days=30):
        """Identify products with little or no sales in the past N days."""
        cutoff_date = date.today() - timedelta(days=days)
        all_products = Product.query.filter(Product.is_active == True).all()

        # Sales in the past N days
        recent_sales = db.session.query(
            SaleItem.product_id,
            func.sum(SaleItem.quantity).label('units_sold'),
            func.sum(SaleItem.subtotal).label('recent_revenue')
        ).join(Sale, SaleItem.sale_id == Sale.sale_id)\
         .filter(Sale.sale_date >= cutoff_date)\
         .group_by(SaleItem.product_id).all()

        recent_sales_dict = {
            r.product_id: {
                'units_sold': int(r.units_sold or 0),
                'recent_revenue': float(r.recent_revenue or 0.0)
            } for r in recent_sales
        }

        slow_movers = []
        for p in all_products:
            sales_info = recent_sales_dict.get(p.product_id, {'units_sold': 0, 'recent_revenue': 0.0})
            # Consider slow moving if sold <= 3 units in the last 30 days and has stock
            if sales_info['units_sold'] <= 3 and p.stock_qty > 0:
                slow_movers.append({
                    'product_id': p.product_id,
                    'name': p.name,
                    'category': p.category,
                    'stock_qty': p.stock_qty,
                    'unit_price': p.unit_price,
                    'inventory_value': round(p.stock_qty * p.unit_price, 2),
                    'units_sold_last_30d': sales_info['units_sold'],
                    'revenue_last_30d': round(sales_info['recent_revenue'], 2)
                })

        # Sort by highest inventory tied up
        slow_movers.sort(key=lambda x: x['inventory_value'], reverse=True)
        return slow_movers

    @staticmethod
    def forecast_sales_7_days():
        """Bonus Feature: Predict sales for the next 7 days based on recent daily revenue trends."""
        daily_sales = AnalyticsService.get_daily_sales()
        if len(daily_sales) < 5:
            # Not enough historical data to fit trend line
            avg_val = daily_sales[0]['revenue'] if daily_sales else 100.0
            forecast = []
            for i in range(1, 8):
                f_date = (date.today() + timedelta(days=i)).strftime('%Y-%m-%d')
                forecast.append({
                    'date': f_date,
                    'predicted_revenue': round(avg_val, 2),
                    'method': 'Baseline Average'
                })
            return forecast

        df = pd.DataFrame(daily_sales)
        df['day_idx'] = np.arange(len(df))

        # Use linear trend regression over recent 30-60 days
        recent_df = df.tail(60).copy()
        x = np.arange(len(recent_df))
        y = recent_df['revenue'].values

        # Linear regression slope and intercept: y = mx + c
        if len(x) > 1:
            coeffs = np.polyfit(x, y, 1)
            slope = coeffs[0]
            intercept = coeffs[1]
        else:
            slope = 0
            intercept = y[0]

        last_date = pd.to_datetime(recent_df['date'].iloc[-1]).date()
        forecast = []
        for i in range(1, 8):
            next_date = last_date + timedelta(days=i)
            pred_idx = len(x) - 1 + i
            pred_val = slope * pred_idx + intercept
            # Ensure predicted revenue is non-negative
            pred_val = max(50.0, float(pred_val))
            forecast.append({
                'date': next_date.strftime('%Y-%m-%d'),
                'predicted_revenue': round(pred_val, 2),
                'method': 'Linear Trend Regression'
            })

        return forecast
