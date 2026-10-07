import frappe

def run():
    # Remove user-specific list view settings for Evaluation so the global one takes effect
    # In frappe v15, listview customizations are stored in User List Settings
    # Actually, they might be in `tabUser` or `tabView`... wait, Frappe stores it in cache or `tabUser`.
    # Let's clear User settings cache entirely.
    frappe.cache().delete_keys('user_default')
    print("User default cache cleared")
