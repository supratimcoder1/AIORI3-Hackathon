import frappe

def run():
    if not frappe.db.exists("Mentor Profile", "eve.mentor@example.com"):
        doc = frappe.get_doc({
            "doctype": "Mentor Profile",
            "name": "eve.mentor@example.com",
            "first_name": "Eve",
            "last_name": "Mentor",
            "email": "eve.mentor@example.com",
            "assigned_track": "Smart Cities",
            "role": "Chief Mentor"
        })
        doc.insert(ignore_permissions=True)
        frappe.db.commit()
        print("Created Eve's Mentor Profile")
    else:
        print("Eve already has a profile")
