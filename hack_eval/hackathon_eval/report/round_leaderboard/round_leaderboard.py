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
        {"label": "Review Status", "fieldname": "review_status", "fieldtype": "Data", "width": 120},
        {"label": "Outcome", "fieldname": "outcome", "fieldtype": "Data", "width": 120}
    ]

def execute(filters=None):
    columns = get_columns()
    
    round_name = filters.get("round") if filters else None
    round_info = None
    if round_name:
        round_info = frappe.db.get_value("Hackathon Round", round_name, ["round_number", "status"], as_dict=True)
    
    # Query all active teams
    team_sql = """
        SELECT name, team_code, team_name, problem_statement_area as track, valid_composition, status, current_level, evaluation_decision
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
                
        # Calculate Current Round Score and Review Status
        round_score = 0.0
        review_status = "Pending"
        
        if round_name:
            current_evals = [e for e in evals if e.round == round_name]
            current_submitted = [e for e in submitted_evals if e.round == round_name]
            scores = [float(e.total_score or 0.0) for e in current_submitted]
            
            if len(scores) > 0:
                round_score = sum(scores) / len(scores)
                
            # Completed once all mentors assigned submit evaluations
            if current_evals and len(current_submitted) == len(current_evals):
                review_status = "Completed"
            else:
                review_status = "Pending"
        else:
            round_score = cumulative_score
            if evals and len(submitted_evals) == len(evals):
                review_status = "Completed"
            else:
                review_status = "Pending"
                
        # Determine Outcome based on round state
        outcome = "Pending"
        if round_info:
            r_num = round_info.round_number
            r_status = round_info.status
            if r_status in ["Open", "Not Started"]:
                outcome = "Pending"
            else: # Round is Closed
                if team.current_level > r_num or (r_num == 3 and team.status == "Winner") or (team.evaluation_decision == "Level Up"):
                    outcome = "Levelled Up"
                elif team.status == "Eliminated" or team.evaluation_decision == "Eliminate":
                    outcome = "Eliminated"
                else:
                    outcome = "Pending"
        else:
            if team.status == "Winner":
                outcome = "Winner"
            elif team.status == "Eliminated":
                outcome = "Eliminated"
            elif team.current_level > 1:
                outcome = "Levelled Up"
            else:
                outcome = "Pending"
            
        team_code_val = (team.team_code or "").strip()
        if team_code_val.startswith("TEAM-"):
            team_code_val = ""
        data.append({
            "team_code": team_code_val,
            "team": team_id,
            "team_name": team.team_name,
            "track": team.track,
            "valid_composition": team.valid_composition,
            "round_score": round_score,
            "cumulative_score": cumulative_score,
            "review_status": review_status,
            "outcome": outcome
        })
        
    # Sort automatically by Cumulative Score then Round Score, and alphabetically by Team Code if score is 0
    data.sort(key=lambda x: (-x["cumulative_score"], -x["round_score"], x["team_code"]))
    
    # Assign Rank
    for idx, row in enumerate(data):
        row["rank"] = idx + 1
        
    return columns, data, None, None, None
