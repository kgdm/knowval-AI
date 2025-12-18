from auth import AuthManager
import os

def test_auth():
    # Use a temporary db
    db_path = "test_users.db"
    if os.path.exists(db_path):
        os.remove(db_path)
    
    auth = AuthManager(db_path=db_path)
    
    print("--- Test 1: Basic Registration & Login ---")
    user = "test@example.com"
    pw = "password123"
    
    reg_result = auth.register_user(user, pw)
    print(f"Registration result: {reg_result}")
    
    login_result = auth.login_user(user, pw)
    print(f"Login result: {login_result}")
    
    if reg_result is True and login_result is True:
        print("PASS: Basic flow works.")
    else:
        print("FAIL: Basic flow failed.")

    print("\n--- Test 2: Whitespace Handling ---")
    user_space = " space@example.com "
    pw_space = " password "
    
    # Register with spaces
    reg_result = auth.register_user(user_space, pw_space)
    print(f"Registration (with spaces): {reg_result}")
    
    # Login with spaces (should work if exact match)
    login_result = auth.login_user(user_space, pw_space)
    print(f"Login (exact match): {login_result}")
    
    # Login without spaces (should fail if not stripped)
    login_result_stripped = auth.login_user(user_space.strip(), pw_space.strip())
    print(f"Login (stripped): {login_result_stripped}")
    
    if login_result is True and login_result_stripped is False:
        print("OBSERVATION: Whitespace is NOT stripped. This might be the issue.")
    
    print("\n--- Test 3: Invalid Email ---")
    invalid_user = "invalid-email"
    reg_result = auth.register_user(invalid_user, pw)
    print(f"Registration (invalid email): {reg_result}")

    print("\n--- Test 4: Case Sensitivity ---")
    mixed_case_user = "MixedCase@Example.com"
    pw = "password"
    
    # Register mixed case
    reg_result = auth.register_user(mixed_case_user, pw)
    print(f"Registration (mixed case): {reg_result}")
    
    # Login exact match
    login_exact = auth.login_user(mixed_case_user, pw)
    print(f"Login (exact match): {login_exact}")
    
    # Login lower case
    login_lower = auth.login_user(mixed_case_user.lower(), pw)
    print(f"Login (lower case): {login_lower}")
    
    if login_exact is True and login_lower is False:
        print("OBSERVATION: Email is Case Sensitive. This is likely the issue.")

    # Clean up
    if os.path.exists(db_path):
        os.remove(db_path)

if __name__ == "__main__":
    test_auth()
