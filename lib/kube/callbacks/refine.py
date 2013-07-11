#!/usr/bin/env python
# coding: utf-8

# Import some useful stuff
from kube.utils 	import *
# Import core engine 
from kube.engine	import KUBE

def start( args ):
	""" 
		Entry point for the 'refine' command.
		Synopsis:
		kube.py refine  [-a APPS] [-n NETS] [-f FILESYS] [-s SYNTHS] [--since SINCE] [--to TO] [--rrd] [--log FILE]
	"""

	# create the engine instance
	kube = KUBE()
	
	opts = args.keys()
	if 'log' in opts:
		Printer.setLogfile(args['log'])
		printer.plain("--------------------------------------------")
		printer.info("Kube run on date",str(datetime.now()))
		printer.plain("--------------------------------------------")
		# remove the --log from the args
		del ( args['log'] )	
	
	useRRD = args['rrd']
	del ( args['rrd'] )	
	
	delta=None
	since=None
	to=datetime.now()

	if args.keys().count('since') !=0 :
		since=parser.parse(args['since'])
		del(args['since'])
	if args.keys().count('to') !=0 :
		to=parser.parse(args['to'])
		del(args['to'])	
	
	if since:
		delta = to-since
	else:
		delta = to - datetime(1973,05,02)
		since = 'origin'

	opts = args.keys()
	if len(opts)==0:
		kube.refine(To=to,Delta=delta,rrd=useRRD)
	else:
		for o in opts:
			what = o 
			items = args[what].split(',')
			if items[0].lower()=='all':
				kube.refine(what,To=to,Delta=delta,rrd=useRRD)	
			else:
				for i in items:
					print "sfsdf"
					kube.refine(what,i,To=to,Delta=delta,rrd=useRRD)
			