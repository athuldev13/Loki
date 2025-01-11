# encoding: utf-8
"""
loki.utils.filegen
~~~~~~~~~~~~~~~~~~

This module provides utils to auto-generate python source code.

"""
__author__ = 'Will Davey'
__email__ = 'will.davey@cern.ch'
__created__ = '2012-10-25'
__copyright__ = 'Copyright 2012 Will Davey'
__licence__ = 'GPL http://www.gnu.org/licenses/gpl.html'


## modules
import os 
import pwd
import datetime
import stat 
from system import Properties,get_project_path

g_sw = 4

# - - - - - - - - - - - - - - -  class defs - - - - - - - - - - - - - - - - - #
#______________________________________________________________________________=buf=
class FileCreator(object):
    """Class to create python scripts/modules 

    Takes in objects of :class:`AspectBase` and writes them to an output file 
    as python source. 

    The structure of the source code is: 
    
    - imports (module import calls)
    - prefunctions (early function definitions)
    - classes (class definitions)
    - functions (function definitions)
    - do_main (whether to include a main function)

    :param filename: name of new output file
    :type filename: str
    :param author: author name to include in file header
    :type author: str
    :param email: author's email to include in file header
    :type email: str

    """
    #__________________________________________________________________________=buf=    
    def __init__(self,filename, author = None, email = None):
        self.filename = filename
        self.aspects = []
        user_prop = Properties(os.path.join(get_project_path(), '.user.cfg'))
        self.author = author or user_prop.fullname()
        self.email  = email or user_prop.email()
        
    #__________________________________________________________________________=buf=
    def add(self,aspect):
        """Add an aspect to your document
        
        :param aspect:
        :type aspect: :class:`AspectBase`
        """
        self.aspects.append(aspect)

    #__________________________________________________________________________=buf=
    def write(self):
        """Write out your new python file"""
        ## get all aspects
        imports      = [ self.aspects[i].imports[j] 
                            for i in range(len(self.aspects)) 
                                for j in range(len(self.aspects[i].imports)) ]
        prefunctions = [ self.aspects[i].prefunctions[j] 
                            for i in range(len(self.aspects)) 
                                for j in range(len(self.aspects[i].prefunctions)) ]
        classes      = [ self.aspects[i].classes[j] 
                            for i in range(len(self.aspects)) 
                                for j in range(len(self.aspects[i].classes)) ]
        functions    = [ self.aspects[i].functions[j] 
                            for i in range(len(self.aspects)) 
                                for j in range(len(self.aspects[i].functions)) ]
        do_main      = True in [ a.do_main for a in self.aspects ]

        ## write 
        f = open(self.filename,'w')
        
        if do_main: f.write(text_exec())
        f.write(text_encoding())
        f.write(text_description(self.filename,author=self.author,email=self.email))
        f.write(text_space(2))
        f.write(text_modules())
        for m in imports: f.write( 'import %s\n'%(m) )
        if prefunctions:
            f.write(text_space(2))
            for m in prefunctions: 
                f.write(m)
                f.write(text_space(2))
                
        if classes:
            f.write(text_space(2))
            f.write(text_class_header())
            for m in classes: 
                f.write(m)
                f.write(text_space(2))
        if functions:
            f.write(text_space(2))
            f.write(text_func_header())
            for m in functions: 
                f.write(m)
                f.write(text_space(2))
        if do_main:
            f.write(text_space(2))
            f.write(text_main_if())

        f.write(text_eof()) 
        f.close()
        if do_main:
            mode = os.stat(self.filename).st_mode
            os.chmod(self.filename, mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


#______________________________________________________________________________=buf=
class AspectBase():
    """Aspect base class that can be added to a file

    :param imports: list of module imports
    :type imports: str list
    :param prefunctions: functions to appear before class defs
    :type prefunctions: functions to 
    :param classes: class definitions
    :type classes: list str
    :param functions: function definitions
    :type functions: list str
    :param do_main: write a main function
    :type do_main: bool

    """    
    #__________________________________________________________________________=buf=
    def __init__(self, 
            imports = None,
            prefunctions = None,
            classes = None,
            functions = None,
            do_main = False,
            ):
        self.imports      = imports if imports else []
        self.prefunctions = prefunctions if prefunctions else []
        self.classes      = classes if classes else []
        self.functions    = functions if functions else []
        self.do_main      = do_main
        

#______________________________________________________________________________=buf=
class Main(AspectBase):
    """ Main function

    Implements following features:

    - main function
    - imports ``optparse`` and ``sys`` modules
    - parsing function skeleton 

    """    
    #__________________________________________________________________________=buf=
    def __init__(self):
        AspectBase.__init__(self)
        self.do_main = True
        self.imports = [
            'argparse',
            'sys',
            ]
        self.prefunctions = [
            text_parser(),
            text_main(),
            ] 


#______________________________________________________________________________=buf=
class Class(AspectBase):
    """Class aspect implementing a class skeleton"""    
    #__________________________________________________________________________=buf=
    def __init__(self,classname):
        AspectBase.__init__(self)
        self.classes = [
            text_class(classname),
            ] 


#______________________________________________________________________________=buf=
class Function(AspectBase):
    """Function aspect implementing a function skeleton"""
    #__________________________________________________________________________=buf=
    def __init__(self,funcname,argstr=None):
        AspectBase.__init__(self)
        self.functions = [
            text_func(funcname,argstr),
            ] 


# - - - - - - - - - - - - - - - function defs - - - - - - - - - - - - - - - - #
#______________________________________________________________________________=buf=
def text_exec():
    """Python exec shebang generator"""
    return '#!/usr/bin/env python\n'


#______________________________________________________________________________=buf=
def text_encoding():
    """Source encoding string generator"""
    return '# encoding: utf-8\n'


#______________________________________________________________________________=buf=
def text_description( filename, author = None, email = None ):
    """Source file doc-string generator"""
    if not author: author = pwd.getpwuid(os.getuid())[0]

    # append module path (if new source file part of module) 
    curr_dir = os.getcwd()
    split_dir = curr_dir.split('/')
    modules = []
    for d,i in zip(reversed(split_dir),xrange(len(split_dir))):
        path = "/".join([".."]*i) 
        path = os.path.join(path,"__init__.py")
        if os.path.exists(path): 
            modules.append(d)
    modules.reverse()
    filename = ".".join(modules+[filename])
   
    # write source code
    text = ''
    text += '\"\"\"\n'
    text += '%s\n'%filename
    text += '~'*len(filename)+'\n'
    text += '\n'
    text += '<Description of module goes here...>\n'
    text += '\n'
    text += '\"\"\"\n'
    text += '__author__    = "%s"\n'%(author)
    if email: text += '__email__     = "%s"\n'%(email)
    text += '__created__   = "%s"\n' % (datetime.datetime.now().strftime("%Y-%m-%d"))
    text += '__copyright__ = "Copyright %s %s"\n' % (datetime.datetime.now().strftime("%Y"),author)
    text += '__license__   = "GPL http://www.gnu.org/licenses/gpl.html"\n'
    text += '\n'
    return text


#______________________________________________________________________________=buf=
def text_modules():
    """Modules comment generator"""
    return '## modules\n'


#______________________________________________________________________________=buf=
def text_space( n ):
    """Newline generator"""
    return '\n'*n


#______________________________________________________________________________=buf=
def text_func_line(indent=0):
    """Horizontal function line generator"""
    global g_sw
    n = 78 - (indent * g_sw)
    return '#' + '_' * n + "=buf="


#______________________________________________________________________________=buf=
def text_class_line():
    """Horizontal class line generator"""
    return '#' + '-' * 78 + "=buf="
                                                                                 

#______________________________________________________________________________=buf=
def text_class_header():
    """Class header generator"""
    return '# - - - - - - - - - - - - - - -  class defs - - - - - - - - - - - - - - - - - #\n'


#______________________________________________________________________________=buf=
def text_class(classname):
    """Class skeleton generator"""
    text = ''
    text += '%s\n'%(text_class_line())
    text += 'class %s():\n'%(classname)
    text += '    \"\"\"Description of %s\n'%(classname)
    text += '    \"\"\"\n'
    text += '    %s\n'%(text_func_line(indent=1))
    text += '    def __init__(self):\n'
    text += '        pass'
    return text


#______________________________________________________________________________=buf=
def text_func_header():
    """Function header generator"""
    return '# - - - - - - - - - - - - - - - function defs - - - - - - - - - - - - - - - - #\n'


#______________________________________________________________________________=buf=
def text_func(funcname, argstr = None, do_pass = True):
    """Function skeleton generator"""
    if argstr == None: argstr = ""
    text = ''
    text += '%s\n'% text_func_line()
    text += 'def %s(%s):\n'%(funcname,argstr)
    text += '    \"\"\"Description of %s\n'%(funcname)
    text += '    \"\"\"\n'
    if do_pass: text += '    pass\n'
    return text


#______________________________________________________________________________=buf=
def text_parser():
    """Option parser fucntion skeleton generator"""
    text = ''
    text += '%s\n' % text_func_line()
    text += 'def parse_args():\n'
    text += '    description="my awesome commandline util"\n'
    text += '    parser = argparse.ArgumentParser(description=description)\n'
    text += '\n'
    text += '    ## Define the Module\n'    
    text += '    # example mandatory positional argument\n'    
    text += '    #parser.add_argument( "infile", help="input file" )\n'    
    text += '    # example option\n'    
    text += '    #parser.add_argument( "-f", "--file", dest="out_file", default="ntup.root",\n'
    text += '    #    metavar="FILE", help="output file name (default: ntup.root)" )\n'
    text += '\n'
    text += '    ## parser args\n'
    text += '    args = parser.parse_args()\n'
    text += '\n'
    text += '    ## check args\n'
    text += '    #if len(args)<1:\n'
    text += '    #    print("ERROR - must supply ARG1"\n)'
    text += '    #    parser.print_help()\n'
    text += '    #    exit(1)\n'
    text += '\n'
    text += '    return args\n'
    return text


#______________________________________________________________________________=buf=
def text_main():
    """Main function skelton generator"""
    text = ''
    text += text_func('main', argstr=None, do_pass=False)
    text += '    args = parse_args()\n'
    text += '\n'
    text += '    ## your script goes here\n'
    text += '\n'
    text += '    exit(0)\n'
    return text


#______________________________________________________________________________=buf=
def text_main_if():
    """Main function include generator"""
    text = ''
    text += '%s\n' % text_func_line()
    text += 'if __name__=="__main__": main()\n'
    return text


#______________________________________________________________________________=buf=
def text_eof():
    """End of file generator"""
    return '## EOF\n'








