# encoding: utf-8
"""
loki.utils.wpplot.py
~~~~~~~~~~~~~~~~~~~~

Subparser and subcommand for *loki wpplot*. 

"""
__author__    = "Will Davey"
__email__     = "will.davey@cern.ch"
__created__   = "2016-09-06"
__copyright__ = "Copyright 2016 Will Davey"
__license__   = "GPL http://www.gnu.org/licenses/gpl.html"



## modules
from .helpers import loki_setup, get_sel, get_wei, start_timer, stop_timer
from loki.core.logger import log


# - - - - - - - - - - - - - - - function defs - - - - - - - - - - - - - - - - #
#______________________________________________________________________________=buf=
def subparser_wpplot(subparsers):
    """Subparser for *loki wpplot*"""
    parser = subparsers.add_parser("wpplot", help="make working-point comparison plots", description="Make Working-point comparison plots")
    parser.add_argument( "fname", metavar="FILE", help="input FILE path" )
    parser.add_argument( "-w", "--weight", dest="weight", metavar="WEIGHT",
        help="comma-separated list of WEIGHTs (default: 'weight')" )
    parser.add_argument( "--sel", dest="sel", metavar="SEL", 
        help="comma-separated list of SELection (eg. 'TauJets.baseline1P'" )
    parser.add_argument( "-o", "--output", dest="output", default = "canvases.root",
        metavar="OUTPUT", help="OUTPUT ROOT file name (default: canvases.root)" )
    parser.add_argument( "--wps", dest="wps", metavar="WP1,WP2...", 
                         help="comma-separated list of working-point variables to compare" )        
    parser.add_argument( "--noweight", dest="noweight", action="store_true", default = False,
        help="Turn off sample weighting" )
    parser.add_argument( "-b", "--bkg", dest="bkg", action="store_true", default = False,
        help="Is background sample" )              
    parser.add_argument( "-n", "--ncores", dest="ncores", type=int, 
        help="Number of processing cores. If negative use all but |n| cores. (default: use all available cores)" )
    parser.add_argument( "-v", "--verbose", dest="verbose", action="store_true", 
        help="Toggle verbose output" )
    parser.set_defaults(command=command_wpplot)
     

#____________________________________________________________
def command_wpplot(args):
    """Subcommand for *loki wpplot*"""

    loki_setup(args.verbose)
    ti = start_timer()
    
    # Configure samples
    # -----------------
    from loki.common import vars, cuts, styles
    from loki.core.sample import Sample
    fname = args.fname
    wei = vars.weight
    if args.weight: wei = get_wei(args.weight)
    sel = get_sel(args.sel)
    if sel is None: sel = cuts.nocut
    sample = Sample(name="Sample", files=[fname], weight=wei, sel=sel, sty=styles.Signal)

    # Configure wps
    # -------------
    from helpers import get_vars
    from copy import deepcopy
    wps = get_vars(args.wps)
    wpdefs = []
    for (i, wp) in enumerate(wps):
        wpname = wp.get_name()
        sty = deepcopy(styles.style_list[i])
        sty.name = sty.tlatex = wpname
        wpdefs.append((wpname, {"sel_total": sel, "sel_pass": sel & wp, "sty":sty}))

    # Configure dependent variables
    # -----------------------------
    taus = vars.taus
    depvars = [taus.ptGeV.get_view(),
               taus.ptGeV.get_view("log"), 
               taus.ptGeV.get_view("low"),
               #taus.ptFinalCalibGeV.get_view(),
               #taus.ptFinalCalibGeV.get_view("log"),
               #taus.ptFinalCalibGeV.get_view("low"),               
               taus.eta.get_view(),
               taus.mu.get_view(),
               taus.nVtx.get_view(),
               ]

    # Configure plots
    # ---------------
    from loki.tauid.plots import create_eff_profiles_wrt_reco, create_eff_profiles 
    plots = []
    #plots += create_eff_profiles_wrt_reco([sample], wpdefs=wpdefs, depvars=depvars)
    plots += create_eff_profiles(sample, wpdefs=wpdefs, depvars=depvars, 
                                 wrt=False, fakes=args.bkg, tag="IDEffWRTReco")

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
