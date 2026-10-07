import frappe
import csv
import string
import random
from io import StringIO

def get_random_password(length=12):
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    return "".join(random.choice(chars) for _ in range(length))

@frappe.whitelist()
def import_teams_csv(file_content):
    frappe.only_for("System Manager")
    
    f = StringIO(file_content)
    reader = csv.DictReader(f)
    for row in reader:
        team_name = row.get("Name your Team", "").strip()
        if not team_name:
            continue
        
        # Extract Faculty info
        faculty = None
        for i in range(1, 4):
            if row.get(f"Team Member {i} - Type", "").strip().lower() == "faculty":
                faculty_email = row.get(f"Tema Member {i} - Email", row.get(f"Team Member {i} - Email", "")).strip().lower()
                if faculty_email:
                    # Find or create faculty
                    if not frappe.db.exists("Faculty", {"email": faculty_email}):
                        faculty_doc = frappe.get_doc({
                            "doctype": "Faculty",
                            "faculty_name": row.get(f"Team Member {i} - Name ", "").strip(),
                            "email": faculty_email,
                            "institution": row.get(f"Team Member {i}  - Affiliation ", "").strip()
                        })
                        faculty_doc.insert(ignore_permissions=True)
                        faculty = faculty_doc.name
                    else:
                        faculty = frappe.db.get_value("Faculty", {"email": faculty_email}, "name")
                break

        if not frappe.db.exists("Hackathon Team", {"team_name": team_name}):
            doc = frappe.get_doc({
                "doctype": "Hackathon Team",
                "team_name": team_name,
                "institution": row.get("Institute", "").strip(),
                "problem_statement_area": row.get("Problem Statement Area", "").strip(),
                "valid_composition": 1 if faculty else 0,
                "faculty": faculty,
                "member_1_name": row.get("Team Member 1 - Name ", "").strip(),
                "member_1_email": row.get("Tema Member 1 - Email", row.get("Team Member 1 - Email", "")).strip(),
                "member_1_type": row.get("Team Member 1 - Type", "").strip(),
                "member_2_name": row.get("Team Member 2 - Name ", "").strip(),
                "member_2_email": row.get("Team Member 2 - Email", "").strip(),
                "member_2_type": row.get("Team Member 2 - Type", "").strip(),
                "member_3_name": row.get("Team Member 3 - Name ", "").strip(),
                "member_3_email": row.get("Team Member 3 - Email", "").strip(),
                "member_3_type": row.get("Team Member 3 - Type", "").strip(),
            })
            doc.insert(ignore_permissions=True)
    
    frappe.db.commit()
    return "Import complete"

@frappe.whitelist()
def import_mentors_csv(file_content):
    frappe.only_for("System Manager")
    
    f = StringIO(file_content)
    reader = csv.DictReader(f)
    
    # We will save passwords in a note or return them
    creds = []
    
    for row in reader:
        email = row.get("Email Address", row.get("email", "")).strip().lower()
        if not email:
            continue
        
        if not frappe.db.exists("User", email):
            pwd = get_random_password()
            user = frappe.get_doc({
                "doctype": "User",
                "email": email,
                "first_name": row.get("Submitter Name", row.get("full_name", "")).strip(),
                "send_welcome_email": 0
            })
            user.insert(ignore_permissions=True)
            # Add Evaluator role
            user.add_roles("Evaluator")
            user.new_password = pwd
            user.save(ignore_permissions=True)
            creds.append(f"{email}: {pwd}")
    
    frappe.db.commit()
    return "Users imported successfully. Passwords:\n" + "\n".join(creds)
