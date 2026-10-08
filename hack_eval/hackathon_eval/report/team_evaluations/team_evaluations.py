import frappe
from frappe.utils import flt

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    return [
        {
            "fieldname": "team_code",
            "label": "Team Code",
            "fieldtype": "Data",
            "width": 120
        },
        {
            "fieldname": "team_name",
            "label": "Team Name",
            "fieldtype": "Data",
            "width": 180
        },
        {
            "fieldname": "track",
            "label": "Track",
            "fieldtype": "Data",
            "width": 180
        },
        {
            "fieldname": "round",
            "label": "Round",
            "fieldtype": "Data",
            "width": 120
        },
        {
            "fieldname": "status",
            "label": "Status",
            "fieldtype": "Data",
            "width": 120
        },
        {
            "fieldname": "average_score",
            "label": "Average Score",
            "fieldtype": "Float",
            "width": 120
        },
        {
            "fieldname": "team_link",
            "label": "Team Link",
            "fieldtype": "Data",
            "hidden": 1
        }
    ]

def get_data(filters):
    conditions = []
    if filters and filters.get('round'):
        conditions.append(f"e.round = '{filters.get('round')}'")
    if filters and filters.get('track'):
        conditions.append(f"t.problem_statement_area = '{filters.get('track')}'")
        
    # Role-based filtering
    is_chief_or_admin = frappe.has_permission("Evaluation", "write") # Rough check, we will do explicit role check
    roles = frappe.get_roles(frappe.session.user)
    
    if "Administrator" in roles or "System Manager" in roles or "Hackathon Organizer" in roles or "Chief Mentor" in roles:
        # Can see all teams
        pass
    else:
        # Regular mentor: only see teams they are explicitly evaluating
        conditions.append(f"e.evaluator = '{frappe.session.user}'")
        
    where_clause = " AND ".join(conditions)
    if where_clause:
        where_clause = " WHERE " + where_clause
        
    sql = f"""
        SELECT 
            t.team_code,
            t.team_name,
            t.name as team_link,
            t.problem_statement_area as track,
            e.round,
            t.status as status,
            AVG(e.total_score) as average_score
        FROM 
            `tabEvaluation` e
        JOIN 
            `tabHackathon Team` t ON e.team = t.name
        {where_clause}
        GROUP BY 
            t.name, e.round
    """
    
    return frappe.db.sql(sql, as_dict=True)
