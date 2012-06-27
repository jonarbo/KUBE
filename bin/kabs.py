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
	"""

def conf(yamldict):
	
	print  "*************************************************************"
	print  "*** "+L0+" Current configuration for the KAUST Benchmark Suite "+LE+" ***"	
	print  "*************************************************************"

	home = yaml_conf['KaBS']['HOME']
	apps = yaml_conf['KaBS']['BENCH']['APPS']
	outputs = home+"/results/"
	submit_cmd = yaml_conf['KaBS']['BATCH']['SUBMIT']['COMMAND']
	submit_params = yaml_conf['KaBS']['BATCH']['SUBMIT']['PARAMETERS']
	submit_script = yaml_conf['KaBS']['BATCH']['SCRIPT']
	
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
	print "\t"+L0+"Inactive Apps:" + LE,
	print [ app['name'] for app in apps if not app['active'] ]	
	print "\t"+L0+"Active Apps:" + LE 
	xapps =dict( [ (app['name'],app['dataset']) for app in apps if app['active'] ])

	for k in xapps.keys():
		print "\t\t"+L1+ k  + LE + " with dataset:"
		for l in range(len(xapps[k])):
			if len(xapps[k][l]) > 1:
				if xapps[k][l]['active'] :
					print "\t\t\t"+L1 + str( xapps[k][l]['name']) + LE 	
			else:
				if xapps[k][1]['active']  and xapps[k][l].keys().count('name'):
					print "\t\t\t"+L1+ str(xapps[k][0]['name']) + LE

	
	print "\t"+L0+"Filesysytems:"+LE
	print "\t"+L0+"Networks:"+LE
	print "\t"+L0+"Synthetic:"+LE
	print "\t"+L0+"Math Libs:"+LE


def readConf():
	pass

def debug():
	print "TODO: debug mode"

#####################################################################                                           
if __name__ == "__main__":

	# ARGS processing
	try:
        	opts, args = getopt.getopt(sys.argv[1:], "hdc", ["help", "debug", "conf"])
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
			conf(yaml_conf)
			sys.exit(0)
		else:
			assert False, "unhandled option"






