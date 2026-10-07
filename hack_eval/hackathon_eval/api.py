import frappe

@frappe.whitelist()
def kill_team(team_name, reason):
    frappe.only_for(["System Manager", "Hackathon Organizer"])
    team = frappe.get_doc("Hackathon Team", team_name)
    team.status = "Eliminated"
    team.add_comment("Comment", text=f"Team eliminated by {frappe.session.user}. Reason: {reason}")
    team.save(ignore_permissions=True)
    frappe.db.commit()
    return "Success"

@frappe.whitelist()
def update_mentor_password(user_email, new_password):
    frappe.only_for(["System Manager", "Hackathon Organizer"])
    if not frappe.db.exists("User", user_email):
        frappe.throw("User not found.")
        
    from frappe.utils.password import update_password
    update_password(user_email, new_password)
    frappe.db.commit()
    return "Password updated successfully"

@frappe.whitelist()
def fix_mentors():
    frappe.only_for(["System Manager", "Administrator"])
    
    # 1. Delete the 15 manually created users that don't have mentor profiles
    generated_users = frappe.get_all('User', filters={'email': ['like', 'mentor_%@aiori.local']}, pluck='name')
    for u in generated_users:
        try:
            frappe.delete_doc('User', u, force=1, ignore_permissions=True)
        except Exception:
            pass
            
    # 2. Delete existing Mentor Profiles and their associated Users
    old_profiles = frappe.get_all('Mentor Profile', pluck='name')
    for p in old_profiles:
        doc = frappe.get_doc('Mentor Profile', p)
        email = doc.email
        frappe.delete_doc('Mentor Profile', p, force=1, ignore_permissions=True)
        # on_trash just disables the user, let's actually delete the user to be clean
        if frappe.db.exists('User', email):
            try:
                frappe.delete_doc('User', email, force=1, ignore_permissions=True)
            except Exception:
                pass
                
    # 3. Create 15 new Mentor Profiles
    tracks = [
        'Internet Measurement',
        'Cyber Security',
        'Cloud Computing & IOT',
        '6G & Future Networks',
        'Smart Cities'
    ]

    mentors_created = []

    for t_idx, track in enumerate(tracks):
        for i in range(1, 4):
            email = f"mentor_{t_idx+1}_{i}@aiori.local"
            first_name = f"Mentor {i}"
            last_name = track
            password = f"Mentor@{2026+t_idx+i}"

            mp = frappe.new_doc("Mentor Profile")
            mp.first_name = first_name
            mp.last_name = last_name
            mp.email = email
            mp.contact_number = f"1234500{t_idx}{i}"
            mp.mentor_role = "AIORI-3 Mentor"
            mp.status = "Active"
            # In on_update, it natively creates the User and sets password to Password123
            mp.insert(ignore_permissions=True)
            
            # Now set the custom password securely using canonical Frappe API
            from frappe.utils.password import update_password
            update_password(email, password)
            
            mentors_created.append({
                "email": email,
                "password": password,
                "track": track
            })

    frappe.db.commit()
    return "Fix complete."

@frappe.whitelist()
def clean_mentor_names():
    frappe.only_for(["System Manager", "Administrator"])
    profiles = frappe.get_all('Mentor Profile')
    for p in profiles:
        doc = frappe.get_doc('Mentor Profile', p.name)
        dirty = False
        if doc.last_name and ('&amp;' in doc.last_name or '&' in doc.last_name):
            doc.last_name = doc.last_name.replace('&amp;', 'and').replace('&', 'and')
            dirty = True
        
        if dirty:
            doc.save(ignore_permissions=True)
            
    frappe.db.commit()
    return "Names cleaned."

@frappe.whitelist()
def align_fields():
    frappe.only_for(["System Manager", "Administrator"])
    doctype = frappe.get_doc("DocType", "Hackathon Team")
    
    label_map = {
        "team_name": "Name your Team",
        "institution": "Institute",
        "member_1_name": "Team Member 1 - Name ",
        "member_1_affiliation": "Team Member 1  - Affiliation ",
        "member_1_contact": "Team Member 1 - Contact Number",
        "member_1_email": "Tema Member 1 - Email",
        "member_1_type": "Team Member 1 - Type",
        
        "member_2_name": "Team Member 2 - Name ",
        "member_2_affiliation": "Team Member 2  - Affiliation ",
        "member_2_contact": "Team Member 2 - Contact Number",
        "member_2_email": "Team Member 2 - Email",
        "member_2_type": "Team Member 2 - Type",
        
        "member_3_name": "Team Member 3 - Name ",
        "member_3_affiliation": "Team Member 3  - Affiliation ",
        "member_3_contact": "Team Member 3 - Contact Number",
        "member_3_email": "Team Member 3 - Email",
        "member_3_type": "Team Member 3 - Type",
    }

    dirty = False
    for row in doctype.fields:
        if row.fieldname in label_map and row.label != label_map[row.fieldname]:
            row.label = label_map[row.fieldname]
            dirty = True
            
        # Also ensure score fields are not importable by accident
        if row.fieldname in ["level1_score", "level2_score", "level3_score", "cumulative_score"]:
            if not row.read_only:
                row.read_only = 1
                dirty = True

    missing_fields = [
        {"fieldname": "city", "fieldtype": "Data", "label": "City", "insert_after": "institution"},
        {"fieldname": "zone", "fieldtype": "Data", "label": "Zone", "insert_after": "city"},
        {"fieldname": "reason_for_problem_area", "fieldtype": "Small Text", "label": "Why have you selected the above Problem Area?", "insert_after": "problem_statement_area"},
        {"fieldname": "collaboration_plan", "fieldtype": "Small Text", "label": "How will you collaborate to solve the above problem in this area?", "insert_after": "reason_for_problem_area"}
    ]

    existing_fields = [f.fieldname for f in doctype.fields]

    for new_f in missing_fields:
        if new_f["fieldname"] not in existing_fields:
            idx = 0
            for i, f in enumerate(doctype.fields):
                if f.fieldname == new_f["insert_after"]:
                    idx = i + 1
                    break
            doctype.append("fields", {
                "fieldname": new_f["fieldname"],
                "fieldtype": new_f["fieldtype"],
                "label": new_f["label"]
            })
            field_doc = doctype.fields[-1]
            doctype.fields.pop()
            doctype.fields.insert(idx, field_doc)
            dirty = True

    if dirty:
        doctype.save(ignore_permissions=True)
        frappe.db.commit()
    return "Fields aligned."

@frappe.whitelist()
def fix_mentor_tracks():
    frappe.only_for(["System Manager", "Administrator"])
    profiles = frappe.get_all("Mentor Profile", fields=["name", "first_name", "last_name", "track"])
    
    # Map from "and" back to "&" if needed
    mapping = {
        "Cloud Computing and IOT": "Cloud Computing & IOT",
        "6G and Future Networks": "6G & Future Networks",
        "Internet Measurement": "Internet Measurement",
        "Cyber Security": "Cyber Security",
        "Smart Cities": "Smart Cities"
    }
    
    for p in profiles:
        doc = frappe.get_doc("Mentor Profile", p.name)
        # If track is empty, infer it from last_name
        if not doc.track:
            ln = doc.last_name or ""
            if ln in mapping:
                doc.track = mapping[ln]
            else:
                doc.track = ln
            doc.save(ignore_permissions=True)
            
    frappe.db.commit()
    return "Mentor tracks fixed."

@frappe.whitelist()
def fix_tracks_sql():
    frappe.only_for(["System Manager", "Administrator"])
    mapping = {
        "Cloud Computing and IOT": "Cloud Computing & IOT",
        "6G and Future Networks": "6G & Future Networks",
        "Internet Measurement": "Internet Measurement",
        "Cyber Security": "Cyber Security",
        "Smart Cities": "Smart Cities"
    }
    for k, v in mapping.items():
        frappe.db.sql("UPDATE `tabMentor Profile` SET track=%s WHERE last_name=%s", (v, k))
    frappe.db.commit()
    return "Done"

@frappe.whitelist()
def force_reprovision_evals():
    frappe.only_for(["System Manager", "Administrator"])
    # Delete existing Pending evaluations just in case
    frappe.db.sql("DELETE FROM `tabEvaluation` WHERE status='Pending'")
    
    round_doc = frappe.get_doc("Hackathon Round", "Level 1")
    round_doc.status = "Closed"
    round_doc.save(ignore_permissions=True)
    frappe.db.commit()
    
    from hack_eval.hackathon_eval.evaluation_logic import open_round
    return open_round("Level 1")