# encoding: utf-8
"""
loki.utils.main.py
~~~~~~~~~~~~~~~~~~

Main function for loki executable. The loki command collects 
a set of subcommands (similar to svn: ls, co, ci, etc). 
A subparser is defined for each subcommand. The command 
function itself (*args.command*) is also specified in the parser 
definition (ie. each command has a separate implementation). 
The following subcommands are currently available:

* plot: make standard performance plots
* quickplot: make quick single plots
* ntup: manipulation of flat training ntuples
* mv: mv algorithms
* mvaplot: mva comparison plots
* wpplot: working point comparison plots
* pdfbook: make pdf plotbooks
* webbook: make web plotbooks
* dev: development tools (new, log, list-tags, tag, rel)  

Deprecated: 

* tune: extract flat efficiency working points
* train: mva training
* grid: mva grid scans

The subcommands and corresponding subparsers should be defined 
in an appropriate module within :mod:`loki.utils`. 

"""
__author__    = "Will Davey"
__email__     = "will.davey@cern.ch"
__created__   = "2016-03-30"
__copyright__ = "Copyright 2016 Will Davey"
__license__   = "GPL http://www.gnu.org/licenses/gpl.html"



## modules
from argparse import ArgumentParser
from .dev import subparser_dev
from .plot import subparser_plot
from .quickplot import subparser_quickplot
from .latex import subparser_pdfbook
from .root2html import subparser_webbook
from .ntup import subparser_ntup
from .mvaplot import subparser_mvaplot
from .wpplot import subparser_wpplot
from .mv import subparser_mv
from .helpers import import_module
from loki import __version__ as version

#______________________________________________________________________________=buf=
def main():
    """Loki main function"""

    description = "Loki commandline interface"
    parser = ArgumentParser(description=description)
    parser.add_argument( "-i", "--import", dest="import_module", metavar="MODULE", 
        help="import python MODULE prior to executing util" )         
    parser.add_argument( "--version", action="version", version=version)

    # add subparsers
    subparsers = parser.add_subparsers(help="loki sub-command")
    subparser_plot(subparsers)
    subparser_quickplot(subparsers)
    subparser_ntup(subparsers)
    subparser_mv(subparsers)
    subparser_mvaplot(subparsers)
    subparser_wpplot(subparsers)
    subparser_pdfbook(subparsers)
    subparser_webbook(subparsers)
    subparser_dev(subparsers)
    
    # parser args
    args = parser.parse_args()

    # custom module import
    if args.import_module:
        if not import_module(args.import_module):
            print(f"WARNING - Failed to import module {args.import_module}")

    # execute subcommand
    args.command(args) 
    exit(0)
    

## EOF
