import frappe
from frappe.auth import LoginManager

def run():
    try:
        login_manager = LoginManager()
        login_manager.authenticate(user="alice.mentor@example.com", pwd="Password123")
        with open("auth_result.txt", "w") as f:
            f.write("Login SUCCESS for alice.mentor@example.com")
    except frappe.AuthenticationError:
        with open("auth_result.txt", "w") as f:
            f.write("Login FAILED for alice.mentor@example.com")
