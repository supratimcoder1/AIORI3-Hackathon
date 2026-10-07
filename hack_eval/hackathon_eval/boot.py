import frappe

def boot_session(bootinfo):
    """
    Ensure module_wise_workspaces only exposes workspaces that the current user
    actually has permission to access.
    This fixes Frappe's default behavior where breadcrumbs blindly pick the 0th
    workspace in a module (e.g. 'Hackathon Control Center') regardless of user roles,
    causing mentors to see inaccessible workspaces and get 403 Permission Denied.
    """
    if not bootinfo:
        return

    allowed_pages = getattr(bootinfo, "allowed_workspaces", None) or []
    allowed_names = {p.get("name") for p in allowed_pages if isinstance(p, dict)}

    module_workspaces = getattr(bootinfo, "module_wise_workspaces", None)
    if module_workspaces:
        for module, workspaces in list(module_workspaces.items()):
            permitted = [ws for ws in workspaces if ws in allowed_names]
            if permitted:
                bootinfo.module_wise_workspaces[module] = permitted
            elif allowed_names:
                bootinfo.module_wise_workspaces[module] = []
