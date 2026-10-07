import frappe

def run():
    out = []
    out.append("=== Hackathon Rounds ===")
    rounds = frappe.get_all("Hackathon Round", fields=["name", "round_name", "round_number", "status", "advance_count"])
    for r in rounds:
        r_doc = frappe.get_doc("Hackathon Round", r.name)
        out.append(f"Round: {r_doc.round_name} (No: {r_doc.round_number}, Status: {r_doc.status}, Advance: {r_doc.advance_count})")
        for c in r_doc.criteria:
            out.append(f"  - Criterion: {c.criterion}, Max: {c.max_score}, Scored By: {c.scored_by}")
            
    out.append("\n=== Evaluation Criteria Master ===")
    criteria = frappe.get_all("Evaluation Criterion", fields=["name", "criterion_name", "scored_by"])
    for c in criteria:
        out.append(f"Criterion: {c.name} ({c.criterion_name}, Scored By: {c.scored_by})")
        
    out.append("\n=== Existing Evaluations ===")
    evals = frappe.get_all("Evaluation", fields=["name", "team", "evaluator", "round", "status", "total_score"])
    for e in evals:
        e_doc = frappe.get_doc("Evaluation", e.name)
        out.append(f"Eval: {e.name} (Team: {e.team}, Round: {e.round}, Evaluator: {e.evaluator})")
        for s in e_doc.scores:
            out.append(f"  - Score row: {s.criterion}, Score: {s.score}, Max: {s.max_score}")
            
    with open("/mnt/d/Projects/AIORI3-Hackathon/scoring_diag.txt", "w") as f:
        f.write("\n".join(out))
