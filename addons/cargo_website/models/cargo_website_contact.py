# -*- coding: utf-8 -*-
# Part of Cargo Marketplace. See LICENSE file for full copyright and licensing details.
"""
cargo.website.contact — Contact form submissions.

Receives data from POST /api/contact.
Submissions land in the Odoo backend where staff can read and reply.
"""
from odoo import fields, models

CONTACT_STATUS = [
    ('new',     'New'),
    ('read',    'Read'),
    ('replied', 'Replied'),
    ('closed',  'Closed'),
]

CONTACT_SUBJECT = [
    ('general',         'General Inquiry'),
    ('support',         'Technical Support'),
    ('partnership',     'Partnership'),
    ('vendor',          'Become a Vendor'),
    ('driver',          'Become a Driver'),
    ('billing',         'Billing'),
    ('other',           'Other'),
]


class CargoWebsiteContact(models.Model):
    _name        = 'cargo.website.contact'
    _description = 'Contact Form Submission'
    _order       = 'create_date desc'
    _rec_name    = 'name'

    name    = fields.Char('Name',    required=True)
    email   = fields.Char('Email',   required=True)
    phone   = fields.Char('Phone')
    subject = fields.Selection(CONTACT_SUBJECT, 'Subject', default='general')
    message = fields.Text('Message', required=True)

    status   = fields.Selection(CONTACT_STATUS, 'Status', default='new', index=True)
    notes    = fields.Text('Internal Notes')

    # ── Source tracking ───────────────────────────────────────────────────────
    source     = fields.Char('Source', default='website')
    ip_address = fields.Char('IP Address')
    user_agent = fields.Char('User Agent')
