import frappe

def run():
    # 0. Seed Hackathon Rounds (Levels 1, 2, 3)
    rounds = [
        {
            "round_number": 1,
            "round_name": "Level 1",
            "status": "Not Started",
            "mentor_scoring_mode": "Mentor Panel",
            "advance_count": 250,
            "criteria": [
                {"criterion": "Presentation", "max_score": 10},
                {"criterion": "Mentor Score", "max_score": 10}
            ]
        },
        {
            "round_number": 2,
            "round_name": "Level 2",
            "status": "Not Started",
            "mentor_scoring_mode": "Mentor Panel",
            "advance_count": 80,
            "criteria": [
                {"criterion": "Coding", "max_score": 10},
                {"criterion": "Architecture", "max_score": 10},
                {"criterion": "Outcome", "max_score": 10},
                {"criterion": "Future Plan", "max_score": 10},
                {"criterion": "Innovation", "max_score": 10},
                {"criterion": "Collaboration", "max_score": 10},
                {"criterion": "Mentor Score", "max_score": 10}
            ]
        },
        {
            "round_number": 3,
            "round_name": "Level 3",
            "status": "Not Started",
            "mentor_scoring_mode": "Mentor Panel",
            "advance_count": 3,
            "criteria": [
                {"criterion": "Mentor Score", "max_score": 10}
            ]
        }
    ]

    for r in rounds:
        if not frappe.db.exists("Hackathon Round", r["round_name"]):
            doc = frappe.get_doc({
                "doctype": "Hackathon Round",
                "round_number": r["round_number"],
                "round_name": r["round_name"],
                "status": r["status"],
                "mentor_scoring_mode": r["mentor_scoring_mode"],
                "advance_count": r["advance_count"]
            })
            for c in r["criteria"]:
                doc.append("criteria", {
                    "criterion": c["criterion"],
                    "max_score": c["max_score"]
                })
            doc.insert(ignore_permissions=True)
            print(f"Created Hackathon Round: {r['round_name']}")

    frappe.db.commit()
    print("Master Data (Levels) generation complete!")
