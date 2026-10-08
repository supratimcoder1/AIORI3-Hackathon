import frappe
from frappe.model.document import Document
import re

def clean_email(email_str):
    if not email_str: return email_str
    # Extract the first valid email from the string
    match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', str(email_str))
    if match:
        return match.group(0).lower()
    return email_str

class HackathonTeam(Document):
    def before_validate(self):
        # Aggressively clean emails before Frappe's built-in Email fieldtype validation crashes the import
        self.member_1_email = clean_email(self.member_1_email)
        self.member_2_email = clean_email(self.member_2_email)
        self.member_3_email = clean_email(self.member_3_email)
        self.email_address_1 = clean_email(self.email_address_1)
        self.email_address_2 = clean_email(self.email_address_2)

    def validate(self):
        self.validate_team_composition()

    def before_insert(self):
        import uuid
        self.team_uuid = str(uuid.uuid4())
        
    def validate_team_composition(self):
        members = [
            (self.member_1_name, self.member_1_type),
            (self.member_2_name, self.member_2_type),
            (self.member_3_name, self.member_3_type),
        ]
        student_count = sum(1 for name, m_type in members if name and m_type and m_type.strip().lower() == "student")
        faculty_count = sum(1 for name, m_type in members if name and m_type and m_type.strip().lower() == "faculty")

        if faculty_count >= 1 and student_count >= 2:
            self.valid_composition = 1
        else:
            self.valid_composition = 0

    def on_trash(self):
        # Optional cleanup logic if a team is "killed" by deleting it
        pass

    def after_insert(self):
        # If teams are imported while a round is already Open, auto-provision evaluations for them!
        if self.current_level:
            round_name = f"Level {self.current_level}"
            if frappe.db.exists("Hackathon Round", round_name):
                rd = frappe.get_doc("Hackathon Round", round_name)
                if rd.status == "Open" and self.status in ["Active", "Finalist"]:
                    team_track = (self.problem_statement_area or "").strip()
                    mentors = frappe.get_all("Mentor Profile", filters={"status": "Active"}, fields=["email", "track", "mentor_role"])
                    
                    assigned_mentors = []
                    chief_mentors = []
                    fallback_map = {
                        "Cloud Computing and IOT": "Cloud Computing & IOT",
                        "6G and Future Networks": "6G & Future Networks"
                    }
                    for m in mentors:
                        if m.get("mentor_role") == "Chief Mentor":
                            chief_mentors.append(m.email)
                            continue
                        t = (m.track or "").strip()
                        if t in fallback_map:
                            t = fallback_map[t]
                        if t == team_track:
                            assigned_mentors.append(m.email)
                            
                    # Build Conflict of Interest (COI) faculty list for this team
                    faculty_emails = set()
                    for i in range(1, 4):
                        m_type = self.get(f"member_{i}_type")
                        m_email = self.get(f"member_{i}_email")
                        if m_type == "Faculty" and m_email:
                            faculty_emails.add(m_email.strip().lower())
                            
                    all_evaluators = list(set(assigned_mentors + chief_mentors))
                    for mentor_email in all_evaluators:
                        # COI Check: Skip evaluation if the mentor is a faculty member of this team
                        if mentor_email.strip().lower() in faculty_emails:
                            continue
                            
                        if not frappe.db.exists("Evaluation", {"team": self.name, "round": round_name, "evaluator": mentor_email}):
                            eval_doc = frappe.get_doc({
                                "doctype": "Evaluation",
                                "team": self.name,
                                "round": round_name,
                                "evaluator": mentor_email,
                                "status": "Pending"
                            })
                            from frappe.utils import flt
                            for rc in rd.criteria:
                                eval_doc.append("scores", {
                                    "criterion": rc.criterion,
                                    "max_score": flt(rc.max_score or 10.0),
                                    "score": 0.0
                                })
                            eval_doc.insert(ignore_permissions=True)
