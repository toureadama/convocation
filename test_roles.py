#!/usr/bin/env python3
"""Test script to verify role-based access control."""

import requests
import sys
import os

sys.path.insert(0, r"c:\Users\HP 820 G3\Desktop\DOUANES CI\CONVOCATION_ONLINE")

BASE_URL = "http://127.0.0.1:5000"

def get_password_from_db(login):
    """Get user password from database."""
    from db_config import get_db_connection, close_connection
    conn = get_db_connection()
    if not conn:
        return None
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT plain_password FROM users WHERE login = %s", (login,))
    row = cursor.fetchone()
    close_connection(conn)
    pwd = row["plain_password"] if row else None
    return pwd if pwd and pwd != "***" else None

def login(login, password):
    """Login and return token + user info."""
    resp = requests.post(f"{BASE_URL}/api/login", json={"login": login, "password": password})
    if resp.status_code == 200:
        data = resp.json()
        return data["token"], data["user"]
    return None, None

def check_endpoint(token, url, method="GET", data=None):
    """Check an endpoint and return status code + response."""
    headers = {"Authorization": f"Bearer {token}"}
    if method == "GET":
        resp = requests.get(f"{BASE_URL}{url}", headers=headers)
    else:
        resp = requests.post(f"{BASE_URL}{url}", headers=headers, json=data or {})
    return resp.status_code, resp.json()

def test_role(role_name, login_name, expected_access):
    """Test a specific role's access."""
    print(f"\n{'='*70}")
    print(f"Testing role: {role_name} ({login_name})")
    print(f"{'='*70}")
    
    password = get_password_from_db(login_name)
    if not password:
        print(f"  ⚠️  No valid password in DB. Skipping.")
        return
    
    token, user = login(login_name, password)
    if not token:
        print(f"  ❌ Login failed (password: {password})")
        return
    
    actual_role = user.get("role", "Unknown")
    print(f"  ✅ Login successful. Role: {actual_role}")
    
    endpoints = {
        "users": ("/api/users", "GET", None),
        "code_agree": ("/api/code_agree", "GET", None),
        "code_operateur": ("/api/code_operateur", "GET", None),
        "generate": ("/api/generate", "POST", {}),
        "history": ("/api/history", "POST", {"page": 0, "limit": 10, "filters": {}}),
    }
    
    all_passed = True
    for name, (endpoint, method, data) in endpoints.items():
        
        expected_allow = expected_access.get(name, False)
        status_code, response = check_endpoint(token, endpoint, method, data)
        
        # For generate, 400 = allowed but missing data, 403 = denied
        if name == "generate" and status_code == 400:
            is_allowed = True  # 400 means it passed the auth check
        
        is_allowed = status_code in (200, 400)  # 400 means auth passed
        passed = is_allowed == expected_allow
        
        if not passed:
            all_passed = False
        
        status_icon = "✅" if passed else "❌"
        access_str = "ALLOW" if expected_allow else "DENY "
        actual_str = f"{'ALLOW' if is_allowed else 'DENY '} ({status_code})"
        error_msg = response.get("error", "")
        
        print(f"  {status_icon} {name:20} Expected: {access_str}  Actual: {actual_str:20} {error_msg}")
    
    print(f"\n  {'='*50}")
    print(f"  {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    print(f"  {'='*50}")
    return all_passed

def main():
    print("Starting role-based access control tests...")
    print(f"Target: {BASE_URL}")
    
    results = {}
    
    # Test Vérificateur (should have generate + history access only)
    results["Vérificateur"] = test_role("Vérificateur", "test.perm", {
        "users": False,
        "code_agree": False,
        "code_operateur": False,
        "generate": True,
        "history": True,
    })
    
    # Test Administrateur (should have history access only, no tabs)
    results["Administrateur"] = test_role("Administrateur", "test.admin", {
        "users": False,
        "code_agree": False,
        "code_operateur": False,
        "generate": False,
        "history": True,
    })
    
    # Test Super Administrateur (should have history access only, no tabs)
    results["Super Administrateur"] = test_role("Super Administrateur", "admin", {
        "users": False,
        "code_agree": False,
        "code_operateur": False,
        "generate": False,
        "history": True,
    })
    
    # Test Administrateur Technique (should have user/code/history access, no generate)
    results["Admin Technique"] = test_role("Administrateur Technique", "info", {
        "users": True,
        "code_agree": True,
        "code_operateur": True,
        "generate": False,
        "history": True,
    })
    
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    for role, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED" if passed is not None else "⚠️  SKIPPED"
        print(f"  {status} - {role}")
    print(f"{'='*70}")

if __name__ == "__main__":
    main()
