import frappe

def get_evaluation_permission_query(user):
    if not user: user = frappe.session.user
    roles = frappe.get_roles(user)
    if "System Manager" in roles or "Hackathon Organizer" in roles or "Reviewer" in roles or "Chief Mentor" in roles:
        return ""
    # Mentors/Evaluators only see their own assigned evaluations
    return f"`tabEvaluation`.evaluator = {frappe.db.escape(user)}"

def evaluation_has_permission(doc, ptype="read", user=None):
    if not user: user = frappe.session.user
    roles = frappe.get_roles(user)
    
    # Admins and Organizers have full access globally
    if "System Manager" in roles or "Hackathon Organizer" in roles or user == "Administrator":
        return True
        
    # Chief Mentors can read all evaluations globally
    if ptype == "read" and "Chief Mentor" in roles:
        return True
        
    # Users can only write/submit THEIR OWN evaluations
    if doc.evaluator == user:
        if ptype in ["write", "submit", "delete"]:
            # Regular mentors and Chief Mentors are locked out if the round is closed or they already submitted
            round_status = frappe.db.get_value("Hackathon Round", doc.round, "status")
            if round_status != "Open":
                return False
            if not doc.is_new():
                db_status = frappe.db.get_value("Evaluation", doc.name, "status")
                if db_status == "Submitted":
                    return False
        return True
        
    return False

def get_team_permission_query(user):
    if not user: user = frappe.session.user
    roles = frappe.get_roles(user)
    if "System Manager" in roles or "Hackathon Organizer" in roles or "Reviewer" in roles or "Chief Mentor" in roles:
        return ""
    return f"`tabHackathon Team`.name in (select team from `tabEvaluation` where evaluator = {frappe.db.escape(user)})"

def team_has_permission(doc, ptype="read", user=None):
    if not user: user = frappe.session.user
    roles = frappe.get_roles(user)
    if "System Manager" in roles or "Hackathon Organizer" in roles or "Reviewer" in roles or "Chief Mentor" in roles:
        return True
    
    if ptype == "read":
        return bool(frappe.db.exists("Evaluation", {"team": doc.name, "evaluator": user}))
    return False

def generate_user_uuid(doc, method):
    import uuid
    doc.custom_uuid = str(uuid.uuid4())
