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
            if (frm.fields_dict.scores && frm.fields_dict.scores.grid && frm.fields_dict.scores.grid.wrapper) {
                frm.fields_dict.scores.grid.wrapper.find('.grid-settings, .grid-custom-setting, .configure-columns').hide();
            }
        }, 200);

        // Setup style to hide the pencil icon when locked
        if ($('style#hide-pencil-css').length === 0) {
            $('<style id="hide-pencil-css">.hide-pencil .grid-row-open { display: none !important; }</style>').appendTo('head');
        }
        
        // Default to not hiding pencil, unless locked below
        if (frm.fields_dict.scores && frm.fields_dict.scores.wrapper) {
            frm.fields_dict.scores.wrapper.removeClass('hide-pencil');
        }

        let evaluator_email = (frm.doc.evaluator || "").trim().toLowerCase();
        let session_email = (frappe.session.user || "").trim().toLowerCase();

        // Check Round Status for Level Gating
        if (frm.doc.round && !frm.is_new()) {
            frappe.db.get_value('Hackathon Round', frm.doc.round, 'status', function(r) {
                var round_status = (r && r.status) ? r.status : (typeof r === 'string' ? r : 'Closed');
                if (!is_admin) {
                    // Chief mentors can see everything, but can only edit their own.
                    if (evaluator_email !== session_email) {
                        frm.disable_save();
                        frm.set_read_only();
                        frm.page.clear_secondary_action();
                        if (frm.fields_dict.scores && frm.fields_dict.scores.wrapper) {
                            frm.fields_dict.scores.wrapper.addClass('hide-pencil');
                        }
                        frm.dashboard.set_headline_alert(
                            __('Read Only: You can view this evaluation, but you cannot edit scores assigned to another mentor.'),
                            'yellow'
                        );
                    } else if (round_status !== 'Open') {
                        frm.disable_save();
                        frm.set_read_only();
                        frm.page.clear_secondary_action();
                        if (frm.fields_dict.scores && frm.fields_dict.scores.wrapper) {
                            frm.fields_dict.scores.wrapper.addClass('hide-pencil');
                        }
                        frm.dashboard.set_headline_alert(
                            __('Scoring Locked: Round {0} is currently {1}. Mentors cannot edit evaluations.', [frm.doc.round, round_status]),
                            'red'
                        );
                    } else if (frm.doc.status === 'Submitted') {
                        frm.disable_save();
                        frm.set_read_only();
                        frm.page.clear_secondary_action();
                        if (frm.fields_dict.scores && frm.fields_dict.scores.wrapper) {
                            frm.fields_dict.scores.wrapper.addClass('hide-pencil');
                        }
                        frm.dashboard.set_headline_alert(
                            __('Evaluation Submitted: This evaluation is locked. Only Admins can modify submitted scores.'),
                            'green'
                        );
                    }
                }
            });
        }

        function setup_submit_button() {
            if (frm.is_new() || frm.doc.status === 'Submitted') {
                frm.page.clear_secondary_action();
                return;
            }

            // Only assigned mentor or Admin can submit
            if (!is_admin && evaluator_email && session_email && evaluator_email !== session_email) {
                frm.page.clear_secondary_action();
                return;
            }

            let submit_action = function() {
                frappe.confirm(__('Are you sure you want to finalize and submit these scores?'), function() {
                    frm.set_value('status', 'Submitted');
                    frm.set_value('submitted_on', frappe.datetime.now_datetime());
                    frm.save();
                });
            };

            // 1. Primary placement in Standard Actions (beside Save button)
            let $sec_btn = frm.page.set_secondary_action(__('Submit Evaluation'), submit_action);
            if ($sec_btn) {
                $sec_btn.removeClass('btn-default hide')
                        .addClass('btn-primary')
                        .css({'display': 'inline-flex', 'margin-right': '6px'});
            }

            // 2. Also register in custom actions & ensure unhidden
            frm.add_custom_button(__('Submit Evaluation'), submit_action);
            if (frm.page.custom_actions) {
                frm.page.custom_actions.removeClass('hide hidden-xs hidden-md');
            }
        }

        // Setup button immediately and on slight delay to handle async header redraws
        setup_submit_button();
        setTimeout(setup_submit_button, 150);

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
                    $('<button class="btn btn-xs btn-default btn-save-row" style="margin-right: 5px; margin-top: -3px;">Close</button>')
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
