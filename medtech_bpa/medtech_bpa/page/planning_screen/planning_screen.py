# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt
from __future__ import unicode_literals
import frappe

from frappe.model.document import Document
import json
from frappe.utils import nowdate, cstr, flt, cint, now, getdate,get_datetime,time_diff_in_seconds,add_to_date,time_diff_in_seconds,add_days
from datetime import datetime,date, timedelta
import time
from collections import OrderedDict

import json
import pandas as pd
import csv
import openpyxl
from frappe import _
import time
import io
import numpy as np
from io import BytesIO
from frappe.utils import cint, flt
from datetime import datetime
from collections import OrderedDict
from datetime import date, timedelta

@frappe.whitelist()
def get_items_data(from_date, to_date):
	print(from_date, to_date, type(from_date), type(to_date))
	sdate =  datetime.strptime(from_date, '%Y-%m-%d').date()
	edate =  datetime.strptime(to_date, '%Y-%m-%d').date()

	delta = edate - sdate

	date_list = []

	for i in range(delta.days + 1):
	    day = sdate + timedelta(days=i)
	    print(day)
	    date_list.append(day.strftime('%d-%m-%Y'))
	data = dict()
	data['header_list'] = date_list

	fg_item_group = frappe.db.sql("select item_group from `tabFG Item Group`", as_dict = 1)
	if fg_item_group:
		fg_group_list = ["'" + row.item_group + "'" for row in fg_item_group]
		fg_item_group_list = ','.join(fg_group_list)
	else:
		fg_item_group_list = "' '"

	item_detail = frappe.db.sql("select i.item_code, i.item_group, i.stock_uom from `tabItem` i join `tabBOM` b on i.item_code = b.item where b.docstatus = 1 and i.item_group in ({0}) group by i.item_code order by i.item_group, i.item_code".format(fg_item_group_list), as_dict=1)
	bom_query = frappe.db.sql("select b.item, b.name  from `tabBOM` b where b.docstatus = 1 and b.is_default = (select max(b2.is_default) from `tabBOM` b2 where b2.item = b.item and b.docstatus = 1)", as_dict = 1)
	bom_dict = {bom.get('item') : bom.get('name') for bom in bom_query}
	for row in item_detail:
		row['bom'] = bom_dict.get(row.get('item_code'))

	data['item_data'] = item_detail

	return data