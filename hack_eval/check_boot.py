import frappe

def run():
    frappe.set_user("Administrator")
    # Check custom docperms
    custom_perms = frappe.get_all("Custom DocPerm", filters={"parent": "Hackathon Team"}, fields=["*"])
    print("ALL CUSTOM DOCPERMS FOR HACKATHON TEAM:")
    for cp in custom_perms:
        print(cp)

    # Let's check what bootinfo / can_create has:
    from frappe.boot import get_bootinfo
    boot = get_bootinfo()
    print("USER CAN CREATE HACKATHON TEAM?", "Hackathon Team" in boot.user.can_create)
    print("USER CAN IMPORT HACKATHON TEAM?", "Hackathon Team" in boot.user.can_import)
    print("USER CAN READ HACKATHON TEAM?", "Hackathon Team" in boot.user.can_read)
