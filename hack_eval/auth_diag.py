import frappe
from frappe.utils.password import update_password, check_password

def run():
    out = []
    mentors = [
        "alice.mentor@example.com",
        "bob.mentor@example.com",
        "charlie.mentor@example.com",
        "diana.mentor@example.com",
        "eve.mentor@example.com"
    ]
    
    for m in mentors:
        try:
            update_password(m, "Password123", logout_all_sessions=False)
            res = check_password(m, "Password123")
            out.append(f"{m}: Verified successfully (authenticated as {res})")
        except Exception as e:
            out.append(f"{m}: FAILED with error {e}")
            
    frappe.db.commit()
    
    with open("/mnt/d/Projects/AIORI3-Hackathon/auth_diag.txt", "w") as f:
        f.write("\n".join(out))
