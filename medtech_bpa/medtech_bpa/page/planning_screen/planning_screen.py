#Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt
from __future__ import unicode_literals
import frappe

from frappe.model.document import Document
from frappe.utils import nowdate, cstr, flt, cint, now, getdate,get_datetime,time_diff_in_seconds,add_to_date,time_diff_in_seconds,add_days,today
from datetime import datetime,date, timedelta
from frappe.model.naming import make_autoname
import time
import json
import pandas as pd
from frappe import _


@frappe.whitelist()
def save_items_data(from_date,to_date,data):
    
    #dates_check(from_date,to_date)
    date_range = pd.date_range(from_date,to_date)
    date_range= [(i).strftime("%d-%m-%Y") for i in  date_range]
    doc = frappe.new_doc("Planning Master")
    doc.from_date=from_date
    doc.to_date=to_date
    data = json.loads(data)
    doc.title="abc"
    doc.save()
    frappe.db.set_value("Planning Master", doc.name,'title',doc.name)
    for j in date_range:
        for i in range(len(data['item_code'])):
            doc_child= frappe.new_doc('Planning Master Item')
            doc_child.item_code = data['item_code'][i]
            doc_child.item_name = data['item_code'][i]
            doc_child.date =  datetime.strptime(j,"%d-%m-%Y")
            try:
                if '<br>' in data[j[:-5]][i]:
                    doc_child.amount = float(data[j[:-5]][i][0:-4]) if data[j[:-5]][i][0:-4] not in ['',None,'.'] else 0
                else:
                    doc_child.amount =  float(data[j[:-5]][i]) 
            except Exception as e:
                frappe.throw("Error in saving data at column %s and row %s"%(j,i+1))
            doc_child.uom = data["uom"][i]
            doc_child.bom = data["bom"][i]
            doc_child.planning_master_parent = doc.name
            doc_child.save()
            frappe.db.set_value("Planning Master Item", doc_child.name,'title',doc_child.name)
    return ["1",doc.name] 

def dates_check(from_date,to_date):    
    if from_date <= today():
        frappe.throw("From Date must be greater than today.")
    if to_date <= today():
        frappe.throw("To Date must be greater than today.")
    if to_date < from_date:
        frappe.throw("To Date must be greater than or equals to From Date.")
    date_overlap = frappe.db.sql("select name,from_date,to_date from `tabPlanning Master` where '%s' between from_date and to_date or '%s' between from_date and to_date"%(from_date,to_date),as_list=1)
    
    if len(date_overlap)>0:
        frappe.throw("Date overlaps with Planning Master %s having From Date %s and To Date %s "%(date_overlap[0][0],date_overlap[0][1].strftime('%d-%m-%Y'),date_overlap[0][2].strftime('%d-%m-%Y')))

@frappe.whitelist()
def delete_data(delete_data):
    doc = frappe.get_doc("Planning Master",delete_data)
    if doc.from_date <= date.today():
        frappe.throw("The entry cannot be deleted because it contains past date or present date.")
    names_of_child = [i[0] for i in frappe.db.sql("""select name from `tabPlanning Master Item` where planning_master_parent = '%s'"""%(delete_data))]
    for i in names_of_child:
        frappe.delete_doc("Planning Master Item",i)

    frappe.delete_doc("Planning Master",delete_data)
    frappe.db.commit()
    return "1"

@frappe.whitelist()
def get_items_data(from_date, to_date,listview=None):
        #dates_check(from_date,to_date)    
        sdate =  datetime.strptime(from_date, '%Y-%m-%d').date()
        edate =  datetime.strptime(to_date, '%Y-%m-%d').date()
        delta = edate - sdate
        date_list = []
        date_dict= []
        for i in range(delta.days + 1):
            day = sdate + timedelta(days=i)
        
            if date.today() >= day:
                date_dict.append([day.strftime('%d-%m'),0])
            else:
                date_dict.append([day.strftime('%d-%m'),1])
            date_list.append(day.strftime('%d-%m-%Y'))
    
        data = dict()
        data['header_list'] = date_dict

        fg_item_group = frappe.db.sql("select item_group from `tabFG Item Group`", as_dict = 1)
    
        if fg_item_group:
            fg_group_list = ["'" + row.item_group + "'" for row in fg_item_group]
            fg_item_group_list = ','.join(fg_group_list)
        else:
            fg_item_group_list = "' '"

        item_detail = frappe.db.sql("select i.item_code,i.name, i.item_group, i.stock_uom from `tabItem` i join `tabBOM` b on i.item_code = b.item where b.docstatus = 1 and i.item_group in ({0}) group by i.item_code order by i.item_group, i.item_code".format(fg_item_group_list), as_dict=1)
        bom_query = frappe.db.sql("select b.item, b.name  from `tabBOM` b where b.docstatus = 1 and b.is_default = (select max(b2.is_default) from `tabBOM` b2 where b2.item = b.item and b.docstatus = 1)", as_dict = 1)
        bom_dict = {bom.get('item') : bom.get('name') for bom in bom_query}
        uom_dict={}
        
        for i in item_detail:
            uom_dict[i.item_code]=[i.name,i.stock_uom]
       
        for row in item_detail:
            row['bom'] = bom_dict.get(row.get('item_code'))
        item_code_list = [i.get('item_code') for i in item_detail]
        data['item_data'] = item_detail
        data['item_code'] = item_code_list
        data['update']=0
        data['uom_dict']=uom_dict
       
        return data

@frappe.whitelist()
def get_bom_based_on_item_code(item_code):
   
    bom_list = [ i[0] for i in frappe.db.sql("select b.name from `tabItem` i join `tabBOM` b on i.item_code = b.item where i.item_code='%s'"%(item_code), as_list=1)]
    
    return bom_list
@frappe.whitelist()
def fetch_data(name):
    try:
        send_data={}
        date_range = pd.date_range(frappe.get_value('Planning Master',name,'from_date'),frappe.get_value('Planning Master',name,'to_date'))
        date_range= [[(i).strftime("%d-%m-%Y"),0 if pd.Timestamp(date.today()) >= i else 1] for i in  date_range]
        data = frappe.db.sql("""select GROUP_CONCAT(name) as name,item_code , uom as stock_uom,bom ,GROUP_CONCAT(amount) as amount from `tabPlanning Master Item` where planning_master_parent = '%s' group by item_code order by date"""%(name),as_dict=1)
        for i in data:
            i['name'] = i['name'].split(',')
            i['amount']= [float(i) for i in i['amount'].split(',')]
        send_data['header_list']=date_range
        send_data['item_data']=data
        send_data['update']=1
        return send_data
    except Exception as e:
        error_log= frappe.log_error(message=frappe.get_traceback(), title=str(e))
        frappe.throw("Error in fetching data {}".format(frappe.utils.get_link_to_form("Error Log",error_log.name)))

@frappe.whitelist()
def update_data(update_data):
    try :

        update_data = json.loads(update_data)
        if  len(update_data) ==0:
            return ["0"]
        #update_data = json.loads(update_data)
        for i in update_data:
            for values in range(len(i)):
                if type(i[values]) == str:
                    if '<br>' in i[values]:
                        i[values]=i[values][0:-4]
                        i[values] = 0 if i[values] == '' else i[values]
                    if '.' == i[values]:
                        i[values]=0
            doc = frappe.get_doc("Planning Master Item" ,i[0])
            #if doc.amount== int(i[2]):
            try:
                doc.amount=float(i[1])
            except Exception as e:
                return ["0","Please check if the values changed  are correct"]
            doc.save()
            #else:
                #frappe.throw("The old amount does not match for planning master item %s and amount %s"%(update_data[1],int(i[2])))
        return ["1",doc.planning_master_parent]
    except Exception as e:
        error_log= frappe.log_error(message=frappe.get_traceback(), title=str(e))
        frappe.throw("Error in updating data {}".format(frappe.utils.get_link_to_form("Error Log",error_log.name)))
        
        
@frappe.whitelist()
def return_list(item_detail):
    item_detail = [i[0] for i in frappe.db.sql("select b.name from `tabItem` i join `tabBOM` b on i.item_code = b.item where i.item_code='%s'"%(item_detail), as_list=1)]
    
    return item_detail