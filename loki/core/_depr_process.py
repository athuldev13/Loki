# encoding: utf-8
"""
loki.core._depr_process
~~~~~~~~~~~~~~~~~~~~~~~

This module has been DEPRECATED (replaced by loki.core.process)

It contains the old TTree::Draw based Processor class.

"""
__author__    = "Will Davey"
__email__     = "will.davey@cern.ch"
__created__   = "2012-11-04"
__copyright__ = "Copyright 2012 Will Davey"
__license__   = "GPL http://www.gnu.org/licenses/gpl.html"



## modules
import logging
import time
from multiprocessing import Pool, cpu_count 
import ROOT
from loki.core.helpers import ProgressBar
from loki.core.histutils import new_hist
from loki.core.logger import log
from loki.core.plot import Plot
from loki.core.var import VarError, default_cut, default_weight


# - - - - - - - - - - - class defs  - - - - - - - - - - - - #
                
#------------------------------------------------------------
class Processor():
    """Class to process :class:`RootDrawable` objects

    Component histograms for the :class:`RootDrawable` objects 
    are filled using the TTree::Draw functionality. 
    Higher-level drawable objects are constructed from the 
    component histograms. 
    If *fout* specified, histograms will be written to file

    The number of cores (*ncores*) to use when processing plots 
    can be specified. If not specified, all available cores 
    will be used. You can also provide a negative number, 
    in which case all but `|n|` cores are used. 

    :param event_frac: event fraction to process
    :type event_frac: float
    :param ncores: number of cores to use
    :type ncores: bool
    :param noweight: Disable sample weighting
    :type noweight: bool
    
    """
    #____________________________________________________________
    def __init__(self,
                 event_frac=None,
                 ncores=None,
                 noweight=False,
                 ):
        # config
        self.event_frac = event_frac
        self.ncores = ncores
        self.noweight = noweight

        # members
        self.hists = []
        self.drawables = []
        self.processed_drawables = []
        self.jobs = {}

    #____________________________________________________________
    def register(self,drawables):
        """Register :class:`RootDrawable` or :class:`loki.core.plot.Plot` 
        
        :param drawables: single or list of ROOT drawables or plots (collection of drawables)
        :param drawables: single or list of :class:`RootDrawable` derivative or :class:`loki.core.plot.Plot`
        """
        if not isinstance(drawables, list):
            drawables = [drawables]
        self.drawables += drawables
        #self.hists+=drawable.get_component_hists()

    #____________________________________________________________
    def process(self,drawables=None):
        """Construct all registered objects
        
        If *drawables* provided, they will be registered prior to processing
        
        :param drawables: single or list of ROOT drawables or plots (collection of drawables)
        :param drawables: single or list of :class:`RootDrawable` derivative or :class:`loki.core.plot.Plot`
        """
        if drawables is not None: 
            self.register(drawables)
        self.__process__()
        
    #____________________________________________________________
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
        

    #____________________________________________________________
    def write(self,f):
        """Write all processed drawables to file 
        
        :param f: output file
        :type f: :class:`ROOT.TFile`
        """
        for rd in self.processed_drawables:
            rd.write(f)
        
    #____________________________________________________________
    def __process__(self):
        """Process all registered drawable objects
        
        Workflow: 
        
            - A list of component histograms is generated. 
            - A HistJob is spawned for every input file in each component hist. 
            - Jobs are launched (in either single-core or multi-core mode). 
            - Output from the HistJobs for each component hist are merged.
            - Finally the higher level objects in the RootDrawables are built
              (eg. efficiency graphs).
              
        TODO: currently rethinking workflow. Better to split jobs across files
        to minimize IO strain. Also planning to build a 'make' like build 
        architecture to auto-congigure build dependencies.
        """
        log().info("Preparing to process hists...")

        # determine number of cores
        if not self.ncores: 
            ncores = cpu_count()
        elif self.ncores < 0: 
            ncores = max(1, cpu_count() + self.ncores)
        else: 
            ncores = min(self.ncores, cpu_count())

        # get hists from drawables
        log().debug("Getting hists from drawables...")
        hist_job_id_map = []
        for d in self.drawables:
            for h in d.get_component_hists():
                hist_job_id_map.append([h,[]])
        
        # spawn HistJobs
        log().debug("Spawning HistJobs...")
        for (h,job_ids) in hist_job_id_map: 
            final_daughters = h.sample.get_final_daughters()
            log().debug(f"In hist {h.name}")
            for d in final_daughters:                    
                if d.files is None: continue
                for f in d.files:
                    log().debug(f"Job for file {f}")
                    job = self.__create_job__(f, h, d)
                    job_ids.append(job.jid)

        # group jobs
        alljobs = [j for j in self.jobs.values() if not j.is_processed()]
                
        # map jobs to filenames and treenames
        log().debug("Mapping jobs to input files...")
        hist_job_file_map = {}
        for j in alljobs: 
            if j.fname not in hist_job_file_map: hist_job_file_map[j.fname] = {}
            d = hist_job_file_map[j.fname]
            tname = j.sample.treename
            if tname not in d: d[tname] = []
            d = d[tname]
            d.append(j)
        
        # initialize HistJobs
        log().debug("Initializing jobs...")
        status = True   
        for (fname, d1) in hist_job_file_map.items():
            # open file and check
            f = ROOT.TFile.Open(fname)
            if not f: 
                log().error(f"Failed to open {fname}")
                status = False
                continue
            
            for (tname, d2) in d1.items():
                # get tree and check
                t = f.Get(tname)
                if not t: 
                    log().error(f"Couldn't find tree {tname} in file {fname}")
                    status = False
                    continue
                
                # initialize jobs
                for j in d2: 
                    status = status and j.initialize(t)
                    
            f.Close()
            
        if not status:
            log().error("Failure in initialization")
            raise VarError
        
        # process         
        ti = time.time()
        if ncores>1: 
            alljobs = self.__process_multicore__(alljobs, ncores)
        else: 
            alljobs = self.__process_singlecore__(alljobs)  
            
        tf = time.time()
        dt = tf-ti
        log().info(f"Hist processing time: {dt:.1f} s")
       
        # update job_dict links with links in 'alljobs'
        # (they were copied in the process command)
        for j in alljobs:
            self.jobs[j.jid] = j

        # post process (scale, normalize etc...)
        self.__post_process__(alljobs)

        # merge hists
        for (h, job_ids) in hist_job_id_map:
            rootobj = h.new_hist()
            for jid in job_ids:
                subobj = self.jobs[jid].rootobj()
                rootobj.Add(subobj)
                subobj.Delete()
            h.set_rootobj(rootobj)
        
        # build drawables
        for o in self.drawables: 
            o.build_rootobj()
            
        # accounting
        self.processed_drawables += self.drawables
        self.drawables = []
   
    #____________________________________________________________
    def __process_singlecore__(self,jobs):
        """Single core processor"""
        # print job stats
        njobs = len(jobs)
        nfiles = len(set([j.fname for j in jobs]))
        nev = sum([j.nevents for j in jobs])
        log().info("")
        log().info("Processing hists in singlecore :-(")
        log().info(f"Total jobs:   {njobs}")
        log().info(f"Total files:  {nfiles}")
        log().info(f"Total events: {nev}")
      
        # build progress bar
        prog = None 
        if log().level >= logging.INFO: 
            prog = ProgressBar(ntotal=nev,text="Processing hists")
            
        # process jobs     
        nevproc = 0
        for job in jobs: 
            job.execute()
            nevproc+=job.nevents
            if prog: prog.update(nevproc)
        if prog: prog.finalize()
        
        return jobs

    #____________________________________________________________
    def __process_multicore__(self,jobs, ncores):
        """Multi core processor"""
        # print job stats
        njobs = len(jobs)
        nfiles = len(set([j.fname for j in jobs]))
        nev = sum([j.nevents for j in jobs])
        log().info("")
        log().info("Processing hists in multicore :-)")
        log().info(f"Lighting up {ncores} cores!!!")
        log().info(f"Total jobs:   {njobs}")
        log().info(f"Total files:  {nfiles}")
        log().info(f"Total events: {nev}")
        
        # build progress bar
        prog = None
        if log().level >= logging.INFO: 
            prog = ProgressBar(ntotal=nev,text="Processing hists") 
        nproc=0
        
        # create pool and unleash the fury
        pool = Pool(processes=ncores)
        results = [pool.apply_async(process_job,(j,)) for j in jobs]
        #results = [pool.map_async(process_job,[j]) for j in jobs]
        completed = []          
        while results: 
            for r in results: 
                if r.ready():
                    j = r.get()
                    completed.append(j)
                    results.remove(r)
                    nproc+=j.nevents
            time.sleep(0.05)
            if prog: prog.update(nproc)
        if prog: prog.finalize()
        return completed

    #____________________________________________________________
    def __post_process__(self,jobs):
        """Post-process"""
        for j in jobs: 
            h = j._rootobj
            if j.scale: 
                log().debug(f"scaling hist {h.GetName()}: {j.scale}")
                h.Scale(j.scale)
                
    #____________________________________________________________
    def __create_job__(self,fname,hist,sample):
        """Create job with unique job id
        
        :param fname: file name 
        :type fname: str
        :param hist: histogram
        :type hist: :class:`Hist`
        :param sample: sample
        :type sample: :class:`loki.core.sample.Sample`
        """
        # unique job id
        jid = len(self.jobs)
                    
        # create job
        job = HistJob(jid,hist,sample,fname,self.event_frac,self.noweight)
        
        # enter in job dict
        self.jobs[jid] = job
        return job


#------------------------------------------------------------
class HistJob():
    """Internal class used by :class:`Processor` to draw histograms
    
    An individual job is used for each input file. The histograms
    are then merged to create the rootobj for objects of type :class:`Hist`.  
    
    The attributes passed in the constructor are used to initialize 
    a new set of attributes of standard python types needed to 
    retain the information when it is serialized to a worker thread. 
    Hence only the post-initialization attributes should be used 
    in the execute function. 
        
    :param jid: unique job id
    :type jid: int
    :param hist: histogram definition
    :type hist: :class:`loki.core.hist.Hist`
    :param sample: input sample
    :type sample: :class:`loki.core.sample.Sample`    
    :param fname: file name
    :type fname: str
    :param event_frac: fraction of events to process
    :type event_frac: float
    :param noweight: apply weighting
    :type noweight: bool
    """
    #____________________________________________________________
    def __init__(self, jid, hist, sample, fname, event_frac=None, noweight=None):
        # attributes
        self.jid = jid
        self.hist = hist
        self.sample = sample 
        self.fname = fname
        self.event_frac = event_frac
        self.noweight = noweight       
        
        # attributes to be initialized
        self.initialized = False
        self.tname = None
        self.varstr = None
        self.weightstr = None
        self.optstr = None
        self.nevents = None
        self.scale = None
        self.histargs = None
               
        # members
        self._rootobj = None
        self._processed = False

    #____________________________________________________________
    def initialize(self, tree = None):
        """Initialize the HistJob
        
        Initializes a set of standard python type attributes 
        that can be streamed to the worker thread.        
        """
        log().debug(f"initializing job {self.jid}: {self.fname}")
        
        # scale (doesn't rely on local tree)                       
        if not self.noweight and self.sample.scaler: 
            self.scale = self.sample.get_scale()
            if self.event_frac: self.scale/=self.event_frac            

        # hist definition
        hname = f"h_{self.__hash__()}"
        self.histargs = self.hist.histargs(hname)

        # get tree 
        self.tname = self.sample.treename
        f = None
        if not tree:
            log().debug(f"Opening file: {self.fname}")
            f = ROOT.TFile.Open(self.fname)
            tree = f.Get(self.tname)        
        
        # nevents 
        n = self.sample.get_nevents(self.fname,tree)
        if self.event_frac: n = int(self.event_frac*float(n))
        #if self.sample.maxevents: n = min(n, self.sample.maxevents)
        self.nevents = n
             
        # init draw strings
        if not self.__init_varstr__(tree): 
            return False
        if not self.__init_weightstr__(tree): 
            return False
        if not self.__init_optstr__(tree):
            return False
        
        if f: f.Close()
        
        self.hist = None
        self.sample = None
        self.initialized = True
        return True

    #____________________________________________________________
    def rootobj(self):
        """Returns ROOT histogram

        :rtype: :class:`ROOT.TH1` or :class:`ROOT.TH2`
        """
        return self._rootobj 

    #____________________________________________________________
    def __hash__(self):
        """Returns unique job id as hash"""
        return self.jid

    #____________________________________________________________
    def __eq__(self,other):
        """Returns comparison using hash"""
        return self.__hash__() == other.__hash__()

    #____________________________________________________________
    def __init_varstr__(self,tree):
        """Initializes the variable string for TTree::Draw"""
        # variables 
        xvar = self.hist.xvar.var
        yvar = self.hist.yvar.var if self.hist.yvar else None
        zvar = self.hist.zvar.var if self.hist.zvar else None
        
        # initialize variables
        status = [v.tree_init(tree) for v in [xvar,yvar,zvar] if v is not None]
        if False in status: return False
        
        # return expression            
        if self.hist.zvar is not None:  
            varstr = f"{zvar.get_expr()}:{yvar.get_expr()}:{xvar.get_expr()}"
        elif self.hist.yvar is not None:  
            varstr = f"{yvar.get_expr()}:{xvar.get_expr()}"
        else:
            varstr = xvar.get_expr()
        self.varstr = varstr
        return True

    #____________________________________________________________
    def __init_weightstr__(self,tree):
        """Initializes the weighting string for TTree::Draw"""
        # selection
        sel = default_cut()
        if self.hist.sel: sel = sel & self.hist.sel
        if self.sample.sel: sel = sel & self.sample.sel

        # weight
        weight = default_weight()
        if not self.noweight: 
            if self.hist.weight: weight = weight * self.hist.weight
            if self.sample.weight: weight = weight * self.sample.weight

        # combine selection and weight
        comb = sel * weight
        if not comb.tree_init(tree): 
            return False 
        self.weightstr = comb.get_expr() 
        return True

    #____________________________________________________________
    def __init_optstr__(self,tree):
        """Initializes the option string for TTree::Draw
        
        TODO: does this need to be udpated to use the hist.optstr? or getter? 
        """      
        if self.hist.yvar and not self.hist.zvar: 
            optstr = "COL"
        else:    
            optstr = "" 
        self.optstr = optstr
        return True

    #____________________________________________________________
    def __build_hist__(self):
        """Build hist with unique name h_<JobID> for job""" 
        h = new_hist(*self.histargs)
        log().debug(f"Created {h.GetName()}")
        return h

    '''
    #____________________________________________________________
    def __init_vars__(self,tree):
        """Initialize variables for tree. Return True if success.
        
        TODO: deprecate?         
        """
        # add active x, y, z variables
        inviews = [self.hist.xvar, self.hist.yvar, self.hist.zvar]
        invars = [v.var for v in inviews if v is not None]
        # add selection variables
        #if self.hist.sel is not None: invars.append(self.hist.sel)
        # initialize
        status = [v.tree_init(tree) for v in invars]
        return False not in status
    '''
    
    #____________________________________________________________
    def execute(self):
        """Execute histogram job"""
        # load inputs
        f = ROOT.TFile.Open(self.fname)
        f.cd()
        tree = f.Get(self.tname)

        ## build hist
        h = self.__build_hist__()
        
        # So TTree::Project actually _projects_ to histogram (thanks ROOT). Why
        # couldn't the API just use a f*@&ing pointer like any normal softare,
        # rather than a name string. 
        h.SetDirectory(f)

        # project onto histogram
        log().debug(f"TTree::Project(): {h.GetName()}, {self.varstr}, {self.weightstr}, {self.optstr}")
        tree.Project(h.GetName(), self.varstr, self.weightstr, self.optstr, self.nevents)
        h.SetDirectory(0)
        self._rootobj = h

        # finalize
        f.Close()
        self._processed = True
        
    #____________________________________________________________
    def is_processed(self):
        """Returns True if already processed"""
        return self._processed
        


#____________________________________________________________
def process_job(j):
    j.execute()
    return j

 
## EOF
