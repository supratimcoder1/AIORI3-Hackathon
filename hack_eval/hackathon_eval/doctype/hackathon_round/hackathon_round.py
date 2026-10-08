import frappe
from frappe.model.document import Document
from frappe.utils import flt

class HackathonRound(Document):
    def validate(self):
        # Calculate max_round_score from criteria
        total = 0.0
        if self.criteria:
            for c in self.criteria:
                total += flt(c.max_score)
        self.max_round_score = total
        
        # Calculate max_cumulative_score
        prev_cumulative = 0.0
        if self.round_number > 1:
            prev_round_name = f"Level {self.round_number - 1}"
            if frappe.db.exists("Hackathon Round", prev_round_name):
                prev_cumulative = flt(frappe.db.get_value("Hackathon Round", prev_round_name, "max_cumulative_score"))
        
        self.max_cumulative_score = prev_cumulative + self.max_round_score

    def on_update(self):
        # Auto-provision evaluations if status is changed to Open manually via save
        if self.has_value_changed('status') and self.status == 'Open':
            from hack_eval.hackathon_eval.evaluation_logic import open_round
            try:
                # We use a delayed execution or direct call 
                # Wait, open_round checks status not in ["Not Started", "Closed"] and throws!
                # We need to bypass it or adapt it.
                # Actually, open_round modifies the status itself. Let's just generate the evaluations manually here.
                round_num = self.round_number
                eligible_teams = frappe.get_all("Hackathon Team", filters={
                    "status": ["in", ["Active", "Finalist"]],
                    "current_level": round_num
                }, fields=[
                    "name", "problem_statement_area",
                    "member_1_type", "member_1_email",
                    "member_2_type", "member_2_email",
                    "member_3_type", "member_3_email"
                ])
                
                mentors = frappe.get_all("Mentor Profile", filters={"status": "Active"}, fields=["email", "track"])
                mentors_by_track = {}
                for m in mentors:
                    if m.track:
                        t = m.track.strip()
                        if t not in mentors_by_track: mentors_by_track[t] = []
                        mentors_by_track[t].append(m.email)
                
                fallback_map = {
                    "Cloud Computing and IOT": "Cloud Computing & IOT",
                    "6G and Future Networks": "6G & Future Networks"
                }
                for m in mentors:
                    if m.track and m.track.strip() in fallback_map:
                        mentors_by_track[fallback_map[m.track.strip()]] = mentors_by_track.get(m.track.strip(), [])
                
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
                            
                    for mentor_email in assigned_mentors:
                        # COI Check: Skip evaluation if the mentor is a faculty member of this team
                        if mentor_email.strip().lower() in faculty_emails:
                            continue
                            
                        if not frappe.db.exists("Evaluation", {"team": team.name, "round": self.name, "evaluator": mentor_email}):
                            eval_doc = frappe.get_doc({
                                "doctype": "Evaluation",
                                "team": team.name,
                                "round": self.name,
                                "evaluator": mentor_email,
                                "status": "Pending"
                            })
                            for rc in self.criteria:
                                eval_doc.append("scores", {
                                    "criterion": rc.criterion,
                                    "max_score": flt(rc.max_score or 10.0),
                                    "score": 0.0
                                })
                            eval_doc.insert(ignore_permissions=True)
            except Exception as e:
                frappe.log_error(title="Auto-provision Evaluations Failed", message=str(e))

