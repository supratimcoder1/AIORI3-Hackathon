import frappe

def run():
    mentor_emails = [
        "alice.mentor@example.com",
        "bob.mentor@example.com",
        "charlie.mentor@example.com",
        "diana.mentor@example.com"
    ]
    
    for email in mentor_emails:
        if frappe.db.exists("User", email):
            user = frappe.get_doc("User", email)
            user.new_password = "Password123"
            user.save(ignore_permissions=True)
            print(f"Password set for {email}")
    
    frappe.db.commit()
    print("All mentor passwords reset to 'Password123'")
