#!/usr/bin/env python
# coding: utf-8

from datetime import datetime , timedelta

# Import the logger
from kube.log 		import *
# Import some useful stuff
from kube.utils 	import *
# Import core engine 
from kube.engine	import KUBE

def start( args ):
	""" 
		Entry point for the 'probe' command.
		Synopsis:
		kube.py probe {-t DIR [-m METRIC_NAME] [--since SINCE] [--to TO] , -k BASE_DIR [--target DIR] [--since SINCE] [--to TO] }
	"""

	# create the engine instance
	kube = KUBE()

	opts = args.keys()
	delta=None
	since=None
	to=datetime.now()
	
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
			kube.timeAnalysis(target,mname)
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
				logger.error("Error","Possible wrong date format")
				return
			kube.timeAnalysis(target,mname,to,delta)	
		
		return
		
		
	if 'k' in opts:
		# Kiviat graph analysis
		target = None

		# get target dir	
		template = args['k']

		# get the target dir
		if 'target' in opts:
				target  = args['target']
		
		if not 'since' in opts and not 'to' in opts:
			# call the fast method
			kube.kiviat(template,target,to,to - datetime(1973,05,02))
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
				logger.error("Error","Possible wrong date format")
				return					
			kube.kiviat(template,target,to,delta)	

		return
		
		
		
		
		
		
		