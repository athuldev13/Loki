# encoding: utf-8
"""
loki.utils.mvaplot.py
~~~~~~~~~~~~~~~~~~~~~

Subparser and subcommand for *loki mvaplot*. 

"""
__author__    = "Will Davey"
__email__     = "will.davey@cern.ch"
__created__   = "2016-09-01"
__copyright__ = "Copyright 2016 Will Davey"
__license__   = "GPL http://www.gnu.org/licenses/gpl.html"



## modules
from .helpers import loki_setup, get_sel, get_wei, read_args_str, start_timer, stop_timer
from loki.core.logger import log


# - - - - - - - - - - - - - - - function defs - - - - - - - - - - - - - - - - #
#______________________________________________________________________________=buf=
def subparser_mvaplot(subparsers):
    """Subparser for *loki mvaplot*"""
    parser = subparsers.add_parser("mvaplot", help="make mva comparison plots", description="Make MVA comparison plots")
    parser.add_argument( "fname_sig", metavar="SIG", help="input SIG file path" )
    parser.add_argument( "fname_bkg", metavar="BKG", help="input BKG file path" )
    parser.add_argument( "--wsig", dest="wsig", metavar="WEIGHT",
        help="comma-separated list of WEIGHTs for signal (default: 'weight')" )
    parser.add_argument( "--wbkg", dest="wbkg", metavar="WEIGHT", 
        help="comma-separated list of WEIGHTs for background (default: 'weight')" )    
    parser.add_argument( "--sel", dest="sel", metavar="SEL", 
        help="comma-separated list of SELection (eg. 'TauJets.baseline1P'" )
    parser.add_argument( "-o", "--output", dest="output", default = "canvases.root",
        metavar="OUTPUT", help="OUTPUT ROOT file name (default: canvases.root)" )
    parser.add_argument( "--vars", dest="vars", metavar="VAR1,VAR2...", 
                         help="comma-separated list of mva output variables to compare" )        
    parser.add_argument( "--noweight", dest="noweight", action="store_true", default = False,
        help="Turn off sample weighting" )     
    parser.add_argument( "-n", "--ncores", dest="ncores", type=int, 
        help="Number of processing cores. If negative use all but |n| cores. (default: use all available cores)" )
    parser.add_argument( "-v", "--verbose", dest="verbose", action="store_true", 
        help="Toggle verbose output" )
    parser.set_defaults(command=command_mvaplot)
     

#____________________________________________________________
def command_mvaplot(args):
    """Subcommand for *loki plot*"""

    loki_setup(args.verbose)
    ti = start_timer()
    
    # Configure samples
    # -----------------
    from loki.common import vars, cuts, styles
    from loki.core.sample import Sample
    fname_sig = args.fname_sig
    fname_bkg = args.fname_bkg
    wei_sig = vars.weight
    wei_bkg = vars.weight
    if args.wsig: wei_sig = get_wei(args.wsig)
    if args.wbkg: wei_bkg = get_wei(args.wbkg)    
    sel = get_sel(args.sel) 
    sig = Sample(name="Signal",     files=[fname_sig], weight=wei_sig, sel=sel, sty=styles.Signal)
    bkg = Sample(name="Background", files=[fname_bkg], weight=wei_bkg, sel=sel, sty=styles.Background)

    # Configure vars
    # --------------
    from loki.core.var import StaticExpr, default_cut, find_container, find_variable
    """
    # binning for grad-boost bdts
    gradbdt_bins = [50, -1., 1.]
    gradbdt_bins_fine = [1000, -1., 1.]
    # binning for ada-boost bdts
    adabdt_bins = [50, 0., 1.]
    adabdt_bins_fine = [1000, 0., 1.]
    """
    # open tree to determine ada/grad range
    from ROOT import TFile
    fsig = TFile.Open(fname_sig)
    tsig = fsig.Get("CollectionTree")
    fbkg = TFile.Open(fname_bkg)
    tbkg = fbkg.Get("CollectionTree")
    # parse varnames
    var_names = read_args_str(args.vars)
    mvavars = []
    from loki.core.process import tree2arrays
    from array import array
    for name in var_names:
        # existing variable
        v = find_variable(name)
        # create new variable
        if not v: 
            # container variable
            if name.count('.'): 
                (cname,vname) = name.split('.')
                cont = find_container(cname)
                if not cont: 
                    log().warn("Failure retrieving container {0}".format(cname))
                    v = StaticExpr(name)
                else: 
                    v = cont.add_var(vname)
            # global variable
            else: 
                v = StaticExpr(name)

        ## old method (assume range either [0,1], or [-1,1])
        """
        if t.Draw("1","%s<0"%(name),"goff", 50000):
            v.add_view(*gradbdt_bins, name="mvacoarse")
            v.add_view(*gradbdt_bins_fine, name="mvafine")
        else: 
            v.add_view(*adabdt_bins, name="mvacoarse")
            v.add_view(*adabdt_bins_fine, name="mvafine")
        """
        ## new method, dynamic range adaption
        # quantiles cl and 1-cl
        cl = 0.01
        # get mva values from signal and background tree and sort
        vals = tree2arrays(tsig,[v])[0][1] + tree2arrays(tbkg,[v])[0][1]
        vals = array('f', sorted(vals))
        # grab values at quantiles
        nevents = len(vals)
        cl_i = int(nevents * cl)
        x1 = vals[cl_i]
        x2 = vals[nevents - cl_i]
        # add a little room each side
        w = x2 - x1
        x1 -= 0.1 * w
        x2 += 0.1 * w
        # make coarse and fine binning (for dist and roc curve) 
        v.add_view(50, x1, x2, name="mvacoarse")
        v.add_view(1000, x1, x2, name="mvafine")
        
        mvavars.append(v) 
    mvaviews = [v.get_view("mvacoarse") for v in mvavars]
    mvaviews_fine = [v.get_view("mvafine") for v in mvavars]
    fsig.Close()
    fbkg.Close()
    
    # Configure plots
    # ---------------
    from loki.tauid.plots import create_roc_comparisons, create_tid_variable_dists    
    plots = []
    plots += create_roc_comparisons(sig,bkg,mvaviews_fine)
    plots += create_tid_variable_dists([sig,bkg], tidvars=mvaviews, sel=default_cut())

    # Process
    # -------    
    from loki.core.process import Processor
    p = Processor(ncores=args.ncores, noweight=args.noweight)    
    p.process(plots)
    p.draw_plots()
    
    ## write outputs to ROOT ntuple
    if args.output:
        from loki.core.file import OutputFileStream
        log().info(f"Writing canvases to {args.output}")
        ofstream = OutputFileStream(args.output)
        ofstream.write(plots)
   
    log().info("Finished dominating!")
    stop_timer(ti)


## EOF
