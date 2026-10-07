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
