# encoding: utf-8
"""
loki.utils.mv.py
~~~~~~~~~~~~~~~~

Command line interface for *loki mv*, providing tools to create/configure, train, 
evaluate and predict output values of MV algorithms.

"""
__author__    = "Will Davey"
__email__     = "will.davey@cern.ch"
__created__   = "2016-08-30"
__copyright__ = "Copyright 2016 Will Davey"
__license__   = "GPL http://www.gnu.org/licenses/gpl.html"



## modules
from .helpers import loki_setup
from loki.core.logger import log
import os

# - - - - - - - - - - - - - - - function defs - - - - - - - - - - - - - - - - #
#______________________________________________________________________________=buf=
def subparser_mv(subparsers):
    """Subparser for *loki mv*"""
    parser_mv = subparsers.add_parser("mv", help="mv algorithm config/train/predict/eval", 
        description="Create, configure, train, predict and evaluate multivariate algorithms")
    subparsers_mv = parser_mv.add_subparsers(help="loki mv sub-command")
    
    ## loki mv new
    ##------------
    parser_new = subparsers_mv.add_parser("new", help="create template alg workspace", 
        description="Create template multivariate algorithm workspace")
    parser_new.add_argument( "wspath", help="Workspace path (must end in '.alg')" )
    group = parser_new.add_mutually_exclusive_group(required=True) 
    group.add_argument( "-c", "--class", dest="algclass", metavar="CLASS", help="Algorithm class (AlgBase sub-class)" )
    group.add_argument( "-t", "--template", dest="template", metavar="ALG", help="Template workspace (.alg) or config (.json)" )
    parser_new.set_defaults(command=command_new)


    ## loki mv train
    ##--------------
    parser_train = subparsers_mv.add_parser("train", help="train algorithm", 
        description="Train multivariate algorithm")    
    parser_train.add_argument( "wspath", nargs='+', help="Workspace path (must end in '.alg')" )
    parser_train.add_argument( "-f", "--force", dest="retrain", action="store_true", 
        help="Force retrain previously trained algs" )
    parser_train.add_argument( "--pbs", dest="pbs", nargs='?', const="medium", metavar="QUEUE", 
        help="Submit to pbs QUEUE (default queue: medium)" )
    parser_train.set_defaults(command=command_train)

    ## loki mv grid
    ##-------------
    parser_grid = subparsers_mv.add_parser("grid", help="spawn grid", 
        description="spawn alg grid from template alg")
    parser_grid.add_argument( "wspath", help="Template workspace path (must end in '.alg')" )
    parser_grid.add_argument( "-a", "--attr", metavar="ATTR", default="algopts", 
        help="Grid attribute name (default: algopts)" )
    parser_grid.add_argument( "-d", "--dir", metavar="DIR", help="Directory to place grid points" )
    parser_grid.set_defaults(command=command_grid)


    ## loki mv cat
    ##------------
    parser_cat = subparsers_mv.add_parser("cat", help="print alg summary", 
        description="Print summary of multivariate algorithm") 
    parser_cat.add_argument( "wspath", help="Workspace path (must end in '.alg')" )
    parser_cat.set_defaults(command=command_cat)


#______________________________________________________________________________=buf=
def command_new(args):
    """Subcommand for *loki mv new*"""
    import os
    # config
    wspath = args.wspath
    name = os.path.basename(wspath)[:-4]

    # register algs
    from loki.train import algs
    
    # from template
    if args.template: 
        from loki.train.alg import load
        temp = load(args.template)
        if not temp:
            log().error("Failed to load alg template {}".format(args.template)) 
            exit(1)
        alg = temp.clone(name=name)
    # from class
    else:         
        # find alg
        algclass = args.algclass
        from loki.train.alg import AlgBase
        from loki.core.helpers import get_all_subclasses    
        all_subclasses = get_all_subclasses(AlgBase)
        matches = [cls for cls in all_subclasses if cls.__name__ == algclass]
        if not matches: 
            log().error("Subclass {} of AlgBase not found!".format(algclass))
            exit(1)
        Alg = matches[0]
        if not Alg:
            log().error("Something went wrong creating MVAlgBase subclass") 
            exit(1)
    
        # build Alg
        alg = Alg(name=name)        

    if not alg.saveas(wspath): exit(1)


#______________________________________________________________________________=buf=
def command_train(args):
    """Subcommand for *loki mv train*"""
    loki_setup()
    # import algs to register AlgBase subclasses
    from loki.train import algs 
    from loki.train.alg import load
    algs = []
    for wspath in args.wspath:
        tmp_algs = load(wspath)
        if not isinstance(tmp_algs,list): tmp_algs = [tmp_algs]
        algs+=tmp_algs
    if not algs: 
        log().error("No input algs found")
        exit(1)
    if args.pbs:
        from loki.train.alg import train_pbs
        mod = args.import_module
        if mod and os.path.exists(mod):
            mod = os.path.abspath(args.import_module)
        if not train_pbs(algs, queue=args.pbs, retrain=args.retrain,
                         import_module=mod):
            log().error("Failure submitting jobs to pbs queue")
            exit(1)
    else: 
        from loki.train.alg import train_local
        if not train_local(algs, retrain=args.retrain): 
            log().error("Failure processing algs")
            exit(1)

#______________________________________________________________________________=buf=
def command_grid(args):
    """Subcommand for *loki mv grid*"""
    from loki.train import algs
    from loki.train.alg import load
    alg = load(args.wspath)
    if not alg: 
        log().error("Failed to open {}".format(args.name))
        exit(1)
    from loki.train.alg import spawn_grid
    spawn_grid(alg, args.attr, dirname=args.dir)


#______________________________________________________________________________=buf=
def command_cat(args):
    """Subcommand for *loki mv cat*"""
    from loki.train import algs 
    from loki.train.alg import load
    alg = load(args.wspath)
    if not alg: 
        log().error("Failed to open {}".format(args.name))
        exit(1)
    alg.print_config()
    

## EOF
