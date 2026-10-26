# 📋 Technical Project Report: GreenLeaf Grocers Inventory & Sales Management System

**Developer Project | Level: Medium**  
**Author:** Antigravity Engineering  
**Application:** GreenLeaf Grocers Inventory, POS & Analytics Platform  
**Date:** October 2026  

---

## 1. Executive Summary & Problem Context

Small and mid-sized retail grocery stores routinely struggle with manual inventory registers and disconnected spreadsheets. At **GreenLeaf Grocers**, this led to four acute operational challenges:
1. **Frequent Stock-Outs**: Fast-moving staple products ran out unmonitored.
2. **Perishable Waste & Expiry Losses**: Inability to identify near-expiry inventory before spoilage.
3. **Billing Errors & Sluggish Checkout**: Manual price checks and lack of cashier accountability.
4. **Blind Strategic Decisions**: Store owners lacked real-time visibility into daily revenue velocity, top categories, and stagnant stock.

To address these pain points, we engineered a modular Python web application combining a normalized relational database (SQLite via SQLAlchemy), an interactive Point-of-Sale billing interface with barcode support, and a Pandas-powered analytical engine with Chart.js visualizations.

---

## 2. System Architecture & Database Design

### 2.1 Architectural Pattern
The application follows the **Application Factory** pattern with modular Flask blueprints:
- **Presentation Layer**: Responsive server-rendered templates using Bootstrap 5, FontAwesome 6, and Chart.js 4.
- **Controller/Routing Layer**: Blueprints for `auth`, `dashboard`, `products`, `billing`, `reports`, and `suppliers`.
- **Service/Domain Layer**: Decoupled business logic:
  - `BillingService`: Cart validation, invoice generation, and atomic stock deductions.
  - `AnalyticsService`: Pandas DataFrames, KPI metrics, and forecasting models.
  - `PDFReceiptGenerator`: Programmatic PDF generation with ReportLab.
- **Persistence Layer**: SQLAlchemy 2.0 ORM with SQLite.

### 2.2 Database Normalization Analysis
The schema was designed strictly to **Third Normal Form (3NF)**:
1. **First Normal Form (1NF)**: All column values are atomic (e.g., individual item quantities and prices are extracted from sales into `sale_items`). Primary keys are established on all entities.
2. **Second Normal Form (2NF)**: Eliminates partial dependencies. `SaleItem` composite dependency is resolved with a surrogate primary key `sale_item_id`. Crucially, `unit_price` and `cost_price` are snapshotted in `sale_items` at the moment of sale, guaranteeing that future catalog price adjustments do not retroactively distort historical accounting.
3. **Third Normal Form (3NF)**: Transitive dependencies are removed. Product suppliers are factored into an independent `suppliers` table and linked by foreign key `supplier_id`. Cashier attribution relies on foreign key `user_id`.

```text
+---------------+        +----------------+        +---------------+
|     USERS     | 1    * |     SALES      | 1    * |  SALE_ITEMS   |
| (user_id PK)  |--------|  (sale_id PK)  |--------| (item_id PK)  |
+---------------+        +----------------+        +---------------+
                                                          | *
                                                          | 1
+---------------+ 1    * +----------------+               |
|   SUPPLIERS   |--------|    PRODUCTS    |---------------+
| (supp_id PK)  |        | (prod_id PK)   |
+---------------+        +----------------+
```

---

## 3. Data Analysis Methodology (Pandas Engine)

Analytics are powered by querying raw relational data directly into **Pandas DataFrames** (`app/services/analytics.py`), unlocking high-performance vector operations and aggregations:

### 3.1 KPIs Evaluated
1. **Total Revenue**: $\sum \text{total\_amount}$ across the selected date window.
2. **Average Bill Value**: $\frac{\text{Total Revenue}}{\text{Number of Unique Orders}}$, measuring customer basket yield.
3. **Stock Turnover Ratio**:
   $$\text{Stock Turnover} = \frac{\text{Total COGS}}{\text{Total Active Inventory Value}}$$
   Measures inventory velocity and capital turnover speed.
4. **Low-Stock Items Count**: Count of active SKUs where $\text{stock\_qty} \le \text{reorder\_level}$.
5. **Top Category Share (%)**: $\frac{\text{Revenue of Leading Category}}{\text{Total Revenue}} \times 100$.

### 3.2 Advanced Insights
- **Top 10 Best Sellers**: Dynamically ranked with an interactive frontend toggle switching between **Gross Revenue** and **Total Volume Sold**.
- **Category Sales Share**: Evaluated through `df.groupby('category')['subtotal'].sum()`, rendered as a doughnut distribution.
- **Slow-Moving Products**: Identifies products where units sold in the preceding 30 days $\le 3$ units, and computes the exact dollar value of capital trapped on shelves.
- **7-Day Sales Forecast (Bonus Feature)**: Computes a rolling trend line using linear regression ($y = mx + c$) across daily historical revenue to predict future daily turnover.

---

## 4. Point-of-Sale (POS) & Concurrency Safety

### 4.1 Stock Overdraw Prevention
In retail environments, multiple items may be checked out rapidly. To prevent stock from dropping below zero or inconsistent states:
1. Every line item's requested quantity is compared against `product.stock_qty`.
2. Deductions are staged atomically within the same database transaction.
3. If any line item exceeds available inventory, the entire checkout aborts with a descriptive `BillingException`, rolling back any staged changes.

### 4.2 Barcode & Quick Checkout Workflow
The POS interface integrates:
- Barcode scanning input with automatic enter-key detection.
- Real-time client-side subtotal, discount, and grand total calculations.
- Clean printable receipt view with CSS print media queries.
- Instant PDF generation using ReportLab.

---

## 5. Validation & Error Handling Strategy

To guarantee store uptime and cashier convenience:
- **Price & Quantity Rules**: Enforces $unit\_price \ge 0$, $stock\_qty \ge 0$, and $quantity > 0$.
- **Date Integrity**: Strict parsing with standard `YYYY-MM-DD` validation and leap-year compliance.
- **Soft Deletion**: Products that have historical sales records cannot be hard deleted (which would break foreign key referential integrity). Instead, they are flagged `is_active = False`, hiding them from the POS while preserving audit history.
- **Friendly Feedback**: All errors are surfaced via dismissible Bootstrap alert banners and never unhandled 500 exceptions.

---

## 6. Testing Strategy & Quality Verification

The project includes an automated test suite with **26 unit and integration tests** built using `pytest`:
- **Isolation**: Tests execute against an ephemeral, in-memory SQLite database (`sqlite:///:memory:`).
- **Authentication Tests**: Verifies role separation, session lifecycle, and redirect targets.
- **Billing Tests**: Validates checkout, atomic stock decrements, overdraw exceptions, negative quantity rejection, and invoice sequences.
- **Analytics Tests**: Tests KPI precision, daily/monthly groupings, top seller rankings, and slow-moving inventory filters.

**Result**: 26 passed in 6.35s with 100% success rate and zero warnings.

---

## 7. Challenges & Key Learnings

| Challenge | Root Cause | Solution Implemented |
| :--- | :--- | :--- |
| **Historical Price Drift** | Catalog product prices change over time; calculating historical revenue from current catalog prices distorts past accounts. | Snapshot `price` and `cost_price` into each `sale_items` row at the moment of sale. |
| **Python 3.13 / SQLAlchemy 2.0 Deprecations** | `datetime.utcnow()` and legacy `Query.get()` trigger warnings in modern Python 3.13. | Refactored all models and queries to use `datetime.now(timezone.utc)` and `db.session.get()`. |
| **Receipt Printing Compatibility** | Browser print dialog prints full web headers and sidebars. | Crafted CSS `@media print` rules isolating only the `.receipt-paper` container and hiding navigation controls. |
| **Accidental Deletion of Sold Goods** | Hard-deleting a product violates foreign keys on `sale_items`. | Implemented intelligent conditional deletion: soft deactivation (`is_active = False`) if orders exist, hard delete otherwise. |

---

## 8. Conclusion & Future Roadmap

The **GreenLeaf Grocers Inventory & Sales Management System** transitions store management from fragmented registers to a secure, data-driven web platform. 

### Future Enhancements:
- **Hardware Integration**: Direct USB POS thermal printer support via ESC/POS protocol.
- **Automated Email Restock Orders**: Automated purchase order generation sent directly to suppliers when stock reaches reorder levels.
- **Docker Containerization**: Multi-container Docker Compose setup with Nginx reverse proxy and Gunicorn WSGI server.
