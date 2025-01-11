# encoding: utf-8
"""
loki.core.sample
~~~~~~~~~~~~~~~~

This module provides a class to store details of an event sample

"""
__author__    = "Will Davey"
__email__     = "will.davey@cern.ch"
__created__   = "2012-10-25"
__copyright__ = "Copyright 2012 Will Davey"
__license__   = "GPL http://www.gnu.org/licenses/gpl.html"


## modules
from glob import glob
import ROOT
from loki.core.logger import log
from loki.core.style import Style


# - - - - - - - - - - - class defs  - - - - - - - - - - - - #
#------------------------------------------------------------
class Sample():
    """Class to store details of event samples 

    :param name: simple text identifier for sample
    :type name: str
    :param sty: sample plotting sty attributes 
    :type sty: :class:`loki.core.sty.Style` 
    :param xsec: cross section
    :type xsec: float
    :param is_data: collision data sample (ie not MC) 
    :type is_data: bool 
    :param daughters: sub-samples 
    :type daughters: `loki.core.sample.Sample` list
    :param regex: regular expression for sample directory
    :type regex: str 
    :param files: list of paths to input MxAOD files
    :type files: str list
    :param treename: name of the TTree in the input MxAOD files
    :type treename: str    
    :param sel: selection always applied to sample
    :type sel: :class:`loki.core.var.VarBase`
    :param weight: weight expression
    :type weight: :class:`loki.core.var.VarBase`
    :param scaler: sample scaler
    :type scaler: :class:`loki.core.hist.HistScaler`
    :param mcevents: nominal number of mcevents
    :type mcevents: int
    """
    #____________________________________________________________
    def __init__(self, 
                 name = None,
                 sty = None,
                 xsec = None,
                 is_data = False,
                 daughters = None,
                 regex = None,
                 files = None,
                 treename = None,
                 sel = None,
                 weight = None,
                 scaler = None,
                 mcevents = None,
                 #maxevents = None,
                 ):
        self.name = name
        self.sty = sty or Style(name) 
        self.xsec = xsec
        # TODO may be redundant - remove if not used soon, Feb 2016
        self.is_data = is_data
        self.daughters = []
        if daughters:
            for d in daughters: self.add_daughter(d)
        self.regex = regex or f"*{name}*"
        self.files = files
        self.treename = treename or "CollectionTree"
        self.sel = sel
        self.weight = weight
        self.scaler = scaler
        self.mcevents = mcevents or 1000000
        #self.maxevents = maxevents

        #: handle on parent (if daughter) 
        self.parent = None
        #self.__curr_file = None
        #: nevents cache
        self.nev_per_file_dict = {}
        
    #____________________________________________________________
    def style_hist(self,h):
        """Apply *self.sty* to *h*"""
        if self.sty: self.sty.apply(h)

    #____________________________________________________________
    def is_parent(self):
        """Check if sample has daughters"""
        return bool(self.daughters) 

    #____________________________________________________________
    def is_mvdataset(self):
        """Check if sample is appropraite for mv trainig"""
        return len(self.files) == 1 and not self.is_parent()  

    #____________________________________________________________
    def add_daughter(self,sample):
        """Add a daughter to this sample
       
        :param sample: daughter (ie sub-sample)
        :type sample: `loki.core.sample.Sample`
        """
        if not self.daughters: self.daughters = []
        self.daughters.append(sample)
        sample.parent = self

    #____________________________________________________________
    def get_final_daughters(self):
        """Return list of non-parent daughters of this sample.

        Walks recursively through all daughters.
        Will return itself if not a parent.

        :rtype: `loki.core.sample.Sample` list
        """
        if not self.is_parent(): return [self]
        daughters = []
        for d in self.daughters: 
            daughters+=d.get_final_daughters()
        return daughters

    #____________________________________________________________
    def get_nevents(self,fname=None,tree=None):
        """Get number of events for sample or per file (*fname*)
        
        Result is cached.
        
        Need to distinguish before or after MxAOD filter.
        
        :param fname: filename
        :type fname: str
        """
        if fname is None: 
            return sum([self.get_nevents(f) for f in self.files])
            
        if fname not in self.nev_per_file_dict:
            log().debug(f"Calculating nevents for {fname}")
            if tree:
                n = tree.GetEntries()
            else:  
                f = ROOT.TFile.Open(fname)
                t = f.Get(self.treename)
                n = t.GetEntries()
                f.Close()                 
            self.nev_per_file_dict[fname]=n
        else:
            log().debug(f"Using cached nevents for {fname}")
        return self.nev_per_file_dict[fname]

    #____________________________________________________________
    def get_tree(self,fname=None):
        """Get tree per file (*fname*)"""
        ## NOTE: Abandoned TChain because of poor support for PyROOT
        '''
        ch = ROOT.TChain(self.treename)
        ch.SetMakeClass(1) # To prevent segfault on MxAODs since Root 6.08
        if fname:
            ch.Add(fname)
        else: 
            for f in self.files: ch.Add(f)
        return ch
        '''
        if not fname:
            if not self.files:
                log().warn("Sample has no input files, cannot return tree!")
                return None
            if len(self.files)>1:
                log().warn("Called get_tree on multi-file sample. Only using first file.")
            fname = self.files[0]
        #if self.__curr_file and self.__curr_file.GetName() == fname:
        #    f = self.__curr_file
        #else:
        f = ROOT.TFile.Open(fname)
        if not f:
            log().warn(f"Failed to open file: {fname}")
            return None
        t = f.Get(self.treename)
        if not t:
            log().warn(f"Failed to get tree: {self.treename} from file: {fname}")
            f.Close()
            return None
        t._file = f
        #self.__curr_file = f
        return t

    #__________________________________________________________________________=buf=
    def get_arrays(self, invars=None, noweight=False):
        """Return data as standard python arrays
 
        If *invars* specified, only those branches will be included. 
        TODO: this is not true, would need to transfer get_invar_items method from TreeData
                 
        If *self.wei* defined, will be added as "weight" column.

        Uses :func:`loki.core.process.tree2arrays`
        
        :param invars: subset of variables to include
        :type invars: list str
        :rtype: :class:`numpy.ndarray`
        """
        if not invars: return None
        if self.weight is not None and not noweight:
            invar_names = [v.get_name() for v in invars]
            # avoid double weight entry, and put at back  
            if "weight" in invar_names:
                invars.append(invars.pop(invar_names.index("weight")))
            else: 
                invars += [self.weight]
        
        # unleash
        log().info(f"Stripping vars from {self.files}")
        from loki.core.process import tree2arrays
        return tree2arrays(self.get_tree(), invars, sel=self.sel) 
        
    #__________________________________________________________________________=buf=
    def get_ndarray(self, invars=None, noweight=False):
        """Return data as numpy ndarray

        If *invars* specified, only those branches will be included. 
        TODO: this is not true, would need to transfer get_invar_items method from TreeData
                 
        If *self.wei* defined, will be added as "weight" column.

        Uses root_numpy.tree2array.
        
        :param invars: subset of variables to include
        :type invars: list str
        :rtype: :class:`numpy.ndarray`
        """
        if not invars: return None
        if self.weight is not None and not noweight:
            invar_names = [v.get_name() for v in invars]
            # avoid double weight entry, and put at back  
            if "weight" in invar_names:
                invars.append(invars.pop(invar_names.index("weight")))
            else: 
                invars += [self.weight]
        t = self.get_tree()
        for v in invars: v.tree_init(t)        
        invar_exprs = [v.get_expr() for v in invars]
        if self.sel: 
            self.sel.tree_init(t)
            sel_expr = self.sel.get_expr()
        else:
            sel_expr = None  
        
        # unleash
        from root_numpy import tree2array
        log().info(f"Stripping vars from {self.files}")
        d = tree2array(t, branches=invar_exprs, selection=sel_expr)
        # rename weight branch
        if self.weight is not None and not noweight: 
            d.dtype.names =  list(d.dtype.names[:-1]) + ["weight"]
        return d

    #____________________________________________________________
    def get_scale(self):
        if not self.scaler: 
            log().warn(f"Attempt to get scale of sample {self.name} that has no scaler")
            return None
        return self.scaler.scale(self)

    #____________________________________________________________
    def get_all_files(self):
        """Returns a list of paths to all input MxAOD files 
        including daughters. 
        
        Walks recursively through all daughters. 

        :rtype: str list
        """
        files = []
        if self.is_parent():
            for d in self.daughters: 
                files += d.get_all_files()
        elif self.files: files += self.files
        return files

    #____________________________________________________________
    def is_active(self):
        """Retruns true if sample has input files"""
        return bool(self.get_all_files()) 

    #____________________________________________________________
    def load_files(self,basedir=None):
        """Load files in *basedir* matching :attr:`regex`

        Walks recursively through all daughters.

        :param basedir: directoy to scan for files
        :type basedir: str 
        """
        if self.is_parent(): 
            for d in self.daughters: d.load_files(basedir)
        else: 
            # check if regex defined
            regex   = self.regex
            if not regex: 
                log().warn(f"No regex defined for {self.name}, cannot scan for input files")
                return
            
            # scan for files
            basedir = basedir or "."
            self.files = glob(f"{basedir}/{regex}/*.root*")
            if not self.files: 
                log().warn(f"No files found for sample {self.name}")

    #__________________________________________________________________________=buf=
    def has_varname(self, varname):
        """Return true if *var* exists in dataset
        
        :param varname: variable name
        :type varname: str
        :rtype: bool
        """
        t = self.get_tree()
        if not t: return False
        return bool(t.GetLeaf(varname))

    #____________________________________________________________
    def clone(self,tag,regexmod=None):
        """Return a clone of the dataset named "<name>_<tag>". 
        
        The cross section, selection, weights, sample scaler and 
        is_data flag from the original sample are retained. 
        The style, files and treename are not set, as they are 
        expected to be different and/or determined later.
        
        The regex for input file scanning can be updated (see below). 
        
        The final daughters will also be cloned with the same *tag* 
        and *regexmod* arguments. 
        
        The logic for updating the regex can be provided by the string *regexmod*.
        It can contain the following keywords, which will be replaced by their
        existing values:: 
        
            {regex} - the current regex of the sample
            {name}  - the current name of the sample
            {tag}   - the new tag
        
        For example, if you want the new regex to match the old regex
        preceeded by the new tag and allowing for additional charachters inbetween, 
        you would do this:: 
            
            regex = "*{tag}*{regex}*"
            

        :param basedir: directoy to scan for files
        :type basedir: str 
        """
        # new name
        name = f"{self.name}_{tag}"
        
        # new regex
        regex = None
        if regexmod is not None: 
            regkw = {}
            if regexmod.count("{regex}"): regkw["regex"] = self.regex
            if regexmod.count("{name}"): regkw["name"] = self.name
            if regexmod.count("{tag}"): regkw["tag"] = tag
            regex = regexmod.format(**regkw)        
            regex = regex.replace("**","*")
            
        # new sample 
        snew = Sample(name=name,
                      regex=regex,
                      xsec=self.xsec,
                      is_data=self.is_data,
                      sel=self.sel,
                      weight=self.weight,
                      scaler=self.scaler,                   
                      )
        
        # clone the daughters:     
        if self.is_parent(): 
            # exact lineage doesn't matter, just use final daughters
            daughters = self.get_final_daughters()
            for d in daughters: 
                dnew = d.clone(tag,regexmod)
                snew.add_daughter(dnew)
    
        return snew

    #____________________________________________________________
    def serialize(self):
        """Return sample in dict format"""
        sel_str = self.sel.get_name() if self.sel else None
        wei_str = self.weight.get_name() if self.weight else None
        #return {"name":self.name, "files":self.files, "sel":sel_str, "weight":wei_str}

        # Warn against serialization of sample selection to simplify
        # Alg training workflow. Rather, you should apply selection by
        # skimming your flat ntuples. Also, don't write null sel_str,
        # to avoid encouraging people to use it.
        d = {"name": self.name, "files": self.files, "weight": wei_str}
        if sel_str:
            log().warn("Serialization of sample selection not recommended as it is not supported by AlgBase!")
            log().warn(f"sel_str: {sel_str}")
            d["sel"] =sel_str
        return d

    #____________________________________________________________
    def __hash__(self):
        """Define hash identifier using hash of *self.name*"""
        return self.name.__hash__()


#------------------------------------------------------------
class HistScaler():
    """Class to scale histograms to sample cross section or 
    target luminosity

    **WARNING: Not yet tested, needs to be updated to MxAOD**

    The scale factor for each sample is calculated as::
        
        w = lumi * xsec / Nevents

    where the target *lumi* is specified, *xsec* is a property 
    of the *sample* and *Nevents* is calculated from the 
    input MxAOD files (usually *sum of weights*). *Nevents* 
    for each input file is extracted from a histogram with 
    name *skim_hist_name*, stored in the bin with index 
    *skim_hist_bin*.

    Note that the scale factor is cached for each sample.

    :param lumi: target luminosity
    :type lumi: float
    :param skim_hist_name: name of nevents histogram 
    :type skim_hist_name: str
    :param skim_hist_bin: index for bin containing nevents 
    :type skim_hist_bin: int
    """
    #____________________________________________________________
    def __init__(self,lumi=None,skim_hist_name=None,skim_hist_bin=None):
        self.lumi=lumi or 1.0
        self.skim_hist_name = skim_hist_name or "CutFlow"
        self.skim_hist_bin = skim_hist_bin or 2
              
        #: sample nevents cache 
        self.nevent_dict = dict()
        #: sample scale factor cache
        self.scale_dict = dict()

    #____________________________________________________________
    def scale(self,sample,event_frac=None):
        """Return scale factor for sample (cached)

        :param sample: event sample
        :type sample: :class:`loki.core.sample.Sample`
        :rtype: float
        """
        s = self.__calc_scale__(sample)
        nevents = self.__get_nevents__(sample)
        if event_frac: 
            s /= event_frac
            log().debug(f'scaling {sample.name}, (lumi*xsec)/(nevents*frac) = {self.lumi:.1f} * {sample.xsec:.3f} / ({float(nevents):.1f} * {event_frac:.2f}) = {s:.2g}')
        else:
            log().debug(f'scaling {sample.name}, (lumi*xsec)/(nevents) = {self.lumi:.1f} * {sample.xsec:.3f} / {float(nevents):.1f} = {s:.2g}') 
        return s

    #____________________________________________________________
    def __get_nevents__(self,sample):
        """Returns Nevents for sample summed over all daughters

        **Internal function not designed to be called by users**
     
        TODO: do we even want to sum over daughters? 
        
        TODO: copy new functionality from sample
        
        :param sample:
        :type sample: :class:`loki.core.sample.Sample`
        :rtype: int 
        """
        if sample.name not in self.nevent_dict:
            log().debug("calculating nevent without cache") 
            nevents = 0
            if sample.files: 
                for fname in sample.files: 
                    f = ROOT.TFile.Open(fname)
                    if not f: 
                        log().warn(f'failed to open {fname}')
                        continue
                    skim_hist = f.Get(self.skim_hist_name)
                    if not skim_hist: 
                        log().warn(f'failed to get {self.skim_hist_name} from {fname}')
                        f.Close()
                        continue 
                    nevents += skim_hist.GetBinContent(self.skim_hist_bin)
                    f.Close()
            #if sample.maxevents: nevents = min(nevents, sample.maxevents)
            self.nevent_dict[sample.name] = nevents          
        return self.nevent_dict[sample.name]

    #____________________________________________________________
    def __calc_scale__(self,sample):
        """Internal sample scale factor calcluation"""
        if sample.name not in self.scale_dict:
            log().debug("calcuating scale without cache")
            scale = 1.0         
            if sample.xsec:
                nevents = self.__get_nevents__(sample)
                if nevents: 
                    scale = self.lumi * sample.xsec / float(nevents)
            self.scale_dict[sample.name] = scale
        return self.scale_dict[sample.name]


# - - - - - - - - - - - - - - - function defs - - - - - - - - - - - - - - - - #


## EOF
