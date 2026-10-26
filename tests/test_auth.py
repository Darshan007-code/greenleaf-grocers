def test_admin_login_success(client, sample_users):
    """Test admin logs in and gets redirected to dashboard."""
    response = client.post('/login', data={
        'username': 'admin_test',
        'password': 'adminpass123'
    }, follow_redirects=False)
    assert response.status_code == 302
    assert response.location.endswith('/dashboard')

def test_cashier_login_success(client, sample_users):
    """Test cashier logs in and gets redirected directly to POS billing."""
    response = client.post('/login', data={
        'username': 'cashier_test',
        'password': 'cashierpass123'
    }, follow_redirects=False)
    assert response.status_code == 302
    assert response.location.endswith('/billing/pos') or response.location.endswith('/billing/')

def test_login_invalid_password(client, sample_users):
    """Test bad credentials reject login."""
    response = client.post('/login', data={
        'username': 'admin_test',
        'password': 'wrongpassword'
    }, follow_redirects=True)
    assert b'Invalid username or password.' in response.data

def test_cashier_forbidden_from_admin_products(client, sample_users):
    """Test cashier is denied access to admin products management."""
    # Login as cashier
    client.post('/login', data={'username': 'cashier_test', 'password': 'cashierpass123'})
    # Attempt to visit products management
    response = client.get('/products/', follow_redirects=True)
    assert b'Access denied' in response.data

def test_cashier_forbidden_from_reports(client, sample_users):
    """Test cashier is denied access to analytics reports."""
    client.post('/login', data={'username': 'cashier_test', 'password': 'cashierpass123'})
    response = client.get('/reports/', follow_redirects=True)
    assert b'Access denied' in response.data

def test_logout(client, sample_users):
    """Test logout clears session."""
    client.post('/login', data={'username': 'admin_test', 'password': 'adminpass123'})
    response = client.get('/logout', follow_redirects=True)
    assert b'You have been logged out successfully.' in response.data
    # Dashboard should now redirect to login
    dash_resp = client.get('/dashboard', follow_redirects=False)
    assert dash_resp.status_code == 302
