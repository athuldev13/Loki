# encoding: utf-8
"""
loki.utils.helpers.py
~~~~~~~~~~~~~~~~~~~~~

helper functions for the *loki.utils* module.

"""
__author__    = "Will Davey"
__email__     = "will.davey@cern.ch"
__created__   = "2016-08-31"
__copyright__ = "Copyright 2016 Will Davey"
__license__   = "GPL http://www.gnu.org/licenses/gpl.html"



## modules
from loki.core.setup import setup
from loki.core.var import find_variable, Cuts, Weights, StaticExpr
from loki.core.logger import log
#from loki.common import vars, cuts #TODO: remove if no problems
import logging
import os

# - - - - - - - - - - - - - - - - class defs  - - - - - - - - - - - - - - - - #
class Arguments(object):
    """Dummy class used to hold attributes which can be passed to commanline functions 
    
    (since you can't add attributes directly to an object() instance)
    
    """
    pass


# - - - - - - - - - - - - - - - function defs - - - - - - - - - - - - - - - - #
#______________________________________________________________________________=buf=
def loki_setup(verbose=None):
    """Standard loki setup for command line utils"""
    loglevel = None
    suppresswarn = True
    suppresserr = True
    if verbose: 
        loglevel = logging.DEBUG
        suppresswarn = False
        suppresserr = False        
    setup(log_level = loglevel,
          suppress_root_msgs = suppresswarn,
          suppress_root_errors = suppresserr)


#______________________________________________________________________________=buf=
def read_args_file(fname):
    """Return list of args by parsing a text file"""
    if fname is None: return None    
    if not os.path.exists(fname): 
        log().error("FILE {0} doesn't exist".format(fname))
        return None
    
    args = []
    with open(fname,'r') as f:
        for l in f: 
            l = l.strip()
            if not l: continue
            if l.startswith("#"): continue
            args.append(l)
    return args

#______________________________________________________________________________=buf=
def read_args_str(arg_str):
    """Return list of args by parsing comma-separated string"""
    if arg_str is None: return None
    return [s.strip() for s in arg_str.split(",")]


#______________________________________________________________________________=buf=
def get_sel(sel_str):
    """Return selection variable from standard selection arg   
    
    Eg. for *sel_str* is 'TauJets.baseline1P,TauJets.pt30'
    
    Note: selection vars MUST be predefined (eg. in *loki.common.vars*)
    
    :param sel_str: comma-separated list of predefined selection variables
    :type sel_str: str
    :rtype: :class:`loki.core.var.VarBase`
    """
    if sel_str is None: return None
    sel_var_strs = read_args_str(sel_str)
    sel_vars = []
    for s in sel_var_strs: 
        var = find_variable(s)
        if var is None: 
            log().error("Requested SEL '{0}' not found, aborting!".format(s))
            exit(1)
        sel_vars.append(var)
    if len(sel_vars) == 1: 
        sel = sel_vars[0]
    else: 
        sel = Cuts("selection", sel_vars, temp=True)
    return sel

#______________________________________________________________________________=buf=
def get_wei(wei_str):
    """Return weight variable from standard weight arg
    
    Eg. for *wei_str* is 'weight,TauJets.weight_pt'
    
    Note: weight vars MUST be predefined (eg. in *loki.common.vars*)
    
    :param wei_str: comma-separated list of predefined weight variables
    :type wei_str: str
    :rtype: :class:`loki.core.var.VarBase`     
    """
    if wei_str is None: return None
    wei_var_strs = read_args_str(wei_str)
    wei_vars = []
    for w in wei_var_strs: 
        var = find_variable(w)
        if var is None: 
            log().error("Requested WEIGHT '{0}' not found, aborting!".format(w))
            exit(1)
        wei_vars.append(var)
    if len(wei_vars) == 1: 
        wei = wei_vars[0]
    else: 
        wei = Weights("weights", wei_vars, temp=True)
    return wei

#______________________________________________________________________________=buf=
def get_vars(var_str, isfile=False):
    """Return list of variables from standard vars arg

    Eg. for *var_str* is 'TauJets.pt,TauJets.eta'
    
    Note: vars don't have to be predefined. Undefined vars will be created on the 
    fly using :class:`loki.core.var.StaticExpr`. 
    
    :param var_str: comma-separated list of variables
    :type var_str: str
    :param isfile: if True, parse *var_str* as text file
    :type isfile: bool
    :rtype: list :class:`loki.core.var.VarBase`         
    """
    if isfile: var_strs = read_args_file(var_str)
    else:      var_strs = read_args_str(var_str)
    if not var_strs: return None
    return [find_variable(v) or StaticExpr(v) for v in var_strs]


#______________________________________________________________________________=buf=
def get_views(view_str, isfile=False, default=None):
    """Return list of variable views from standard var views arg

    Eg. for *var_str* is 'TauJets.pt:log,TauJets.eta', 
    returning the 'log' view for TauJets.pt and the default view for TauJets.eta.
    
    Can also specify a new view binning in format: VAR:NBINS;XMIN;XMAX, which will 
    be called "temp" view.
    
    Finally, can provide a *default* binning (eg. [1000, 0., 1.]) to be used if 
    no view found.

    Note: vars don't have to be predefined. Undefined vars will be created on the 
    fly using :class:`loki.core.var.StaticExpr`. 
    
    
    :param view_str: comma-separated list of predefined views VAR:VIEW
    :type view_str: str
    :param isfile: if True, parse *var_str* as text file
    :type isfile: bool
    :param default: default binning if no view found (nbins, xmin, xmax) 
    :type default: (int, float, float)
    :rtype: list :class:`loki.core.var.View`
    """
    if isfile: view_strs = read_args_file(view_str)
    else:      view_strs = read_args_str(view_str)
    views = []
    for view_str in view_strs:
        viewargs = None
        # view name or binning provided
        if view_str.count(':'): 
            (varname,viewname) = [v.strip() for v in view_str.split(':')]
            if viewname.count(";"):
                d = [v.strip() for v in viewname.split(';')] 
                viewargs = (int(d[0]), float(d[1]), float(d[2]))
            elif default: 
                viewargs = default
        # no view provided (take default view or default binning) 
        else: 
            varname = view_str.strip()
            viewname = None
        var = find_variable(varname)
        # var not found
        if var is None and not viewargs: 
            log().error("Requested VAR {0} not found!".format(varname))
            return None
        # create var on fly
        elif var is None: 
            var = StaticExpr(varname)
        view = var.get_view(viewname)
        # view not found
        if view is None and not viewargs:
            log().error("Requested VIEW {0} for VAR {1} not found!".format(viewname, varname))
            return None
        # create view on fly
        elif view is None:            
            var.add_view(*viewargs, name="temp")
            view = var.get_view("temp")
        views.append(view)
    return views


#______________________________________________________________________________=buf=
def get_args(arg_str, isfile=False):
    """Return dictionary of key-value pairs from tmva-style arg string
    
    Eg. for *arg_str* is '!V,AnalysisType=Classification,...'
    
    :param arg_str: comma-separated list of arguments
    :type arg_str: str
    :param isfile: if True, parse *arg_str* as text file
    :type isfile: bool
    :rtype: dict     
    """
    if isfile: arg_strs = read_args_file(arg_str)
    else:      arg_strs = read_args_str(arg_str)
    if not arg_strs: return None
    args = {}
    for s in arg_strs: 
        if s.count("="): 
            (key,val) = s.split('=')
            if val.lower() == "none": continue
            elif val.lower() == "true":  val = True
            elif val.lower() == "false": val = False 
            args[key] = val
        else: 
            if s.startswith("!"): 
                args[s[1:]] = False
            else: 
                args[s] = True
    return args


#______________________________________________________________________________=buf=
def start_profiler():
    """Return profiler"""
    import cProfile
    pr = cProfile.Profile()
    pr.enable()
    return pr


#______________________________________________________________________________=buf=
def stop_profiler(pr):
    """Summarize profiler"""
    pr.disable()
    import StringIO, pstats
    s = StringIO.StringIO()
    sortby = 'cumulative'
    ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
    ps.print_stats()
    print(s.getvalue())


#______________________________________________________________________________=buf=
def start_timer():
    """Return current time"""
    from time import time
    return time()


#______________________________________________________________________________=buf=
def stop_timer(ti):
    """Summarize job timing"""
    from time import time
    from datetime import timedelta
    time_str = str(timedelta(seconds=(time()-ti)))
    log().info("Execution time: {0}".format(time_str))


#______________________________________________________________________________=buf=
def import_module(fname):
    """Dynamically import python module"""
    from os import path
    mod = None
    mod_name,file_ext = path.splitext(path.split(fname)[-1])
    
    # filename import
    if file_ext.lower() == ".py":
        import imp 
        mod = imp.load_source(mod_name, fname)
    
    # module name import
    else: 
        import importlib
        preference = ['loki.common', 'loki', None]
        for prefix in preference:
            name = '.'.join([prefix,fname]) if prefix else fname
            try: 
                mod = importlib.import_module(name)
                break
            except: 
                continue
    if mod:
        log().info("Imported module {0}".format(mod.__name__))

    return mod


## EOF
