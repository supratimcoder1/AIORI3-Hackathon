import frappe
from frappe.utils.password import update_password

def run():
    mentor_emails = [
        "alice.mentor@example.com",
        "bob.mentor@example.com",
        "charlie.mentor@example.com",
        "diana.mentor@example.com"
    ]
    
    for email in mentor_emails:
        if frappe.db.exists("User", email):
            try:
                update_password(user=email, pwd="Password123")
                frappe.db.commit()
            except Exception as e:
                pass
