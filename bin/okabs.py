#!/usr/bin/python
# coding: utf-8

# import system issues
import sys
import glob
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
	
#####################################################################                                           
#
#	Getters functions
#
#####################################################################  					
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
		counter=1
		repeat = True
		while repeat and counter < 20:	
			for litem in  whichdataset:
				str2find = "%("+ str(litem).upper() +")%"
				prog = re.compile(str2find);
				if litem != 'numprocs':
						#data = prog.sub( unicode(whichdataset[litem]) ,data)	
						data = prog.sub( str(whichdataset[litem]) ,data)	
				else:
					#data = prog.sub( unicode(p) ,data)		
					data = prog.sub( str(p).strip() ,data)		
			
			if re.search("%.+%", data) != None:
				repeat = True
				counter = counter +1
			else:
				repeat = False	
		
		if counter>19:
			self.log.error("Missing variable!!!","I suspect that you missed to define some variable in the config file that is needed; presumably in the batch script.\n" )
			sys.exit(1)	
				
		return data	

#####################################################################                                           
#
#	Visualization (Kiviat graph) functions
#
#####################################################################  
	def kiviat(self,template,target):		
		""" Shows a kiviat diagram for the specified template and target
			Both arguments are directory path. The first is the path to the directory that holds the 
			analysis results for a specific run. This will be used as the reference value.
			The second argument is also a path to a dir but now this dir can contain more dirs being each of 
			them the output for different runs (the analysis results). All of them will be compared against the 
			template values.			
		"""
		
		if not template or not target:
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


#####################################################################                                           
#
#	Post-Process (Analysis) functions
#
#####################################################################  
	def analysis(self,item=None,name=None):
		""" Runs the analysis stage for a given 'item' and 'name' 
		"""
		if item == None: # means analyze everything	
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
			first = True
			for synth in self.a_synths:
				if first:	
					self.analysis('s',synth)
					first = False
				else:
					self.__analysisSynthetics(synth)		
		
		elif item == 'a':
			self.log.plain("***********************************************")
			self.log.plain("***  KaBS analysis stage for selected Apps: ***")
			self.log.plain("***********************************************")
			if self.a_apps.keys().count(name) == 0:
				self.log.warning( "Warning", "Application " +  self.log.bold( name ) + " not found or not active"	)
				return
			self.__analysisApp(name)	
				
		elif item == 'n':		
			self.log.plain("***********************************************")
			self.log.plain("***    KaBS analysis stage for Networks:    ***")
			self.log.plain("***********************************************")
			if self.a_nets.keys().count(name) == 0:
				self.log.warning( "Warning", "Network " +  self.log.bold( name ) + " not found or not active"	)
				return
			self.__analysisNet(name)	

		elif item == 'f':
			self.log.plain("***********************************************")
			self.log.plain("***    KaBS analysis stage for Filesystems: ***")
			self.log.plain("***********************************************")
			if self.a_filesys.keys().count(name) == 0:
				self.log.warning( "Warning", "Filesystem " +  self.log.bold( name ) + " not found or not active"	)
				return
			self.__analysisFilesystem(name)				

		elif item == 's':
			self.log.plain("***********************************************")
			self.log.plain("***    KaBS analysis stage for  Synthetics: ***")
			self.log.plain("***********************************************")
			if self.a_synths.keys().count(name) == 0:
				self.log.warning( "Warning", "Benchmark " +  self.log.bold( name ) + " not found or not active"	)
				return
			self.__analysisSynthetics(name)				

		else:
			print "Unknown item: '" + str(item) + "'"
			
	def __analysisApp(self,name):
		"""  Performs the analysis stage for an app. Go into the runs dir and identify the app and the dataset.
			 then creates a similar entry in the 'results/analysis' dir  and copies the output files to the new location.
			 it also creates a .cvs and a .raw files with the metrics specified in the YAML config file. The .raw file is used later on
			 when visualizing the metric.
 		"""
 		self.log.log( name )
		app = self.a_apps[name]
		analysisd = self.output_dir + "/analysis/apps/"+ name + "/"
		runsd = self.output_dir + "/runs/apps/"+ name + "/"
		if not os.path.exists(runsd):
			self.log.warning("Can't find any completed run for this app: " + self.log.bold(name) )
			return
			#sys.exit(1)
		if not os.path.exists(analysisd):
			os.makedirs(analysisd)

		for dataset in app:
			self.__analizeDataset(dataset,runsd,analysisd)			

	def __analysisSynthetics(self,name):
		self.log.log( name )
		synth = self.a_synths[name]
		analysisd = self.output_dir + "/analysis/synthetics/"+ name + "/"
		runsd = self.output_dir + "/runs/synthetics/"+ name + "/"
		if not os.path.exists(runsd):
			self.log.warning("Can't find any completed run for this synthetic: " + self.log.bold(name) )
			return
			#sys.exit(1)
		if not os.path.exists(analysisd):
			os.makedirs(analysisd)

		for dataset in synth:	
			self.__analizeDataset(dataset,runsd,analysisd)		

	def __analysisFilesystem(self,name):
		self.log.log( name )
		fs = self.a_filesys[name]
		analysisd = self.output_dir + "/analysis/filesystems/"+ name + "/"
		runsd = self.output_dir + "/runs/filesystems/"+ name + "/"
		if not os.path.exists(runsd):
			self.log.warning("Can't find any completed run for this filesystem: " + self.log.bold(name) )
			return
			#sys.exit(1)
		if not os.path.exists(analysisd):
			os.makedirs(analysisd)
		
		for dataset in filesys:	
			self.__analizeDataset(dataset,runsd,analysisd)	
			
			
	def __analysisNet(self,name):
		self.log.log( name )
		net = self.a_nets[name]
		analysisd = self.output_dir + "/analysis/networks/"+ name + "/"
		runsd = self.output_dir + "/runs/networks/"+ name + "/"
		if not os.path.exists(runsd):
			self.log.warning("Can't find any completed run for this network: " + self.log.bold(name) )
			return
			#sys.exit(1)
		if not os.path.exists(analysisd):
			os.makedirs(analysisd)

		for dataset in net:	
			self.__analizeDataset(dataset,runsd,analysisd)		

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
			for outp in  dataset['outputs'].keys():
				failed = False
				mobj = re.match("#(\d+)#", outp)
				if mobj:
					if mobj.group(1) == cpus:
						if os.path.isfile(rundir + "/" + i + "/" + dataset['outputs'][outp]) :					
							shutil.copy( rundir + "/" + i + "/" + dataset['outputs'][outp] , "./")
						else:
							self.log.waring("Warning","File " + self.log.bold( rundir + "/" + i + "/" + str(dataset['outputs'][outp]) ) + " Does not exist.")
							self.log.error("Analysis not completed!!!")
							failed = True
							break
				else:
					skip = False
					for again_outp in  dataset['outputs'].keys():				
						if re.match("#"+cpus+"#"+outp , again_outp):
							skip = True
							break								
					if not skip:	
						if os.path.isfile(rundir + "/" + i + "/" + dataset['outputs'][outp]) :					
							shutil.copy( rundir + "/" + i + "/" + dataset['outputs'][outp] , "./")
						else:
							self.log.warning("Warning","File " + self.log.bold( rundir + "/" + i + "/" + str(dataset['outputs'][outp]) ) + " Does not exist.")
							self.log.error("Analysis not completed!!!")
							failed = True
							break		
				
				if failed == True:
					continue
				
				if  dataset.keys().count('metrics') != 0 :
					# now crate a .csv and the .raw file suitable to be used later on with gnuplot...
					START = 0.0
					END = 2*math.pi
					STEP =  END/len(dataset['metrics'])	
					theta = frange(START,END,STEP)		
					radio = []
					metrics = []
					o = open( "analysis.csv","w")
					o.write(  "\"metric\",\"value\",\"units\"\n" )
					for metric in dataset['metrics']:
						# Up to this point, values in Metric may contain %VALUES% to be replaced ... so we have to do it now
						name=None
						command=None
						units=None
						
						# replace references to the output section						
						for outp in  dataset['outputs'].keys():
							#if not re.match( "#"+cpus+"#",outp  ):
							if not re.match( "#\d+#",outp  ):
								reple = re.compile( "%"+str(outp).upper()+"%" )
								if dataset['outputs'].keys().count( "#"+cpus+"#"+outp) != 0:
									name    = reple.sub(dataset['outputs']["#"+cpus+"#"+outp] , metric['name'] )	
									units   = reple.sub(dataset['outputs']["#"+cpus+"#"+outp] , metric['units'] )	
									command = reple.sub(dataset['outputs']["#"+cpus+"#"+outp] , metric['command'] )	
								else:
									name    = reple.sub(dataset['outputs'][outp] , metric['name'] )	
									units   = reple.sub(dataset['outputs'][outp] , metric['units'] )	
									command = reple.sub(dataset['outputs'][outp] , metric['command'] )	
								
						# Now replace other variables from the dataset... (TODO)		
								
						#o.write( "\"" +metric['name']+ "\"," + "\"" + syscall( metric['command'])[0].strip() +"\"," +"\"" + metric['units'] + "\"\n"  ) 
						o.write( "\"" + name + "\"," + "\"" + syscall(command)[0].strip() +"\"," +"\"" + units + "\"\n"  ) 
						radio.append ( syscall( command )[0].strip() )				
						metrics.append( name )
					o.flush()
					o.close
					
					sort_dict = zip(metrics, theta, radio)		
									
					r = open( "analysis.raw","w")
					for k in sort_dict:
						r.write( str(k[0]) + "  "  + str(k[1]) + "  "  + str(k[2])   + "\n"  )
					r.write( str(sort_dict[0][0])	 + "  "  + str(sort_dict[0][1]) + "  "  + str(sort_dict[0][2])    + "\n"  )
					r.flush
					r.close		

#####################################################################                                           
#
#	RUN functions
#
#####################################################################  
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
			first = True
			for synth in self.a_synths:
				if first:
					self.run('s',synth)
					first = False
				else:
					self.__runSynthetics(synth)
			first = True
			for fs in self.a_filesys:
				if first:
					self.run('f',fs)
					first = False
				else:
					self.__runFilesys(fs)		
				
		elif item == 'a':
			self.log.plain("********************************************")			
			self.log.plain("***  Running KaBS for selected Apps:     ***")
			self.log.plain("********************************************")
			if self.a_apps.keys().count(name) == 0:
				self.log.warning("Warning","Application " +  self.log.bold(name) + " not found or not active"	)
				return		
			self.__runApp(name)	
				
		elif item == 'n':		
			self.log.plain("********************************************")			
			self.log.plain("***  Running KaBS for selected Networks: ***")
			self.log.plain("********************************************")
			if self.a_nets.keys().count(name) == 0:
				self.log.warning("Warning","Network " +  self.log.bold(name) + " not found or not active"	)
				return		
			self.__runNet(name)
				
		elif item == 'f':
			self.log.plain("*********************************************")			
			self.log.plain("*** Running KaBS for selected Filesystem: ***")
			self.log.plain("*********************************************")
			if self.a_filesys.keys().count(name) == 0:
				self.log.warning("Warning","Filesystem " +  self.log.bold(name) + " not found or not active"	)
				return		
			self.__runFilesys(name)
		
		elif item == 's':
			self.log.plain("**********************************************")			
			self.log.plain("***  Running KaBS for selected Synthetics: ***")
			self.log.plain("**********************************************")
			if self.a_synths.keys().count(name) == 0:
				self.log.warning("Warning","Benchmark " +  self.log.bold(name) + " not found or not active"	)
				return		
			self.__runSynthetics(name)

		else:
			print "Unknown item: '" + str(item) + "'"

	def __runApp(self,which):
		""" Run the given app whose name is specified
		"""
		self.log.log(which)
		app = self.a_apps[which]
		source = self.home + "/bench/apps/"+ which + "/"
		target = self.output_dir + "/"+ "runs/apps/" + which + "/"
		self.__runBasic(app,source,target,True)
	

	def __runSynthetics(self, which):
		""" Run the given Synthetic whose name is specified
		"""
		self.log.log(which)
		synth = self.a_synths[which]
		source = self.home + "/bench/synthetics/"+ which + "/"
		target = self.output_dir + "/" + "runs/synthetics/" + which + "/"
		self.__runBasic(synth,source,target)

	def __runNet(self, which):
		""" Run the given Network whose name is specified
		"""
		self.log.log(which)
		net = self.a_nets[which]
		source = self.home + "/bench/networks/"+ which + "/"
		target = self.output_dir + "/" + "runs/networks/" + which + "/"
		self.__runBasic(net,source,target)

	def __runFilesys(self, which):
		""" Run the given Filesystem benchmark whose name is specified
		"""
		self.log.log(which)
		net = self.a_filesys[which]
		source = self.home + "/bench/filesystems/"+ which + "/"
		target = self.output_dir + "/" + "runs/filesystems/" + which + "/"
		self.__runBasic(net,source,target)


	def __runBasic(self,bench,source,target,isApp=False):
		for dataset in bench:
			self.log.plain( "Dataset: " +  self.log.bold(dataset['name'] ) )
			if not os.path.exists(source):
				self.log.error("Dataset Error:","Could not find: " + source)
				sys.exit(1)        	
			t = target + dataset['name'] +"/"
			if not os.path.exists(t):
				os.makedirs(t)
				os.makedirs(t + dataset['name'])
			elif not os.path.exists(t+dataset['name']):
				os.makedirs(t+dataset['name'])
				
			cwd = os.getcwd()
			os.chdir(t)					

			# If App copy the dataset
			if isApp==True:
				#APP SPECIFIC PART!!!	
	 			s = source + dataset['name']+".tgz" 	
	 			if not os.path.exists(s):
	 				self.log.error("Dataset Error:","Could not find: " + s)
	 				sys.exit(1)       	
	 			# Uncompress dataset:
	 			file = s  
	 			self.log.plain( "Unpacking file: "+ self.log.bold( file ))
	 			cmd = "tar -zxf " + file 
	 			print cmd
	 			os.system(cmd)				

			self.__runDataset(dataset,source,t,isApp)
			shutil.rmtree(  dataset['name'] )		

	def __runDataset(self,dataset,source,t, isApp ):
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
			p = p.strip()
			try:
				if int(p)==0:
					self.log.warning("Warning","No valid proc found ... dataset " + self.log.bold( str( dataset['name'] ))  + " skipped")
					return
			except:
				self.log.warning("Warning","No valid proc found ... dataset " + self.log.bold( str( dataset['name'] ))  + " skipped")
				return
				
			if dataset['tasks_per_node'] != None and  dataset['tasks_per_node'] != '':
				n = str( int(round ( float(p)/float(dataset['tasks_per_node'])))  )			
				run_id = dataset['name'] + "_" + p + "cpus_" + n + "nodes_"  + str(newname)					
			else:
				run_id = dataset['name'] + "_" + p + "cpus_"  + str(newname)
			
			print "Run ID: " + self.log.bold( run_id) , 
	
			# change dir name to identify as an unique outcome	
			if os.path.isdir( run_id ):
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
			data = self.__getBatchScript(dataset,p.strip()) 
			
			rpath = t + run_id 
			os.chdir(rpath)  
			
			if not isApp:
				files = None
				exe = None
			
				#see if there is any #PROCS# field
				if  dataset.keys().count("#"+str(p)+"#dependencies") != 0:
					files = dataset['#'+str(p)+'#dependencies']
				elif dataset.keys().count("dependencies") != 0 :
					files = dataset['dependencies']
					
				if 	dataset.keys().count("#"+str(p)+"#exe") != 0:
					exe = dataset['#'+str(p)+'#exe']
				elif dataset.keys().count("exe") != 0 :
					exe = dataset['exe']
					
					
				# Now copy files  if any				
				if files != None:	
					inputs = str(files).split(',')
					for input in inputs:
						if input != 'None' and input != "" and input != "u''":
							input = input.strip()
							self.log.plain( "Copying dependency file: "+ self.log.bold( str(input) )  + " into run directory")
							# input is always relative to the 'source' directory
							if not os.path.exists( os.path.dirname("./" + input )) :
								os.makedirs( os.path.dirname("./" + input ) )
							file = glob.glob(os.path.join( source + dataset['name']+ '/'  , input))
							for f in file:
								shutil.copy( f ,os.path.dirname("./" + input )  )
						
				print exe		
				if not re.match("/",exe): # Is not in full path format
					if  os.path.exists(source + dataset['name']+ '/' + exe ):
						if not os.path.exists( os.path.dirname("./" + exe)) :
							os.makedirs( os.path.dirname("./" + exe ) )
						if not os.path.isfile( "./" + exe ):	
							shutil.copy( source + dataset['name']+ '/' + exe , "./" + exe)
					else:
						self.log.warning("Warning","Can't copy exe file. File not found. Plese check the benchmark and the configuration file")
						sys.exit(1)
	
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


#####################################################################                                           
#
#	Print Config info functions
#
#####################################################################   
	def printConf(self, item=None, name=None ):
		""" Prints out the configuration for a given 'item' and 'name' or the global configuration
			if no item is given
		"""		
		self.log.log("*************************************************************")
		self.log.log("***  Current configuration for the KAUST Benchmark Suite  ***"	)
		self.log.log("*************************************************************")
			
		if item == None: # means show the global configuration	
	
			self.log.log("KaBS Home",self.home )
			self.log.log("KaBS Outputs",self.output_dir )
			self.log.log("KaBS Batch Systems:" )
						
			for nbatch in self.batchs:
				Log.Level = 1
				self.log.log(nbatch['name'] +":") 
				if  nbatch['name'] != "NONE" :
					Log.Level = 2
					self.log.log("Submission script",nbatch['script'])
			Log.Level = 2
			self.log.log("Submission command",nbatch['submit']['command'] + ' '+ nbatch['submit']['parameters'])			
			self.log.log("Items to Benchmark")
			self.__printAppsInfo()	
			self.__printFSInfo()
			self.__printNetInfo()
			self.__printSynthInfo()

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
			self.log.plain("\n***  Showing configuration for Synthetics benchmarks ***\n")	
			self.__printSynthInfo(name)
		else:
			print "Unknown item: '" + str(item) + "'"
		
	def __printAppsInfo(self,which=None):
		""" Prints out configuration information for a specific app or for All apps
		"""
		if which==None: # means ALL
			#Log.Level = 1
			#self.log.log("Inactive Apps", str(self.i_apps) )
			Log.Level = 1
			self.log.log("Apps"," " )
			#self.log.log("Active Apps"," " )			
			for k in self.a_apps.keys():
				Log.Level = 2
				#self.log.data(k,"with ..." )
				self.log.log(k,"with ..." )
				for l in range(len(self.a_apps[k])):
					Log.Level =3
					self.log.log("dataset",str( self.a_apps[k][l]['name']))
					for litem in  self.a_apps[k][l]:
						if litem != 'name' and litem != 'outputs' and litem != 'metrics' and litem != 'datasets' and litem != 'active' and not re.match("launcher",litem) and  not re.match("#\d+#",litem):
							if str(self.a_apps[k][l][litem]).strip() != None or str(self.a_apps[k][l][litem]).strip() != '' :
								Log.Level = 4								
								self.log.log(litem ,str( self.a_apps[k][l][litem])  )
		else:
			if self.a_apps.keys().count(which) == 0:
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
	
	def __printFSInfo(self, which=None):
		""" Prints out configuration information for a specific Filesystem benchmarks or for all filesystem benchmarks
		"""
		self.__printBaseInfo( self.a_filesys, self.filesys, which, "Filesystems")
		
	def __printSynthInfo(self,which=None):
		""" Prints out configuration information for a specific Synthetic benchmarks or for all synthetic benchmarks
		"""
		self.__printBaseInfo( self.a_synths, self.synths, which,"Synthetics")

	def __printNetInfo(self,which=None):
		""" Prints out configuration information for a specific app or for All apps
		"""
		self.__printBaseInfo( self.a_nets, self.nets, which,"Networks")		
		
	def __printBatchSystemInfo(self,mybatch):
		submit_cmd = mybatch['submit']['command']
		submit_params = mybatch['submit']['parameters']	
		if  mybatch == None or mybatch['name'] == "NONE":
			# No batch system found .... 
			self.log.warning("Warning","No batch system specified for " + self.log.bold(which) )
			self.log.log("Submission command:")
			Log.Level = 1
			#self.log.data(submit_cmd +" " + submit_params )
			self.log.log(submit_cmd +" " + submit_params )
		else:
			submit_script = mybatch['script']
			self.log.plain("Using " + self.log.bold(str(mybatch['name']))+ " batch system" )
			self.log.log("Submission command:")
			Log.Level = 1
			self.log.log(submit_cmd +" " + submit_params )
		print "\n"

	def __printDatasetInfo(self,which):
		Log.Level = 0
		for   dataset in which:
			nprocs = str(dataset['numprocs']).split(',')
			if len(nprocs) == 0:
				self.log.warning("Warning","No procs found ... dataset " + self.log.bold(str( dataset['name'] ))  +" skipped")
				continue
			for p in nprocs:
				self.log.plain("dataset: " + self.log.bold(str( dataset['name'] )) + " with " +  self.log.bold(p)  + " procs")
				self.log.log("Submission script:")
				data = self.__getBatchScript(dataset,p.strip())
				print data
				print "-------------------------------------------------"			

	def __printBaseInfo(self, who, all ,which,section):
		""" Prints out configuration common information for Networks, Filesystems and Synthetics benchmarks
		"""
		if which==None: # means ALL
			Log.Level = 1	
			self.log.log(str(section)," " )		
			for k in who.keys():
				Log.Level =	 2
				self.log.log(k," " )
				for l in range(len(who[k])):
					Log.Level =3
					self.log.log("dataset",str( who[k][l]['name']))
					for litem in  who[k][l]:
						if litem == 'numprocs' or litem == 'tasks_per_node' or litem == 'exe' or litem == 'batch' and  not re.match("#\d+#",litem):
							Log.Level = 4
							self.log.log(litem ,str( who[k][l][litem])  )
		else:
			if who.keys().count(which) == 0:
				self.log.warning("Warning","Element " + self.log.bold(which)  + " not found or not active")
			else:
				Log.Level = 0	
				self.log.log(str(which)+"\n","" )
				for k in who.keys():
					if which==k:
						mybatch=[]
						for elem in all:
						 if elem['name'] == which:
							mybatch = self.__getBatchSystem(elem)					
							self.__printBatchSystemInfo(mybatch)
							self.__printDatasetInfo(who[which])							
						break;

	def debug(self):
		print "TODO: debug mode"
		
#####################################################################                                           
#
#	Reading and variables functions
#
#####################################################################   			
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
					self.log.error("Config file error","'active' and 'name' are mandatory fields within an APP ... Skipping this entry")
					self.apps.remove(app)
					repeat = True
				else:
					if app['active'] and ( app.keys().count('datasets')==0 or app.keys().count('batch')==0 or app.keys().count('exe')==0  ):
						self.log.error("Config file Error"," 'datasets', 'exe' and 'batch' fields are required for any active APP: " + self.log.bold(app['name']) + " ... Skipping this entry")
						self.apps.remove(app)
						repeat = True		

		# set i_apps and self.a_apps
		self.i_apps = [ app['name'] for app in self.apps if not app['active'] ]	# List with the name of the inactive apps
		self.a_apps = dict( [ (app['name'],app['datasets']) for app in self.apps if app['active'] ]) # Dictionary Name->Array of datasets  of active apps
		
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
							self.log.error("Config file error","'name' and 'active' fields are required for any dataset in app: " + self.log.bold(napp) + " ... Skipping this dataset")
							self.a_apps[napp].remove(dataset)
							repeat = True
						elif dataset['active'] != True:
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
								if key!="name" and key!="script" and key!="monitor" and key!="submit"   and a.keys().count(key)==0 :
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
									if sk == 'outputs':
										for o in a[sk].keys():
											if  dataset.keys().count(sk)==0:
												dataset[sk]={}											
											dataset[sk][o] = a[sk][o] 											
									elif sk == 'metrics':
										for m in  a[sk]:
											if dataset.keys().count(sk)==0:
												dataset[sk]=[]
											dataset[sk].append(m)
									else:
										dataset[sk] = a[sk] 
								else:
									dataset[sk] = "" 		

						if dataset.keys().count('tasks_per_node')==0:
							self.log.error("Config file error"," Dataset of " + self.log.bold(appname) + " found without 'tasks_per_node' defined. This tag is mandatory!!!") 
							self.log.error("Please revise your configuration file !!!")
							sys.exit(1)	
						elif dataset.keys().count('numprocs')==0 :
							self.log.error("Config file error"," Dataset of " + self.log.bold(appname) + " found without 'numprocs'. This tag is mandatory!!!") 
							self.log.error("Please revise your configuration file !!!")
							sys.exit(1)	
						elif dataset.keys().count('outputs')==0 :
							self.log.error("Config file error"," Dataset of " + self.log.bold(appname) + " found without 'outputs'. This tag is mandatory!!!") 
							self.log.error("Please revise your configuration file !!!")
							sys.exit(1)	
						
						break # step out apps loop

		self.__substituteVarsForAnalysis(self.a_apps)
	
	def __readSynthetics(self,yaml_conf):
		""" Reads Synthetic section and do some error check """
		# set self.synths
		self.synths = yaml_conf['KaBS']['BENCH']['SYNTHETICS'] # Array of dictionaries with synthetic bench info: active, exe, name, etc...
		self.__sanityBasic(self.synths,"Synthetics")
		#set active Synthetics:
		self.a_synths = dict( [ (synth['name'],synth['datasets']) for synth in self.synths if synth['active'] ]) # Dictionary Name->Array of datasets  of active networks
		# update self.a_synths and remove inactive datasets ... also if there is no active dataset remove synthetic from the list of active items
		self.__updateActiveElements(self.a_synths,"Synthetics")
		self.__populateElements(self.a_synths, self.synths)
		self.__substituteVarsForAnalysis(self.a_synths)
	
	def __readNets(self,yaml_conf):
		""" Reads Networks section and do some error check """
		# set self.nets
		self.nets = yaml_conf['KaBS']['BENCH']['NETWORKS'] # Array of dictionaries with nets info: active, exe, name, etc...
		self.__sanityBasic(self.nets,"Networks")
		#set active networks:
		self.a_nets = dict( [ (net['name'],net['datasets']) for net in self.nets if net['active'] ]) # Dictionary Name->Array of datasets  of active networks
		# update self.a_nets and remove inactive datasets ... also if there is no active dataset remove network from the list of active networks
		self.__updateActiveElements( self.a_nets ,"Networks")
		self.__populateElements(self.a_nets ,self.nets)
		self.__substituteVarsForAnalysis(self.a_nets)

	def __readFilesystems(self,yaml_conf):
		""" Reads Filesystems section and do some error check """
		# set self.filesys
		self.filesys = yaml_conf['KaBS']['BENCH']['FILESYSTEMS'] # Array of dictionaries with filesystems info: active, exe, name, etc...
		self.__sanityBasic(self.filesys,"Filesystems")
		#set active filesystems:
		self.a_filesys = dict( [ (fs['name'],fs['datasets']) for fs in self.filesys if fs['active'] ]) # Dictionary Name->Array of datasets  of active filesystems
		# update self.a_filesys and remove inactive datasets ... also if there is no active dataset remove filesystem from the list of active filesystems
		self.__updateActiveElements( self.a_filesys ,"Filesystems")
		self.__populateElements(self.a_filesys ,self.filesys)
		self.__substituteVarsForAnalysis(self.a_filesys)


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

	# Substitute in the target string, all the matches contained in keysDict with the values in dataset[ ... ] 
	def __substitute( self, strTarget , keysDict, dataset  ):
		outputDict={}
		for sstr in keysDict.keys():
			reple = re.compile( keysDict[sstr] )	
			if reple.search( strTarget ) : # there is a match
				ndatasetsstr = re.sub(r'\s', '', str(dataset[sstr]) )	# security ... just remove all white spaces							
				if 	len(ndatasetsstr.split(','))<2 : # there is not a comma separated list:
							strTarget = reple.sub(ndatasetsstr,strTarget)									
				else: # there is a comma separated list,so we have to create an entry for every value (ie: numprocs could be a comma separated list)
					values = ndatasetsstr.split(',')
					for value in values: # create an entry for each value	 
						value = value.strip()	
						outputDict[str(value)] = self.__substitute( reple.sub(value,strTarget) , keysDict, dataset )
		
		if not outputDict :		
			return strTarget
		else:
			return outputDict
	
	def __substituteVarsForAnalysis(self,item):
		""" Inside a dataset; the ['outputs'] , ['args'], ['dependencies'] and ['exe'] fields may contain references to fields defined
			in the app. ie: one output name might contain the number of cpus used in the run.
			Additionally, the ['metrics'] elements may contain references to the outputs names defined above.
			So, this function does this replacements of the references to the right values. The convention used
			for a reference is %FIELD_NAME_IN_CAPITALS%	"""
		# Replace inline variables in the ['outputs'] section inside each dataset
		itemsToReplace=['outputs','dependencies','args','exe']
		for name in item.keys():	
			for dataset in item[name]:
				str2find = {}
				for nkey in dataset.keys():
					# to avoid cyclic dependencies, remove the entries to be replaced from the search list
					if nkey!='outputs' and  nkey!='metrics' and  nkey!='dependencies' and  nkey!='args' and  nkey!='exe': 
						str2find[nkey]= "%"+ nkey.upper() +"%"		
				for rkey in itemsToReplace:
					if dataset.keys().count(rkey) != 0:
						if rkey =='outputs':
							for outpkey in dataset[rkey].keys():
								if dataset[rkey][outpkey] != None: 
									 retValue = self.__substitute( dataset[rkey][outpkey] , str2find, dataset )	
									 if isinstance(retValue,dict):
										for retKey in retValue.keys():
											dataset[rkey]["#" + retKey + "#" + outpkey] = retValue[retKey]
										# and delete previous entry .. NOOOOOOOO dont delete cuz it will be used later on ... ie: metrics are not translated into a specific proc number until the end
										#del dataset[rkey][outpkey]
									 else:
										 dataset[rkey][outpkey] = retValue 
						else:
							if dataset[rkey] != None: 
								retValue = self.__substitute( dataset[rkey] , str2find, dataset )	
								if isinstance(retValue,dict):
									for retKey in retValue.keys():
										dataset["#" + retKey + "#" + rkey] = retValue[retKey]
									# and delete previous entry .. NOOOOOOOO dont delete cuz it will be used later on ... ie: metrics are not translated into a specific proc number until the end
									#del dataset[rkey]
								else:
									dataset[rkey]= retValue 					
									
		# Replace inline variables in the ['metrics'] section inside each dataset ...
		for name in item.keys():	
			for dataset in item[name]:
				str2find = {}
				for nkey in dataset['outputs'].keys():
					str2find[nkey]= "%"+ nkey.upper() +"%"
				for sstr in str2find.keys():
					reple = re.compile( str2find[sstr] );
					if ( dataset.keys().count('metrics') != 0 ):
						for metric in dataset['metrics']:
							for elem in metric:
								metric[elem] = reple.sub(dataset['outputs'][sstr],metric[elem])									
		
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
													
				if len( a_elems[elem] ) == 0:
					del(a_elems[elem])
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
									if sk == 'outputs':
										for o in a[sk].keys():
											if  dataset.keys().count(sk)==0:
												dataset[sk]={}											
											dataset[sk][o] = a[sk][o] 											
									elif sk == 'metrics':
										for m in  a[sk]:
											if dataset.keys().count(sk)==0:
												dataset[sk]=[]
											dataset[sk].append(m)
									else:											
										dataset[sk] = a[sk] 	
								else:
									dataset[sk] = "" 		
													
						if dataset.keys().count('tasks_per_node')==0:
							self.log.error("Config file error"," Dataset of " + self.log.bold(aname) + " found without 'tasks_per_node' defined. This tag is mandatory!!!") 
							self.log.error("Please revise your configuration file !!!")
							sys.exit(1)	
						elif dataset.keys().count('numprocs')==0 :
							self.log.error("Config file error"," Dataset of " + self.log.bold(aname) + " found without 'numprocs'. This tag is mandatory!!!") 
							self.log.error("Please revise your configuration file !!!")
							sys.exit(1)	
						elif dataset.keys().count('outputs')==0 :
							self.log.error("Config file error"," Dataset of " + self.log.bold(aname) + " found without 'outputs'. This tag is mandatory!!!") 
							self.log.error("Please revise your configuration file !!!")
							sys.exit(1)	
								
						break # step out 'a' loop		
		
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
					if elem['active'] and ( elem.keys().count('datasets')==0 or elem.keys().count('batch')==0  ):
						self.log.error("Config file Error"," 'datasets', and 'batch' fields are required for any active "+mstr+": " + self.log.bold(elem['name']) + " ... Skipping this entry")
						self.elems.remove(elem)
						repeat = True	
										
#####################################################################                                           
#
#	Init and read conf YAML
#
#####################################################################   		
	def __readYaml(self, yaml_conf):
		"""Parse the yaml_conf structure and reads the configuration variables needed. Also do some basic correctness and sanity check"""	
		# some basic error correctness
		if yaml_conf.keys().count('KaBS') ==0:
			self.log.error("Config file error", "KaBS head tag is not defined") 
			sys.exit(1)	
		if yaml_conf['KaBS'].keys().count("HOME") == 0 or \
		   yaml_conf['KaBS'].keys().count("OUTPUTS") == 0 or \
		   yaml_conf['KaBS'].keys().count("BATCH") == 0 or \
		   yaml_conf['KaBS'].keys().count("BENCH") == 0:
			self.log.error("Config file error","HOME, OUTPUTS, BATCH and BENCH must be defined")
			sys.exit(1)			

		#######################################################################################
		# Set important variables
		
		# set home
		self.home = yaml_conf['KaBS']['HOME']
		if self.home == None: 
			self.log.error("Config file error","HOME must be defined")
			sys.exit(1) 

		#set outputs
		self.output_dir = yaml_conf['KaBS']['OUTPUTS']
		if re.match("[^/]",self.output_dir):
			self.output_dir = self.home + "/" + self.output_dir
		
		# set batchs
		self.batchs = yaml_conf['KaBS']['BATCH']
		if self.batchs==None:
			self.log.error("Config file error","at least one BATCH must be defined")
			sys.exit(1)	
		# set absolute path to the scripts and do some error check
		for nbatch in self.batchs:
			if nbatch.keys().count('name')==0 or nbatch.keys().count('submit')==0:
				self.log.error("Config file error"," 'name' and 'submit' tags are mandatory in the BATCH" )
				sys.exit(1)
			if nbatch['submit'] == None : 
				self.log.error("Config file error","'submit' tag in one of your BATCHs is empty")
				sys.exit(1)	
			if  nbatch['name'] != "NONE" and nbatch['name']!=None:
				if  nbatch.keys().count('script')==0:
					self.log.error("Config file error"," 'script' tag is mandatory in an a BATCH unless you name it as 'NONE'")
					sys.exit(1)
				if nbatch['script']!=None:
					if re.match("[^/]",nbatch['script']):
						nbatch['script'] = self.home + "/etc/" + nbatch['script']
				else:
					self.log.error("Config file error","Missing 'script' in one of your non 'NONE' BATCHs")
					sys.exit(1)			
			else:
				if nbatch['name']==None:
					self.log.error("Config file error","Missing 'name' in one of your BATCHs")
					sys.exit(1)	
		
		# Verify that the main tags ni BENCH section exist
		if (yaml_conf['KaBS']['BENCH'].keys().count('APPS') == 0) or \
			(yaml_conf['KaBS']['BENCH'].keys().count('FILESYSTEMS') == 0) or \
			(yaml_conf['KaBS']['BENCH'].keys().count('NETWORKS') == 0) or \
			(yaml_conf['KaBS']['BENCH'].keys().count('SYNTHETICS') == 0) :		
			self.log.error("Config file error","'APPS','FILESYSTEMS','NETWORKS','SYNTHETICS' tags are mandatory inside BENCH")
			sys.exit(1)	
			
		# and fill each one if them:	
		self.__readApps(yaml_conf)
		self.__readNets(yaml_conf)
		self.__readSynthetics(yaml_conf)
		self.__readFilesystems(yaml_conf)
														
		# End setting variables
		########################################################################################
		
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
		self.__substituteVarsInBatch_NONE()

		
#####################################################################                                           
#
#	Main Program entry point
#
#####################################################################                                           
if __name__ == "__main__":

	# ARGS processing
	usage = "%prog <Option> [ [<Selector>] [<arg>] ]"
	parser = optparse.OptionParser(usage=usage,version='%prog version 0.8')
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
	groupRun.add_option("-s", action="store", help="Select a specific synthetic benchmark.", dest='s')
	groupRun.add_option("-f", action="store", help="Select a specific filesystem benchmark",dest='f')
#	groupRun.add_option("-x", action="store_true", help="Select the Acceptance benchmark", default=False,dest='x')
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
#			elif attr=='s' :
#				sel_counter = sel_counter +1
		elif ( attr=='a'  or  attr=='n' or  attr=='f' or  attr=='s') and value != None:
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
#		if  ( ( attr=='a'  or  attr=='n' or  attr=='f' or  attr=='s' ) and value!= None) or ( attr=='x' and value==True):
		if  ( ( attr=='a'  or  attr=='n' or  attr=='f' or  attr=='s' ) and value!= None) :
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

			
			