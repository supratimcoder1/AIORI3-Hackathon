import frappe

def run():
    out = []
    out.append("=== 1. Hackathon Rounds & Criteria ===")
    rounds = frappe.get_all("Hackathon Round", fields=["name", "round_name", "round_number", "status", "advance_count"], order_by="round_number asc")
    for r in rounds:
        r_doc = frappe.get_doc("Hackathon Round", r.name)
        total_max = sum([c.max_score for c in r_doc.criteria])
        out.append(f"{r_doc.round_name} (Round {r_doc.round_number}, Status: {r_doc.status}, Advance: {r_doc.advance_count}, Total Max: {total_max})")
        for c in r_doc.criteria:
            out.append(f"  - {c.criterion}: max {c.max_score} (scored by: {c.scored_by})")
            
    out.append("\n=== 2. Level 1 Evaluations Inspection ===")
    evals = frappe.get_all("Evaluation", filters={"round": "Level 1"}, fields=["name", "team", "evaluator", "status"])
    out.append(f"Total Level 1 Evaluations: {len(evals)}")
    for ev in evals[:3]:
        ev_doc = frappe.get_doc("Evaluation", ev.name)
        scores_summary = ", ".join([f"{s.criterion}: {s.score}/{s.max_score}" for s in ev_doc.scores])
        out.append(f"  - {ev.name} ({ev.team}, Evaluator: {ev.evaluator}, Status: {ev.status}): [{scores_summary}]")

    out.append("\n=== 3. Permission & Level Gating Verification ===")
    # Test Alice write permission on her evaluation when round is Open
    alice_eval = evals[0].name if evals else None
    if alice_eval:
        alice_doc = frappe.get_doc("Evaluation", alice_eval)
        evaluator_user = alice_doc.evaluator
        frappe.set_user(evaluator_user)
        can_write_open = frappe.has_permission("Evaluation", "write", doc=alice_doc, user=evaluator_user)
        out.append(f"Can {evaluator_user} write while Round is Open? {can_write_open}")
        
        # Test write permission if round is Closed
        frappe.set_user("Administrator")
        frappe.db.set_value("Hackathon Round", "Level 1", "status", "Closed")
        frappe.set_user(evaluator_user)
        can_write_closed = frappe.has_permission("Evaluation", "write", doc=alice_doc, user=evaluator_user)
        out.append(f"Can {evaluator_user} write while Round is Closed? {can_write_closed}")
        
        # Test Administrator write permission while Round is Closed
        can_admin_write = frappe.has_permission("Evaluation", "write", doc=alice_doc, user="Administrator")
        out.append(f"Can Administrator write while Round is Closed? {can_admin_write}")
        
        # Restore Round to Open
        frappe.set_user("Administrator")
        frappe.db.set_value("Hackathon Round", "Level 1", "status", "Open")
        frappe.db.commit()

    with open("/mnt/d/Projects/AIORI3-Hackathon/verify_scoring_report.txt", "w") as f:
        f.write("\n".join(out))
