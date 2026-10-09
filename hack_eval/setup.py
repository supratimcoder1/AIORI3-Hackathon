import frappe

def after_install():
    # Create roles
    roles = ["Hackathon Organizer", "Mentor", "Evaluator", "Reviewer"]
    for role in roles:
        if not frappe.db.exists("Role", role):
            frappe.get_doc({
                "doctype": "Role",
                "role_name": role,
                "desk_access": 1
            }).insert(ignore_permissions=True)
    
    # Create evaluation criteria
    criteria = [
        {"name": "Presentation", "scored_by": "Evaluator"},
        {"name": "Mentor Score", "scored_by": "Mentor"},
        {"name": "Coding", "scored_by": "Evaluator"},
        {"name": "Solution Architecture", "scored_by": "Evaluator"},
        {"name": "Outcome", "scored_by": "Evaluator"},
        {"name": "Future Plan", "scored_by": "Evaluator"},
        {"name": "Innovation", "scored_by": "Evaluator"},
        {"name": "Collaboration", "scored_by": "Evaluator"}
    ]
    for c in criteria:
        if not frappe.db.exists("Evaluation Criterion", c["name"]):
            frappe.get_doc({
                "doctype": "Evaluation Criterion",
                "criterion_name": c["name"],
                "scored_by": c["scored_by"]
            }).insert(ignore_permissions=True)

    # Note: Rounds will be created after DocTypes are synced via bench migrate.
    after_migrate()

def after_migrate():
    ensure_rounds_exist()
    backfill_evaluation_team_codes()
    sync_custom_workspaces()
    hide_standard_workspaces()

def ensure_rounds_exist():
    # Only create rounds if they do not already exist. Never overwrite existing round status!
    rounds = [
        {
            "round_number": 1,
            "round_name": "Level 1",
            "criteria": [
                {"criterion": "Presentation", "max_score": 10.0, "scored_by": "Evaluator"},
                {"criterion": "Mentor Score", "max_score": 10.0, "scored_by": "Mentor"}
            ]
        },
        {
            "round_number": 2,
            "round_name": "Level 2",
            "criteria": [
                {"criterion": "Coding", "max_score": 10.0, "scored_by": "Evaluator"},
                {"criterion": "Architecture", "max_score": 10.0, "scored_by": "Evaluator"},
                {"criterion": "Outcome", "max_score": 10.0, "scored_by": "Evaluator"},
                {"criterion": "Future Plan", "max_score": 10.0, "scored_by": "Evaluator"},
                {"criterion": "Innovation", "max_score": 10.0, "scored_by": "Evaluator"},
                {"criterion": "Collaboration", "max_score": 10.0, "scored_by": "Evaluator"},
                {"criterion": "Mentor Score", "max_score": 10.0, "scored_by": "Mentor"}
            ]
        },
        {
            "round_number": 3,
            "round_name": "Level 3",
            "criteria": [
                {"criterion": "Mentor Score", "max_score": 10.0, "scored_by": "Mentor"}
            ]
        }
    ]
    for r in rounds:
        for c in r["criteria"]:
            if not frappe.db.exists("Evaluation Criterion", c["criterion"]):
                frappe.get_doc({
                    "doctype": "Evaluation Criterion",
                    "criterion_name": c["criterion"],
                    "scored_by": c.get("scored_by") or "Evaluator"
                }).insert(ignore_permissions=True)

        if not frappe.db.exists("Hackathon Round", r["round_name"]):
            doc = frappe.get_doc({
                "doctype": "Hackathon Round",
                "round_number": r["round_number"],
                "round_name": r["round_name"],
                "status": "Not Started",
                "mentor_scoring_mode": "Mentor Panel",
                "criteria": r["criteria"]
            })
            doc.insert(ignore_permissions=True)
    frappe.db.commit()

def backfill_evaluation_team_codes():
    frappe.db.sql("""
        UPDATE `tabHackathon Team`
        SET team_code = ''
        WHERE team_code = name OR team_code LIKE 'TEAM-%'
    """)
    frappe.db.sql("""
        UPDATE `tabEvaluation` e
        JOIN `tabHackathon Team` t ON e.team = t.name
        SET e.team_code = IFNULL(t.team_code, ''), e.team_name = IFNULL(t.team_name, '')
    """)
    frappe.db.commit()

def hide_standard_workspaces():
    workspaces_to_hide = ['Users', 'Website', 'Tools', 'Integrations', 'Build']
    for ws in workspaces_to_hide:
        if frappe.db.exists('Workspace', ws):
            frappe.db.set_value('Workspace', ws, 'public', 0)
            frappe.db.set_value('Workspace', ws, 'is_hidden', 1)
    frappe.db.commit()

def sync_custom_workspaces():
    import json
    import os
    for ws_dir in ["mentor_dashboard", "hackathon_control_center"]:
        path = frappe.get_app_path("hack_eval", "hackathon_eval", "workspace", ws_dir, f"{ws_dir}.json")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            ws_name = data.get("name")
            if frappe.db.exists("Workspace", ws_name):
                frappe.delete_doc("Workspace", ws_name, ignore_permissions=True, force=True)
            doc = frappe.get_doc(data)
            doc.flags.ignore_permissions = True
            doc.insert()
    frappe.db.commit()
    frappe.clear_cache()
