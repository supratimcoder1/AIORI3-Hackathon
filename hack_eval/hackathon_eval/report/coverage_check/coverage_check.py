import frappe

def execute(filters=None):
    columns, data = get_columns(), get_data(filters)
    return columns, data

def get_columns():
    return [
        {"label": "Team", "fieldname": "team", "fieldtype": "Link", "options": "Hackathon Team", "width": 200},
        {"label": "Round", "fieldname": "round", "fieldtype": "Link", "options": "Hackathon Round", "width": 120},
        {"label": "Missing Mentor", "fieldname": "missing_mentor", "fieldtype": "Check", "width": 120},
        {"label": "Evaluations Expected", "fieldname": "expected", "fieldtype": "Int", "width": 150},
        {"label": "Evaluations Found", "fieldname": "found", "fieldtype": "Int", "width": 150},
        {"label": "Evaluations Submitted", "fieldname": "submitted", "fieldtype": "Int", "width": 150},
        {"label": "Status", "fieldname": "status", "fieldtype": "Data", "width": 150}
    ]

def get_data(filters):
    # This report might be tricky because we need to join Team with Round if the round is active.
    # We can look at Team Round Result to find expectations, or just compute dynamically.
    
    conditions = []
    if filters.get("round"):
        conditions.append(f"trr.round = {frappe.db.escape(filters.get('round'))}")
    
    where_clause = " AND ".join(conditions) if conditions else "1=1"

    sql = f"""
        SELECT 
            ht.name as team,
            trr.round,
            (CASE WHEN (SELECT COUNT(*) FROM `tabEvaluation` ev WHERE ev.team = ht.name AND ev.round = trr.round) = 0 THEN 1 ELSE 0 END) as missing_mentor,
            trr.evaluations_expected as expected,
            (SELECT COUNT(*) FROM `tabEvaluation` ev WHERE ev.team = ht.name AND ev.round = trr.round) as found,
            trr.evaluations_submitted as submitted,
            (CASE 
                WHEN trr.evaluations_submitted < trr.evaluations_expected THEN 'Incomplete'
                ELSE 'Complete'
            END) as status
        FROM `tabHackathon Team` ht
        JOIN `tabTeam Round Result` trr ON trr.team = ht.name
        WHERE {where_clause}
        ORDER BY missing_mentor DESC, status ASC, team ASC
    """
    
    return frappe.db.sql(sql, as_dict=True)
