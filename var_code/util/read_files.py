# This file is part of the util module of the MDTF code package (see mdtf/MDTF_v2.0/LICENSE.txt)


import re 
import os
import sys
import yaml


def get_var_from_namelist(varname,vartype,vardict,default,verbose=0):
   if (varname in vardict): 
      if verbose > 2: print "get_var_from_namelist found key ",varname," of type ",type(default)," in dict"

      if type(default) == type(True):    #boolean
         var = get_boolean_from_namelist(varname,vardict,default,verbose) 
      elif type(default) == type(0):     #int
         var = get_int_from_namelist(varname,vardict,default,verbose) 
      elif type(default) == type('s'):   #string
         var = vardict['varname']
      else:
         errstr= "get_var_from_namelist cannot deal with vartype ",vartype
         return return_default_from_namelist(varname,default,errstr=errstr,verbose=verbose)

      if verbose > 2: print "VAR from namelist: ",varname," = ",var
      return var

   else:
      errstr = "Did not find varname ",varname," in dict"
      return return_default_from_namelist(varname,default,errstr=errstr,verbose=verbose)


def get_boolean_from_namelist(varname,vardict,default,verbose=0):

   if verbose > 2: print "get_boolean_from_namelist ",varname
   
   try:
      var = (vardict[varname] in ('True', 'true', '1'))
   except:
      errstr = "Failed to eval() ",varname," = ",vardict[varname]
      return return_default_from_namelist(varname,default,errstr=errstr,verbose=verbose)

   if ( type(var) != type(True) ):
      errstr = "Conversion to boolean erroneously returned type "+type(var)
      return return_default_from_namelist(varname,default,errstr=errstr,verbose=verbose)
   else:
      if verbose > 2: print "SUCCESS: trying for boolean, var ',varname,' is type ",type(var)

   return var


def get_int_from_namelist(varname,vardict,default,verbose=0):

   if verbose > 2: print "get_int_from_namelist ",varname
   
   try:
      var = int(vardict[varname])
   except:
      errstr = "Conversion to int failed, for ",varname," = ",vardict[varname]
      return return_default_from_namelist(varname,default,errstr=errstr,verbose=verbose)

   if ( type(var) != type(0) ):
      errstr = "Conversion to int erroneously returned type "+type(var)
      return return_default_from_namelist(varname,default,errstr=errstr,verbose=verbose)
   else:
      if verbose > 2: print "SUCCESS: trying for intvar ',varname,' is type ",type(var)

   return var

#==========================================================================
def pprint_dict(dict,title=""):
   if ( title != "" ): print title
   if ('casename' in dict):  # print in this order
      print "\t  %-10s =  " % "casename",dict['casename']
      print "\t  %-10s =  " % "modeltype",dict['modeltype']
      print "\t  %-10s =  " % "firstyr",dict['firstyr']
      print "\t  %-10s =  " % "lastyr",dict['lastyr']
   else: 
      for key, value in dict.iteritems():
         print "\t "+str(key)+" = "+str(value)

def pprint_list(list_in,title=""):
   for item in list_in:
      if (type(item)== type({})):
         pprint_dict(item,title=title)
      else:
         print "\t "+str(item)

#==========================================================================
class Any_file_input:
   pass

class Varlist:
   def __init__(self):
      self.varlist = []


class Namelist:
   def __init__(self):
      self.case     = {}  #dict ['casename',casename],['modeltype',model],['startyr',startyr],,['endyr',endyr]
      self.pod_list = []  #list [pod_name1,pod_name2,...]
      self.envvar   = {}  #dict ['envvar_name',envvar_value,],...
#      print "Namelist initialized self"
#      print self
      

def get_available_programs(verbose=0):
   return {'py': sys.executable, 'ncl': 'ncl'}  

def print_namelist_podlist(namelist,verbose=0):
   print "POD LIST : "
   pprint_list(namelist.pod_list)

def print_namelist_case(namelist,verbose=0):
   print("CASE LIST :")
   pprint_dict(namelist.case)

def print_namelist(namelist,verbose=0):
   print_namelist_case(namelist,verbose)
   print_namelist_podlist(namelist,verbose)

def print_varlist(varlist,pod_name,verbose=0):
   if (verbose > 1): print pod_name+" varlist: "
   for i in varlist:
      print "\t",i

def return_default_from_namelist(varname,default,errstr="",verbose=0):
   if verbose > 0: print "WARNING: Using default ",varname,"  = ",default," ",errstr
   return default



def check_required_envvar(verbose=0,*varlist):
   varlist = varlist[0]   #unpack tuple
   for n in range(len(varlist)):
      if ( verbose > 2): print "checking envvar ",n,varlist[n],str(varlist[n])
      try:
         test = os.environ[varlist[n]]
      except:
         print "ERROR: Required environment variable ",varlist[n]," not found "
         print "       Please set in input file (default namelist) as VAR ",varlist[n]," value "
         exit()

def determine_pod_name(path ,verbose=0):
   if (verbose > 2): print "determine_pod_name received args ",path
   filename_split = path.split('/')
   if ( len(filename_split) >= 1 ):
      if (verbose > 1 ): print "Setting pod_name to ",filename_split[-2]
      return filename_split[-2]
   else:
      return ""

def remove_junk(line,verbose=0):
   if (verbose > 2 ): print "remove_junk: received line",line
   spec_chars = re.compile(r"[\"\t\n:, ]+") #define spec_chars to split string below,
   line_in = spec_chars.split(line) # split string by characters defined above in spec_chars (space, tab, comma, ", ...) 
   line_in = filter(None,line_in)   # remove empty elements
   
   if (verbose > 2 ): print "remove_junk: returning line_in",line_in
   return line_in



def parse_namelist(file_input,file_contents, verbose=0):
   func_name = " read_namelist_case "
   if verbose > 2: print func_name +" called with args: ",file_contents['case_list'][0]
   file_input.namelist.case['casename'] = file_contents['case_list'][0]['CASENAME']
   file_input.namelist.case['modeltype'] = file_contents['case_list'][0]['model']
   file_input.namelist.case['firstyr'] = file_contents['case_list'][0]['FIRSTYR']
   file_input.namelist.case['lastyr'] = file_contents['case_list'][0]['LASTYR']

   os.environ["CASENAME"] = file_input.namelist.case['casename']
   os.environ["model"]    = file_input.namelist.case['modeltype']
   os.environ["FIRSTYR"]  = str(file_input.namelist.case['firstyr'])
   os.environ["LASTYR"]   = str(file_input.namelist.case['lastyr'])

   file_input.namelist.pod_list = file_contents['pod_list']
      
   for varname, varvalue in file_contents['settings'].items():
      # environment variables must be strings
      if type(varvalue) is bool:
         if varvalue == True:
            varvalue = '1'
         else:
            varvalue = '0'
      elif type(varvalue) is not str:
         varvalue = str(varvalue)
      file_input.namelist.envvar[varname] = varvalue  #this should be sent to setenv but currently is not!
      os.environ[varname] = varvalue
      if ( verbose > 1 ): print func_name," Added environment variable:  ",varname," = ",varvalue

def read_pod_varlist_varname(varname_in,verbose=0):
   func_name = " read_pod_varlist_varname "
   if ( verbose > 2): print func_name+" read in varname: ",varname_in
   if ( varname_in in os.environ ):
      varname = os.environ[varname_in]  #gets variable name as imported by set_variables_$modeltype.py
      if ( verbose > 1): print func_name+" found varname: ",varname
   else: 
      varname = varname_in
      if ( verbose > 1): print func_name+"WARNING: didn't find ",varname, " in environment vars, not substituting"
      #      print "To do: Modify read_files.main to accept argument of model type and import"
   if ( verbose > 2): print func_name + "returning ",varname
   return varname

def parse_pod_varlist(file_input,file_contents,verbose=0):
   func_name = " parse_pod_varlist: "
   default_file_required = False 
   for var in file_contents['varlist']:
      item = {}
      item['varname'] = read_pod_varlist_varname(var['var_name'], verbose=verbose)

      assert(var['freq'] in ["1hr","3hr","6hr","day","mon"]), \
         "WARNING: didn't find "+var['freq']+" in frequency options "+\
            " (set in "+__file__+":"+func_name+")"
      item['varfreq'] = var['freq']
      if 'requirement' in var.keys():
         item['required'] = (var['requirement'].lower() == 'required')
      else:
         item['required'] = default_file_required
      if 'alternates' in var.keys():
         item['alternatives'] = var['alternates']
      else:
         item['alternatives'] = ''

      file_input.varlist.append(item)  #Add this item to the list of all requested
      if ( verbose > 1): print "added item to file_input.varlist ",file_input.varlist[-1]

def makefilepath(varname,timefreq,casename,datadir):
    """ 
    USAGE (varname, timefreq, casename, datadir )
       str varname  (as set by var_code/util/set_variables_*.py)
       str timefreq "mon","day","6hr","3hr","1hr"
       str datadir directory where model data lives

    """

    return datadir+"/"+timefreq+"/"+casename+"."+varname+"."+timefreq+".nc"


def check_for_varlist_files(varlist,verbose=0):
   func_name = "\t \t check_for_varlist_files :"
   if ( verbose > 2 ): print func_name+" check_for_varlist_files called with ",varlist
#   all_required_files_found = True
   missing_list = []
   for item in varlist:
      if (verbose > 2 ): print func_name +" "+item
      filepath = makefilepath(item['varname'],item['varfreq'],os.environ['CASENAME'],os.environ['DATADIR'])

      if ( os.path.isfile(filepath) ):
         print "found ",filepath
      else:
         if ( not item['required'] ):
            print "WARNING: optional file not found ",filepath
         else: 
            if ( not 'alternatives' in item ):
               print "ERROR: required file not found ",filepath
               missing_list.append(filepath)
            else:
               alt_list = item['alternatives']
               if ( not alt_list  ):
                  print "ERROR: missing required file ",filepath,". No alternatives found"
                  missing_list.append(filepath)
               else:
                  print "WARNING: required file not found ",filepath,"\n \t Looking for alternatives: ",alt_list
                  for alt_item in alt_list: # maybe some way to do this w/o loop since check_ takes a list
                     if (verbose > 1): print "\t \t examining alternative ",alt_item
                     new_var = item.copy()  # modifyable dict with all settings from original
                     new_var['varname'] = read_pod_varlist_varname(alt_item,verbose=verbose)  # alternative variable name 
                     del new_var['alternatives']    # remove alternatives (could use this to implement multiple options)
                     if ( verbose > 2): print "created new_var for input to check_for_varlist_files",new_var
                     missing_list.append(check_for_varlist_files([new_var],verbose=verbose))

   if (verbose > 2): print "check_for_varlist_files returning ",missing_list

   #   return all_required_files_found
   missing_list_wo_empties = [x for x in missing_list if x]
   return missing_list_wo_empties

def set_pod_driver(varval,pod_name,verbose=0):
   func_name = " set_pod_driver "
   if verbose > 2:  print func_name+" received input: ",varval,pod_name

   driver_fullpath = os.path.join(os.environ["VARCODE"],pod_name,varval)
   errstr = "ERROR: "+func_name+" driver script specified in "+pod_name+"/settings file does not exist"
   assert( os.path.exists(driver_fullpath)),errstr  #this should be an error since user setting!

   if (verbose > 2):  print "confirmed existence of settings file driver ",driver_fullpath

   return driver_fullpath

def set_pod_program(driver,verbose=0):
   func_name = "set_pod_program"
   if verbose > 2:  print func_name+" received input: ",driver

   programs = get_available_programs()
   program_tails = programs.keys()

   # Find ending of filename to determine the program that should be used
   pod_tail  = driver.split(".")[-1]   #last element of the split (can have full path or not)

   # Possible error: Driver found but tail is not recognized so program can't call
   errstr_programs = "Available programs: "+str(program_tails)
   errstr_badtail = func_name+" does not know how to call a ."+pod_tail+" file \n\t"+errstr_programs
   assert (pod_tail in program_tails),errstr_badtail

   if ( verbose >2): print func_name +": Found program "+programs[pod_tail]

   return programs[pod_tail]

def parse_pod_settings(file_input,file_contents,verbose=0):
   func_name = " read_pod_settings "
   for var, varval in file_contents['settings'].items():
      if (verbose > 1): print func_name+" setting "+var+" "+varval
      if ( var == 'driver'):
         file_input.pod_settings['driver']  = set_pod_driver(
            varval,file_input.pod_name,verbose)
         file_input.pod_settings['program'] = set_pod_program(
            file_input.pod_settings['driver'],verbose)
      else:
         file_input.pod_settings[var] = varval
   if (verbose > 2): print func_name+" "+str(file_input.pod_settings)

def check_pod_settings(pod_name,pod_settings,verbose=0):
   func_name = "check_pod_settings "
   if (verbose > 1):  print func_name," received POD settings: ",pod_name,pod_settings

   pod_dir  = os.path.join(os.environ["VARCODE"],pod_name)

   if ( not 'driver' in pod_settings):  #try to find one
      try_filenames = [pod_name+".","driver."]      
      programs = get_available_programs()

      if (verbose > 1):  print "WARNING: no valid driver entry found for ",pod_name

      # cross-product
      file_combos = [ file_root + program for file_root in try_filenames for program in programs.keys()]
      if verbose > 1: print "Checking for possible driver names in ",pod_dir," ",file_combos

      for try_file in file_combos:
         try_path = os.path.join(pod_dir,try_file)
         if verbose > 1: print " looking for driver file "+try_path
         if os.path.exists(try_path):
            pod_settings['driver'] = try_path
            if (verbose > 0): print "Found driver script for "+pod_name+" : "+pod_settings['driver']
            break    #go with the first one found
         else:
            if (verbose > 1 ): print "\t "+try_path+" not found..."

   # Possible error: No driver found
   errstr_nodriver = "No driver script found for package "+str(pod_name) +"\n\t"\
                 +"Looked in "+pod_dir+" for pod_name.* or driver.* \n\t"\
                 +"To specify otherwise, add a line to "+pod_name+"/settings file containing:  driver driver_script_name \n\t" \
                 +"\n\t"+func_name
   assert ('driver' in pod_settings),errstr_nodriver
   pod_settings['program'] = set_pod_program(pod_settings['driver'],verbose)

   if (verbose > 0): 
      print "POD settings: ",pod_name
      pprint_dict(pod_settings)


def read_mdtf_config_file(argv, verbose=0):
   if (verbose > 2): print "read_mdtf_config_file received arguments "+str(argv)
   
   namelist_file_default = os.environ["DIAG_HOME"]+"/config.yml"  
   if (len(argv) > 1 ):
      namelist_file = argv[1]
      if ( verbose > 0 ): print "Received command-line argument for input namelist file: ", namelist_file
   else:  #try the default
      namelist_file = namelist_file_default
      if ( verbose > 0 ): print """WARNING : Expected command-line argument with input namelist file name.
         \n\t Checking for default input namelist file """, namelist_file
   assert(os.path.exists(namelist_file)), "Input file does not exist "+str(namelist_file)

   fileobject = open(namelist_file, 'r')
   file_contents = yaml.safe_load(fileobject)
   fileobject.close()

   file_input = Any_file_input()
   file_input.namelist = Namelist()  #initialize class (defined above)
   file_input.pod_name = ""
   parse_namelist(file_input, file_contents, verbose)

   if (verbose > 1):
      print_namelist(file_input.namelist)  #print it to stdout 
   return file_input


def read_pod_settings_file(filename, verbose=0):
   assert(os.path.exists(filename)), "Input file does not exist "+str(filename)

   fileobject = open(filename,'r')
   file_contents = yaml.safe_load(fileobject)
   fileobject.close()

   file_input = Any_file_input()
   file_input.pod_name = determine_pod_name(filename)
   file_input.pod_settings = {}
   file_input.varlist = []
   parse_pod_settings(file_input, file_contents, verbose)
   check_pod_settings(file_input.pod_name, file_input.pod_settings, verbose=verbose)
   parse_pod_varlist(file_input, file_contents, verbose)

   if (verbose > 0): 
      print_varlist(file_input.varlist, file_input.pod_name)
   return file_input


# ------------ MAIN for testing ----------------------------------------------
# USAGE  python read_files.py filename [namelist,settings,varlist]

if ( __name__ != '__main__'): 
   pass
else:
   from sys import argv

   verbose = 1
   if (verbose > 0):
       print 'Testing functionality of read_files'

   if (len(argv) < 2 ):
       print "ERROR, read_files.py in testing mode requires filename argument"
   exit()

   read_mdtf_config_file(argv[1],verbose=verbose)


   
