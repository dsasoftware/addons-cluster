#!/usr/bin/python
# -*- encoding: utf-8 -*-
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#    Module Writen to OpenERP, Open Source Management Solution
#    Copyright (C) OpenERP Venezuela (<http://openerp.com.ve>).
#    All Rights Reserved
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#    Author: Cluster Brands
#    Copyright 2013 Cluster Brands
#    Designed By: Jose J Perez M <jose.perez@clusterbrands.com>
#    Coded by: Eduardo Ochoa  <eduardo.ochoa@clusterbrands.com.ve>
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

import datetime
import calendar
from datetime import date, timedelta
from openerp.osv import osv, fields
from openerp.tools.translate import _


class hr_payperiod_schedule(osv.Model):

    _name = 'hr.payroll.period.schedule'

    def _get_weekly_periods(self,start_date):

        periods = []
        end_date = date(start_date.year, 12, 31)
        if (start_date.month > 1):
            start_date = start_date - timedelta(days=start_date.weekday())
        while start_date + timedelta(days=7-start_date.weekday()) < end_date:
            periods.append({
                'date_start': start_date,
                'date_end': start_date + timedelta(days=6-start_date.weekday())
            })
            start_date = start_date + timedelta(days=7-start_date.weekday())
        periods.append({'date_start':start_date, 'date_end': end_date})
        return periods

    def _get_biweekly_periods(self,start_date):
        periods = []
        end_of_year = date(start_date.year, 12, 31)
        while start_date <= end_of_year:
            if start_date.day <= 15:
                start_date = date(start_date.year, start_date.month, 1)
                end_date = date(start_date.year, start_date.month, 15)
            else:
                start_date = date(start_date.year, start_date.month, 16)
                end_day =  calendar.monthrange(start_date.year, start_date.month)[1]
                end_date = date(start_date.year, start_date.month, end_day)
            periods.append({
                'date_start':start_date, 
                'date_end': end_date,
            })
            start_date = end_date + timedelta(days=1)
        return periods

    def _get_monthly_periods(self,start_date):
        periods = []
        end_of_year = date(start_date.year, 12, 31)
        for month in range(start_date.month, 13):
            end_day =  calendar.monthrange(start_date.year, month)[1]
            periods.append({
                'date_start': date(start_date.year, month, 1), 
                'date_end': date(start_date.year, month, end_day),
            })
        return periods

    def create_period(self, cr, uid, ids, context=None):
        context = context or {}
        for obj in self.browse(cr, uid, ids, context=context):
            periods = []
            start_date = datetime.datetime.strptime(obj.start_date, '%Y-%m-%d').date()
            if obj.type == "weekly":
                periods = self._get_weekly_periods(start_date) 
            elif obj.type == "biweekly":
                periods = self._get_biweekly_periods(start_date)
            elif obj.type == "monthly":
                periods = self._get_monthly_periods(start_date)
            p_obj = self.pool.get('hr.payroll.period')
            p_ids = p_obj.search(cr, uid, [('schedule_id',"=", obj.id)], context= context)
            p_obj.unlink(cr, uid, p_ids, context=context)
            for i in range(0,len(periods)):
                values = {
                    'name': str(i+1).rjust(5,'0'),
                    'type': obj.type,
                    'schedule_id': obj.id,
                    'date_start': periods[i].get('date_start'),
                    'date_end': periods[i].get('date_end'),
                }
                p_obj.create(cr, uid, values, context=context)

    _columns = {
        'name': fields.char('Description', size=256, required=True),
        'type': fields.selection([
            ('weekly', 'Weekly'),
            ('biweekly', 'Biweekly'),
            ('monthly', 'Monthly'),
            ('custom', 'Custom'),
        ],    'Type', select=True, required=True),
        'start_date': fields.date('Initial Period Start Date', required=True),
        'paydate_biz_day': fields.boolean('Pay Date on a Business Day', required=False),
        'period_ids':fields.one2many('hr.payroll.period', 'schedule_id', 'Periods'), 
    }


class hr_payroll_period(osv.Model):

    _name = 'hr.payroll.period'

    _columns = {
        'name': fields.char('Description', size=5, required=True),
        'schedule_id': fields.many2one('hr.payroll.period.schedule',
                                       'Payroll Period Schedule',
                                       required=True, ondelete="cascade"),
        'date_start': fields.date('Start Date', required=True),
        'date_end': fields.date('End Date', required=True),
        'state': fields.selection([('draft', 'Draft'),
                                   ('actived', 'Active'),
                                   ('confirmed', 'Confirmado'),
                                   ('paid', 'Paid'),
                                   ('closed', 'Closed')],
                                  'State', select=True, readonly=True),
    }

    _defaults = {  
        'state': 'draft',  
    }
