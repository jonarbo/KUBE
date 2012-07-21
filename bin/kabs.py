#!/usr/bin/python

# import system issues
import sys
import os, inspect
import getopt
import re
import shutil
import datetime
import subprocess	
	
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


apps = yaml_conf['KaBS']['BENCH']['APPS'] # Array of dictionaries with apps info: active, exe, name, etc...

output_dir = yaml_conf['KaBS']['OUTPUTS']
if re.match("[^/]",output_dir):
	output_dir = home + "/" + output_dir

for app in apps:
	if  app.keys().count('name')==0 or \
		app.keys().count('active')==0:
		print "Config file error: 'active' and 'name' are mandatory fields within an APP: "
		sys.exit(1)
	else:
		if app['active'] and app.keys().count('dataset')==0:
			print "Config file error: 'dataset' field required for an active APP: " + app['name']
			sys.exit(1)

i_apps = [ app['name'] for app in apps if not app['active'] ]	# List with the name of the inactive apps
a_apps =dict( [ (app['name'],app['dataset']) for app in apps if app['active'] ]) # Dictionary Name->Array of datasets  of active apps
# update a_apps and remove inactive datasets... also if there is no active dataset remove app from the list of active apps
for napp in a_apps.keys():	
		for dataset in a_apps[napp]:
			if dataset['active'] != True:
				a_apps[napp].remove(dataset)
		if len( a_apps[napp] ) == 0:
			del(a_apps[napp])
# populate a_apps -> datasets with the app parameters if they are not already set in the dataset:			
for appname in a_apps.keys():	
	for dataset in a_apps[appname]:
		for a in apps:	
 			if a['name'] == appname:	
  				if  a.keys().count('batch')==0 or \
 			 		a.keys().count('exe')==0:
 			 		print "Config file error: 'batch' and 'exe' are mandatory fields within an active APP: " + appname
 			 		sys.exit(1)
 				for sk in a.keys():
					if sk=="batch": # Force the dataset to use always the batch system defined  for the app
									# the 'batch' parameter is global to the app, not dataset specific 
						dataset[sk] = a[sk]
					elif  dataset.keys().count(sk)==0 and sk!="name" and sk!="dataset" and sk!="active" :
						if a[sk] != None:
							dataset[sk] = a[sk] 
						else:
							dataset[sk] = "" 
							
									
# End setting global variables
########################################################################################
 
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
		
				
def usage():
	print """
	Usage: ./kabs.py  [OPTIONS]
            -h Display this usage message
            -d Debug mode: Show the actions to be performed
            -c <arg> Show the current configuration
               <arg>: Argument to -c option is one of: A,a,n,s,f,m 
            -r <arg> Run the benchmark for the selected item
               <arg>: Argument to -r option is one of: a,n,s,f,m                            
	"""

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
					if litem != 'name':
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
	
def conf(item = () ):
	
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
		if (len(sys.argv) != 4):
			print "Unknown options"
			usage()
			sys.exit(2)	
		else:
			printAppsInfo(sys.argv[3])	
	
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
	else:
		print "Not known item " + str(item) + "\nAllowed items are one of: [ A, a, f, n, s, m ]"

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

def run(item):
	if item == 'a':
		print "********************************************"
		print  "*** "+L0+" Running KaBS for selected App: "+ L1+ sys.argv[3] + LE+" ***"	
		if (len(sys.argv) != 4):
			print "Unknown options"
			usage()
			sys.exit(2)	
		else:
			runApp(sys.argv[3])	
			
	elif item == 'n':		
		pass
	elif item == 'f':
		pass
	elif item == 's':
		pass
	elif item == 'm':
		pass
	else:
		print "Unknown flag: " + str(item) + "\nAllowed flags is one of: [ a, f, n, s, m ]"


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
		newname = datetime.datetime.now().isoformat() 
		
		############# 
		# Run dataset
		#############
		nprocs = str(dataset['numprocs']).split(',')
		if len(nprocs) == 0:
			print L2 + "No procs found ... dataset " + str( dataset['name'] )  +" skipped"	+ LE
			continue
		
		print "---------------------------------------------------------"
		for p in nprocs:
			run_id = dataset['name'] + "_" + p + "cpus_"  + str(newname)
			print "Run ID: " + L1 + run_id + LE , 
			# change dir name to identify as an unique outcome		
			shutil.copytree(  dataset['name'] , run_id )		

			# create the same identifier in the outcomes dir:
			# os.makedirs( target + "outcomes/"  +run_id )
		
			# get the script or the command to run it
			data = getAppBatchScript(dataset,p)
									
			# submit or run job
			if  dataset['batch'] == "NONE":
				# No batch system found .... 
				rpath = t + run_id 
				os.chdir(rpath)  
				syscall( data )
			else:
				o = open( run_id + "/run.batch","w")	
				o.write(data)
				o.close		
				# get the batch system submission commands	
				mybatch = getBatchSystem(dataset)
				submit_cmd = mybatch['submit']['command']
				submit_params = mybatch['submit']['parameters']	
				syscall( str( submit_cmd +" " + submit_params  + " run.batch" ) )					
			
			print "... Submitted"
		
		shutil.rmtree(  dataset['name'] )	
	
def syscall(str):
	process = subprocess.Popen( str , shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
	output,stderr = process.communicate()		
	return process.wait()	
	
#####################################################################                                           
if __name__ == "__main__":

	# ARGS processing
	try:
        	opts, args = getopt.getopt(sys.argv[1:], "hdc:r:", ["help", "debug", "conf=","run=","clean"])
	except getopt.GetoptError, err:
        	# print help information and exit:
		print str(err) # will print something like "option -a not recognized"
		usage()
		sys.exit(2)

	for o, a in opts:
		if o in ("-h", "--help"):
			usage()
			sys.exit(0)
		elif o in ("-d", "--debug"):
			debug()
			sys.exit(0)	
		elif o in ("-c","--conf"):
			conf(a)
			sys.exit(0)
		elif o in ("-r","--run"):
			run(a)
		elif o in ("--clean"):
			print L1 + "Cleaning..." + LE
			print "You are about to remove all stored results from previous runs" 
			var = raw_input("Are you sure you want to do that? (Yes/No)")	
			if var=="Yes":
				clean(output_dir+"/runs/")
				clean(output_dir+"/analysis/")
 				print L1 + "Done." + LE
			else:
				print L1+ "Cleaning cancelled" + LE
		else:
			assert False, "unhandled option"

	#print yaml_conf
	
			