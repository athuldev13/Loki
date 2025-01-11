# encoding: utf-8
"""
loki.utils.dev.py
~~~~~~~~~~~~~~~~~

This module provides utils to aid development of the loki package.

Since the migration from SVN to GitHub, the package has become
a lot lighter, as much of the functionality is now provided by
GitHub directly.

Tags are now created using the 3rd party lib: ``bumpversion``,
which should be called from the top dir of the loki package.
``bumpversion`` operates by incrementing the specified digit
of the release string: v<major>.<minor>.<patch>. Eg.::

    bumpversion patch

will increment v0.5.1 to v0.5.2. Upon incrementing the
version number, ``bumpversion`` will commit the changes and
then create a tag. Push the tag to the main repo via::

    git push --tags upstream

When this tag is merged to the main repo, a pipeline will
be triggered that will build and deploy the loki release
to our web server.

.. warning:: you should always make sure your local branch is
             completely up-to-date before calling ``bumpversion``.
             It will complain otherwise.

In case of any future problems with the server build, it is
also possible to build and deploy a loki release manually.
Please still increment the version and make sure it is
committed, tagged and merged to the main repo. Then make
a fresh loki clone directly from the server, build and
deploy::

    git clone ssh://git@gitlab.cern.ch:7999/atlas-perf-tau/loki.git
    cd loki
    git checkout tags/vX.Y.Z
    source setup_dev.sh
    loki dev build
    loki dev deploy


The tools are provided to the commandline as subtools of *loki dev*.
The active tools are:

* new: create a new python source code template  
* build: build a loki release
* deploy: deploy a loki release

"""
__author__    = "Will Davey"
__email__     = "will.davey@cern.ch"
__created__   = "2016-03-03"
__copyright__ = "Copyright 2016 Will Davey"
__license__   = "GPL http://www.gnu.org/licenses/gpl.html"



## modules
from subprocess import Popen, check_call, PIPE
import os
from loki import __gitpath__ as defaultgit
from loki import __afspath__ as defaultafs
from loki import __server__ as defaultserver
from loki.utils.system import get_project_path
from loki import __version__ as loki_version

# - - - - - - - - - - - - - - -  class defs - - - - - - - - - - - - - - - - - #
#______________________________________________________________________________=buf=
class DevTool():
    """Class providing API for developers.
    
    Provides: 

    * API for building loki releases.
    * API for publishing webbooks

    """
    #__________________________________________________________________________=buf=
    def __init__(self, gitpath=defaultgit, afspath=defaultafs,
                 serverurl=defaultserver, project="loki"):
        self.gitpath = gitpath
        self.afspath = afspath
        self.serverurl = serverurl
        self.project = project

    #__________________________________________________________________________=buf=
    def print_cmd(self,cmd):
        """Prints a command
        
        :param cmd: list of command strings
        :type cmd: list str
        """
        print(" ".join(cmd))

    #__________________________________________________________________________=buf=
    def on_lxplus(self):
        """Returns True if currently on lxplus host"""
        return ("lxplus" in os.uname()[1])

    #__________________________________________________________________________=buf=
    def afs_webbook_dir(self):
        """Returns afs live webbook path"""
        return os.path.join(self.afspath,"data/webplots/plotbooks")

    #__________________________________________________________________________=buf=
    def server_webbook_url(self):
        """Returns webbook url on loki server"""
        return os.path.join(self.serverurl,"data/webplots/plotbooks")

    #__________________________________________________________________________=buf=
    def build_release(self):
        """Build loki release

        Builds the loki source distribtuion and accompanying html documentation
        using the script ``scripts/runner_build.sh``.

        Output is placed in ``public/``

        """
        runner_build = os.path.join(get_project_path(), "scripts", "runner_build.sh")
        print(f"Building release {loki_version}...")
        p = Popen(["sh", runner_build], stdout=PIPE, stderr=PIPE)
        output = p.communicate()[0]
        if p.returncode != 0:
            print(output)
            print("")
            print("Encountered Errors when building release")
            return False

        print("Build successful!")
        return True

    #__________________________________________________________________________=buf=
    def deploy_release(self):
        """Deploy loki release

        The previously built release, located in ``public/``, will be deployed to
        the loki server.

        The default server location is: {}

        """.format(defaultserver)

        # check for local build
        localdistpath = "public/data/dist/loki-{}.tar.gz".format(loki_version)
        localhtmlpath = "public/data/html/html-{}".format(loki_version)
        if not os.path.exists(localdistpath):
            print(f"ERROR: local distribution build not found: {localdistpath}, aborting")
            return False
        if not os.path.exists(localhtmlpath):
            print(f"ERROR: local html build not found: {localhtmlpath}, aborting")
            return False

        # deploy
        distpath = os.path.join(self.afspath, f"data/dist/loki-{loki_version}.tar.gz")
        # local
        if self.on_lxplus() and os.path.exists(self.afspath):
            if os.path.exists(distpath):
                print(f"ERROR: loki-{loki_version} already deployed, aborting!")
                return False
            else:
                print(f"Deploying release {loki_version} to {self.afspath}...")
                p = Popen(["rsync", "-arzqSHx", "public/*", f"{self.afspath}/."])
                output = p.communicate()[0]
                if p.returncode != 0:
                    print(output)
                    print("")
                    print("Encountered Errors when deploying release")
                    return False
                print("Deployment successful!")
                return True
        # remote
        else:
            print("Attempting to deploy release remotely...")
            print("Querying server...")
            p = Popen(["ssh", "lxplus.cern.ch", "stat", distpath], stdout=PIPE, stderr=PIPE)
            (out, err) = p.communicate()

            if p.returncode == 0:
                print(f"ERROR: loki-{loki_version} already deployed, aborting!")
                return False
            if not "No such file or directory" in err:
                print("stdout: ")
                print(out)
                print("")
                print("stderr: ")
                print(err)
                print("")
                print("An Error occurred when trying to access the server")
                print("If you are having troubles deploying remotely, try on lxplus")
                return False

            ## go ahead with remote deploy
            print("Deployment area ready.")
            print("Deploying release {} to lxplus.cern.ch:{}...".format(loki_version,self.afspath))
            print("This may take some time.")
            p = Popen(" ".join(["rsync", "-arzqSHxe", "ssh", "public/*",
                       "lxplus.cern.ch:{}/.".format(self.afspath)]),
                      stdout=PIPE, stderr=PIPE, shell=True)
            (out, err) = p.communicate()
            if p.returncode != 0:
                print("stdout: ")
                print(out)
                print("")
                print("stderr: ")
                print(err)
                print("")
                print("Encountered Errors when deploying release")
                return False
            print("Deployment successful!")

        return True

    #__________________________________________________________________________=buf=
    def rsync(self,source,target):
        """Rsync from *source* to *target*"""
        print(f"Rsyncing {source} to {target}")
        flags = "-arzqSHxe ssh"
        cmd = ["rsync", flags,source,target]
        p = Popen(cmd,stdout=PIPE)
        print(p.communicate()[0])
        return p.returncode == 0

    #__________________________________________________________________________=buf=
    def publish_webbook(self,source,server=None):
        """Use Rsync to copy webbook to server"""
        if not self.check_webbook(source): 
            print(f"ERROR - invalid webbook '{source}', aborting...")
            return False
        if not server: server = "lxplus:{path}/.".format(path=self.afs_webbook_dir())
        return self.rsync(source,server)

    #__________________________________________________________________________=buf=
    def check_webbook(self,source):
        """Returns True if webbook passes checks"""
        if not os.path.exists(source):
            print(f"Webbook path '{source}' doesn't exist")
            return False 
        if not os.path.isdir(source):
            print(f"Webbook '{source}' is not directory")
            return False    
        index = os.path.join(source,"index.html")
        if not os.path.exists(index):
            print(f"Webbook missing {index}")
            return False
        return True


#______________________________________________________________________________=buf=
def subparser_dev(subparsers):
    """Subparser for *loki dev*"""
    parser_dev = subparsers.add_parser("dev", help="development tools", 
        description="Loki development tools")
    subparsers_dev = parser_dev.add_subparsers(help="loki dev sub-command")

    ## loki dev new
    ##-------------
    parser_new = subparsers_dev.add_parser("new", 
        help="create a new python source code template", 
        description="Creates new python source code templates")
    parser_new.add_argument('file', metavar='FILE', nargs=1,
        help='name of the new python file')
    parser_new.add_argument('-m','--mode',dest="mode",
        choices=['exec','mod','script'],default='mod',
        help='create new python EXECutable, MODule or SCRIPT (default: mod)')
    parser_new.add_argument('-e','--exec', action="store_const", 
        const="exec", dest="mode",
        help='wrapper for "-m exec"')
    parser_new.add_argument('-s','--script', action="store_const", 
        const="script", dest="mode",
        help='wrapper for "-m script"')
    parser_new.add_argument('--mod',action="store_const", const="mod", dest="mode",
        help='wrapper for "-m mod"')
    parser_new.set_defaults(command=command_new)


    ## loki dev build
    ##---------------
    parser_build = subparsers_dev.add_parser("build",
        help="build a loki release", description="Builds a loki release")
    parser_build.set_defaults(command=command_build)

    ## loki dev deploy
    ##----------------
    parser_deploy = subparsers_dev.add_parser("deploy",
        help="deploy a loki release", description="Deploys a loki release")
    parser_deploy.set_defaults(command=command_deploy)

    ## loki dev list-tags
    ##-------------------
    parser_lstags = subparsers_dev.add_parser("list-tags", 
        help="DEPRECATED (use 'git tag' or 'git ls-remote)",
        description="DEPRECATED: use 'git tag -l' to check local tags or 'git ls-remote --tags ssh://git@gitlab.cern.ch:7999/atlas-perf-tau/loki.git' to check server")
    parser_lstags.set_defaults(command=command_lstags)

    ## loki dev tag
    ##------------- 
    parser_tag = subparsers_dev.add_parser("tag", 
        help="DEPRECATED (use 'bumpversion')",
        description="DEPRECATED: use 'bumpversion <part>', part=patch,minor,major'")
    parser_tag.set_defaults(command=command_tag)

    ## loki dev log
    ##-------------
    parser_log = subparsers_dev.add_parser("log",
        help="DEPRECATED (use git comments)",
        description="DEPRECATED: ChangeLog replaced by thoughtful git commit/merge comments")
    parser_log.set_defaults(command=command_log)


#______________________________________________________________________________=buf=
def command_new(args):
    """Subcommand for *loki new*"""
    mode = args.mode
    fname = args.file[0]
    from filegen import FileCreator
    fc = FileCreator(fname)
    if mode == "exec":
        from filegen import Main
        fc.add(Main())
    if mode == "mod": 
        from filegen import Class, Function
        fc.add(Class('MyClass'))
        fc.add(Function('my_function'))         
    fc.write()
    exit(0)


#______________________________________________________________________________=buf=
def command_build(args):
    """Subcommand for *loki dev build*"""
    t = DevTool()
    # build release
    if not t.build_release():
        print("ERROR: failure building release")
        exit(1)


# ______________________________________________________________________________=buf=
def command_deploy(args):
    """Subcommand for *loki dev deploy*"""
    t = DevTool()
    # deploy release
    if not t.deploy_release():
        print("ERROR: failure deploying release")
        exit(1)


#______________________________________________________________________________=buf=
def command_tag(args):
    """DEPRECATED: Subcommand for *loki tag*"""
    print("DEPRECATED: use 'bumpversion <part>', part=patch,minor,major'")
    exit(1)


#______________________________________________________________________________=buf=
def command_log(args):
    """DEPRECATED: Subcommand for *loki log*"""
    print("DEPRECATED: ChangeLog replaced by thoughtful git commit/merge comments")
    exit(1)


#______________________________________________________________________________=buf=
def command_lstags(args):
    """DEPRECATED: Subcommand for *loki list-tags*"""
    print("DEPRECATED: use 'git tag -l' to check local tags or 'git ls-remote --tags ssh://git@gitlab.cern.ch:7999/atlas-perf-tau/loki.git' to check server")
    exit(1)


## EOF
