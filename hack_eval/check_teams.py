import frappe

def run():
    teams = frappe.get_all("Hackathon Team", fields=["name", "mentor", "problem_statement_area"])
    for t in teams:
        print(f"{t.name}: Mentor = {t.mentor}, Track = {t.problem_statement_area}")
