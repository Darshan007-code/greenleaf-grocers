// GreenLeaf Grocers POS Logic
class POSController {
    constructor() {
        this.cart = []; // Array of { product_id, name, unit_price, stock_qty, quantity, barcode }
        this.discount = 0.0;
        this.paymentMethod = 'Cash';
        this.init();
    }

    init() {
        this.bindEvents();
        this.renderCart();
    }

    bindEvents() {
        // Barcode reader input
        const barcodeInput = document.getElementById('posBarcodeInput');
        if (barcodeInput) {
            barcodeInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    this.lookupBarcode(barcodeInput.value.trim());
                    barcodeInput.value = '';
                }
            });
        }

        // Search live filter
        const searchInput = document.getElementById('posSearchInput');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                this.searchProducts(e.target.value.trim());
            });
        }

        // Category filter buttons
        const categoryButtons = document.querySelectorAll('.cat-filter-btn');
        categoryButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                categoryButtons.forEach(b => b.classList.remove('active', 'btn-success'));
                categoryButtons.forEach(b => b.classList.add('btn-outline-secondary'));
                btn.classList.add('active', 'btn-success');
                btn.classList.remove('btn-outline-secondary');
                this.filterCategory(btn.dataset.category);
            });
        });

        // Discount input
        const discountInput = document.getElementById('posDiscountInput');
        if (discountInput) {
            discountInput.addEventListener('input', (e) => {
                this.discount = parseFloat(e.target.value) || 0.0;
                this.updateTotals();
            });
        }

        // Checkout submit
        const checkoutBtn = document.getElementById('posCheckoutBtn');
        if (checkoutBtn) {
            checkoutBtn.addEventListener('click', () => this.handleCheckout());
        }

        // Clear cart
        const clearBtn = document.getElementById('posClearCartBtn');
        if (clearBtn) {
            clearBtn.addEventListener('click', () => {
                if (this.cart.length > 0 && confirm('Clear current cart?')) {
                    this.cart = [];
                    this.renderCart();
                }
            });
        }
    }

    async lookupBarcode(barcode) {
        if (!barcode) return;
        try {
            const res = await fetch(`/products/api/barcode/${encodeURIComponent(barcode)}`);
            if (res.ok) {
                const product = await res.json();
                this.addToCart(product);
            } else {
                this.showToast(`Product with barcode "${barcode}" not found.`, 'danger');
            }
        } catch (err) {
            this.showToast('Error looking up barcode.', 'danger');
        }
    }

    async searchProducts(query) {
        const activeCat = document.querySelector('.cat-filter-btn.active')?.dataset.category || '';
        try {
            const res = await fetch(`/products/api/search?q=${encodeURIComponent(query)}&category=${encodeURIComponent(activeCat)}`);
            if (res.ok) {
                const products = await res.json();
                this.renderProductGrid(products);
            }
        } catch (err) {
            console.error('Search error:', err);
        }
    }

    filterCategory(category) {
        const query = document.getElementById('posSearchInput')?.value.trim() || '';
        this.searchProducts(query);
    }

    renderProductGrid(products) {
        const grid = document.getElementById('posProductGrid');
        if (!grid) return;

        if (products.length === 0) {
            grid.innerHTML = `<div class="col-12 text-center text-muted py-5">No products found matching criteria.</div>`;
            return;
        }

        grid.innerHTML = products.map(p => {
            const outOfStock = p.stock_qty <= 0;
            return `
            <div class="col-6 col-md-4 col-xl-3">
                <div class="pos-product-card p-3 h-100 d-flex flex-column justify-content-between ${outOfStock ? 'out-of-stock' : ''}"
                     onclick="${outOfStock ? '' : `pos.addToCart(${JSON.stringify(p).replace(/"/g, '&quot;')})`}">
                    <div>
                        <div class="d-flex justify-content-between align-items-start mb-1">
                            <span class="badge bg-light text-secondary small">${p.category}</span>
                            <span class="badge ${p.is_low_stock ? 'badge-low-stock' : 'badge-healthy'}">${p.stock_qty} left</span>
                        </div>
                        <h6 class="fw-bold text-dark mb-1 text-truncate" title="${p.name}">${p.name}</h6>
                        <small class="text-muted d-block font-monospace" style="font-size: 0.75rem;">${p.barcode || ''}</small>
                    </div>
                    <div class="mt-2 pt-2 border-top d-flex justify-content-between align-items-center">
                        <span class="fw-bold text-success fs-5">$${p.unit_price.toFixed(2)}</span>
                        ${outOfStock ? '<span class="badge bg-danger">Sold Out</span>' : '<button class="btn btn-sm btn-outline-success"><i class="fa-solid fa-plus"></i></button>'}
                    </div>
                </div>
            </div>`;
        }).join('');
    }

    addToCart(product) {
        const existing = this.cart.find(item => item.product_id === product.product_id);
        if (existing) {
            if (existing.quantity >= product.stock_qty) {
                this.showToast(`Cannot add more. Only ${product.stock_qty} in stock.`, 'warning');
                return;
            }
            existing.quantity += 1;
        } else {
            if (product.stock_qty <= 0) {
                this.showToast(`'${product.name}' is out of stock!`, 'danger');
                return;
            }
            this.cart.push({
                product_id: product.product_id,
                name: product.name,
                unit_price: product.unit_price,
                stock_qty: product.stock_qty,
                quantity: 1,
                barcode: product.barcode
            });
        }
        this.renderCart();
    }

    updateQuantity(productId, delta) {
        const item = this.cart.find(i => i.product_id === productId);
        if (!item) return;

        const newQty = item.quantity + delta;
        if (newQty <= 0) {
            this.removeFromCart(productId);
            return;
        }
        if (newQty > item.stock_qty) {
            this.showToast(`Max available stock is ${item.stock_qty}.`, 'warning');
            return;
        }
        item.quantity = newQty;
        this.renderCart();
    }

    removeFromCart(productId) {
        this.cart = this.cart.filter(i => i.product_id !== productId);
        this.renderCart();
    }

    renderCart() {
        const container = document.getElementById('cartItemsContainer');
        const emptyMsg = document.getElementById('emptyCartMsg');
        const checkoutBtn = document.getElementById('posCheckoutBtn');

        if (!container) return;

        if (this.cart.length === 0) {
            container.innerHTML = '';
            if (emptyMsg) emptyMsg.style.display = 'block';
            if (checkoutBtn) checkoutBtn.disabled = true;
            this.updateTotals();
            return;
        }

        if (emptyMsg) emptyMsg.style.display = 'none';
        if (checkoutBtn) checkoutBtn.disabled = false;

        container.innerHTML = this.cart.map(item => `
            <div class="d-flex align-items-center justify-content-between p-2 mb-2 bg-light rounded-3 border">
                <div style="max-width: 50%;">
                    <div class="fw-semibold text-dark text-truncate small" title="${item.name}">${item.name}</div>
                    <div class="text-muted small">$${item.unit_price.toFixed(2)} ea</div>
                </div>
                <div class="d-flex align-items-center gap-1">
                    <button class="btn btn-sm btn-outline-secondary py-0 px-2" onclick="pos.updateQuantity(${item.product_id}, -1)">-</button>
                    <span class="fw-bold px-2 small">${item.quantity}</span>
                    <button class="btn btn-sm btn-outline-secondary py-0 px-2" onclick="pos.updateQuantity(${item.product_id}, 1)">+</button>
                </div>
                <div class="text-end" style="min-width: 65px;">
                    <span class="fw-bold text-success small d-block">$${(item.unit_price * item.quantity).toFixed(2)}</span>
                    <button class="btn btn-sm text-danger p-0" onclick="pos.removeFromCart(${item.product_id})" title="Remove">
                        <i class="fa-solid fa-trash-can" style="font-size: 0.75rem;"></i>
                    </button>
                </div>
            </div>
        `).join('');

        this.updateTotals();
    }

    updateTotals() {
        const subtotal = this.cart.reduce((sum, item) => sum + (item.unit_price * item.quantity), 0.0);
        let discount = Math.max(0.0, this.discount);
        if (discount > subtotal) {
            discount = subtotal;
        }
        const total = Math.max(0.0, subtotal - discount);

        const subtotalEl = document.getElementById('cartSubtotal');
        const discountEl = document.getElementById('cartDiscount');
        const totalEl = document.getElementById('cartTotal');
        const itemCountEl = document.getElementById('cartItemCount');

        if (subtotalEl) subtotalEl.textContent = `$${subtotal.toFixed(2)}`;
        if (discountEl) discountEl.textContent = `-$${discount.toFixed(2)}`;
        if (totalEl) totalEl.textContent = `$${total.toFixed(2)}`;
        if (itemCountEl) itemCountEl.textContent = this.cart.reduce((sum, i) => sum + i.quantity, 0);
    }

    async handleCheckout() {
        if (this.cart.length === 0) {
            this.showToast('Your cart is empty!', 'warning');
            return;
        }

        const customerName = document.getElementById('posCustomerName')?.value.trim() || 'Walk-in Customer';
        const customerPhone = document.getElementById('posCustomerPhone')?.value.trim() || '';
        const paymentMethod = document.getElementById('posPaymentMethod')?.value || 'Cash';
        const notes = document.getElementById('posNotes')?.value.trim() || '';

        const checkoutBtn = document.getElementById('posCheckoutBtn');
        if (checkoutBtn) {
            checkoutBtn.disabled = true;
            checkoutBtn.innerHTML = `<span class="spinner-border spinner-border-sm me-1"></span> Processing...`;
        }

        const payload = {
            items: this.cart.map(i => ({ product_id: i.product_id, quantity: i.quantity })),
            discount: this.discount,
            payment_method: paymentMethod,
            customer_name: customerName,
            customer_phone: customerPhone,
            notes: notes
        };

        try {
            const res = await fetch('/billing/api/checkout', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            const data = await res.json();
            if (res.ok && data.success) {
                // Show checkout success modal
                this.showSuccessModal(data);
                // Clear cart
                this.cart = [];
                this.discount = 0.0;
                document.getElementById('posDiscountInput').value = '0';
                this.renderCart();
            } else {
                this.showToast(data.message || 'Checkout failed. Please try again.', 'danger');
            }
        } catch (err) {
            this.showToast('Network error during checkout.', 'danger');
        } finally {
            if (checkoutBtn) {
                checkoutBtn.disabled = false;
                checkoutBtn.innerHTML = `<i class="fa-solid fa-check-double me-1"></i> Complete Checkout`;
            }
        }
    }

    showSuccessModal(data) {
        document.getElementById('modalInvoiceNo').textContent = data.invoice_no;
        document.getElementById('modalTotalAmount').textContent = `$${parseFloat(data.total_amount).toFixed(2)}`;
        document.getElementById('modalReceiptLink').href = data.receipt_url;
        document.getElementById('modalPdfLink').href = data.pdf_url;

        const modalEl = document.getElementById('checkoutSuccessModal');
        const modal = new bootstrap.Modal(modalEl);
        modal.show();
    }

    showToast(message, type = 'info') {
        const toastContainer = document.getElementById('posToastContainer');
        if (!toastContainer) {
            alert(message);
            return;
        }

        const toastEl = document.createElement('div');
        toastEl.className = `alert alert-${type} alert-dismissible fade show shadow-sm`;
        toastEl.innerHTML = `
            <span>${message}</span>
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        toastContainer.appendChild(toastEl);
        setTimeout(() => toastEl.remove(), 4500);
    }
}

// Global instance
let pos;
document.addEventListener('DOMContentLoaded', () => {
    pos = new POSController();
});
