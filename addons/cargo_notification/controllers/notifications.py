# -*- coding: utf-8 -*-
# Part of Cargo Marketplace. See LICENSE file for full copyright and licensing details.
"""
CargoNotificationController — In-app notification endpoints for the Flutter app.

Routes:
  GET  /api/notifications                  — list user notifications
  POST /api/notifications/:id/read         — mark one as read
  POST /api/notifications/read-all         — mark all as read
"""
import json
import logging

from odoo import http
from odoo.http import request

from odoo.addons.cargo_base.constants import HTTP_200, HTTP_404, ERR_NOT_FOUND
from odoo.addons.cargo_api.controllers.base import CargoBaseController
from odoo.addons.cargo_api.utils.decorators import require_cargo_auth

_logger = logging.getLogger(__name__)


class CargoNotificationController(CargoBaseController):

    @http.route(
        '/api/notifications',
        auth='none',
        methods=['GET'],
        type='http',
        csrf=False,
        save_session=False,
    )
    @require_cargo_auth()
    def cargo_list_notifications(self, **kwargs):
        """GET /api/notifications[?limit=20&offset=0&unread=true]"""
        user = request.cargo_user
        args = request.httprequest.args

        try:
            limit  = max(1, min(int(args.get('limit', 20)), 100))
            offset = max(0, int(args.get('offset', 0)))
        except (TypeError, ValueError):
            limit, offset = 20, 0

        domain = [('user_id', '=', user.id)]
        if args.get('unread') in ('true', '1'):
            domain.append(('is_read', '=', False))

        notifs = request.env['cargo.notification'].sudo().search(
            domain, order='id desc', limit=limit, offset=offset,
        )
        total  = request.env['cargo.notification'].sudo().search_count(domain)
        unread = request.env['cargo.notification'].sudo().search_count(
            [('user_id', '=', user.id), ('is_read', '=', False)]
        )

        data = [n.to_notification_dict() for n in notifs]
        return request.make_response(
            json.dumps({'data': data, 'total': total, 'unreadCount': unread}),
            status=HTTP_200,
            headers=[('Content-Type', 'application/json')],
        )

    @http.route(
        '/api/notifications/<int:notif_id>/read',
        auth='none',
        methods=['POST'],
        type='http',
        csrf=False,
        save_session=False,
    )
    @require_cargo_auth()
    def cargo_mark_notification_read(self, notif_id, **kwargs):
        """POST /api/notifications/:id/read"""
        user  = request.cargo_user
        notif = request.env['cargo.notification'].sudo().browse(notif_id)

        if not notif.exists() or notif.user_id.id != user.id:
            return request.make_response(
                json.dumps({'error': ERR_NOT_FOUND, 'message': 'Notification not found.'}),
                status=HTTP_404,
                headers=[('Content-Type', 'application/json')],
            )

        notif.action_mark_read()
        return request.make_response(
            json.dumps(notif.to_notification_dict()),
            status=HTTP_200,
            headers=[('Content-Type', 'application/json')],
        )

    @http.route(
        '/api/notifications/read-all',
        auth='none',
        methods=['POST'],
        type='http',
        csrf=False,
        save_session=False,
    )
    @require_cargo_auth()
    def cargo_mark_all_read(self, **kwargs):
        """POST /api/notifications/read-all"""
        user   = request.cargo_user
        notifs = request.env['cargo.notification'].sudo().search(
            [('user_id', '=', user.id), ('is_read', '=', False)],
        )
        notifs.action_mark_read()
        return request.make_response(
            json.dumps({'message': f'Marked {len(notifs)} notifications as read.', 'count': len(notifs)}),
            status=HTTP_200,
            headers=[('Content-Type', 'application/json')],
        )
