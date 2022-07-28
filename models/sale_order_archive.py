from odoo import models, fields, api
import datetime
from dateutil.relativedelta import relativedelta


class TaskArchive(models.Model):
    _name = 'sale.order.archive'
    _description = "Sales Order Archive"

    name = fields.Char(string="Name")
    order_create_date = fields.Date(string="Order create date")
    customer_id = fields.Many2one('res.partner', string='Customer')
    sale_person_id = fields.Many2one('res.users', string='Sale Person')
    order_currency_id = fields.Many2one('res.currency')
    order_total_amount_id = fields.Monetary(string='Order Total Amount', currency_field='order_currency_id')
    count_of_orders_lines = fields.Integer(string='Count of Order Lines')

    def archive_order(self):
        val = []
        for record in self.env['sale.order'].search(['|', ('state', '=', 'cancel'), ('state', '=', 'sale')]):
            start_date = record.date_order.strftime('%Y-%m-%d')
            current_date = datetime.datetime.now().date() + relativedelta(days=-30)
            if start_date <= current_date.strftime('%Y-%m-%d'):
                count_order_quantity = 0
                for rec in self.env['sale.order.line'].search([('order_id.id', '=', record.id)]):
                    count_order_quantity += rec.product_uom_qty
                vals = {
                    'name': record.name,
                    'order_create_date': record.date_order,
                    'customer_id': record.partner_id.id,
                    'sale_person_id': record.user_id.id,
                    'order_currency_id': record.currency_id.id,
                    'order_total_amount_id': record.amount_total,
                    'count_of_orders_lines': count_order_quantity,
                }
                val.append(vals)
                record.unlink()
        for each in val:
            self.env['sale.order.archive'].create(each)
