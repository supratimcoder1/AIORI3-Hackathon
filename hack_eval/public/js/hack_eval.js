// AIORI-3 Global Desk Utilities

frappe.provide("hack_eval");

// 1. Route Guard: Prevent mentors from getting stranded on Admin Workspace
frappe.router.on('change', () => {
    let route = frappe.get_route();
    if (!route || !route.length) return;

    let is_hcc = (route[0] === 'hackathon-control-center') || 
                 (route[0] === 'Workspaces' && route[1] === 'Hackathon Control Center');

    if (is_hcc) {
        let is_admin = frappe.user_roles.includes('System Manager') || 
                       frappe.user_roles.includes('Hackathon Organizer') || 
                       frappe.session.user === 'Administrator';
        if (!is_admin) {
            frappe.show_alert({
                message: __('Redirecting to your Mentor Dashboard'),
                indicator: 'blue'
            }, 3);
            frappe.set_route('mentor-dashboard');
        }
    }
});

// 2. Global Breadcrumbs Guard: Ensure mentors always see Mentor Dashboard instead of Hackathon Control Center
if (frappe.breadcrumbs) {
    const orig_set_workspace = frappe.breadcrumbs.set_workspace;
    frappe.breadcrumbs.set_workspace = function(breadcrumbs) {
        orig_set_workspace.apply(this, arguments);
        let is_admin = frappe.user_roles.includes('System Manager') || 
                       frappe.user_roles.includes('Hackathon Organizer') || 
                       frappe.session.user === 'Administrator';
        if (!is_admin && breadcrumbs.workspace === 'Hackathon Control Center') {
            breadcrumbs.workspace = 'Mentor Dashboard';
        }
    };
}

// 3. Force Local Download on all Reports (Hide "Export in Background" and guarantee export_in_background=0)
function patch_export_utils() {
    if (frappe.report_utils && !frappe.report_utils._export_patched) {
        const orig_get_export_dialog = frappe.report_utils.get_export_dialog;
        if (orig_get_export_dialog) {
            frappe.report_utils.get_export_dialog = function(report_name, extra_fields, callback) {
                const wrapped_callback = function(values) {
                    if (values) {
                        values.export_in_background = 0;
                    }
                    if (callback) {
                        return callback(values);
                    }
                };

                const dialog = orig_get_export_dialog.call(this, report_name, extra_fields, wrapped_callback);
                if (dialog && dialog.fields_dict && dialog.fields_dict['export_in_background']) {
                    dialog.fields_dict['export_in_background'].df.hidden = 1;
                    dialog.set_value('export_in_background', 0);
                    dialog.fields_dict['export_in_background'].refresh();
                }

                if (dialog) {
                    const orig_get_values = dialog.get_values ? dialog.get_values.bind(dialog) : null;
                    if (orig_get_values) {
                        dialog.get_values = function() {
                            const vals = orig_get_values(...arguments);
                            if (vals) {
                                vals.export_in_background = 0;
                            }
                            return vals;
                        };
                    }
                }
                return dialog;
            };
            frappe.report_utils._export_patched = true;
        }
    }
}

function patch_open_url_post() {
    if (window.open_url_post && !window._orig_open_url_post) {
        window._orig_open_url_post = window.open_url_post;
        window.open_url_post = function(URL, PARAMS, new_window) {
            if (PARAMS && typeof PARAMS === 'object') {
                for (let k in PARAMS) {
                    if (PARAMS[k] === undefined) {
                        delete PARAMS[k];
                    } else if (k === 'export_in_background' && (PARAMS[k] === 'undefined' || !PARAMS[k])) {
                        PARAMS[k] = 0;
                    }
                }
            }
            return window._orig_open_url_post(URL, PARAMS, new_window);
        };
    }
}

$(document).ready(() => {
    patch_export_utils();
    patch_open_url_post();
});

frappe.router.on('change', () => {
    patch_export_utils();
    patch_open_url_post();
});

