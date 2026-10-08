// Copyright (c) 2026, AIORI and contributors
// For license information, please see license.txt

frappe.ui.form.on('Hackathon Round', {
    refresh(frm) {
        var is_admin = frappe.user_roles.includes('System Manager') || 
                       frappe.user_roles.includes('Hackathon Organizer') || 
                       frappe.session.user === 'Administrator';

        if (frm.is_new() || !is_admin) return;
        
        // State 1: Not Started
        if (frm.doc.status === 'Not Started') {
            frm.add_custom_button(__('Open Round'), () => {
                frappe.confirm(__('Opening Round {0} will provision evaluation forms for all eligible teams and allow mentors to begin grading. Proceed?', [frm.doc.round_name]), () => {
                    frappe.call({
                        method: 'hack_eval.hackathon_eval.evaluation_logic.open_round',
                        args: { round_name: frm.doc.name },
                        callback: (r) => { 
                            if (!r.exc) {
                                frappe.msgprint(r.message || __('Round Opened'));
                                frm.reload_doc(); 
                            }
                        }
                    });
                });
            }).addClass('btn-primary');
        }
        
        var reset_handler = () => {
            frappe.prompt([
                {
                    fieldname: 'reset_level',
                    fieldtype: 'Select',
                    label: __('Wipe Options'),
                    options: 'Revert completely to starting (Wipe all scores)\nRevert to Level 1 (Wipe L2 & L3 scores)\nRevert to Level 2 (Wipe L3 scores)',
                    reqd: 1,
                    default: 'Revert completely to starting (Wipe all scores)'
                }
            ], (values) => {
                frappe.confirm(__('WARNING: This will reset the round and wipe scores as selected. Proceed?'), () => {
                    frappe.call({
                        method: 'hack_eval.hackathon_eval.evaluation_logic.reset_round',
                        args: { 
                            round_name: frm.doc.name,
                            reset_level: values.reset_level
                        },
                        callback: (r) => { 
                            if (!r.exc) {
                                frappe.msgprint(r.message || __('Round Reset'));
                                frm.reload_doc(); 
                            }
                        }
                    });
                });
            }, __('Reset Round'), __('Reset'));
        };

        // State 2: Open
        if (frm.doc.status === 'Open') {
            frm.add_custom_button(__('Refresh Live Leaderboard'), () => {
                frappe.call({
                    method: 'hack_eval.hackathon_eval.evaluation_logic.recompute_round_results',
                    args: { round_name: frm.doc.name },
                    callback: (r) => { 
                        if (!r.exc) {
                            frappe.msgprint(__('Leaderboard snapshot refreshed with live scores!'));
                            frm.reload_doc(); 
                        }
                    }
                });
            }).addClass('btn-info');
            
            frm.add_custom_button(__('Close Round'), () => {
                frappe.confirm(__('Closing Round {0} will freeze mentor scoring. Proceed?', [frm.doc.round_name]), () => {
                    frappe.call({
                        method: 'hack_eval.hackathon_eval.evaluation_logic.close_round',
                        args: { round_name: frm.doc.name, force: 0 },
                        callback: (r) => { 
                            if (!r.exc) {
                                frappe.msgprint(r.message || __('Round Closed'));
                                frm.reload_doc(); 
                            }
                        }
                    });
                });
            }).addClass('btn-danger');

            frm.add_custom_button(__('Force Close (Ignore Pending)'), () => {
                frappe.confirm(__('Force close this round regardless of pending mentor evaluations?'), () => {
                    frappe.call({
                        method: 'hack_eval.hackathon_eval.evaluation_logic.close_round',
                        args: { round_name: frm.doc.name, force: 1 },
                        callback: (r) => { 
                            if (!r.exc) {
                                frappe.msgprint(r.message || __('Round Force Closed'));
                                frm.reload_doc(); 
                            }
                        }
                    });
                });
            });

            frm.add_custom_button(__('Reset to Not Started'), reset_handler).addClass('btn-danger');
        }
        
        // State 3: Closed
        if (frm.doc.status === 'Closed') {
            frm.add_custom_button(__('Reset to Not Started'), reset_handler).addClass('btn-danger');

            frm.add_custom_button(__('Reopen Round'), () => {
                frappe.confirm(__('Reopen Round {0} to allow mentors to continue scoring?', [frm.doc.round_name]), () => {
                    frappe.call({
                        method: 'hack_eval.hackathon_eval.evaluation_logic.reopen_round',
                        args: { round_name: frm.doc.name },
                        callback: (r) => { 
                            if (!r.exc) {
                                frappe.msgprint(r.message || __('Round Reopened'));
                                frm.reload_doc(); 
                            }
                        }
                    });
                });
            }).addClass('btn-warning');

            frm.add_custom_button(__('Recompute Results'), () => {
                frappe.call({
                    method: 'hack_eval.hackathon_eval.evaluation_logic.recompute_round_results',
                    args: { round_name: frm.doc.name },
                    callback: (r) => { 
                        if (!r.exc) {
                            frappe.msgprint(r.message || __('Results Recomputed'));
                            frm.reload_doc(); 
                        }
                    }
                });
            });
            
            frm.add_custom_button(__('Apply Cutoff & Advance'), () => {
                frappe.prompt([
                    {
                        fieldname: 'advance_count',
                        fieldtype: 'Int',
                        label: __('Top N Teams to Advance'),
                        default: frm.doc.advance_count || 5,
                        reqd: 1
                    }
                ], (values) => {
                    frappe.call({
                        method: 'hack_eval.hackathon_eval.evaluation_logic.promote_round',
                        args: { 
                            round_name: frm.doc.name,
                            advance_count: values.advance_count
                        },
                        callback: (r) => { 
                            if (!r.exc) {
                                frappe.msgprint(r.message || __('Cutoff Applied Successfully'));
                                frm.reload_doc(); 
                            }
                        }
                    });
                }, __('Set Advancement Cutoff (N)'), __('Apply Cutoff'));
            }).addClass('btn-success');
        }
    }
});
