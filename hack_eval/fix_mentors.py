import frappe
from frappe.utils.password import update_password

def run():
    # 1. Create 5th mentor for Smart Cities
    email = "eve.mentor@example.com"
    if not frappe.db.exists("Mentor Profile", email):
        doc = frappe.get_doc({
            "doctype": "Mentor Profile",
            "first_name": "Eve",
            "last_name": "Mentor",
            "email": email,
            "mentor_role": "AIORI-3 Mentor",
            "track": "Smart Cities",
            "status": "Active"
        })
        doc.insert(ignore_permissions=True)
    
    frappe.db.commit()

    # Find the teams that are in Smart Cities and assign Eve to them if not assigned properly
    teams = frappe.get_all("Hackathon Team", filters={"problem_statement_area": "Smart Cities"})
    for t in teams:
        team_doc = frappe.get_doc("Hackathon Team", t.name)
        if team_doc.mentor != email:
            team_doc.mentor = email
            team_doc.save(ignore_permissions=True)
            
            # Also update the evaluation evaluator
            round_name = frappe.db.get_value("Hackathon Round", {"round_number": 1}, "name")
            evals = frappe.get_all("Evaluation", filters={"team": t.name, "round": round_name})
            for ev in evals:
                ev_doc = frappe.get_doc("Evaluation", ev.name)
                ev_doc.evaluator = email
                ev_doc.save(ignore_permissions=True)
    
    frappe.db.commit()

    # Reset passwords for all 5 mentors using the correct Frappe API
    mentor_emails = [
        "alice.mentor@example.com",
        "bob.mentor@example.com",
        "charlie.mentor@example.com",
        "diana.mentor@example.com",
        "eve.mentor@example.com"
    ]
    
    for email in mentor_emails:
        if frappe.db.exists("User", email):
            update_password(user=email, pwd="Password123")
    
    frappe.db.commit()
