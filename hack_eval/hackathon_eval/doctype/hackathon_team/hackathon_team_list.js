frappe.listview_settings['Hackathon Team'] = {
    hide_name_filter: true,
    hide_name_column: true,
    add_fields: ['team_code', 'status', 'current_level', 'cumulative_score', 'valid_composition', 'problem_statement_area', 'evaluation_decision'],
    
    onload(listview) {
        frappe.listview_settings['Hackathon Team'].patch_listview(listview);
        frappe.listview_settings['Hackathon Team'].add_bulk_actions(listview);
    },

    before_render() {
        const listview = frappe.get_list_view('Hackathon Team');
        if (listview) {
            frappe.listview_settings['Hackathon Team'].patch_listview(listview);
            frappe.listview_settings['Hackathon Team'].add_bulk_actions(listview);
        }
    },

    add_bulk_actions(listview) {
        var is_admin = frappe.user_roles.includes('System Manager') || 
                       frappe.user_roles.includes('Hackathon Organizer') || 
                       frappe.session.user === 'Administrator';

        if (is_admin && !listview._level_up_actions_added) {
            listview._level_up_actions_added = true;
            listview.page.add_action_item(__('Mark as Level Up'), function() {
                let checked_items = listview.get_checked_items();
                if (!checked_items.length) {
                    frappe.msgprint(__('Please select at least one team.'));
                    return;
                }
                let names = checked_items.map(d => d.name);
                frappe.call({
                    method: 'hack_eval.hackathon_eval.evaluation_logic.bulk_set_team_evaluation_decision',
                    args: {
                        team_names: names,
                        decision: 'Level Up'
                    },
                    freeze: true,
                    freeze_message: __('Marking teams as Level Up...'),
                    callback: function(r) {
                        if (!r.exc) {
                            frappe.show_alert({
                                message: __('{0} teams marked as Level Up', [names.length]),
                                indicator: 'green'
                            }, 4);
                            listview.refresh();
                        }
                    }
                });
            });

            listview.page.add_action_item(__('Clear Level Up'), function() {
                let checked_items = listview.get_checked_items();
                if (!checked_items.length) {
                    frappe.msgprint(__('Please select at least one team.'));
                    return;
                }
                let names = checked_items.map(d => d.name);
                frappe.call({
                    method: 'hack_eval.hackathon_eval.evaluation_logic.bulk_set_team_evaluation_decision',
                    args: {
                        team_names: names,
                        decision: ''
                    },
                    freeze: true,
                    freeze_message: __('Clearing Level Up...'),
                    callback: function(r) {
                        if (!r.exc) {
                            frappe.show_alert({
                                message: __('Cleared Level Up for {0} teams', [names.length]),
                                indicator: 'blue'
                            }, 4);
                            listview.refresh();
                        }
                    }
                });
            });
        }
    },

    toggle_level_up(btn, e) {
        if (e) {
            e.preventDefault();
            e.stopPropagation();
        }
        let $btn = $(btn);
        let team_name = $btn.attr('data-team') || $btn.data('team');
        let current_decision = $btn.attr('data-decision');
        let new_decision = current_decision === 'Level Up' ? '' : 'Level Up';

        $btn.prop('disabled', true);

        frappe.call({
            method: 'hack_eval.hackathon_eval.evaluation_logic.set_team_evaluation_decision',
            args: {
                team_name: team_name,
                decision: new_decision
            },
            callback: function(r) {
                $btn.prop('disabled', false);
                if (!r.exc) {
                    if (new_decision === 'Level Up') {
                        $btn.attr('data-decision', 'Level Up')
                            .removeClass('btn-default')
                            .addClass('btn-success')
                            .css({
                                'background-color': '#28a745',
                                'border-color': '#28a745',
                                'color': '#fff'
                            })
                            .html('<i class="fa fa-check" style="margin-right: 3px;"></i> Levelled Up');

                        frappe.show_alert({
                            message: __('Team {0} marked as Level Up (Saved)', [team_name]),
                            indicator: 'green'
                        }, 3);
                    } else {
                        $btn.attr('data-decision', '')
                            .removeClass('btn-success')
                            .addClass('btn-default')
                            .css({
                                'background-color': 'transparent',
                                'border-color': '#d1d8dd',
                                'color': '#495057'
                            })
                            .html('Level Up');

                        frappe.show_alert({
                            message: __('Level Up cleared for Team {0} (Saved)', [team_name]),
                            indicator: 'blue'
                        }, 3);
                    }
                }
            },
            error: function() {
                $btn.prop('disabled', false);
            }
        });
        return false;
    },

    patch_listview(listview) {
        if (!listview || !listview.columns) return;

        if (!listview.list_view_settings) {
            listview.list_view_settings = {};
        }
        listview.list_view_settings.total_fields = 12;

        // Ensure user settings don't drop any of the required fields
        let user_settings = frappe.get_user_settings('Hackathon Team');
        if (user_settings && user_settings.fields) {
            ['team_code', 'problem_statement_area', 'cumulative_score', 'evaluation_decision'].forEach(f => {
                if (!user_settings.fields.includes(f)) {
                    user_settings.fields.push(f);
                }
            });
        }

        const ensure_column = (fieldname, label, fieldtype, after_fieldname) => {
            const exists = listview.columns.some(col => col.df && col.df.fieldname === fieldname);
            if (!exists) {
                const df = frappe.meta.get_docfield('Hackathon Team', fieldname) || {
                    fieldname: fieldname,
                    label: __(label),
                    fieldtype: fieldtype
                };
                const new_col = { type: 'Field', df: df };
                
                let target_idx = -1;
                if (after_fieldname) {
                    target_idx = listview.columns.findIndex(col => 
                        (col.type === after_fieldname) || (col.df && col.df.fieldname === after_fieldname)
                    );
                }
                if (target_idx !== -1) {
                    listview.columns.splice(target_idx + 1, 0, new_col);
                } else {
                    listview.columns.push(new_col);
                }
            }
        };

        ensure_column('team_code', 'Team Code', 'Data', 'Status');
        ensure_column('problem_statement_area', 'Problem Statement Area', 'Data', 'team_code');
        ensure_column('cumulative_score', 'Average Score', 'Float', 'problem_statement_area');
        ensure_column('evaluation_decision', 'Evaluate', 'Select', 'cumulative_score');

        if (listview.$result && listview.$result.find('.list-row-head').length) {
            listview.render_header(true);
        }
    },

    formatters: {
        evaluation_decision(val, df, doc) {
            var is_admin = frappe.user_roles.includes('System Manager') || 
                           frappe.user_roles.includes('Hackathon Organizer') || 
                           frappe.session.user === 'Administrator';

            if (!is_admin) {
                if (val === 'Level Up') return `<span class="indicator-pill green bold">Levelled Up</span>`;
                return `<span class="text-muted">-</span>`;
            }

            if (val === 'Level Up') {
                return `
                    <div class="eval-btn-wrapper" onmousedown="event.stopPropagation();" onclick="event.stopPropagation();" style="display:inline-block;">
                        <button type="button" 
                                class="btn btn-xs btn-success btn-level-up" 
                                data-team="${frappe.utils.escape_html(doc.name)}" 
                                data-decision="Level Up"
                                onclick="frappe.listview_settings['Hackathon Team'].toggle_level_up(this, event);" 
                                onmousedown="event.stopPropagation();" 
                                style="height: 24px; padding: 1px 10px; font-size: 11px; font-weight: 600; border-radius: 4px; background-color: #28a745; border-color: #28a745; color: #fff; cursor: pointer;">
                            <i class="fa fa-check" style="margin-right: 3px;"></i> Levelled Up
                        </button>
                    </div>
                `;
            }

            return `
                <div class="eval-btn-wrapper" onmousedown="event.stopPropagation();" onclick="event.stopPropagation();" style="display:inline-block;">
                    <button type="button" 
                            class="btn btn-xs btn-default btn-level-up" 
                            data-team="${frappe.utils.escape_html(doc.name)}" 
                            data-decision=""
                            onclick="frappe.listview_settings['Hackathon Team'].toggle_level_up(this, event);" 
                            onmousedown="event.stopPropagation();" 
                            style="height: 24px; padding: 1px 10px; font-size: 11px; font-weight: 600; border-radius: 4px; border: 1px solid #d1d8dd; color: #495057; cursor: pointer; background-color: transparent;">
                        Level Up
                    </button>
                </div>
            `;
        },
        cumulative_score(val, df, doc) {
            let score = flt(val);
            return `<span class="bold" style="color: ${score > 0 ? '#2490ef' : '#888'}; font-size: 12px;">${score.toFixed(3)}</span>`;
        }
    },

    get_indicator(doc) {
        if (doc.valid_composition === 0) return [__("Invalid Comp"), "red", "valid_composition,=,0"];
        if (doc.status === "Eliminated") return [__("Eliminated"), "red", "status,=,Eliminated"];
        if (doc.status === "Active") return [__("Active"), "green", "status,=,Active"];
        if (doc.status === "Finalist") return [__("Finalist"), "orange", "status,=,Finalist"];
        if (doc.status === "Winner") return [__("Winner"), "blue", "status,=,Winner"];
    }
};
