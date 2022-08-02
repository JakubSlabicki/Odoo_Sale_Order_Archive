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


Now we create a Schedule Action:![Schedule Action](https://github.com/JakubSlabicki/Odoo_Sale_Order_Archive/blob/main/task_2.PNG). To do this we go through Web App **Settings/Technical/Automation/Schedule Actions**. After naming action, linking model and setting time period we simple call our function:

    model.archive_order().


## Editing *sale* module

We are editing *sale* module to add exporting functionary. Function task is to create  [example of **product_list**](https://github.com/JakubSlabicki/Odoo_Sale_Order_Archive/blob/main/product_list.csv) **file** that contains main information about product from orders like:

 - Product ID , Barcode , Internal reference
 - Sales count, mean and sum price

Function counts only products form orders which state is equal to *cancel* or *done* ( `('state', '=', 'done')` or `('state', '=', 'sale')`) and sale checkbox is checked and chosen **Export to .csv** option: ![checked ](https://github.com/JakubSlabicki/Odoo_Sale_Order_Archive/blob/main/checkboxed_sales.PNG) 

We are editing one **sale/views** file named [sale_views.xml](https://github.com/JakubSlabicki/Odoo_Sale_Order_Archive/blob/main/sale%28edited_files%29/views/sale_views.xml) with simply adding several lines which create option with action called **export_data_csv()** in :

    <record id="model_sale_order_action_export_csv" model="ir.actions.server">
	    <field name="name">Export to .cvs</field>
	    <field name="model_id" ref="sale.model_sale_order"/>
		<field name="binding_model_id" ref="sale.model_sale_order"/>
		<field name="binding_view_types">form,list</field>
		<field name="state">code</field>
		<field name="code">action = records.export_data_csv()</field>
	</record>


Action will be declared in file [sale_order.py](https://github.com/JakubSlabicki/Odoo_Sale_Order_Archive/blob/main/sale%28edited_files%29/models/sale_order.py) located in **sale/models** . At the end of model *sale.order* we are adding: 

    def export_data_csv(self):
	    products_id_price = {}
		with open('product_list.csv', mode='w') as employee_file:
			employee_writer = csv.writer(employee_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
			employee_writer.writerow(['Product ID', 'Product Barcode', 'Product internal reference', 'Sales count', 'Average price unit','Sales price'])
			for record_id in self.ids:
				for record_order in self.env['sale.order'].search([('id', '=', record_id), '|', ('state', '=', 'done'), ('state', '=', 'sale')]):
					for record_line in self.env['sale.order.line'].search([('order_id.id', '=', record_order.id)]):
						key = record_line.product_id.id
						value = record_line.price_unit

						for _ in range(int(record_line.product_uom_qty)):
							if key not in products_id_price:
								products_id_price[key] = []
							products_id_price[key].append(value)
			for k, v in products_id_price.items():
				products_id_price[k] = [len(v), numpy.mean(v), sum(v)]
			for k, array_v in products_id_price.items():
				for record_product in self.env['product.product'].search([('id', '=', k)]):
					employee_writer.writerow([record_product.id,record_product.barcode, record_product.default_code,array_v[0], array_v[1], array_v[2]])

Function that:
	

 1. Creates *.csv* file and writes column names



	    with open('product_list.csv', mode='w') as employee_file: 
	  		employee_writer = csv.writer(employee_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL) 
		    employee_writer.writerow(['Product ID', 'Product Barcode', 'Product internal reference', 'Sales count', 'Average price unit','Sales price'])



 2. Collects checked  **sale.order** ids checks if statuses are *done* or *sale*

	    for record_id in self.ids:
		    for record_order in self.env['sale.order'].search([('id', '=', record_id), '|', ('state', '=', 'done'), ('state', '=', 'sale')]):
		    
 3. Compares ids to  **sale.order.line** model to get product ID, calculate mean (using **numpy** lib) and sum of sales.

			    for record_line in self.env['sale.order.line'].search([('order_id.id', '=', record_order.id)]):
					key = record_line.product_id.id
					value = record_line.price_unit
					for _ in range(int(record_line.product_uom_qty)):
						if key not in products_id_price:
							products_id_price[key] = []
						products_id_price[key].append(value)
			for k, v in products_id_price.items():
				products_id_price[k] = [len(v), numpy.mean(v), sum(v)]
 4. Compares product ID and gets more product info from **product.product** model

	    for k, array_v in products_id_price.items():
		    for record_product in self.env['product.product'].search([('id', '=', k)]):
 5. Saves data to *.csv* file

	    employee_writer.writerow([record_product.id, record_product.barcode, record_product.default_code, array_v[0], array_v[1], array_v[2]])
