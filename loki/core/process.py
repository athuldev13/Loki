# encoding: utf-8
"""
loki.core.process
~~~~~~~~~~~~~~~~~

This module provides the core functionality to generate histograms
for samples from input MxAOD files. The histograms are generated 
using the cpp compiled LokiSelector class (located in loki/src
directory). 

The module also provides functionality for stripping python arrays
from TTrees and vice-versa. 

TODO: May want to reintroduce sample checking for daughters (eg. 
incase they are missing input files)

The old TTree::Draw style processor has been deprecated and is 
now located in the _depr_process module.

"""
__author__    = "Will Davey"
__email__     = "will.davey@cern.ch"
__created__   = "2012-11-04"
__copyright__ = "Copyright 2012 Will Davey"
__license__   = "GPL http://www.gnu.org/licenses/gpl.html"



## modules
import hashlib
import itertools
import logging
import shutil
import tempfile
import time
import operator
import os
from array import array
from multiprocessing import Pool, cpu_count 

import ROOT

from loki.core import filelock
from loki.core.filelock import FileLock #, TimeoutError TODO: INVESTIGATE: What does timeout error do????? How diud this work in Py2?
from loki.core.helpers import ProgressBar, mkdir_p
from loki.core.histutils import new_hist
from loki.core.logger import log
from loki.core.plot import Plot
from loki.core.var import VarError, default_cut, default_weight
from loki.utils.system import get_project_path

filelock.logger.setLevel(logging.WARNING)


# - - - - - - - - - - - class defs  - - - - - - - - - - - - #
                
#------------------------------------------------------------------------------=buf=
class Processor():
    """Class to process :class:`RootDrawable` objects

    Component histograms for the :class:`RootDrawable` objects 
    are filled using the cpp compiled LokiSelector class. 
    Higher-level drawable objects are constructed from the 
    component histograms. 

    The number of cores (*ncores*) to use when processing plots 
    can be specified. If not specified, all available cores 
    will be used. You can also provide a negative number, 
    in which case all but `|n|` cores are used. 

    By default, histogram caching is enabled. A unique hash 
    is generated for each histogram based on the x,y,z 
    variable draw expressions, the x,y,z binning, the 
    selection and weight expressions, and the event fraction. 
    An individual cache file is created for each input 
    file. The cache files are located under ``~/.lokicache``  
    

    :param event_frac: event fraction to process
    :type event_frac: float
    :param ncores: number of cores to use
    :type ncores: bool
    :param noweight: Disable sample weighting
    :type noweight: bool
    :param usecache: use histogram caching
    :type usecache: bool
        
    """
    #__________________________________________________________________________=buf=
    def __init__(self,
                 event_frac=None,
                 ncores=None,
                 noweight=False,
                 usecache=True,
                 ):        
        # config
        self.event_frac = self.__discritize_event_frac__(event_frac)
        self.ncores = ncores
        self.noweight = noweight
        self.usecache = usecache

        # members
        self.hists = []
        self.drawables = []
        self.processed_drawables = []
        self.jobs = {}

    #__________________________________________________________________________=buf=
    def register(self,drawables):
        """Register :class:`RootDrawable` or :class:`loki.core.plot.Plot` 
        
        :param drawables: single or list of ROOT drawables or plots (collection of drawables)
        :param drawables: single or list of :class:`RootDrawable` derivative or :class:`loki.core.plot.Plot`
        """
        if not isinstance(drawables, list):
            drawables = [drawables]
        self.drawables += drawables
        #self.hists+=drawable.get_component_hists()

    #__________________________________________________________________________=buf=
    def process(self,drawables=None):
        """Construct all registered objects
        
        If *drawables* provided, they will be registered prior to processing
        
        :param drawables: single or list of ROOT drawables or plots (collection of drawables)
        :param drawables: single or list of :class:`RootDrawable` derivative or :class:`loki.core.plot.Plot`
        """
        if drawables is not None: 
            self.register(drawables)
        self.__process__()
        
    #__________________________________________________________________________=buf=
    def draw_plots(self,plots=None):
        """Draw all registered plots
         
        If *plots* provided, they will be registered prior to processing 

        :param plots: single or list of plots
        :param plots: single or list of :class:`loki.core.plot.Plot`        
        """
        if plots is not None: 
            self.register(plots)
        self.__process__()
        for p in self.processed_drawables:
            if not isinstance(p, Plot): continue
            p.draw()
        

    #__________________________________________________________________________=buf=
    def write(self,f):
        """Write all processed drawables to file 
        
        :param f: output file
        :type f: :class:`ROOT.TFile`
        """
        for rd in self.processed_drawables:
            rd.write(f)
           
    #__________________________________________________________________________=buf=
    def __process__(self):
        """Process all registered drawable objects
        
        Workflow: 
        
        * Create hist configs for components of drawables (separate configs 
          are made for each input file)
        * Look for cached versions of hists
        * Collect uncached hists in selector configs (one selector per input file)
        * Process selectors using pool of threads, sequentially writing processed hists to cache. 
        * Merge hists for each subsample and scale. 
        * Construct higher level objects in the RootDrawables from component hists
              
        """
        log().info("Hist processor in da haus!")
        if not self.drawables: 
            log().info("Nothing to process")
            return

        # organise RootDrawable component hists into selector jobs 
        selectors = self.__get_selectors__()
        
        # process selector jobs using pool of worker threads
        self.__process_selectors__(selectors)

        ## construct drawables from component hists and clean up
        self.__finalize_outputs__()

    #__________________________________________________________________________=buf=
    def __discritize_event_frac__(self, event_frac):
        """Discritize event frac (necessary for creating hist hashes)"""
        if event_frac is None: return event_frac 
        new_event_frac = max(float(f"{event_frac:0.3f}"), 0.001)
        if event_frac != new_event_frac: 
            log().warn(f"Discretizing event fraction: {event_frac} -> {new_event_frac}")
        return new_event_frac

    #__________________________________________________________________________=buf=
    def __get_selectors__(self):
        """Configure RootDrawable components into selectors
        
        Work flow is: 
        
        * Create hist configs for components of drawables (separate configs 
          are made for each input file)
        * Look for cached versions of hists
        * Collect uncached hists in selector configs (one selector per input file)
        
        The histograms are grouped into selectors based on their input file 
        (a separate selector job is made for each individual input file)
        and their multivalued container (a selector job can only handle 
        variables from up to one multi-valued container, eg. TauJets).
        
        """
        event_frac = self.__discritize_event_frac__(self.event_frac)
        log().info("Preparing jobs...")
        log().info("Using {:.1f}% of available events".format(event_frac*100. if event_frac else 100.))
        
        # create tmp working path
        tmpdir = tempfile.mkdtemp(prefix='loki_')
        log().info(f"Created tmp work dir: {tmpdir}")
        
        # group hists into selector jobs based on mvcont and input file
        selector_dict = dict()
        file_dict = dict()
        for rd in self.drawables: 
            for h in rd.get_component_hists():
                # store all input components for hist in dict
                h.components = dict() 
                for s in h.sample.get_final_daughters():
                    if not s.files: continue
                    log().debug(f"sample files: {s.files}")
                    h.components[s] = []
                    
                    # combine selection from hist and sample
                    sel = default_cut()
                    if h.sel: sel = sel & h.sel
                    if s.sel: sel = sel & s.sel
            
                    # combine weight from hist and sample
                    weight = default_weight()
                    if not self.noweight: 
                        if h.weight: weight = weight * h.weight
                        if s.weight: weight = weight * s.weight

                    # determine multi-valued container group
                    # --------------------------------------
                    # this is important since only histograms 
                    # from the same mutli-valued container group 
                    # can be grouped together in a single selector
                    invars = [v.var for v in [h.xvar, h.yvar, h.zvar] if v]
                    invars += [v for v in [sel, weight] if v]
                    mvconts = set([c for v in invars for c in v.get_mvinconts()])
                    if len(mvconts) >= 2: 
                        log().warn(f"Hist {h.name} has multiple multi-valued containers, skipping")
                        continue
                    elif len(mvconts) == 1: mvcont = list(mvconts)[0]
                    else:                   mvcont = None
                    if not mvcont in selector_dict: 
                        selector_dict[mvcont] = dict() 

                    # create a component hist for each input file
                    # and add to corresponding selector
                    for f in s.files:
                        # get and cache input file hash and tree
                        if f not in file_dict:
                            fhash = file_hash(f)
                            tree  = s.get_tree(f)
                            file_dict[f] = {"hash":fhash, "tree":tree}
                        else: 
                            fhash = file_dict[f]["hash"]
                            tree = file_dict[f]["tree"]
                            
                        # get and cache selector for this file and mvcont
                        if f not in selector_dict[mvcont]:
                            # temp output file for selector
                            tmpfile = os.path.join(tmpdir, next(tempfile._get_candidate_names()))
                            log().debug(f"creating output file: {tmpfile}")
                            # number of events to process for selector
                            n = s.get_nevents(f)
                            if event_frac: n = int(event_frac*float(n))
                            # cache path for this input file  
                            fcache = os.path.join(os.getenv('HOME'), ".lokicache", f"{fhash}.root")
                            # now cache the selector and tree
                            scfg = SelectorCfg(fin=f,fout=tmpfile,fcache=fcache,
                                               tname=s.treename, nevents=n)
                            selector_dict[mvcont][f] = scfg 
                        else: 
                            scfg = selector_dict[mvcont][f]


                        # init vars using current tree
                        for var in [h.xvar, h.yvar, h.zvar]: 
                            if not var: continue
                            var.var.tree_init(tree)
                        for var in [sel, weight]: 
                            if not var: continue
                            var.tree_init(tree)
            
                        # generate unique hash for histogram
                        hhash = hist_hash(xvar=h.xvar, yvar=h.yvar, zvar=h.zvar, 
                                          sel=sel, wei=weight, event_frac=event_frac)
            
                        # check for cached hist
                        cached = False
                        if self.usecache and os.path.exists(scfg.fcache): 
                            fcache = ROOT.TFile.Open(scfg.fcache)
                            if fcache and fcache.Get(hhash): 
                                h.components[s] += [{"file":scfg.fcache, "hash":hhash, "cached":True}]
                                cached = True                            
                            fcache.Close()
                        
                        # prepare job if not cached           
                        if not cached: 
                            # hist configuration
                            zexpr = h.zvar.get_expr() if h.zvar else None
                            zbins = h.zvar.xbins if h.zvar else None
                            yexpr = h.yvar.get_expr() if h.yvar else None
                            ybins = h.yvar.xbins if h.yvar else None
                            xexpr = h.xvar.get_expr() if h.xvar else None
                            xbins = h.xvar.xbins if h.xvar else None
                            hcfg = HistCfg(hash=hhash, 
                                           xexpr=xexpr, xbins=xbins,
                                           yexpr=yexpr, ybins=ybins,
                                           zexpr=zexpr, zbins=zbins,
                                           wexpr = weight.get_expr(),
                                           sexpr = sel.get_expr(),
                                           )
                            log().debug(f"adding hist: {h.name}, hash: {hhash}")
                            scfg.add(hcfg)
                            h.components[s] += [{"file":scfg.fout, "hash":hhash}]

        # Remove selectors with no inputs (b/c cached versions were available)
        selectors = [scfg for sublist in selector_dict.values() 
                          for scfg in sublist.values() if scfg.hists]        
        return selectors

    #__________________________________________________________________________=buf=
    def __process_selectors__(self, selectors):
        """Process selectors using pool of worker threads"""

        # determine number of cores
        if not self.ncores:   ncores = min(2, cpu_count())
        elif self.ncores < 0: ncores = max(1, cpu_count() + self.ncores)
        else:                 ncores = min(self.ncores, cpu_count())
        
        # print job stats
        nfiles      = len(set([s.fin for s in selectors]))
        nev         = sum([s.nevents for s in selectors])
        nhist_proc  = sum([len(s.hists) for s in selectors])        
        nhist_cached= self.__get_nhist_cached__()
        nhist_total = self.__get_nhist_total__()
        nhist_dup   = nhist_total-nhist_cached-nhist_proc        
        log().info(f"")
        log().info(f"Job Summary")
        log().info(f"===========")
        log().info(f"Lighting up {ncores} cores!!!")
        log().info(f"Total files  : {nfiles}")
        log().info(f"Total events : {nev}")
        log().info(f"Hist summary")
        log().info(f"------------")
        log().info(f"  process    : {nhist_proc}")
        log().info(f"  duplicates : {nhist_dup}")
        log().info(f"  cached     : {nhist_cached}")
        log().info(f"  total      : {nhist_total}")
        log().info(f"")
        
        # compile cpp classes (must be done before sending jobs)
        load_cpp_classes()
        
        # create pool and unleash the fury
        ti = time.time()
        prog = ProgressBar(ntotal=nev,text="Processing hists") if log().level >= logging.INFO else None         
        pool = Pool(processes=ncores)
        results = [pool.apply_async(process_selector, (s,)) for s in selectors]
                
        nproc=0
        nhist_tot = 0
        nhist_cached = 0
        while results: 
            for r in results:
                if r.ready():
                    scfg = r.get()
                    nproc+=scfg.nevents
                    if self.usecache:
                        (ntot,ncache) = self.__cache_selector__(scfg)
                        nhist_tot += ntot
                        nhist_cached += ncache
                    results.remove(r)                    
            time.sleep(1)
            if prog: prog.update(nproc)
        if prog: prog.finalize()
        tf = time.time()
        dt = tf-ti
        log().info(f"Hist processing time: {dt:.1f} s")
        if self.usecache: 
            log().info(f"Cached {nhist_cached} / {nhist_tot} hists!")

    #__________________________________________________________________________=buf=
    def __cache_selector__(self, scfg):
        """Save tmp hists from selector into permanent cache files""" 
        fin_name = scfg.fout 
        fout_name = scfg.fcache
        # ensure cache dir exists
        fout_dir = os.path.dirname(fout_name)
        mkdir_p(fout_dir)
        # get lock on cache file
        fout_base = os.path.basename(fout_name)
        fout_lock = os.path.join(fout_dir, f".{fout_base}.lock")
        lock = FileLock(fout_lock)
        log().debug(f"Saving histograms to cache file: {fout_name}")
        nhist_cached = 0        
        try: 
            with lock.acquire(timeout = 20):
                # make tmp copy of cache incase failure
                ftmp_name = tempfile.mktemp()
                if os.path.exists(fout_name):
                    try: 
                        shutil.copy(fout_name, ftmp_name)
                    except: 
                        log().warn(f"Failed copying cache to tmp location, {fout_name} -> {ftmp_name}")
                        raise IOError
                                
                # open tmp cache
                ftmp = ROOT.TFile.Open(ftmp_name, "UPDATE")
                if not ftmp: 
                    log().warn(f"Failure opening cache: {ftmp_name}")
                    raise IOError
                
                # open input
                fin = ROOT.TFile.Open(fin_name)
                if not fin: 
                    log().warn(f"Failure opening tmp: {fin_name}")
                    raise IOError
                
                # copy hists from input to tmp
                for hhash in scfg.hists:
                    h = fin.Get(hhash)
                    if not h: 
                        log().warn(f"Couldn't get {hhash} from {fin_name}")
                        continue
                    ftmp.WriteTObject(h)
                    nhist_cached+=1
                
                # close, move back and cleanup
                fin.Close()
                ftmp.Close()
                if os.path.exists(fout_name):
                    os.remove(fout_name)
                shutil.copy(ftmp_name, fout_name)
                os.remove(ftmp_name)
        except TimeoutError: 
            log().warn(f"Couldn't get lock on cache: {fout_name}")
        except: 
            log().warn(f"Couldn't write hists to cache: {fout_name}")
        
        return (nhist_cached, len(scfg.hists))        
        


    #__________________________________________________________________________=buf=
    def __finalize_outputs__(self):
        """Merge component hists and construct higher-level RootDrawable objects"""
        event_frac = self.__discritize_event_frac__(self.event_frac)
        # group and merge all the outputs
        for rd in self.drawables:
            for h in rd.get_component_hists():
                rootobj = h.new_hist()
                h.set_rootobj(rootobj)
                for (s, components) in h.components.items():
                    # scale
                    if not self.noweight and s.scaler: 
                        scale = s.get_scale()
                        if event_frac: scale/=event_frac
                    else: 
                        scale = None
                                   
                    # merge sub-objects (from each file)
                    for c in components: 
                        f = ROOT.TFile.Open(c["file"])
                        o = f.Get(c["hash"]).Clone()
                        if scale: o.Scale(scale)
                        rootobj.Add(o)
                        f.Close()
            rd.build_rootobj()
            
        # accounting
        self.processed_drawables += self.drawables
        self.drawables = []

    #__________________________________________________________________________=buf=
    def __get_nhist_total__(self):
        """Return the total number of histograms needed to construct drawables"""
        n = 0
        for rd in self.drawables: 
            for h in rd.get_component_hists():
                for subcomponents in h.components.values():
                    n+=len(subcomponents)
        return n
                     
    #__________________________________________________________________________=buf=
    def __get_nhist_cached__(self):
        """Return the number of pre-cached histograms"""
        n = 0
        for rd in self.drawables: 
            for h in rd.get_component_hists():
                for subcomponents in h.components.values():
                    for sc in subcomponents: 
                        if sc.get("cached",False): n+=1
        return n


#------------------------------------------------------------------------------=buf=
class HistCfg(object):
    """Simple python class to store blueprints for cpp compiled LokiHist1D/2D/3D.
    
    The HistCfg objects are collected in an instance of :class:`SelectorCfg`. 
    
    The class should be kept simple to reduce load when streaming to worker threads 
    (to the :func:`process_selector`).  
    """
    #__________________________________________________________________________=buf=
    def __init__(self, hash=None, 
                 xexpr=None, xbins=None, 
                 yexpr=None, ybins=None,
                 zexpr=None, zbins=None,
                 sexpr=None, wexpr=None):
        # attributes
        self.hash = hash
        self.xexpr = xexpr
        self.xbins = xbins
        self.yexpr = yexpr
        self.ybins = ybins
        self.zexpr = zexpr
        self.zbins = zbins
        self.sexpr = sexpr
        self.wexpr = wexpr


#------------------------------------------------------------------------------=buf=
class SelectorCfg(object):
    """Simple python class to store blueprints for cpp compiled LokiSelector.
    
    The class should be kept simple to reduce load when streaming to worker threads 
    (to the :func:`process_selector`).      
    """
    #__________________________________________________________________________=buf=
    def __init__(self, fin=None, fout=None, fcache=None, tname=None, nevents=None):
        self.fin = fin 
        self.fout = fout
        self.fcache = fcache
        self.tname = tname
        self.nevents = nevents
        self.hists = dict()

    #__________________________________________________________________________=buf=
    def add(self, h):
        """Add histogram configuration (HistCfg) to selector config.
        
        :param h: hist config
        :type h: :class:`HistCfg`
        """
        if h.hash not in self.hists: 
            self.hists[h.hash] = h 


#______________________________________________________________________________=buf=
def process_selector(scfg):
    """Configure and process LokiSelector
    
    The LokiSelector is configured via the SelectorCfg (*scfg*).
    
    This function is sent to worker threads by the :class:`Processor`.    
    
    :param scfg: selector configuration
    :type scfg: :class:`SelectorCfg`
    
    """
    # configure 
    nevents = scfg.nevents
    if not nevents: 
        if ROOT.gROOT.GetVersion() < '6.00': nevents = 1000000000  
        else:                                nevents = ROOT.TTree.kMaxEntries     

    # get input
    fin = ROOT.TFile.Open(scfg.fin)
    if not fin: 
        return
    ch = fin.Get(scfg.tname)
    if not ch: 
        fin.Close()
        return
    
    # load cpp classes
    load_cpp_classes()
    from ROOT import LokiSelector, LokiHist1D, LokiHist2D, LokiHist3D

    # configure selector
    selector = LokiSelector(scfg.fout)
    for (hash, hcfg) in scfg.hists.items():
        h = None
        if hcfg.zexpr and hcfg.yexpr and hcfg.xexpr:
            h = LokiHist3D(hash,
                hcfg.xexpr, get_xbins_stdvec(hcfg.xbins),
                hcfg.yexpr, get_xbins_stdvec(hcfg.ybins),
                hcfg.zexpr, get_xbins_stdvec(hcfg.zbins),
                hcfg.sexpr, hcfg.wexpr)
        elif hcfg.yexpr and hcfg.xexpr: 
            h = LokiHist2D(hash, 
                hcfg.xexpr, get_xbins_stdvec(hcfg.xbins),
                hcfg.yexpr, get_xbins_stdvec(hcfg.ybins),
                hcfg.sexpr, hcfg.wexpr)
        elif hcfg.xexpr and not hcfg.zexpr: 
            h = LokiHist1D(hash, 
                hcfg.xexpr, get_xbins_stdvec(hcfg.xbins),
                hcfg.sexpr, hcfg.wexpr)
        
        if h: selector.AddHist(h)
    
    # unleash the fury
    ch.Process(selector, "", nevents)
    
    # finish up
    fin.Close()
    return scfg


#______________________________________________________________________________=buf=
def tree2arrays(tree, vars, sel=None, lenvar=None, nevents=None):
    """Return dictionary of arrays from TTree 
    
    TODO: switch to using vars rather than varstrs for args (can just 
    initialize in function)
    TODO: Clean up this function
    
    :param tree: input tree
    :type tree: ROOT.TTree
    :param varstrs: list of variable expressions 
    :type varstrs: list str
    :param selstr: selection string
    :type selstr: str
    :param nevents: maximum number of events to process
    :type nevents: int
    :rtype: dict (str, array)
    """
    # initialize
    initvars = [v for v in vars+[sel,lenvar] if v is not None]
    status = [v.tree_init(tree) for v in initvars]
    if False in status: 
        log().error("Failure initializing variables")
        return None
    # config
    selstr = sel.get_expr() if sel else "1"
    lenstr = lenvar.get_expr() if lenvar else "1"
    if not nevents: 
        if ROOT.gROOT.GetVersion() < '6.00': nevents = 1000000000  
        else:                                nevents = ROOT.TTree.kMaxEntries 
    
    # determine output array length for draw
    # Note: lenvar included like this to ensure output array length correct 
    elistselstr = f"{selstr} + (0. * {lenstr})"
    n = tree.Draw("",elistselstr,"goff",nevents)
    tree.SetEstimate(n)
    log().debug(f"Setting Array Length: {n}")
    # In principle could use EntryListArray here to save some time 
    # on the next draw, but the implementation is soo poor it leaks
    # mem like a sieve and segfaults after sucking down ~60GB
    
    # smash the draw
    varstr = ":".join([v.get_expr() for v in vars])
    tree.Draw(varstr,selstr,"candle,goff",nevents)
    
    # extract the arrays
    arrays = []
    length = tree.GetSelectedRows()
    for (i,v) in enumerate(vars): 
        result = tree.GetVal(i)
        # result = [result[a] for a in range(0, length)] # Possible alternative
        result.reshape((length,))
        log().debug(f"Stripped {v.get_name()} of size {length:d}")
        if tree.GetVar(i).IsInteger():
            # Note: previously had nan/inf checking, but after fixing 
            # other bugs it wasn't necessary. May need to bring back
            # if problems arise.
            a = array('i', [int(val) for val in result])
        else:
            a = array('f', result)
        arrays.append((v, a))
    return arrays


#______________________________________________________________________________=buf=
def array2tree(arr, name, tree):
    """Attach array to TTree
    
    :param arr: array 
    :type arr: array
    :param name: branch name
    :type name: str 
    :param tree: tree
    :type tree: ROOT.TTree
    """
    arr_type = arr.typecode
    ref = array(arr_type,[0])
    if tree.GetBranch(name):
        br = tree.GetBranch(name)
        br.SetAddress(ref)
        #log().info(f"Extending existing branch: {name}, entries: {br.GetEntries()}")
    else:
        root_type = arr_type.capitalize()
        name_with_type = f"{name}/{root_type}"
        log().debug(f"Creating branch ({name}, {ref}, {name_with_type})")
        #log().info(f"Creating branch ({name}, {ref}, {name_with_type})")
        br = tree.Branch(name,ref,name_with_type)
    for v in arr: 
        ref[0] = v
        br.Fill()
    #br.FlushBaskets()
    #log().info(f"Final branch entries: {br.GetEntries()}")

#______________________________________________________________________________=buf=
def arrays2tree(arrays, tree):
    """Attach arrays to TTree 
    
    :param arrays: dictionary of arrays (name, array)
    :type arrays: dict (str, array)
    :param tree: tree
    :type tree: ROOT.TTree
    """
    # register branches
    for (v,a) in arrays:
        array2tree(a,v.get_newbranch(),tree)

    # get number of events    
    #nev_set = set([len(a) for (v,a) in arrays])
    nev_set = set([tree.GetBranch(v.get_newbranch()).GetEntries() for (v, a) in arrays])
    if len(nev_set)!=1: 
        log().error("inconsistent array lengths in arrays2tree")
        raise VarError
    nev = [n for n in nev_set][0]
    log().debug(f"Setting tree entries: {nev:d}")
    tree.SetEntries(nev)
 
 
#______________________________________________________________________________=buf=
def arrays2dmatrix(dsig, dbkg):
    """Convert sig and bkg numpy arrays to xgb DMatrix"""
    import numpy, xgboost
    # merge invars
    invars = [v for v in dsig.dtype.names if v != "weight"]
    dmerged = numpy.concatenate([dsig[invars], dbkg[invars]])
    dmerged = dmerged.view(numpy.float32).reshape(dmerged.shape +(-1,))
    # weight
    if "weight" in dsig.dtype.names: wsig = dsig["weight"] 
    else:                            wsig = numpy.ones(len(dsig))
    if "weight" in dbkg.dtype.names: wbkg = dbkg["weight"]
    else:                            wbkg = numpy.ones(len(dbkg))                    
    weight = numpy.concatenate([wsig, wbkg])
    # label
    label = numpy.concatenate([numpy.ones(len(dsig)), numpy.zeros(len(dbkg))])
    # clean up and construct
    del dsig, dbkg, wsig, wbkg
    return xgboost.DMatrix(dmerged, label=label, weight=weight)

#______________________________________________________________________________=buf=
def samples2dmatrix(sig, bkg, invars=None):
    """Convert Sig+Bkg TreeData to xgb DMatrix"""
    dsig = sig.get_ndarray(invars)
    dbkg = bkg.get_ndarray(invars)
    return arrays2dmatrix(dsig, dbkg)

#______________________________________________________________________________=buf=
def ndarray2array(nd):
    """TODO"""
    import numpy as np
    if issubclass(nd.dtype.type, np.integer):
        if nd.dtype != np.int16:
            nd = nd.astype(np.int16)
        output = array('i')
        output.fromstring(nd.tostring())
    else:
        if nd.dtype != np.float32:
            nd = nd.astype(np.float32)
        output = array('f')
        output.fromstring(nd.tostring())
    return output
 

#______________________________________________________________________________=buf=
def hist_hash(xvar=None, yvar=None, zvar=None, sel=None, wei=None, event_frac=None):
    """Create unique hash for histogram

    Hash is based on: 
    
    * x,y,z variable expressions
    * x,y,z binning
    * selection, weight expressions
    * event fraction
    
    :param xvar: x-variable view
    :type xvar: :class:`~loki.core.var.View`
    :param yvar: y-variable view
    :type yvar: :class:`~loki.core.var.View`
    :param zvar: z-variable view
    :type zvar: :class:`~loki.core.var.View`
    :param sel: selection
    :type sel: :class:`~loki.core.var.VarBase` subclass
    :param wei: weight
    :type wei: :class:`~loki.core.var.VarBase` subclass
    :param event_frac: fraction of total events to be processed
    :type event_frac: float
    """
    
    # make the hash object
    hash_obj = hashlib.md5("".encode())

    # pump in filenames
    #for fname in s.files:
    #    hash_obj.update(fname)
    #    hash_obj.update("|")
    
    # pump vars and binning
    for var in [xvar, yvar, zvar]:
        if var:  
            hash_obj.update(var.var.get_expr().encode())
            hash_obj.update(str(var.xbins).encode())
        else: 
            hash_obj.update("None".encode())
        hash_obj.update("|".encode())
    
    # pump sel and weight
    for var in [sel, wei]:
        if var:  
            hash_obj.update(var.get_expr().encode())
        else: 
            hash_obj.update("None".encode())
        hash_obj.update("|".encode())
            
    # pump event_frac
    if not event_frac: event_frac = 1.0
    evstr = f"EvFrac{event_frac*1000.:04.0f}"
    hash_obj.update(evstr.encode())
       
    return hash_obj.hexdigest()

#______________________________________________________________________________=buf=
def file_hash(fname):
    """Create unique hash for file. 
    
    Hash based on: 
    
    * absolute file-path
    * file modification time
    
    While an md5 checksum of the full file contents could be used, it is very 
    slow, which significantly delays processing startup.  
     
    Details on the full checksum can be found here:
    
    http://stackoverflow.com/questions/3431825/generating-an-md5-checksum-of-a-file
    """
    # Full md5sum hash takes very long on ~GB files
    '''
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()
    '''
    # Try hashing mod time and path instead
    hash_md5 = hashlib.md5()
    hash_md5.update(str(os.path.getmtime(fname)).encode())
    hash_md5.update("|".encode())
    hash_md5.update(os.path.abspath(fname).encode())
    return hash_md5.hexdigest()
    
 
#______________________________________________________________________________=buf=
def load_cpp_classes():
    """Loads LokiHist1D/2D/3D and LokiSelector c++ classes"""
    for path in [os.path.join(get_project_path(),"src", "LokiHist.C" ),
                 os.path.join(get_project_path(),"src", "LokiSelector.C" )]:                 
        ROOT.gROOT.ProcessLine(f".L {path}+")
        #ROOT.gROOT.LoadMacro(f"{path}")


#__________________________________________________________________________=buf=
def get_xbins_stdvec(xbins):
    """Return xbins in std::vector format"""
    vec = ROOT.vector(float)()
    for v in xbins: vec.push_back(v)
    return vec

 
## EOF
