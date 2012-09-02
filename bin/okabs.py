#!/usr/bin/python

# import system issues
import sys
import os, inspect
import optparse
import re
import shutil
import datetime, time
import subprocess	
import shlex
import math

# get the path to the current script
cmd_folder = os.path.abspath(os.path.split(inspect.getfile( inspect.currentframe() ))[0])

######################################################
#
#  utility functions 
#
######################################################
def clean(dir):
	"""Function that removes 'dir' and sub-directories inside 'dir'"""
	for d in os.listdir(dir):
		if os.path.isdir(dir+"/"+d) == True:
			clean(dir+"/"+d)
			os.rmdir( dir +"/"+d)	
		else:
			os.remove(dir+"/"+d) 			

def syscall(str):	
	"""Wrapper function to make a system call where pipes are allowed"""
  	cmds = str.split("|")
	cmds = list(map(shlex.split,cmds))
	# run the commands
	stdout_old = None
	stderr_old = None
	p = []
	for cmd in cmds:
		p.append(subprocess.Popen(cmd,stdin=stdout_old,stdout=subprocess.PIPE,stderr=subprocess.PIPE))
		stdout_old = p[-1].stdout
		stderr_old = p[-1].stderr
	return p[-1].communicate()

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
   
######################################################
#
#  Log Class 
#
######################################################
class Log:
	# Some colors to print 
	LError="\033[0;41m" # red
	LBold="\033[1;42m" 	# green	
	#LData="\033[1;46m"	# light blue
	LData="\033[1;90m"	# light blue
	LInfo="\033[1;94m"  # blue	
	LWarning="\033[0;43m" # orange
	LEnd="\033[0;0m" # End string
	
	Level = 0

	def bold(self,str):
		return Log.LBold + str + Log.LEnd

	def __printout(self,color,header,message=None ):
		for i in range (0 ,Log.Level):
			print "\t",	
		Log.Level = 0	
		if message :
			print color + header + ":" + Log.LEnd + " " + message 
		else:
			print  color + header + Log.LEnd 
	
	def plain(self,  header, message=None):
		for i in range (0 ,Log.Level):
			print "\t",	
		Log.Level = 0	
		if message :
			print  header + ":" + " " + message 
		else:
			print header 
			
	def warning(self,  header, message=None):
		color = Log.LWarning
		self.__printout(color, header,message)
	
	def log(self, header, message=None):
		color = ""
		if Log.Level == 0 :
			color = Log.LInfo  
		elif Log.Level%2 != 0:
			color = Log.LData
		elif Log.Level%2 == 0:
			color = Log.LInfo
			
		self.__printout(color, header,message)
		
	def  error(self, header,message=None):
		color = Log.LError
		self.__printout(color,header,message)
		
		    
######################################################
#
#  main Class 
#
######################################################
class KABS:
	
	##################
	# Class variables
	
	LIB_DIR = cmd_folder + "/../lib"
	CONF_FILE_PATH = cmd_folder + "/../etc/"
	CONF_FILE_NAME = "kabs.yaml"
	# Some colors to print 
#	L0="\033[1m"  # Bold
	L0="\033[0;40m"  # Bold
	L1="\033[94m" # Blue 
	L2="\033[92m" # Green
	LE="\033[0;0m" # End string

	def __substituteVarsInBatch_NONE(self):
		""" The 'NONE' batch system should be very flexible. For that reason inside the 'submit' tag,
			any field can use references to any tag defined in the NONE batch definition.
			This function does the replacement. References to dataset specific tags such as 
			%NUMPROCS% are also allowed but those are replaced later on when the submission script is created.
		"""
		# Replace inline variables in batch: NONE section	
		for batch in self.batchs: 	
			if batch['name'] == "NONE":
				str2find = {}
				for nkey in batch.keys():
					str2find[nkey]= "%"+ nkey.upper() +"%"
				for sstr in str2find.keys():
					reple = re.compile( str2find[sstr] );
					for nkey2 in batch.keys():
						if isinstance(batch[nkey2],dict) and not isinstance(batch[sstr],dict):
							for elem in batch[nkey2]:
								batch[nkey2][elem] = reple.sub(batch[sstr],batch[nkey2][elem])		
				break;
	
	def __substituteVarsInSection_analysis(self,item):
		""" Inside a dataset; the ['analysis']['outputs'] fields may contain references to fields defined
			in the app. ie: one output name might contain the number of cpus used in the run.
			Additionally, the ['analysis']['metrics'] elements may contain references to the outputs names defined above.
			So, this function does this replacements of the references to the right values. The convention used
			for a reference is %FIELD_NAME_IN_CAPITALS%	"""
		# Replace inline variables in the ['analysis']['outputs'] section inside each dataset
		#for appname in self.a_apps.keys():
		for name in item.keys():	
#			for dataset in self.a_apps[appname]:
			for dataset in item[name]:
				str2find = {}
				for nkey in dataset.keys():
					if nkey!='analysis' : 
						str2find[nkey]= "%"+ nkey.upper() +"%"		
				for sstr in str2find.keys():
					reple = re.compile( str2find[sstr] )	
					ndatasetsstr = re.sub(r'\s', '', unicode(dataset[sstr]) )	# security ... just remove all white spaces		
					if 	len(ndatasetsstr.split(','))<2 : # there is not a comma separated list:
						for outpkey in dataset['analysis']['outputs'].keys():
							dataset['analysis']['outputs'][outpkey] = reple.sub(ndatasetsstr,dataset['analysis']['outputs'][outpkey])		
					else: # there is a comma separated list,so we have to create an entry for every value (ie: numprocs could be a comma separated list)
						values = ndatasetsstr.split(',')
						for outpkey in dataset['analysis']['outputs'].keys():
							if reple.search( dataset['analysis']['outputs'][outpkey] ) : # there is a match
								for value in values: # create an entry for each value	 
									dataset['analysis']['outputs']['#'+str(value)+'#'+outpkey] = reple.sub(value,dataset['analysis']['outputs'][outpkey])
								# and delete previous entry ..
								del dataset['analysis']['outputs'][outpkey]	
							else:
								# Do nothing ...
								pass
								
		# Replace inline variables in the ['analysis']['metrics'] section inside each dataset
		for name in item.keys():	
			for dataset in item[name]:
				str2find = {}
				for nkey in dataset['analysis']['outputs'].keys():
					str2find[nkey]= "%"+ nkey.upper() +"%"
				for sstr in str2find.keys():
					reple = re.compile( str2find[sstr] );
					for metric in dataset['analysis']['metrics']:
						for elem in metric:
							metric[elem] = reple.sub(dataset['analysis']['outputs'][sstr],metric[elem])									
			



	def __readApps(self,yaml_conf):
		""" Reads APPS section and do some error check """
		# set self.apps
		self.apps = yaml_conf['KaBS']['BENCH']['APPS'] # Array of dictionaries with apps info: active, exe, name, etc...		
		# sanity check
		repeat=True
		while repeat:
			repeat = False				
			for app in self.apps:
				if  app.keys().count('name')==0 or \
					app.keys().count('active')==0:
					#print "Config file error: 'active' and 'name' are mandatory fields within an APP ... Skipping this entry"
					self.log.error("Config file error","'active' and 'name' are mandatory fields within an APP ... Skipping this entry")
					self.apps.remove(app)
					repeat = True
				else:
					if app['active'] and ( app.keys().count('dataset')==0 or app.keys().count('batch')==0 or app.keys().count('exe')==0  ):
						#print "Config file error: 'dataset', 'exe' and 'batch' fields are required for any active APP: " + app['name'] + " ... Skipping this entry"
						self.log.error("Config file Error"," 'dataset', 'exe' and 'batch' fields are required for any active APP: " + self.log.bold(app['name']) + " ... Skipping this entry")
						self.apps.remove(app)
						repeat = True		

		# set i_apps and self.a_apps
		self.i_apps = [ app['name'] for app in self.apps if not app['active'] ]	# List with the name of the inactive apps
		self.a_apps = dict( [ (app['name'],app['dataset']) for app in self.apps if app['active'] ]) # Dictionary Name->Array of datasets  of active apps
		
		# update self.a_apps and remove inactive datasets... also if there is no active dataset remove app from the list of active apps
		repeatf = True
		while repeatf:
			repeatf = False
			for napp in self.a_apps.keys():			
				repeat = True
				while repeat:
					repeat = False
					for dataset in self.a_apps[napp]:
						if dataset.keys().count('name')==0 or dataset.keys().count('active')==0:
							#print "Config file error: 'name' and 'active' fields are required for any dataset in app: " + napp + ".\nSkipping this dataset"
							self.log.error("Config file error","'name' and 'active' fields are required for any dataset in app: " + self.log.bold(napp) + " ... Skipping this dataset")
							self.a_apps[napp].remove(dataset)
							repeat = True
						elif dataset['active'] != True:
							self.a_apps[napp].remove(dataset)
							repeat = True
						elif dataset.keys().count('analysis')==0:
							#print "Config file error: 'analysis' field is required for any active dataset in app: " + napp + ".\nSkipping this dataset"
							self.log.error("Config file error"," 'analysis' field is required for any active dataset in app: " + self.log.bold(napp) + " ... Skipping this dataset")
							self.a_apps[napp].remove(dataset)
							repeat = True
													
				if len( self.a_apps[napp] ) == 0:
					del(self.a_apps[napp])
					repeatf = True
	
		# populate self.apps with the batch parameters if they are not already set in the app:
		for appname in self.a_apps.keys():	
			for a in self.apps:	
				if a['name'] == appname:	 			
					for batch in self.batchs: 
						if batch['name'] == a['batch']:
							for key in batch.keys():
								if key!="name" and key!="script" and key!="monitor" and key!="submit" and a.keys().count(key)==0 :
									a[key] = batch[key]				
							break # step out the batch loop
					break # step out self.apps loop
					
		# populate self.a_apps -> datasets with the app parameters if they are not already set in the dataset:			
		for appname in self.a_apps.keys():	
			for dataset in self.a_apps[appname]:
				for a in self.apps:	
					if a['name'] == appname:	
						for sk in a.keys():
							if sk=="batch": # Force the dataset to use always the batch system defined  for the app
											# the 'batch' parameter is global to the app, not dataset specific 
								dataset[sk] = a[sk]
							elif  dataset.keys().count(sk)==0 and sk!="name" and sk!="dataset" and sk!="active" :
								if a[sk] != None:
									dataset[sk] = a[sk] 
								else:
									dataset[sk] = "" 		
														
						if dataset.keys().count('numprocs')==0 or dataset.keys().count('tasks_per_node')==0:
							#print "Config file error: Dataset of " + appname + " found without 'numprocs' and/or 'tasks_per_node' defined. This tags are mandatory!!!\nPlease revise your configuration file" 
							self.log.error("Config file error"," Dataset of " + self.log.bold(appname) + " found without 'numprocs' and/or 'tasks_per_node' defined. This tags are mandatory!!!") 
							self.log.error("Please revise your configuration file !!!")
							sys.exit(1)	
						break # step out apps loop

		self.__substituteVarsInSection_analysis(self.a_apps)
	
	def __readSynthetic(self,yaml_conf):
		""" Reads Synthetic section and do some error check """
		# set self.synths
		self.synths = yaml_conf['KaBS']['BENCH']['SYNTHETIC'] # Array of dictionaries with synthetic bench info: active, exe, name, etc...
		self.__sanityBasic(self.synths,"Synthetic")
		#set active Synthetics:
		self.a_synths = dict( [ (synth['name'],synth['dataset']) for synth in self.synths if synth['active'] ]) # Dictionary Name->Array of datasets  of active networks
		# update self.a_synths and remove inactive datasets ... also if there is no active dataset remove synthetic from the list of active items
		self.__updateActiveElements(self.a_synths,"Synthetic")
		self.__populateElements(self.a_synths, self.synths)
		self.__substituteVarsInSection_analysis(self.a_synths)

	
	def __readNets(self,yaml_conf):
		""" Reads Networks section and do some error check """
		# set self.nets
		self.nets = yaml_conf['KaBS']['BENCH']['NETWORKS'] # Array of dictionaries with nets info: active, exe, name, etc...
		self.__sanityBasic(self.nets,"Network")
		#set active networks:
		self.a_nets = dict( [ (net['name'],net['dataset']) for net in self.nets if net['active'] ]) # Dictionary Name->Array of datasets  of active networks
		# update self.a_nets and remove inactive datasets ... also if there is no active dataset remove network from the list of active networks
		self.__updateActiveElements( self.a_nets ,"Networks")
		self.__populateElements(self.a_nets ,self.nets)
		self.__substituteVarsInSection_analysis(self.a_nets)

	def __sanityBasic(self,elems,mstr):
		# sanity check 
		repeat=True
		while repeat:
			repeat = False				
			for elem in elems:
				if  elem.keys().count('name')==0 or \
					elem.keys().count('active')==0:
					self.log.error("Config file error","'active' and 'name' are mandatory fields within item: " + mstr +" ... Skipping this entry")
					self.elems.remove(elem)
					repeat = True
				else:
					if elem['active'] and ( elem.keys().count('dataset')==0 or elem.keys().count('batch')==0  ):
						self.log.error("Config file Error"," 'dataset', and 'batch' fields are required for any active "+mstr+": " + self.log.bold(net['name']) + " ... Skipping this entry")
						self.elems.remove(elem)
						repeat = True					
		
	def __updateActiveElements(self,a_elems,mstr):	
		repeatf = True
		while repeatf:
			repeatf = False
			for elem in a_elems.keys():			
				repeat = True
				while repeat:
					repeat = False
					for dataset in a_elems[elem]:
						if dataset.keys().count('name')==0 or dataset.keys().count('active')==0:
							self.log.error("Config file error","'name' and 'active' fields are required for any dataset in "+ mstr +": " + self.log.bold(elem) + " ... Skipping this dataset")
							a_elems[elem].remove(dataset)
							repeat = True
						elif dataset['active'] != True:
							a_elems[elem].remove(dataset)
							repeat = True
						elif dataset.keys().count('analysis')==0:							
							self.log.error("Config file error"," 'analysis' field is required for any active dataset in " + mstr + ": " + self.log.bold(elem) + " ... Skipping this dataset")
							a_elems[elem].remove(dataset)
							repeat = True
													
				if len( a_elems[elem] ) == 0:
					del(a_elems[elems])
					repeatf = True

	def	__populateElements(self,a_elems,elems):
		# populate self.XXX with the batch parameters if they are not already set in the XXX entry:
		for aname in a_elems.keys():	
			for a in elems:	
				if a['name'] == aname:	 			
					for batch in self.batchs: 
						if batch['name'] == a['batch']:
							for key in batch.keys():
								if key!="name" and key!="script" and key!="monitor" and key!="submit" and a.keys().count(key)==0 :
									a[key] = batch[key]				
							break # step out the batch loop
					break # step out self.apps loop				
		# populate self.a_XXX -> datasets with the XXX parameters if they are not already set in the dataset:			
		for aname in a_elems.keys():	
			for dataset in a_elems[aname]:
				for a in elems:	
					if a['name'] == aname:	
						for sk in a.keys():
							if sk=="batch": # Force the dataset to use always the batch system defined  for the network
											# the 'batch' parameter is global to all the network datasets 
								dataset[sk] = a[sk]
							elif  dataset.keys().count(sk)==0 and sk!="name" and sk!="dataset" and sk!="active" :
								if a[sk] != None:
									dataset[sk] = a[sk] 
								else:
									dataset[sk] = "" 		
														
						if dataset.keys().count('numprocs')==0 or dataset.keys().count('tasks_per_node')==0:							
							self.log.error("Config file error"," dataset of " + self.log.bold(aname) + " found without 'numprocs' and/or 'tasks_per_node' defined. This tags are mandatory!!!") 
							self.log.error("Please revise your configuration file !!!")
							sys.exit(1)	
						break # step out 'a' loop		


	def __readYaml(self, yaml_conf):
		"""Parse the yaml_conf structure and reads the configuration variables needed. Also do some basic correctness and sanity check"""	
		# some basic error correctness
		if yaml_conf.keys().count('KaBS') ==0:
			#print "Config file error: KaBS head tag is not defined" 
			self.log.error("Config file error", "KaBS head tag is not defined") 
			sys.exit(1)	
		if yaml_conf['KaBS'].keys().count("HOME") == 0 or \
		   yaml_conf['KaBS'].keys().count("OUTPUTS") == 0 or \
		   yaml_conf['KaBS'].keys().count("BATCH") == 0 or \
		   yaml_conf['KaBS'].keys().count("BENCH") == 0:
			#print "Config file error: HOME, OUTPUTS, BATCH and BENCH must be defined" 
			self.log.error("Config file error","HOME, OUTPUTS, BATCH and BENCH must be defined")
			sys.exit(1)			

		#######################################################################################
		# Set important variables
		
		# set home
		self.home = yaml_conf['KaBS']['HOME']
		if self.home == None: 
			#print "Config file error: HOME must be defined" 
			self.log.error("Config file error","HOME must be defined")
			sys.exit(1) 

		#set outputs
		self.output_dir = yaml_conf['KaBS']['OUTPUTS']
		if re.match("[^/]",self.output_dir):
			self.output_dir = self.home + "/" + self.output_dir
		
		# set batchs
		self.batchs = yaml_conf['KaBS']['BATCH']
		if self.batchs==None:
			#print "Config file error: at least one BATCH must be defined" 
			self.log.error("Config file error","at least one BATCH must be defined")
			sys.exit(1)	
		# set absolute path to the scripts and do some error check
		for nbatch in self.batchs:
			if nbatch.keys().count('name')==0 or nbatch.keys().count('submit')==0:
				#print "Config file error: 'name' and 'submit' tags are mandatory in the BATCH" 
				self.log.error("Config file error"," 'name' and 'submit' tags are mandatory in the BATCH" )
				sys.exit(1)
			if nbatch['submit'] == None : 
				self.log.error("Config file error","'submit' tag in one of your BATCHs is empty")
				#print "Config file error: 'submit' tag in one of your BATCHs is empty" 				
				sys.exit(1)	
			if  str(nbatch['name']) != "NONE" and nbatch['name']!=None:
				if  nbatch.keys().count('script')==0:
					#print "Config file error: 'script' tag is mandatory in an a BATCH unless you name it as 'NONE'" 
					self.log.error("Config file error"," 'script' tag is mandatory in an a BATCH unless you name it as 'NONE'")
					sys.exit(1)
				if nbatch['script']!=None:
					if re.match("[^/]",nbatch['script']):
						nbatch['script'] = self.home + "/etc/" + nbatch['script']
				else:
					#print "Config file error: Missing 'script' in one of your non 'NONE' BATCHs" 
					self.log.error("Config file error","Missing 'script' in one of your non 'NONE' BATCHs")
					sys.exit(1)			
			else:
				if nbatch['name']==None:
					#print "Config file error: Missing 'name' in one of your BATCHs" 
					self.log.error("Config file error","Missing 'name' in one of your BATCHs")
					sys.exit(1)	
		
		# Verify that the main tags ni BENCH section exist
		if (yaml_conf['KaBS']['BENCH'].keys().count('APPS') == 0) or \
			(yaml_conf['KaBS']['BENCH'].keys().count('FILESYSTEM') == 0) or \
			(yaml_conf['KaBS']['BENCH'].keys().count('MATHLIBS') == 0) or \
			(yaml_conf['KaBS']['BENCH'].keys().count('NETWORKS') == 0) or \
			(yaml_conf['KaBS']['BENCH'].keys().count('SYNTHETIC') == 0) or \
			(yaml_conf['KaBS']['BENCH'].keys().count('ACCEPTANCE') == 0):		
			#print "Config file error: 'APPS','FILESYSTEM','MATHLIBS','NETWORKS','SYNTHETIC','ACCEPTANCE' tags are mandatory inside BENCH" 
			self.log.error("Config file error","'APPS','FILESYSTEM','MATHLIBS','NETWORKS','SYNTHETIC','ACCEPTANCE' tags are mandatory inside BENCH")
			sys.exit(1)	
			
		# and fill each one if them:	
		self.__readApps(yaml_conf)
		self.__readNets(yaml_conf)
		self.__readSynthetic(yaml_conf)			
											
		# End setting variables
		########################################################################################
		
				
		
	def __getBatchSystem(self,whichapp):	 # parameter can be a dataset or an app since it holds the same values.
		""" Returns the batch object for a specific dataset or app
		"""
		for batch in self.batchs:
			if batch['name'] == whichapp['batch']:
	 			return batch 		
		return None	 			
		
				
		
	def __getBatchScript(self,whichdataset,p):
		""" Returns the batch script or the submission command for a specific dataset and cpu number
			Here takes place the final fields reference replacements: Any left reference in the batch script or a submission command
			to the tags in a dataset will be done here
		"""
		batch =  self.__getBatchSystem(whichdataset)	
		if batch != None and batch['name'] != "NONE":
			submit_script = batch['script']
			file = open(submit_script,'r')
			data = file.read()
			file.close()		
		else:
			# TODO: what happens when there is no batch system
			# Get manual submission command:
			if whichdataset.keys().count('args') != 0:  # other values should be mandatory and checked when file correctness is executed
				data =  str(batch['submit']['command']) + " " + str(batch['submit']['parameters'] )+ " " + str(whichdataset['exe'] )+ " " + str(whichdataset['args'] )
			else:
				data =  str(batch['submit']['command']) + " " + str(batch['submit']['parameters'] )+ " " + str(whichdataset['exe'] )
			
		# replace variables
		for litem in  whichdataset:
			str2find = "%("+ str(litem).upper() +")%"
			prog = re.compile(str2find);
			if litem != 'numprocs':
					data = prog.sub( str(whichdataset[litem]) ,data)	
			else:
				data = prog.sub( str(p) ,data)		
				
		return data	
			
		
		
			
	def __printAppsInfo(self,which=None):
		""" Prints out configuration information for a specific app or for All apps
		"""
		if which==None: # means ALL
			#print "\t"+KABS.L0+"Inactive Apps:" + KABS.LE,
			Log.Level = 1
			self.log.log("Inactive Apps", str(self.i_apps) )
			#print self.i_apps
			#print "\t"+KABS.L0+"Active Apps:" + KABS.LE 
			Log.Level = 1
			self.log.log("Active Apps"," " )
			for k in self.a_apps.keys():
				#print "\t\t"+ KABS.L1+ k  + KABS.LE + " with:"
				Log.Level = 2
				#self.log.data(k,"with ..." )
				self.log.log(k,"with ..." )
				for l in range(len(self.a_apps[k])):
					#print "\t\t\tdataset: "+KABS.L1 + str( self.a_apps[k][l]['name']) + KABS.LE 
					Log.Level =3
					#self.log.data("dataset",str( self.a_apps[k][l]['name']))
					self.log.log("dataset",str( self.a_apps[k][l]['name']))
					for litem in  self.a_apps[k][l]:
						if litem != 'name' and litem != 'analysis':
							#print "\t\t\t\t"+litem +": "+KABS.L1 + str( self.a_apps[k][l][litem]) + KABS.LE 
							Log.Level = 4
							#self.log.data(litem ,str( self.a_apps[k][l][litem])  )
							self.log.log(litem ,str( self.a_apps[k][l][litem])  )
		else:
			if self.a_apps.keys().count(which) == 0:
				#print "Application " + which  + " not found or not active"
				self.log.warning("Warning","Application " + self.log.bold(which)  + " not found or not active")
			else:
				for k in self.a_apps.keys():
					if which==k:
						mybatch=[]
						for tapp in self.apps:
						 if tapp['name'] == which:
							mybatch = self.__getBatchSystem(tapp)
						 	self.__printBatchSystemInfo(mybatch)
							self.__printDatasetInfo(self.a_apps[which])
						break;	
	
	def __printMathlibInfo(self):
		Log.Level = 1
		self.log.log("Math Libraries:")
		#self.__printBaseInfo( self.a_mathlibs, self.mathlibs, which)

				
	def __printFSInfo(self):
		#print "\t"+KABS.L0+"Filesysytems:"+KABS.LE
		Log.Level = 1
		self.log.log("Filesystems:")
		#self.__printBaseInfo( self.a_filesys, self.filesys, which)

	
	def __printSynthInfo(self,which=None):
		""" Prints out configuration information for a specific Synthetic benchmarks or for all synthetic benchmarks
		"""
		Log.Level = 1
		self.log.log("Synthetic:")
		self.__printBaseInfo( self.a_synths, self.synths, which)


	def __printNetInfo(self,which=None):
		""" Prints out configuration information for a specific app or for All apps
		"""
		Log.Level = 1
		self.log.log("Networks:")
		self.__printBaseInfo( self.a_nets, self.nets, which)
		
		
	def __printBaseInfo(self, who, all ,which):
		""" Prints out configuration common information for Network, Mathlibs, Filesystem and Synthetic benchmarks
		"""
		if which==None: # means ALL
			Log.Level =	 2
			for k in who.keys():
				self.log.log(k," " )
				for l in range(len(who[k])):
					Log.Level =3
					self.log.log("dataset",str( who[k][l]['name']))
					for litem in  who[k][l]:
						if litem == 'numprocs' or litem == 'tasks_per_node' or litem == 'exe' or litem == 'batch' :
							Log.Level = 4
							self.log.log(litem ,str( who[k][l][litem])  )
		else:
			if who.keys().count(which) == 0:
				#print "Application " + which  + " not found or not active"
				self.log.warning("Warning","Element " + self.log.bold(which)  + " not found or not active")
			else:
				for k in who.keys():
					if which==k:
						mybatch=[]
						for elem in all:
						 if elem['name'] == which:
							mybatch = self.__getBatchSystem(elem)					
							self.__printBatchSystemInfo(mybatch)
							self.__printDatasetInfo(who[which])							
						break;



	def __printDatasetInfo(self,which):
		for   dataset in which:
			nprocs = str(dataset['numprocs']).split(',')
			if len(nprocs) == 0:
				self.log.warning("Warning","No procs found ... dataset " + self.log.bold(str( dataset['name'] ))  +" skipped")
				continue
			for p in nprocs:
				self.log.plain("dataset: " + self.log.bold(str( dataset['name'] )) + " with " +  self.log.bold(p)  + " procs")
				self.log.log("Submission script:")
				data = self.__getBatchScript(dataset,p,)
				print data
				print "-------------------------------------------------"			
	
	
	
	
	def __printBatchSystemInfo(self,mybatch):
		submit_cmd = mybatch['submit']['command']
		submit_params = mybatch['submit']['parameters']	
		if  mybatch == None or mybatch['name'] == "NONE":
			# No batch system found .... 
			#print "No batch system specified for app: " + KABS.L1 + which + KABS.LE
			self.log.warning("Warning","No batch system specified for " + self.log.bold(which) )
			#print "Submission command: " 
			self.log.log("Submission command:")
			Log.Level = 1
			#self.log.data(submit_cmd +" " + submit_params )
			self.log.log(submit_cmd +" " + submit_params )
			#print "\t" + submit_cmd +" " + submit_params 	
		else:
			submit_script = mybatch['script']
			#print "Using "  + KABS.L1 + mybatch['name'] + KABS.LE + " for app: " + KABS.L1 + which + KABS.LE
			#self.log.plain("Using " + self.log.bold(str(mybatch['name'])) + " for " + self.log.bold(which) )
			self.log.plain("Using " + self.log.bold(str(mybatch['name']))+ " batch system" )
			#print "Submission command: "
			self.log.log("Submission command:")
			Log.Level = 1
			#print "\t" + submit_cmd +" " + submit_params # + " " + submit_script					
			#self.log.data(submit_cmd +" " + submit_params )
			self.log.log(submit_cmd +" " + submit_params )
		print "\n"
	
		
	def __printAcceptanceInfo(self):
		Log.Level = 1
		self.log.log("Acceptance:")


	def __analizeDataset(self,dataset,runsd,analysisd):
		rundir = runsd + dataset['name']	
		analysisdir = analysisd +dataset['name']
		if not os.path.exists(analysisdir):
			os.makedirs(analysisdir)
		# Analyze every run which is not already been analyzed
		runs = os.listdir(rundir)
		# now remove the known failure dirs
		repeat = True
		while repeat:
			repeat = False
			for r in runs:
				if re.match("FAILED_",r) !=	None:
					runs.remove(r)		
					repeat = True
					break		
		
		# This code eliminates the need to re-analyze  an already analyzed run ...
		# But I commented this because it could be useful to re-analyze a run because the user
		# might have changed the metrics configuration ... for example  			
# 		canalysis =  os.listdir(analysisdir)		
# 		if  len(canalysis)!=0:
# 			for a in canalysis:
# 				for r in runs:
# 					if r==a:
# 						# Found the same dataset in the analysis dir...
# 						# if it is not empty we will assume the analysis phase has been done
# 						if len(os.listdir( analysisdir+'/'+a ))!=0:
# 							runs.remove(r)
# 							break
							
		# now remove from the list the runs that are still running ...
		batch = self.__getBatchSystem(dataset)
		cmd = None		
		if batch.keys().count('monitor') != 0:
			cmd =  batch['monitor']
			if cmd != None:
				repeat = True
				while repeat:
					repeat = False
					for r in runs:
						files = os.listdir(rundir + "/" + r)
						for f in files:
							if re.match("batch.jobid",f) :
								jobid = re.search("\d+$",f).group(0)
								ncmd = re.sub("%JOBID%",jobid,cmd) 
								out,err = syscall( ncmd )	
								if out.strip()==jobid.strip():
									# the job is running ... remove it from the list
									runs.remove(r)
									repeat = True										
								break		
		u = runs			
		if len(u) == 0:
			#print "No new runs to analize"
			self.log.plain("No new runs to analize")	
			return
		# create analysis dir for each  run
		for i in u:
			os.chdir( analysisdir )
			if not os.path.exists(i):
				os.makedirs(i)
			os.chdir( i )
			
			#get the cpus from the run name:
			str2find = "_(\d+)cpus_"	
			reple = re.compile( str2find )
			mobj = reple.search(i)
			cpus = mobj.group(1)
			
			# Copy the outputs needed ...
			str2find = "^#(\d+)#"
			prog = re.compile(str2find);	
			for outp in  dataset['analysis']['outputs'].keys():
				failed = False
				mobj = prog.match(outp) 
				if mobj:
					if mobj.group(1)==cpus: 
						if os.path.isfile(rundir + "/" + i + "/" + dataset['analysis']['outputs'][outp]) :					
							shutil.copy( rundir + "/" + i + "/" + dataset['analysis']['outputs'][outp] , "./")
						else:
							#print "Warning: File " + KABS.L1 +  rundir + "/" + i + "/" + dataset['analysis']['outputs'][outp] + KABS.LE + " Does not exist.\nAnalysis not completed!!!"
							self.log.waring("Warning","File " + self.log.bold( rundir + "/" + i + "/" + str(dataset['analysis']['outputs'][outp]) ) + " Does not exist.")
							self.log.error("Analysis not completed!!!")
							failed = True
							break
				else:
					if os.path.isfile(rundir + "/" + i + "/" + dataset['analysis']['outputs'][outp]) :					
						shutil.copy( rundir + "/" + i + "/" + dataset['analysis']['outputs'][outp] , "./")
					else:
						#print "Warning: File " + KABS.L1 +  rundir + "/" + i + "/" + dataset['analysis']['outputs'][outp] + KABS.LE + " Does not exist.\nAnalysis not completed!!!"
						self.log.warning("Warning","File " + self.log.bold( rundir + "/" + i + "/" + str(dataset['analysis']['outputs'][outp]) ) + " Does not exist.")
						self.log.error("Analysis not completed!!!")
						failed = True
						break
			
				if failed == True:
					continue

				# now crate a .csv and the .raw file suitable to be used later on with gnuplot...
				START = 0.0
				END = 2*math.pi
				STEP =  END/len(dataset['analysis']['metrics'])	
				theta = frange(START,END,STEP)		
				radio = []	
				metrics = []
				o = open( "analysis.csv","w")
				o.write(  "\"metric\",\"value\",\"units\"\n" )
				for metric in dataset['analysis']['metrics']:
					o.write( "\"" +metric['name']+ "\"," + "\"" + syscall( metric['command'])[0].strip() +"\"" +"\"" + metric['units'] + "\"\n"  ) 
					radio.append ( syscall( metric['command'])[0].strip() )				
					metrics.append( metric['name'] )
				o.flush()
				o.close
				
				sort_dict = zip(metrics, theta, radio)		
								
				r = open( "analysis.raw","w")
				for k in sort_dict:
					r.write( str(k[0]) + "  "  + str(k[1]) + "  "  + str(k[2])   + "\n"  )
				r.write( str(sort_dict[0][0])	 + "  "  + str(sort_dict[0][1]) + "  "  + str(sort_dict[0][2])    + "\n"  )
				r.flush
				r.close		
		

	def __analysisSynthetic(self,name):
		synth = self.a_synths[name]
		analysisd = self.output_dir + "/analysis/synthetic/"+ name + "/"
		runsd = self.output_dir + "/runs/synthetic/"+ name + "/"
		if not os.path.exists(runsd):
			#print "Can't find any completed run for this app: " + KABS.L1+ name + KABS.LE
			self.log.error("Can't find any completed run for this synthetic: " + self.log.bold(name) )
			sys.exit(1)
		if not os.path.exists(analysisd):
			os.makedirs(analysisd)

		for dataset in net:	
			self.__analizeDataset(dataset,runsd,analysisd)		
	



	def __analysisNet(self,name):
		net = self.a_nets[name]
		analysisd = self.output_dir + "/analysis/networks/"+ name + "/"
		runsd = self.output_dir + "/runs/networks/"+ name + "/"
		if not os.path.exists(runsd):
			#print "Can't find any completed run for this app: " + KABS.L1+ name + KABS.LE
			self.log.error("Can't find any completed run for this network: " + self.log.bold(name) )
			sys.exit(1)
		if not os.path.exists(analysisd):
			os.makedirs(analysisd)

		for dataset in net:	
			self.__analizeDataset(dataset,runsd,analysisd)		
			



	def __analysisApp(self,name):
		"""  Performs the analysis stage for an app. Go into the runs dir and identify the app and the dataset.
			 then creates a similar entry in the 'results/analysis' dir  and copies the output files to the new location.
			 it also creates a .cvs and a .raw files with the metrics specified in the YAML config file. The .raw file is used later on
			 when visualizing the metric.
 		"""
		app = self.a_apps[name]
		analysisd = self.output_dir + "/analysis/apps/"+ name + "/"
		runsd = self.output_dir + "/runs/apps/"+ name + "/"
		if not os.path.exists(runsd):
			#print "Can't find any completed run for this app: " + KABS.L1+ name + KABS.LE
			self.log.error("Can't find any completed run for this app: " + self.log.bold(name) )
			sys.exit(1)
		if not os.path.exists(analysisd):
			os.makedirs(analysisd)

		for dataset in app:
			self.__analizeDataset(dataset,runsd,analysisd)


	def __runSynthetic(self, which):
		""" Run the given Synthetic whose name is specified
		"""
		synth = self.a_synths[which]
		source = self.home + "/bench/synthetic/"+ which + "/"
		target = self.output_dir + "/" + "runs/synthetic/" + which + "/"
		self.__runBasic(synth,source,target)
		

	def __runNet(self, which):
		""" Run the given Network whose name is specified
		"""
		net = self.a_nets[which]
		source = self.home + "/bench/networks/"+ which + "/"
		target = self.output_dir + "/" + "runs/networks/" + which + "/"
		self.__runBasic(net,source,target)
		
	
	def __runBasic(self,bench,source,target):
		for dataset in bench:
			self.log.plain( "\nDataset: " +  self.log.bold(dataset['name'] ) )
			if not os.path.exists(source):
				self.log.error("Dataset Error:","Could not find: " + s)
				sys.exit(1)        	
			t = target + dataset['name'] +"/"
			if not os.path.exists(t):
				os.makedirs(t)
				os.makedirs(t + dataset['name'])
			elif not os.path.exists(t+dataset['name']):
				os.makedirs(t+dataset['name'])
				
			cwd = os.getcwd()
			os.chdir(t)					
			# Copy input files if any
			files = ""
			if dataset.keys().count("dependencies") != 0:
				files = dataset['dependencies']
			inputs = str(files).split(',')
			for input in inputs:
				if input != 'None' :
					self.log.plain( "Copying dependency file: "+ self.log.bold( str(input) )  + " into run directory")
					# input is always relative to the 'source' directory
					if not os.path.exists( os.path.dirname("./" + dataset['name'] + '/'+ input )) :
						os.makedirs( os.path.dirname("./" + dataset['name'] + '/'+ input ) )
					shutil.copy( source + dataset['name']+ '/' + input , "./" + dataset['name'] + '/'+  input )

			#now copy the  exe if it is in a relative path format
			if not re.match("/",dataset['exe']): # Is not in full path format
				if  os.path.exists(source + dataset['name']+ '/' + dataset['exe'] ):
					if not os.path.exists( os.path.dirname("./" + dataset['name'] + '/'+ dataset['exe'])) :
						os.makedirs( os.path.dirname("./" + dataset['name'] + '/'+ dataset['exe'] ) )
					shutil.copy( source + dataset['name']+ '/' + dataset['exe'] , "./" + dataset['name'] + '/'+ dataset['exe'])
				else:
					self.log.warning("Warning","Can't copy exe file. File not found. Plese check the benchmark and the configuration file")
					sys.exit(1)
						
			self.__runDataset(dataset,t)
			shutil.rmtree(  dataset['name'] )			
			
			
	def __runDataset(self,dataset,t):
		############# 
		# Run dataset
		#############
		now = datetime.datetime.now()
		newname = str(now.strftime("%Y-%m-%dT%H:%M:%S"))
	
		nprocs = str(dataset['numprocs']).split(',')
		if len(nprocs) == 0:
			self.log.warning("Warning","No procs found ... dataset " + self.log.bold( str( dataset['name'] ))  + " skipped")
			return
		
		print "---------------------------------------------------------"
		for p in nprocs:
			
			if dataset['tasks_per_node'] != None and  dataset['tasks_per_node'] != '':
				n = str( int(round ( float(p)/float(dataset['tasks_per_node'])))  )			
				run_id = dataset['name'] + "_" + p + "cpus_" + n + "nodes_"  + str(newname)					
			else:
				run_id = dataset['name'] + "_" + p + "cpus_"  + str(newname)
			
			print "Run ID: " + self.log.bold( run_id) , 
			# change dir name to identify as an unique outcome	
	
			if os.path.isdir( run_id ):
				#print "\n\tDirectory: " + KABS.L1+  run_id  + KABS.LE +" already exists" + ".\n\tTrying to run the same dataset in less than a second."
				print "\n"
				self.log.plain("Directory: " +   self.log.bold(run_id)  +" already exists" + ". Trying to run the same dataset in less than a second.")
				print "\tDelaying a second..." ,
				sys.stdout.flush()		 
				time.sleep( 1 )
				print "Resuming" 
				now = datetime.datetime.now()
				newname = str(now.strftime("%Y-%m-%dT%H:%M:%S"))
				if dataset['tasks_per_node'] != None and  dataset['tasks_per_node'] != '':
					n = str( int(round ( float(p)/float(dataset['tasks_per_node'])))  )			
					run_id = dataset['name'] + "_" + p + "cpus_" + n + "nodes_"  + str(newname)					
				else:
					run_id = dataset['name'] + "_" + p + "cpus_"  + str(newname)
			
			shutil.copytree(  dataset['name'] , run_id )		
	
			# get the script or the command to run it
			data = self.__getBatchScript(dataset,p)
	
			rpath = t + run_id 
			os.chdir(rpath)  
				
			failed = False				
			# submit or run job
			if  dataset['batch'] == "NONE":
				# No batch system found .... 
				syscall( data )
			else:
				o = open( "run.batch","w")
				o.write(data)
				o.flush()
				o.close		
				# get the batch system submission commands	
				mybatch = self.__getBatchSystem(dataset)
				submit_cmd = mybatch['submit']['command']
				submit_params = mybatch['submit']['parameters']	
				
				if submit_params=="<":
					cmd =  " cat run.batch |  " + submit_cmd
				else:
					cmd = submit_cmd + " " + submit_params + " run.batch"
				
				out,err = syscall( cmd )					
				sopattern = mybatch['submit']['submittedmsg']
				sopattern = sopattern.replace("%JOBID%","(\d+)")
				mobj = re.search(sopattern,out)
				if mobj:
					jobid = mobj.group(1)
					cmd = "touch batch.jobid." + jobid
					syscall( cmd )
					print "... Submitted"
				else:
					#print KABS.L1 + "\n\tWarning: "+ KABS.LE + "It seems there was a problem while submitting this job.\n\tPlease read the following error message:"
					#print "\t\t" + KABS.L1  +  err + KABS.LE	
					self.log.error("Warning","It seems there was a problem while submitting this job.")
					Log.Level = 1
					self.log.warning("Please read the following error message:")
					Log.Level = 2
					self.log.plain(err)
					failed = True
													
			os.chdir("..")	
			if failed:
				# mark directory as failed
				shutil.move( run_id , "FAILED_"+run_id )
				
			
						
	
	def __runApp(self,whichapp):
		""" Run the given app whose name is specified
		"""
		app = self.a_apps[whichapp]
		source = self.home + "/bench/apps/"+ whichapp + "/"
		target = self.output_dir + "/"
		for dataset in app:
			self.log.plain( "Dataset: " +  self.log.bold(dataset['name'] ) )
			s = source + dataset['name']+".tgz" 	
			if not os.path.exists(s):
				#print "Dataset Error: Could not find: " + s
				self.log.error("Dataset Error:","Could not find: " + s)
				sys.exit(1)        	
			t = target+"runs/apps/"+whichapp+"/"+dataset['name'] +"/"
			if not os.path.exists(t):
				os.makedirs(t)
		
			# Uncompress dataset:
			cwd = os.getcwd()
			file = s  
			self.log.plain( "Unpacking file: "+ self.log.bold( file ))
			cmd = "tar -zxf " + file 
			print cmd
			os.chdir(t)
			os.system(cmd)
			
			self.__runDataset(dataset,t)			
			shutil.rmtree(  dataset['name'] )




	def kiviat(self,template,target):		
		""" Shows a kiviat diagram for the specified template and target
			Both arguments are directory path. The first is the path to the directory that holds the 
			analysis results for a specific run. This will be used as the reference value.
			The second argument is also a path to a dir but now this dir can contain more dirs being each of 
			them the output for different runs (the analysis results). All of them will be compared against the 
			template values.			
		"""
		
		if not template or not target:
			#print "Error: Wrong arguments. Two arguments needed.\n1.- the path to the base analysis dir\n2.- the path to the dir containing the analysis dirs to compare"
			self.log.error("Wrong arguments. Two arguments needed.\n1.- the path to the base analysis dir\n2.- the path to the dir containing the analysis dirs to compare")
			sys.exit(1)
		
		self.log.plain( "Reading data from template analysis: " + self.log.bold( template ) )
		
		if not os.path.exists(template+"/analysis.raw"):
			self.log.error("Data File not found!","The file " + self.log.bold( template+"/analysis.raw") + " could not be found" )
			sys.exit(1)
			
		tf = open(template+"/analysis.raw", 'r') 
		theta = []
		radio = []
		metrics = []
		legend = []
		radio.append([])
		tfc = tf.readline()
		while tfc:		
			line = tfc.split()
			metrics.append(line[0])	
			theta.append(line[1])
			radio[0].append(line[2])
			tfc = tf.readline()
		tf.close
		
		legend.append(os.path.basename(template))	
			
		print "Reading data from target analysis:"
		if (os.path.isfile(target+"/analysis.raw")):
			#print "\t" + KABS.L1 + target + KABS.LE
			Log.Level = 1
			self.log.plain( self.log.bold(target ))
			if not os.path.exists(target+"/analysis.raw"):
				self.log.error("Data File not found!","The file " + self.log.bold( target+"/analysis.raw") + " could not be found" )
				sys.exit(1)
			tf = open(target+"/analysis.raw", 'r') 
			ofc = tf.readline()
			radio.append([])
			legend.append(os.path.basename(target))	
			while ofc:
				line = ofc.split()
				radio[len(radio)-1].append(line[2])
				ofc = tf.readline()	
			tf.close
	
		u = os.listdir(target)
		for file in u:
			if os.path.isfile(target + "/" + file + "/analysis.raw"):
				#print "\t" + KABS.L1 + target + "/"+ file + KABS.LE
				Log.Level = 1
				self.log.plain( self.log.bold(target + "/"+ file ) )
				
				if not os.path.exists(target + "/" + file+"/analysis.raw"):
					self.log.error("Data File not found!","The file " + self.log.bold( target + "/" + file+"/analysis.raw") + " could not be found...skipping" )
					continue
				
				tf = open(target + "/" + file+"/analysis.raw", 'r') 
				ofc = tf.readline()
				radio.append([])
				legend.append(os.path.basename(target + "/" + file))
				while ofc:
					line = ofc.split()
					radio[len(radio)-1].append(line[2])
					ofc = tf.readline()	
				tf.close
	
		of = open("kanalysis.raw", 'w') 	
		mnvalue = 0
		for t in range(0,len(theta)):
			lineout = metrics[t] + ' ' +  str(theta[t]) + ' ' 	
			for l in range(0,len(radio)):
				nvalue = float(radio[l][t])/float(radio[0][t])			
				if (nvalue>mnvalue):
					mnvalue = nvalue  
				lineout = lineout + str(nvalue) + ' '  # normalizar respecto al patron	
			of.write(lineout + "\n")
		of.flush()
		of.close
			
		# create gnuplot file
		gnuplotfile = "kiviat.gnuplot"
		kf = open(gnuplotfile,'w')
		kf.write(
		"""
set clip points
unset border
set dummy t,y
set polar
set xtics axis 
set ytics axis 
set grid polar
	""") 
		kf.write("set xrange[-"+ str(mnvalue+0.8) + ":"+ str(mnvalue+0.8) + "]\n")
		kf.write("set yrange[-"+ str(mnvalue+0.8) + ":" + str(mnvalue+0.8) + "]\n")
		#kf.write( " set title \"Some title here\" ")
		for t in range(0,len(theta)):
			xpos = mnvalue*math.cos(float(theta[t]))
			ypos = mnvalue*math.sin(float(theta[t]))
			kf.write("set label '" + metrics[t] + "' at " + str(xpos) + "," + str(ypos) + " front font \"Sans,14\"\n")	
					
		plotstr = "plot 'kanalysis.raw' using 2:3 with linespoints title \"" + legend[0] + "\""	
		for l in range(4,len(radio)+3):
			plotstr = plotstr + " ,  'kanalysis.raw' using 2:" + str(l) + " with  linespoints title \"" + legend[l-3] +"\""  
	
		kf.write( plotstr )
		kf.flush()
		kf.close()
			
		# and call it
		print syscall ( "gnuplot -persist " + gnuplotfile )[1]




	def analysis(self,item=None,name=None):
		""" Runs the analysis stage for a given 'item' and 'name' 
		"""
		if item == None: # means analyze everything	
			if item == None: # means run everything	
				first = True
				for app in self.a_apps:
					if first:
						self.analysis('a',app)
						first = False
					else:
						self.__analysisApp(app)
				first = True
				for net in self.a_nets:
					if first:				
						self.analysis('n',net)
						first = False	
					else:			
						self.__analysisApp(net)
		
		elif item == 'a':
			self.log.plain("***********************************************")
			self.log.plain("***  KaBS analysis stage for selected App:  ***")
			self.log.plain("***********************************************")
			self.log.plain( self.log.bold(name) )
			if self.a_apps.keys().count(name) == 0:
				self.log.warning( "Warning", "Application " +  self.log.bold( name ) + " not found or not active"	)
				return
			self.__analysisApp(name)	
				
		elif item == 'n':		
			self.log.plain("***********************************************")
			self.log.plain("***    KaBS analysis stage for  Network:    ***")
			self.log.plain("***********************************************")
			self.log.plain( self.log.bold(name) )
			if self.a_nets.keys().count(name) == 0:
				self.log.warning( "Warning", "Network " +  self.log.bold( name ) + " not found or not active"	)
				return
			self.__analysisNet(name)	

		elif item == 'f':
			pass

		elif item == 's':
			self.log.plain("***********************************************")
			self.log.plain("***    KaBS analysis stage for  Synthetic:   ***")
			self.log.plain("***********************************************")
			self.log.plain( self.log.bold(name) )
			if self.a_synths.keys().count(name) == 0:
				self.log.warning( "Warning", "Benchmark " +  self.log.bold( name ) + " not found or not active"	)
				return
			self.__analysisSynthetic(name)				

		elif item == 'm':
			pass

		elif item == 'x':
			pass	

		else:
			print "Unknown item: '" + str(item) + "'"




	def run(self,item=None,name=None):
		""" Runs a given 'name' benchmark from 'item'
		"""
		if item == None: # means run everything	
			first = True	
			for app in self.a_apps:
				if first:
					self.run('a',app)
					first = False
				else:
					self.__runApp(app)
			first = True
			for net in self.a_nets:
				if first:
					self.run('n',net)
					first = False
				else:
					self.__runNet(net)
			for synth in self.a_synths:
				if first:
					self.run('s',synth)
					first = False
				else:
					self.__runSynthetic(synth)
					
				
		elif item == 'a':
			self.log.plain("********************************************")			
			self.log.plain( "***  Running KaBS for selected App:      ***")
			self.log.plain("********************************************")
			#print  KABS.L1+ name + KABS.LE + "\n"
			self.log.log(name)
			if self.a_apps.keys().count(name) == 0:
				#print "Application " +  KABS.L1+ name + KABS.LE + " not found or not active"	
				self.log.warning("Warning","Application " +  self.log.bold(name) + " not found or not active"	)
				return		
			self.__runApp(name)	
				
		elif item == 'n':		
			self.log.plain("********************************************")			
			self.log.plain( "***  Running KaBS for selected Network:  ***")
			self.log.plain("********************************************")
			self.log.log(name)
			if self.a_nets.keys().count(name) == 0:
				self.log.warning("Warning","Network " +  self.log.bold(name) + " not found or not active"	)
				return		
			self.__runNet(name)
				
		elif item == 'f':
			pass
		
		elif item == 's':
			self.log.plain("**********************************************")			
			self.log.plain( "***  Running KaBS for selected Synthetic:  ***")
			self.log.plain("**********************************************")
			self.log.log(name)
			if self.a_synths.keys().count(name) == 0:
				self.log.warning("Warning","Benchmark " +  self.log.bold(name) + " not found or not active"	)
				return		
			self.__runSynthetic(name)
		
		elif item == 'm':
			pass
		
		elif item == 'x':
			pass	
		
		else:
			print "Unknown item: '" + str(item) + "'"




	def printConf(self, item=None, name=None ):
		""" Prints out the configuration for a given 'item' and 'name' or the global configuration
			if no item is given
		"""		
		self.log.log("*************************************************************")
		self.log.log("***  Current configuration for the KAUST Benchmark Suite  ***"	)
		self.log.log("*************************************************************")
			
		if item == None: # means show the global configuration	
	
			#print KABS.L0 + "KaBS Home:" + KABS.LE + self.home
			self.log.log("KaBS Home",self.home )
			#print KABS.L0 + "KaBS Otputs: " + KABS.LE + self.output_dir
			self.log.log("KaBS Outputs",self.output_dir )
			#print KABS.L0 + "KaBS Batch Systems: " + KABS.LE
			self.log.log("KaBS Batch Systems:" )
						
			for nbatch in self.batchs:
				#print "\t" + KABS.L1 + nbatch['name'] +": "+ KABS.LE
				Log.Level = 1
				self.log.log(nbatch['name'] +":") 
				if  str(nbatch['name']) != "NONE" :
					#print "\t\tSubmission script: " + KABS.L1 + nbatch['script'] + KABS.LE
					Log.Level = 2
					#self.log.data("Submission script",nbatch['script'])
					self.log.log("Submission script",nbatch['script'])
			#print "\t\tSubmission command: " + KABS.L1 + nbatch['submit']['command'] + ' '+ nbatch['submit']['parameters'] + KABS.LE
			Log.Level = 2
			#self.log.data("Submission command",nbatch['submit']['command'] + ' '+ nbatch['submit']['parameters'])			
			self.log.log("Submission command",nbatch['submit']['command'] + ' '+ nbatch['submit']['parameters'])			
			#print KABS.L0+"Items to Benchmark:"+ KABS.LE
			self.log.log("Items to Benchmark")
			self.__printAppsInfo()	
			self.__printFSInfo()
			self.__printNetInfo()
			self.__printSynthInfo()
			self.__printMathlibInfo()

		elif item == 'a':
			self.log.plain("\n***  Showing configuration for selected App  ***\n")
			self.__printAppsInfo(name)	
		
		elif item == 'f':
			self.log.plain("\n***  Showing configuration for Filesystems  ***\n"	)
			self.__printFSInfo(name)
		elif item == 'n':
			self.log.plain("\n***  Showing configuration for Networks  ***\n")
			self.__printNetInfo(name)
		elif item == 's':
			self.log.plain("\n***  Showing configuration for Synthetic benchmarks  ***\n")	
			self.__printSynthInfo(name)
		elif item == 'm':
			self.log.plain("\n***  Showing configuration for Math Libs  ***\n"	)
			self.__printMathlibInfo(name)
		elif item == 'x':
			self.log.plain("\n***  Showing configuration for the Acceptance benchmark  ***\n"	)
			self.__printAcceptanceInfo()	
		else:
			print "Unknown item: '" + str(item) + "'"



	def debug(self):
		print "TODO: debug mode"
		
		
		
		
	def __loadYaml(self,configfile=None):
		"""Reads the configuration file and load the YAML into a variable. Then parse this structure to load the configuration variables"""
		# import YAML 
		import yaml

		# read configuration file
		try:
			if configfile == None:
				cfname = KABS.CONF_FILE_PATH+KABS.CONF_FILE_NAME
			else:
				cfname = configfile
				
			stream = file(cfname, 'r')
		except IOError as e:
			print "I/O error({0}): {1}".format(e.errno, e.strerror)
			sys.exit(e.errno)


		print "\nUsing configuration file: ",
		self.log.plain( self.log.bold(cfname) )
		print "\n"

		# global variable holding the configuration 
		yaml_conf = yaml.load( stream )		
		self.__readYaml(yaml_conf)
	

	
	
	def __init__(self,configfile=None):
		self.log = Log()
		# include KABS.LIB_DIR in the module search path 
		if KABS.LIB_DIR not in sys.path:
			sys.path.insert(0, KABS.LIB_DIR)		
		self.__loadYaml(configfile)
		#self.__substituteVarsInSection_analysis()
		self.__substituteVarsInBatch_NONE()

		
#####################################################################                                           
#
#	Main Program entry point
#
#####################################################################                                           
if __name__ == "__main__":

	# ARGS processing
	usage = "%prog <Option> [ [<Selector>] [<arg>] ]"
	parser = optparse.OptionParser(usage=usage,version='%prog version 0.1')
	parser.add_option("--clean", action="store_true", help="Remove all stored results from previous runs and analysis", default=False,dest='clean')
	parser.add_option("-d", "--debug", action="store_true", help="Debug mode: Show the actions to be performed", default=False,dest='d')
	parser.add_option("-r", "--run", action="store_true",   help="Run the whole benchmark or a specific item according to the 'Selectors' below", default=False,dest='r')
	parser.add_option("-c", "--configuration" ,action="store_true", help="Show the benchmark global configuration or a specific item configuration according to the 'Selectors' below ", default=False,dest='c')	
	parser.add_option("-p", "--postprocess",action="store_true", help="Perform the Postprocess/Analysis stage for the whole benchmark or for a specific item according to the 'Selectors' below .", default=False,dest='p')	
	parser.add_option("-y", "--yaml",action="store", help="Use the specified yaml configuration file rather than the default one", dest='y')	
	parser.add_option("-k", "", nargs=2 ,action="store" , help="Displays the kiviat diagram for the specified analysis dir. The first argument is the path to the reference directory and the second argument is a path to another directory which might contain multiple dirs. If any of these dirs contain a valid analysis data, they will be used to compared against the reference dir specified in the first argument" , dest='k')	
		
	groupRun = optparse.OptionGroup(parser, "Selectors")
	groupRun.add_option("-a", action="store", help="Select a specific application" , dest='a')
	groupRun.add_option("-n", action="store", help="Select a specific network benchmark",dest='n')
	groupRun.add_option("-s", action="store", help="Select the synthetic benchmark.", dest='s')
	groupRun.add_option("-f", action="store", help="Select a specific filesystem benchmark",dest='f')
	groupRun.add_option("-m", action="store", help="Select a specific mathlib benchmark",dest='m')
	groupRun.add_option("-x", action="store_true", help="Select the Acceptance benchmark", default=False,dest='x')
	parser.add_option_group(groupRun)
		
	(opts, args) = parser.parse_args()

	if opts.clean == True:
		kabs=KABS()
		print "Cleaning..." 
		print "You are about to remove all stored results from previous runs" 
		var = raw_input("Are you sure you want to do that? (Yes/No)")	
		if var=="Yes":			
			clean(kabs.output_dir+"/runs/")
			clean(kabs.output_dir+"/analysis/")
 			print "Done."
		else:
			print  "Cleaning cancelled"
		sys.exit(0)	

	rargs = 0
	if opts.y:
		rargs = 2	
	#
	# Arguments check
	#
	if len(sys.argv)-rargs>4 or len(args)>0:
		print  "******************\nToo many arguments\n******************" 
		parser.print_help()
		exit(-1)

	# at least one option selected
	if not ( opts.d or opts.r or opts.p or opts.c or opts.k):
		print  "**************\nWrong argument\n**************" 
		parser.print_help()
		exit(-1)

	# but no more than one at a time. Also check there is only one Selector active:
	opt_counter = 0
	sel_counter = 0
	for attr, value in opts.__dict__.iteritems():
		if value == True:
			if attr=='d' or attr=='r' or attr=='p' or attr=='c' :
				opt_counter = opt_counter + 1
			elif attr=='s' or attr=='x' :
				sel_counter = sel_counter +1
		elif ( attr=='a'  or  attr=='n' or  attr=='f' or  attr=='m' ) and value != None:
			sel_counter = sel_counter +1		
		elif attr=='k' and value != None :
			opt_counter = opt_counter + 1
				
	if opt_counter > 1:
		print  "*************************************\nToo many options. Only one is allowed\n*************************************" 
		parser.print_help()
		exit(-1)
	
	if sel_counter > 1:
		print  "*************************************\nToo many Selectors. Only one is allowed\n*************************************" 
		parser.print_help()
		exit(-1)

	#
	# Get the selected options and selectors
	#
	option = ''
	selector=''
	itemname=''
	for attr, value in opts.__dict__.iteritems():		
		if ( ( attr=='d' or attr=='r' or attr=='p' or attr=='c' ) and value==True ) or (attr=='k' and value!=None) :
			# got the option
			option = attr	
			if (attr=='k' and value!=None):	
				itemname = value
		if  ( ( attr=='a'  or  attr=='n' or  attr=='f' or  attr=='m' or attr=='s' ) and value!= None) or ( attr=='x' and value==True):
			# got selector
			selector = attr
			itemname = value

	
	# Well, finally create the instance...
	kabs=KABS( opts.y )

	#
	# RUN 
	#
	if option == "d":
		kabs.debug()
	
 	elif option == "c":
 		if selector=='' :
 			kabs.printConf()
		else:
 			kabs.printConf(selector,itemname)
 	
 	elif option =="r":
 		if selector=='' :
 			kabs.run()	
 		else:
 			kabs.run(selector,itemname)	
 	
 	elif option == "p":
 		if selector=='' :
 			kabs.analysis()	
 		else:
 			kabs.analysis(selector,itemname)	
 	
 	elif option == "k":
 		kabs.kiviat(itemname[0],itemname[1])
 		
 	else:
 		assert False, "unhandled option"
 			
	sys.exit(0)

			
			