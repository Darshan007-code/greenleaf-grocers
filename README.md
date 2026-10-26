# 🥬 GreenLeaf Grocers - Inventory & Sales Management System

A production-grade Python web application for retail grocery inventory tracking, Point of Sale (POS) billing, automated stock replenishment alerts, and business intelligence analytics. Built with **Flask**, **SQLite**, **SQLAlchemy**, **Pandas**, and **Chart.js**.

---

## 📌 Executive Summary & Background

Small and mid-sized retail grocery stores commonly face inventory inaccuracies, expiry spoilage, stock-outs on fast-moving goods, and lack of visibility into daily revenue velocity. **GreenLeaf Grocers** solves these challenges with:
- **Centralized Inventory Database**: Normalized relational database storing products, suppliers, cashiers, sales, and line items.
- **Real-Time Point-of-Sale (POS)**: Barcode scanning, multi-item basket billing, instant stock deduction, and thermal/PDF receipt generation.
- **Operational Safety Alerts**: Real-time alerts for low-stock reordering and near-expiry goods (&le; 15 days) to eliminate inventory waste.
- **Analytics & BI Dashboard**: Pandas-powered revenue trends, Top 10 selling products (with revenue/volume toggling), category share distributions, slow-moving inventory tracking, and 7-day predictive sales forecasting.
- **Role-Based Access Control**: Strict segregation between store administrators and cashiers.

---

## 🏗 System Architecture & Database Design

### Normalized Database Schema (3NF)

```mermaid
erDiagram
    USERS ||--o{ SALES : "processes"
    SUPPLIERS ||--o{ PRODUCTS : "supplies"
    PRODUCTS ||--o{ SALE_ITEMS : "included_in"
    SALES ||--|{ SALE_ITEMS : "contains"

    USERS {
        int user_id PK
        string username UK
        string password_hash
        string role "admin | cashier"
        string full_name
        datetime created_at
    }

    SUPPLIERS {
        int supplier_id PK
        string name
        string phone
        string email
        string contact_person
        text address
        datetime created_at
    }

    PRODUCTS {
        int product_id PK
        string name INDEX
        string category INDEX
        float unit_price
        float cost_price
        int stock_qty
        int reorder_level
        date expiry_date INDEX
        string barcode UK
        int supplier_id FK
        boolean is_active
        datetime created_at
    }

    SALES {
        int sale_id PK
        string invoice_no UK
        date sale_date INDEX
        time sale_time
        datetime sale_timestamp INDEX
        int user_id FK
        string customer_name
        string customer_phone
        string payment_method
        float subtotal
        float discount
        float total_amount
        text notes
    }

    SALE_ITEMS {
        int sale_item_id PK
        int sale_id FK
        int product_id FK
        int quantity
        float price
        float cost_price
        float subtotal
    }
```

### Table Normalization Rationale
- **1NF**: Atomic column values with primary keys identified on all entities.
- **2NF**: No partial dependencies; all non-key attributes in `sale_items` depend on the composite entity representation. Historical prices are snapshot in `sale_items` to protect against subsequent product price changes.
- **3NF**: Non-key columns depend only on primary keys. Supplier contact information is isolated in `suppliers` and referenced via foreign key `supplier_id`.

---

## ⚡ Quickstart & Installation

### 1. Prerequisites
- Python 3.10+ (tested on Python 3.13)
- pip

### 2. Clone / Setup Workspace
```bash
cd greenleaf-grocers
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Seed Database with Realistic Sample Data
The `seed_data.py` script populates the database with:
- 3 User accounts (1 Admin, 2 Cashiers)
- 6 Grocery suppliers
- 59 Distinct products across 8 categories
- 670+ Historical sales transactions spread across the past 4 months

```bash
python seed_data.py
```

### 5. Launch Application
```bash
python run.py
```
Open your browser and navigate to: **`http://127.0.0.1:5000`**

---

## 🔐 Default User Credentials

| Role | Username | Password | Permitted Modules |
| :--- | :--- | :--- | :--- |
| **Store Admin** | `admin` | `admin123` | Dashboard, Products, Suppliers, POS Billing, Reports, CSV Import/Export |
| **Cashier 1** | `cashier` | `cashier123` | POS Billing Terminal, Order History, Receipts |
| **Cashier 2** | `cashier2` | `cashier123` | POS Billing Terminal, Order History, Receipts |

> **Note**: A quick-fill credential helper is embedded right on the `/login` screen for one-click demo testing.

---

## 🚀 Key Modules & Functional Features

### 1. Role-Based Access Control (RBAC)
- Admin accounts have full permissions across inventory CRUD, supplier tracking, analytics reports, and product imports.
- Cashier accounts are restricted to the POS Billing screen and Sales History; attempts to access `/products`, `/reports`, or `/suppliers` automatically trigger security flash warnings and redirect to `/billing/pos`.

### 2. Point of Sale (POS) Billing Terminal
- **Barcode Lookup**: Instant lookup by typing or scanning a 12-digit barcode and pressing Enter.
- **Instant Product Search & Category Filtering**: Filter by category chips (Produce, Dairy, Bakery, etc.) or search live by name.
- **Stock Validation & Overdraw Prevention**: Real-time safeguards prevent adding more items than currently in stock. Zero or negative quantities are strictly rejected.
- **Discounts & Payment Methods**: Supports cash, credit card, and digital/UPI payments with automatic total recalculation.
- **Atomic Stock Deduction**: Completed checkout decrements inventory quantities atomically inside an isolated database transaction.

### 3. Invoicing & Receipt Generation
- **Printable Thermal/A4 Receipt**: Clean web view formatted for POS receipt printers (`window.print()`).
- **PDF Tax Invoice**: Formatted receipt generated dynamically with **ReportLab** (`/billing/receipt/<id>/pdf`).
- **CSV Receipt Export**: Downloadable raw CSV transaction records.

### 4. Inventory Catalog Management
- **Product CRUD**: Add, edit, soft-delete products with validation for negative price/stock.
- **CSV Bulk Import**: Upload `.csv` files with validation reporting skipped/invalid rows.
- **CSV Catalog Export**: Export current inventory with health status flags.

### 5. Analytics & Business Intelligence Dashboard
- **5 Core KPIs**:
  1. **Total Revenue**: Total sales in selected date range.
  2. **Average Bill Value**: Total revenue divided by number of completed orders.
  3. **Stock Turnover Ratio**: Cost of Goods Sold (or sales) divided by total inventory value.
  4. **Low-Stock Items Count**: Products whose quantity is &le; reorder threshold.
  5. **Top Category Share (%)**: Percentage revenue contributed by the best-selling category.
- **Interactive Visualizations (Chart.js)**:
  - Daily sales revenue and volume bar/line chart.
  - Monthly sales history trend.
  - Top 10 Best Sellers with instant toggle between **Revenue ($)** and **Quantity Sold**.
  - Category revenue distribution doughnut chart.
  - **7-Day Sales Forecast (Bonus)**: Linear regression trend modeling future daily demand.
- **Dedicated Operational Reports**:
  - **Low-Stock & Reorder Report**: Calculates replenishments needed (`reorder_level * 2 - stock_qty`) and displays supplier contact phone/email.
  - **Expiry Tracker & Waste Prevention**: Flags items expiring within 15 days or already expired, calculating total financial capital at risk.
  - **Slow-Moving Goods**: Identifies items with &le; 3 sales in 30 days and calculates capital tied up.

---

## 🧪 Testing Strategy & Verification

The test suite contains **26 unit and integration tests** executing against an isolated in-memory SQLite database (`sqlite:///:memory:`).

### Run Test Suite
```bash
python -m pytest tests/ -v
```

### Test Coverage Highlights
- `tests/test_auth.py`: Admin/cashier authentication, role-based route guards, session clearing.
- `tests/test_products.py`: Input validation, negative price/stock rejection, duplicate barcode prevention, search APIs.
- `tests/test_billing.py`: Atomic stock deduction, overdraw prevention, discount logic, invoice sequence format, PDF generation.
- `tests/test_analytics.py`: KPI calculations, daily/monthly pandas aggregations, top products sorting, category share, slow-moving detection.

---

## 📂 Project Structure

```text
greenleaf-grocers/
├── app/
│   ├── __init__.py           # Flask app factory, custom filters, global alert context
│   ├── config.py             # Development, Testing, Production configurations
│   ├── database.py           # SQLAlchemy instance
│   ├── models.py             # User, Product, Supplier, Sale, SaleItem models
│   ├── routes/
│   │   ├── auth.py           # Authentication & role-based route guards
│   │   ├── billing.py        # POS terminal, checkout API, receipt views, PDF download
│   │   ├── dashboard.py      # Admin executive KPI dashboard
│   │   ├── products.py       # Product catalog CRUD, CSV import/export, barcode API
│   │   ├── reports.py        # Analytics, low-stock, expiry, CSV export
│   │   └── suppliers.py      # Supplier vendor management
│   ├── services/
│   │   ├── analytics.py      # Pandas aggregations, KPIs, 7-day forecast
│   │   ├── billing_service.py# Checkout transaction logic & atomic stock deduction
│   │   └── pdf_service.py    # ReportLab PDF invoice generation
│   ├── static/
│   │   ├── css/style.css     # Responsive UI styling & print receipt styles
│   │   └── js/pos.js         # POS terminal interactive cart controller
│   └── templates/
│       ├── base.html         # Base template with responsive navbar & alert badges
│       ├── 404.html & 500.html
│       ├── auth/login.html
│       ├── dashboard/index.html
│       ├── products/ (index.html, form.html, import.html)
│       ├── billing/ (pos.html, receipt.html, sales_list.html)
│       ├── reports/ (index.html, low_stock.html, expiry.html)
│       └── suppliers/ (index.html, form.html)
├── sample_data/
│   └── sample_products_import.csv
├── tests/
│   ├── conftest.py           # In-memory test database & fixtures
│   ├── test_analytics.py
│   ├── test_auth.py
│   ├── test_billing.py
│   └── test_products.py
├── PROJECT_REPORT.md         # Detailed technical design & learnings report
├── README.md                 # Setup guide and documentation
├── requirements.txt          # Python dependencies
├── run.py                    # Application entry point
└── seed_data.py              # Realistic sample data generator (50+ products, 500+ sales)
```
