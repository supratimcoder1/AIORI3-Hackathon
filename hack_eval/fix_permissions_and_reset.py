import frappe
import json
import os

def run():
    print("--- 1. DELETING ROGUE CUSTOM DOCPERMS ---")
    deleted = frappe.db.delete("Custom DocPerm", {
        "parent": ["in", ["Hackathon Team", "Hackathon Round", "Evaluation"]]
    })
    print(f"Deleted {deleted} Custom DocPerm records.")

    base_dir = "/mnt/d/Projects/AIORI3-Hackathon/frappe-bench/apps/hack_eval/hack_eval/hackathon_eval/doctype"

    # --- 2. Update hackathon_team.json ---
    team_json_path = os.path.join(base_dir, "hackathon_team", "hackathon_team.json")
    with open(team_json_path, "r") as f:
        team_data = json.load(f)
    team_data["allow_import"] = 1
    team_data["permissions"] = [
        {"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "import": 1, "export": 1, "report": 1, "share": 1, "print": 1, "email": 1},
        {"role": "Hackathon Organizer", "read": 1, "write": 1, "create": 1, "delete": 1, "import": 1, "export": 1, "report": 1, "share": 1, "print": 1, "email": 1},
        {"role": "AIORI-3 Mentor", "read": 1},
        {"role": "Chief Mentor", "read": 1},
        {"role": "Evaluator", "read": 1},
        {"role": "Mentor", "read": 1},
        {"role": "Reviewer", "read": 1}
    ]
    with open(team_json_path, "w") as f:
        json.dump(team_data, f, indent=1)
    print("Updated hackathon_team.json")

    # --- 3. Update hackathon_round.json ---
    round_json_path = os.path.join(base_dir, "hackathon_round", "hackathon_round.json")
    with open(round_json_path, "r") as f:
        round_data = json.load(f)
    round_data["permissions"] = [
        {"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "import": 1, "export": 1, "report": 1, "share": 1, "print": 1, "email": 1},
        {"role": "Hackathon Organizer", "read": 1, "write": 1, "create": 1, "delete": 1, "import": 1, "export": 1, "report": 1, "share": 1, "print": 1, "email": 1},
        {"role": "AIORI-3 Mentor", "read": 1},
        {"role": "Chief Mentor", "read": 1},
        {"role": "Evaluator", "read": 1},
        {"role": "Mentor", "read": 1},
        {"role": "Reviewer", "read": 1}
    ]
    with open(round_json_path, "w") as f:
        json.dump(round_data, f, indent=1)
    print("Updated hackathon_round.json")

    # --- 4. Update evaluation.json ---
    eval_json_path = os.path.join(base_dir, "evaluation", "evaluation.json")
    with open(eval_json_path, "r") as f:
        eval_data = json.load(f)
    eval_data["allow_import"] = 1
    eval_data["permissions"] = [
        {"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "import": 1, "export": 1, "report": 1, "share": 1, "print": 1, "email": 1},
        {"role": "Hackathon Organizer", "read": 1, "write": 1, "create": 1, "delete": 1, "import": 1, "export": 1, "report": 1, "share": 1, "print": 1, "email": 1},
        {"role": "AIORI-3 Mentor", "read": 1, "write": 1},
        {"role": "Chief Mentor", "read": 1, "write": 1},
        {"role": "Evaluator", "read": 1, "write": 1},
        {"role": "Mentor", "read": 1, "write": 1},
        {"role": "Reviewer", "read": 1}
    ]
    with open(eval_json_path, "w") as f:
        json.dump(eval_data, f, indent=1)
    print("Updated evaluation.json")

    # --- 5. Reload DocTypes into DB ---
    frappe.reload_doc("hackathon_eval", "doctype", "hackathon_team", force=True)
    frappe.reload_doc("hackathon_eval", "doctype", "hackathon_round", force=True)
    frappe.reload_doc("hackathon_eval", "doctype", "evaluation", force=True)
    print("Reloaded DocTypes into DB.")

    frappe.db.commit()
    frappe.clear_cache()
    print("Database committed and cache cleared.")

    # --- 6. Verification ---
    frappe.set_user("Administrator")
    from frappe.boot import get_bootinfo
    boot = get_bootinfo()
    print("VERIFICATION FOR ADMINISTRATOR:")
    print("Can Create Hackathon Team?", "Hackathon Team" in boot.user.can_create)
    print("Can Import Hackathon Team?", "Hackathon Team" in boot.user.can_import)
    print("Can Create Hackathon Round?", "Hackathon Round" in boot.user.can_create)
    print("Can Create Evaluation?", "Evaluation" in boot.user.can_create)
