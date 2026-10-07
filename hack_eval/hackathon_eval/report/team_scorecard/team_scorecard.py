import frappe

def get_columns():
    return [
        {"label": "Team", "fieldname": "team", "fieldtype": "Link", "options": "Hackathon Team", "width": 150},
        {"label": "Round", "fieldname": "round", "fieldtype": "Link", "options": "Hackathon Round", "width": 120},
        {"label": "Evaluation", "fieldname": "evaluation", "fieldtype": "Link", "options": "Evaluation", "width": 150},
        {"label": "Evaluator", "fieldname": "evaluator", "fieldtype": "Data", "width": 250},
        {"label": "Total Score Given", "fieldname": "score", "fieldtype": "Float", "width": 140},
        {"label": "Max Possible Score", "fieldname": "max_score", "fieldtype": "Float", "width": 140}
    ]

def get_data(filters):
    conditions = []
    if filters and filters.get("team"):
        conditions.append(f"ev.team = {frappe.db.escape(filters.get('team'))}")
    if filters and filters.get("round"):
        conditions.append(f"ev.round = {frappe.db.escape(filters.get('round'))}")
    if filters and filters.get("evaluator"):
        conditions.append(f"ev.evaluator = {frappe.db.escape(filters.get('evaluator'))}")
        
    where_clause = " AND ".join(conditions) if conditions else "1=1"
    
    sql = f"""
        SELECT
            ev.team,
            ev.round,
            ev.name as evaluation,
            ev.evaluator,
            SUM(es.score) as score,
            SUM(es.max_score) as max_score
        FROM `tabEvaluation Score` es
        JOIN `tabEvaluation` ev ON ev.name = es.parent
        WHERE {where_clause}
        GROUP BY ev.name
        ORDER BY ev.team ASC, ev.evaluator ASC
    """
    
    data = list(frappe.db.sql(sql, as_dict=True))
    
    if data:
        total_score = sum(d.get("score") or 0.0 for d in data)
        total_max = sum(d.get("max_score") or 0.0 for d in data)
        avg_score = total_score / len(data)
        avg_max = total_max / len(data)
        
        # Spacer row
        data.append({
            "team": "", "round": "", "evaluation": "", "evaluator": "", "score": None, "max_score": None
        })
        
        # Grand Total row
        data.append({
            "team": "",
            "round": "",
            "evaluation": "",
            "evaluator": "<b>GRAND TOTAL (Sum of Mentors)</b>",
            "score": total_score,
            "max_score": total_max
        })
        
        # Average / Final Level Score row
        data.append({
            "team": "",
            "round": "",
            "evaluation": "",
            "evaluator": "<b style='color: blue;'>AVERAGE SCORE (Level Score)</b>",
            "score": avg_score,
            "max_score": avg_max
        })
        
    return data

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    
    report_summary = []
    if filters and filters.get("team"):
        team_name = filters.get("team")
        
        # Calculate Live Cumulative Score across ALL rounds directly from evaluations
        live_sql = """
            SELECT 
                ev.round, 
                ev.evaluator, 
                SUM(es.score) as total_eval_score
            FROM `tabEvaluation` ev
            JOIN `tabEvaluation Score` es ON es.parent = ev.name
            WHERE ev.team = %s
            GROUP BY ev.round, ev.evaluator
        """
        all_evals = frappe.db.sql(live_sql, team_name, as_dict=True)
        
        round_totals = {}
        round_counts = {}
        for r in all_evals:
            rnd = r.round
            if rnd not in round_totals:
                round_totals[rnd] = 0.0
                round_counts[rnd] = 0
            round_totals[rnd] += float(r.total_eval_score or 0.0)
            round_counts[rnd] += 1
            
        live_cumulative = 0.0
        for rnd in round_totals:
            if round_counts[rnd] > 0:
                live_cumulative += (round_totals[rnd] / round_counts[rnd])
                
        report_summary.append({
            "value": round(live_cumulative, 3),
            "label": "Live Cumulative Score (All Rounds)",
            "indicator": "Blue",
            "datatype": "Float"
        })
        
    return columns, data, None, None, report_summary
