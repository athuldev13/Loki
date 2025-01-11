# encoding: utf-8
"""
loki.utils.system.py
~~~~~~~~~~~~~~~~~~~~

Module for storing (system) properties. 

"""
__author__    = "Will Davey"
__email__     = "will.davey@cern.ch"
__created__   = "2016-03-03"
__copyright__ = "Copyright 2016 Will Davey"
__license__   = "GPL http://www.gnu.org/licenses/gpl.html"



## modules
import os
import loki


# - - - - - - - - - - - - - - -  class defs - - - - - - - - - - - - - - - - - #
#------------------------------------------------------------------------------=buf=
class Properties():
    """Class to write and retieve properties to/from file
    
    :param cfgfile: file to read from / write to
    :type cfgfile: str
    """
    #__________________________________________________________________________=buf=
    def __init__(self,cfgfile):
        self.data = dict()
        self.cfgfile = cfgfile 
        self.read_config()

    #__________________________________________________________________________=buf=
    def __del__(self):
        self.write_config()
    

    #__________________________________________________________________________=buf=
    def has_property(self,key):
        return self.data.has_key(key)

    #__________________________________________________________________________=buf=
    def get_property(self,key):
        return self.data.get(key,None)

    #__________________________________________________________________________=buf=
    def get_or_prompt_property(self,key):
        if not self.has_property(key): 
            val = raw_input(f"Please set {key}: ")
            self.data[key] = val
        return self.data[key] 

    #__________________________________________________________________________=buf=
    def email(self):
        return self.get_or_prompt_property("email")
    
    #__________________________________________________________________________=buf=
    def fullname(self):
        return self.get_or_prompt_property("User Name (First Last)")


    #__________________________________________________________________________=buf=
    def set_property(self,key,val):
        self.data[key] = val

    #__________________________________________________________________________=buf=
    def read_config(self):
        if not os.path.exists(self.cfgfile): return
        f = open(self.cfgfile)
        for line in f.readlines():
            line = line.strip()
            if line.startswith('#'): continue
            pair = [s.strip() for s in line.split(':')]
            self.data[pair[0]] = pair[1]

    #__________________________________________________________________________=buf=
    def write_config(self):
        f = open(self.cfgfile,'w')
        for (key,val) in sorted(self.data.items()):
            f.write("{0}: {1}\n".format(key,val))
        f.close()    


# - - - - - - - - - - - - - - - function defs - - - - - - - - - - - - - - - - #
#______________________________________________________________________________=buf=
def get_project_path():
    """Returns path to the local loki installation"""
    return os.path.abspath(os.path.join(os.path.dirname(loki.__file__),".."))


# - - - - - - - - - - - - - - - - globals - - - - - - - - - - - - - - - - - #
#g_user_prop = Properties(os.path.join(get_project_path(),'.user.cfg')) # Only used in utils/filegen, so made local 
#g_rel_prop = Properties(os.path.join(get_project_path(),'RELEASES')) # Never used in codebase????

## EOF
