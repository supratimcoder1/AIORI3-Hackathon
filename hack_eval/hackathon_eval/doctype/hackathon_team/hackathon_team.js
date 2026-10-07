// Copyright (c) 2026, AIORI and contributors
// For license information, please see license.txt

frappe.ui.form.on("Hackathon Team", {
    refresh(frm) {
        if (!frm.is_new() && frm.doc.status !== "Eliminated" && (frappe.user_roles.includes("System Manager") || frappe.user_roles.includes("Hackathon Organizer"))) {
            frm.add_custom_button(__("Kill Team"), () => {
                frappe.prompt([
                    {
                        fieldname: 'reason',
                        fieldtype: 'Small Text',
                        label: 'Reason for Disqualification',
                        reqd: 1
                    }
                ], (values) => {
                    frappe.call({
                        method: 'hack_eval.hackathon_eval.api.kill_team',
                        args: { 
                            team_name: frm.doc.name,
                            reason: values.reason
                        },
                        callback: (r) => { 
                            if (!r.exc) frm.reload_doc(); 
                        }
                    });
                }, __("Kill Team"), __("Eliminate"));
            }).addClass("btn-danger");
        }

        if (!frm.is_new() && (frappe.user_roles.includes("System Manager") || frappe.user_roles.includes("Hackathon Organizer") || frappe.user_roles.includes("Chief Mentor"))) {
            frm.add_custom_button(__("View Scorecard"), () => {
                frappe.set_route('query-report', 'Team Scorecard', { 'team': frm.doc.name });
            });
        }
    }
});
