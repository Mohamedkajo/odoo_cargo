# -*- coding: utf-8 -*-
# Part of Cargo Marketplace. See LICENSE file for full copyright and licensing details.
"""
cargo.website.job — Careers / job listings.

Consumed by GET /api/careers.
"""
from odoo import fields, models

JOB_TYPES = [
    ('full_time',  'Full Time'),
    ('part_time',  'Part Time'),
    ('contract',   'Contract'),
    ('remote',     'Remote'),
    ('internship', 'Internship'),
]


class CargoWebsiteJob(models.Model):
    _name        = 'cargo.website.job'
    _description = 'Job Listing'
    _order       = 'department, title'
    _rec_name    = 'title'

    title       = fields.Char('Job Title',   required=True)
    department  = fields.Char('Department',  required=True)
    location    = fields.Char('Location',    default='Cairo, Egypt')
    job_type    = fields.Selection(JOB_TYPES, 'Type', default='full_time')
    salary_range = fields.Char('Salary Range', help='e.g. "EGP 15,000 – 25,000"')

    description  = fields.Html('Job Description', sanitize=True)
    requirements = fields.Html('Requirements',    sanitize=True)
    benefits     = fields.Html('Benefits',        sanitize=True)

    is_active   = fields.Boolean('Active', default=True)
    posted_date = fields.Date('Posted Date', default=fields.Date.today)

    def to_job_dict(self) -> dict:
        self.ensure_one()
        return {
            'id':          self.id,
            'title':       self.title,
            'department':  self.department,
            'location':    self.location or '',
            'type':        self.job_type,
            'salaryRange': self.salary_range or '',
            'description': self.description or '',
            'requirements': self.requirements or '',
            'benefits':    self.benefits or '',
            'postedDate':  str(self.posted_date) if self.posted_date else None,
        }
