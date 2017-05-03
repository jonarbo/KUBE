#!/usr/bin/env python
# coding: utf-8

import os, inspect, subprocess, shlex
from datetime import datetime , timedelta
from dateutil import parser
from kube.printer import *

######################################################
#
#  utility functions 
#
######################################################
def clean(dir,removeDir=False):
	"""Function that removes 'dir' and sub-directories inside 'dir'"""
	printer=Printer()
	printer.info("deleting" , dir)

	if not os.path.isdir(dir):
		return 	
	for d in os.listdir(dir):
		if os.path.isdir(dir+"/"+d) == True:
			clean(dir+"/"+d)
			os.rmdir( dir +"/"+d)	
		else:
			os.remove(dir+"/"+d) 			
	if removeDir == True:
		os.rmdir( dir ) 	

def syscall(str, wait=True  ):	
	"""Wrapper function to make a system call where pipes are allowed"""
  	cmds = str.split("|")
	cmds = list(map(shlex.split,cmds))
	# run the commands
	stdout_old = None
	stderr_old = None
	p = []
	try:
		for cmd in cmds:
			p.append(subprocess.Popen(cmd,stdin=stdout_old,stdout=subprocess.PIPE,stderr=subprocess.PIPE))
			stdout_old = p[-1].stdout
			stderr_old = p[-1].stderr
		if wait:
			return p[-1].communicate()
	except:
		e = sys.exc_info()[0]
		printer.error("Call error","There was an error executing '"+ str +"'" )
		print e
		sys.exit(1)	

def frange(start, end=None, inc=None):
    """A range function, that does accept float increments..."""
    import math

    if end == None:
        end = start + 0.0
        start = 0.0
    else: start += 0.0 # force it to be a float

    if inc == None:
        inc = 1.0
    count = int(math.ceil((end - start) / inc))

    L = [None,] * count

    L[0] = start
    for i in xrange(1,count):
        L[i] = L[i-1] + inc
    return L
    
def walkDir(dir,to=None,delta=None):
	for dirname, dirnames, file in os.walk(dir):
		for  subdirname in dirnames:
			dname = os.path.join(dirname, subdirname) 		
			if to!=None and delta!=None:
				try:						
					td = to-parser.parse( os.path.basename(dname) )
					if td>=timedelta(0) and td<=delta :
						yield dname
				except Exception as x :
					pass
			else:
				yield dname	
