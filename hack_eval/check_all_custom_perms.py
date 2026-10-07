import frappe

def run():
    custom_perms = frappe.get_all("Custom DocPerm", fields=["name", "parent", "role", "create", "write", "read"])
    print("ALL CUSTOM DOCPERMS IN SYSTEM:")
    for cp in custom_perms:
        print(cp)
