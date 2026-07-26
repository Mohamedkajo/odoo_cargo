# -*- coding: utf-8 -*-
# cargo_order extends sale.order with delivery-specific fields.
# No cargo.order custom model — sale.order (with cargo_status) IS the order.
from . import sale_order
