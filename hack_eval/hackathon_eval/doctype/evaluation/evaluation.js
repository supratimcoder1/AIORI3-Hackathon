frappe.ui.form.on('Evaluation', {
    refresh: function(frm) {
        var is_admin = frappe.user_roles.includes('System Manager') || 
                       frappe.user_roles.includes('Hackathon Organizer') || 
                       frappe.session.user === 'Administrator';

        // Ensure breadcrumb points to the user's accessible workspace
        var target_workspace = is_admin ? "Hackathon Control Center" : "Mentor Dashboard";
        frappe.breadcrumbs.add({
            module: "Hackathon Eval",
            doctype: "Evaluation",
            type: "DocType",
            workspace: target_workspace
        });

        // Disallow adding or deleting rows manually to prevent data corruption
        frm.set_df_property('scores', 'cannot_add_rows', 1);
        frm.set_df_property('scores', 'cannot_delete_rows', 1);

        // Hide settings gear from grid header
        setTimeout(() => {
            frm.fields_dict.scores.grid.wrapper.find('.grid-settings, .grid-custom-setting, .configure-columns').hide();
        }, 200);

        // Check Round Status for Level Gating
        if (frm.doc.round && !frm.is_new()) {
            frappe.db.get_value('Hackathon Round', frm.doc.round, 'status', function(r) {
                var round_status = r ? r.status : 'Closed';
                if (!is_admin) {
                    if (round_status !== 'Open') {
                        frm.disable_save();
                        frm.set_read_only();
                        frm.dashboard.set_headline_alert(
                            __('Scoring Locked: Round {0} is currently {1}. Mentors cannot edit evaluations.', [frm.doc.round, round_status]),
                            'red'
                        );
                    } else if (frm.doc.status === 'Submitted') {
                        frm.disable_save();
                        frm.set_read_only();
                        frm.dashboard.set_headline_alert(
                            __('Evaluation Submitted: This evaluation is locked. Only Admins can modify submitted scores.'),
                            'green'
                        );
                    }
                }
            });
        }

        // Action button to Submit Evaluation
        if (!frm.is_new() && frm.doc.status !== 'Submitted') {
            frm.add_custom_button(__('Submit Evaluation'), function() {
                frappe.confirm(__('Are you sure you want to finalize and submit these scores?'), function() {
                    frm.set_value('status', 'Submitted');
                    frm.set_value('submitted_on', frappe.datetime.now_datetime());
                    frm.save();
                });
            }).addClass('btn-primary');
        }

        // Admin override button: Reopen / Mark as Draft
        if (is_admin && frm.doc.status === 'Submitted') {
            frm.add_custom_button(__('Re-open for Mentor (Mark Draft)'), function() {
                frm.set_value('status', 'Draft');
                frm.save();
            });
        }
    },
    
    round: function(frm) {
        populate_criteria(frm);
    }
});

frappe.ui.form.on('Evaluation Score', {
    form_render: function(frm, cdt, cdn) {
        setTimeout(() => {
            let grid_row = frm.fields_dict.scores.grid.grid_rows_by_docname[cdn];
            if (grid_row && grid_row.wrapper) {
                // Hide Frappe's native action buttons in the child row form
                grid_row.wrapper.find('.grid-delete-row, .grid-insert-row, .grid-insert-row-below, .grid-duplicate-row, .grid-move-row, .grid-append-row').hide();
                
                let $heading = grid_row.wrapper.find('.grid-form-heading');
                let $del_btn = $heading.find('.grid-delete-row');
                
                if ($heading.find('.btn-save-row').length === 0) {
                    $('<button class="btn btn-xs btn-primary btn-save-row" style="margin-right: 5px; margin-top: -3px;">Save</button>')
                        .insertBefore($del_btn)
                        .on('click', function(e) {
                            e.preventDefault();
                            e.stopPropagation();
                            grid_row.toggle_view(false);
                            return false;
                        });
                }
            }
        }, 100);
    },
    score: function(frm, cdt, cdn) {
        var row = locals[cdt][cdn];
        if (row.score > row.max_score) {
            frappe.msgprint(__('Score cannot exceed max score of {0}', [row.max_score]));
            frappe.model.set_value(cdt, cdn, 'score', row.max_score);
        } else if (row.score < 0) {
            frappe.msgprint(__('Score cannot be negative.'));
            frappe.model.set_value(cdt, cdn, 'score', 0);
        }
        calculate_total(frm);
    }
});

function calculate_total(frm) {
    var total = 0.0;
    (frm.doc.scores || []).forEach(function(row) {
        total += flt(row.score);
    });
    frm.set_value('total_score', total);
}

function populate_criteria(frm) {
    if (frm.doc.round && (!frm.doc.scores || frm.doc.scores.length === 0)) {
        frappe.call({
            method: 'frappe.client.get',
            args: {
                doctype: 'Hackathon Round',
                name: frm.doc.round
            },
            callback: function(r) {
                if (r.message && r.message.criteria) {
                    frm.clear_table('scores');
                    r.message.criteria.forEach(function(c) {
                        var row = frm.add_child('scores');
                        row.criterion = c.criterion;
                        row.max_score = flt(c.max_score || 10.0);
                        row.score = 0.0;
                    });
                    frm.refresh_field('scores');
                    calculate_total(frm);
                }
            }
        });
    }
}
