import frappe

def reset_hackathon_to_level_1(delete_level1_evaluations=False):
    """
    Canonical reset script for AIORI-3 Hackathon.
    Resets all teams, rounds, results, and evaluations back to Level 1.
    """
    frappe.db.begin()
    try:
        # 1. Reset Hackathon Teams
        teams = frappe.get_all("Hackathon Team", pluck="name")
        for team_name in teams:
            team_doc = frappe.get_doc("Hackathon Team", team_name)
            team_doc.current_level = 1
            team_doc.status = "Active"
            team_doc.eliminated_at_level = None
            if hasattr(team_doc, "final_position"):
                team_doc.final_position = None
            team_doc.level1_score = 0.0
            team_doc.level2_score = 0.0
            team_doc.level3_score = 0.0
            team_doc.cumulative_score = 0.0
            team_doc.save(ignore_permissions=True)
            
        print(f"[*] Reset {len(teams)} teams to Level 1 (Active, zeroed scores).")

        # 2. Delete all Team Round Results
        results = frappe.get_all("Team Round Result", pluck="name")
        for res_name in results:
            frappe.delete_doc("Team Round Result", res_name, ignore_permissions=True, force=True)
        print(f"[*] Deleted {len(results)} Team Round Result records.")

        # 3. Delete all Score Adjustments
        adjustments = frappe.get_all("Score Adjustment", pluck="name")
        for adj_name in adjustments:
            frappe.delete_doc("Score Adjustment", adj_name, ignore_permissions=True, force=True)
        print(f"[*] Deleted {len(adjustments)} Score Adjustment records.")

        # 4. Remove Level 2 and Level 3 Evaluations
        l2_l3_evals = frappe.get_all(
            "Evaluation", 
            filters={"round": ["in", ["Level 2", "Level 3"]]}, 
            pluck="name"
        )
        for eval_name in l2_l3_evals:
            frappe.delete_doc("Evaluation", eval_name, ignore_permissions=True, force=True)
        print(f"[*] Deleted {len(l2_l3_evals)} Level 2 & 3 Evaluation documents.")

        # 5. Handle Level 1 Evaluations
        l1_evals = frappe.get_all("Evaluation", filters={"round": "Level 1"}, pluck="name")
        if delete_level1_evaluations:
            for eval_name in l1_evals:
                frappe.delete_doc("Evaluation", eval_name, ignore_permissions=True, force=True)
            print(f"[*] Deleted {len(l1_evals)} Level 1 evaluations (re-opening will recreate them).")
        else:
            for eval_name in l1_evals:
                eval_doc = frappe.get_doc("Evaluation", eval_name)
                eval_doc.status = "Pending"
                eval_doc.submitted_on = None
                eval_doc.total_score = 0.0
                for row in eval_doc.scores:
                    row.score = 0.0
                    row.remarks = ""
                eval_doc.save(ignore_permissions=True)
            print(f"[*] Reset {len(l1_evals)} Level 1 evaluations to 'Pending' with 0.0 scores.")

        # 6. Reset Round States
        if frappe.db.exists("Hackathon Round", "Level 1"):
            r1 = frappe.get_doc("Hackathon Round", "Level 1")
            r1.status = "Open"
            r1.advance_count = 0
            r1.save(ignore_permissions=True)

        if frappe.db.exists("Hackathon Round", "Level 2"):
            r2 = frappe.get_doc("Hackathon Round", "Level 2")
            r2.status = "Not Started"
            r2.advance_count = 0
            r2.save(ignore_permissions=True)

        if frappe.db.exists("Hackathon Round", "Level 3"):
            r3 = frappe.get_doc("Hackathon Round", "Level 3")
            r3.status = "Not Started"
            r3.advance_count = 0
            r3.save(ignore_permissions=True)

        print("[*] Hackathon Rounds reset: Level 1 -> Open, Level 2 & 3 -> Not Started.")

        frappe.db.commit()
        print("\n[SUCCESS] Entire system successfully reset to Level 1!")

    except Exception as e:
        frappe.db.rollback()
        print(f"[ERROR] Reset failed, rolled back changes: {e}")
        raise e

if __name__ == "__main__":
    reset_hackathon_to_level_1()
