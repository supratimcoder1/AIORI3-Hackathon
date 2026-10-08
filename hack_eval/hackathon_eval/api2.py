import frappe

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
        'Internet Measurements',
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
