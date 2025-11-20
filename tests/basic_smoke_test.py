#!/usr/bin/env python3
import os
import sys

def get_app():
    sys.path.insert(0, os.getcwd())
    from src.apps.app import app
    app.testing = True
    return app

def assert_true(cond, msg):
    if not cond:
        raise AssertionError(msg)

def run_tests():
    app = get_app()
    client = app.test_client()

    # Home requires login - expect redirect to /login
    resp = client.get('/')
    assert_true(resp.status_code in (301, 302), f"Expected 302 redirect from '/', got {resp.status_code}")
    loc = resp.headers.get('Location', '')
    assert_true('/login' in loc, f"Expected redirect to /login, got {loc}")

    # Login page should load
    resp = client.get('/login')
    assert_true(resp.status_code == 200, f"/login should return 200, got {resp.status_code}")

    # Perform login with default admin created by initialize_app()
    login_resp = client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)
    assert_true(login_resp.status_code == 200, f"Login should lead to 200 on index, got {login_resp.status_code}")

    # After login, home should be accessible (HTTP 200)
    resp = client.get('/')
    assert_true(resp.status_code == 200, f"After login, '/' should return 200, got {resp.status_code}")

    # Dashboard should be accessible (HTTP 200)
    resp = client.get('/dashboard')
    assert_true(resp.status_code == 200, f"After login, '/dashboard' should return 200, got {resp.status_code}")

    # /api/products returns JSON with product structure
    resp = client.get('/api/products')
    assert_true(resp.status_code == 200, f"/api/products should return 200, got {resp.status_code}")
    data = resp.get_json()
    assert_true(isinstance(data, dict), "Expected dict JSON from /api/products")
    assert_true(len(data) > 0, "Expected at least 1 product")
    first_key = next(iter(data.keys()))
    item = data[first_key]
    assert_true('name' in item and 'type' in item and 'template_exists' in item, "Product item missing keys")

    print("All smoke tests passed")

if __name__ == '__main__':
    try:
        run_tests()
    except AssertionError as e:
        print("TEST FAILED:", e)
        raise