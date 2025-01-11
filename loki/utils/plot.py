# encoding: utf-8
"""
loki.utils.plot.py
~~~~~~~~~~~~~~~~~~

Subparser and subcommand for *loki plot*. 

"""
__author__    = "Will Davey"
__email__     = "will.davey@cern.ch"
__created__   = "2016-03-29"
__copyright__ = "Copyright 2016 Will Davey"
__license__   = "GPL http://www.gnu.org/licenses/gpl.html"



## modules


# - - - - - - - - - - - - - - - function defs - - - - - - - - - - - - - - - - #
#______________________________________________________________________________=buf=
def subparser_plot(subparsers):
    """Subparser for *loki plot*"""
    parser = subparsers.add_parser("plot", help="make standard performance plots", description="Make standard performance plots")
    parser.add_argument( "-d", "--dir", dest="dir", required=True,
        metavar="DIR", help="input dataset DIR name (where you CALLED rucio get)" )
    parser.add_argument("plots", nargs="?", choices=["tid","tes","ele","pi0","pan","trk"],
                        help="performance plot categories to include")
    parser.add_argument( "-o", "--output", dest="output", default = "canvases.root",
        metavar="OUTPUT", help="OUTPUT ROOT file name (default: canvases.root)" )
    parser.add_argument( "-e", "--event-frac", dest="event_frac", type=float, 
        metavar="FRAC", help="Specify a limited FRAC of events to process" )
    parser.add_argument( "-s", "--sample", dest="signal", default="sample",
        metavar="SIGNAL", help="Specify the SIGNAL sample name (default: sample)" )
    parser.add_argument( "-b", "--bkg", dest="background", default="bkg",
        metavar="BACKGROUND", help="Specify the BACKGROUND sample name (default: bkg)" )
    parser.add_argument(       "--elebkg", dest="elebkg", default="bkg_ele",
        metavar="ELEBKG", help="Specify the electron ELEBKG sample name (default: bkg_ele)" )
    parser.add_argument(       "--sys", dest="sys",
        metavar="SYSLIST", help="Comma separated list of systematics" )    
    parser.add_argument( "-l", "--level", dest="level", type=int, default = 0,
        metavar="LEVEL", help="Set plot detail LEVEL" )                 
    parser.add_argument( "--noweight", dest="noweight", action="store_true", default = False,
        help="Turn off sample weighting" )     
    parser.add_argument( "-n", "--ncores", dest="ncores", type=int, 
        help="Number of processing cores. If negative use all but |n| cores. (default: use all available cores)" )
    parser.add_argument( "--nocache", dest="usecache", action="store_false", default=True,
        help="Switch off histogram caching" )                  
    parser.add_argument( "--usedraw", dest="usedraw", action="store_true", default=False, 
        help="Switch old TTree::Draw based Processor" )
    parser.add_argument( "--nologos", dest="nologos", action="store_true",
        help="Switch off completely awesome THOR/loki logos :'(" )
    parser.add_argument( "--inprog", dest="inprog", action="store_true",
        help="Use 'Work in Progress' stamp and remove logos" )
    parser.add_argument( "-v", "--verbose", dest="verbose", action="store_true", 
        help="Toggle verbose output" )
    parser.add_argument( "--profile", dest="profile", action="store_true",
        default = False, help="Toggle python profiler" )

    parser.set_defaults(command=command_plot)
     

#____________________________________________________________
def command_plot(args):
    """Subcommand for *loki plot*"""

    # enable profiling
    if args.profile: 
        from helpers import start_profiler
        pr = start_profiler()
    
    # setup loki framework
    import logging
    from loki.core.logger import log
    from loki.core.setup import setup
    loglevel = None
    suppresswarn = True
    suppresserr = True
    if args.verbose: 
        loglevel = logging.DEBUG
        suppresswarn = False
        suppresserr = False        
    setup(log_level = loglevel,
          suppress_root_msgs = suppresswarn,
          suppress_root_errors = suppresserr)

    # configure nominal samples
    from loki.common import samples     
    if not hasattr(samples,args.signal): 
        print(f"ERROR - invalid sample {args.signal}")
        exit(1)
    if not hasattr(samples,args.background): 
        print(f"ERROR - invalid sample {args.background}")
        exit(1)
    sample = getattr(samples,args.signal)
    bkg = getattr(samples,args.background)
    elebkg = getattr(samples,args.elebkg)
    
    # load sample input files
    from loki.core.file import FileHandler
    if not args.sys:
        # baseline samples
        FileHandler(args.dir,[sample,bkg,elebkg])                  
    else: 
        # systematic samples 
        log().info("Configuring systematics samples") 
        syssamples = []
        systematics = args.sys.split(',')
        from loki.common import styles
        for sys in systematics: 
            clone = sample.clone(sys,regexmod="*{tag}*{regex}*")
            if hasattr(styles,sys): 
                clone.sty = getattr(styles,sys)
            else: 
                log().warn("No predefined style for systematic {}".format(sys))
            syssamples.append(clone)    
    
        # load inputs
        FileHandler(args.dir,syssamples)
        
        # enforce sub-sample consistency
        log().info("Enforcing sub-sample consistency...")
        missing_samples = False
        for daughters in zip(*[s.get_final_daughters() for s in syssamples]):
            valid = True
            for d in daughters: 
                if not d.files: 
                    valid = False
                    missing_samples = True
            if not valid: 
                log().warn("Dropping incomplete set of samples associated with {}".format(daughters[0].name))        
                for d in daughters: d.files = []
        if not missing_samples: 
            log().info("Everything OK!")
    
    # define plots 
    lvl = args.level # plot detail level
    plots_tid = []
    plots_ele = []
    plots_tes = []
    plots_pan = []
    plots_trk = []
    # baseline plots
    if not args.sys: 
        if not args.plots or "tid" in args.plots: 
            from loki.tauid.plots import baseline_plots as tid_baseline_plots
            plots_tid += tid_baseline_plots(sample,bkg,lvl)
        if not args.plots or "tes" in args.plots: 
            from loki.tes.plots import baseline_plots as tes_baseline_plots
            plots_tes += tes_baseline_plots(sample,lvl)
        if not args.plots or "ele" in args.plots: 
            from loki.tauid.plots import baseline_ele_plots as ele_baseline_plots
            plots_ele += ele_baseline_plots(sample,elebkg,lvl)        
        if not args.plots or "pan" in args.plots: 
            from loki.substr.plots import baseline_plots as substr_baseline_plots
            plots_pan += substr_baseline_plots(sample,lvl)
        if not args.plots or "trk" in args.plots: 
            from loki.trk.plots import baseline_plots as trk_baseline_plots
            plots_trk += trk_baseline_plots(sample,lvl)    
    # systematics plots
    else: 
        if not args.plots or "tid" in args.plots: 
            from loki.tauid.plots import comparison_plots as tid_comparison_plots
            plots_tid += tid_comparison_plots(syssamples,lvl)
        if not args.plots or "tes" in args.plots: 
            from loki.tes.plots import comparison_plots as tes_comparison_plots
            plots_tes += tes_comparison_plots(syssamples,lvl)
        if not args.plots or "ele" in args.plots: 
            from loki.tauid.plots import comparison_ele_plots as ele_comparison_plots
            plots_ele += ele_comparison_plots(syssamples,lvl)    
        if not args.plots or "pan" in args.plots:
            # not substructure systematics plots yet 
            pass 
        if not args.plots or "trk" in args.plots: 
            from loki.trk.plots import comparison_plots as trk_comparison_plots
            plots_trk += trk_comparison_plots(syssamples,lvl)
                
    plots = plots_tid + plots_tes + plots_ele + plots_pan + plots_trk

    # switch off logos (what a travesty)
    if args.nologos or args.inprog:
        for p in plots: p.dologos = False

    # in progress stamps
    if args.inprog:
        for p in plots: p.atlas_label = "Work in Progress"

    # process
    if not args.usedraw: 
        from loki.core.process import Processor
        p = Processor(event_frac=args.event_frac,
                      ncores=args.ncores,
                      noweight=args.noweight,
                      usecache=args.usecache,
                      )   
    else: 
        from loki.core._depr_process import Processor
        p = Processor(event_frac=args.event_frac,
                      ncores=args.ncores,
                      noweight=args.noweight,
                      )    

    p.draw_plots(plots)
    
    ## write outputs to ROOT ntuple
    if args.output:
        from loki.core.file import OutputFileStream
        log().info(f"Writing canvases to {args.output}")
        ofstream = OutputFileStream(args.output)
        ofstream.write(plots_tid,"tid")
        ofstream.write(plots_tes,"tes")
        ofstream.write(plots_ele,"ele")
        ofstream.write(plots_pan,"pan")
        ofstream.write(plots_trk,"trk")
   
    log().info("Finished dominating!")

    # print profiling output
    if args.profile:
        from helpers import stop_profiler
        stop_profiler(pr)


## EOF
