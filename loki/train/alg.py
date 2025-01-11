# encoding: utf-8
"""
loki.train.alg.py
~~~~~~~~~~~~~~~~~

Implementation for MVA training, testing and evaluation

TODO: update documentation once generic interface built

"""
__author__    = "Will Davey"
__email__     = "will.davey@cern.ch"
__created__   = "2016-07-20"
__copyright__ = "Copyright 2016 Will Davey"
__license__   = "GPL http://www.gnu.org/licenses/gpl.html"


## modules
from loki.core.logger import log
from loki.core.helpers import mkdir_p, get_all_subclasses
from loki.core.sample import Sample
from loki.core.var import VarBase, View, get_variable
from loki.core.helpers import ProgressBar
from loki.utils.system import get_project_path
import os, sys, shutil, time, itertools, json, logging, tempfile
from glob import glob
from array import array
from copy import copy
from multiprocessing import Pool, cpu_count
import subprocess

# - - - - - - - - - - - - - - -  class defs - - - - - - - - - - - - - - - - - #
#------------------------------------------------------------------------------=buf=
class AlgBase(object):
    """Generic interface for multivariate algorithm training/prediction 
    
    Subclasses should be written for specific algorithms, and should 
    overload :func:`__subclass_train__` and :func:`__subclass_predict__`.
    
    Input data is provided in the form of :class:`~loki.core.sample.Sample`. 
    It is intended that these are comprised of single flat ntuples. If you 
    are starting from nested MxAOD samples, merge them into single trees via 
    :func:`~loki.train.ntup.flatten_ntup`.
    An example can be found in: example09_flatntup.py   
        
    Specific implemenations are available in :mod:`loki.train.algs`.

    Important Caveats when building AlgBase subclasses: 
    
    * named args passed to sub-class constructor must be set as attributes
      with the same name as the arg, otherwise alg serialization will fail.
    * as training is performed in a tmpdir, the :func:`__get_abspath_worker__` 
      and :func:`__get_sample_worker__` helper functions should be used 
      to access config files and samples in the subclass specific 
      :func:`__subclass_train__` method.

    Other than the *name* argument, no other arguments are intended to be 
    passed by the user to the subclass constructor. Rather they are 
    either set in the :func:`load` method or in the subclass constructor.

    :param name: algorithm name
    :type name: str
    :param wspath: workspace path (don't set yourself, passed by :func:`~loki.train.alg.load`) 
    :type wspath: str
    :param valtype: value type of algorithm output (set by subclass constructor)
    :type valtype: char
    :param info: algorithm info (don't set yourself, passed by :func:`~loki.train.alg.load`)
    :type info: dict
    """
    # 'static' variables
    fname_json = "config.json"
    dname_aux = "aux"    
    #__________________________________________________________________________=buf=
    def __init__(self, name = None, wspath = None, valtype = None, info = None):
        # general defaults
        if name is None: name = "MyAlgorithm"
        if valtype is None: valtype = 'f'
        if info is None: info = dict()
        
        # need to have abs path to allow processing in tmp dir
        if wspath: wspath = os.path.abspath(wspath) 

        # attributes
        self.name = name
        self.wspath = wspath
        self.valtype = valtype
        self.info = info
            
        # get constructor args (removing 'self')
        self.__stream_attrs__ = list(self.__init__.__code__.co_varnames)[1:]
        self.submitdir = os.getcwd()
        self.tmpdir = None
        self.logout = None
        self.logerr = None

        if wspath and not self.ispersistified():
            log().warn("Passing 'wspath' to alg constructor does not persistify, use alg.saveas(wspath)") 

    # 'Public' interface
    #__________________________________________________________________________=buf=
    def train(self):
        """Train the classifier"""
        self.__start_train__()
        if not self.__subclass_train__():
            log().error("Problem encountered during training")
            return False
        self.__end_train__()
        return True
        
    #__________________________________________________________________________=buf=
    def predict(self, s, **kw):
        """Predict classifier output 
                
        :param s: sample
        :type s: :class:`~loki.core.sample.Sample`
        :param kw: key-word args passed to sub-class predict
        :rtype: class:`array`
        """
        return self.__subclass_predict__(s, **kw)
    
    #__________________________________________________________________________=buf=
    def get_var_name(self, **kw):
        """Return unique tag based on kw args passed to the predict method 
        (can override in subclass)
        """
        return self.name

    #__________________________________________________________________________=buf=
    def ispersistified(self):
        """Return True if alg is persistified"""    
        return self.info.get("persistified", False)
    
    #__________________________________________________________________________=buf=
    def saveas(self, wspath):
        """Persistify the workspace at new path
        
        *wspath* cannot refer to existing workspace. To save an alg that has 
        already been persistified to a workspace, use :func:`save`.
        
        :param wspath: workspace path
        :type wspath: str
        """
        # validate wspath 
        if not wspath:
            log().error("Cannot create algorithm without workspace")
            return False        
        wspath = wspath.strip().rstrip("/") # strip whitespace and trailing '/'
        if not wspath.endswith(".alg"):
            log().error(f"Alg workspace must have '.alg' ext: {os.path.relpath(wspath)}")
            return False
        if os.path.exists(wspath): 
            log().error(f"Alg workspace {os.path.relpath(wspath)} already exists, cannot overwrite")
            return False
        self.wspath = os.path.abspath(wspath)

        # create workspace
        log().info(f"Creating alg workspace {os.path.relpath(wspath)}")
        mkdir_p(wspath)

        # persistify to json
        return self.save()
            
    #__________________________________________________________________________=buf=
    def save(self):
        """Persistify the workspace. 
        
        Can only be called after the algorithm has already been persistified with 
        :func:`saveas`. 
        """
        if not self.wspath: 
            log().error("Cannot save non-persistified workspace (try saveas)")
            return False
        
        # set persistified
        self.info["persistified"] = True
        
        # prepare attributes
        (config, samples, info) = self.__get_attr_groups__()                
        d = dict()
        d["name"] = self.name
        d["class"] = self.__class__.__name__
        d["config"] = config
        #d["samples"] = {k:v.serialize() for (k,v) in samples.items()}
        d["samples"] = samples
        d["info"] = info        
        
        # persistify to json
        jconfig = os.path.join(self.wspath, self.fname_json)
        with open(jconfig, "w") as f:
            json.dump(d, f, indent=4, sort_keys=True, cls=LokiEncoder)        
        
        return True

    #__________________________________________________________________________=buf=
    def kwargs(self):
        """Return constructor arguments"""
        return {k:getattr(self,k) for k in self.__stream_attrs__}

    #__________________________________________________________________________=buf=
    def clone(self, **kw):
        """Return a clone of the algorithm with 'info' reset
        
        :param kw: override key-word args passed to alg constructor 
        """
        oldkw = self.kwargs()
        oldkw.pop("wspath", None)
        oldkw.pop("info", None)
        oldkw.update(kw)
        return self.__class__(**oldkw)

    #__________________________________________________________________________=buf=
    def print_config(self):
        """Print Alg Configruation Summary"""

        # get attributes
        (config, samples, info) = self.__get_attr_groups__()
        name = self.name
        wspath = self.wspath
        
        log().info("")
        log().info("=====>>>>>> Loki MVA Algorithm Configuration <<<<<<=====")
        
        # header
        log().info("Algorithm :")
        log().info(f"  Name    : {name}")
        log().info(f"  Class   : {self.__class__.__name__}")
        log().info(f"  File    : {wspath}")
        log().info("")
        
        # configuration
        log().info("Configuration : ")
        self.__print_dict__(config)

        # samples
        log().info("Samples: ")
        self.__print_dict__({k:v.serialize() for (k,v) in samples.items()}, ignored=["sel"])
            
        # info
        log().info("Info: ")
        self.__print_dict__(info)

        # working dir
        log().info(f"Working dir: {os.getcwd()}")
        log().info("")


    # 'Virtual' interfaces
    #__________________________________________________________________________=buf=
    def __subclass_train__(self):
        """Sub-class specific trainig implementation (overwrite in subclass)
        
        This method is not directly called by the user. The user calls
        :func:`train`, which does some basic pre- and post-training operations. 
        
        IMPORTANT: one of the pre-training operations is to change to a temporary
        working directory, to avoid unwanted interaction between output of 
        concurrently trained algorithms. Because of this, it is important to 
        use the helper functions :func:`__get_abspath_worker__` and 
        :func:`__get_sample_worker__` in the subclass implementation of 
        :func:`__subclass_train__`, which will convert config file paths
        and samples to be given w.r.t. the submit directory (where train 
        was called). 
        
        """
        log().warn(f"Train not implemented for {self.__class__.__name__}")
        return True

    #__________________________________________________________________________=buf=
    def __subclass_predict__(self, s, **kw):
        """Sub-class specific prediction implementation (overwrite in subclass)"""
        log().warn("Predict not implemented for {}".format(self.__class__.__name__))
        return []

    #__________________________________________________________________________=buf=
    def __predict_single__(self, invals):
        """Predict classifier output based on input values *invals* (overwrite in subclass)
        
        This is the simplest way to implement a predict method. The method should 
        predict the output value(s) of the algorithm for one event, based on a set 
        of input values (*invals*). After overriding this method in your sub-class, 
        call :func:`__predict_python_loop__` in your :func:`__subclass_predict__`
        implementation.
        """
        log().warn("Predict single not implemented for {}".format(self.__class__.__name__))
        return 0.0

    # Concrete implementation (helper functions)
    #__________________________________________________________________________=buf=
    def __print_dict__(self, d, ignored=None):
        """Print content of a dictionary in a commonly formatted way"""
        if ignored is None: ignored = []
        if d:  
            for (k,v) in d.items():
                if isinstance(v,dict): 
                    log().info("  {} :".format(k))
                    for (k2,v2) in v.items():
                        if v2 is not None and k2 in ignored:
                            log().warn("    {0:20s} : {1:20s} --> NOT SUPPORTED, ignoring!".format(k2, str(v2)))
                        else:
                            log().info("    {0:20s} : {1:20s}".format(k2,str(v2)))
                elif isinstance(v,list): 
                    log().info("  {} :".format(k))
                    for v2 in v: 
                        log().info("    {0:20s}".format(str(v2)))                        
                else:  
                    log().info("  {0:22s} : {1:20s}".format(k,str(v)))
        else: 
            log().info("  none set")
        log().info("")    
            
    #__________________________________________________________________________=buf=
    def __start_train__(self):
        """Generic training initialization 
        
        Can be overwritten in subclass if necessary, but note, most sub-class 
        specific initialization occurs within self.__subclass_train__ itself. 
        """
        if self.info.get("trained", False): 
            log().info("Retraining previously trained algorithm!")
        self._tstart = time.time()
        self.tmpdir = self.__tmp_wkdir__()
        self.print_config()
        self.__pretrain_checks__()
        
    #__________________________________________________________________________=buf=
    def __end_train__(self):
        """Generic training finalization 
        
        Can be overwritten in subclass if necessary, but note, most sub-class
        specific finalization occurs within self.__subclass_train__ itself.
        """
        tend = time.time()
        self.info["trained"] = True
        self.info["train_time"] = tend - self._tstart
        os.chdir(self.submitdir)
            
    #__________________________________________________________________________=buf=
    def __predict_python_loop__(self, inputs):
        """Generic predict using :func:`__predict_single__` in python loop"""
        log().info("Calculating var with python-based loop")
        entries = len(inputs[0][1])
        output = array(self.valtype, [])

        # build progress bar
        prog = None
        if log().level >= logging.INFO:
            prog = ProgressBar(ntotal=entries,text=self.name) 
        
        # process
        step = int(entries / 100)
        for i in range(entries):
            if prog and i%step==0: prog.update(i)
            output.append(self.__predict_single__([a[1][i] for a in inputs]))
        if prog: prog.update(entries)
        
        # finalize
        if prog: prog.finalize()
        return output

    #__________________________________________________________________________=buf=
    def __get_attr_groups__(self):
        """Return (config, samples, info) attributes"""
        # get attributes
        config = {k:v for (k,v) in self.__dict__.items() if k in self.__stream_attrs__}
        config.pop("name", None)
        config.pop("wspath", None)
        info = config.pop("info", None)
        samples = {k:v for (k,v) in config.items() if isinstance(v,Sample) }
        for v in samples: config.pop(v)
        return (config, samples, info)

    #__________________________________________________________________________=buf=
    def __get_abspath_worker__(self, path):
        """Return absolute path initially given wrt submitdir 
        
        Eg. on worker thread in tmp dir.
        """
        if os.path.isabs(path): return path
        return os.path.abspath(os.path.join(self.submitdir, path))

    #__________________________________________________________________________=buf=
    def __get_sample_worker__(self, s):
        """Return copy of sample with 'files' corrected to absolute path,  
        initially given wrt submitdir.
         
        Eg. on worker thread in tmp dir. 
        """
        if not s: return s
        snew = copy(s)
        snew.files =  [self.__get_abspath_worker__(f) for f in s.files]
        return snew

    #__________________________________________________________________________=buf=
    def __get_fmodel_path__(self):
        """Return path to the model file"""
        if not self.wspath: return None
        if not self.info.get("fmodel", None): return None
        return os.path.join(self.wspath,self.info["fmodel"])

    #__________________________________________________________________________=buf=
    def __tmp_wkdir__(self):
        """Create and change to temporary working dir and return its abspath"""
        temp_path = tempfile.mkdtemp(prefix='loki_') 
        os.chdir(temp_path)
        return temp_path

    #__________________________________________________________________________=buf=
    def __prepare_auxdir__(self):
        """Create aux dir"""
        auxdir = os.path.join(self.wspath, self.dname_aux)
        if not os.path.exists(auxdir):
            mkdir_p(auxdir)
        return auxdir

    #__________________________________________________________________________=buf=
    def __finalize_training_outputs__(self, fmodel_old, aux_files):
        """Move temp training outputs to final paths"""
        # model
        if fmodel_old:    
            if not os.path.exists(fmodel_old):
                log().warn("Failure writing model, output not found: {0}".format(fmodel_old))
            else:
                (_, fext) = os.path.splitext(fmodel_old)        
                fmodel_new = "model" + fext if fext else "model"
                fmodel_new_path = os.path.join(self.wspath, fmodel_new)
                if os.path.exists(fmodel_new_path): 
                    log().info("Removing existing model file: {}".format(fmodel_new_path))
                    os.remove(fmodel_new_path)
                log().info("Writing model: {0}".format(fmodel_new_path))
                shutil.move(fmodel_old, fmodel_new_path)
                self.info["fmodel"] = fmodel_new
    
        # aux files
        if aux_files:
            auxdir = self.__prepare_auxdir__()
            aux_files_new = []
            for faux_old in aux_files:
                if not os.path.exists(faux_old):
                    log().warn("Failure writing aux output, file not found: {0}".format(faux_old))
                else:
                    faux_new_abs = os.path.join(auxdir, os.path.basename(faux_old))
                    faux_new_rel = os.path.relpath(faux_new_abs, self.wspath)                    
                    if os.path.exists(faux_new_abs): 
                        log().info("Removing existing aux file: {}".format(faux_new_abs))
                        os.remove(faux_new_abs)
                    log().info("Writing aux output: {0}".format(faux_new_abs))
                    shutil.move(faux_old, auxdir)
                    aux_files_new.append(faux_new_rel)
            self.info["aux_files"] = aux_files_new

    # __________________________________________________________________________=buf=
    def __pretrain_checks__(self):
        """Perform some pre-train checks"""

        # get attributes
        (config, samples, info) = self.__get_attr_groups__()
        for s in samples.values():
            if s.sel: log().warn("AlgBase doesn't support sample selection: {}, ignoring.".format(s.sel.get_name()))

    # __________________________________________________________________________=buf=
    def __check_sample__(self, s, quiet=False):
        """Return True if sample suitable for use with AlgBase

        :param s: sample
        :type s: :class:`~loki.core.sample.Sample`
        """
        if len(s.files) != 1:
            if not quiet:
                log().error("Sample {} must have single file for use with AlgBase (has {})" \
                            .format(s.name,len(s.files)))
            return False
        if not os.path.exists(s.files[0]):
            if not quiet: log().error("File {} doesn't exist".format(s.files[0]))
            return False
        t = s.get_tree()
        if not t:
            if not quiet: log().error("Failed to get tree {} from file {}" \
                                      .format(s.treename, s.files[0]))
            return False
        return True



#------------------------------------------------------------------------------=buf=
class LokiEncoder(json.JSONEncoder):
    """JSONEncoder with implementation for :class:`~loki.core.sample.Sample`, 
    :class:`~loki.core.var.VarBase` and :class:`~loki.core.var.View`.
    """
    serializable = [Sample, VarBase, View]
    #__________________________________________________________________________=buf=
    def default(self, obj):
        if True in [isinstance(obj, cls) for cls in self.serializable]: 
            return obj.serialize()
        return json.JSONEncoder.default(self, obj)


#______________________________________________________________________________=buf=
def load(wspath):
    """Load and return AlgBase subclass(es)
    
    If wildcard (*) used, will return list of algs
    """
    # wildcard for multiple algs
    if '*' in wspath:
        wspaths = glob(wspath)
        algs = [load(wspath) for wspath in wspaths] 
        algs = [a for a in algs if a is not None]
        return algs
    
    # trim whitespace and trailing '/'
    wspath = wspath.strip().rstrip("/")

    # init from workspace
    if wspath.endswith(".alg"):
        if not os.path.exists(wspath): return None
        if not os.path.isdir(wspath): return None    
        jconfig = os.path.join(wspath, AlgBase.fname_json)
    # init from json 
    elif wspath.endswith(".json"): 
        jconfig = str(wspath)
        wspath = None      
        # scan algs dir if not found
        if not os.path.exists(jconfig):
            algdir = os.path.join(get_project_path(), "loki/mvacfg")
            log().info("{} not found in local path".format(jconfig))
            log().info("Scanning in {}".format(algdir))
            jconfig = os.path.join(algdir, jconfig)        
    else: return None 
    # check json config defined        
    if not os.path.exists(jconfig): return None        
    # parse json config
    with open(jconfig, 'r') as f:
        try: 
            cfg = json.load(f)
        except: 
            log().error("Failure parsing JSON file: {}, probably unwanted comma at list end".format(jconfig))
            return None

    # convert unicode values from json into python strings
    cfg = {convert_to_string(k): convert_to_string(v) for (k,v) in cfg.items()}   

    # get attribute blocks
    name = cfg.pop("name", None)
    algclass = cfg.pop("class", None)
    config = cfg.pop("config", None)
    samples = cfg.pop("samples", None)
    info = cfg.pop("info", None)
    
    # unset persistified if init from json (since no wspath defined)
    if info and not wspath: info["persistified"] = False
    
    # rebuild samples from dicts
    new_samples = dict()
    for (k,v) in samples.items():
        if v.get("sel",False):
            log().warn("AlgBase doesn't support sample selection: {}, may have unintended results!".format(v["sel"]))
        s = Sample(name=v.get("name",None),
                   files=v.get("files",None), 
                   sel=get_variable(v.get("sel",None)),
                   weight=get_variable(v.get("weight",None)))
        new_samples[k] = s
    samples = new_samples
    kwargs = dict(config)
    kwargs.update(samples)
    
    # find alg
    all_subclasses = get_all_subclasses(AlgBase)
    matches = [cls for cls in all_subclasses if cls.__name__ == algclass]
    if not matches: 
        log().warn("Subclass {} of AlgBase not found!".format(algclass))
        return None
    Alg = matches[0]
    if not Alg:
        log().warn("Something went wrong creating AlgBase subclass") 
        return None
    
    # build Alg
    alg = Alg(name=name, wspath=wspath, info=info, **kwargs)
    
    return alg


#______________________________________________________________________________=buf=
def train_local(algs, retrain=False, ncores=None):
    """Train a list of algorithms on local machine
    
    Previously trained algorithms will be skipped unless *retrain* is set to True. 
    
    :param algs: algorithms to train
    :type algs: list :class:`AlgBase`
    :param retrain: force retrain on previously trained algorithms
    :type retrain: bool
    :param ncores: number of cores to use
    :type ncores: int
    """
    if not isinstance(algs,list): algs = [algs]
    # multiple algs
    if len(algs)>1:
        # filter algs
        algs_submit = []
        for alg in algs:
            if alg.info.get("trained", False) and not retrain:
                log().info("{} already trained, skipping...".format(os.path.relpath(alg.wspath)))
                continue
            algs_submit.append(alg)
            
        if not algs_submit: 
            log().info("No algs to process")
            return True
        
        # determine number of cores
        if not ncores:   ncores = cpu_count()
        elif ncores < 0: ncores = max(1, cpu_count() + ncores)
        else:            ncores = min(ncores, cpu_count())
        
        # create pool and unleash the fury
        log().info("Processing {} algs in local mode".format(len(algs_submit)))
        log().info("Lighting up {} cores".format(ncores))        
        pool = Pool(processes=ncores)
        results = [pool.apply_async(run_train, (a.wspath,)) for a in algs_submit]
        
        # monitory progress
        failures = 0
        while results: 
            for r in results:
                if r.ready():
                    status = r.get()
                    results.remove(r)
                    if not status:
                        failures += 1
                        log().error("Training Job Failed! {} left".format(len(results)))
                    else: 
                        log().info("Job finished! {} left".format(len(results)))                        
            time.sleep(2)
        
        if failures:
            log().warn("Training completed with {} failures".format(failures))
            return False
        
        log().info("Training completed successfully!")
        return True
    
    # single job
    log().info("Processing single alg in local mode")
    alg = algs[0]
    if alg.info.get("trained", False) and not retrain:
        log().info("{} already trained, skipping...".format(os.path.relpath(alg.wspath)))
        return True
    if not alg.train():
        log().warning("Failure training {}".format(os.path.relpath(alg.wspath)))
        return False
    alg.save()
    return True


#______________________________________________________________________________=buf=
def train_pbs(algs, queue=None, retrain=False, import_module=None):
    """Submit alg train jobs to PBS batch queue. 
    
    Previously submitted algoirhtms will be skipped unless *retrain* is set to True. 

    :param algs: algorithms to train
    :type algs: list :class:`AlgBase`
    :param queue: PBS queue name (default: medium)
    :type queue: str
    :param retrain: force retrain on previously trained algorithms
    :type retrain: bool
    :param import_module: name of pre-import module
    :type import_module: str
    """
    # set defaults
    if queue is None: queue = "medium"

    # config
    script = os.path.join(get_project_path(), "scripts", "pbs_train.sh")    

    # filter algs
    if not isinstance(algs, list): algs = [algs]
    algs_submit = []
    for alg in algs:
        if alg.info.get("submitted_train", False) and not retrain:
            log().info("{} already trained, skipping...".format(os.path.relpath(alg.wspath)))
            continue
        algs_submit.append(alg)

    # submit
    if not algs_submit:
        log().info("No algs to be submitted.") 
        return True
    # job array submit
    else:
        # write job array file
        (fd, fname) = tempfile.mkstemp('.index', '.alg.', './') 
        for alg in algs_submit: 
            os.write(fd, "{}\n".format(alg.wspath))
        os.close(fd)

        # define job environment variables
        env = ["LOKIDIR={}".format(os.getenv("LOKIDIR")),
               "ALGINDEX={}".format(fname)]
        if import_module:
            # convert rel to abs path
            if os.path.exists(import_module):
                import_module = os.path.abspath(import_module)
            env +=["IMPORTMOD={}".format(import_module)]

        # unleash
        log().info("Submitting: {} algs".format(len(algs_submit)))
        cmdargs = ["qsub", 
                    "-d", os.getcwd(),
                    "-N", "loki-train-{}".format(os.path.basename(os.getcwd())),
                    "-t", "1-{}".format(len(algs_submit)), 
                    "-q", queue,
                    "-v", ",".join(env),
                    script]
        #print " ".join(cmdargs)
        retcode = subprocess.call(cmdargs)

    if retcode != 0: 
        return False
    
    # Set submitted to true
    for alg in algs_submit:
        alg.info["submitted_train"] = True
        alg.save()
    return True


#______________________________________________________________________________=buf=
def spawn_grid(alg, attrname, dirname=None):
    """Generate a grid of Algs from a template *alg*.
    
    The algorithm attribute that contains the dictionary to be used to contruct
    the grid must be specified by *attrname*.  
    
    The grid will be formed by makig all possible combinations of options that 
    are specified as lists within this dictionary. For example, say your
    algorithm has the attribute "algopts", which is a dictionary of algorithm 
    options. To make a grid template, you might fill it something like this: 
    
    .. code-block:: python
    
        algopts : {
            "NTrees": [20, 30, 40, 60, 100], 
            "MaxDepth": [8, 10, 12],
            "MinNodeSize": 0.1,
            ...
            }
    
    This will create 5 x 3 = 15 grid points. 
     
                
    :param alg: template algorithm
    :type alg: list :class:`AlgBase`
    :param attrname: name of alg attribute 
    :type attrname: str
    :param dirname: output directory name (if None, current directory used) 
    :type dirname: str            
    """
    if alg.ispersistified(): 
        log().info("Spawning algs from: {}".format(os.path.relpath(alg.wspath)))
    else: 
        log().info("Spawning algs from: {}".format(alg.name))

    # Get all combinations of options
    grid = getattr(alg, attrname)
    if not isinstance(grid, dict): 
        log.error("attribute for spawn_grid must be dict")
        return []
    options = {key: grid[key] if isinstance(grid[key], list) else [grid[key]] for key in grid}
    keys, vals = options.keys(), options.values()
    product = itertools.product(*vals)
    options = [dict(zip(keys, x)) for x in product]
                    
    # prepare
    if alg.ispersistified(): 
        prefix = os.path.splitext(os.path.basename(alg.wspath))[0]
    else: 
        prefix = alg.name or ""
    if dirname: 
        if not os.path.exists(dirname): 
            mkdir_p(dirname)
        prefix = os.path.join(dirname, prefix) 

    # Build grid point workspaces
    index=0    
    for opt in options:
        # get next available wspath
        while True: 
            label = "{:04}".format(index)
            wspath = prefix + label + ".alg"
            if not os.path.exists(wspath): break
            index+=1
        name = "{}{}".format(alg.name,label)
        newalg = alg.clone(name=name, **{attrname: opt})
        newalg.saveas(wspath)


#______________________________________________________________________________=buf=
def run_train(wspath):
    """Run alg train on multiprocess thread"""
    f = open(os.path.join(wspath,"train.log"),'w')
    sys.stdout = sys.stderr = f
    os.dup2(f.fileno(), 1)
    os.dup2(f.fileno(), 2)
    alg = load(wspath)
    status = alg.train()
    sys.stdout = sys.__stdout__
    sys.stderr = sys.__stderr__
    if not status: return False
    alg.save()
    return True


#______________________________________________________________________________=buf=
def convert_to_string(o):
    """Recursively convert unicode objects to python string"""
    if   isinstance(o,str): 
        return str(o)
    elif isinstance(o,list): 
        return [convert_to_string(i) for i in o]
    elif isinstance(o,dict): 
        return {convert_to_string(k):convert_to_string(v) for (k,v) in o.items()}
    return o


## EOF
