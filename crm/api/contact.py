import frappe
from frappe import _


def validate(doc, method):
	update_deals_email_mobile_no(doc)


def update_deals_email_mobile_no(doc):
	linked_deals = frappe.get_all(
		"CRM Contacts",
		filters={"contact": doc.name, "is_primary": 1},
		fields=["parent"],
	)

	for linked_deal in linked_deals:
		deal = frappe.get_cached_doc("CRM Deal", linked_deal.parent)
		if deal.email != doc.email_id or deal.mobile_no != doc.mobile_no:
			deal.email = doc.email_id
			deal.mobile_no = doc.mobile_no
			deal.save(ignore_permissions=True)


@frappe.whitelist()
def get_contact(name):
	"""Get contact details including linked addresses"""
	contact = frappe.get_doc("Contact", name)
	contact.check_permission("read")

	contact_dict = contact.as_dict()

	if not len(contact_dict):
		frappe.throw(_("Contact not found"), frappe.DoesNotExistError)

	# Get linked addresses
	address_links = frappe.get_all(
		"Dynamic Link",
		filters={
			"link_doctype": "Contact",
			"link_name": name,
			"parenttype": "Address"
		},
		fields=["parent"]
	)

	addresses = []
	for link in address_links:
		address = frappe.get_doc("Address", link.parent)
		addresses.append({
			"name": address.name,
			"address_type": address.address_type,
			"address_line1": address.address_line1,
			"address_line2": address.address_line2,
			"pincode": address.pincode,
			"city": address.city,
			"state": address.state,
			"country": address.country,
			"modified": address.modified
		})

	contact_dict["addresses"] = addresses
	return contact_dict


@frappe.whitelist()
def get_linked_deals(contact):
	"""Get linked deals for a contact"""

	if not frappe.has_permission("Contact", "read", contact):
		frappe.throw("Not permitted", frappe.PermissionError)

	deal_names = frappe.get_all(
		"CRM Contacts",
		filters={"contact": contact, "parenttype": "CRM Deal"},
		fields=["parent"],
		distinct=True,
	)

	# get deals data
	deals = []
	for d in deal_names:
		deal = frappe.get_cached_doc(
			"CRM Deal",
			d.parent,
			fields=[
				"name",
				"organization",
				"currency",
				"annual_revenue",
				"status",
				"email",
				"mobile_no",
				"deal_owner",
				"modified",
			],
		)
		deals.append(deal.as_dict())

	return deals


@frappe.whitelist()
def create_new(contact, field, value):
	"""Create new email or phone for a contact"""
	if not frappe.has_permission("Contact", "write", contact):
		frappe.throw("Not permitted", frappe.PermissionError)

	contact = frappe.get_cached_doc("Contact", contact)

	if field == "email":
		email = {"email_id": value, "is_primary": 1 if len(contact.email_ids) == 0 else 0}
		contact.append("email_ids", email)
	elif field in ("mobile_no", "phone", "custom_main_phone_number"):
		# Check if this is the first phone number
		is_first_phone = len(contact.phone_nos) == 0
		phone = {
			"phone": value,
			"is_primary_mobile_no": 1 if is_first_phone else 0,
			"is_primary_phone": 1 if is_first_phone else 0
		}
		contact.append("phone_nos", phone)
		
		# If this is the first number, update the contact's mobile_no field
		if is_first_phone:
			contact.mobile_no = value
	else:
		frappe.throw("Invalid field")

	contact.save()
	# Reload the contact to ensure all fields are updated
	contact.reload()
	return True


@frappe.whitelist()
def set_as_primary(contact, field, value):
	"""Set email or phone as primary for a contact"""
	if not frappe.has_permission("Contact", "write", contact):
		frappe.throw("Not permitted", frappe.PermissionError)

	contact = frappe.get_doc("Contact", contact)

	if field == "email":
		for email in contact.email_ids:
			if email.email_id == value:
				email.is_primary = 1
			else:
				email.is_primary = 0
	elif field in ("mobile_no", "phone"):
		name = "is_primary_mobile_no" if field == "mobile_no" else "is_primary_phone"
		for phone in contact.phone_nos:
			if phone.phone == value:
				phone.set(name, 1)
			else:
				phone.set(name, 0)
	else:
		frappe.throw("Invalid field")

	contact.save()
	return True


@frappe.whitelist()
def search_emails(txt: str):
	doctype = "Contact"
	meta = frappe.get_meta(doctype)
	filters = [["Contact", "email_id", "is", "set"]]

	if meta.get("fields", {"fieldname": "enabled", "fieldtype": "Check"}):
		filters.append([doctype, "enabled", "=", 1])
	if meta.get("fields", {"fieldname": "disabled", "fieldtype": "Check"}):
		filters.append([doctype, "disabled", "!=", 1])

	or_filters = []
	search_fields = ["full_name", "email_id", "name"]
	if txt:
		for f in search_fields:
			or_filters.append([doctype, f.strip(), "like", f"%{txt}%"])

	results = frappe.get_list(
		doctype,
		filters=filters,
		fields=search_fields,
		or_filters=or_filters,
		limit_start=0,
		limit_page_length=20,
		order_by="email_id, full_name, name",
		ignore_permissions=False,
		as_list=True,
		strict=False,
	)

	return results


@frappe.whitelist()
def get_linked_addresses(contact):
	"""Get linked addresses for a contact"""

	if not frappe.has_permission("Contact", "read", contact):
		frappe.throw("Not permitted", frappe.PermissionError)

	address_links = frappe.get_all(
		"Dynamic Link",
		filters={
			"link_doctype": "Contact",
			"link_name": contact,
			"parenttype": "Address"
		},
		fields=["parent"]
	)

	addresses = []
	for link in address_links:
		address = frappe.get_doc("Address", link.parent)
		addresses.append({
			"name": address.name,
			"address_type": address.address_type,
			"address_line1": address.address_line1,
			"address_line2": address.address_line2,
			"pincode": address.pincode,
			"city": address.city,
			"state": address.state,
			"country": address.country,
			"modified": address.modified
		})

	return addresses

@frappe.whitelist()
def create_address_and_link_contact(address_data, contact_name):
    """Create a new address and link it to a contact"""
    try:
        address_doc = frappe.get_doc({
            "doctype": "Address",
            **address_data,
            "links": [
                {
                    "link_doctype": "Contact",
                    "link_name": contact_name,
                }
            ],
        })
        address_doc.insert()

        contact_doc = frappe.get_doc("Contact", contact_name)

        if not any(link.link_doctype == "Address" and link.link_name == address_doc.name for link in contact_doc.links):
            contact_doc.append("links", {
                "link_doctype": "Address",
                "link_name": address_doc.name,
                "link_title": address_doc.address_title or address_doc.name,
            })
            contact_doc.save()

        return address_doc.as_dict()
    except Exception as e:
        frappe.throw(str(e))


def update_contact_links(doc, method=None):
    """Update contact links when an address is created or updated"""
    contact_link = next((link for link in doc.links if link.link_doctype == "Contact"), None)
    if not contact_link:
        return

    contact_name = contact_link.link_name

    try:
        contact = frappe.get_doc("Contact", contact_name)
    except frappe.DoesNotExistError:
        return

    exists = any(link.link_doctype == "Address" and link.link_name == doc.name for link in contact.links)

    if not exists:
        contact.append("links", {
            "link_doctype": "Address",
            "link_name": doc.name,
            "link_title": doc.address_title or doc.name,
        })
        contact.save(ignore_permissions=True)


@frappe.whitelist()
def update_contact_and_link_address(contact_name, fieldname, value):
    """Update a contact field and link an address in a single transaction"""
    if not frappe.has_permission("Contact", "write"):
        frappe.throw("Not permitted", frappe.PermissionError)

    # Get fresh copy of contact to avoid timestamp mismatch
    contact = frappe.get_doc("Contact", contact_name)
    
    # Update the field value
    contact.set(fieldname, value)
    
    # Create the address link if it's an address field
    if fieldname == "address" and value:
        # Add link from address to contact
        address = frappe.get_doc("Address", value)
        address.append("links", {
            "link_doctype": "Contact",
            "link_name": contact_name
        })
        address.save(ignore_permissions=True)
        
        # Add link from contact to address
        contact.append("links", {
            "link_doctype": "Address",
            "link_name": value,
            "link_title": address.address_title or value
        })
    
    try:
        # Save everything in a single transaction
        contact.save(ignore_permissions=True)
    except frappe.TimestampMismatchError:
        # If we get a timestamp mismatch, reload and try again
        frappe.db.rollback()
        contact = frappe.get_doc("Contact", contact_name)
        contact.set(fieldname, value)
        if fieldname == "address" and value:
            contact.append("links", {
                "link_doctype": "Address",
                "link_name": value,
                "link_title": address.address_title or value
            })
        contact.save(ignore_permissions=True)
    
    # Return the complete contact data including addresses
    return get_contact(contact_name)


@frappe.whitelist()
def delete_contact_safely(contact_name):
    """Delete a contact by removing only this contact's links from addresses, without deleting addresses"""
    if not frappe.has_permission("Contact", "delete"):
        frappe.throw("Not permitted", frappe.PermissionError)

    try:
        # Get all linked addresses
        address_links = frappe.get_all(
            "Dynamic Link",
            filters={
                "link_doctype": "Contact",
                "link_name": contact_name,
                "parenttype": "Address"
            },
            fields=["parent"]
        )

        # Remove only this contact's links from addresses
        for link in address_links:
            address = frappe.get_doc("Address", link.parent)
            # Keep all links except the one for this contact
            address.links = [
                l for l in address.links 
                if not (l.link_doctype == "Contact" and l.link_name == contact_name)
            ]
            # Save the address regardless of remaining links
            address.save(ignore_permissions=True)

        # Now delete the contact
        frappe.delete_doc("Contact", contact_name, ignore_permissions=True)
        return True

    except Exception as e:
        frappe.throw(str(e))


@frappe.whitelist()
def add_contact_number(contact, contact_data):
    """Add a new contact number to the contact."""
    contact = frappe.get_doc("Contact", contact)
    
    # Create new contact phone entry
    contact.append("phone_nos", {
        "phone": contact_data.get("phone"),
        "custom_name": contact_data.get("custom_name"),
        "custom_last_name": contact_data.get("custom_last_name"),
        "custom_title": contact_data.get("custom_title"),
        "custom_email": contact_data.get("custom_email"),
        "custom_telefon": contact_data.get("custom_telefon"),
        "custom_function": contact_data.get("custom_function"),
        "is_primary_mobile_no": not contact.phone_nos,  # Set as primary if first number
        "is_primary_phone": not contact.phone_nos,  # Set as primary if first number
    })
    
    contact.save()
    return contact.as_dict()
