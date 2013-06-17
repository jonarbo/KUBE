#!/usr/bin/env python
# coding: utf-8

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
	def __new__(cls, *args, **kwargs):
		if not cls._instance:
			cls._instance = super(Printer, cls).__new__(cls, *args, **kwargs)
			cls._themeName = 'WhiteOnBlack' 
			cls._theme = Printer._Themes[cls._themeName  ] 
			cls.Level = 0
		return cls._instance
	
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
	def bold(str):
		return Printer._theme['Bold'] + str + Printer._End
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
	def __printout(self,header,message=None,color=None,wait=None ):
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
		color = Printer._theme['Warning']
		self.__printout(header,message,color,wait)
	
	def info( self,header, message=None,wait=None):
		color = Printer._theme['Info']
		self.__printout(header,message,color,wait)
		
	def  error( self, header,message=None,wait=None):
		color = Printer._theme['Error']
		self.__printout(header,message,color,wait)


printer = Printer()		
		    