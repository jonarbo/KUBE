#!/usr/bin/env python
# coding: utf-8

# Import some useful stuff
from kube.utils 	import *
# Import core engine 
from kube.engine	import KUBE

def start( args ):
	""" 
		Entry point for the 'run' command.
		Synopsis:
		kube.py run [-a APPS] [-n NETS] [-f FILESYS] [-s SYNTHS]
	"""

	# create the engine instance
	kube = KUBE()

	if len( args.keys())==0:
		# Run everything
		kube.run()	
	else:
		opts = args.keys()
		for o in opts:
			what = o 
			items = args[what].split(',')
			if items[0].lower()=='all':
				kube.run(what)	
			else:
				for i in items:
					kube.run(what,i)
