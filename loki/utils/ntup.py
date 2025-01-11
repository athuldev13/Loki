# encoding: utf-8
"""
loki.utils.ntup.py
~~~~~~~~~~~~~~~~~~

Command line interface for *loki ntup*, which provides production and 
manipulation of flat training ntuples.

"""
__author__    = "Will Davey"
__email__     = "will.davey@cern.ch"
__created__   = "2016-08-29"
__copyright__ = "Copyright 2016 Will Davey"
__license__   = "GPL http://www.gnu.org/licenses/gpl.html"



## modules
from loki.core.logger import log
from .helpers import loki_setup, get_sel, start_timer, stop_timer

# - - - - - - - - - - - - - - - function defs - - - - - - - - - - - - - - - - #
#______________________________________________________________________________=buf=
def subparser_ntup(subparsers):
    """Subparser for *loki ntup*"""
    parser_ntup = subparsers.add_parser("ntup", help="ntuple manipulation", 
        description="Ntuple manipulation (for flat training ntuples)")
    subparsers_ntup = parser_ntup.add_subparsers(help="loki ntup sub-command")
    
    ## loki ntup flat
    ##---------------
    parser_flat = subparsers_ntup.add_parser("flat", help="ntuple flattener", 
        description="Convert MxAODs to flat training ntuples")
    parser_flat.add_argument( "-d", "--dir", dest="dir", required=True,
        metavar="DIR", help="input dataset DIR name (where you CALLED rucio get)" )
    parser_flat.add_argument( "-o", "--output", dest="output", default = "ntup.root",
        metavar="OUTPUT", help="OUTPUT ROOT file name (default: ntup.root)" )
    parser_flat.add_argument( "-s", "--sample", dest="sample", default="DYtautau",
        metavar="SAMPLE", help="Specify the SAMPLE name (default: DYtautau)" )
    parser_flat.add_argument( "--vars", dest="vars", metavar="VARS", 
        help="comma-separated list of input VARiableS" )
    parser_flat.add_argument( "--fvars", dest="fvars", metavar="FILE", 
        help="text FILE containing input variables (one per line)" )    
    parser_flat.add_argument( "--sel", dest="sel", metavar="SEL", 
        help="Comma-separated list of SELection (eg. 'TauJets.baseline1P'" )
    parser_flat.add_argument( "--useweight", dest="useweight", action="store_true", 
        help="Toggle sub-sample weights and xsec scaling" )    
    #parser_flat.add_argument( "-c", "--config", dest="config", 
    #    metavar="CONFIG", help="path to python CONFIG script to override defaults" )         
    parser_flat.add_argument( "-v", "--verbose", dest="verbose", action="store_true", 
        help="Toggle verbose output" )
    parser_flat.add_argument( "--notruth", dest="notruth", action="store_true", 
        help="Don't use truth (eg. for Dijets samples)" )    
    parser_flat.set_defaults(command=command_flat)

    ## loki ntup skim
    ##---------------
    parser_skim = subparsers_ntup.add_parser("skim", help="ntuple skimmer", 
        description="Skim ntuple")
    parser_skim.add_argument( "file", metavar="FILE", help="input FILE path" )
    parser_skim.add_argument( "-o", "--output", dest="output", default = "skim.root",
        metavar="OUTPUT", help="OUTPUT ROOT file name (default: skim.root)" )
    parser_skim.add_argument( "--sel", dest="sel", metavar="SEL", 
        help="Comma-separated list of SELection (eg. 'TauJets.baseline1P'" )
    parser_skim.add_argument( "-v", "--verbose", dest="verbose", action="store_true", 
        help="Toggle verbose output" )
    parser_skim.set_defaults(command=command_skim)

    ## loki ntup split
    ##----------------
    parser_split = subparsers_ntup.add_parser("split", help="ntuple splitter", 
        description="Split ntuple into two subsamples (eg. train and test)")
    parser_split.add_argument( "file", metavar="FILE", help="input FILE path" )
    parser_split.add_argument( "--fout1", dest="fout1", metavar="OUTFILE1", 
        help="First (training) output path (default: <FILE>_train.root)" )
    parser_split.add_argument( "--fout2", dest="fout2", metavar="OUTFILE2", 
        help="Second (testing) output path (default: <FILE>_test.root)" )
    parser_split.add_argument( "-e", "--expr", dest="expr", metavar="EXPR", 
        help="EXPRession to select events for OUTFILE1 (default: 'Entry$ %% 2 == 0', ie every second entry)" )
    parser_split.add_argument( "-v", "--verbose", dest="verbose", action="store_true", 
        help="Toggle verbose output" )
    parser_split.set_defaults(command=command_split)

    ## loki ntup weight
    ##-----------------
    parser_weight = subparsers_ntup.add_parser("weight", help="ntuple weighter", 
        description="Weight ntuple")
    parser_weight.add_argument( "fname_tar", metavar="TARGET",    help="input TARGET file path" )
    parser_weight.add_argument( "fname_ref", metavar="REFERENCE", help="input REFERENCE file path" )
    #parser_weight.add_argument( "-o", "--output", dest="output", 
    #    metavar="OUTPUT", help="OUTPUT ROOT file name (default: overwrite TARGET)" )
    parser_weight.add_argument( "--var", dest="var", metavar="VAR:VIEW",
        help="Variable for reweighting. View can be specified after a colon. (default: 'TauJets.ptGeV:weight')" )
    #parser_weight.add_argument( "-n", "--name", dest="name", metavar="NAME",
    #    help="NAME of the new weight variable (default: 'weight')" )
    parser_weight.add_argument( "-v", "--verbose", dest="verbose", action="store_true", 
        help="Toggle verbose output" )
    parser_weight.set_defaults(command=command_weight)


    ## loki ntup deco
    ##---------------
    parser_deco = subparsers_ntup.add_parser("deco", help="ntuple mv alg decorator", description="Decorate ntuple with mv alg outputs")
    parser_deco.add_argument( "fin", metavar="NTUP", help="input NTUP path" )
    parser_deco.add_argument( "wspath", metavar="WORKSPACE", help="mv alg WORKSPACE path" )        
    parser_deco.add_argument( "-a", "--args", dest="args", metavar="ARGS", 
        help="comma-separated list of ARGS passed to the alg predict function (format 'ARG1=VAL1,ARG2=VAL2')" )    
    parser_deco.add_argument( "-f", "--force", dest="overwrite", action="store_true", 
        help="Force overwrite of existing variable" )    
    parser_deco.add_argument( "-v", "--verbose", dest="verbose", action="store_true", 
        help="Toggle verbose output" )
    parser_deco.set_defaults(command=command_deco)


#____________________________________________________________
def command_flat(args):
    """Subcommand for *loki ntup flat*"""
    
    loki_setup(args.verbose)
    ti = start_timer()
    
    # configure sample
    from loki.common import samples     
    if not hasattr(samples,args.sample):
        log().error(f"invalid sample {args.sample}")
        exit(1)
    SAMPLE = getattr(samples,args.sample)

    # default variables
    from loki.common import vars, cuts
    taus = cuts.taus
    INVARS = [ taus.numTrack,
               taus.decayMode,
               taus.pt,
               taus.eta,
               taus.mu,
               taus.nVtx,
               taus.isTauFlags,
               ]
    INVARS += [v.var for v in vars.tidvars]
    if not args.notruth: 
        INVARS += [ taus.numProngTruth,
                    taus.decayModeTruth,
                    taus.ptTruth,
                    taus.etaTruth,
                    ]
        
    # selected variables
    from helpers import get_vars        
    if args.vars:     
        INVARS = get_vars(args.vars)
    elif args.fvars: 
        INVARS = get_vars(args.fvars, isfile=True)    
    
    # configured selection
    if args.sel:
        SEL = get_sel(args.sel)
    # default selection            
    else:       
        SEL = taus.baseline & taus.mode1P3PWithTruth
        if args.notruth:
            SEL = taus.baselineNoTruth & taus.mode1P3PNoTruth
    
    '''
    # config override
    if args.config: 
        import imp
        import os
        configpath = args.config
        log().info("Processing config: {0}".format(configpath))
        mod_name,file_ext = os.path.splitext(os.path.split(configpath)[-1])
        if file_ext.lower() != ".py": 
            log().error("CONFIG file ({0}) must have .py extension".format(configpath))
            exit(1)
        py_mod = imp.load_source(mod_name, configpath)
        if hasattr(py_mod, "SAMPLE"): 
            SAMPLE = getattr(py_mod, "SAMPLE")
            log().info("Loaded SAMPLE {0}".format(SAMPLE.name))
        if hasattr(py_mod, "INVARS"): 
            INVARS = getattr(py_mod, "INVARS")
            log().info("Loaded INVARS")
        if hasattr(py_mod, "SEL"): 
            INVARS = getattr(py_mod, "SEL")
            log().info("Loaded SEL")    
    '''

    log().info("Got input vars: ")
    for v in INVARS: 
        log().info("    {0}".format(v.get_newbranch()))
    
    # load sample input files
    from loki.core.file import FileHandler
    FileHandler(args.dir,[SAMPLE])                  
    
    # run writer
    from loki.train.ntup import flatten_ntup
    flatten_ntup(SAMPLE, INVARS, sel=SEL, fout=args.output, useweight=args.useweight)
    
    log().info("Finished dominating!")
    stop_timer(ti)

#____________________________________________________________
def command_skim(args):
    """Subcommand for *loki ntup skim*"""
    
    loki_setup(args.verbose)
    ti = start_timer()
    
    from loki.train.ntup import skim_ntup
    from loki.common import cuts
    sel = get_sel(args.sel)
    skim_ntup(fin = args.file,
              fout = args.output, 
              sel = sel,
               )
    log().info("Finished dominating!")
    stop_timer(ti)


#____________________________________________________________
def command_split(args):
    """Subcommand for *loki ntup split*"""
    
    loki_setup(args.verbose)
    ti = start_timer()
    
    from loki.train.ntup import split_ntup
    split_ntup(fin = args.file,
               fout1 = args.fout1,
               fout2 = args.fout2,
               cut1 = args.expr,
               )
    
    log().info("Finished dominating!")
    stop_timer(ti)
    

#____________________________________________________________
def command_weight(args):
    """Subcommand for *loki ntup weight*    
    """
    loki_setup(args.verbose)
    ti = start_timer()
        
    # config
    from loki.core.sample import Sample
    from loki.common import vars
    tar = Sample("tar", weight=vars.weight, files=[args.fname_tar])
    ref = Sample("ref", weight=vars.weight, files=[args.fname_ref])
    prodvar = vars.weight
    name = "weight"
    var = args.var
    
    # init alg
    from loki.train import algs
    alg = algs.Reweighter(name=name, var=var, prodvar=prodvar, tar=tar, ref=ref)
    
    # decorate
    from loki.train.ntup import decorate_ntup
    if not decorate_ntup(fin=args.fname_tar, alg=alg, overwrite=True): 
        log().error("Failed to decorate weight")
        exit(1)
    
    log().info("Finished dominating!")
    stop_timer(ti)
    

#____________________________________________________________
def command_deco(args):
    """Subcommand for *loki ntup deco*"""
    loki_setup(args.verbose)
    ti = start_timer()

    # register AlgBase subclasses
    from loki.train import algs
    from loki.train.alg import load
    alg = load(args.wspath)
    if not alg: 
        log().error("Coulnd't load {}, failed to decorate".format(args.wspath))
        exit(1)

    # get predict args
    if args.args:
        from helpers import get_args
        predargs = get_args(args.args)
    else: predargs = dict()
    
    # decorate
    from loki.train.ntup import decorate_ntup    
    if not decorate_ntup(args.fin, alg, args.overwrite, **predargs):
        log().error("Failed to decorate")
        exit(1)
    stop_timer(ti)


## EOF
