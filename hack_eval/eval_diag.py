import frappe

def run():
    out = []
    # Check Evaluation records
    evals = frappe.get_all("Evaluation", fields=["name", "team", "evaluator", "round", "status"])
    out.append(f"Total Evaluation records: {len(evals)}")
    if evals:
        out.append("First 5 records:")
        for e in evals[:5]:
            out.append(str(e))
            
    # Check permissions on Evaluation DocType
    perms = frappe.get_all("Custom DocPerm", filters={"parent": "Evaluation"}, fields=["role", "read", "write", "create"])
    if not perms:
        out.append("No Custom DocPerms for Evaluation. Checking standard perms from DocType.")
        doc = frappe.get_doc("DocType", "Evaluation")
        for p in doc.permissions:
            out.append(f"Role: {p.role}, Read: {p.read}, Write: {p.write}")
    else:
        out.append(f"Custom DocPerms found: {perms}")
        
    # Test permission query for Alice
    user = "alice.mentor@example.com"
    out.append(f"\nTesting permission query for {user}")
    frappe.set_user(user)
    try:
        visible_evals = frappe.get_all("Evaluation")
        out.append(f"Visible Evaluation records for {user}: {len(visible_evals)}")
    except Exception as e:
        out.append(f"Error fetching as Alice: {e}")
    finally:
        frappe.set_user("Administrator")
        
    # Check role of Alice
    roles = frappe.get_roles(user)
    out.append(f"\nRoles for {user}: {roles}")

    with open("/mnt/d/Projects/AIORI3-Hackathon/eval_diag.txt", "w") as f:
        f.write("\n".join(out))
