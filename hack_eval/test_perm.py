import frappe
from frappe.permissions import get_role_permissions

def run():
    frappe.set_user("Administrator")
    meta = frappe.get_meta("Hackathon Team")
    print("META PERMISSIONS:", [p.as_dict() for p in meta.permissions])
    print("ROLE PERMISSIONS FOR ADMIN:", get_role_permissions(meta, user="Administrator"))
    print("CAN CREATE:", frappe.has_permission("Hackathon Team", "create", user="Administrator"))
    print("CAN IMPORT:", frappe.has_permission("Hackathon Team", "import", user="Administrator"))
    print("ROLES OF ADMIN:", frappe.get_roles("Administrator"))

    # Also check Mentor Profile
    meta_mp = frappe.get_meta("Mentor Profile")
    print("MENTOR PROFILE CAN CREATE:", frappe.has_permission("Mentor Profile", "create", user="Administrator"))
    print("MENTOR PROFILE CAN IMPORT:", frappe.has_permission("Mentor Profile", "import", user="Administrator"))
