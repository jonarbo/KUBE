#!/usr/bin/env python
# coding: utf-8
import sys, os

class Logger(object):
	_instance = None
	def __new__(cls, *args, **kwargs):
		if not cls._instance:
			cls._instance = super(Logger, cls).__new__(cls, *args, **kwargs)
		return cls._instance
    
	def __init__(self, filename="kube.log"):
		self.terminal = sys.stdout
		try:
			self.log = open(filename, "a")
		except  IOError as e:
			print "I/O error({0}): {1}".format(e.errno, e.strerror)
			sys.exit(e.errno) 

	def write(self, message):
		self.terminal.write(message)
		self.log.write(message)

	@staticmethod		
	def getInstance():
		return Logger._instance
		


######################################################
#
#  Printer Class 
#
######################################################
class Printer(object):
	""" Singleton class to print out with fancy colors """

	_End="\033[0;0m" # End string
	_theme = None
	_themeName =''
	_instance = None
	_log = None
	def __new__(cls, *args, **kwargs):
		if not cls._instance:
			cls._instance = super(Printer, cls).__new__(cls, *args, **kwargs)
			cls._themeName = 'WhiteOnBlack' 
			cls._theme = Printer._Themes[cls._themeName  ] 
			cls.Level = 0
			cls._log = None
		return cls._instance

	# Decorator to make this class loggable to file	
	def __loggable(f):
		def inner(*args,**kwargs):
			if Printer._log:
				if not Logger.getInstance():
					sys.stdout = Logger(Printer._log)
				if f.__name__ == 'bold':
					return str(args[0])
				elif f.__name__ != None:
					if kwargs.keys().count('color')!=0:
						kwargs['color'] = None				
					f(*args,**kwargs)
			else:
				logger = Logger.getInstance()
				if logger:
					del logger
				if f.__name__ == 'bold':
					return f(str(args[0]))				
				else:
					f(*args,**kwargs)				
		return inner			
	
	#######################################
	# class members
	Level = 0
	_Themes={\
			'None':{
				'Error':"\033[1m",   \
				'Bold':"\033[1m",    \
				'Info':"\033[1m",    \
				'Warning':"\033[1m", \
			},\
			'WhiteOnBlack' : {\
				'Error':"\033[0;41m",   # red\  
				'Bold':"\033[1m",    \
				#'Bold':"\033[1;42m",    # green\	
				'Info':"\033[1;94m",    # blue\
				'Warning':"\033[0;43m", # orange\
			 }
		  }
	@staticmethod
	@__loggable
	def bold(str):
		return Printer._theme['Bold'] + str + Printer._End

	@staticmethod
	def setLogfile(logfile=None):
		Printer._log = logfile 

	#######################################
	
	def getCurrentTheme(self):
		return Printer._themeName
		
	def setCurrentTheme(self,name):
		if not name in Printer._Themes.keys():
			print "\'" + name + "\' not a theme"
		else:
			Printer._themeName = name
			Printer._theme = Printer._Themes[Printer._themeName] 

	####################################### 	
	# Private methods
	@__loggable
	def __printout(self,header,message=None,wait=None,color=None ):
		for i in range (0 ,Printer.Level):
			print "\t",	

		if message :
			if color:
				if wait:
					print color + header + ":" + Printer._End + " " + message ,
				else:
					print color + header + ":" + Printer._End + " " + message 
			else:
				if wait:
					print header + ": " + message ,
				else:
					print header + ": " + message 
		else:
			if color:
				if wait:
					print  color + header + Printer._End ,
				else:
					print  color + header + Printer._End 
			else:
				if wait:
					print header,
				else:
					print header				
	####################################### 	
	
	#
	# Methods
 	#
	def plain(self, header, message=None,wait=None):
		self.__printout(header,message,wait)
			
	def warning( self, header, message=None,wait=None):
		tcolor = Printer._theme['Warning']
		self.__printout(header,message,wait,color=tcolor)
	
	def info( self,header, message=None,wait=None):
		tcolor = Printer._theme['Info']
		self.__printout(header,message,wait,color=tcolor)
		
	def  error( self, header,message=None,wait=None):
		tcolor = Printer._theme['Error']
		self.__printout(header,message,wait,color=tcolor)


printer = Printer()		
		    