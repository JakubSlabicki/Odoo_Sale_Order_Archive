# Welcome to Go_REST_API!

Hi! In this project I create simple module in Odoo 15, module to archive sale orders. The goal is to automatically rewrite data from *sale.order* module to archive and delete them from *sale.order* module. 


# Setup steps

 - Oracle VM VirtualBox 6.1
 - Ubuntu 22.04 LTS
 - Odoo 15
 - PyCharm 


## Model
Model is named **sale.order.archive**.  It has fields for name of order, order create date, some relative data as customer, sale person ID and order currency and amount of all order items.

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


When we have model, we can create function which we declare in Scheduler on Odoo APP. Function will do:

 1. Get all records from *sale.order* module with state equal to  **cancel** or **sale**

        for record in self.env['sale.order'].search(['|', ('state', '=','cancel'), ('state', '=', 'sale')]):


 2. If record date order is more then 30 days older it searches *sale.order.line* model to count all of items in order.


        start_date = record.date_order.strftime('%Y-%m-%d')
        current_date = datetime.datetime.now().date() + relativedelta(days=-30)
        if start_date <= current_date.strftime('%Y-%m-%d'):
	    	count_order_quantity = 0
	    	for rec in self.env['sale.order.line'].search([('order_id.id', '=', record.id)]):
	    		count_order_quantity += rec.product_uom_qty

 3. Create list of all data and append to array *val* (becouse of **RecursionError**) and delete record from *sale.order* module.

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
		
 4. Create record in archive module.

    
        for each in val:
			self.env['sale.order.archive'].create(each)


Now we create a ![Schedule Action](https://github.com/JakubSlabicki/Odoo_Sale_Order_Archive/blob/main/task_2.PNG). To do this we go through Web App **Settings/Technical/Automation/Schedule Actions**. After naming action, linking model and setting time period we simple call our function:

    model.archive_order().



