import frappe

def run():
    if not frappe.db.exists('Client Script', {'dt': 'User', 'module': 'Hackathon Eval'}):
        doc = frappe.get_doc({
            'doctype': 'Client Script',
            'dt': 'User',
            'module': 'Hackathon Eval',
            'script': '''
frappe.ui.form.on('User', {
    refresh(frm) {
        if (!frm.is_new() && (frappe.user_roles.includes('System Manager') || frappe.user_roles.includes('Hackathon Organizer'))) {
            frm.add_custom_button(__('Change Mentor Password'), () => {
                frappe.prompt([
                    {
                        fieldname: 'new_password',
                        fieldtype: 'Password',
                        label: 'New Password',
                        reqd: 1
                    }
                ], (values) => {
                    frappe.call({
                        method: 'hack_eval.hackathon_eval.api.update_mentor_password',
                        args: {
                            user_email: frm.doc.name,
                            new_password: values.new_password
                        },
                        callback: function(r) {
                            if (!r.exc) {
                                frappe.msgprint(__('Password updated successfully'));
                            }
                        }
                    });
                }, __('Change Mentor Password'), __('Update'));
            }, __('Actions'));
        }
    }
});
'''
        })
        doc.insert(ignore_permissions=True)
        frappe.db.commit()
        print("Client script created.")
