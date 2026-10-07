import frappe

def execute(filters=None):
    columns, data = get_columns(), get_data(filters)
    return columns, data

def get_columns():
    return [
        {"label": "Evaluator", "fieldname": "evaluator", "fieldtype": "Link", "options": "User", "width": 200},
        {"label": "Role", "fieldname": "evaluator_type", "fieldtype": "Data", "width": 120},
        {"label": "Assigned", "fieldname": "total_assigned", "fieldtype": "Int", "width": 100},
        {"label": "Submitted", "fieldname": "total_submitted", "fieldtype": "Int", "width": 100},
        {"label": "Pending", "fieldname": "total_pending", "fieldtype": "Int", "width": 100},
        {"label": "Avg Score Given", "fieldname": "avg_score", "fieldtype": "Float", "width": 120},
        {"label": "Score Spread", "fieldname": "score_spread", "fieldtype": "Float", "width": 120}
    ]

def get_data(filters):
    conditions = []
    if filters.get("round"):
        conditions.append(f"round = {frappe.db.escape(filters.get('round'))}")
    
    where_clause = " AND ".join(conditions) if conditions else "1=1"

    sql = f"""
        SELECT 
            evaluator,
            MAX(evaluator_type) as evaluator_type,
            COUNT(name) as total_assigned,
            SUM(CASE WHEN status = 'Submitted' THEN 1 ELSE 0 END) as total_submitted,
            SUM(CASE WHEN status != 'Submitted' THEN 1 ELSE 0 END) as total_pending,
            AVG(CASE WHEN status = 'Submitted' THEN total_score ELSE NULL END) as avg_score,
            (MAX(CASE WHEN status = 'Submitted' THEN total_score ELSE NULL END) - 
             MIN(CASE WHEN status = 'Submitted' THEN total_score ELSE NULL END)) as score_spread
        FROM `tabEvaluation`
        WHERE {where_clause}
        GROUP BY evaluator
        ORDER BY total_pending DESC, total_assigned DESC
    """
    
    return frappe.db.sql(sql, as_dict=True)
