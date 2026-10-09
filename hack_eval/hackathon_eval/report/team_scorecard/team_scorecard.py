import frappe

def get_columns():
    return [
        {"label": "Team Code", "fieldname": "team_code", "fieldtype": "Data", "width": 160},
        {"label": "Team Name", "fieldname": "team_name", "fieldtype": "Data", "width": 180},
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
            COALESCE(NULLIF(t.team_code, ''), t.name) as team_code,
            t.team_name as team_name,
            ev.team,
            ev.round,
            ev.status as ev_status,
            ev.name as evaluation,
            ev.evaluator,
            SUM(es.score) as score,
            SUM(es.max_score) as max_score
        FROM `tabEvaluation Score` es
        JOIN `tabEvaluation` ev ON ev.name = es.parent
        JOIN `tabHackathon Team` t ON t.name = ev.team
        WHERE {where_clause}
        GROUP BY ev.name
        ORDER BY ev.team ASC, ev.evaluator ASC
    """
    
    data = list(frappe.db.sql(sql, as_dict=True))
    
    if data:
        submitted_data = [d for d in data if d.get("ev_status") == "Submitted"]
        total_score = sum(d.get("score") or 0.0 for d in submitted_data)
        total_max = sum(d.get("max_score") or 0.0 for d in submitted_data)
        valid_count = len(submitted_data) if submitted_data else 1
        
        avg_score = total_score / valid_count
        avg_max = total_max / valid_count
        
        # Spacer row
        data.append({
            "team_code": "", "team_name": "", "team": "", "round": "", "evaluation": "", "evaluator": "", "score": None, "max_score": None
        })
        
        # Grand Total row
        data.append({
            "team_code": "",
            "team_name": "",
            "team": "",
            "round": "",
            "evaluation": "",
            "evaluator": "<b>GRAND TOTAL (Sum of Mentors)</b>",
            "score": total_score,
            "max_score": total_max
        })
        
        # Average / Final Level Score row
        data.append({
            "team_code": "",
            "team_name": "",
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
            WHERE ev.team = %s AND ev.status = 'Submitted'
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
