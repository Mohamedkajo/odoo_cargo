# -*- coding: utf-8 -*-
# Part of Cargo Marketplace. See LICENSE file for full copyright and licensing details.
"""
res.partner extension — Cargo vendor business fields.

Every user already has a res.partner record (user.partner_id).
Vendor-specific business details are added here as cargo-prefixed fields
so they are visible on both the partner form and the user form (via the
partner_id relation).

Approval workflow:
  pending → approved  (by admin)
  pending → rejected  (by admin)

Only partners with cargo_role = 'vendor' (set on res.partner by cargo_base)
and cargo_vendor_is_approved = True may operate stores on the marketplace.
"""
from odoo import api, fields, models


class CargoVendorPartner(models.Model):
    """Extend res.partner with vendor registration and approval fields."""

    _inherit = 'res.partner'

    # ── Business identity ─────────────────────────────────────────────────────
    cargo_vendor_business_name = fields.Char(
        string='Business Name',
        help='Trading name of the vendor business.',
    )
    cargo_vendor_tax_number = fields.Char(
        string='Tax / VAT Number',
    )
    cargo_vendor_bank_account = fields.Char(
        string='Bank Account IBAN',
        help='IBAN for vendor payouts.',
    )

    # ── Commission ────────────────────────────────────────────────────────────
    cargo_vendor_commission_rate = fields.Float(
        string='Commission Rate (%)',
        digits=(5, 2),
        default=15.0,
        help='Platform commission percentage applied to each order subtotal.',
    )

    # ── Approval workflow ─────────────────────────────────────────────────────
    cargo_vendor_is_approved = fields.Boolean(
        string='Vendor Approved',
        default=False,
        index=True,
        help='Set True by an admin after vetting the vendor application.',
    )
    cargo_vendor_approved_at  = fields.Datetime('Approved At',     readonly=True)
    cargo_vendor_approved_by  = fields.Many2one(
        'res.users', 'Approved By', readonly=True,
    )
    cargo_vendor_reject_reason = fields.Text('Rejection Reason')

    # ── Computed ──────────────────────────────────────────────────────────────
    cargo_vendor_store_count = fields.Integer(
        string='Store Count',
        compute='_compute_vendor_store_count',
        help='Number of active stores owned by this vendor.',
    )

    def _compute_vendor_store_count(self):
        Store = self.env.get('cargo.store')
        if Store is None:
            for rec in self:
                rec.cargo_vendor_store_count = 0
            return
        for rec in self:
            user = self.env['res.users'].sudo().search(
                [('partner_id', '=', rec.id)], limit=1,
            )
            rec.cargo_vendor_store_count = (
                Store.sudo().search_count([('vendor_id', '=', user.id)])
                if user else 0
            )

    # ── Approval actions ──────────────────────────────────────────────────────

    def cargo_vendor_approve(self):
        """Approve this partner as a vendor and assign the vendor group."""
        for partner in self:
            partner.write({
                'cargo_vendor_is_approved': True,
                'cargo_vendor_approved_at': fields.Datetime.now(),
                'cargo_vendor_approved_by': self.env.uid,
                'cargo_vendor_reject_reason': False,
                'cargo_role': 'vendor',
            })
            user = self.env['res.users'].sudo().search(
                [('partner_id', '=', partner.id)], limit=1,
            )
            if user:
                group = self.env.ref('cargo_base.cargo_group_vendor', raise_if_not_found=False)
                if group:
                    user.sudo().write({'groups_id': [(4, group.id)]})

    def cargo_vendor_reject(self, reason=''):
        """Reject a vendor application."""
        self.write({
            'cargo_vendor_is_approved': False,
            'cargo_vendor_reject_reason': reason,
        })

    # ── API serialisation ─────────────────────────────────────────────────────

    def cargo_vendor_to_api_dict(self) -> dict:
        """Return vendor profile dict for REST API responses."""
        self.ensure_one()
        return {
            'id':             self.id,
            'businessName':   self.cargo_vendor_business_name or self.name,
            'taxNumber':      self.cargo_vendor_tax_number,
            'isApproved':     self.cargo_vendor_is_approved,
            'commissionRate': self.cargo_vendor_commission_rate,
            'storeCount':     self.cargo_vendor_store_count,
        }
