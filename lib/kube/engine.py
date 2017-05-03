#!/usr/bin/env python
# coding: utf-8

from kube.printer import *
from kube.utils import * 

# import system issues
import sys
import glob
import os, inspect
import re
import shutil
import datetime, time
import math
import copy
import stat

# get the path to the current script
cmd_folder = os.path.abspath(os.path.split(inspect.getfile( inspect.currentframe() ))[0])

######################################################
#
#  main Class 
#
######################################################
class KUBE:
	
	##################
	# Class variables
	LIB_DIR = cmd_folder + "/../../lib"
	CONF_FILE_PATH = cmd_folder + "/../../etc/"
	CONF_FILE_NAME = "kube.yaml"
	
#####################################################################                                           
#
#	Getters functions
#
#####################################################################  					
	def __getBatchSystem(self,which):	 # parameter can be a dataset or an app since it holds the same values.
		""" Returns the batch object for a specific dataset or app
		"""
		for batch in self.batchs:
			if batch['name'] == which['batch']:
	 			return batch 		
		return None	 			
		
	def __getBatchScript(self,whichdataset,p):
		""" Returns the batch script or the submission command for a specific dataset and cpu number
			Here takes place the final fields reference replacements: Any left reference in the batch script or a submission command
			to the tags in a dataset will be done here
		"""
		batch =  self.__getBatchSystem(whichdataset)	
		
		if (whichdataset.keys().count('script') != 0):	
			submit_script = whichdataset['script']
		elif (batch.keys().count('script')!=0):
			submit_script = batch['script']
		else:
			printer.error("Missing script","Can't find any run/submission script for this batch system '"+batch['name']+"'" )
			sys.exit(1)	
		
		if re.match("[^/]",submit_script):
			submit_script = self.home + "/etc/" + submit_script
		
		try:
			file = open(submit_script,'r')
			data = file.read()
			file.close()		
		except:
			e = sys.exc_info()[0]
			printer.error("Script error","There was an error reading the file '"+ submit_script +"'" )
			print e
			sys.exit(1)	
			

		# replace variables
		for litem in  whichdataset:
			str2find = "%("+ str(litem).upper() +")%"
			prog = re.compile(str2find);
			if litem != 'numprocs':
				data = prog.sub( str(whichdataset[litem]) ,data)	
			else:
				(data,n) = prog.subn( str(p).strip() ,data)		
	
		if re.search("%.+%", data) != None:
			printer.error("Missing variable","I suspect that you missed to define some variable in the config file that is needed; presumably in the batch script." )
			sys.exit(1)	
				
		return data	

####################################################################                                           
#
#	Visualization (metrics bar plots) functions
#
#####################################################################  
	def metricAnalysis(self,template,target=None,printToSTDOUT=False,to=None,delta=None, lmetrics=None):		
		""" Shows a box plot of the metrics for the specified template and target
			Both arguments are directory path. The first is the path to the directory that holds the 
			results for a specific run. This will be used as the reference value.
			The second argument is also a path to a dir but now this dir can contain more dirs being each of 
			them the output for different runs (the results). All of them will be compared against the 
			template values.			
		"""
		
		if not template or not os.path.isdir(template) :
			printer.error("Error","Wrong arguments")
			sys.exit(1)
		
		template = os.path.abspath(template)
		
		printer.info( "Reading data from",template )
		
		if not os.path.exists(template+"/analysis.raw"):
			printer.error("Data File not found","The file " + printer.bold( template+"/analysis.raw") + " could not be found" )
			sys.exit(1)
			
		tf = open(template+"/analysis.raw", 'r') 
		timestamp = []
		m_values = []
		metrics = []
		legend = []
		units = []
		m_values.append([])
		tfc = tf.readline()
		timestamp.append( tfc.split()[3] )
		while tfc:		
			line = tfc.split()
			if lmetrics==None or line[0] in lmetrics:
				metrics.append(line[0])	
				units.append(line[1])
				#timestamp.append(line[4])
				m_values[0].append(line[2])							
			tfc = tf.readline()
		tf.close

		if len(metrics)==0:
			return

		if template[len(template)-1] == '/':
			template = template[:-1] 	

		# set the legend from the run name:
		template = os.path.abspath(template)	
		title_rundate_template = os.path.basename(template)
		title_runcase_template=''
		if len(title_rundate_template)==0:
			title_rundate_template = os.path.basename( str(os.path.dirname(template))[1:len(str(os.path.dirname(template)))] )
			title_runcase_template = os.path.dirname( str(os.path.dirname(template))[1:len(str(os.path.dirname(template)))]  )
		else:
			title_runcase_template = os.path.dirname(template)
		title_dataset_template =  os.path.basename( os.path.dirname( title_runcase_template  ))	
		title_app_template = os.path.basename( os.path.dirname( os.path.dirname(title_runcase_template )) )
		title_runcase_template = os.path.basename(title_runcase_template)
		#legend.append( "Benchmark:"+title_app_template +" , Dataset:"+ title_dataset_template   +" , Run:"+ title_runcase_template)	
		legend.append( title_dataset_template   +" => "+ title_runcase_template)			

		u=[]
		t=[]
			
		if target:	
			t = target.split(',')

		for target in t:		
			if target and target[len(target)-1] == '/':
				target = target[:-1] 	
	
			# filter directories by date
			if target and os.path.isdir(target):
				for d  in walkDir(target , to, delta):
					u.append(d)

		if len(u) == 0 :
			if target:	
				#printer.plain("Reading data from target:")
				if (os.path.isfile(target+"/analysis.raw")):
					Printer.Level = 1
					#printer.plain( printer.bold(target ))
	
				 	target = os.path.abspath(target)	
					title_rundate_target = os.path.basename(target)
					title_runcase_target=''
					if len(title_rundate_target)==0:
						title_rundate_target = os.path.basename( str(os.path.dirname(target))[1:len(str(os.path.dirname(target)))] )
						title_runcase_target = os.path.dirname( str(os.path.dirname(target))[1:len(str(os.path.dirname(target)))]  )
					else:
						title_runcase_target = os.path.dirname(target)
					title_dataset_target =  os.path.basename( os.path.dirname( title_runcase_target  ))	
					title_app_target = os.path.basename( os.path.dirname( os.path.dirname(title_runcase_target )) )
					title_runcase_target = os.path.basename(title_runcase_target)
					#legend.append( "Benchmark:"+title_app_target +" , Dataset:"+ title_dataset_target   +" , Run:"+ title_runcase_target)						
					legend.append( title_dataset_target   +" => "+ title_runcase_target)										
				
					if not os.path.exists(target+"/analysis.raw"):
						printer.error("Data File not found","The file " + printer.bold( target+"/analysis.raw") + " could not be found" )
						sys.exit(1)
					tf = open(target+"/analysis.raw", 'r') 
					ofc = tf.readline()
					m_values.append([])
					while ofc:					
						line = ofc.split()
						if lmetrics == None or  line[0] in lmetrics:
							m_values[len(m_values)-1].append(line[2])
							timestamp.append(line[3])
						ofc = tf.readline()	
					tf.close
		else:
			for file in u:
				target = os.path.abspath(file)	

				# skip the template dir if present	
				if target == template:
					continue

				title_rundate_target = os.path.basename(target)
				title_runcase_target=''
				if len(title_rundate_target)==0:
					title_rundate_target = os.path.basename( str(os.path.dirname(target))[1:len(str(os.path.dirname(target)))] )
					title_runcase_target = os.path.dirname( str(os.path.dirname(target))[1:len(str(os.path.dirname(target)))]  )
				else:
					title_runcase_target = os.path.dirname(target)
				title_dataset_target =  os.path.basename( os.path.dirname( title_runcase_target  ))	
				title_app_target = os.path.basename( os.path.dirname( os.path.dirname(title_runcase_target )) )
				title_runcase_target = os.path.basename(title_runcase_target)
				#legend.append( "Benchmark:" + title_app_target +" ==> Dataset:"+ title_dataset_target   +" ==> Run:"+ title_runcase_target)						
				legend.append( title_dataset_target   +" => "+ title_runcase_target)						
				
				if os.path.isfile( file + "/analysis.raw"):
					Printer.Level = 1
					#printer.plain( printer.bold(file ) )
				
					if not os.path.exists( file+"/analysis.raw"):
						printer.error("Data File not found","The file " + printer.bold( target + "/" + file+"/analysis.raw") + " could not be found...skipping" )
						continue
				
					tf = open( file+"/analysis.raw", 'r') 
					ofc = tf.readline()
					m_values.append([])
					#legend.append(os.path.basename(file))
					timestamp.append( ofc.split()[3] )

					while ofc:
						line = ofc.split()
						if lmetrics == None or line[0] in lmetrics :
							m_values[len(m_values)-1].append(line[2])
						ofc = tf.readline()	
					tf.close
	
		if printToSTDOUT:
			mnvalue = 0
			if len(metrics)>0:
				for t in range(0,len(metrics)):			
					printer.info("Metric",metrics[t])
					for l in range(0,len(m_values)):
						nvalue = float(m_values[l][t])			
						printer.plain( legend[l]+ " => " + timestamp[l] + " "  +  str(nvalue) )
			return		

		of = open(template + "/.metrics_analysis.raw", 'w') 	
		mnvalue = 0
		if len(metrics)>1:
			for t in range(0,len(metrics)):			
				lineout = metrics[t] + '\\n'+ str( str(float(m_values[0][t]))) + '\\n' + units[t] + ' ' +  str(float(m_values[0][t])) + ' ' 
				for l in range(0,len(m_values)):
					nvalue = float(m_values[l][t])/float(m_values[0][t])			
					lineout = lineout +  str(nvalue) + ' '  # normalizar respecto al patron			
				of.write(lineout  + "\n")
		else:
			lineout = metrics[0] + '\\n'+ str( str(float(m_values[0][0]))) + '\\n' + units[0] + ' ' +  str(float(m_values[0][0])) + ' ' 
			for l in range(0,len(m_values)):
				nvalue = float(m_values[l][0])
				lineout = lineout +  str(nvalue) + ' ' 		
			of.write(lineout  + "\n")
							
		of.flush()
		of.close
	
		# create gnuplot file
		gnuplotfile = template + "/.metrics.gnuplot"
		kf = open(gnuplotfile,'w')
		kf.write(
		"""
set boxwidth 0.9 relative
set style data histograms
set style histogram cluster
#set key autotitle columnhead
set style fill solid 0.2 border lt -1
set grid
set bmargin 5
#set term qt persist title 'KUBE'   font 'sans'
set term x11 persist title 'KUBE'  font 'sans' 
""") 
#		plotstr = "plot '" + template + "/.metrics_analysis.raw' every ::1 using 2:xtic(1) title '" + legend[0]+ " Date: " + timestamp[0] +"' "
#		plotstr = plotstr +  ", for [n=3:"+ str(len(m_values)+1) + "]  '' u (column(n)) title columnhead(n) " 
		plotstr = "plot '" + template + "/.metrics_analysis.raw' using 3:xtic(1) title '" + legend[0]+ " => " + timestamp[0] +"' "
		for n in range(4,len(m_values)+3):
			plotstr = plotstr +  ", '' u " + str(n) + " title '" + legend[n-3]+ " => " + timestamp[n-3] +"' "

		kf.write( plotstr )
		kf.write("\npause -1\n")
		kf.flush()
		kf.close()
			
		# and call it
		syscall ( "gnuplot " + gnuplotfile )[1]

#####################################################################                                           
#
#	Display time evolution of the metrics
#
#####################################################################  
	def timeAnalysis(self,target,metric_names,printToSTDOUT=False,to=None,delta=None):		
		""" Shows the time evolution of the metrics found in the 'target' dir.
			'target' must contain a list of directories created 
			in the postprocess stage that contain the analysis.raw file.
			For instance:		
			data/results/apps/namd/namd_apoa1/4cpus_1nodes 
		"""
		
		if not target:
			printer.error("Wrong arguments","Target dir arguments needed")
			sys.exit(1)
			
 		metrics = []
 		# set the legend from the run name:
		target = os.path.abspath(target)	
		title_run = os.path.basename(target)
		title_dataset=''
		if len(title_run)==0:
			title_run = os.path.basename( str(os.path.dirname(target))[1:len(str(os.path.dirname(target)))] )
			title_dataset = os.path.dirname( str(os.path.dirname(target))[1:len(str(os.path.dirname(target)))]  )
		else:
			title_dataset = os.path.dirname(target)
		title_bench =  os.path.basename( os.path.dirname( title_dataset  ))	
		title_dataset = os.path.basename(title_dataset)
				
		printer.info( "Reading data from", target ) 

		if not os.path.isdir(target):
			printer.error("Wrong argument","Path to directory expected")
			sys.exit(1)
		
		u=[]	
		# filter directories by date
		if to and delta:
			for d  in walkDir(target , to, delta):
				u.append( os.path.basename(d) )
		else:
			if os.path.isdir(target):
				for d in glob.glob(target+"/*"): # dont see hidden files
					u.append(os.path.basename(d) )
					#u = os.listdir(target)
		
		for file in u:
			if os.path.isfile(target + "/" + file + "/analysis.raw"):    # and os.path.isfile(target + "/" + file + "/timestamp"):
				Printer.Level = 1
				printer.info("-", target + "/"+ file)
				
				if not os.path.exists(target + "/" + file+"/analysis.raw"):  # or  not os.path.exists(target + "/" + file+"/timestamp")  :
					printer.error("Data File not found","The file " + printer.bold( target + "/" + file+"/analysis.raw") + " could not be found...skipping" )
					continue
								
				tf = open(target + "/" + file+"/analysis.raw", 'r') 
				ofc = tf.readline()

				metrics.append({})			
				while ofc:
					line = ofc.split()
					if metric_names==None or ( metric_names!=None and line[0] in metric_names ): 
						if len(line)>4:
							metrics[len(metrics)-1][line[0]] = ( line[2],line[3],line[1],line[4],line[5],line[6] ) 
						else:
							metrics[len(metrics)-1][line[0]] = ( line[2],line[3],line[1] ) 
					ofc = tf.readline()
				if len( metrics[len(metrics)-1]) == 0:
					metrics.pop()	
				tf.close
			else:
				if os.path.isfile(target + "/" + file):
					printer.warning("Warning",printer.bold( file ) + " is not a directory")
				else:		
					printer.warning("Warning","No data found in " + printer.bold(target + "/" + file)  )
		
		if len(metrics)==0:
			printer.warning("Warning","No metric information found!!!")
			return
	
		ofname={}
		if printToSTDOUT:
			while len(metrics)>0:
				mname = None
				for me in metrics:
					if len(me.keys()) == 0:
						return
					if  mname == None:
						mname = me.keys()[0]
 						printer.info("Metric",str(mname))					
					if len(me[mname])>3 :
						v_4 = me[mname][4]
						v_5 = me[mname][5]
						printer.plain( me[mname][1] + ' ' +me[mname][0] + ' ' + me[mname][3] + ' ' + v_4  + ' ' + v_5 )
					else:
						printer.plain( me[mname][1] + ' ' + me[mname][0] )					
					del me[mname]
				mname = None
			return			
		
		for m in metrics:
			for name in m.keys():
				if ofname.keys().count(name) == 0:
					ofname[name] =[ open( target + "/." + name + ".raw", 'w'),'' ] 
				if len(m[name])>3:
					v_4 = m[name][4]
					v_5 = m[name][5]
					ofname[name][0].write( m[name][1].replace('T',"\\n") + ' ' + m[name][0] + ' ' + m[name][3] + ' ' + v_4  + ' ' + v_5 +  '\n' )
				else:
					ofname[name][0].write( m[name][1].replace('T',"\\n") + ' ' + m[name][0] +  '\n' )
				ofname[name][1] =  m[name][2]
				ofname[name][0].flush()

		# now close the files
		donelist = []
		for m in metrics:
			for name in m.keys():
				if not name in donelist and ofname.keys().count(name) != 0:
					ofname[name][0].close()
					ofname[name][0] = open( target + "/." + name + ".raw", 'r') 	
					lines = [line for line in ofname[name][0] if line.strip()]
					ofname[name][0].close()
					lines.sort()
					# now lines are sorted due to the Date format ;)
					nlines = [ str(i)+' '+lines[i] for i in range(0,len(lines)) ]	
					ofname[name][0] = open(target + "/." +  name + ".raw", 'w')
					ofname[name][0].writelines(nlines) 	
					ofname[name][0].close()
					donelist.append(name)

		nplots = len (metrics[0].keys())
		nplotsx = math.ceil(math.sqrt(nplots))
		nplotsy = math.ceil(nplots/nplotsx) if nplotsx!=0 else nplots

		# create gnuplot file
		gnuplotfile = target + "/." +  "metricsvstime.gnuplot"
		kf = open(gnuplotfile,'w')
		kf.write(
		"""
set clip points
unset border
set xtics axis 
set ytics axis 
set grid
set style fill solid 0.2
#set term qt persist size 1280,640 title 'KUBE'   font 'sans'
set term x11 persist title 'KUBE'  font 'sans'
set format y '%f'	
set bmargin 7
set xtics rotate
""")
		if len(ofname.keys()) >1:	
			for key in ofname.keys():		
				# dummy plot to get the range...
				kf.write( "plot '"+ target +"/." + key +".raw' u  1:3:xtic(2), ''  u 1:4 \nymax_" + key +  "=GPVAL_Y_MAX\nymin_" + key  +  "=GPVAL_Y_MIN\n")					
				
			kf.write("set key off\n")
			kf.write("set multiplot layout " + str(nplotsx) + "," + str(nplotsy) + " title \"Benchmark:" + title_bench + " , Dataset:"+ title_dataset+  " , Run:" + title_run + "\"\n")
			kf.write( "set mouse zoomjump\n")
			splotstr = " "
			for key in ofname.keys():		
				splotstr = splotstr + "set title \'"+ key + "\'\n"  # "\' font \'Bold\'\n"
				splotstr = splotstr + "set ylabel \'"+ ofname[key][1]  +"\'\n" 
		 		# now the plot
				splotstr = splotstr + "plot '" +  target +"/." + key + ".raw' using  1:3:xtic(2) with linespoint lt rgb \"blue\"  lw 2 title \"" + key + "\", '' u 1:($5!='inf'?($5!='-inf'?$5:ymin_"+key+"):ymax_"+key+") with linespoint lw 2 lt \'dotted\' lc rgb \'orange\' notitle , '' u 1:($6!='inf'?($6!='-inf'?$6:ymin_"+key+"):ymax_"+key+") with linespoint notitle lw 2 lt \'dotted\' lc rgb \'orange\',''  u 1:4 title 'reference' with linespoint lw 2 lt rgb \'green\'\n" 

			kf.write( splotstr )
			kf.write( "\nunset multiplot\n")
		else:	
			key = ofname.keys()[0]
			kf.write("set title \"Benchmark:" +title_bench + " , Dataset:"+ title_dataset+  " , Run:" + title_run + "\"\n")
			# dummy plot to get the range...
			kf.write( "plot '"+  target +"/." + key +".raw' u  1:3:xtic(2) , ''  u 1:4 \nymax=GPVAL_Y_MAX\nymin=GPVAL_Y_MIN\n")				
	 		# now the plot
			#kf.write( "plot '" +  target +"/." + key+ ".raw' using 1:3:xtic(2) with linespoint lt rgb \"blue\"  lw 2 title \"" + key + "\", '' u 1:($5!='inf'?($5!='-inf'?$5:ymin):ymax):($6!='inf'?($6!='-inf'?$6:ymin):ymax) with filledcu fs transparent pattern 4 lt rgb \"green\"  notitle  ,'' u 1:($5!='inf'?($5!='-inf'?$5:ymin):ymax) with linespoint lw 2 lt rgb \'red\' notitle , '' u 1:($6!='inf'?($6!='-inf'?$6:ymin):ymax) with linespoint notitle lw 2 lt rgb \'red\',''  u 1:4 title 'reference' with linespoint lw 2 lt rgb \'green\'\n" )
			kf.write( "plot '" +  target +"/." + key+ ".raw' using 1:3:xtic(2) with linespoint lt rgb \"blue\"  lw 2 title \"" + key + "\", '' u 1:($5!='inf'?($5!='-inf'?$5:ymin):ymax):($6!='inf'?($6!='-inf'?$6:ymin):ymax) with filledcu fs transparent solid 0.1 lt rgb \"green\"  notitle  ,'' u 1:($5!='inf'?($5!='-inf'?$5:ymin):ymax) with linespoint lw 4 lt \'dotted\' lc rgb \'green\' notitle , '' u 1:($6!='inf'?($6!='-inf'?$6:ymin):ymax) with linespoint notitle lw 4 lt \'dotted\' lc rgb \'green\',''  u 1:4 title 'reference' with linespoint lw 2 lt rgb \'green\'\n" )
			# this would allow to make zoom the the window but for some reason, when the window is closed the process still waits for something from the system and hangs..
			kf.write("pause -1\n")
		
			
		kf.flush()
		kf.close()
			
		# and call it
		syscall ( "gnuplot " + gnuplotfile )[1]


#####################################################################                                           
#
#	Post-Process (refine) functions
#
#####################################################################  
	def refine(self,item=None,name=None,To=None,Delta=None,rrd=False,force=False):
		""" Runs the refine stage for a given 'item' and 'name' 
		"""
		if item == None: # means analyze everything	
			for app in self.a_apps:
					self.__refineApp(app,To,Delta,rrd,force)
			for net in self.a_nets:
					self.__refineNet(net,To,Delta,rrd,force)
			for synth in self.a_synths:
					self.__refineSynthetics(synth,To,Delta,rrd,force)		
			for fs in self.a_filesys:
					self.__refineFilesystem(fs,To,Delta,rrd,force)		

		elif item == 'apps':
			printer.plain(printer.bold("***********************************************"))
			printer.plain(printer.bold("***")+"   KUBE refine stage for selected Apps:  " + printer.bold("***"))
			printer.plain(printer.bold("***********************************************"))
			if name and self.a_apps.keys().count(name) == 0:
				printer.warning( "Warning", "Application " +  printer.bold( name ) + " not found or not active"	)
				return
			if name:
				self.__refineApp(name,To,Delta,rrd,force)	
			else:
				for app in self.a_apps:	
					self.__refineApp(app,To,Delta,rrd,force)	

		elif item == 'nets':		
			printer.plain(printer.bold("***********************************************"))
			printer.plain(printer.bold("***") + "     KUBE refine stage for Networks:     "+printer.bold("***"))
			printer.plain(printer.bold("***********************************************"))
			if name and self.a_nets.keys().count(name) == 0:
				printer.warning( "Warning", "Network " +  printer.bold( name ) + " not found or not active"	)
				return
			if name:
				self.__refineNet(name,To,Delta,rrd,force)	
			else:
				for app in self.a_nets:	
					self.__refineNet(app,To,Delta,rrd,force)	

		elif item == 'filesys':
			printer.plain(printer.bold("***********************************************"))
			printer.plain(printer.bold("***")+"     KUBE refine stage for Filesystems:  " +printer.bold("***"))
			printer.plain(printer.bold("***********************************************"))
			if name and  self.a_filesys.keys().count(name) == 0:
				printer.warning( "Warning", "Filesystem " +  printer.bold( name ) + " not found or not active"	)
				return
			if name:
				self.__refineFilesystem(name,To,Delta,rrd,force)				
			else:
				for app in self.a_filesys:	
					self.__refineFilesystem(app,To,Delta,rrd,force)	

		elif item == 'synths':
			printer.plain(printer.bold("***********************************************"))
			printer.plain(printer.bold("***")+"     KUBE refine stage for  Synthetics:  "+printer.bold("***"))
			printer.plain(printer.bold("***********************************************"))
			if name and self.a_synths.keys().count(name) == 0:
				printer.warning( "Warning", "Benchmark " +  printer.bold( name ) + " not found or not active"	)
				return
			if name:
				self.__refineSynthetics(name,To,Delta,rrd,force)				
			else:
				for app in self.a_synths:	
					self.__refineSynthetics(app,To,Delta,rrd,force)	

		else:
			printer.error("Unknown item",  printer.bold(str(item)) ) 
		
		# after the analysis, remove runs that needs to be removed
		self.__cleanOldRuns()

	
	def __refineApp(self,name,To,Delta,rrd,force):
		"""  Performs the refine stage for an app. Go into the runs dir and identify the app and the dataset.
			 then creates a similar entry in the 'data/results' dir and copies the output files to the new location.
			 it also creates a .cvs and a .raw files with the metrics specified in the YAML config file. The .raw file is used later on
			 when visualizing the metric.
 		"""
 		printer.info("App", name )
		Printer.Level=Printer.Level+1
		app = self.a_apps[name]
		analysisd = self.results_dir + "/apps/"+ name + "/"
		runsd = self.runs_dir + "/apps/"+ name + "/"
		if not os.path.exists(runsd):
			printer.warning("There is no run dir for this app", printer.bold(name) )
		if not os.path.exists(analysisd):
			os.makedirs(analysisd)
		
		for dataset in app:
			self.__refineDataset(dataset,runsd,analysisd,To,Delta,rrd,force)			

		Printer.Level=Printer.Level-1

	def __refineSynthetics(self,name,To,Delta,rrd,force):
		printer.info("Synthetic", name )
		Printer.Level=Printer.Level+1
		synth = self.a_synths[name]
		analysisd = self.results_dir + "/synthetics/"+ name + "/"
		runsd = self.runs_dir + "/synthetics/"+ name + "/"
		if not os.path.exists(runsd):
			printer.warning("There is no run dir for this synthetic" , printer.bold(name) )
			#return
			#sys.exit(1)
		if not os.path.exists(analysisd):
			os.makedirs(analysisd)

		for dataset in synth:	
			self.__refineDataset(dataset,runsd,analysisd,To,Delta,rrd,force)		
		Printer.Level=Printer.Level-1

	def __refineFilesystem(self,name,To,Delta,rrd,force):
		printer.info("Filesystem", name )
		Printer.Level=Printer.Level+1
		fs = self.a_filesys[name]
		analysisd = self.results_dir + "/filesystems/"+ name + "/"
		runsd = self.runs_dir + "/runs/filesystems/"+ name + "/"
		if not os.path.exists(runsd):
			printer.warning("There is no run dir for this filesystem", printer.bold(name) )
			#return
			#sys.exit(1)
		if not os.path.exists(analysisd):
			os.makedirs(analysisd)
		
		for dataset in fs:
			self.__refineDataset(dataset,runsd,analysisd,To,Delta,rrd,force)	
		Printer.Level=Printer.Level-1
						
	def __refineNet(self,name,To,Delta,rrd,force):
		printer.info( "Network",name )
		Printer.Level=Printer.Level+1
		net = self.a_nets[name]
		analysisd = self.results_dir + "/networks/"+ name + "/"
		runsd = self.runs_dir + "/networks/"+ name + "/"
		if not os.path.exists(runsd):
			printer.warning("There is no run dir for this network",printer.bold(name) )
			#return
			#sys.exit(1)
		if not os.path.exists(analysisd):
			os.makedirs(analysisd)

		for dataset in net:		
			self.__refineDataset(dataset,runsd,analysisd,To,Delta,rrd,force)		
		Printer.Level=Printer.Level-1

	def __refineDataset(self,dataset,runsd,analysisd,To=None,Delta=None,rrd=False,force=False):
		import yaml
		import hashlib
		
		rundir = runsd + dataset['name']	
		allruns={}
		resultsdir = analysisd +dataset['name']
		allanalysis = {}
		filteredallanalysis = {}
		
		# 'digest' contains the global config settings md5 sum that affects this particular dataset
		m = hashlib.md5()		
		m.update( yaml.dump(dataset,default_flow_style=False) )
		digest = m.hexdigest()
		# name of the file that contains the digest
		digestFile = resultsdir+'/.'+dataset['name']+'.md5'

		# if analysis dir does not exists, create it, otherwise get the list of dirs to analyze
		if not os.path.exists(resultsdir):
			os.makedirs(resultsdir)
		else:
			if os.path.isdir(resultsdir):
				for r in os.listdir(resultsdir):
					if os.path.isdir(resultsdir+'/'+r):
						allanalysis[r] = os.listdir(resultsdir+'/'+r)	
						again = True	
						while again:
							again = False
							for d in allanalysis[r] :
								# remove dir that are not in the date format
								if not re.search("\d\d\d\d-\d\d-\d\dT\d\dh\d\dm\d\ds",d):
									allanalysis[r].remove(d)
									again = True						
						if To and Delta:
							# filter dirs by date
							filteredallanalysis[r] = []
							for d in walkDir(resultsdir+'/'+r,To,Delta):
								filteredallanalysis[r].append( os.path.basename(d) ) 

		configChanged = True
		# if file already exists ... Check if 
		# the config specifics for this dataset  
		# changed, this will avoid re-processing already existing data 
		if  os.path.isfile( digestFile  ) :
			# if digest file exists, read it and compare signatures.
			mydigest = file( digestFile, 'r' ).read()	
			if mydigest == digest:
				configChanged= False or force
			else:
 				file( digestFile, 'w' ).write(str(digest))
		else:
			# if digest file is not there, create it and assume this dataset needs to be analyzed.
 			file( digestFile, 'w' ).write(str(digest))
						
		printer.info( "Dataset",  dataset['name'] )	
		Printer.Level=Printer.Level+1
		# Analyze every run which is not already been analyzed
		if os.path.exists(rundir):
			try:
				allruns = dict( [ [r,os.listdir(rundir+'/'+r)] for r in os.listdir(rundir) if os.path.isdir(rundir+'/'+r)])
				# now remove the known failure dirs
				repeat = True
				while repeat and len(allruns.keys())!=0:
					repeat = False
					for k in allruns.keys():
						for r in allruns[k]:
							if re.match("INVALID_",r) !=	None or not os.path.isdir(rundir+'/'+k+'/'+r):
								allruns[k].remove(r)		
								repeat = True
				# now remove already analyzed runs
				for k in allruns.keys():
					repeat = True
					if k in allanalysis.keys():										
						while repeat and len(allruns[k])!=0:
							repeat = False
							for r in allruns[k]:
								if r in allanalysis[k]:
									allruns[k].remove(r)
									repeat = True
									break		
			except Exception as e:
				print e
				pass
				
		# now remove from the list the runs that are still running ...
		batch = self.__getBatchSystem(dataset)
		if batch != None:
			cmd = None		
			if batch.keys().count('monitor') != 0:
				cmd =  batch['monitor']
				if cmd != None:
					repeat = True
					while repeat and len(allruns.keys())!=0:
						repeat = False			
						for k in allruns.keys():
							for r in allruns[k]:
								if os.path.isdir( rundir + "/" + k + "/" + r ):
									files = os.listdir(rundir + "/" + k + "/" + r)
									for f in files:
										if re.match("batch.jobid",f) :
											jobid = re.search("\d+$",f).group(0)
											ncmd = re.sub("%JOBID%",jobid,cmd) 
											out,err = syscall( ncmd )	
											if out.strip()==jobid.strip():
												# the job is running ... remove it from the list	
												printer.warning("Skipping running job" , rundir + "/" + k + "/" + r )
												allruns[k].remove(r)
												repeat = True										
											break		
					
		# so far allruns contains only valid, new runs									
		u = allruns
		if len(filteredallanalysis)==0:
			a = allanalysis
		else:
			a = filteredallanalysis

		# if there is nothing in u (runs) and nothing has changed  .. skip dataset because there is nothing new
		if len( [v for v in u.values() if len(v) !=0 ]  )==0 and not configChanged: 
			printer.info( "Nothing changed", "Skipping dataset " + dataset['name'] )
			Printer.Level=Printer.Level-1
			return	

		# Add to the new runs list, the dirs already analyzed ... Only if they have changed 
		# New runs are ALWAYS refined ... only existing dirs in the results dir can be skipped
		if configChanged:
			for key in a.keys():
				if not key in u: 
					u[key] = a[key]
				else:
					# merge the existing runs with the new ones ..
					u[key] = u[key] + a[key]

		# At this point we either have new runs to process or we need to re-process existing results because we changed the config file
						
		if len(u) == 0:
			# this should never happen...only when running refine with no new runs and no previous results
			printer.warning("Nothing to refine")	
			Printer.Level=Printer.Level-1
			return
			
		pythonlibpath = self.rrdtool_root + '/lib/python' + str(sys.version_info.major) + '.' + str(sys.version_info.minor) + '/site-packages/'
		if rrd and not 	os.path.isdir(pythonlibpath):					
			printer.warning("RRDTool","Can't find a valid RRDTool instalation that matches this Python version or RRD is misconfigured in the config file")
			rrd = False
		else:
			sys.path.append( pythonlibpath )
			
		# Do the analysis ...
		START = 0.0
		END = 2*math.pi
		for rd in u:
	
			#get the cpus from the run name:
			str2find = "(\d+)cpus_"	
			reple = re.compile( str2find )
			mobj = reple.search(rd)
			cpus = mobj.group(1)

			# Prepare to update RRD tool
			epoch = datetime.datetime(1970, 1, 1)
			rrddatabasepath = dataset['rrdtool'] + '/' +  dataset['bench'] + '/' +  dataset['parent'] + '/' +  dataset['name'] + '/' + rd + '/'
			updatedatabasestr = {}
			if rrd:
				import rrdtool, tempfile
				if not os.path.isdir(rrddatabasepath):
					os.makedirs(rrddatabasepath)
				
				if dataset.keys().count('metrics') != 0:	
					for metric in  dataset['metrics']:
						if (metric.keys().count('name') != 0 and metric.keys().count('command') != 0 and metric.keys().count('units') != 0) :
							name= metric['name']		
							# first check if a file exists with the name of the metric
							rrddatabasefile = rrddatabasepath + name + '.rrd'
							if not os.path.isfile(rrddatabasefile):
								# create 	
								if len(name)>19 : # RRD Limitation
									name = name[0:18]
								rrdtool.create(  rrddatabasefile ,\
												 '--step', '21600', '--no-overwrite','--start', '1356998400',	# step 6h \
												 'DS:'+ name +':GAUGE:172800:U:U', 								# heartbeat 48h \
												 'RRA:AVERAGE:0.9:1:124',										# keep one sample every 6 hour for 1 month \
												 'RRA:AVERAGE:0.9:28:52',										# 1 week average for 1 year  \
												 'RRA:AVERAGE:0.9:124:24' 										# 1 month average for 2 years\
											   )																
						else:
							rrd=False
				else:
					rrd=False

			for i in u[rd]:
				printer.info("Run", rd +"/" +i )
				timestamp = i
				# change to analysis dir
				os.chdir( resultsdir )
				# create results dir for each  run
				if not os.path.exists(rd+"/"+i):
					# if not exists, create it and copy the necessary files ... 
					os.makedirs(rd+"/"+i)

					# Copy the outputs needed ...
					for outp in  dataset['outputs'].keys():
						failed = False
						mobj = re.match("#(\d+)#", outp)
						if mobj:
							# the output key contains a reference to the number of cpus used ...
							# this is it because we may have some different outputs' name 
							# related to the number of cpus used.	
							if mobj.group(1) == cpus:
								if os.path.isfile(rundir + "/" + rd + "/" + i + "/" + dataset['outputs'][outp]) :					
									shutil.copy( rundir + "/" + rd + "/" + i + "/" + dataset['outputs'][outp] , rd+"/"+i+"/")
								else:
									printer.warning("Warning","File " + printer.bold( rundir + "/" + rd + "/" + i + "/" + str(dataset['outputs'][outp]) ) + " Does not exist.")
									printer.error("Refine stage not completed!!!")
									failed = True
									shutil.rmtree( rd+"/"+i )	
									break
						else:
							# Now be sure to skip the key that originated the cpu dependency ...
							skip = False
							for again_outp in  dataset['outputs'].keys():				
								if re.match("#"+cpus+"#"+outp , again_outp):
									skip = True
									break								
							if not skip:
								if os.path.isfile(rundir + "/" + rd + "/" + i + "/" + dataset['outputs'][outp]) :					
									shutil.copy( rundir + "/" + rd + "/" + i + "/" + dataset['outputs'][outp] , rd + "/"+ i +"/")
								else:
									printer.warning("Warning","File " + printer.bold( rundir + "/" + rd + "/" + i + "/" + str(dataset['outputs'][outp]) ) + " Does not exist.")
									printer.error("Refine stage not completed!!!")
									shutil.rmtree(rd+"/"+i)								
									failed = True
									break		
					
					if failed == True:
						# TODO: mark run dir as INVALID
						thename = rundir + "/" + rd + "/" + i
						newname = rundir + "/" + rd + "/INVALID_" + i
 						shutil.move( thename , newname )
						continue
							
					# output data copied for this run
					# always analyze this run 
				else:
					if not configChanged:	
						continue		
				
				# only continue if available metrics ... 
				if dataset.keys().count('metrics') == 0:	
					continue
	
				# now crate a .csv and the .raw file suitable to be used later on with gnuplot...
				o = open( rd +"/"+i + "/analysis.csv","w")
				r = open( rd +"/"+i + "/analysis.raw","w")
				o.write(  "\"metric\",\"value\",\"units\",\"reference\",\"accuracy (%)\",\"validation\"\n" )
				STEP =  END/len(dataset['metrics'])	
				#theta = frange(START,END,STEP)		
				m_values = []
				metrics = []
				ref_value_a = []
				units_a = []
				threshold_a_u=[]
				threshold_a_l=[]
				os.chdir(rd + "/" + i)				

				# Now make the replacements and prepare commands ...
				if dataset.keys().count('metrics') != 0:	
		 			for metric in  dataset['metrics']:
						if not (metric.keys().count('name') != 0 and metric.keys().count('command') != 0 and metric.keys().count('units') != 0) :
							continue
					
						# Up to this point, values in Metrics may contain %VALUES% to be replaced ... so we have to do it now
						name= metric['name']
						command=metric['command']
						units=metric['units']
						reference  = ""
						accuracy   = ""
						validation = ""
						threshold  = ""
						threshold_type = ""
						tolerance  = ""
						ref_value  = ""
						refIsValue = True

						if metric.keys().count('reference') != 0:
							if not (metric['reference'].keys().count('threshold') != 0 and  metric['reference'].keys().count('threshold_type') != 0 and metric['reference'].keys().count('value') != 0 and metric['reference'].keys().count('tolerance') != 0):
								continue
							try:
								tolerance = metric['reference']['tolerance']	
								threshold = float(metric['reference']['threshold'])
								threshold_type = metric['reference']['threshold_type']
								reference = metric['reference']['value']									
								try:
									reference = float( reference )
									refIsValue = True			
								except:
									refIsValue = False			
	
							except:
								printer.warning( "Skipping metric", printer.bold(name) + " in dataset: " + printer.bold(dataset['name'])  + ". Please check out the config params for this metric." )
								continue

						# replace references to the output section						
						for outp in  dataset['outputs'].keys():
							if not re.match( "#\d+#",outp  ):
								reple = re.compile( "%"+str(outp).upper()+"%" )
								if dataset['outputs'].keys().count( "#"+cpus+"#"+outp) != 0:
									name    = reple.sub(  str(dataset['outputs']["#"+cpus+"#"+outp]) , name )	
									units   = reple.sub(  str(dataset['outputs']["#"+cpus+"#"+outp]) ,units )	
									command = reple.sub(  str(dataset['outputs']["#"+cpus+"#"+outp]) ,command )	
									if not refIsValue:
										reference = reple.sub(  str(dataset['outputs']["#"+cpus+"#"+outp]) ,reference )	
								else:
									name    = reple.sub(  str(dataset['outputs'][outp]) ,name )	
									units   = reple.sub(  str(dataset['outputs'][outp]) , units)	
									command = reple.sub(  str(dataset['outputs'][outp]) , command )	
									if not refIsValue:
										reference = reple.sub(  str(dataset['outputs'][outp]) ,reference )	
					
						# Now replace other variables from the dataset...
						for tagp in  dataset.keys():
							if tagp == 'numprocs':
								reple = re.compile( "%NUMPROCS%" )
								command = reple.sub( cpus , command)
								if not refIsValue:
									reference = reple.sub( cpus , reference)
							else:	
								# '%TOOLS%' does need ot be replaced since it was already done in __substituteVarsForAnalysis
								if not tagp in ['outputs','metrics','tools','common'] and not isinstance(dataset[tagp],dict):
									if not re.match( "#\d+#",tagp  ):
										reple = re.compile( "%"+str(tagp).upper()+"%" )
										if dataset.keys().count( "#"+cpus+"#"+tagp) != 0:
											toSubst = str(dataset["#"+cpus+"#"+tagp])	
											name    = reple.sub( toSubst , name    )	
											units   = reple.sub( toSubst , units   )	
											command = reple.sub( toSubst , command )	
											if not refIsValue:
												reference = reple.sub( toSubst , reference)
										else:
											toSubst = str(dataset[tagp])	
											name    = reple.sub( toSubst , name )	
											units   = reple.sub( toSubst , units )	
											command = reple.sub( toSubst , command)	
											if not refIsValue:
												reference = reple.sub( toSubst , reference)
						
						# Now compute this metric for this run 
						cmdoutput = syscall(command)
						command_value = cmdoutput[0].strip()	
						if len(cmdoutput[1].strip())!=0 or len(command_value)==0 :
							printer.error("Oppsss!!!","Some error found while trying to get the "+ printer.bold(metric['name']) + " information in "+ printer.bold(dataset['name']+ "/" + i) +"\nUsing the command: " + printer.bold(command) +"\nPlease, be sure the run data is in place and the data was copied to the results dir and if the execution ended correctly.")
							printer.warning("Warning","Marking this run as "+ printer.bold(" INVALID"))
							thename = rundir + "/" + rd + "/" + i
							newname = rundir + "/" + rd + "/INVALID_" + i
 							shutil.move( thename , newname )
 							printer.error("Refine stage not completed!!!")
							os.chdir("..") 	
							shutil.rmtree(i)	
							break
						else:	
							ref_value = reference if refIsValue else syscall(reference)[0].strip()
							if len(ref_value) != 0:
								try:
									accuracy = abs( ( float(command_value) - float(ref_value)  )/float(ref_value)) * 100
								
									if threshold_type.lower() == 'percentage':
										threshold_v = abs(float(ref_value)*(threshold/100))						
									elif threshold_type.lower() == 'absolute':								
										threshold_v = abs(threshold)						
	
									if tolerance.lower() == 'bilateral':
										validation = "Failed" if threshold<accuracy else "Passed"	
										threshold_a_u.append(float(ref_value)+threshold_v)
										threshold_a_l.append(float(ref_value)-threshold_v)
									elif tolerance.lower() == 'above':	
										validation = "Passed" if threshold>accuracy and ref_value<command_value else "Failed"						
										threshold_a_u.append(float(ref_value)+threshold_v)
										threshold_a_l.append(float(ref_value))
									elif tolerance.lower() == 'below':	
										validation = "Passed" if threshold>accuracy and ref_value>command_value else "Failed"						
										threshold_a_l.append(float(ref_value)-threshold_v)
										threshold_a_u.append(float(ref_value))
									o.write( "\"" + name + "\"," + "\"" + command_value +"\"," +"\"" + units + "\",\"" +  ref_value + "\",\"" + str(accuracy)  + "\",\"" + validation + "\"\n"  ) 
								except:
									continue	
							else:
								o.write( "\"" + name + "\"," + "\"" + command_value +"\"," +"\"" + units + "\"\n"  ) 
								threshold_a_l.append('')
								threshold_a_u.append('')
						
							m_values.append ( command_value )				
							ref_value_a.append(ref_value)
							metrics.append( name )
							if len(units)!=0:
								units_a.append(units)
							else:
								units_a.append('Unknown')
	
				# Finished proceesing the metrics. Close the csv file and prepare the raw file
				o.flush()
				o.close
				
				# compute the time in secs since 1970 to be used with rrd and append to the final dict
				#td = datetime.datetime.strptime(timestamp,'%Y-%m-%dT%Hh%Mm%Ss') - epoch
				#dt = [ td.days*86400+td.seconds ]*len(metrics)			
				#sort_dict = zip(metrics, units_a , m_values, ref_value_a, threshold_a_u, threshold_a_l ,dt)		
				
				sort_dict = zip(metrics, units_a , m_values, ref_value_a, threshold_a_u, threshold_a_l )		
				if sort_dict:
					for k in sort_dict:
						r.write( str(k[0]) + "  " + str(k[1])  + "  "  + str(k[2]) + "  "  + timestamp + "  " + str(k[3])  + "  " + str(k[4]) + "  " + str(k[5]) + "\n"  )
			
					# r.write( str(sort_dict[0][0]) + "  " + str(sort_dict[0][1]) + "  "  + str(sort_dict[0][2]) + "  "  + str(sort_dict[0][3]) + "  " + timestamp   + "  " + str(sort_dict[0][4]) + "  " + str(sort_dict[0][5]) + "  " + str(sort_dict[0][6]) + "\n"  )
				r.flush
				r.close		
				
				if rrd:
					if sort_dict:					
						for sd in sort_dict:		
							dt = datetime.datetime.strptime(i,'%Y-%m-%dT%Hh%Mm%Ss')
							td = dt-epoch
							if updatedatabasestr.keys().count(sd[0]) == 0:
								updatedatabasestr[sd[0]] = {}						
							updatedatabasestr[sd[0]][td.days*86400+td.seconds] = sd[2]
																
				os.chdir( resultsdir )

			# update rrd 
			if rrd:
				for uk in updatedatabasestr.keys():
					for sd in sorted(updatedatabasestr[uk].keys()):
							# only update if the date is greater than the last update ...
							if rrdtool.last( rrddatabasepath + uk + '.rrd') < sd:
								rrdtool.update(  rrddatabasepath + uk + '.rrd', str(sd)+':'+str(updatedatabasestr[uk][sd] ))

		Printer.Level=Printer.Level-1

#####################################################################                                           
#
#	RUN functions
#
#####################################################################  
	def run(self,item=None,name=None):
		""" Runs a given 'name' benchmark from 'item'
		"""
		if item == None: # means run everything			
			for app in self.a_apps:
					self.__runApp(app)
			for net in self.a_nets:
					self.__runNet(net)
			for synth in self.a_synths:
					self.__runSynthetics(synth)
			for fs in self.a_filesys:
					self.__runFilesys(fs)		
				
		elif item == 'apps':
			printer.plain(printer.bold("********************************************"))			
			printer.plain(printer.bold("***")+"  Running KUBE for selected Apps:     "+ printer.bold("***"))
			printer.plain(printer.bold("********************************************"))
			if name and self.a_apps.keys().count(name) == 0:
				printer.warning("Warning","Application " +  printer.bold(name) + " not found or not active"	)
				return		
			if  name:
				self.__runApp(name)	
			else:
				for app in self.a_apps:
					self.__runApp(app)
				
		elif item == 'nets':			
			printer.plain(printer.bold("********************************************"))			
			printer.plain(printer.bold("***")+"  Running KUBE for selected Networks: "+printer.bold("***"))
			printer.plain(printer.bold("********************************************"))
			if name  and self.a_nets.keys().count(name) == 0:
				printer.warning("Warning","Network " +  printer.bold(name) + " not found or not active"	)
				return		
			if  name:
				self.__runNet(name)
			else:
				for app in self.a_nets:
					self.__runNet(app)
				
		elif item == 'filesys':
			printer.plain(printer.bold("*********************************************"))
			printer.plain(printer.bold("***")+" Running KUBE for selected Filesystem: "+printer.bold("***"))
			printer.plain(printer.bold("*********************************************"))
			if name  and self.a_filesys.keys().count(name) == 0:
				printer.warning("Warning","Filesystem " +  printer.bold(name) + " not found or not active"	)
				return		
			if  name:
				self.__runFilesys(name)
			else:
				for app in self.a_filesys:
					self.__runFilesys(app)
		
		elif item == 'synths':
			printer.plain(printer.bold("**********************************************"))			
			printer.plain(printer.bold("***")+"  Running KUBE for selected Synthetics: "+printer.bold("***"))
			printer.plain(printer.bold("**********************************************"))
			print name, self.a_synths.keys()
			if name  and self.a_synths.keys().count(name) == 0:
				printer.warning("Warning","Benchmark " +  printer.bold(name) + " not found or not active"	)
				return		
			if  name:
				self.__runSynthetics(name)
			else:
				for app in self.a_synths:
					self.__runSynthetics(app)

		else:
			print "Unknown item: '" + str(item) + "'"

	def __runApp(self,which):
		""" Run the given app whose name is specified
		"""
		printer.info("App",which)
		Printer.Level = Printer.Level + 1
		app = self.a_apps[which]
		source = self.home + "/bench/apps/"+ which + "/"
		target = self.runs_dir + "/apps/" + which + "/"
		self.__runBasic(app,source,target,True)
		Printer.Level = Printer.Level - 1
	

	def __runSynthetics(self, which):
		""" Run the given Synthetic whose name is specified
		"""
		printer.info("Synthetic",which)
		Printer.Level = Printer.Level + 1
		synth = self.a_synths[which]
		source = self.home + "/bench/synthetics/"+ which + "/"
		target = self.runs_dir + "/synthetics/" + which + "/"
		self.__runBasic(synth,source,target)
		Printer.Level = Printer.Level - 1
		
	def __runNet(self, which):
		""" Run the given Network whose name is specified
		"""
		printer.info("Network",which)
		Printer.Level = Printer.Level + 1	
		net = self.a_nets[which]
		source = self.home + "/bench/networks/"+ which + "/"
		target = self.runs_dir +  "/networks/" + which + "/"
		self.__runBasic(net,source,target)
		Printer.Level = Printer.Level - 1
		
	def __runFilesys(self, which):
		""" Run the given Filesystem benchmark whose name is specified
		"""
		printer.info("Filesystem",which)
		Printer.Level = Printer.Level + 1	
		net = self.a_filesys[which]
		source = self.home + "/bench/filesystems/"+ which + "/"
		target = self.runs_dir + "/filesystems/" + which + "/"
		self.__runBasic(net,source,target)
		Printer.Level = Printer.Level - 1

	def __runBasic(self,bench,source,target,isApp=False):	
		for dataset in bench:
			printer.info( "Dataset" , printer.bold(dataset['name']) )
			Printer.Level = Printer.Level + 1
			if not os.path.exists(source):
				printer.error("Could not find" + source)
				Printer.Level = Printer.Level - 1	
				sys.exit(1)        	
			t = target + dataset['name'] +"/"
			if not os.path.exists(t):
				os.makedirs(t)
				os.makedirs(t + dataset['name'])
			elif not os.path.exists(t+dataset['name']):
				os.makedirs(t+dataset['name'])
				
			cwd = os.getcwd()
			os.chdir(t)					

			###########################
			# If App copy the dataset
			if isApp==True:
				#APP SPECIFIC PART!!!	
	 			s = source + dataset['name']+".tgz" 	
	 			if not os.path.exists(s):
	 				printer.error("Dataset Error","Could not find: " + s)
	 				sys.exit(1)       	
	 			# Uncompress dataset:
	 			file = s  
	 			printer.info( "Unpacking file"+ printer.bold( file ))
	 			cmd = "tar -zxf " + file 
	 			printer.info("Command", cmd)
	 			os.system(cmd)				

			self.__runDataset(dataset,source,t,isApp)
			shutil.rmtree(  dataset['name'] )		
			Printer.Level = Printer.Level - 1
			
	def __runDataset(self,dataset,source,t, isApp ):
		############# 
		# Run dataset
		#############
		now = datetime.datetime.now()
		newname = str(now.strftime("%Y-%m-%dT%Hh%Mm%Ss"))

		nprocs = str(dataset['numprocs']).split(',')
		if len(nprocs) == 0:
			printer.warning("No procs found in", printer.bold( str( dataset['name'] )) + " ... skipped")
			Printer.Level = Printer.Level - 1	
			return
		
		nnodes=[]
		if dataset.keys().count('nodes')!=0 and dataset['nodes'] != None and  dataset['nodes'] != '':
			nnodes = str(dataset['nodes']).split(',')	
		
		if len(nnodes)>1 and len(nnodes)!=len(nprocs):
			printer.warning("Misleading procs/nodes configuration found in", printer.bold( str( dataset['name'] )) + " ... skipped")
			Printer.Level = Printer.Level - 1	
			return

		nodesdict = dict(zip(nprocs, nnodes))

		printer.plain(printer.bold("---------------------------------------------------------"))
		for p in nprocs:
			p = p.strip()
			try:
				if int(p)==0:
					printer.warning("No valid proc found in" , printer.bold( str( dataset['name'] ))  + " ... skipped")
					Printer.Level = Printer.Level - 1	
					return
			except:
				printer.warning("No valid proc found in" , printer.bold( str( dataset['name'] ))  + " ... skipped")
				Printer.Level = Printer.Level - 1	
				return
				
			if dataset.keys().count('tasks_per_node')!=0 and dataset['tasks_per_node'] != None and  dataset['tasks_per_node'] != '':
				if ( int(p)%int(dataset['tasks_per_node'])) == 0 :
					n = str( int(( float(p)/float(dataset['tasks_per_node'])))  )	
				else:
					n = str( int(round(float(p)/float(dataset['tasks_per_node'])+0.5))  )			
				#run_id = dataset['name'] + "_" + p + "cpus_" + n + "nodes_"  + str(newname)					
				run_id =  p + "cpus_" + n + "nodes/"  + str(newname)					
			elif len(nnodes)==1:
				run_id =  p + "cpus_" + str(nnodes[0]) + "nodes/"  + str(newname)					
			elif len(nnodes)>1:
				run_id =  p + "cpus_" + str(nodesdict[p]) + "nodes/"  + str(newname)					
			else:	
				run_id =  p + "cpus/"  + str(newname)
			
			printer.info( "Run ID" , printer.bold( run_id) + " ... ", wait="true" ) 
#			Printer.Level = Printer.Level + 1
			waiting = True
						
			# change dir name to identify as an unique outcome	
			if os.path.isdir( run_id ):
				if waiting:
					printer.info("") # remove the wait flag
					waiting = None
				Printer.Level = Printer.Level + 1				
				printer.warning("Directory already exists" ,   printer.bold(run_id) + ". Trying to run the same dataset in less than a second.")
				printer.info("Delaying a second ...",wait="true")
				oLevel = Printer.Level
				Printer.Level = 0
				sys.stdout.flush()		 
				time.sleep( 1 )
				printer.info( "Resuming" ) 
				Printer.Level = oLevel
				now = datetime.datetime.now()
				newname = str(now.strftime("%Y-%m-%dT%Hh%Mm%Ss"))
				if dataset.keys().count('tasks_per_node')!=0 and dataset['tasks_per_node'] != None and  dataset['tasks_per_node'] != '':
					if ( int(p)%int(dataset['tasks_per_node'])) == 0 :
						n = str( int(( float(p)/float(dataset['tasks_per_node'])))  )	
					else:
						n = str( int(round(float(p)/float(dataset['tasks_per_node'])+0.5))  )								
					#run_id = dataset['name'] + "_" + p + "cpus_" + n + "nodes_"  + str(newname)					
					run_id = p + "cpus_" + n + "nodes/"  + str(newname)					
				elif len(nnodes)==1:
					run_id =  p + "cpus_" + str(nnodes[0]) + "nodes/"  + str(newname)
				elif len(nnodes)>1:
					run_id =  p + "cpus_" + str(nodesdict[p]) + "nodes/"  + str(newname)
				else:
					run_id =  p + "cpus/"  + str(newname)
				Printer.Level = Printer.Level - 1
			
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
							if waiting:
								printer.info("") # remove the wait flag
								waiting = None
							Printer.Level = Printer.Level + 1
							printer.info( "Copying dependency file" , printer.bold( str(input) )  + " into run directory")
							# input is always relative to the 'source' directory
							if not os.path.exists( os.path.dirname("./" + input )) :
								os.makedirs( os.path.dirname("./" + input ) )
							file = glob.glob(os.path.join( source + dataset['name']+ '/'  , input))
							for f in file:
								shutil.copy( f ,os.path.dirname("./" + input )  )
							Printer.Level = Printer.Level - 1
							
				if not re.match("/",exe): # Is not in full path format
					if  os.path.exists(source + dataset['name']+ '/' + exe ):
						if not os.path.exists( os.path.dirname("./" + exe)) :
							os.makedirs( os.path.dirname("./" + exe ) )
						if not os.path.isfile( "./" + exe ):	
							shutil.copy( source + dataset['name']+ '/' + exe , "./" + exe)
					else:
						if waiting:
							printer.info("") # remove the wait flag
							waiting = None
						Printer.Level = Printer.Level + 1							
						printer.warning("File not found","Can't copy exe file. Plese check the benchmark and the configuration file")
						Printer.Level = Printer.Level - 1
						sys.exit(1)
	
			failed = False			
			# submit or run job
			try: 
				o = open( "run.batch.tmp", "w" )	
				o.write(data)
			except:
				e = sys.exc_info()[0]
				printer.error("Cant create file","run.batch in "+ os.getcwd() )
				print e
				sys.exit(1)
			finally:
				o.flush()
				o.close	
	
			#
			# workaround to remove the message "text file busy"
			# when trying to execute the script 
			#	
			shutil.copyfile("run.batch.tmp","run.batch")
			os.chmod('run.batch',0755)
			os.remove("run.batch.tmp")		
			
			# get the batch system submission commands	
			mybatch = self.__getBatchSystem(dataset)
			if mybatch == None:
				if waiting:
					printer.info("") # remove the wait flag
					waiting = None
				Printer.Level = Printer.Level + 1	
				printer.error("Batch system error","Could not find any valid Batch system.")
				Printer.Level = Printer.Level - 1			
				sys.exit(1)
				
			submit_cmd = mybatch['submit']['command']
			submit_params = mybatch['submit']['parameters']	
			
			if submit_cmd == "run.batch":
				cmd = "./"+submit_cmd
			else:
				if submit_params=="<":
					cmd = "cat run.batch |  " + submit_cmd
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

				oLevel = Printer.Level
				if waiting:
						Printer.Level = 0
						printer.info("Submitted")
						Printer.Level = oLevel
				else:
					Printer.Level = Printer.Level + 1
					printer.info("Submitted")
					Printer.Level = Printer.Level - 1
			else:
				if waiting:
					printer.info("") # remove the wait flag
					waiting = None
				Printer.Level = Printer.Level + 1	
				printer.error("Warning","It seems there was a problem while submitting this job.")
				printer.warning("Please read the following error message:")
				printer.plain(err)
				Printer.Level = Printer.Level - 1
				failed = True
												
			os.chdir(t)	
			if failed:
				# mark directory as failed
				os.chdir(run_id)
				os.chdir("..")
				shutil.move( newname , "INVALID_"+newname )
				os.chdir(t)	
			
			
#####################################################################                                           
#
#	Print Config info functions (list command)
#
#####################################################################   
	def view(self, item=None, name=None ):
		""" Prints out the configuration for a given 'item' and 'name' or the global configuration
			if no item is given
		"""		
		printer.plain(printer.bold("*************************************************************"))
		printer.plain(printer.bold("***")+" Current configuration for the KAUST Benchmark Suite  "+printer.bold("***"))
		printer.plain(printer.bold("*************************************************************"))
			
		if item == None: # means show the global configuration	
	
			printer.info("KUBE Home",self.home )
			printer.info("KUBE Runs",self.runs_dir )
			printer.info("KUBE Results",self.results_dir )
			printer.info("KUBE Batch Systems:" )
						
			for nbatch in self.batchs:
				Printer.Level = Printer.Level + 1
				printer.info(nbatch['name'] +":") 
				Printer.Level = Printer.Level + 1
				printer.info("Submission command",nbatch['submit']['command'] + ' '+ nbatch['submit']['parameters'])			
				Printer.Level = Printer.Level - 2 
				
			printer.info("Items to Benchmark")			
			self.__viewApp()	
			self.__viewFS()
			self.__viewNet()
			self.__viewSynths()

		elif item == 'apps':
			printer.plain(printer.bold("***")+"  Showing configuration for selected App  "+printer.bold("***"))
			self.__viewApp(name)	
		
		elif item == 'filesys':
			printer.plain(printer.bold("***")+"  Showing configuration for Filesystems  "+printer.bold("***"))	
			self.__viewFS(name)
		elif item == 'nets':
			printer.plain(printer.bold("***")+"  Showing configuration for Networks  "+printer.bold("***"))
			self.__viewNet(name)
		elif item == 'synths':
			printer.plain(printer.bold("***")+"  Showing configuration for Synthetics benchmarks "+printer.bold("***"))	
			self.__viewSynths(name)
		else:
			print "Unknown item: '" + str(item) + "'"
		
	def __viewApp(self,which=None):
		""" Prints out configuration information for a specific app or for All apps
		"""
		if which==None: # means ALL
			printer.info("Apps"," " )
			#Printer.Level = Printer.Level + 1
			#printer.info("Active Apps"," " )			
			for k in self.a_apps.keys():
				Printer.Level = Printer.Level + 1
				printer.info(k," " )
				for l in range(len(self.a_apps[k])):
					Printer.Level = Printer.Level + 1
					printer.info("dataset",str( self.a_apps[k][l]['name']))
					for litem in  self.a_apps[k][l]:
						if litem != 'name' and litem != 'outputs' and litem != 'metrics' and litem != 'datasets' and litem != 'active' and not re.match("launcher",litem) and  not re.match("#\d+#",litem):
							if str(self.a_apps[k][l][litem]).strip() != None or str(self.a_apps[k][l][litem]).strip() != '' :
								Printer.Level = Printer.Level + 1
								printer.info(litem ,str( self.a_apps[k][l][litem])  )
								Printer.Level = Printer.Level - 1
					Printer.Level = Printer.Level - 1			
				Printer.Level = Printer.Level - 1	
			#Printer.Level = Printer.Level - 1	
		else:	
			if which.lower() != "all" and  self.a_apps.keys().count(which) == 0:
				printer.warning("Warning","Application " + printer.bold(which)  + " not found or not active")
			else:	
				if which.lower() != "all" :
					for k in self.a_apps.keys():
						if which==k:
							mybatch=[]
							for tapp in self.apps:
							 if tapp['name'] == which :
								mybatch = self.__getBatchSystem(tapp)
							 	self.__printBatchSystemInfo(mybatch)
								self.__printDatasetInfo(self.a_apps[which])
							break;	
				else:
					for k in self.a_apps.keys():
						mybatch=[]
						for tapp in self.apps:
							if tapp['name'] == k:
								mybatch = self.__getBatchSystem(tapp)
					 			self.__printBatchSystemInfo(mybatch)
								self.__printDatasetInfo(self.a_apps[k])


	def __viewFS(self, which=None):
		""" Prints out configuration information for a specific Filesystem benchmarks or for all filesystem benchmarks
		"""
		self.__printBaseInfo( self.a_filesys, self.filesys, which, "Filesystems")
		
	def __viewSynths(self,which=None):
		""" Prints out configuration information for a specific Synthetic benchmarks or for all synthetic benchmarks
		"""
		self.__printBaseInfo( self.a_synths, self.synths, which,"Synthetics")

	def __viewNet(self,which=None):
		""" Prints out configuration information for a specific app or for All apps
		"""
		self.__printBaseInfo( self.a_nets, self.nets, which,"Networks")		
		
	def __printBatchSystemInfo(self,mybatch):
		if 	 mybatch == None:
			printer.info("Using command line execution\n")
			return 
						
		submit_script = mybatch['script']
		printer.plain("Using " + printer.bold(str(mybatch['name']))+ " batch system" )
		if  mybatch['name'] != "None":
			submit_cmd = mybatch['submit']['command']
			submit_params = mybatch['submit']['parameters']
			printer.info("Submission command",submit_cmd +" " + submit_params)
		printer.plain(printer.bold("-------------------------------------------------"))

	def __printDatasetInfo(self,which):	
		for   dataset in which:
			nprocs = str(dataset['numprocs']).split(',')
			if len(nprocs) == 0:
				printer.warning("No procs found in" + printer.bold(str( dataset['name'] ))  +" ... skipped")
				continue
			for p in nprocs:
				printer.plain("dataset: " + printer.bold(str( dataset['name'] )) + " with " +  printer.bold(p)  + " procs")
				printer.info("Submission script:")
				data = self.__getBatchScript(dataset,p.strip())
				print data
				printer.plain(printer.bold("-------------------------------------------------"))			

	def __printBaseInfo(self, who, all ,which,section):
		""" Prints out configuration common information for Networks, Filesystems and Synthetics benchmarks
		"""
		if which==None: # means ALL		
			printer.info(str(section)," " )		
			for k in who.keys():
				Printer.Level = Printer.Level + 1
				printer.info(k," " )
				for l in range(len(who[k])):
					Printer.Level = Printer.Level + 1
					printer.info("dataset",str( who[k][l]['name']))
					for litem in  who[k][l]:
						if litem == 'numprocs' or litem == 'nodes' or litem == 'tasks_per_node' or litem == 'exe' or litem == 'args' or litem == 'batch' and  not re.match("#\d+#",litem):
							Printer.Level = Printer.Level + 1
							printer.info(litem ,str( who[k][l][litem])  )
							Printer.Level = Printer.Level - 1
					Printer.Level = Printer.Level - 1
				Printer.Level = Printer.Level - 1			
		else:
			if which.lower() != "all" and  who.keys().count(which) == 0:
				printer.warning("Warning","Element " + printer.bold(which)  + " not found or not active")
			else:
				if which.lower() != "all":
					printer.info(str(which)+"\n","" )
					for k in who.keys():
						if which==k:
							mybatch=[]
							for elem in all:
							 if elem['name'] == which:
								mybatch = self.__getBatchSystem(elem)					
								self.__printBatchSystemInfo(mybatch)
								self.__printDatasetInfo(who[which])							
							break;
				else:	
					for k in who.keys():
						mybatch=[]
						printer.info(str(k)+"\n","" )
						for tapp in all:
							if tapp['name'] == k:
								mybatch = self.__getBatchSystem(tapp)
					 			self.__printBatchSystemInfo(mybatch)
								self.__printDatasetInfo(who[k])


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
		self.apps = yaml_conf['KUBE']['BENCH']['APPS'] # Array of dictionaries with apps info: active, exe, name, etc...		
		# sanity check
		repeat=True
		while repeat:
			repeat = False				
			for app in self.apps:
				if  app.keys().count('name')==0 or \
					app.keys().count('active')==0:
					printer.error("Config file error","'active' and 'name' are mandatory fields within an APP ... Skipping this entry")
					self.apps.remove(app)
					repeat = True
				else:
					if app['active'] and ( app.keys().count('datasets')==0 or app.keys().count('batch')==0 or app.keys().count('exe')==0  ):
						printer.error("Config file Error"," 'datasets', 'exe' and 'batch' fields are required for any active APP: " + printer.bold(app['name']) + " ... Skipping this entry")
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
							printer.error("Config file error","'name' and 'active' fields are required for any dataset in app: " + printer.bold(napp) + " ... Skipping this dataset")
							self.a_apps[napp].remove(dataset)
							repeat = True
						elif dataset['active'] != True:
							self.a_apps[napp].remove(dataset)
							repeat = True
						else:
							dataset['bench'] = "apps"
							dataset['parent'] = napp
													
				if len( self.a_apps[napp] ) == 0:
					del(self.a_apps[napp])
					repeatf = True
	
		# populate self.apps with the batch parameters if they are not already set in the app:
		for appname in self.a_apps.keys():	
			for a in self.apps:	
				if a['name'] == appname:	 			
					for gk in yaml_conf['KUBE'].keys():
						if not gk in ["BATCH","BENCH"]  :
							a[str(gk).lower()] =  yaml_conf['KUBE'][gk]['path']
					for batch in self.batchs: 
						if batch['name'] == a['batch']:
							for key in batch.keys():
								if key!="name" and key!="script" and key!="monitor" and key!="submit"   and a.keys().count(key)==0 :
									a[key] = copy.deepcopy( batch[key] )	 			
							break # step out the batch loop
					break # step out self.apps loop
													
		# populate self.a_apps -> datasets with the app parameters if they are not already set in the dataset:			
		for appname in self.a_apps.keys():	
			for dataset in self.a_apps[appname]:
				for a in self.apps:	
					if a['name'] == appname:
						notToReplace=['name','datasets','active']	
						for sk in a.keys():
							if sk=="batch": # Force the dataset to use always the batch system defined  for the app
									# the 'batch' parameter is global to the app, not dataset specific 
								dataset[sk] = a[sk] # no deepcopy needed as we want a reference to the batch system
							elif sk=="tools": # Force the dataset to use always the globally defined  value, no redefinition allowed
								dataset['common'] = str(a[sk]) + "/common/"
								dataset[sk] = str(a[sk]) + "/" + str(dataset['bench'])  + "/" + str(dataset['parent']) + '/' # no deepcopy needed as we want a reference 
							elif  dataset.keys().count(sk)==0 and not sk in notToReplace :
								if a[sk] != None:
									dataset[sk] = copy.deepcopy(a[sk])
								else:
									dataset[sk] = "" 		
						if dataset.keys().count('numprocs')==0 :
							# if there is no numprocs, at least tasks_per_node and nodes are needed
							if dataset.keys().count('tasks_per_node')==0 and  dataset.keys().count('nodes')==0:
								printer.error("Config file error"," Cannot figure out the number of tasks to run for " + printer.bold(appname) + " use either 'numprocs' or a combination of 'nodes' and 'tasks_per_run'!!!") 
								printer.error("Please revise your configuration file !!!")
								sys.exit(1)
							elif dataset.keys().count('tasks_per_node')!=0 and  dataset.keys().count('nodes')!=0:	
								numprocs_str=''
								for n in   ("".join(dataset['nodes'].split())).split(','): 
									numprocs_str = numprocs_str + ',' +  str( int(dataset['tasks_per_node'])*int(n) )	
								dataset['numprocs'] = numprocs_str[1:]	
							else:
								printer.error("Config file error"," Cannot figure out the number of tasks to run for " + printer.bold(appname) +" !!!") 
								printer.error("Please revise your configuration file !!!")
								sys.exit(1)
						else:
							nprocs = str(dataset['numprocs']).split(',')
							if len(nprocs) == 0:
								printer.error("No procs found in", printer.bold( str( dataset['name'] )) )
								printer.error("Please revise your configuration file !!!")
								sys.exit(1)

							nnodes=[]
							if dataset.keys().count('nodes')!=0 and dataset['nodes'] != None and  dataset['nodes'] != '':
								nnodes = str(dataset['nodes']).split(',')
								if len(nnodes)>1 and len(nnodes)!=len(nprocs):
									printer.error("Misleading procs/nodes configuration found in", printer.bold( str( dataset['name'] )) )
									printer.error("Please revise your configuration file !!!")
									sys.exit(1)
								
						if dataset.keys().count('outputs')==0 :
							printer.error("Config file error"," Dataset of " + printer.bold(appname) + " found without 'outputs'. This tag is mandatory!!!") 
							printer.error("Please revise your configuration file !!!")
							sys.exit(1)	

						if dataset.keys().count('hostsfile')!=0 and re.match("[^/]",dataset['hostsfile']) :
                       					dataset['hostsfile']= self.home + "/etc/" + dataset['hostsfile']					
							
						break # step out apps loop

		self.__substituteVarsForAnalysis(self.a_apps)
	
	def __readSynthetics(self,yaml_conf):
		""" Reads Synthetic section and do some error check """
		# set self.synths
		self.synths = yaml_conf['KUBE']['BENCH']['SYNTHETICS'] # Array of dictionaries with synthetic bench info: active, exe, name, etc...
		self.__sanityBasic(self.synths,"Synthetics")
		#set active Synthetics:
		self.a_synths = dict( [ (synth['name'],synth['datasets']) for synth in self.synths if synth['active'] ]) # Dictionary Name->Array of datasets  of active networks
		# update self.a_synths and remove inactive datasets ... also if there is no active dataset remove synthetic from the list of active items
		self.__updateActiveElements(self.a_synths,"Synthetics")
		self.__populateElements(self.a_synths, self.synths,yaml_conf)
		self.__substituteVarsForAnalysis(self.a_synths)
	
	def __readNets(self,yaml_conf):
		""" Reads Networks section and do some error check """
		# set self.nets
		self.nets = yaml_conf['KUBE']['BENCH']['NETWORKS'] # Array of dictionaries with nets info: active, exe, name, etc...
		self.__sanityBasic(self.nets,"Networks")
		#set active networks:
		self.a_nets = dict( [ (net['name'],net['datasets']) for net in self.nets if net['active'] ]) # Dictionary Name->Array of datasets  of active networks
		# update self.a_nets and remove inactive datasets ... also if there is no active dataset remove network from the list of active networks
		self.__updateActiveElements( self.a_nets ,"Networks")
		self.__populateElements(self.a_nets ,self.nets,yaml_conf)
		self.__substituteVarsForAnalysis(self.a_nets)

	def __readFilesystems(self,yaml_conf):
		""" Reads Filesystems section and do some error check """
		# set self.filesys
		self.filesys = yaml_conf['KUBE']['BENCH']['FILESYSTEMS'] # Array of dictionaries with filesystems info: active, exe, name, etc...
		self.__sanityBasic(self.filesys,"Filesystems")
		#set active filesystems:
		self.a_filesys = dict( [ (fs['name'],fs['datasets']) for fs in self.filesys if fs['active'] ]) # Dictionary Name->Array of datasets  of active filesystems
		# update self.a_filesys and remove inactive datasets ... also if there is no active dataset remove filesystem from the list of active filesystems
		self.__updateActiveElements( self.a_filesys ,"Filesystems")
		self.__populateElements(self.a_filesys ,self.filesys,yaml_conf)
		self.__substituteVarsForAnalysis(self.a_filesys)


	# Substitute in the target string, all the matches contained in keysDict with the values in dataset[ ... ] 
	def __substitute( self, strTarget , keysDict, dataset  ):
		outputDict={}
		strTarget = str(strTarget) # be sure strTarget is str :) 	
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
		#itemsToReplace=['outputs','dependencies','args','exe']
		itemsNotToReplace=['metrics','name','active','batch']
		# name => bench name
		for name in item.keys():	
			for dataset in item[name]:
				str2find = {}
				# added
				# all variables are susceptible to be replaced but the ones in itemsNotToReplace	
				for nkey in dataset.keys():
					str2find[nkey] = "%"+ nkey.upper() +"%"		
				for nkey in dataset.keys():
					if dataset.keys().count(nkey) != 0 and not nkey in itemsNotToReplace:
						if nkey =='outputs':
							# iterate over every output	
							for outpkey in dataset[nkey].keys():
								if dataset[nkey][outpkey] != None: 
									 retValue = self.__substitute( dataset[nkey][outpkey] , str2find, dataset )	
									 if isinstance(retValue,dict):
										for retKey in retValue.keys():
											dataset[nkey]["#" + retKey + "#" + outpkey] = retValue[retKey]
										# and delete previous entry .. NOOOOOOOO dont delete cuz it will be used later on ... ie: metrics are not translated into a specific proc number until the end
										#del dataset[nkey][outpkey]
									 else:
										 dataset[nkey][outpkey] = retValue 
						else:
							if dataset[nkey] != None:
								retValue = self.__substitute( dataset[nkey] , str2find, dataset )	
								if isinstance(retValue,dict):
									for retKey in retValue.keys():
										dataset["#" + retKey + "#" + nkey] = retValue[retKey]
									# and delete previous entry .. NOOOOOOOO dont delete cuz it will be used later on ... ie: metrics are not translated into a specific proc number until the end
									#del dataset[nkey]
								else:
									dataset[nkey]= retValue 							
								
		# Replace inline variables in the ['metrics'] section inside each dataset ...
		for name in item.keys():	
			for dataset in item[name]:
				str2find = {}
				# replace metrics elements referred to the outputs ...
				for nkey in dataset['outputs'].keys():
					str2find[nkey]= "%"+ nkey.upper() +"%"
				for sstr in str2find.keys():
					reple = re.compile( str2find[sstr] );
					if ( dataset.keys().count('metrics') != 0 ):
						for metric in dataset['metrics']:
							for elem in metric:
								if elem != 'reference':
									metric[elem] = reple.sub(dataset['outputs'][sstr],metric[elem])		
								else:
									for t in metric[elem]:
										metric[elem][t] = reple.sub(dataset['outputs'][sstr], str(metric[elem][t]) ) 	
				str2find = {}
				str2find['tools'] = "%TOOLS%"
				str2find['common'] = "%COMMON%"
				for sstr in str2find.keys():
					reple = re.compile( str2find[sstr] );
					if ( dataset.keys().count('metrics') != 0 ):
						for metric in dataset['metrics']:
							for elem in metric:
								if elem != 'reference':
									metric[elem] = reple.sub(dataset[sstr],metric[elem])		
								else:
									for t in metric[elem]:
										metric[elem][t] = reple.sub(dataset[sstr], str(metric[elem][t]) ) 	
							
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
							printer.error("Config file error","'name' and 'active' fields are required for any dataset in "+ mstr +": " + printer.bold(elem) + " ... Skipping this dataset")
							a_elems[elem].remove(dataset)
							repeat = True
						elif dataset['active'] != True:
							a_elems[elem].remove(dataset)
							repeat = True
						else:
							dataset['bench'] = mstr.lower()
							dataset['parent'] = elem						
								
				if len( a_elems[elem] ) == 0:
					del(a_elems[elem])
					repeatf = True

	def	__populateElements(self,a_elems,elems,yaml_conf):
		# populate self.XXX with the batch parameters if they are not already set in the XXX entry:
		# populate also de global tags values: HOME, RUNS, RESULTS, TOOLS ... 
		for aname in a_elems.keys():	
			for a in elems:	
				if a['name'] == aname:	 			
					for gk in yaml_conf['KUBE'].keys():
						if not gk in ["BATCH","BENCH"]  :
							a[str(gk).lower()] =  yaml_conf['KUBE'][gk]['path']
					for batch in self.batchs: 
						if batch['name'] == a['batch']:
							for key in batch.keys():
								if not key in ["name","script","monitor","submit"] and a.keys().count(key)==0 :
									a[key] = copy.deepcopy( batch[key] )	 			
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
								dataset[sk] = a[sk] # no deepcopy needed as we want a reference to the batch system
							elif sk=="tools": # Force the dataset to use always the globally defined  value, no redefinition allowed
								dataset['common'] = str(a[sk]) + "/common/"
								dataset[sk] = str(a[sk]) + "/" + str(dataset['bench'])  + "/" + str(dataset['parent']) + '/' # no deepcopy needed as we want a reference 
							elif  dataset.keys().count(sk)==0 and not sk in ["name","datasets","active"] :
								if a[sk] != None:
									dataset[sk] = copy.deepcopy(a[sk])
								else:
									dataset[sk] = "" 		
						if dataset.keys().count('numprocs')==0 :
                                                        # if there is no numprocs, at least tasks_per_node and nodes are needed
                                                        if dataset.keys().count('tasks_per_node')==0 and  dataset.keys().count('nodes')==0:
                                                                printer.error("Config file error"," Cannot figure out the number of tasks to run for " + printer.bold(aname) + " use either 'numprocs' or a  combination of 'nodes' and 'tasks_per_run'!!!") 
                                                                printer.error("Please revise your configuration file !!!")
                                                                sys.exit(1)
                                                        elif dataset.keys().count('tasks_per_node')!=0 and  dataset.keys().count('nodes')!=0:
                                                                numprocs_str=''
                                                                for n in   ("".join(dataset['nodes'].split())).split(','):
                                                                        numprocs_str = numprocs_str +',' +  str( int(dataset['tasks_per_node'])*int(n) )
                                                                dataset['numprocs'] = numprocs_str[1:]
                                                        else:
                                                                printer.error("Config file error"," Cannot figure out the number of tasks to run for " + printer.bold(aname) +" !!!")
                                                                printer.error("Please revise your configuration file !!!")
                                                                sys.exit(1)
						else:
							nprocs = str(dataset['numprocs']).split(',')
							if len(nprocs) == 0:
								printer.error("No procs found in", printer.bold( str( dataset['name'] )) )
								printer.error("Please revise your configuration file !!!")
								sys.exit(1)

							nnodes=[]
							if dataset.keys().count('nodes')!=0 and dataset['nodes'] != None and  dataset['nodes'] != '':
								nnodes = str(dataset['nodes']).split(',')
								if len(nnodes)>1 and len(nnodes)!=len(nprocs):
									printer.error("Misleading procs/nodes configuration found in", printer.bold( str( dataset['name'] )) )
									printer.error("Please revise your configuration file !!!")
									sys.exit(1)

						if dataset.keys().count('outputs')==0 :
							printer.error("Config file error"," Dataset of " + printer.bold(aname) + " found without 'outputs'. This tag is mandatory!!!") 
							printer.error("Please revise your configuration file !!!")
							sys.exit(1)	
						
						if dataset.keys().count('hostsfile')!=0 and re.match("[^/]",dataset['hostsfile']) :
                       					dataset['hostsfile']= self.home + "/etc/" + dataset['hostsfile']					
								
						break # step out 'a' loop		

		
	def __sanityBasic(self,elems,mstr):
		# sanity check 
		repeat=True
		while repeat:
			repeat = False				
			for elem in elems:
				if  elem.keys().count('name')==0 or \
					elem.keys().count('active')==0:
					printer.error("Config file error","'active' and 'name' are mandatory fields within item: " + mstr +" ... Skipping this entry")
					self.elems.remove(elem)
					repeat = True
				else:
					if elem['active'] and ( elem.keys().count('datasets')==0 or elem.keys().count('batch')==0  ):
						printer.error("Config file Error"," 'datasets', and 'batch' fields are required for any active "+mstr+": " + printer.bold(elem['name']) + " ... Skipping this entry")
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
		if yaml_conf.keys().count('KUBE') ==0:
			printer.error("Config file error", "KUBE head tag is not defined") 
			sys.exit(1)	
		if yaml_conf['KUBE'].keys().count("HOME") == 0 or \
		   yaml_conf['KUBE'].keys().count("RUNS") == 0 or \
		   yaml_conf['KUBE'].keys().count("RESULTS") == 0 or \
		   yaml_conf['KUBE'].keys().count("TOOLS") == 0 or \
		   yaml_conf['KUBE'].keys().count("BATCH") == 0 or \
		   yaml_conf['KUBE'].keys().count("BENCH") == 0:
			printer.error("Config file error","HOME, RUNS, RESULTS, TOOLS, BATCH and BENCH must be defined")
			sys.exit(1)			

		#######################################################################################
		# Set important variables
		
		# set home
		self.home = yaml_conf['KUBE']['HOME']['path']
		if self.home == None: 
			printer.error("Config file error","HOME must be defined")
			sys.exit(1) 

		#set results
		self.results_dir = yaml_conf['KUBE']['RESULTS']['path']
		if re.match("[^/]",self.results_dir):
			self.results_dir = self.home + "/" + self.results_dir
			yaml_conf['KUBE']['RESULTS']['path'] = self.results_dir
		
		#set runs
		self.runs_dir = yaml_conf['KUBE']['RUNS']['path']
		self.runs_lifespan = int(yaml_conf['KUBE']['RUNS']['lifespan'])
		if re.match("[^/]",self.runs_dir):
			self.runs_dir = self.home + "/" + self.runs_dir
			yaml_conf['KUBE']['RUNS']['path'] = self.runs_dir
		
		#set tools
		self.tools_dir = yaml_conf['KUBE']['TOOLS']['path']
		if re.match("[^/]",self.tools_dir):
			self.tools_dir = self.home + "/" + self.tools_dir
			yaml_conf['KUBE']['TOOLS']['path']= self.tools_dir

		#set RRDTOOL
		self.rrdtool_path = yaml_conf['KUBE']['RRDTOOL']['path']
		if re.match("[^/]",self.rrdtool_path):
			self.rrdtool_path = self.home + "/" + self.rrdtool_path
			yaml_conf['KUBE']['RRDTOOL']['path']= self.rrdtool_path
		self.rrdtool_root = yaml_conf['KUBE']['RRDTOOL']['root']
		if re.match("[^/]",self.rrdtool_root):
			self.rrdtool_root = self.home + "/" + self.rrdtool_root
			yaml_conf['KUBE']['RRDTOOL']['root']= self.rrdtool_root

			
		# set batchs
		self.batchs = yaml_conf['KUBE']['BATCH']
		if self.batchs==None:
			printer.error("Config file error","at least one BATCH must be defined")
			sys.exit(1)	
		# set absolute path to the scripts and do some error check
		for nbatch in self.batchs:
			if nbatch['name']==None or nbatch['name']=='':
				printer.error("Config file error","Missing 'name' in one of your BATCHs")
				sys.exit(1)	
		
			if nbatch['name']!="None" and nbatch['name']!=None:
				if ( nbatch.keys().count('name')==0 or nbatch.keys().count('submit')==0):
					printer.error("Config file error"," 'name' and 'submit' tags are mandatory in the BATCH" )
					sys.exit(1)
				if nbatch['submit'] == None : 
					printer.error("Config file error","'submit' tag in one of your BATCHs is empty")
					sys.exit(1)
				else:
					if nbatch['submit'].keys().count('parameters')==0:
						 nbatch['submit']['parameters'] = ' '
					if nbatch['submit'].keys().count('submittedmsg')==0:
						printer.error("Config file error","'submit' tag in one of your BATCHs is missing the field 'submittedmsg'")
						sys.exit(1)
			
				if  nbatch.keys().count('script')==0 or  nbatch['script']==None:
					print nbatch['name']	
					print nbatch.keys().count('script')	
					printer.error("Config file error"," 'script' tag is mandatory in an a BATCH")
					sys.exit(1)
				else:
					if re.match("[^/]",nbatch['script']):
						nbatch['script'] = self.home + "/etc/" + nbatch['script']

		
		# Verify that the main tags ni BENCH section exist
		if (yaml_conf['KUBE']['BENCH'].keys().count('APPS') == 0) or \
			(yaml_conf['KUBE']['BENCH'].keys().count('FILESYSTEMS') == 0) or \
			(yaml_conf['KUBE']['BENCH'].keys().count('NETWORKS') == 0) or \
			(yaml_conf['KUBE']['BENCH'].keys().count('SYNTHETICS') == 0) :		
			printer.error("Config file error","'APPS','FILESYSTEMS','NETWORKS','SYNTHETICS' tags are mandatory inside BENCH")
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
				cfname = KUBE.CONF_FILE_PATH+KUBE.CONF_FILE_NAME
			else:
				cfname = configfile
				
			stream = file(cfname, 'r')
		except IOError as e:
			print "I/O error({0}): {1}".format(e.errno, e.strerror)
			sys.exit(e.errno)

		printer.info("Using configuration file",  printer.bold(cfname) )
		
		# global variable holding the configuration 
		yaml_conf = yaml.load( stream )		
		self.__readYaml(yaml_conf)
	
	def __init__(self,configfile=None):
		# include KUBE.LIB_DIR in the module search path 
		if KUBE.LIB_DIR not in sys.path:
			sys.path.insert(0, KUBE.LIB_DIR)		
		self.__loadYaml(configfile)

	def __cleanOldRuns(self):
		"""Function that removes old runs according to the 'lifespan' param"""

		if self.runs_lifespan == 0:
			return	

		# remove hidden files and dirs from the list
		bench   = [ d for d in os.listdir(self.runs_dir)  if not re.match('\\.',d) and os.path.isdir(self.runs_dir + "/" +d) ]	
		what    = [ b+'/'+l for b in bench for l in os.listdir(self.runs_dir+'/'+b)  if not re.match('\\.',l) and os.path.isdir(self.runs_dir + "/" +b+"/"+l) ]
		dataset = [ w+'/'+d for w in what for d in  os.listdir(self.runs_dir+'/' + w) if not re.match('\\.',d) and os.path.isdir(self.runs_dir + "/" +w+"/"+d)  ]
	
		dateexp = re.compile("\d\d\d\d-\d\d-\d\dT\d\dh\d\dm\d\ds")		
		
		printer.plain(printer.bold("**************************************************"))	
		printer.plain( "Removing old runs according to current policy of:\n" + printer.bold(str(self.runs_lifespan)) + " days"  )
		toRemove=[]
		for d in dataset:
			current = self.runs_dir + "/" + d
			if os.path.isdir(current):
				for ud in os.listdir(current):
					if os.path.isdir(current +'/' + ud):
						for e in os.listdir(current +'/' + ud): 
							mobj = dateexp.search(e)
							if mobj:
								fecha = datetime.datetime.strptime( mobj.group(0) , '%Y-%m-%dT%Hh%Mm%Ss')		
								now = datetime.datetime.now()
								if  (now - fecha) > datetime.timedelta (days = self.runs_lifespan ):
									toRemove.append( current + '/' + ud + '/' + e )
						if len(os.listdir(current +'/' + ud))==0:
							toRemove.append( current + '/' + ud) 
		elemsremoved = 0
		for e in toRemove:
			if os.path.isdir(e):	
				clean(e,True)
				#printer.warning( e)
				elemsremoved=elemsremoved+1	
				
		#printer.plain( printer.bold(str(elemsremoved)) + " elements removed")
		printer.plain(printer.bold("**************************************************"))	
								
