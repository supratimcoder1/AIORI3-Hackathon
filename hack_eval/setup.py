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
    backfill_evaluation_team_codes()
    sync_custom_workspaces()
    hide_standard_workspaces()

def backfill_evaluation_team_codes():
    frappe.db.sql("""
        UPDATE `tabEvaluation` e
        JOIN `tabHackathon Team` t ON e.team = t.name
        SET e.team_code = t.team_code, e.team_name = t.team_name
        WHERE IFNULL(e.team_code, '') = '' OR IFNULL(e.team_name, '') = ''
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
