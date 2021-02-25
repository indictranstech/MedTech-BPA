# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from frappe import _

def get_data():
	return [
		{
			"module_name": "MedTech-BPA",
			"color": "Blue",
			"icon": "octicon octicon-plus",
			"type": "module",
			"label": _("MedTech-BPA")
		},
		{
			"module_name": "MedTech Reports",
			"color": "grey",
			"icon": "octicon octicon-circuit-board",
			"type": "module",
			"label": _("Reports")
		}
	]