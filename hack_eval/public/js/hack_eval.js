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

// 3. Force Local Download on all Reports (Hide "Export in Background")
frappe.router.on('change', () => {
    if (frappe.report_utils && !frappe.report_utils._export_patched) {
        const orig_get_export_dialog = frappe.report_utils.get_export_dialog;
        if (orig_get_export_dialog) {
            frappe.report_utils.get_export_dialog = function(report_name, extra_fields, callback) {
                const dialog = orig_get_export_dialog.apply(this, arguments);
                if (dialog.fields_dict && dialog.fields_dict['export_in_background']) {
                    dialog.fields_dict['export_in_background'].df.hidden = 1;
                    dialog.fields_dict['export_in_background'].df.default = 0;
                }
                return dialog;
            };
            frappe.report_utils._export_patched = true;
        }
    }
});
