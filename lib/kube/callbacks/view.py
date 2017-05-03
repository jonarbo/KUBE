#!/usr/bin/env python
# coding: utf-8

# Import some useful stuff
from kube.utils 	import *
# Import core engine 
from kube.engine	import KUBE

def start( args ):
	""" 
		Entry point for the 'view' command.
		Synopsis:
		kube.py view [-a APPS] [-n NETS] [-f FILESYS] [-s SYNTHS]
	"""

	configfile=None
	if  args.keys().count('configfile') != 0:
		configfile=args['configfile']
		del args['configfile'] 

	# create the engine instance
	kube = KUBE(configfile)
	
	if len( args.keys())==0:
		# view everything
		kube.view()	
	else:
		opts = args.keys()
		for o in opts:
			what = o 
			items = args[what].split(',')
			if items[0].lower()=='all':
				kube.view(what)	
			else:
				for i in items:
					kube.view(what,i)
