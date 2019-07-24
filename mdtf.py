# ======================================================================
# NOAA Model Diagnotics Task Force (MDTF) Diagnostic Driver
#
# March 2019
# Dani Coleman, NCAR
# Chih-Chieh (Jack) Chen, NCAR, 
# Yi-Hung Kuo, UCLA
#
# ======================================================================
# Usage
#
# USAGE: python mdtf.py input_file (default=namelist)
# The input file sets all model case/dates and which modules to run
# This file (mdtf.py) should NOT be modified
#
# Please see Getting Started [link] and Developer's Walk-Through
# for full description of how to run
# ======================================================================
# What's Included
#
# The input file (namelist) provided in the distribution will run
# the following diagnostic modules (PODs) by default:
#    Convective Transition Diagnostics   from J. David Neelin (UCLA)
#    MJO Teleconnections                 from Eric Maloney (CSU)
#    Extratropical Variance (EOF 500hPa) from CESM/AMWG (NCAR)
#    Wavenumber-Frequency Spectra        from CESM/AMWG (NCAR)
#    MJO Spectra and Phasing             from CESM/AMWG (NCAR)
#
# In addition, the following package is provided in full but does not run
# by default because of higher memory requirements
#    Diurnal Cycle of Precipitation      from Rich Neale (NCAR)
#
# The following modules are under development. Future releases will be
# available on the  MDTF main page
# http://www.cesm.ucar.edu/working_groups/Atmosphere/mdtf-diagnostics-package/index.html
#    MJO Propagation and Amplitude        from Xianan Jiang, UCLA
#    ENSO Moist Static Energy budget      from Hariharasubramanian Annamalai, U. Hawaii
#    Warm Rain Microphysics               from Kentaroh Suzuki (AORI, U. Tokyo
#    AMOC 3D structure                    from Xiaobiao Xu (FSU/COAPS)
#
# The MDTF code package and the participating PODs are distributed under
# the LGPLv3 license (see LICENSE.txt).
# ======================================================================
# Requirements
#
# As well as Ncar Command Language (NCL),
# this release uses the following Python modules: 
#     os, glob, json, dataset, numpy, scipy, matplotlib, 
#     networkx, warnings, numba, netcdf4
# ======================================================================
#

print "==== Starting "+__file__

import os
import sys
import argparse
import glob
import shutil
import timeit
if os.name == 'posix' and sys.version_info[0] < 3:
  try:
    import subprocess32 as subprocess
  except (ImportError, ModuleNotFoundError):
    import subprocess
else:
    import subprocess
import yaml
sys.path.insert(0,'var_code')
import util
from util import setenv

cwd = os.path.dirname(os.path.realpath(__file__)) # gets dir of currently executing script
parser = argparse.ArgumentParser()
parser.add_argument("-v", "--verbosity", action="count",
                    help="Increase output verbosity")
parser.add_argument("--test_mode", action="store_true",
                    help="Set flag to not call PODs, just say what would be called")
parser.add_argument('--DIAG_HOME', type=str, 
                    default=cwd,
                    help="Code installation directory")
parser.add_argument('--MODEL_ROOT_DIR', type=str, 
                    default=os.path.join(os.path.dirname(cwd), 'inputdata', 'model'),
                    help="Parent directory containing results from different models.")
parser.add_argument('--OBS_ROOT_DIR', type=str, 
                    default=os.path.join(os.path.dirname(cwd), 'inputdata', 'obs_data'),
                    help="Parent directory containing observational data used by individual PODs.")
parser.add_argument('--WORKING_DIR', type=str, 
                    default=os.path.join(cwd, 'wkdir'),
                    help="Working directory.")
parser.add_argument('--OUTPUT_DIR', type=str, 
                    default=os.path.join(cwd, 'wkdir'),
                    help="Directory to write output files. Defaults to working directory.")
args = parser.parse_args()
if args.verbosity == None:
   verbose = 1
else:
   verbose = args.verbosity + 1 # fix for case  verb = 0
test_mode = args.test_mode

os.system("date")

errstr = "ERROR "+__file__+" : "

# ======================================================================
# Default script settings over-ridden by namelist: VAR var-name varvalue
# It is recommended to make all changes in the namelist
#

envvars = {}
# ======================================================================
# DIRECTORIES: set up locations
# ======================================================================

#  Home directory for diagnostic code (needs to have 'var_code',  sub-directories)
setenv("DIAG_HOME",args.DIAG_HOME,envvars,verbose=verbose)   # eg. mdtf/MDTF_2.0
setenv("DIAG_ROOT",os.path.dirname(os.environ["DIAG_HOME"]),envvars,verbose=verbose) # dir above DIAG_HOME

path_var_code_absolute = os.environ["DIAG_HOME"]+'/var_code/util/'
if ( verbose > 1): print "Adding absolute path to modules in "+path_var_code_absolute
sys.path.insert(0,path_var_code_absolute)

# inputdata contains model/$casename, obs_data/$package/*  #drb change?
setenv("VARCODE",os.environ["DIAG_HOME"]+"/var_code",envvars,overwrite=False,verbose=verbose)
setenv("VARDATA",args.OBS_ROOT_DIR,envvars,overwrite=False,verbose=verbose)
setenv("RGB",os.environ["VARCODE"]+"/util/rgb",envvars,overwrite=False,verbose=verbose)



# ======================================================================
# Input settings from namelist file (name = argument to this script, default DIAG_HOME/namelist)
# to set CASENAME,model,FIRSTYR,LASTYR, POD list and environment variables 

try:
   config = util.read_mdtf_config_file(sys.argv,verbose=verbose)
except Exception as error:
   print error
   exit()
config['envvars'].update(envvars)


# output goes into wkdir & variab_dir (diagnostics should generate .nc files & .ps files in subdirectories herein)

setenv("DATADIR",os.path.join(args.MODEL_ROOT_DIR, os.environ["CASENAME"]),envvars,overwrite=False,verbose=verbose)

setenv("WKDIR",args.WORKING_DIR,envvars,verbose=verbose)
variab_dir = "MDTF_"+os.environ["CASENAME"]+"_"+os.environ["FIRSTYR"]+"_"+os.environ["LASTYR"]
setenv("variab_dir",os.path.join(args.WORKING_DIR, variab_dir),envvars,overwrite=False,verbose=verbose)
util.check_required_dirs( already_exist =["DIAG_HOME","VARCODE","VARDATA"], create_if_nec = ["WKDIR","variab_dir"],verbose=verbose)



pod_configs = []
for pod in config['pod_list']: # list of pod names to do here
   try:
      pod_cfg = util.read_pod_settings_file(pod, verbose)
      util.check_pod_driver(pod_cfg['settings'], verbose)
      var_files = util.check_for_varlist_files(pod_cfg['varlist'], verbose)
      pod_cfg.update(var_files)
   except AssertionError as error:  
      print str(error)
   if ('long_name' in pod_cfg['settings']) and verbose > 0: 
      print "POD long name: ", pod_cfg['settings']['long_name']

   if len(pod_cfg['missing_files']) > 0:
      print "WARNING: POD ",pod," Not executed because missing required input files:"
      print yaml.dump(pod_cfg['missing_files'])
      continue
   else:
      if (verbose > 0): print "No known missing required input files"

   pod_configs.append(pod_cfg)

# ======================================================================
# Check for programs that must exist (eg ncl)
# To Do: make a dictionary 'program name':'ENV VARNAME' and loop like dir_list below
# ======================================================================

ncl_err = os.system("which ncl")
if ncl_err == 0:
   setenv("NCL",subprocess.check_output("which ncl", shell=True),config['envvars'],overwrite=False,verbose=verbose)
   print("using ncl "+os.environ["NCL"])
else:
   print(errstr+ ": ncl not found")
# workaround for conda-installed ncl on csh: ncl activation script doesn't set environment variables properly
if not ("NCARG_ROOT" in os.environ) and ("CONDA_PREFIX" in os.environ):
   setenv("NCARG_ROOT",os.environ['CONDA_PREFIX'],config['envvars'],verbose=verbose)

# Check if any required namelist/envvars are missing  
util.check_required_envvar(verbose,["CASENAME","model","FIRSTYR","LASTYR","NCARG_ROOT"])
util.check_required_dirs( already_exist =["NCARG_ROOT"], verbose=verbose)


# update local variables used in this script with env var changes from reading namelist
# variables that are used through os.environ don't need to be assigned here (eg. NCARG_ROOT)
test_mode = config['envvars']['test_mode']
verbose   = config['envvars']['verbose']



# ======================================================================
# set variable names based on model
# ======================================================================
found_model = False
if os.environ["model"] == "CESM":
   import set_variables_CESM        #in var_code/util
   found_model = True
if os.environ["model"] == "CMIP":
   import set_variables_CMIP
   found_model = True
if os.environ["model"] == "AM4":
   import set_variables_AM4
   found_model = True
if found_model == False:
   print "ERROR: model ", os.environ["model"]," Not Found"
   print "      This is set in namelist "
   print "      CASE case-name *model* start-year end-year"
   quit()


# ======================================================================
# Check directories that must already exist
# ======================================================================

os.chdir(os.environ["WKDIR"])

# ======================================================================
# set up html file
# ======================================================================
if os.path.isfile(os.environ["variab_dir"]+"/index.html"):
   print("WARNING: index.html exists, not re-creating.")
else: 
   os.system("cp "+os.environ["VARCODE"]+"/html/mdtf_diag_banner.png "+os.environ["variab_dir"])
   os.system("cp "+os.environ["VARCODE"]+"/html/mdtf1.html "+os.environ["variab_dir"]+"/index.html")

# ======================================================================
# Diagnostics:
# ======================================================================

# Diagnostic logic: call a piece of python code that: 
#   (A) Calls NCL, python (or other languages) to generate plots (PS)
#   (B) Converts plots to png
#   (C) Adds plot links to HTML file

pod_procs = []
log_files = []
for pod in pod_configs:
   # Find and confirm POD driver script , program (Default = {pod_name,driver}.{program} options)
   # Each pod could have a settings files giving the name of its driver script and long name

   if verbose > 0: print("--- MDTF.py Starting POD "+pod['pod_name']+"\n")

   command_str = pod['settings']['program']+" "+pod['settings']['driver']  
   if test_mode:
      print("TEST mode: would call :  "+command_str)
   else:
      start_time = timeit.default_timer()
      log = open(os.environ["variab_dir"]+"/"+pod['pod_name']+".log", 'w')
      log_files.append(log)
      try:
         print("Calling :  "+command_str) # This is where the POD is called #
         proc = subprocess.Popen(command_str, shell=True, env=os.environ, stdout=log, stderr=subprocess.STDOUT)
         pod_procs.append(proc)
      except OSError as e:
         print('ERROR :',e.errno,e.strerror)
         print(errstr + " occured with call: " +command_str)

for proc in pod_procs:
   proc.wait()

for log in log_files:
   log.close()
               
if verbose > 0: 
   print("---  MDTF.py Finished POD "+pod+"\n")
   # elapsed = timeit.default_timer() - start_time
   # print(pod+" Elapsed time ",elapsed)


# ======================================================================
# Record settings in file variab_dir/config_save.yml for rerunning
#=======================================================================
out_file = os.environ["variab_dir"]+'/config_save.yml'
if os.path.isfile(out_file):
   out_fileold = os.environ["variab_dir"]+'/config_save_OLD.yml'
   if ( verbose > 1 ): print "WARNING: moving existing namelist file to ",out_fileold
   shutil.move(out_file,out_fileold)
file_object = open(out_file,'w')  #create it
yaml.dump(config, file_object)
file_object.close() 


# ==================================================================================================
#  Make tar file
# ==================================================================================================
if ( ( os.environ["make_variab_tar"] == "0" ) ):
   print "Not making tar file because make_variab_tar = ",os.environ["make_variab_tar"]
else:
   print "Making tar file because make_variab_tar = ",os.environ["make_variab_tar"]
   if os.path.isfile( os.environ["variab_dir"]+".tar" ):
      print "Moving existing "+os.environ["variab_dir"]+".tar to "+os.environ["variab_dir"]+".tar_old"
      os.system("mv -f "+os.environ["variab_dir"]+".tar "+os.environ["variab_dir"]+".tar_old")
      os.chdir(os.environ["WKDIR"])

   print "Creating "+os.environ["variab_dir"]+".tar "
   status = os.system(
      "tar --exclude='*netCDF' --exclude='*nc' --exclude='*ps' --exclude='*PS' -cf " + variab_dir + ".tar " + variab_dir)
   if not status == 0:
      print("ERROR $0")
      print("trying to do:     tar -cf "+os.environ["variab_dir"]+".tar "+os.environ["variab_dir"])
      exit()

print "Exiting normally from ",__file__
exit()
