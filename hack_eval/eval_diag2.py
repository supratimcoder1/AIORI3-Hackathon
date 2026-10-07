import frappe

def run():
    out = []
    mentors = [
        "alice.mentor@example.com",
        "bob.mentor@example.com",
        "charlie.mentor@example.com",
        "diana.mentor@example.com",
        "eve.mentor@example.com"
    ]
    
    for user in mentors:
        frappe.set_user(user)
        try:
            visible = frappe.get_list("Evaluation", ignore_permissions=False, fields=["name", "team", "evaluator"])
            out.append(f"Visible for {user}: {len(visible)}")
            for v in visible:
                out.append(f"  - {v.name} (Team: {v.team})")
        except Exception as e:
            out.append(f"ERROR for {user}: {e}")
        finally:
            frappe.set_user("Administrator")
            
    with open("/mnt/d/Projects/AIORI3-Hackathon/eval_diag2.txt", "w") as f:
        f.write("\n".join(out))
