#!/usr/bin/env python
# coding: utf-8

######################################################
#
#  Log Class 
#
######################################################
class Log(object):
	""" Singleton class to print out with fancy colors """

	_instance = None
	def __new__(cls, *args, **kwargs):
		if not cls._instance:
			cls._instance = super(Log, cls).__new__(cls, *args, **kwargs)
		return cls._instance

	# Some colors to print 
	LError="\033[0;41m" # red
	LBold="\033[1;42m" 	# green	
	#LData="\033[1;46m"	# light blue
	LData="\033[1;90m"	# light blue
	LInfo="\033[1;94m"  # blue	
	LWarning="\033[0;43m" # orange
	LEnd="\033[0;0m" # End string
	
	#######################################
	# class members
	Level = 0
	@staticmethod
	def bold(str):
		return Log.LBold + str + Log.LEnd
	#######################################
	
	####################################### 	
	# Private methods
	def __printout(self,header,message=None,color=None ):
		for i in range (0 ,Log.Level):
			print "\t",	
		#Log.Level = 0	
		if message :
			if color:
				print color + header + ":" + Log.LEnd + " " + message 
			else:
				print header + ": " + message 
		else:
			if color:
				print  color + header + Log.LEnd 
			else:
				print header 		
	####################################### 	
	
	#
	# Methods
 	#
	
	def plain(self, header, message=None):
		self.__printout(header,message)
			
	def warning( self, header, message=None):
		color = Log.LWarning
		self.__printout(header,message,color)
	
	def log( self,header, message=None):
		color = ""
		if Log.Level == 0 :
			color = Log.LInfo  
		elif Log.Level%2 != 0:
			color = Log.LData
		elif Log.Level%2 == 0:
			color = Log.LInfo
			
		self.__printout(header,message,color)
		
	def  error( self, header,message=None):
		color = Log.LError
		self.__printout(header,message,color)


logger = Log()		
		    