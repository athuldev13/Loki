# encoding: utf-8
"""
loki.utils.quickplot.py
~~~~~~~~~~~~~~~~~~~~~~~

Subparser and subcommand for *loki qp*. 

"""
__author__    = "Will Davey"
__email__     = "will.davey@cern.ch"
__created__   = "2016-03-29"
__copyright__ = "Copyright 2016 Will Davey"
__license__   = "GPL http://www.gnu.org/licenses/gpl.html"



## modules
from .helpers import loki_setup
from loki.core.logger import log

# - - - - - - - - - - - - - - - function defs - - - - - - - - - - - - - - - - #
#______________________________________________________________________________=buf=
def subparser_quickplot(subparsers):
    """Subparser for *loki qp*"""
    parser = subparsers.add_parser("qp", description="Make quick plot",
        help="make quick plot" )
    parser.add_argument( dest="var", metavar="VAR:VIEW",
        help="Variable to plot. View can be specified after a colon VAR:VIEW, or as tuple VAR:NBINS;XMIN;XMAX." )
    parser.add_argument( "samples", nargs='+', metavar="SAMPLE",
        help="list of filenames (flat ntups) or sample names (when combined with -d flag)" )
    parser.add_argument( "-d", "--dir", dest="dir", metavar="DIR",
        help="input dataset DIR name (where you CALLED rucio get)" )
    parser.add_argument( "--sel", dest="sel", metavar="SEL",
        help="Comma-separated list of SELection (eg. 'TauJets.baseline1P')" )
    parser.add_argument( "-e", "--eff", dest="eff", metavar="DISC",
        help="Make efficiency plot of boolean DISCriminant" )
    parser.add_argument( "--norm", action="store_true",
        help="Normalize histograms to unit area" )
    parser.add_argument( "--logy", action="store_true",
        help="Set log scale on y-axis" )
    parser.add_argument( "--noweight", dest="noweight", action="store_true", default = False,
        help="Turn off sample weighting" )
    # parser.add_argument( "-n", "--ncores", dest="ncores", type=int,
    #     help="Number of processing cores. If negative use all but |n| cores. (default: use all available cores)" )
    parser.add_argument( "-v", "--verbose", dest="verbose", action="store_true",
        help="Toggle verbose output" )

    parser.set_defaults(command=command_quickplot)
     

#____________________________________________________________
def command_quickplot(args):
    """Subcommand for *loki plot*"""
    
    # setup loki framework
    loki_setup(args.verbose)

    # config sel
    if args.sel: 
        from loki.common import cuts
        from helpers import get_sel
        sel = get_sel(args.sel)
    else: sel = None

    # config var
    from loki.core.var import get_view
    from loki.common import vars
    view = get_view(args.var)
    if not view: 
        log().error("View {} not found!".format(args.var))
        exit(1)
    
    # config disc
    if args.eff:
        from loki.common import cuts
        from helpers import get_vars
        disc = get_vars(args.eff)[0]
        if not disc: 
            log().error("Var {} not found!".format(args.eff))
            exit(1)

    # config file name
    if ";" in args.var or view.name == "default":
        viewname = args.var.split(":")[0]
    else:
        viewname = view.get_name()
    if args.eff:
        fname_base = "{}_vs_{}".format(disc.get_name(), viewname)
    else:
        fname_base = viewname

    # configure samples
    samples = []
    if args.dir:
        from loki.common import samples as common_samples
        for s in args.samples: 
            if not hasattr(common_samples, s): 
                log().error(f"ERROR - invalid sample {args.signal}")
                exit(1)
            samples.append(getattr(common_samples, s))

        from loki.core.file import FileHandler            
        FileHandler(args.dir,samples)        
    else: 
        from loki.core.sample import Sample
        from loki.common import vars, styles
        import os
        for i, s in enumerate(args.samples):
            s = s.strip()
            spathbase = os.path.splitext(s)[0]
            sname = os.path.basename(spathbase)
            sty = styles.style_list[i]
            sty.name = sname
            sty.tlatex = sname
            samples += [Sample(name=sname, files=[s], weight=vars.weight, sty=sty)]

    # define plot 
    rds = []
    from loki.core.plot import Plot
    if args.eff:
        from loki.core.hist import EffProfile
        for s in samples:
            rds += [EffProfile(sample=s, xvar=view, sel_total=sel, sel_pass=disc&sel)]                    
    else:
        from loki.core.hist import Hist 
        for s in samples: 
            rds += [Hist(sample=s, xvar=view, sel=sel, normalize=args.norm)]
    p = Plot(name=fname_base, rds=rds, logy=args.logy)

    # process plots
    from loki.core.process import Processor
    proc = Processor(ncores=1, noweight=args.noweight)
    proc.draw_plots([p])
    
    ## write outputs to ROOT ntuple
    from loki.core.file import OutputFileStream
    fname = fname_base + ".root"
    log().info(f"Writing canvases to {fname}")
    ofstream = OutputFileStream(fname)
    ofstream.write([p])
    log().info("Finished dominating!")


## EOF
