import frappe
from frappe.utils import flt

@frappe.whitelist()
def reset_round(round_name, reset_level=None):
    frappe.only_for(["System Manager", "Hackathon Organizer"])
    round_doc = frappe.get_doc("Hackathon Round", round_name)
    
    if reset_level == "Revert completely to starting (Wipe all scores)":
        teams = frappe.get_all("Hackathon Team")
        for t in teams:
            doc = frappe.get_doc("Hackathon Team", t.name)
            doc.level1_score = 0
            doc.level2_score = 0
            doc.level3_score = 0
            doc.cumulative_score = 0
            doc.current_level = 1
            doc.status = "Active"
            doc.save(ignore_permissions=True)
        frappe.db.sql("DELETE FROM `tabEvaluation Score`")
        frappe.db.sql("DELETE FROM `tabEvaluation`")
        frappe.db.sql("DELETE FROM `tabTeam Round Result`")
        frappe.db.sql("UPDATE `tabHackathon Round` SET status='Not Started'")
        
    elif reset_level == "Revert to Level 1 (Wipe L2 & L3 scores)":
        teams = frappe.get_all("Hackathon Team")
        for t in teams:
            doc = frappe.get_doc("Hackathon Team", t.name)
            doc.level2_score = 0
            doc.level3_score = 0
            doc.cumulative_score = doc.level1_score or 0.0
            doc.current_level = 1
            doc.status = "Active"
            doc.save(ignore_permissions=True)
        frappe.db.sql("DELETE FROM `tabEvaluation Score` WHERE parent IN (SELECT name FROM `tabEvaluation` WHERE round IN ('Level 2', 'Level 3'))")
        frappe.db.sql("DELETE FROM `tabEvaluation` WHERE round IN ('Level 2', 'Level 3')")
        frappe.db.sql("DELETE FROM `tabTeam Round Result` WHERE round IN ('Level 2', 'Level 3')")
        frappe.db.sql("UPDATE `tabHackathon Round` SET status='Not Started' WHERE round_name IN ('Level 2', 'Level 3')")
        
    elif reset_level == "Revert to Level 2 (Wipe L3 scores)":
        teams = frappe.get_all("Hackathon Team")
        for t in teams:
            doc = frappe.get_doc("Hackathon Team", t.name)
            doc.level3_score = 0
            doc.cumulative_score = (doc.level1_score or 0.0) + (doc.level2_score or 0.0)
            doc.current_level = 2
            doc.status = "Active"
            doc.save(ignore_permissions=True)
        frappe.db.sql("DELETE FROM `tabEvaluation Score` WHERE parent IN (SELECT name FROM `tabEvaluation` WHERE round = 'Level 3')")
        frappe.db.sql("DELETE FROM `tabEvaluation` WHERE round = 'Level 3'")
        frappe.db.sql("DELETE FROM `tabTeam Round Result` WHERE round = 'Level 3'")
        frappe.db.sql("UPDATE `tabHackathon Round` SET status='Not Started' WHERE round_name = 'Level 3'")
        
    round_doc.status = "Not Started"
    round_doc.save(ignore_permissions=True)
    frappe.db.commit()
    return f"Round '{round_name}' reset processed."

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
    }, fields=[
        "name", "team_code", "team_name", "problem_statement_area",
        "member_1_type", "member_1_email",
        "member_2_type", "member_2_email",
        "member_3_type", "member_3_email"
    ])
    
    # Get all active mentors mapped by their track, and separate out Chief Mentors
    mentors = frappe.get_all("Mentor Profile", filters={"status": "Active"}, fields=["email", "track", "mentor_role"])
    mentors_by_track = {}
    chief_mentors = []
    
    for m in mentors:
        if m.mentor_role == "Chief Mentor":
            chief_mentors.append(m.email)
        elif m.track:
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
        if m.mentor_role != "Chief Mentor" and m.track and m.track.strip() in fallback_map:
            mentors_by_track[fallback_map[m.track.strip()]] = mentors_by_track.get(m.track.strip(), [])
    
    created_count = 0
    for team in eligible_teams:
        team_track = (team.problem_statement_area or "").strip()
        assigned_mentors = mentors_by_track.get(team_track, [])
        
        # Build Conflict of Interest (COI) faculty list for this team
        faculty_emails = set()
        for i in range(1, 4):
            m_type = team.get(f"member_{i}_type")
            m_email = team.get(f"member_{i}_email")
            if m_type == "Faculty" and m_email:
                faculty_emails.add(m_email.strip().lower())
        
        # Combine track-specific regular mentors and ALL Chief Mentors for this team
        all_evaluators = list(set(assigned_mentors + chief_mentors))
        
        for mentor_email in all_evaluators:
            # COI Check: Skip evaluation if the mentor is a faculty member of this team
            if mentor_email.strip().lower() in faculty_emails:
                continue
                
            exists = frappe.db.exists("Evaluation", {"team": team.name, "round": round_name, "evaluator": mentor_email})
            if not exists:
                eval_doc = frappe.get_doc({
                    "doctype": "Evaluation",
                    "team": team.name,
                    "team_code": team.team_code or "",
                    "team_name": team.team_name or "",
                    "round": round_name,
                    "evaluator": mentor_email,
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
    
    evaluations = frappe.get_all("Evaluation", filters={"round": round_name, "status": "Submitted"}, fields=["name", "team"])
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
def promote_round(round_name):
    frappe.only_for(["System Manager", "Hackathon Organizer"])
    round_doc = frappe.get_doc("Hackathon Round", round_name)
    if round_doc.status != "Closed":
        frappe.throw("Only Closed rounds can be advanced.")
        
    round_num = round_doc.round_number
    
    # Query all active/finalist teams currently in this round
    current_teams = frappe.get_all("Hackathon Team", filters={
        "status": ["in", ["Active", "Finalist"]],
        "current_level": round_num
    }, fields=["name", "evaluation_decision"])
    
    level_up_teams = [t for t in current_teams if t.evaluation_decision == "Level Up"]
    if not level_up_teams:
        frappe.throw("No teams have been marked as 'Level Up'. Please mark teams with 'Level Up' in the Hackathon Team list view before advancing.")
        
    advanced_count = 0
    eliminated_count = 0
    
    for t in current_teams:
        team_doc = frappe.get_doc("Hackathon Team", t.name)
        result_name = frappe.db.get_value("Team Round Result", {"team": t.name, "round": round_name}, "name")
        res_doc = frappe.get_doc("Team Round Result", result_name) if result_name else None

        if t.evaluation_decision == "Level Up":
            if round_num < 3:
                team_doc.current_level = round_num + 1
                team_doc.status = "Active"
                if res_doc: res_doc.outcome = "Advanced"
            else:
                team_doc.status = "Finalist"
                if res_doc: res_doc.outcome = "Finalist"
            team_doc.evaluation_decision = ""
            advanced_count += 1
        else:
            team_doc.status = "Eliminated"
            team_doc.eliminated_at_level = round_num
            team_doc.evaluation_decision = ""
            if res_doc: res_doc.outcome = "Eliminated"
            eliminated_count += 1

        team_doc.save(ignore_permissions=True)
        if res_doc:
            res_doc.save(ignore_permissions=True)
            
    recompute_round_results(round_name)
    frappe.db.commit()
    return f"Round {round_name} advanced successfully: {advanced_count} teams Levelled Up to Level {round_num + 1 if round_num < 3 else 'Finale'}, {eliminated_count} teams Eliminated."

@frappe.whitelist()
def rename_teams_to_codes():
    return "Team identifiers are preserved as TEAM-xxxx IDs internally."

@frappe.whitelist()
def set_team_evaluation_decision(team_name, decision):
    if frappe.session.user != "Administrator" and not any(r in frappe.get_roles() for r in ["System Manager", "Hackathon Organizer"]):
        frappe.throw("Not permitted. Only Admins and Hackathon Organizers can mark teams for Level Up.")
    if decision not in ["Level Up", ""]:
        frappe.throw("Invalid decision.")
    frappe.db.set_value("Hackathon Team", team_name, "evaluation_decision", decision)
    frappe.db.commit()
    return {"status": "success", "team": team_name, "decision": decision}

@frappe.whitelist()
def bulk_set_team_evaluation_decision(team_names, decision):
    if frappe.session.user != "Administrator" and not any(r in frappe.get_roles() for r in ["System Manager", "Hackathon Organizer"]):
        frappe.throw("Not permitted. Only Admins and Hackathon Organizers can mark teams for Level Up.")
    import json
    if isinstance(team_names, str):
        team_names = json.loads(team_names)
    if decision not in ["Level Up", ""]:
        frappe.throw("Invalid decision.")
    for name in team_names:
        frappe.db.set_value("Hackathon Team", name, "evaluation_decision", decision)
    frappe.db.commit()
    return {"status": "success", "count": len(team_names)}


def sanitize_request_params():
    """
    Sanitize request parameters before handler execution to prevent
    type casting crashes in Frappe core (e.g. export_in_background='undefined').
    """
    if hasattr(frappe, "local") and hasattr(frappe.local, "form_dict"):
        export_in_bg = frappe.local.form_dict.get("export_in_background")
        if export_in_bg in ("undefined", "null", "None", ""):
            frappe.local.form_dict["export_in_background"] = 0


@frappe.whitelist()
def sync_team_scores(team_name):
    """
    Recalculates round scores (level1_score, level2_score, level3_score) and
    cumulative_score (Average Score) for a Hackathon Team based on all Submitted evaluations.
    Updates Hackathon Team and Team Round Result in MariaDB.
    """
    if not team_name:
        return None

    # Handle if team identifier is team_code or team_name instead of docname
    if not frappe.db.exists("Hackathon Team", team_name):
        matched = frappe.db.get_value("Hackathon Team", {"team_code": team_name}, "name")
        if not matched:
            matched = frappe.db.get_value("Hackathon Team", {"team_name": team_name}, "name")
        if not matched:
            return None
        team_name = matched

    # Query submitted evaluations for this team
    submitted_evals = frappe.db.sql("""
        SELECT name, round, total_score
        FROM `tabEvaluation`
        WHERE team = %(team)s AND status = 'Submitted'
    """, {"team": team_name}, as_dict=True)

    # Fetch rounds mapping (round_name -> round_number)
    rounds_data = frappe.get_all("Hackathon Round", fields=["round_name", "round_number"])
    round_num_map = {r.round_name: r.round_number for r in rounds_data}
    round_num_map.setdefault("Level 1", 1)
    round_num_map.setdefault("Level 2", 2)
    round_num_map.setdefault("Level 3", 3)

    # Fetch active score adjustments for this team
    adjustments = frappe.get_all(
        "Score Adjustment",
        filters={"team": team_name, "is_active": 1},
        fields=["round", "criterion", "adjusted_score"]
    )
    adj_by_round = {}
    for a in adjustments:
        if a.round not in adj_by_round:
            adj_by_round[a.round] = {}
        if a.criterion:
            adj_by_round[a.round][a.criterion] = flt(a.adjusted_score)

    # Group submitted evaluations by round
    evals_by_round = {}
    for ev in submitted_evals:
        rnd = ev.round
        if rnd not in evals_by_round:
            evals_by_round[rnd] = []
        evals_by_round[rnd].append(ev)

    scores_by_level = {1: 0.0, 2: 0.0, 3: 0.0}

    for rnd, ev_list in evals_by_round.items():
        if not ev_list:
            continue
        level_num = round_num_map.get(rnd)
        if not level_num or level_num not in scores_by_level:
            continue

        adj_map = adj_by_round.get(rnd, {})
        if adj_map:
            # Criterion-level adjustments present: calculate effective criterion scores
            eval_names = [e.name for e in ev_list]
            c_scores = {}
            if eval_names:
                score_rows = frappe.db.sql("""
                    SELECT criterion, score
                    FROM `tabEvaluation Score`
                    WHERE parent IN %(eval_names)s
                """, {"eval_names": tuple(eval_names)}, as_dict=True)
                for row in score_rows:
                    c_scores.setdefault(row.criterion, []).append(flt(row.score))

            total_round_score = 0.0
            for c, sc_vals in c_scores.items():
                avg_sc = sum(sc_vals) / len(sc_vals) if sc_vals else 0.0
                eff_sc = adj_map.get(c, avg_sc)
                total_round_score += eff_sc
            scores_by_level[level_num] = round(total_round_score, 3)
        else:
            # Arithmetic average of total_score across submitted mentor evaluations
            avg_score = sum(flt(e.total_score) for e in ev_list) / len(ev_list)
            scores_by_level[level_num] = round(avg_score, 3)

    l1 = scores_by_level[1]
    l2 = scores_by_level[2]
    l3 = scores_by_level[3]
    cumulative = round(l1 + l2 + l3, 3)

    # Update Hackathon Team scores directly
    frappe.db.set_value("Hackathon Team", team_name, {
        "level1_score": l1,
        "level2_score": l2,
        "level3_score": l3,
        "cumulative_score": cumulative
    })

    # Also keep Team Round Result synchronized for rounds that have evaluations or existing results
    all_team_results = frappe.get_all("Team Round Result", filters={"team": team_name}, fields=["name", "round"])
    existing_rounds = {tr.round for tr in all_team_results}

    for tr in all_team_results:
        lvl = round_num_map.get(tr.round)
        r_score = scores_by_level.get(lvl, 0.0)
        ev_list = evals_by_round.get(tr.round, [])
        expected = frappe.db.count("Evaluation", {"team": team_name, "round": tr.round})
        frappe.db.set_value("Team Round Result", tr.name, {
            "round_score": r_score,
            "cumulative_score": cumulative,
            "evaluations_submitted": len(ev_list),
            "evaluations_expected": expected,
            "flag_incomplete": 1 if len(ev_list) < expected else 0
        })

    for rnd, ev_list in evals_by_round.items():
        if rnd not in existing_rounds:
            lvl = round_num_map.get(rnd)
            r_score = scores_by_level.get(lvl, 0.0)
            expected = frappe.db.count("Evaluation", {"team": team_name, "round": rnd})
            try:
                res_doc = frappe.get_doc({
                    "doctype": "Team Round Result",
                    "team": team_name,
                    "round": rnd,
                    "round_score": r_score,
                    "cumulative_score": cumulative,
                    "evaluations_submitted": len(ev_list),
                    "evaluations_expected": expected,
                    "flag_incomplete": 1 if len(ev_list) < expected else 0,
                    "review_status": "Not Required"
                })
                res_doc.insert(ignore_permissions=True)
            except Exception:
                pass

    return {
        "team": team_name,
        "level1_score": l1,
        "level2_score": l2,
        "level3_score": l3,
        "cumulative_score": cumulative
    }


@frappe.whitelist()
def sync_all_team_scores(all_teams=False):
    """
    Synchronizes scores for teams with evaluations or existing non-zero scores,
    or for all teams if all_teams=True.
    """
    if all_teams:
        teams = frappe.get_all("Hackathon Team", pluck="name")
    else:
        teams = frappe.db.sql_list("""
            SELECT DISTINCT team FROM `tabEvaluation` WHERE team IS NOT NULL AND team != ''
            UNION
            SELECT name FROM `tabHackathon Team` WHERE cumulative_score > 0 OR level1_score > 0 OR level2_score > 0 OR level3_score > 0
        """)

    count = 0
    for t_name in teams:
        sync_team_scores(t_name)
        count += 1

    frappe.db.commit()
    return f"Successfully synchronized scores for {count} teams."



