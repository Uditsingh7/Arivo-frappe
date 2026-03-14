import frappe
from groq import Groq

@frappe.whitelist(allow_guest=True)
def draft_reminder(invoice_name):
    inv = frappe.db.get_value(
        "Sales Invoice",
        invoice_name,
        ["customer", "customer_name", "outstanding_amount",
         "due_date", "grand_total", "currency", "name"],
        as_dict=True
    )

    if not inv:
        frappe.throw(f"Invoice {invoice_name} not found")

    from frappe.utils import date_diff, today
    days_overdue = date_diff(today(), inv.due_date)

    customer_email = frappe.db.get_value("Customer", inv.customer, "email_id") or "N/A"
    past_reminders = frappe.db.count("Collection Log", {"sales_invoice": invoice_name})

    if days_overdue >= 30:
        tone = "Final Notice"
        tone_instruction = "firm, urgent, and professional. Make it clear this is the final reminder before escalation."
    elif days_overdue >= 15:
        tone = "Firm"
        tone_instruction = "firm but professional. Express concern about the delay and request immediate action."
    else:
        tone = "Polite"
        tone_instruction = "polite and friendly. Assume it may be an oversight and gently remind them."

    settings = frappe.get_single("Collection Settings")
    api_key = settings.get_password("groq_api_key") if settings.groq_api_key else None

    if not api_key:
        frappe.throw("Groq API Key not set in Collection Settings")

    prompt = f"""
You are a professional accounts receivable assistant for a company.
Write a collection reminder email with a {tone_instruction} tone.

Invoice Details:
- Invoice Number: {inv.name}
- Customer Name: {inv.customer_name}
- Amount Due: {inv.currency} {inv.outstanding_amount:,.2f}
- Original Due Date: {inv.due_date}
- Days Overdue: {days_overdue} days
- Previous Reminders Sent: {past_reminders}

Requirements:
- Keep it concise (max 150 words)
- Include invoice number and amount clearly
- End with a clear call to action
- Do not include subject line, just the email body
- Sign off as "Accounts Team"
"""

    client = Groq(api_key=api_key)

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "You are a professional accounts receivable assistant."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=300,
        temperature=0.7
    )

    email_body = response.choices[0].message.content.strip()

    subject_map = {
        "Polite": f"Friendly Reminder: Invoice {inv.name} – {inv.currency} {inv.outstanding_amount:,.2f} Overdue",
        "Firm": f"Action Required: Invoice {inv.name} – {inv.currency} {inv.outstanding_amount:,.2f} Past Due",
        "Final Notice": f"FINAL NOTICE: Invoice {inv.name} – {inv.currency} {inv.outstanding_amount:,.2f} Immediate Payment Required"
    }

    return {
        "invoice": inv.name,
        "customer": inv.customer_name,
        "customer_email": customer_email,
        "amount": inv.outstanding_amount,
        "currency": inv.currency,
        "days_overdue": days_overdue,
        "tone": tone,
        "subject": subject_map[tone],
        "body": email_body
    }


@frappe.whitelist(allow_guest=True)
def send_reminder(invoice_name, subject, body, customer_email):
    email_sent = False
    email_error = None

    try:
        frappe.sendmail(
            recipients=[customer_email],
            subject=subject,
            message=body.replace('\n', '<br>'),
            now=True
        )
        email_sent = True
    except Exception as e:
        email_error = str(e)
        frappe.log_error(frappe.get_traceback(), "Arivo Send Reminder Email Error")

    try:
        customer = frappe.db.get_value("Sales Invoice", invoice_name, "customer")
        log = frappe.get_doc({
            "doctype": "Collection Log",
            "sales_invoice": invoice_name,
            "customer": customer,
            "email_subject": subject,
            "email_body": body,
            "status": "Sent" if email_sent else "Failed",
        })
        log.insert(ignore_permissions=True)
        frappe.db.commit()
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Arivo Reminder Log Error")

    if email_sent:
        return {"status": "sent", "message": f"Reminder sent to {customer_email}"}
    else:
        return {"status": "logged", "message": f"Email failed ({email_error}) but reminder was logged"}

def load():
    pass
