import frappe

def run():
    profiles = frappe.get_all("Mentor Profile")
    users = frappe.get_all("User", filters={"name": ["like", "%mentor%"]}, fields=["name", "enabled"])
    print(f"Profiles: {profiles}")
    print(f"Users: {users}")
