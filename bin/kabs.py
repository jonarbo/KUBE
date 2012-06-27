#!/usr/bin/python

# import system issues
import sys
import os, inspect
import getopt

# get the path to the current script
cmd_folder = os.path.abspath(os.path.split(inspect.getfile( inspect.currentframe() ))[0])

LIB_DIR = cmd_folder + "/../lib"
CONF_FILE_PATH = cmd_folder + "/../etc/"
CONF_FILE_NAME = "kabs.yaml"

# include LIB_DIR in the module search path 
if LIB_DIR not in sys.path:
        sys.path.insert(0, LIB_DIR)


# import YAML 
import yaml

# read configuration file
stream = file(CONF_FILE_PATH+CONF_FILE_NAME, 'r')

# global variable holding the configuration 
yaml_conf = yaml.load( stream )

# some global vars
home = yaml_conf['KaBS']['HOME']
apps = yaml_conf['KaBS']['BENCH']['APPS']
outputs = home+"/results/"
submit_cmd = yaml_conf['KaBS']['BATCH']['SUBMIT']['COMMAND']
submit_params = yaml_conf['KaBS']['BATCH']['SUBMIT']['PARAMETERS']
submit_script = yaml_conf['KaBS']['BATCH']['SCRIPT']
i_apps = [ app['name'] for app in apps if not app['active'] ]	
a_apps =dict( [ (app['name'],app['dataset']) for app in apps if app['active'] ])


# Some color to print 
L0="\033[1m"  # Bold
L1="\033[94m" # Blue 
L2="\033[92m" # Green
LE="\033[0;0m"

def usage():
	print """
	Usage: ./kabs.py  [OPTIONS]
     		-h Display this usage message
     		-d Debug mode: Show the actions to be performed
		-c Show the current configuration
			Argument to -c option is one of: all,a,n,s,f,m 
	"""

def printAppsInfo(which):
	if which=="All":
		print "\t"+L0+"Inactive Apps:" + LE,
		print i_apps
		print "\t"+L0+"Active Apps:" + LE 
		for k in a_apps.keys():
			print "\t\t"+L1+ k  + LE + " with:"
			for l in range(len(a_apps[k])):
				if len(a_apps[k][l]) > 1:
					if a_apps[k][l]['active'] :
						print "\t\t\tdataset: "+L1 + str( a_apps[k][l]['name']) + LE 	
				else:
					if a_apps[k][1]['active']  and a_apps[k][l].keys().count('name'):
						print "\t\t\tdataset: "+L1+ str(a_apps[k][0]['name']) + LE
			
			for a in  yaml_conf['KaBS']['BENCH']['APPS']:
				if  a['name'] == k :
					for sk in a.keys():
						if sk!="name" and sk!="dataset" and sk!="active":
							print "\t\t\t"+sk+": "+ L1 + str(a[sk]) + LE

	else:
		if a_apps.keys().count(which) == 0:
			print "Application " + which  + " not found"	


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
	
		print L0+"Batch system settings: "+LE
		print "\t"+L1+"Submission command: "+LE+  submit_cmd + " " + submit_params
		print "\t"+L1+"Submission script template: "+LE + ""  + submit_script
		batch_script= file(CONF_FILE_PATH+submit_script ,'r')
		print "\t\t----------------------------------------------"
   		while True:
      			line = batch_script.readline()
      			if len(line) == 0:
       	  			break	
 			print "\t\t" + line.strip()
		print "\t\t----------------------------------------------"
		batch_script.close()
		print L0+"Items to Benchmark:"+ LE
		
		printAppsInfo("All")	
		printFSInfo()
		printNetInfo()
		printSynthInfo()
		printMathlibInfo()
  
	elif item == 'a':
		print  "*** "+L0+" Showing configuration for Apps "+LE+" ***"	
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

#####################################################################                                           
if __name__ == "__main__":

	# ARGS processing
	try:
        	opts, args = getopt.getopt(sys.argv[1:], "hdc:", ["help", "debug", "conf="])
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
		else:
			assert False, "unhandled option"

	print a_apps

	for k in a_apps.keys():
		for a in  yaml_conf['KaBS']['BENCH']['APPS']:
			if  a['name'] == k :
				for sk in a.keys():
					if sk!="name" and sk!="dataset" and sk!="active":
						print "\t\t\t"+sk+": "+ L1 + str(a[sk]) + LE
