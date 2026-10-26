// GreenLeaf Grocers POS Controller - Enhanced & Smooth Edition
class POSController {
    constructor() {
        this.cart = [];
        this.discount = 0.0;
        this.paymentMethod = 'Cash';
        this.cashTendered = 0.0;
        this.soundEnabled = true;
        this.categoryIcons = {
            'Fresh Produce': '🥦',
            'Dairy & Eggs': '🥛',
            'Bakery': '🥐',
            'Beverages': '🧃',
            'Pantry & Grains': '🌾',
            'Snacks & Sweets': '🍫',
            'Canned & Packaged': '🥫',
            'Household Essentials': '🧼'
        };
        this.init();
    }

    init() {
        this.bindEvents();
        this.renderCart();
    }

    // Web Audio Sound Engine (zero external dependencies)
    playTone(type) {
        if (!this.soundEnabled) return;
        try {
            const ctx = new (window.AudioContext || window.webkitAudioContext)();
            const osc = ctx.createOscillator();
            const gain = ctx.createGain();
            osc.connect(gain);
            gain.connect(ctx.destination);

            if (type === 'beep') {
                // Short affirmative chime
                osc.type = 'sine';
                osc.frequency.setValueAtTime(587.33, ctx.currentTime); // D5
                gain.gain.setValueAtTime(0.08, ctx.currentTime);
                gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.12);
                osc.start(ctx.currentTime);
                osc.stop(ctx.currentTime + 0.12);
            } else if (type === 'success') {
                // Happy chord
                [523.25, 659.25, 783.99].forEach((freq, idx) => {
                    const o = ctx.createOscillator();
                    const g = ctx.createGain();
                    o.connect(g);
                    g.connect(ctx.destination);
                    o.type = 'triangle';
                    o.frequency.setValueAtTime(freq, ctx.currentTime + idx * 0.07);
                    g.gain.setValueAtTime(0.07, ctx.currentTime + idx * 0.07);
                    g.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + idx * 0.07 + 0.25);
                    o.start(ctx.currentTime + idx * 0.07);
                    o.stop(ctx.currentTime + idx * 0.07 + 0.25);
                });
            } else if (type === 'error') {
                // Warning tone
                osc.type = 'sawtooth';
                osc.frequency.setValueAtTime(220, ctx.currentTime);
                gain.gain.setValueAtTime(0.08, ctx.currentTime);
                gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.18);
                osc.start(ctx.currentTime);
                osc.stop(ctx.currentTime + 0.18);
            }
        } catch (e) {
            // Audio context not allowed or unsupported
        }
    }

    bindEvents() {
        // Barcode input
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

        // Live search input
        const searchInput = document.getElementById('posSearchInput');
        if (searchInput) {
            let debounceTimer;
            searchInput.addEventListener('input', (e) => {
                clearTimeout(debounceTimer);
                debounceTimer = setTimeout(() => {
                    this.searchProducts(e.target.value.trim());
                }, 150);
            });
        }

        // Category filter buttons
        const categoryButtons = document.querySelectorAll('.cat-filter-btn');
        categoryButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                categoryButtons.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
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

        // Payment method selector
        const paymentSelect = document.getElementById('posPaymentMethod');
        const tenderContainer = document.getElementById('cashTenderContainer');
        if (paymentSelect) {
            paymentSelect.addEventListener('change', (e) => {
                this.paymentMethod = e.target.value;
                if (tenderContainer) {
                    tenderContainer.style.display = (this.paymentMethod === 'Cash') ? 'block' : 'none';
                }
            });
        }

        // Cash Tendered input
        const tenderInput = document.getElementById('posCashTendered');
        if (tenderInput) {
            tenderInput.addEventListener('input', (e) => {
                this.cashTendered = parseFloat(e.target.value) || 0.0;
                this.updateChangeDue();
            });
        }

        // Checkout button
        const checkoutBtn = document.getElementById('posCheckoutBtn');
        if (checkoutBtn) {
            checkoutBtn.addEventListener('click', () => this.handleCheckout());
        }

        // Clear cart
        const clearBtn = document.getElementById('posClearCartBtn');
        if (clearBtn) {
            clearBtn.addEventListener('click', () => {
                if (this.cart.length > 0 && confirm('Clear the current shopping cart?')) {
                    this.cart = [];
                    this.renderCart();
                }
            });
        }

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.key === 'F2') {
                e.preventDefault();
                document.getElementById('posSearchInput')?.focus();
            } else if (e.key === 'F4') {
                e.preventDefault();
                document.getElementById('posBarcodeInput')?.focus();
            } else if (e.altKey && e.key.toLowerCase() === 'c') {
                e.preventDefault();
                this.handleCheckout();
            }
        });
    }

    async lookupBarcode(barcode) {
        if (!barcode) return;
        try {
            const res = await fetch(`/products/api/barcode/${encodeURIComponent(barcode)}`);
            if (res.ok) {
                const product = await res.json();
                this.addToCart(product);
                this.showToast(`Scanned: ${product.name}`, 'success');
            } else {
                this.playTone('error');
                this.showToast(`Barcode "${barcode}" not recognized.`, 'danger');
            }
        } catch (err) {
            this.playTone('error');
            this.showToast('Network error during barcode lookup.', 'danger');
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
            grid.innerHTML = `
                <div class="col-12 text-center text-muted py-5">
                    <i class="fa-solid fa-box-open fs-1 text-muted mb-2 d-block opacity-50"></i>
                    <p class="mb-0">No matching items found.</p>
                </div>`;
            return;
        }

        grid.innerHTML = products.map(p => {
            const outOfStock = p.stock_qty <= 0;
            const icon = this.categoryIcons[p.category] || '📦';
            return `
            <div class="col-6 col-md-4 col-xl-3">
                <div class="pos-product-card p-3 h-100 d-flex flex-column justify-content-between ${outOfStock ? 'out-of-stock' : ''}"
                     onclick="${outOfStock ? '' : `pos.addToCart(${JSON.stringify(p).replace(/"/g, '&quot;')})`}">
                    <div>
                        <div class="d-flex justify-content-between align-items-center mb-2">
                            <span class="category-icon-pill" title="${p.category}">${icon}</span>
                            <span class="badge ${p.stock_qty <= 0 ? 'bg-danger' : (p.is_low_stock ? 'badge-low-stock' : 'badge-healthy')}">
                                ${p.stock_qty <= 0 ? 'Out of Stock' : p.stock_qty + ' left'}
                            </span>
                        </div>
                        <h6 class="fw-bold text-dark mb-1 text-truncate" title="${p.name}">${p.name}</h6>
                        <small class="text-muted d-block font-monospace" style="font-size: 0.72rem;">${p.barcode || p.category}</small>
                    </div>
                    <div class="mt-3 pt-2 border-top d-flex justify-content-between align-items-center">
                        <span class="fw-bold text-success fs-5">$${p.unit_price.toFixed(2)}</span>
                        ${outOfStock ? '' : '<button class="btn btn-sm btn-outline-success rounded-circle" style="width: 30px; height: 30px; padding: 0;"><i class="fa-solid fa-plus"></i></button>'}
                    </div>
                </div>
            </div>`;
        }).join('');
    }

    addToCart(product) {
        const existing = this.cart.find(item => item.product_id === product.product_id);
        if (existing) {
            if (existing.quantity >= product.stock_qty) {
                this.playTone('error');
                this.showToast(`Cannot add more. Only ${product.stock_qty} available in stock.`, 'warning');
                return;
            }
            existing.quantity += 1;
        } else {
            if (product.stock_qty <= 0) {
                this.playTone('error');
                this.showToast(`'${product.name}' is out of stock!`, 'danger');
                return;
            }
            this.cart.push({
                product_id: product.product_id,
                name: product.name,
                category: product.category,
                unit_price: product.unit_price,
                stock_qty: product.stock_qty,
                quantity: 1,
                barcode: product.barcode
            });
        }
        this.playTone('beep');
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
            this.playTone('error');
            this.showToast(`Maximum available stock is ${item.stock_qty}.`, 'warning');
            return;
        }
        item.quantity = newQty;
        this.playTone('beep');
        this.renderCart();
    }

    removeFromCart(productId) {
        this.cart = this.cart.filter(i => i.product_id !== productId);
        this.renderCart();
    }

    applyPresetDiscount(type, val) {
        const subtotal = this.cart.reduce((sum, item) => sum + (item.unit_price * item.quantity), 0.0);
        if (subtotal <= 0) return;

        let disc = 0.0;
        if (type === 'fixed') {
            disc = Math.min(val, subtotal);
        } else if (type === 'percent') {
            disc = Math.round((subtotal * (val / 100)) * 100) / 100;
        }

        this.discount = disc;
        const discountInput = document.getElementById('posDiscountInput');
        if (discountInput) discountInput.value = disc.toFixed(2);
        this.updateTotals();
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
            <div class="cart-item-row d-flex align-items-center justify-content-between">
                <div style="max-width: 48%;">
                    <div class="fw-bold text-dark text-truncate small" title="${item.name}">${item.name}</div>
                    <div class="text-muted small">$${item.unit_price.toFixed(2)} ea</div>
                </div>
                <div class="d-flex align-items-center gap-1">
                    <button class="btn btn-sm btn-light border qty-btn" onclick="pos.updateQuantity(${item.product_id}, -1)">-</button>
                    <span class="fw-bold px-2 small">${item.quantity}</span>
                    <button class="btn btn-sm btn-light border qty-btn" onclick="pos.updateQuantity(${item.product_id}, 1)">+</button>
                </div>
                <div class="text-end" style="min-width: 70px;">
                    <span class="fw-bold text-success small d-block">$${(item.unit_price * item.quantity).toFixed(2)}</span>
                    <button class="btn btn-sm text-danger p-0 opacity-75" onclick="pos.removeFromCart(${item.product_id})" title="Remove item">
                        <i class="fa-solid fa-trash-can" style="font-size: 0.72rem;"></i>
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

        this.updateChangeDue();
    }

    updateChangeDue() {
        const subtotal = this.cart.reduce((sum, item) => sum + (item.unit_price * item.quantity), 0.0);
        const total = Math.max(0.0, subtotal - Math.min(this.discount, subtotal));
        const changeEl = document.getElementById('posChangeDueText');

        if (changeEl) {
            if (this.cashTendered > 0 && this.cashTendered >= total) {
                const change = this.cashTendered - total;
                changeEl.textContent = `$${change.toFixed(2)}`;
                changeEl.className = 'fw-bold text-success fs-6';
            } else if (this.cashTendered > 0 && this.cashTendered < total) {
                const deficit = total - this.cashTendered;
                changeEl.textContent = `Short: -$${deficit.toFixed(2)}`;
                changeEl.className = 'fw-bold text-danger fs-6';
            } else {
                changeEl.textContent = '$0.00';
                changeEl.className = 'fw-bold text-muted fs-6';
            }
        }
    }

    async handleCheckout() {
        if (this.cart.length === 0) {
            this.playTone('error');
            this.showToast('Your shopping basket is currently empty!', 'warning');
            return;
        }

        const customerName = document.getElementById('posCustomerName')?.value.trim() || 'Walk-in Customer';
        const customerPhone = document.getElementById('posCustomerPhone')?.value.trim() || '';
        const paymentMethod = document.getElementById('posPaymentMethod')?.value || 'Cash';
        const notes = document.getElementById('posNotes')?.value.trim() || '';

        const checkoutBtn = document.getElementById('posCheckoutBtn');
        if (checkoutBtn) {
            checkoutBtn.disabled = true;
            checkoutBtn.innerHTML = `<span class="spinner-border spinner-border-sm me-2"></span> Finalizing Transaction...`;
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
                this.playTone('success');
                this.showSuccessModal(data);
                // Reset cart & inputs
                this.cart = [];
                this.discount = 0.0;
                this.cashTendered = 0.0;
                const discInput = document.getElementById('posDiscountInput');
                if (discInput) discInput.value = '0';
                const tenderInput = document.getElementById('posCashTendered');
                if (tenderInput) tenderInput.value = '';
                this.renderCart();
            } else {
                this.playTone('error');
                this.showToast(data.message || 'Checkout failed. Please inspect items.', 'danger');
            }
        } catch (err) {
            this.playTone('error');
            this.showToast('Network error during checkout.', 'danger');
        } finally {
            if (checkoutBtn) {
                checkoutBtn.disabled = false;
                checkoutBtn.innerHTML = `<i class="fa-solid fa-check-double me-2"></i> Complete Order (Alt+C)`;
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
        toastEl.className = `alert alert-${type} pos-toast alert-dismissible fade show shadow border-0 d-flex align-items-center gap-2 mb-2`;
        const icon = type === 'success' ? 'fa-circle-check text-success' : (type === 'danger' ? 'fa-circle-xmark text-danger' : 'fa-circle-info text-primary');
        toastEl.innerHTML = `
            <i class="fa-solid ${icon} fs-5"></i>
            <span class="fw-semibold small flex-grow-1">${message}</span>
            <button type="button" class="btn-close ms-2" data-bs-dismiss="alert"></button>
        `;
        toastContainer.appendChild(toastEl);
        setTimeout(() => toastEl.remove(), 4000);
    }
}

// Global instance
let pos;
document.addEventListener('DOMContentLoaded', () => {
    pos = new POSController();
});
