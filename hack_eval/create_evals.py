import frappe

def run():
    out = []
    try:
        # Find Level 1 round
        round_name = frappe.db.get_value("Hackathon Round", {"round_number": 1}, "name")
        
        if not round_name:
            doc = frappe.get_doc({
                "doctype": "Hackathon Round",
                "round_name": "Level 1",
                "round_number": 1,
                "status": "Open",
                "advance_count": 5
            })
            crit1 = frappe.db.get_value("Evaluation Criterion", {"criterion_name": "Presentation"})
            if not crit1:
                crit1_doc = frappe.get_doc({"doctype": "Evaluation Criterion", "criterion_name": "Presentation", "scored_by": "Evaluator"}).insert(ignore_permissions=True)
                crit1 = crit1_doc.name
                
            crit2 = frappe.db.get_value("Evaluation Criterion", {"criterion_name": "Mentor Score"})
            if not crit2:
                crit2_doc = frappe.get_doc({"doctype": "Evaluation Criterion", "criterion_name": "Mentor Score", "scored_by": "Mentor"}).insert(ignore_permissions=True)
                crit2 = crit2_doc.name
                
            doc.append("criteria", {"criterion": crit1, "max_score": 10.0, "scored_by": "Evaluator"})
            doc.append("criteria", {"criterion": crit2, "max_score": 10.0, "scored_by": "Mentor"})
            doc.insert(ignore_permissions=True)
            round_name = doc.name
            out.append(f"Created Hackathon Round: {round_name}")
        else:
            frappe.db.set_value("Hackathon Round", round_name, "status", "Open")
            out.append(f"Found round: {round_name}")

        teams = frappe.get_all("Hackathon Team", fields=["name", "mentor"])
        out.append(f"Found {len(teams)} teams.")
        
        count = 0
        for t in teams:
            if t.mentor:
                exists = frappe.db.exists("Evaluation", {"team": t.name, "round": round_name, "evaluator": t.mentor})
                if not exists:
                    eval_doc = frappe.get_doc({
                        "doctype": "Evaluation",
                        "team": t.name,
                        "round": round_name,
                        "evaluator": t.mentor,
                        "evaluator_type": "Mentor",
                        "status": "Pending"
                    })
                    round_doc = frappe.get_doc("Hackathon Round", round_name)
                    for rc in round_doc.criteria:
                        if rc.scored_by == "Mentor":
                            eval_doc.append("scores", {
                                "criterion": rc.criterion,
                                "max_score": rc.max_score,
                                "score": 0.0
                            })
                    eval_doc.insert(ignore_permissions=True)
                    count += 1
        frappe.db.commit()
        out.append(f"Created {count} Evaluation documents for Level 1.")
    except Exception as e:
        out.append(f"ERROR: {str(e)}")
        import traceback
        out.append(traceback.format_exc())

    with open("/mnt/d/Projects/AIORI3-Hackathon/create_evals_diag.txt", "w") as f:
        f.write("\n".join(out))
