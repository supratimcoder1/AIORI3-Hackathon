import frappe

def run():
    out = []
    eve = "eve.mentor@example.com"
    
    teams = frappe.get_all("Hackathon Team", filters={"problem_statement_area": "Smart Cities"})
    for t in teams:
        team_doc = frappe.get_doc("Hackathon Team", t.name)
        old_mentor = team_doc.mentor
        team_doc.mentor = eve
        team_doc.save(ignore_permissions=True)
        out.append(f"Reassigned {t.name} from {old_mentor} to Eve")
        
        evals = frappe.get_all("Evaluation", filters={"team": t.name})
        for ev in evals:
            ev_doc = frappe.get_doc("Evaluation", ev.name)
            ev_doc.evaluator = eve
            ev_doc.save(ignore_permissions=True)
            out.append(f"Reassigned evaluation {ev.name} to Eve")
            
    frappe.db.commit()
    with open("/mnt/d/Projects/AIORI3-Hackathon/reassign_diag.txt", "w") as f:
        f.write("\n".join(out))
