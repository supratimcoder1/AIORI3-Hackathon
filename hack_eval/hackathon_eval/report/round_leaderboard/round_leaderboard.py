import frappe

def get_columns():
    return [
        {"label": "Rank", "fieldname": "rank", "fieldtype": "Int", "width": 60},
        {"label": "Team Code", "fieldname": "team_code", "fieldtype": "Data", "width": 160},
        {"label": "Team Name", "fieldname": "team_name", "fieldtype": "Data", "width": 180},
        {"label": "Track", "fieldname": "track", "fieldtype": "Data", "width": 180},
        {"label": "Valid Composition", "fieldname": "valid_composition", "fieldtype": "Check", "width": 80},
        {"label": "Round Score", "fieldname": "round_score", "fieldtype": "Float", "width": 100},
        {"label": "Cumulative Score", "fieldname": "cumulative_score", "fieldtype": "Float", "width": 100},
        {"label": "Incomplete", "fieldname": "flag_incomplete", "fieldtype": "Check", "width": 80},
        {"label": "Disagreement", "fieldname": "flag_disagreement", "fieldtype": "Check", "width": 80},
        {"label": "Near Cutoff", "fieldname": "flag_near_cutoff", "fieldtype": "Check", "width": 80},
        {"label": "Tie at Cutoff", "fieldname": "flag_tie_at_cutoff", "fieldtype": "Check", "width": 80},
        {"label": "Review Status", "fieldname": "review_status", "fieldtype": "Data", "width": 120},
        {"label": "Outcome", "fieldname": "outcome", "fieldtype": "Data", "width": 100}
    ]

def execute(filters=None):
    columns = get_columns()
    
    round_name = filters.get("round") if filters else None
    
    # Query all active teams
    team_sql = """
        SELECT name, team_code, team_name, problem_statement_area as track, valid_composition, status
        FROM `tabHackathon Team`
        WHERE status IN ('Active', 'Finalist', 'Winner', 'Eliminated')
    """
    if filters and filters.get("track"):
        team_sql += f" AND problem_statement_area = {frappe.db.escape(filters.get('track'))}"
        
    teams = frappe.db.sql(team_sql, as_dict=True)
    
    # Query all evaluations with sum of scores
    eval_sql = """
        SELECT 
            ev.team,
            ev.round,
            ev.evaluator,
            ev.status,
            ev.name as evaluation_id,
            SUM(es.score) as total_score
        FROM `tabEvaluation` ev
        LEFT JOIN `tabEvaluation Score` es ON es.parent = ev.name
        GROUP BY ev.name
    """
    eval_data = frappe.db.sql(eval_sql, as_dict=True)
    
    # Organize by team
    team_evals = {}
    for e in eval_data:
        if e.team not in team_evals:
            team_evals[e.team] = []
        team_evals[e.team].append(e)
        
    try:
        threshold = float(frappe.db.get_single_value("Hackathon Settings", "disagreement_threshold") or 3.0)
    except:
        threshold = 3.0
        
    data = []
    
    for team in teams:
        team_id = team.name
        evals = team_evals.get(team_id, [])
        
        # Separate submitted vs all evaluations
        submitted_evals = [e for e in evals if e.status == "Submitted"]
        
        # Calculate Cumulative Score across ALL rounds live (using ONLY submitted)
        round_totals = {}
        round_counts = {}
        for e in submitted_evals:
            rnd = e.round
            if rnd not in round_totals:
                round_totals[rnd] = 0.0
                round_counts[rnd] = 0
            round_totals[rnd] += float(e.total_score or 0.0)
            round_counts[rnd] += 1
            
        cumulative_score = 0.0
        for rnd in round_totals:
            if round_counts[rnd] > 0:
                cumulative_score += (round_totals[rnd] / round_counts[rnd])
                
        # Calculate Current Round Score
        round_score = 0.0
        flag_incomplete = 0
        flag_disagreement = 0
        
        if round_name:
            # All provisioned evals for this round
            current_evals = [e for e in evals if e.round == round_name]
            
            # Only submitted evals for scoring
            current_submitted = [e for e in submitted_evals if e.round == round_name]
            scores = [float(e.total_score or 0.0) for e in current_submitted]
            
            if len(scores) > 0:
                round_score = sum(scores) / len(scores)
                spread = max(scores) - min(scores)
                if spread >= threshold:
                    flag_disagreement = 1
                    
            submitted = len(current_submitted)
            if submitted < len(current_evals):
                flag_incomplete = 1
        else:
            round_score = cumulative_score
            
        team_code_val = (team.team_code or "").strip() or team_id
        data.append({
            "team_code": team_code_val,
            "team": team_id,
            "team_name": team.team_name,
            "track": team.track,
            "valid_composition": team.valid_composition,
            "round_score": round_score,
            "cumulative_score": cumulative_score,
            "flag_incomplete": flag_incomplete,
            "flag_disagreement": flag_disagreement,
            "flag_near_cutoff": 0,
            "flag_tie_at_cutoff": 0,
            "review_status": "Pending" if (flag_incomplete or flag_disagreement) else "Not Required",
            "outcome": "Pending"
        })
        
    # Sort automatically by Cumulative Score then Round Score, and alphabetically by Team Code if score is 0
    data.sort(key=lambda x: (-x["cumulative_score"], -x["round_score"], x["team_code"]))
    
    # Assign Rank
    for idx, row in enumerate(data):
        row["rank"] = idx + 1
        
    return columns, data, None, None, None
