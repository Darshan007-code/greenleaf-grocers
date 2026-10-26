"""
Seed script for GreenLeaf Grocers Inventory & Sales Management System.
Generates:
- Default Admin & Cashier user accounts
- 6 Realistic grocery suppliers
- 55+ Grocery products across 8 categories with varied stock levels and expiry dates
- 550+ Historical sales transactions spread across several months
"""

import sys
import os
import random
from datetime import datetime, date, time, timedelta

# Ensure project directory is in python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app
from app.database import db
from app.models import User, Supplier, Product, Sale, SaleItem

def seed_database():
    app = create_app('development')
    with app.app_context():
        print("Clearing existing database tables...")
        db.drop_all()
        db.create_all()

        print("1. Creating Users (Admin & Cashiers)...")
        admin = User(
            username='admin',
            role='admin',
            full_name='Store Manager (Admin)'
        )
        admin.set_password('admin123')

        cashier1 = User(
            username='cashier',
            role='cashier',
            full_name='Alice Smith (Cashier 1)'
        )
        cashier1.set_password('cashier123')

        cashier2 = User(
            username='cashier2',
            role='cashier',
            full_name='Bob Johnson (Cashier 2)'
        )
        cashier2.set_password('cashier123')

        db.session.add_all([admin, cashier1, cashier2])
        db.session.commit()
        print(f"   Created 3 users: admin, cashier, cashier2.")

        print("2. Creating Suppliers...")
        suppliers_data = [
            Supplier(name='Sunrise Organic Farms', contact_person='Carlos Rivera', phone='(555) 234-8901', email='orders@sunriseorganics.com', address='742 Farm Road, Salinas Valley, CA'),
            Supplier(name='Valley Dairy Co-operative', contact_person='Hannah Brooks', phone='(555) 456-1122', email='supply@valleydairy.org', address='12 Pasture Lane, Green County, WI'),
            Supplier(name='Artisan Crust Bakery Supply', contact_person='Marco Rossi', phone='(555) 789-3344', email='sales@artisancrust.com', address='88 Flour Mill Blvd, Portland, OR'),
            Supplier(name='Evergreen Beverage Distributors', contact_person='Linda Chen', phone='(555) 321-7788', email='distribution@evergreenbev.com', address='500 Industrial Pkwy, Seattle, WA'),
            Supplier(name='Harvest Grain & Pantry Mills', contact_person='Samuel Wright', phone='(555) 654-9900', email='orders@harvestgrain.com', address='320 Silo Ave, Omaha, NE'),
            Supplier(name='EcoClean & Household Essentials', contact_person='Rachel Green', phone='(555) 987-4411', email='support@ecocleangoods.com', address='150 GreenTech Way, Austin, TX'),
        ]
        db.session.add_all(suppliers_data)
        db.session.commit()
        print(f"   Created {len(suppliers_data)} suppliers.")

        print("3. Creating 55+ Products across 8 Categories...")
        today = date.today()

        raw_products = [
            # Fresh Produce (Supplier 1: Sunrise Organic Farms)
            ("Organic Bananas (Bunch)", "Fresh Produce", 1.89, 0.90, 85, 20, today + timedelta(days=5), "078910010001", 1),
            ("Honeycrisp Apples (1 lb)", "Fresh Produce", 2.99, 1.40, 60, 15, today + timedelta(days=12), "078910010002", 1),
            ("Hass Avocados (4-pack)", "Fresh Produce", 4.99, 2.50, 4, 10, today + timedelta(days=4), "078910010003", 1), # Low stock & near expiry
            ("Organic Baby Spinach (5oz)", "Fresh Produce", 3.49, 1.80, 22, 10, today + timedelta(days=6), "078910010004", 1),
            ("Roma Tomatoes (1 lb)", "Fresh Produce", 2.19, 1.10, 45, 15, today + timedelta(days=9), "078910010005", 1),
            ("Sweet Bell Peppers (3-pack)", "Fresh Produce", 3.99, 2.00, 30, 10, today + timedelta(days=11), "078910010006", 1),
            ("Organic Carrots (2 lb bag)", "Fresh Produce", 2.49, 1.20, 50, 15, today + timedelta(days=25), "078910010007", 1),
            ("English Seedless Cucumbers", "Fresh Produce", 1.99, 0.95, 35, 12, today + timedelta(days=8), "078910010008", 1),
            ("Fresh Blueberries (pint)", "Fresh Produce", 4.49, 2.30, 2, 10, today + timedelta(days=3), "078910010009", 1), # Low stock & near expiry
            ("Yellow Onions (3 lb bag)", "Fresh Produce", 2.99, 1.30, 70, 20, today + timedelta(days=60), "078910010010", 1),
            ("Yukon Gold Potatoes (5 lb)", "Fresh Produce", 4.99, 2.20, 55, 15, today + timedelta(days=45), "078910010011", 1),

            # Dairy & Eggs (Supplier 2: Valley Dairy)
            ("Whole Milk (1 Gallon)", "Dairy & Eggs", 4.29, 2.80, 48, 15, today + timedelta(days=10), "078910020001", 2),
            ("Organic Cage-Free Eggs (Dozen)", "Dairy & Eggs", 5.49, 3.20, 65, 20, today + timedelta(days=18), "078910020002", 2),
            ("Salted Creamery Butter (1 lb)", "Dairy & Eggs", 4.99, 3.10, 35, 12, today + timedelta(days=60), "078910020003", 2),
            ("Greek Plain Yogurt (32oz)", "Dairy & Eggs", 4.79, 2.90, 5, 10, today + timedelta(days=7), "078910020004", 2), # Low stock & near expiry
            ("Sharp Cheddar Cheese Block (8oz)", "Dairy & Eggs", 3.89, 2.20, 40, 12, today + timedelta(days=90), "078910020005", 2),
            ("Almond Milk Unsweetened (64oz)", "Dairy & Eggs", 3.99, 2.40, 28, 10, today + timedelta(days=35), "078910020006", 2),
            ("Sour Cream All-Natural (16oz)", "Dairy & Eggs", 2.49, 1.40, 1, 8, today - timedelta(days=2), "078910020007", 2), # Expired!
            ("Heavy Whipping Cream (16oz)", "Dairy & Eggs", 3.69, 2.10, 18, 8, today + timedelta(days=14), "078910020008", 2), # Near expiry

            # Bakery (Supplier 3: Artisan Crust)
            ("San Francisco Sourdough Batard", "Bakery", 4.99, 2.40, 24, 8, today + timedelta(days=3), "078910030001", 3),
            ("Whole Wheat Sandwich Bread", "Bakery", 3.79, 1.90, 36, 10, today + timedelta(days=5), "078910030002", 3),
            ("French Butter Croissants (4pk)", "Bakery", 5.99, 3.20, 14, 6, today + timedelta(days=2), "078910030003", 3),
            ("Everything Bagels (6pk)", "Bakery", 4.29, 2.10, 20, 8, today + timedelta(days=4), "078910030004", 3),
            ("Blueberry Crumble Muffins (4pk)", "Bakery", 5.49, 2.80, 12, 6, today + timedelta(days=3), "078910030005", 3),
            ("Brioche Hamburger Buns (4pk)", "Bakery", 3.99, 2.00, 18, 8, today + timedelta(days=5), "078910030006", 3),

            # Beverages (Supplier 4: Evergreen Beverage)
            ("Cold-Pressed 100% Orange Juice (52oz)", "Beverages", 5.99, 3.60, 32, 10, today + timedelta(days=14), "078910040001", 4), # Near expiry
            ("Italian Sparkling Water (12x330ml)", "Beverages", 7.49, 4.20, 42, 12, today + timedelta(days=200), "078910040002", 4),
            ("Organic Cold Brew Coffee (32oz)", "Beverages", 6.29, 3.80, 20, 8, today + timedelta(days=28), "078910040003", 4),
            ("Japanese Green Tea Bags (40ct)", "Beverages", 5.49, 2.90, 50, 15, today + timedelta(days=365), "078910040004", 4),
            ("Oat Milk Barista Blend (32oz)", "Beverages", 4.49, 2.50, 34, 10, today + timedelta(days=120), "078910040005", 4),
            ("Apple Cider Spiced (64oz)", "Beverages", 4.99, 2.70, 3, 10, today + timedelta(days=13), "078910040006", 4), # Low stock & near expiry

            # Pantry & Grains (Supplier 5: Harvest Grain Mills)
            ("Extra Virgin Olive Oil (750ml)", "Pantry & Grains", 12.99, 7.80, 40, 10, today + timedelta(days=450), "078910050001", 5),
            ("Jasmine Fragrant Rice (5 lb bag)", "Pantry & Grains", 8.49, 4.90, 60, 15, today + timedelta(days=500), "078910050002", 5),
            ("Organic Tricolor Quinoa (2 lb)", "Pantry & Grains", 6.99, 3.90, 25, 8, today + timedelta(days=400), "078910050003", 5),
            ("Bronze-Cut Penne Rigate (16oz)", "Pantry & Grains", 2.79, 1.30, 80, 20, today + timedelta(days=600), "078910050004", 5),
            ("San Marzano Marinara Sauce (24oz)", "Pantry & Grains", 5.99, 3.20, 45, 12, today + timedelta(days=300), "078910050005", 5),
            ("Organic Rolled Oats (32oz)", "Pantry & Grains", 4.49, 2.20, 38, 10, today + timedelta(days=360), "078910050006", 5),
            ("Wildflower Raw Honey (16oz)", "Pantry & Grains", 8.99, 5.00, 22, 8, today + timedelta(days=700), "078910050007", 5),
            ("Balsamic Glaze of Modena (250ml)", "Pantry & Grains", 6.49, 3.50, 15, 6, today + timedelta(days=550), "078910050008", 5),
            ("Organic Coconut Flour (1 lb)", "Pantry & Grains", 5.29, 3.00, 28, 8, today + timedelta(days=280), "078910050009", 5), # Slow mover

            # Snacks & Sweets (Supplier 5: Harvest Grain / Sweets)
            ("72% Dark Chocolate Sea Salt Bar (3.5oz)", "Snacks & Sweets", 3.49, 1.70, 75, 20, today + timedelta(days=240), "078910060001", 5),
            ("Kettle Cooked Sea Salt Chips (8oz)", "Snacks & Sweets", 3.99, 2.00, 52, 15, today + timedelta(days=90), "078910060002", 5),
            ("Roasted Salted Almonds (12oz)", "Snacks & Sweets", 7.99, 4.60, 30, 10, today + timedelta(days=180), "078910060003", 5),
            ("Organic Butter Popcorn (6oz)", "Snacks & Sweets", 3.29, 1.60, 40, 12, today + timedelta(days=120), "078910060004", 5),
            ("Nut Butter Granola Clusters (10oz)", "Snacks & Sweets", 5.49, 2.90, 35, 10, today + timedelta(days=150), "078910060005", 5),
            ("Organic Vegan Fruit Gummies (5oz)", "Snacks & Sweets", 2.99, 1.40, 48, 15, today + timedelta(days=210), "078910060006", 5),

            # Canned & Packaged Goods (Supplier 5: Harvest Grain Mills)
            ("Organic Black Beans (15oz)", "Canned & Packaged", 1.69, 0.80, 90, 25, today + timedelta(days=700), "078910070001", 5),
            ("Diced Tomatoes with Basil (14.5oz)", "Canned & Packaged", 1.89, 0.90, 85, 20, today + timedelta(days=650), "078910070002", 5),
            ("Organic Coconut Milk (13.5oz)", "Canned & Packaged", 2.79, 1.40, 50, 15, today + timedelta(days=500), "078910070003", 5),
            ("Wild Albacore Tuna in Olive Oil (5oz)", "Canned & Packaged", 3.99, 2.20, 65, 18, today + timedelta(days=800), "078910070004", 5),
            ("Organic Garbanzo Chickpeas (15oz)", "Canned & Packaged", 1.79, 0.85, 70, 20, today + timedelta(days=600), "078910070005", 5),
            ("Artisan Smoked Sardines in Oil (4.4oz)", "Canned & Packaged", 4.49, 2.50, 25, 8, today + timedelta(days=600), "078910070006", 5), # Slow mover

            # Household Essentials (Supplier 6: EcoClean)
            ("Plant-Based Dish Soap Citrus (25oz)", "Household Essentials", 4.29, 2.20, 45, 12, None, "078910080001", 6),
            ("Bamboo Unbleached Paper Towels (6pk)", "Household Essentials", 9.99, 5.50, 30, 10, None, "078910080002", 6),
            ("100% Recycled Bath Tissue (12 rolls)", "Household Essentials", 11.49, 6.80, 40, 12, None, "078910080003", 6),
            ("Eco Concentrated Laundry Detergent (64oz)", "Household Essentials", 13.99, 8.00, 25, 8, None, "078910080004", 6),
            ("All-Purpose Surface Spray Lavender (32oz)", "Household Essentials", 4.79, 2.40, 35, 10, None, "078910080005", 6),
            ("Compostable Trash Bags 13 Gal (30ct)", "Household Essentials", 7.99, 4.30, 28, 8, None, "078910080006", 6),
            ("Organic Beeswax Furniture Polish (8oz)", "Household Essentials", 9.49, 5.20, 12, 5, None, "078910080007", 6), # Slow mover
        ]

        products_list = []
        for p in raw_products:
            prod = Product(
                name=p[0],
                category=p[1],
                unit_price=p[2],
                cost_price=p[3],
                stock_qty=p[4],
                reorder_level=p[5],
                expiry_date=p[6],
                barcode=p[7],
                supplier_id=p[8]
            )
            products_list.append(prod)

        db.session.add_all(products_list)
        db.session.commit()
        print(f"   Created {len(products_list)} catalog products.")

        print("4. Generating 550+ Historical Sales Transactions over the past 4 months...")
        cashiers = [cashier1, cashier2, admin]
        payment_methods = ['Cash', 'Card', 'UPI / Digital']
        payment_weights = [0.45, 0.40, 0.15]

        customer_names = [
            'Walk-in Customer', 'Walk-in Customer', 'Walk-in Customer',
            'Sarah Jenkins', 'David Patel', 'Emma Wilson', 'Michael Chang',
            'Sophia Martinez', 'James Robinson', 'Olivia Taylor', 'Lucas Brown',
            'Chloe Davis', 'Daniel Miller', 'Isabella Anderson', 'Benjamin White'
        ]

        # Fast-moving products (high probability of being in basket)
        fast_movers = [p for p in products_list if p.category in ['Fresh Produce', 'Dairy & Eggs', 'Bakery', 'Beverages']]
        all_prods = [p for p in products_list if p.name not in ["Organic Coconut Flour (1 lb)", "Artisan Smoked Sardines in Oil (4.4oz)", "Organic Beeswax Furniture Polish (8oz)"]]

        # Generate 550 sales over the last 120 days
        start_date = today - timedelta(days=120)
        total_days = 120

        sales_to_insert = []
        sale_items_to_insert = []

        global_sale_counter = 1

        for day_offset in range(total_days):
            current_date = start_date + timedelta(days=day_offset)
            is_weekend = current_date.weekday() >= 5
            # More sales on weekends and Fridays
            daily_transactions_count = random.randint(5, 10) if is_weekend else random.randint(3, 7)

            for _ in range(daily_transactions_count):
                # Pick cashier
                cashier = random.choices(cashiers, weights=[0.55, 0.35, 0.10])[0]
                customer = random.choice(customer_names)
                payment_method = random.choices(payment_methods, weights=payment_weights)[0]

                # Random realistic grocery shopping hours: 8:00 AM to 9:30 PM
                hour = random.choices(
                    list(range(8, 22)),
                    weights=[3, 5, 8, 9, 7, 6, 5, 6, 8, 10, 8, 6, 4, 2] # Morning and evening peaks
                )[0]
                minute = random.randint(0, 59)
                second = random.randint(0, 59)
                sale_time_obj = time(hour, minute, second)
                sale_datetime = datetime.combine(current_date, sale_time_obj)

                # Basket size: 1 to 5 items
                basket_size = random.choices([1, 2, 3, 4, 5], weights=[0.20, 0.35, 0.25, 0.12, 0.08])[0]
                
                # Sample products for basket
                basket_products = []
                # 70% chance of fast-moving products
                for _ in range(basket_size):
                    if random.random() < 0.70 and fast_movers:
                        basket_products.append(random.choice(fast_movers))
                    else:
                        basket_products.append(random.choice(all_prods))
                # Deduplicate by product_id
                basket_products = list({p.product_id: p for p in basket_products}.values())

                subtotal = 0.0
                basket_items_staged = []

                for prod in basket_products:
                    # Quantity per item: 1 to 3
                    qty = random.choices([1, 2, 3], weights=[0.70, 0.22, 0.08])[0]
                    line_price = prod.unit_price
                    line_cost = prod.cost_price
                    line_subtotal = round(line_price * qty, 2)
                    subtotal += line_subtotal

                    basket_items_staged.append({
                        'product_id': prod.product_id,
                        'quantity': qty,
                        'price': line_price,
                        'cost_price': line_cost,
                        'subtotal': line_subtotal
                    })

                subtotal = round(subtotal, 2)

                # Discount: ~15% chance of small discount ($0.50 to $3.00, or 5%)
                discount = 0.0
                if random.random() < 0.15 and subtotal > 10.0:
                    discount = round(random.uniform(0.50, min(5.00, subtotal * 0.10)), 2)

                total_amount = max(0.50, round(subtotal - discount, 2))
                invoice_no = f"GL-{current_date.strftime('%Y%m%d')}-{global_sale_counter:04d}"
                global_sale_counter += 1

                sale_obj = Sale(
                    invoice_no=invoice_no,
                    sale_date=current_date,
                    sale_time=sale_time_obj,
                    sale_timestamp=sale_datetime,
                    user_id=cashier.user_id,
                    customer_name=customer,
                    customer_phone=None if customer == 'Walk-in Customer' else f"(555) {random.randint(200,999)}-{random.randint(1000,9999)}",
                    payment_method=payment_method,
                    subtotal=subtotal,
                    discount=discount,
                    total_amount=total_amount
                )
                db.session.add(sale_obj)
                db.session.flush() # flush to get sale_obj.sale_id

                for bi in basket_items_staged:
                    si = SaleItem(
                        sale_id=sale_obj.sale_id,
                        product_id=bi['product_id'],
                        quantity=bi['quantity'],
                        price=bi['price'],
                        cost_price=bi['cost_price'],
                        subtotal=bi['subtotal']
                    )
                    db.session.add(si)

            # Periodic commit every 10 days
            if day_offset % 10 == 0:
                db.session.commit()
                print(f"   Progress: Seeded up to {current_date.strftime('%Y-%m-%d')} ({global_sale_counter - 1} sales)...")

        db.session.commit()
        total_sales_count = Sale.query.count()
        total_items_count = SaleItem.query.count()
        print(f"Successfully generated {total_sales_count} sales transactions with {total_items_count} line items!")
        print("\nSeed Data Summary:")
        print(f"• Users: 3 (admin: 'admin123', cashier: 'cashier123', cashier2: 'cashier123')")
        print(f"• Suppliers: {Supplier.query.count()}")
        print(f"• Catalog Products: {Product.query.count()}")
        print(f"• Total Orders: {total_sales_count}")
        print(f"• Total Revenue: ${Sale.query.with_entities(db.func.sum(Sale.total_amount)).scalar():,.2f}")
        print("Ready to run GreenLeaf Grocers application!")

if __name__ == '__main__':
    seed_database()
