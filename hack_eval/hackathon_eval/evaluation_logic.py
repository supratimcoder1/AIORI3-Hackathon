import frappe
from frappe.utils import flt

@frappe.whitelist()
def open_round(round_name):
    frappe.only_for(["System Manager", "Hackathon Organizer"])
    round_doc = frappe.get_doc("Hackathon Round", round_name)
    if round_doc.status not in ["Not Started", "Closed"]:
        frappe.throw(f"Round is currently {round_doc.status}. It cannot be opened.")
        
    round_doc.status = "Open"
    round_doc.save(ignore_permissions=True)
    
    # Auto-generate evaluation records for all eligible teams at this level
    round_num = round_doc.round_number
    eligible_teams = frappe.get_all("Hackathon Team", filters={
        "status": ["in", ["Active", "Finalist"]],
        "current_level": round_num
    }, fields=["name", "problem_statement_area"])
    
    # Get all active mentors mapped by their track
    mentors = frappe.get_all("Mentor Profile", filters={"status": "Active"}, fields=["email", "track"])
    mentors_by_track = {}
    for m in mentors:
        if m.track:
            track_name = m.track.strip()
            if track_name not in mentors_by_track:
                mentors_by_track[track_name] = []
            mentors_by_track[track_name].append(m.email)
            
    # Also support fallback mappings (e.g., 'and' instead of '&')
    fallback_map = {
        "Cloud Computing and IOT": "Cloud Computing & IOT",
        "6G and Future Networks": "6G & Future Networks"
    }
    for m in mentors:
        if m.track and m.track.strip() in fallback_map:
            mentors_by_track[fallback_map[m.track.strip()]] = mentors_by_track.get(m.track.strip(), [])
    
    created_count = 0
    for team in eligible_teams:
        team_track = (team.problem_statement_area or "").strip()
        assigned_mentors = mentors_by_track.get(team_track, [])
        
        for mentor_email in assigned_mentors:
            exists = frappe.db.exists("Evaluation", {"team": team.name, "round": round_name, "evaluator": mentor_email})
            if not exists:
                eval_doc = frappe.get_doc({
                    "doctype": "Evaluation",
                    "team": team.name,
                    "round": round_name,
                    "evaluator": mentor_email,
                    "evaluator_type": "Mentor",
                    "status": "Pending"
                })
                for rc in round_doc.criteria:
                    eval_doc.append("scores", {
                        "criterion": rc.criterion,
                        "max_score": flt(rc.max_score or 10.0),
                        "score": 0.0
                    })
                eval_doc.insert(ignore_permissions=True)
                created_count += 1
                
    frappe.db.commit()
    return f"Round '{round_name}' opened. {created_count} evaluation forms provisioned for assigned mentors."

@frappe.whitelist()
def reopen_round(round_name):
    frappe.only_for(["System Manager", "Hackathon Organizer"])
    round_doc = frappe.get_doc("Hackathon Round", round_name)
    round_doc.status = "Open"
    round_doc.save(ignore_permissions=True)
    frappe.db.commit()
    return f"Round '{round_name}' reopened for mentors."

@frappe.whitelist()
def close_round(round_name, force=0):
    frappe.only_for(["System Manager", "Hackathon Organizer"])
    round_doc = frappe.get_doc("Hackathon Round", round_name)
    if round_doc.status != "Open":
        frappe.throw("Only Open rounds can be closed.")
        
    pending = frappe.db.count("Evaluation", {"round": round_name, "status": ["in", ["Pending", "Draft"]]})
    if pending > 0 and not int(force):
        frappe.throw(f"There are {pending} pending evaluations. Click 'Force Close' to close anyway.")
        
    round_doc.status = "Closed"
    round_doc.save(ignore_permissions=True)
    frappe.db.commit()
    
    # Auto recompute immediately
    recompute_round_results(round_name)
    return "Round Closed. Mentor scoring is now locked, and results have been recomputed."

@frappe.whitelist()
def recompute_round_results(round_name):
    frappe.only_for(["System Manager", "Hackathon Organizer"])
    round_doc = frappe.get_doc("Hackathon Round", round_name)
    
    evaluations = frappe.get_all("Evaluation", filters={"round": round_name, "status": "Submitted"}, fields=["name", "team", "evaluator_type"])
    teams = frappe.get_all("Hackathon Team", filters={"status": ["in", ["Active", "Finalist", "Winner", "Eliminated"]]})
    
    disagreement_threshold = flt(frappe.db.get_single_value("Hackathon Settings", "disagreement_threshold") or 3.0)
    
    for team in teams:
        team_evs = [e for e in evaluations if e.team == team.name]
        if not team_evs:
            # Check if an evaluation was even expected
            expected = frappe.db.count("Evaluation", {"team": team.name, "round": round_name})
            if expected == 0:
                continue
                
        ev_docs = [frappe.get_doc("Evaluation", e.name) for e in team_evs]
        
        result_name = frappe.db.get_value("Team Round Result", {"team": team.name, "round": round_name}, "name")
        if not result_name:
            result = frappe.get_doc({
                "doctype": "Team Round Result",
                "team": team.name,
                "round": round_name
            })
        else:
            result = frappe.get_doc("Team Round Result", result_name)
            
        result.set("criterion_scores", [])
        
        total_score = 0.0
        flag_disagreement = 0
        
        # Group by criterion
        c_scores = {}
        for ev in ev_docs:
            for row in ev.scores:
                if row.criterion not in c_scores:
                    c_scores[row.criterion] = []
                c_scores[row.criterion].append(flt(row.score))
                
        # Check adjustments
        adjustments = frappe.get_all("Score Adjustment", filters={"team": team.name, "round": round_name, "is_active": 1}, fields=["criterion", "adjusted_score"])
        adj_map = {a.criterion: flt(a.adjusted_score) for a in adjustments if a.criterion}
        
        for c, scores in c_scores.items():
            avg = sum(scores) / len(scores) if scores else 0.0
            spread = max(scores) - min(scores) if scores else 0.0
            
            if spread >= disagreement_threshold:
                flag_disagreement = 1
                
            eff_score = adj_map.get(c, avg)
            
            result.append("criterion_scores", {
                "criterion": c,
                "evaluator_average": avg,
                "spread": spread,
                "adjusted_score": adj_map.get(c, 0.0),
                "effective_score": eff_score
            })
            total_score += eff_score
            
        result.round_score = total_score
        
        # Update team scores by level
        team_doc = frappe.get_doc("Hackathon Team", team.name)
        if round_doc.round_number == 1:
            team_doc.level1_score = total_score
        elif round_doc.round_number == 2:
            team_doc.level2_score = total_score
        elif round_doc.round_number == 3:
            team_doc.level3_score = total_score
            
        # Cumulative score calculation
        if round_doc.round_number == 1:
            result.previous_cumulative = 0.0
            team_doc.cumulative_score = flt(team_doc.level1_score)
        elif round_doc.round_number == 2:
            result.previous_cumulative = flt(team_doc.level1_score)
            team_doc.cumulative_score = flt(team_doc.level1_score) + flt(team_doc.level2_score)
        elif round_doc.round_number == 3:
            result.previous_cumulative = flt(team_doc.level1_score) + flt(team_doc.level2_score)
            team_doc.cumulative_score = flt(team_doc.level1_score) + flt(team_doc.level2_score) + flt(team_doc.level3_score)
            
        team_doc.save(ignore_permissions=True)
        result.cumulative_score = team_doc.cumulative_score
        
        # Flags
        expected = frappe.db.count("Evaluation", {"team": team.name, "round": round_name})
        result.evaluations_expected = expected
        result.evaluations_submitted = len(ev_docs)
        result.flag_incomplete = 1 if result.evaluations_submitted < expected else 0
        result.flag_disagreement = flag_disagreement
        
        if result.flag_incomplete or result.flag_disagreement:
            if result.review_status == "Not Required":
                result.review_status = "Pending"
        
        result.save(ignore_permissions=True)
        
    # Ranking across the round
    results = frappe.get_all("Team Round Result", filters={"round": round_name}, fields=["name", "cumulative_score", "round_score"], order_by="cumulative_score desc, round_score desc")
    
    cutoff = round_doc.advance_count
    near_cutoff_margin = frappe.db.get_single_value("Hackathon Settings", "near_cutoff_ranks") or 10
    
    for idx, r in enumerate(results):
        rank = idx + 1
        res_doc = frappe.get_doc("Team Round Result", r.name)
        res_doc.rank = rank
        
        res_doc.flag_near_cutoff = 1 if cutoff and abs(rank - cutoff) <= near_cutoff_margin else 0
        
        # Check tie at cutoff boundary
        res_doc.flag_tie_at_cutoff = 0
        if cutoff and rank == cutoff:
            if idx + 1 < len(results):
                next_r = results[idx+1]
                if flt(r.cumulative_score) == flt(next_r.cumulative_score) and flt(r.round_score) == flt(next_r.round_score):
                    res_doc.flag_tie_at_cutoff = 1
                    frappe.db.set_value("Team Round Result", next_r.name, "flag_tie_at_cutoff", 1)
                    
        res_doc.save(ignore_permissions=True)
        
    frappe.db.commit()
    return "Recomputed all results and ranked teams."

@frappe.whitelist()
def promote_round(round_name, advance_count=None):
    frappe.only_for(["System Manager", "Hackathon Organizer"])
    round_doc = frappe.get_doc("Hackathon Round", round_name)
    if round_doc.status != "Closed":
        frappe.throw("Only Closed rounds can have cutoff applied and promoted.")
        
    if advance_count is not None and int(advance_count) > 0:
        round_doc.advance_count = int(advance_count)
        round_doc.save(ignore_permissions=True)
        
    recompute_round_results(round_name)
    
    cutoff = round_doc.advance_count
    if not cutoff or cutoff <= 0:
        frappe.throw("Please set a valid Advance Count (N) before promoting.")
        
    ties = frappe.db.count("Team Round Result", {"round": round_name, "flag_tie_at_cutoff": 1})
    if ties > 0:
        frappe.throw(f"There are tied teams right at cutoff rank {cutoff}. A Reviewer must resolve the tie before advancing.")
        
    results = frappe.get_all("Team Round Result", filters={"round": round_name}, fields=["name", "team", "rank"], order_by="rank asc")
    
    advanced_count = 0
    eliminated_count = 0
    
    for r in results:
        team_doc = frappe.get_doc("Hackathon Team", r.team)
        res_doc = frappe.get_doc("Team Round Result", r.name)
        
        if r.rank <= cutoff:
            # Advance
            if round_doc.round_number < 3:
                team_doc.current_level = round_doc.round_number + 1
                team_doc.status = "Active"
                res_doc.outcome = "Advanced"
            else:
                team_doc.status = "Winner"
                team_doc.final_position = r.rank
                if r.rank == 1: res_doc.outcome = "First"
                elif r.rank == 2: res_doc.outcome = "Second"
                elif r.rank == 3: res_doc.outcome = "Third"
                else: res_doc.outcome = "Finalist"
            advanced_count += 1
        else:
            # Eliminate
            team_doc.status = "Eliminated"
            team_doc.eliminated_at_level = round_doc.round_number
            res_doc.outcome = "Eliminated"
            eliminated_count += 1
            
        team_doc.save(ignore_permissions=True)
        res_doc.save(ignore_permissions=True)
        
    frappe.db.commit()
    return f"Cutoff {cutoff} applied successfully: {advanced_count} advanced, {eliminated_count} eliminated."
