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
            "width": 160
        },
        {
            "fieldname": "team_name",
            "label": "Team Name",
            "fieldtype": "Data",
            "width": 180
        },
        {
            "fieldname": "valid",
            "label": "Valid",
            "fieldtype": "Data",
            "width": 100
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
        },
        {
            "fieldname": "evaluation_id",
            "label": "Evaluation ID",
            "fieldtype": "Data",
            "hidden": 1
        }
    ]

def get_data(filters):
    conditions = []
    values = {"user": frappe.session.user}
    if filters and filters.get('round'):
        conditions.append("e.round = %(round)s")
        values["round"] = filters.get("round")
    if filters and filters.get('track'):
        conditions.append("t.problem_statement_area = %(track)s")
        values["track"] = filters.get("track")
        
    roles = frappe.get_roles(frappe.session.user)
    is_privileged = any(r in roles for r in ["Administrator", "System Manager", "Hackathon Organizer", "Chief Mentor"])
    
    if not is_privileged:
        conditions.append("e.evaluator = %(user)s")
        
    where_clause = ""
    if conditions:
        where_clause = " WHERE " + " AND ".join(conditions)
        
    sql = f"""
        SELECT 
            IFNULL(t.team_code, '') as team_code,
            t.name as team_link,
            t.team_name,
            COALESCE(MAX(CASE WHEN e.evaluator = %(user)s THEN e.name ELSE NULL END), MAX(e.name)) as evaluation_id,
            CASE WHEN IFNULL(t.valid_composition, 0) = 1 THEN 'Valid' ELSE 'Invalid' END as valid,
            t.problem_statement_area as track,
            e.round,
            t.status as status,
            ROUND(IFNULL(AVG(CASE WHEN e.status = 'Submitted' THEN e.total_score ELSE NULL END), 0), 3) as average_score
        FROM 
            `tabEvaluation` e
        JOIN 
            `tabHackathon Team` t ON (e.team = t.name)
        {where_clause}
        GROUP BY 
            t.name, t.team_code, t.team_name, t.valid_composition, t.problem_statement_area, e.round, t.status
        ORDER BY 
            average_score DESC, team_code ASC
    """
    
    return frappe.db.sql(sql, values, as_dict=True)
