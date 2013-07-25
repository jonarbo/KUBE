#!/usr/bin/env python
# coding: utf-8

from datetime import datetime , timedelta

# Import the printer
from kube.printer	import *
# Import some useful stuff
from kube.utils 	import *
# Import core engine 
from kube.engine	import KUBE

def start( args ):
	""" 
		Entry point for the 'graph' command.
		Synopsis:
		kube.py graph {-t DIR [-p] [-m METRIC_NAME] [--since SINCE] [--to TO] , -b BASE_DIR [-p] [--target DIR] { [--since SINCE] [--to TO], [--at DATE] }}
	"""

	# create the engine instance
	kube = KUBE()

	opts = args.keys()
	delta=None
	since=None
	to=datetime.now()
	printToSTDOUT=args['p'] 
	
	if 't' in opts:
		# time analysis
		mname=None

		# get target dir	
		target = args['t'] 
		
		# get the list of the metrics
		if 'metric_name' in opts:
				mname  = args['metric_name'].split(',')
				
		if not 'since' in opts and not 'to' in opts:
			# call the fast method
			kube.timeAnalysis(target,mname,printToSTDOUT)
		else:	
			try:			
				if args.keys().count('since') !=0 :
					since=parser.parse(args['since'])
				if args.keys().count('to') !=0 :
					to=parser.parse(args['to'])
	
				if since:
					delta = to-since
				else:
					delta = to - datetime(1973,05,02)
			except Exception as x :
				printer.error("Error!!! Possible wrong date format" , str(x))
				return
			kube.timeAnalysis(target,mname,printToSTDOUT,to,delta)	
		
		return
		
		
	if 'b' in opts:
		# metrics boxplot graph analysis
		target = None
		mname=None
		at = None

		# get target dir	
		template = args['b']

		# get the list of the metrics
		if 'metric_name' in opts:
			mname  = args['metric_name'].split(',')

		# get the target dir
		if 'target' in opts:
			target  = args['target']
				
		# get the exact date if exists
		if 'at' in opts:
			since  = parser.parse(args['at'])
			to = since
		
		if not 'since' in opts and not 'to' in opts and not 'at' in opts:
			# call the fast method
			kube.metricAnalysis(template,target,printToSTDOUT,to,to - datetime(1973,05,02),mname)
		else:		
			try:		
				if args.keys().count('since') !=0 :
					since=parser.parse(args['since'])
				if args.keys().count('to') !=0 :
					to=parser.parse(args['to'])
		
				if since:
					delta = to-since
				else:
					delta = to - datetime(1973,05,02)
			except Exception as x :
				printer.error("Error","Possible wrong date format")
				return					
			kube.metricAnalysis(template,target,printToSTDOUT,to,delta,mname)	

		return
		
		
		
		
		
		
		