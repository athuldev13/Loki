# encoding: utf-8
"""
loki.train.ntup.py
~~~~~~~~~~~~~~~~~~

Utils for creating, manipulating and decorating flat ntuples.

"""
__author__    = "Will Davey"
__email__     = "will.davey@cern.ch"
__created__   = "2016-08-31"
__copyright__ = "Copyright 2016 Will Davey"
__license__   = "GPL http://www.gnu.org/licenses/gpl.html"



## modules
import os
import shutil
import tempfile
from array import array
from ROOT import TFile, TTree
#from loki.core.helpers import ProgressBar
from loki.core.logger import log
from loki.core.process import tree2arrays, array2tree, arrays2tree
from loki.core.sample import Sample
from loki.core.var import Weights, StaticExpr
#from loki.train.alg import AlgWorkspace
#from loki.train.tree import TreeData


# - - - - - - - - - - - - - - - function defs - - - - - - - - - - - - - - - - #
#______________________________________________________________________________=buf=
def flatten_ntup(sample, invars, sel=None, fout=None, useweight=False):
    """Convert mutlti-MxAOD sample into single flat ntuple
    
    Flattened ntuples are used in the mva training module as they are easier 
    to manipulate and interface with other libraries. 
    
    The input *sample* may be comprised of many (nested) sub-samples, which 
    are themselves eventually comprised of MxAODs. 
    
    The set of variables to write to the ntuple (*invars*) must be specified.
    A selection (*sel*) can also be applied in the ntuple production. 
    An additional "weight" variable will be written to the tree. If *useweight*
    is set to True, the weight will be the product of the event weight for 
    each subsample and its cross-section scale factor, otherwise it will be 
    1 for each event.  
    
    Note: the set of variables (including the weights and selection) cannot contain 
    variables from more than one _multivalued_ container (TauJets is a multivalued 
    container since there can be more than one tau per event, while EventInfo is a 
    single valued container). There is simply no logical way to perform the 
    flattening in that case.     

    Note: now includes sequential output writing

    :param sample: input sample
    :type sample: :class:`~loki.core.sample.Sample`
    :param invars: variables to write out
    :type invars: list :class:`~loki.core.var.VarBase`
    :param sel: selection
    :type sel: :class:`~loki.core.var.VarBase`
    :param fout: name of output ntuple
    :type fout: str
    :param useweight: use sample weight and xsec scale
    :type useweight: bool
    """
    log().info("Running ntuple flattener")
    subsamples = sample.get_final_daughters()

    # ensure maximum of 1 multivalued containers used and find first valid 
    # variable to calculate it's length (lenvar)
    lenvar = None
    mvconts = []
    for v in invars: mvconts += v.get_mvinconts()
    mvconts = list(set(mvconts))
    if len(mvconts) >= 2: 
        log().error("Found multiple multi-valued containers in flatten_ntup()")
        raise ValueError
    elif len(mvconts) == 1:
        lenvar = [v for v in invars if v.is_multivalued()][0]
        log().info(f"Using lenvar: {lenvar.get_name()}")
    else: 
        log().info("Found no multi-valued containers in flatten_ntup()")

    # open output file for continuous write
    log().info("Creating output tree...")
    f = TFile.Open(fout,"RECREATE")
    tout = TTree(sample.treename,"Flat MxAOD")

    # extract arrays for each sub-sample and write to *tout*
    for s in subsamples:
        if not s.files: 
            log().warn(f"Sample {s.name} has not input files, skipping...")
            continue
        log().info(f"Processing sample {s.name}")

        for fname in s.files:
            log().info(f"--> Processing file: {os.path.basename(fname)}")

            # get input tree
            t = s.get_tree(fname)

            # define tempvars
            tempvars = list(invars)
            eventweight_active = False
            if useweight and s.weight:
                tempvars.append(Weights("weight",[s.weight],temp=True))
                eventweight_active = True
            # define sel
            if s.sel: tempsel = s.sel & sel
            else:     tempsel = sel

            # extract arrays
            arrays = tree2arrays(t,tempvars,sel=tempsel,lenvar=lenvar)

            # add dummy weight if needed
            if not eventweight_active:
                arr = array('f',[1.] * len(arrays[0][1]))
                var = StaticExpr("weight","1",temp=True)
                arrays.append((var, arr))

            # correct event weight array for sample scale
            if s.scaler and useweight:
                arr = [a for (v,a) in arrays if v.get_name() == "weight"][0]
                for (i,v) in enumerate(arr):
                    arr[i] = v * s.get_scale()

            # write output to tree
            arrays2tree(arrays, tout)
            f.cd()
            #tout.FlushBaskets()
            tout.AutoSave("Overwrite")

    # write output
    log().info("Finished processing input datasets")
    log().info(f"Output tree written to {fout}")
    f.Close()


#______________________________________________________________________________=buf=
def skim_ntup(fin=None, fout=None, sel=None):
    """Apply skimming selection to a flattened ntup
    
    :param fin: filename of input ntuple
    :type fin: str
    :param fout: filename of output ntuple
    :type fout: str
    :param sel: selection
    :type sel: :class:`~loki.core.var.VarBase`
    """
    log().info("Running ntuple skimmer")
    
    # open input file
    log().info(f"Input file: {fin}")
    if not os.path.exists(fin): 
        log.error(f"Input file not found {fin}")
        return False
    f = TFile.Open(fin)
    if not f: 
        log().error(f"Failed to open input file {fin}")
        return False
    
    # get input tree
    tname = "CollectionTree"
    tree = f.Get(tname)
    if not tree:
        log().error(f"tree {tname} not found in input file {fin}")
        f.Close()
        return False
           
    # get selection string    
    selstr = ""
    if sel: 
        status = sel.tree_init(tree)
        if not status: 
            log().error("Failed to initialize selection, aborting!")
            exit(1)
        selstr = sel.get_expr()
    
    # skim tree
    log().info("Output file: {0}".format(fout))
    log().info( "Old tree entries: {0:d}".format(tree.GetEntries()))
    log().info("Applying selection: {0}".format(selstr))
    fout = TFile.Open(fout,"RECREATE")
    newtree = tree.CopyTree(selstr)
    log().info( "New tree entries: {0:d}".format(newtree.GetEntries()))
    fout.WriteTObject(newtree, newtree.GetName(), "Overwrite")
    fout.Close()
    f.Close()


#______________________________________________________________________________=buf=
def split_ntup(fin=None, fout1=None, fout2=None, cut1=None):
    """Split flat ntuple (*fin*) into two independent sub-samples (*fout1*, *fout2*)
    
    The expression to select events for *fout1* can be specified (*cut1*).
    The complementary events are written to *fout2*. By default even numbered 
    entries go to *fout1* while odd entries go to *fout2*. It is also possible 
    to use event properties (eg. EventInfo.EventNumber) for the selection. 
    
    The main forseen use is to create training and testing samples. 
    
    :param fin: filename of input ntuple
    :type fin: str
    :param fout1: filename of first output ntuple
    :type fout1: str
    :param fout2: filename of second output ntuple
    :type fout2: str    
    :param cut1:  selection for first output (default "Entry$ % 2 == 0")
    :type cut1: :class:`~loki.core.var.VarBase`
    """
    log().info("Running ntuple splitter")
    
    # default
    cut1 = cut1 or "Entry$ % 2 == 0"
    if not fout1: fout1 = fin.replace(".root","_train.root")
    if not fout2: fout2 = fin.replace(".root","_test.root")
    
    log().info(f"Splitting {fin} into {fout1} : {fout2} with expr '{cut1}'")
    # config
    cut2 = f"!({cut1})"
    tname = "CollectionTree"
    # read in
    f = TFile.Open(fin)
    t = f.Get(tname)
    # tree 1
    f1 = TFile.Open(fout1,"RECREATE")
    t1 = t.CopyTree(cut1)
    f1.WriteTObject(t1,t1.GetName(),"Overwrite")
    f1.Close()
    log().info(f"{fout1} written!")
    # tree 2
    f2 = TFile.Open(fout2,"RECREATE")
    t2 = t.CopyTree(cut2)
    f2.WriteTObject(t2,t2.GetName(),"Overwrite")
    f2.Close()
    log().info(f"{fout2} written!")


#______________________________________________________________________________=buf=
def decorate_ntup(fin=None, alg=None, overwrite=False, **kw):
    """Decorate mv algorithm output onto flat ntuple

    :param fin: filename of input ntuple
    :type fin: str
    :param alg: algorithm
    :type alg: :class:`~loki.train.alg.AlgBase` subclass    
    :param overwrite: force overwrite if deco var already exists in input
    :type overwrite: bool
    :param kw: key word args passed to the alg predict function
    """
    log().info("Running ntuple decorator")
    log().info(f"Ntup  : {fin}")        
    if not fin or not os.path.exists(fin): 
        log().error(f"Input file {fin} does not exist")
        return False
    
    # configure
    s = Sample(files=[fin])
    brname  = alg.get_var_name(**kw) 
    log().info(f"Deco  : {brname}")

    # check for overwrite
    if s.has_varname(brname): 
        if overwrite:
            log().info(f"Overwriting var: {brname}")
        else: 
            log().error(f"Will not overwrite existing var {brname} (use 'overwrite' option)")
            return False

    # predict alg values on input dataset
    log().info("Predicting algorithm output")    
    brarray = alg.predict(s, **kw)
    if brarray is None:
        log().error("Failure predicting algorithm output, aborting") 
        return False
    
    # write out new tree
    log().info("Decorating output to file")
    ## TODO: put in root_numpy based deco with check for lib

    # decorate on temp copy of ntup
    f = TFile.Open(fin)
    t = f.Get("CollectionTree")
    temp_path = os.path.join(tempfile.mkdtemp(prefix='loki_'), 
                             next(tempfile._get_candidate_names()))
    fnew = TFile.Open(temp_path,"RECREATE")
    #if s.has_varname(brname): t.SetBranchStatus(brname, 0)# THIS BREAKS TREE WRITE!
    if t.GetBranch(brname): t.SetBranchStatus(brname, 0)
    tnew = t.CopyTree("") # should we use t.CloneTree()?
    array2tree(brarray, brname, tnew)
    fnew.WriteTObject(tnew,tnew.GetName(),"Overwrite")
    fnew.Close()
    f.Close()

    # replace existing file
    os.remove(fin)
    shutil.move(temp_path, fin)
    
    return True


## EOF
