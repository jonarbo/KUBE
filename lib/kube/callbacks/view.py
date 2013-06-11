#!/usr/bin/env python
# coding: utf-8

# Import the logger
from kube.log 		import *
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

	# create the engine instance
	kube = KUBE()

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