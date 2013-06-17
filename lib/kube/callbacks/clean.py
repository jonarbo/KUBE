#!/usr/bin/env python
# coding: utf-8

import sys
import shutil
from datetime import datetime , timedelta

# Import the printer
from kube.printer 		import *
# Import some useful stuff
from kube.utils 	import *
# Import core engine 
from kube.engine	import KUBE

def cleanup(dir,since,to,delta):
	# borrar solo el dir seleccionado entre since y to:
	printer.info( "Cleaning","You are about to remove all data in "  +  Printer.bold(dir) +"  since " + Printer.bold(str(since)) + " to " + Printer.bold(str(to)) )
	var = raw_input("Are you sure you want to do that? (Yes/No)")	
	if var=="Yes":			
		for dd in walkDir(dir,to,delta):
			clean( dd ,True)
			# remove if empty ...
			pd = os.path.dirname(dd)
			if not os.listdir( pd ) :	
				shutil.rmtree( pd )						
	else:
		printer.info( "Cleaning","cancelled")				
		return
		
	# cleaning empty dirs
	repeat = True
	import glob
	while repeat:
		repeat = False
		for dd in walkDir(dir):
			if  len( glob.glob(dd+"/*") )==0:
				repeat = True
				clean( dd ,True)			
	printer.info("Cleaning", "Done." )
		
def start( args ):
	""" 
		Entry point for the 'clean' command.
		Synopsis:
		kube.py clean [-d {runs,results}] [--since SINCE] [--to TO] [-a APPS] [-n NETS] [-f FILESYS] [-s SYNTHS]
	"""

	# create the engine instance
	kube = KUBE()
	
	cleaner={\
			'runs':    kube.runs_dir, \
			'results': kube.results_dir }	

	#printer.setCurrentTheme('None')
	header = "Cleaning"
	
	opts = args.keys()
	if len(opts)==0:
		printer.warning(header, Printer.bold("You are about to remove all stored results") )
		var = raw_input("Are you sure you want to do that? (Yes/No)")	
		if var=="Yes":			
			clean( cleaner['runs'] )
			clean( cleaner['results'] )
 			printer.info( header, "Done." )
		else:
			printer.info( header, "cancelled" )
		# end exit	
		sys.exit(0)	
	
	delta=None
	since=None
	to=datetime.now()

	if args.keys().count('since') !=0 :
		since=parser.parse(args['since'])
	if args.keys().count('to') !=0 :
		to=parser.parse(args['to'])
	
	if since:
		delta = to-since
	else:
		delta = to - datetime(1973,05,02)
		since = 'origin'
		
		
	if 	args.keys().count('apps') == 0 and  \
		args.keys().count('nets') == 0 and  \
		args.keys().count('filesys') == 0 and  \
		args.keys().count('synths') == 0 :
	
		if args.keys().count('d') == 0 :
			dir = cleaner['runs'] + "/"
			cleanup(dir,since,to,delta)
			dir = cleaner['results'] + "/"
			cleanup(dir,since,to,delta)
		else:
			dir = cleaner[args['d']] + "/"
			cleanup(dir,since,to,delta)

	else:	
		if args.keys().count('apps') != 0 :
			if args['apps'].lower() == "all":
				if args.keys().count('d') == 0:
					dir = cleaner['runs'] + "/apps/"
					cleanup(dir,since,to,delta)
					dir = cleaner['results'] + "/apps/"
					cleanup(dir,since,to,delta)
				else:
					dir = cleaner[args['d']] + "/apps/"
					cleanup(dir,since,to,delta)
			else:	
				if args.keys().count('d') == 0:
					dir = cleaner['runs'] + "/apps/" + args['apps'] + "/"
					cleanup(dir,since,to,delta)
					dir = cleaner['results'] + "/apps/" + args['apps'] + "/"
					cleanup(dir,since,to,delta)
				else:
					dir = cleaner[args['d']] + "/apps/" + args['apps'] + "/"
					cleanup(dir,since,to,delta)

		if args.keys().count('nets') != 0 :
			if args['nets'].lower() == "all":
				if args.keys().count('d') == 0:
					dir = cleaner['runs'] + "/networks/"
					cleanup(dir,since,to,delta)
					dir = cleaner['results'] + "/networks/"
					cleanup(dir,since,to,delta)
				else:
					dir = cleaner[args['d']] + "/networks/"
					cleanup(dir,since,to,delta)
			else:	
				if args.keys().count('d') == 0:
					dir = cleaner['runs'] + "/networks/" + args['nets'] + "/"
					cleanup(dir,since,to,delta)
					dir = cleaner['results'] + "/networks/" + args['nets'] + "/"
					cleanup(dir,since,to,delta)
				else:
					dir = cleaner[args['d']] + "/networks/" + args['nets'] + "/"
					cleanup(dir,since,to,delta)


		if args.keys().count('filesys') != 0 :
			if args['filesys'].lower() == "all":
				if args.keys().count('d') == 0:
					dir = cleaner['runs'] + "/filesystems/"
					cleanup(dir,since,to,delta)
					dir = cleaner['results'] + "/filesystems/"
					cleanup(dir,since,to,delta)
				else:
					dir = cleaner[args['d']] + "/filesystems/"
					cleanup(dir,since,to,delta)
			else:	
				if args.keys().count('d') == 0:
					dir = cleaner['runs'] + "/filesystems/" + args['filesys'] + "/"
					cleanup(dir,since,to,delta)
					dir = cleaner['results'] + "/filesystems/" + args['filesys'] + "/"
					cleanup(dir,since,to,delta)
				else:
					dir = cleaner[args['d']] + "/filesystems/" + args['filesys'] + "/"
					cleanup(dir,since,to,delta)

		if args.keys().count('synths') != 0 :
			if args['synths'].lower() == "all":
				if args.keys().count('d') == 0:
					dir = cleaner['runs'] + "/synthetics/"
					cleanup(dir,since,to,delta)
					dir = cleaner['results'] + "/synthetics/"
					cleanup(dir,since,to,delta)
				else:
					dir = cleaner[args['d']] + "/synthetics/"
					cleanup(dir,since,to,delta)
			else:	
				if args.keys().count('d') == 0:
					dir = cleaner['runs'] + "/synthetics/" + args['synths'] + "/"
					cleanup(dir,since,to,delta)
					dir = cleaner['results'] + "/synthetics/" + args['synths'] + "/"
					cleanup(dir,since,to,delta)
				else:
					dir = cleaner[args['d']] + "/synthetics/" + args['synths'] + "/"
					cleanup(dir,since,to,delta)



