import frappe

def run():
    # 1. Tracks
    tracks = [
        "Internet Measurement",
        "Cyber Security",
        "Cloud Computing & IOT",
        "6G & Future Networks",
        "Smart Cities"
    ]

    # 2. Create 4 Mentors via Mentor Profile
    mentors_data = [
        {"first_name": "Alice", "last_name": "Mentor", "email": "alice.mentor@example.com", "track": tracks[0]},
        {"first_name": "Bob", "last_name": "Mentor", "email": "bob.mentor@example.com", "track": tracks[1]},
        {"first_name": "Charlie", "last_name": "Mentor", "email": "charlie.mentor@example.com", "track": tracks[2]},
        {"first_name": "Diana", "last_name": "Mentor", "email": "diana.mentor@example.com", "track": tracks[3]}
    ]

    mentor_users = []
    for m in mentors_data:
        existing = frappe.db.get_value("Mentor Profile", {"email": m["email"]}, "name")
        if not existing:
            doc = frappe.get_doc({
                "doctype": "Mentor Profile",
                "first_name": m["first_name"],
                "last_name": m["last_name"],
                "email": m["email"],
                "mentor_role": "AIORI-3 Mentor",
                "track": m["track"],
                "status": "Active"
            })
            doc.insert(ignore_permissions=True)
            print(f"Created Mentor Profile: {m['email']}")
        mentor_users.append(m["email"])  # Wait, Mentor Profile creates a User with name = email, so mentor_users should be email, since the Hackathon Team's 'mentor' field is a Link to 'User'. Let's verify 'mentor' link type.

    # 3. Create 2 Faculty records
    faculties = [
        {"faculty_name": "Dr. Smith", "email": "smith.faculty@example.com", "institution": "Tech University", "contact_number": "1112223333"},
        {"faculty_name": "Dr. Jones", "email": "jones.faculty@example.com", "institution": "Science College", "contact_number": "4445556666"}
    ]

    faculty_names = []
    for f in faculties:
        existing_name = frappe.db.get_value("Faculty", {"email": f["email"]}, "name")
        if not existing_name:
            doc = frappe.get_doc({
                "doctype": "Faculty",
                "faculty_name": f["faculty_name"],
                "email": f["email"],
                "institution": f["institution"],
                "contact_number": f["contact_number"]
            })
            doc.insert(ignore_permissions=True)
            existing_name = doc.name
            print(f"Created Faculty: {existing_name} for {f['email']}")
        faculty_names.append(existing_name)

    # 4. Create 10 Teams
    for i in range(1, 11):
        team_name = f"Hack Team {i:02d}"
        track = tracks[i % 5]
        faculty = faculty_names[i % 2]
        mentor = mentor_users[i % 4]
        
        if not frappe.db.exists("Hackathon Team", team_name):
            doc = frappe.get_doc({
                "doctype": "Hackathon Team",
                "team_name": team_name,
                "institution": f"Institute {i}",
                "problem_statement_area": track,
                "faculty": faculty,
                "mentor": mentor,
                "member_1_name": f"Student A{i}",
                "member_1_type": "Student",
                "member_1_email": f"studenta{i}@example.com",
                "member_2_name": f"Student B{i}",
                "member_2_type": "Student",
                "member_2_email": f"studentb{i}@example.com",
                "member_3_name": f"Faculty C{i}",
                "member_3_type": "Faculty",
                "member_3_email": "faculty@example.com"
            })
            doc.insert(ignore_permissions=True)
            print(f"Created Team: {team_name}")
        else:
            print(f"Team exists: {team_name}")

    frappe.db.commit()
    print("Mock data generation complete!")
