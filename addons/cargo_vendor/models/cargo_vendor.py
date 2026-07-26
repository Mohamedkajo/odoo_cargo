# -*- coding: utf-8 -*-
"""
cargo.vendor — Vendor profile.

One cargo.vendor record per vendor user. Links to their stores and holds
business-specific metadata (tax number, bank account, commission rate,
approval status).
"""
from odoo import api, fields, models


class CargoVendor(models.Model):
    _name = 'cargo.vendor'
    _description = 'Cargo Vendor Profile'
    _rec_name = 'business_name'

    user_id = fields.Many2one(
        'res.users', 'Vendor User',
        required=True, ondelete='cascade', index=True,
        domain=[('cargo_role', '=', 'vendor')],
    )
    business_name = fields.Char('Business Name', required=True)
    tax_number    = fields.Char('Tax / VAT Number')
    bank_account  = fields.Char('Bank Account IBAN')

    # Commission rate — overrides the platform default
    commission_rate = fields.Float(
        'Commission Rate (%)', default=15.0, digits=(5, 2),
        help='Percentage of each order subtotal paid to Cargo.',
    )

    # Approval workflow
    is_approved  = fields.Boolean('Approved', default=False, index=True)
    approved_at  = fields.Datetime('Approved At', readonly=True)
    approved_by  = fields.Many2one('res.users', 'Approved By', readonly=True)
    reject_reason = fields.Text('Rejection Reason')

    # Stores owned by this vendor
    store_ids = fields.One2many('cargo.store', 'vendor_id', string='Stores')
    store_count = fields.Integer('Store Count', compute='_compute_store_count')

    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('unique_vendor_user', 'UNIQUE(user_id)', 'Each user can have only one vendor profile.'),
    ]

    @api.depends('store_ids')
    def _compute_store_count(self):
        for v in self:
            v.store_count = len(v.store_ids)

    def action_approve(self):
        self.write({
            'is_approved': True,
            'approved_at': fields.Datetime.now(),
            'approved_by': self.env.uid,
        })
        for v in self:
            v.user_id.sudo().write({'groups_id': [(4, self.env.ref('cargo_base.cargo_group_vendor').id)]})

    def action_reject(self, reason=''):
        self.write({'is_approved': False, 'reject_reason': reason})

    def to_vendor_dict(self):
        self.ensure_one()
        return {
            'id':             self.id,
            'userId':         self.user_id.id,
            'businessName':   self.business_name,
            'taxNumber':      self.tax_number,
            'isApproved':     self.is_approved,
            'commissionRate': self.commission_rate,
            'storeCount':     self.store_count,
        }
