#!/usr/bin/env python
# coding: utf-8

# Import some useful stuff
from kube.utils 	import *
# Import core engine 
from kube.engine	import KUBE

import datetime

def start( args ):
	""" 
		Entry point for the 'run' command.
		Synopsis:
		kube.py run [-a APPS] [-n NETS] [-f FILESYS] [-s SYNTHS] [--log FILE]
	"""

	configfile=None
	if  args.keys().count('configfile') != 0:
		configfile=args['configfile']
		del args['configfile'] 

	# create the engine instance
	kube = KUBE(configfile)

	opts = args.keys()
	if 'log' in opts:
		Printer.setLogfile(args['log'])
		printer.plain("--------------------------------------------")
		printer.info("Kube run on date",str(datetime.datetime.now()))
		printer.plain("--------------------------------------------")
		# remove the --log from the args
		del ( args['log'] )	

	if len( args.keys())==0:
		# Run everything
		kube.run()	
	else:
		for o in opts:
			if o != 'log':
				what = o 
				items = args[what].split(',')
				if items[0].lower()=='all':
					kube.run(what)	
				else:
					for i in items:
						kube.run(what,i)
