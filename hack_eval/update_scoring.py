import frappe

def run():
    out = []
    
    # 1. Ensure all criteria exist
    criteria_list = [
        ("Presentation", "Presentation quality and clarity"),
        ("Mentor Score", "Mentor overall assessment"),
        ("Coding", "Code quality, architecture and implementation"),
        ("Solution Architecture", "Technical design and structural soundness"),
        ("Outcome", "Demonstrated functionality and project output"),
        ("Future Plan", "Roadmap and sustainability of the project"),
        ("Innovation", "Novelty and creative problem solving"),
        ("Collaboration", "Team synergy and faculty collaboration")
    ]
    
    for crit_name, desc in criteria_list:
        if not frappe.db.exists("Evaluation Criterion", crit_name):
            doc = frappe.get_doc({
                "doctype": "Evaluation Criterion",
                "criterion_name": crit_name,
                "description": desc,
                "scored_by": "Mentor"
            })
            doc.insert(ignore_permissions=True)
            out.append(f"Created criterion: {crit_name}")
        else:
            frappe.db.set_value("Evaluation Criterion", crit_name, "scored_by", "Mentor")
            out.append(f"Updated criterion: {crit_name}")
            
    frappe.db.commit()

    # 2. Configure Hackathon Rounds
    # Level 1
    l1_name = frappe.db.get_value("Hackathon Round", {"round_number": 1}, "name")
    if not l1_name:
        l1 = frappe.get_doc({
            "doctype": "Hackathon Round",
            "round_name": "Level 1",
            "round_number": 1,
            "status": "Open",
            "advance_count": 5
        })
        l1.insert(ignore_permissions=True)
        l1_name = l1.name
        
    l1_doc = frappe.get_doc("Hackathon Round", l1_name)
    l1_doc.round_name = "Level 1"
    l1_doc.round_number = 1
    l1_doc.set("criteria", [])
    l1_doc.append("criteria", {"criterion": "Presentation", "max_score": 10.0, "scored_by": "Mentor"})
    l1_doc.append("criteria", {"criterion": "Mentor Score", "max_score": 10.0, "scored_by": "Mentor"})
    l1_doc.save(ignore_permissions=True)
    out.append("Updated Round Level 1 criteria (Presentation + Mentor Score = 20 pts)")

    # Level 2
    l2_name = frappe.db.get_value("Hackathon Round", {"round_number": 2}, "name")
    if not l2_name:
        l2 = frappe.get_doc({
            "doctype": "Hackathon Round",
            "round_name": "Level 2",
            "round_number": 2,
            "status": "Not Started",
            "advance_count": 3
        })
        l2.insert(ignore_permissions=True)
        l2_name = l2.name
        
    l2_doc = frappe.get_doc("Hackathon Round", l2_name)
    l2_doc.round_name = "Level 2"
    l2_doc.round_number = 2
    l2_doc.set("criteria", [])
    l2_criteria = [
        "Coding",
        "Solution Architecture",
        "Outcome",
        "Future Plan",
        "Innovation",
        "Collaboration",
        "Mentor Score"
    ]
    for c in l2_criteria:
        l2_doc.append("criteria", {"criterion": c, "max_score": 10.0, "scored_by": "Mentor"})
    l2_doc.save(ignore_permissions=True)
    out.append("Updated Round Level 2 criteria (7 criteria = 70 pts)")

    # Level 3
    l3_name = frappe.db.get_value("Hackathon Round", {"round_number": 3}, "name")
    if not l3_name:
        l3 = frappe.get_doc({
            "doctype": "Hackathon Round",
            "round_name": "Level 3",
            "round_number": 3,
            "status": "Not Started",
            "advance_count": 3
        })
        l3.insert(ignore_permissions=True)
        l3_name = l3.name
        
    l3_doc = frappe.get_doc("Hackathon Round", l3_name)
    l3_doc.round_name = "Level 3"
    l3_doc.round_number = 3
    l3_doc.set("criteria", [])
    l3_doc.append("criteria", {"criterion": "Mentor Score", "max_score": 10.0, "scored_by": "Mentor"})
    l3_doc.save(ignore_permissions=True)
    out.append("Updated Round Level 3 criteria (Mentor Score = 10 pts)")

    # 3. Synchronize existing Level 1 evaluations to have both criteria
    evals = frappe.get_all("Evaluation", filters={"round": l1_name})
    for ev in evals:
        ev_doc = frappe.get_doc("Evaluation", ev.name)
        existing_crits = [s.criterion for s in ev_doc.scores]
        if "Presentation" not in existing_crits:
            ev_doc.append("scores", {
                "criterion": "Presentation",
                "max_score": 10.0,
                "score": 0.0
            })
        if "Mentor Score" not in existing_crits:
            ev_doc.append("scores", {
                "criterion": "Mentor Score",
                "max_score": 10.0,
                "score": 0.0
            })
        # Remove any stray criteria not in Level 1
        ev_doc.scores = [s for s in ev_doc.scores if s.criterion in ["Presentation", "Mentor Score"]]
        ev_doc.save(ignore_permissions=True)
        out.append(f"Synced evaluation {ev.name} to 2 criteria")

    frappe.db.commit()

    with open("/mnt/d/Projects/AIORI3-Hackathon/update_scoring_structure.txt", "w") as f:
        f.write("\n".join(out))
