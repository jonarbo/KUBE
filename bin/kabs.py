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

LIB_DIR = cmd_folder + "/../lib"
CONF_FILE_PATH = cmd_folder + "/../etc/"
CONF_FILE_NAME = "kabs.yaml"

# Some colors to print 
L0="\033[1m"  # Bold
L1="\033[94m" # Blue 
L2="\033[92m" # Green
LE="\033[0;0m"

# include LIB_DIR in the module search path 
if LIB_DIR not in sys.path:
        sys.path.insert(0, LIB_DIR)

# import YAML 
import yaml

# read configuration file
try:
	stream = file(CONF_FILE_PATH+CONF_FILE_NAME, 'r')
except IOError as e:
    print "I/O error({0}): {1}".format(e.errno, e.strerror)

# global variable holding the configuration 
yaml_conf = yaml.load( stream )

# some basic error correctness
if yaml_conf.keys().count('KaBS') ==0:
	print "Config file error: KaBS head tag is not defined" 
	sys.exit(1)	
if yaml_conf['KaBS'].keys().count("HOME") == 0 or \
   yaml_conf['KaBS'].keys().count("OUTPUTS") == 0 or \
   yaml_conf['KaBS'].keys().count("BATCH") == 0 or \
   yaml_conf['KaBS'].keys().count("BENCH") == 0:
	print "Config file error: HOME, OUTPUTS, BATCH and BENCH must be defined" 
	sys.exit(1)	


########################################################################################
# Set some global vars
home = yaml_conf['KaBS']['HOME']
if home == None: 
	print "Config file error: HOME must be defined" 
	sys.exit(1)	

batchs = yaml_conf['KaBS']['BATCH']
if batchs==None:
	print "Config file error: at least one BATCH must be defined" 
	sys.exit(1)	
# set absolute path to the scripts and do some error check
for nbatch in batchs:
	if nbatch.keys().count('name')==0 or nbatch.keys().count('submit')==0:
		print "Config file error: 'name' and 'submit' tags are mandatory in the BATCH" 
		sys.exit(1)
	if nbatch['submit'] == None:
		print "Config file error: 'submit' tag in one of your BATCHs is empty" 
		sys.exit(1)	
	if  str(nbatch['name']) != "NONE" and nbatch['name']!=None:
		if  nbatch.keys().count('script')==0:
			print "Config file error: 'script' tag is mandatory in an a BATCH unless you name it as 'NONE'" 
			sys.exit(1)
		if nbatch['script']!=None:
			if re.match("[^/]",nbatch['script']):
				nbatch['script'] = home + "/etc/" + nbatch['script']
		else:
			print "Config file error: Missing 'script' in one of your non 'NONE' BATCHs" 
			sys.exit(1)			
	else:
		if nbatch['name']==None:
			print "Config file error: Missing 'name' in one of your BATCHs" 
			sys.exit(1)	


if (yaml_conf['KaBS']['BENCH'].keys().count('APPS') == 0) or \
	(yaml_conf['KaBS']['BENCH'].keys().count('FILESYSTEM') == 0) or \
	(yaml_conf['KaBS']['BENCH'].keys().count('MATHLIBS') == 0) or \
	(yaml_conf['KaBS']['BENCH'].keys().count('NETWORKS') == 0) or \
	(yaml_conf['KaBS']['BENCH'].keys().count('SYNTHETIC') == 0) or \
	(yaml_conf['KaBS']['BENCH'].keys().count('ACCEPTANCE') == 0):			
	print "Config file error: 'APPS','FILESYSTEM','MATHLIBS','NETWORKS','SYNTHETIC','ACCEPTANCE' tags are mandatory inside BENCH" 
	sys.exit(1)	
apps = yaml_conf['KaBS']['BENCH']['APPS'] # Array of dictionaries with apps info: active, exe, name, etc...

output_dir = yaml_conf['KaBS']['OUTPUTS']
if re.match("[^/]",output_dir):
	output_dir = home + "/" + output_dir

for app in apps:
	if  app.keys().count('name')==0 or \
		app.keys().count('active')==0:
		print "Config file error: 'active' and 'name' are mandatory fields within an APP.\nSkipping this entry"
		apps.remove(app)
	else:
		if app['active'] and ( app.keys().count('dataset')==0 or app.keys().count('batch')==0 or app.keys().count('exe')==0  ):
			print "Config file error: 'dataset', 'exe' and 'batch' fields are required for any active APP: " + app['name'] + ".\nSkipping this entry"
			apps.remove(app)
i_apps = [ app['name'] for app in apps if not app['active'] ]	# List with the name of the inactive apps
a_apps =dict( [ (app['name'],app['dataset']) for app in apps if app['active'] ]) # Dictionary Name->Array of datasets  of active apps

# update a_apps and remove inactive datasets... also if there is no active dataset remove app from the list of active apps
for napp in a_apps.keys():	
		for dataset in a_apps[napp]:
			if dataset.keys().count('name')==0 or dataset.keys().count('active')==0 or dataset.keys().count('analysis')==0:
				print "Config file error: 'name', 'active' and 'analysis' fields are required for any dataset in app: " + napp + ".\nSkipping this dataset"
				a_apps[napp].remove(dataset)
			elif dataset['active'] != True:
				a_apps[napp].remove(dataset)
		if len( a_apps[napp] ) == 0:
			del(a_apps[napp])

# populate apps with the batch parameters if they are not already set in the app:
for appname in a_apps.keys():	
	for a in apps:	
		if a['name'] == appname:	 			
			for batch in batchs: 
				if batch['name'] == a['batch']:
					for key in batch.keys():
						if key!="name" and key!="script" and key!="submittedmsg" and key!="submit" and a.keys().count(key)==0 :
							a[key] = batch[key]				
					break # step out the batch loop
			break # step out apps loop
# populate a_apps -> datasets with the app parameters if they are not already set in the dataset:			
for appname in a_apps.keys():	
	for dataset in a_apps[appname]:
		for a in apps:	
 			if a['name'] == appname:	
 				for sk in a.keys():
					if sk=="batch": # Force the dataset to use always the batch system defined  for the app
									# the 'batch' parameter is global to the app, not dataset specific 
						dataset[sk] = a[sk]
					elif  dataset.keys().count(sk)==0 and sk!="name" and sk!="dataset" and sk!="active" and sk!="analysis" :
						if a[sk] != None:
							dataset[sk] = a[sk] 
						else:
							dataset[sk] = "" 		
												
				if dataset.keys().count('numprocs')==0 or dataset.keys().count('tasks_per_node')==0:
					print "Config file error: Dataset of " + appname + " found without 'numprocs' and/or 'tasks_per_node' defined. This tags are mandatory!!!\nPlease revise your configuration file" 
					sys.exit(1)	
				break # step out apps loop
									
# End setting global variables
########################################################################################

# Replace inline variables in the ['analysis']['outputs'] section inside each dataset
for appname in a_apps.keys():	
	for dataset in a_apps[appname]:
		str2find = {}
		for nkey in dataset.keys():
			if nkey!='analysis' : 
				str2find[nkey]= "%"+ nkey.upper() +"%"		
		for sstr in str2find.keys():
			reple = re.compile( str2find[sstr] )			
			ndatasetsstr = re.sub(r'\s', '', str(dataset[sstr]) )	# security ... just remove all white spaces		
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
for appname in a_apps.keys():	
	for dataset in a_apps[appname]:
		str2find = {}
		for nkey in dataset['analysis']['outputs'].keys():
			str2find[nkey]= "%"+ nkey.upper() +"%"
		for sstr in str2find.keys():
			reple = re.compile( str2find[sstr] );
			for metric in dataset['analysis']['metrics']:
				for elem in metric:
					metric[elem] = reple.sub(dataset['analysis']['outputs'][sstr],metric[elem])			
 
# Replace inline variables in batch: NONE section	
for batch in batchs: 	
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
    
    
def getBatchSystem(whichapp):	 # parameter can be a dataset or an app since it holds the same value.
	for batch in batchs:
		if batch['name'] == whichapp['batch']:
	 		return batch 		
	return None	 	
		
def getAppBatchScript(whichdataset,p):
	batch =  getBatchSystem(whichdataset)	
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
	
def printAppsInfo(which):
	if which=="All":
		print "\t"+L0+"Inactive Apps:" + LE,
		print i_apps
		print "\t"+L0+"Active Apps:" + LE 
		for k in a_apps.keys():
 			print "\t\t"+L1+ k  + LE + " with:"
			
			for l in range(len(a_apps[k])):
				print "\t\t\tdataset: "+L1 + str( a_apps[k][l]['name']) + LE 
				for litem in  a_apps[k][l]:
					if litem != 'name' and litem != 'analysis':
						print "\t\t\t\t"+litem +": "+L1 + str( a_apps[k][l][litem]) + LE 
	else:
		if a_apps.keys().count(which) == 0:
			print "Application " + which  + " not found or not active"
		else:
			for k in a_apps.keys():
				if which==k:
					mybatch=[]
					for tapp in apps:
					 if tapp['name'] == which:
						mybatch = getBatchSystem(tapp)
					submit_cmd = mybatch['submit']['command']
					submit_params = mybatch['submit']['parameters']	
					if  mybatch == None or mybatch['name'] == "NONE":
						# No batch system found .... 
						print "No batch system specified for app: " + L1 + which + LE
						print "Submission command: "
						print "\t" + submit_cmd +" " + submit_params 	
					else:
						submit_script = mybatch['script']
						print "Using "  + L1 + mybatch['name'] + LE + " for app: " + L1 + which + LE
						print "Submission command: "
						print "\t" + submit_cmd +" " + submit_params # + " " + submit_script					
					print "\n"
					
					for   dataset in a_apps[which]:
						nprocs = str(dataset['numprocs']).split(',')
						if len(nprocs) == 0:
							print L2 + "No procs found ... dataset " + str( dataset['name'] )  +" skipped"	+ LE
							continue
					
						for p in nprocs:
							print "dataset: "+L1 + str( dataset['name'] ) + LE  + " with " + L1 + p + LE + " procs"
							print "Submission script:\n"
							data = getAppBatchScript(dataset,p,)
							print data
							print "-------------------------------------------------"									
					break;
					
def printFSInfo():
	print "\t"+L0+"Filesysytems:"+LE

def printSynthInfo():
	print "\t"+L0+"Synthetic:"+LE

def printNetInfo():
	print "\t"+L0+"Networks:"+LE

def printMathlibInfo():
	print "\t"+L0+"Math Libs:"+LE

def printAcceptanceInfo():
	print "\t"+L0+"Acceptance:"+LE	
	
def conf(item , name ):
	
	print  "*************************************************************"
	print  "*** "+L0+" Current configuration for the KAUST Benchmark Suite "+LE+" ***"	
	print  "*************************************************************"

	if item == 'A':	

		print L0 + "KaBS Home:" + LE + home
		print L0 + "KaBS Otputs: " + LE + output_dir
		print L0 + "KaBS Batch Systems: " + LE
		
		for nbatch in batchs:
			print "\t" + L1 + nbatch['name'] +": "+ LE
			if  str(nbatch['name']) != "NONE" :
				print "\t\tSubmission script: " + L1 + nbatch['script'] + LE
			print "\t\tSubmission command: " + L1 + nbatch['submit']['command'] + ' '+ nbatch['submit']['parameters'] + LE
					
		print L0+"Items to Benchmark:"+ LE
		printAppsInfo("All")	
		printFSInfo()
		printNetInfo()
		printSynthInfo()
		printMathlibInfo()
  
	elif item == 'a':
		print  "*** "+L0+" Showing configuration for selected App "+ LE+" ***"	
		printAppsInfo(name)	
	
	elif item == 'f':
		print  "*** "+L0+" Showing configuration for Filesystems "+LE+" ***"	
		printFSInfo()
	elif item == 'n':
		print  "*** "+L0+" Showing configuration for Networks "+LE+" ***"	
		printNetInfo()
	elif item == 's':
		print  "*** "+L0+" Showing configuration for Synthetic benchmarks "+LE+" ***"	
		printSynthInfo()
	elif item == 'm':
		print  "*** "+L0+" Showing configuration for Math Libs "+LE+" ***"	
		printMathlibInfo()
	elif item == 'x':
		print  "*** "+L0+" Showing configuration for the Acceptance benchmark "+LE+" ***"	
		printAcceptanceInfo()	
	else:
		print "Unknown item: '" + str(item) + "'"

def debug():
	print "TODO: debug mode"

######################################################################
def clean(dir):
	for d in os.listdir(dir):
		if os.path.isdir(dir+"/"+d) == True:
			clean(dir+"/"+d)
			os.rmdir( dir +"/"+d)	
		else:
			os.remove(dir+"/"+d) 			

def runAll():
	pass

def analysisAll():
	pass

def analysisApp(name):
	app = a_apps[name]
	analysisd = home + "/results/analysis/"+ name + "/"
	runsd = home + "/results/runs/"+ name + "/"
	if not os.path.exists(runsd):
		print "Can't find any completed run for this app: " + L1+ name + LE
		sys.exit(1)
	if not os.path.exists(analysisd):
		os.makedirs(analysisd)
	for dataset in app:
		rundir = runsd + dataset['name']	
		analysisdir = analysisd +dataset['name']
		if not os.path.exists(analysisdir):
			os.makedirs(analysisdir)
		# Analyze every run which is not already been analyzed
		runs = os.listdir(rundir)
		canalysis =  os.listdir(analysisdir)		
		if  len(canalysis)!=0:
			for a in canalysis:
				for r in runs:
					if r==a:
						# Found the same dataset in the analysis dir...
						# if it is not empty we will assume the analysis phase has been done
						if len(os.listdir( analysisdir+'/'+a ))!=0:
							runs.remove(r)
							break
		u = runs			
  		if len(u) == 0:
   			print "No new runs to analize"
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
   				mobj = prog.match(outp) 
   				if mobj:
   					if mobj.group(1)==cpus: 
   						if os.path.isfile(rundir + "/" + i + "/" + dataset['analysis']['outputs'][outp]) :					
	   						shutil.copy( rundir + "/" + i + "/" + dataset['analysis']['outputs'][outp] , "./")
						else:
							print "Warning: File " + L1 +  rundir + "/" + i + "/" + dataset['analysis']['outputs'][outp] + LE + " Does not exist."
				else:
					if os.path.isfile(rundir + "/" + i + "/" + dataset['analysis']['outputs'][outp]) :					
						shutil.copy( rundir + "/" + i + "/" + dataset['analysis']['outputs'][outp] , "./")
					else:
						print "Warning: File " + L1 +  rundir + "/" + i + "/" + dataset['analysis']['outputs'][outp] + LE + " Does not exist."

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
		
		
		
	
def analysis(item,name):
	if item == 'a':
		print "***********************************************"
		print  "*** "+L0+" KaBS analysis stage for selected App: " + LE+" ***"	
		print "***********************************************"
		print  L1+ name + LE + "\n"
		if a_apps.keys().count(name) == 0:
			print "Application " +  L1+ name + LE + " not found or not active"	
			return
		analysisApp(name)	
			
	elif item == 'n':		
		pass
	elif item == 'f':
		pass
	elif item == 's':
		pass
	elif item == 'm':
		pass
	elif item == 'x':
		pass	
	else:
		print "Unknown item: '" + str(item) + "'"
	
def run(item,name):
	if item == 'a':
		print "********************************************"
		print  "*** "+L0+" Running KaBS for selected App:      " + LE + "***"
		print "********************************************"
		print  L1+ name + LE + "\n"
		if a_apps.keys().count(name) == 0:
			print "Application " +  L1+ name + LE + " not found or not active"	
			return
			
		runApp(name)	
			
	elif item == 'n':		
		pass
	elif item == 'f':
		pass
	elif item == 's':
		pass
	elif item == 'm':
		pass
	elif item == 'x':
		pass	
	else:
		print "Unknown item: '" + str(item) + "'"

def runApp(whichapp):
	app = a_apps[whichapp]
	source=home + "/bench/apps/"+ whichapp + "/"
	target=output_dir + "/"
	for dataset in app:
		print "\n"
		print "Dataset: " + L1+ dataset['name'] +LE
		s = source+dataset['name']+".tgz" 	
		if not os.path.exists(s):
			print "Dataset Error: Could not find: " + s
			sys.exit(1)        	
		t = target+"runs/"+whichapp+"/"+dataset['name'] +"/"
		if not os.path.exists(t):
			os.makedirs(t)
	
		# Uncompress dataset:
		cwd = os.getcwd()
		file = s  
		print "Unpacking file: "+ L1+  file + LE
		cmd = "tar -zxf " + file 
		print cmd
		os.chdir(t)
		os.system(cmd)
		
		# remove tgz and generate time stamp to be use in the dir names
		now = datetime.datetime.now()
		newname = str(now.strftime("%Y-%m-%dT%H:%M:%S"))
		#newname = str(now.year) + "-" + str(now.month) + "-" + str(now.day) + "T" + str(now.hour) + ":" + str(now.minute)+ ":" + str(now.second)
				
		############# 
		# Run dataset
		#############
		nprocs = str(dataset['numprocs']).split(',')
		if len(nprocs) == 0:
			print L2 + "No procs found ... dataset " + str( dataset['name'] )  +" skipped"	+ LE
			continue
		
		print "---------------------------------------------------------"
		for p in nprocs:
			
			if dataset['tasks_per_node'] != None and  dataset['tasks_per_node'] != '':
				n = str( int(round ( float(p)/float(dataset['tasks_per_node'])))  )			
				run_id = dataset['name'] + "_" + p + "cpus_" + n + "nodes_"  + str(newname)					
			else:
				run_id = dataset['name'] + "_" + p + "cpus_"  + str(newname)
			
			print "Run ID: " + L1 + run_id + LE , 
			# change dir name to identify as an unique outcome	

			if os.path.isdir( run_id ):
				print "\n\tDirectory: " + L1+  run_id  + LE +" already exists" + ".\n\tTrying to run the same dataset in less than a second."
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

			# create the same identifier in the outcomes dir:
			# os.makedirs( target + "outcomes/"  +run_id )
		
			# get the script or the command to run it
			data = getAppBatchScript(dataset,p)

			rpath = t + run_id 
			os.chdir(rpath)  
							
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
				mybatch = getBatchSystem(dataset)
				submit_cmd = mybatch['submit']['command']
				submit_params = mybatch['submit']['parameters']	
				
				if submit_params=="<":
					cmd =  " cat run.batch |  " + submit_cmd
				else:
					cmd = submit_cmd + " " + submit_params + " run.batch"
				
				out,err = syscall( cmd )					
				sopattern = mybatch['submittedmsg']
				sopattern = sopattern.replace("%JOBID%","(\d+)")
 				mobj = re.search(sopattern,out)
 				if mobj:
					jobid = mobj.group(1)
					cmd = "touch batch.jobid." + jobid
					syscall( cmd )
					print "... Submitted"
				else:
					print L1 + "\n\tWarning: "+ LE + "It seems there was a problem while submitting this job.\n\tPlease read the following error message:"
					print "\t\t" + L1  +  err + LE	
													
			os.chdir("..")		
			
		shutil.rmtree(  dataset['name'] )	

def kiviat(template,target):		
	print "Reading data from template analysis: " + L1 + template + LE
	tf = open(template+"/analysis.raw", 'r') 
	theta = []
	radio = []
	metrics = []
	radio.append([])
	tfc = tf.readline()
	while tfc:		
		line = tfc.split()
		metrics.append(line[0])	
		theta.append(line[1])
		radio[0].append(line[2])
		tfc = tf.readline()
	tf.close
		
	print "Reading data from target analysis:"
	if (os.path.isfile(target+"/analysis.raw")):
		print "\t" + L1 + target + LE
		tf = open(target+"/analysis.raw", 'r') 
		ofc = tf.readline()
		radio.append([])
		while ofc:
			line = ofc.split()
			radio[len(radio)-1].append(line[2])
			ofc = tf.readline()	
		tf.close

	u = os.listdir(target)
	for file in u:
		if os.path.isfile(target + "/" + file + "/analysis.raw"):
			print "\t" + L1 + target + "/"+ file + LE
			tf = open(target + "/" + file+"/analysis.raw", 'r') 
			ofc = tf.readline()
			radio.append([])
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
				
	plotstr = "plot 'kanalysis.raw' using 2:3 with linespoints"	
	for l in range(4,len(radio)+3):
		plotstr = plotstr + " ,  'kanalysis.raw' using 2:" + str(l) + " with  linespoints" 

	kf.write( plotstr )
	kf.flush()
	kf.close()
	
	print len(radio)
	
	# and call it
	print syscall ( "gnuplot -persist " + gnuplotfile )[1]
	
def syscall(str):	
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
		
#####################################################################                                           
if __name__ == "__main__":

	# ARGS processing
	usage = "%prog <Option> [ [<Selector>] [<arg>] ]"
	parser = optparse.OptionParser(usage=usage,version='%prog version 0.1')
	parser.add_option("--clean", action="store_true", help="Remove all stored results from previous runs ", default=False,dest='clean')
	parser.add_option("-d", "--debug", action="store_true", help="Debug mode: Show the actions to be performed", default=False,dest='d')
	parser.add_option("-r", "--run", action="store_true",   help="Run the whole benchmark or a specific item according to the 'Selectors' below", default=False,dest='r')
	parser.add_option("-c", "--configuration" ,action="store_true", help="Show the benchmark global configuration or a specific item configuration according to the 'Selectors' below ", default=False,dest='c')	
	parser.add_option("-p", "--postprocess",action="store_true", help="Perform the Postprocess/Analysis stage for the whole benchmark or for a specific item according to the 'Selectors' below .", default=False,dest='p')	
	parser.add_option("-k", "--kiviat", nargs=2 ,action="store" , dest='k')	
		
	groupRun = optparse.OptionGroup(parser, "Selectors")
	groupRun.add_option("-a", action="store", help="Select a specific application" , dest='app')
	groupRun.add_option("-n", action="store", help="Select a specific network benchmark",dest='net')
	groupRun.add_option("-s", action="store_true", help="Select the synthetic benchmark.", default=False,dest='s')
	groupRun.add_option("-f", action="store", help="Select a specific filesystem benchmark",dest='filesystem')
	groupRun.add_option("-m", action="store", help="Select a specific mathlib benchmark",dest='mathlib')
	groupRun.add_option("-x", action="store_true", help="Select the Acceptance benchmark", default=False,dest='x')
	parser.add_option_group(groupRun)
		
	(opts, args) = parser.parse_args()

	if opts.clean == True:
		print L1 + "Cleaning..." + LE
		print "You are about to remove all stored results from previous runs" 
		var = raw_input("Are you sure you want to do that? (Yes/No)")	
		if var=="Yes":
			clean(output_dir+"/runs/")
			clean(output_dir+"/analysis/")
 			print L1 + "Done." + LE
		else:
			print L1+ "Cleaning cancelled" + LE
		sys.exit(0)	

	#
	# Arguments check
	#
	if len(sys.argv)>4 or len(args)>0:
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
			elif attr=='s' or attr=='A' :
				sel_counter = sel_counter +1
		elif ( attr=='app'  or  attr=='net' or  attr=='filesystem' or  attr=='mathlib' ) and value != None:
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
		if  ( ( attr=='app'  or  attr=='net' or  attr=='filesystem' or  attr=='mathlib'  ) and value!= None) or ( ( attr=='s' or attr=='x' ) and value==True):
			# got selector
			selector = attr
			itemname = value

	#
	# RUN 
	#
	if option == "d":
		debug()
	
	elif option == "c":
		if selector=='' :
			selector="All"
		conf(selector[0],itemname)
	
	elif option =="r":
		if selector=='' :
			runAll()
		else:
			run(selector[0],itemname)	
	
	elif option == "p":
		if selector=='' :
			analysisRun()
		else:
			analysis(selector[0],itemname)	
	
	elif option == "k":
		kiviat(itemname[0],itemname[1])
		
	else:
		assert False, "unhandled option"
			
	sys.exit(0)