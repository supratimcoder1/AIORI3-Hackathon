import frappe
from frappe.utils.password import update_password

def run():
    out = []
    eve = "eve.mentor@example.com"
    
    if not frappe.db.exists("User", eve):
        user = frappe.get_doc({
            "doctype": "User",
            "email": eve,
            "first_name": "Eve",
            "last_name": "Mentor",
            "enabled": 1,
            "send_welcome_email": 0
        })
        user.append("roles", {"role": "AIORI-3 Mentor"})
        user.insert(ignore_permissions=True)
        update_password(eve, "Password123")
        frappe.db.commit()
        out.append("Created Eve in User and set password.")
    else:
        out.append("Eve already exists in User.")
        
    with open("/mnt/d/Projects/AIORI3-Hackathon/eval_diag3.txt", "w") as f:
        f.write("\n".join(out))
