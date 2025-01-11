# encoding: utf-8
"""
loki.core.var
~~~~~~~~~~~~~

This module provides an implemenation of the :class:`loki.core.var.Var` 
class for features like binning and latex formatted names for variables.

"""
__author__    = "Will Davey"
__email__     = "will.davey@cern.ch"
__created__   = "2012-10-25"
__copyright__ = "Copyright 2012 Will Davey"
__license__   = "GPL http://www.gnu.org/licenses/gpl.html"



## modules
import re
import ROOT
#from array import array
from loki.core.histutils import new_hist, histargs, bins, log_bins, set_axis_binnames
from loki.core.logger import log


# - - - - - - - - - - - - - - -  global - - - - - - - - - - - - - - - - - #


# - - - - - - - - - - - - - - -  class defs - - - - - - - - - - - - - - - - - #

#------------------------------------------------------------------------------=buf=
class VarBase(object):
    """Base class for TTree variables and expressions. 

    This class implements some basic common functionality and defines the 
    virtual interfaces to be implemented by the derived variable classes.  
    
    *tree_init* must be called before using the variable with an input tree 
    
    VarBase objects can be combined via the ``&`` operator, creating a 
    :class:`loki.core.var.Cuts` object, which represents a selection string.
    
    VarBase objects can be combined via the ``*`` operator, creating a 
    :class:`loki.core.var.Weights` object, which represents a weight string. 
    
    :param name: unique identifier
    :type name: str
    :param cont: container name in MxAOD
    :type cont: str
    :param invars: input variables
    :type invars: list :class:`loki.core.var.VarBase`
    :param xtitle: TLatex formatted title of variable to be used on plots
    :type xtitle: str
    :param short_title: short title mainly used for resolution variables
    :type short_title: str
    :param xunit: unit for variable
    :type xunit: str
    :param truth_partner: truth-tau equivalent to matched variable
    :type truth_partner: :class:`Var`
    :param temp: if True, don't add to global variable registry
    :type temp: bool
    """
    global_instances = dict()
    counter = 0
    #__________________________________________________________________________=buf=
    def __init__(self, 
            name    = None, 
            cont    = None, 
            invars  = None,
            xtitle  = None,
            short_title = None,
            xunit   = None,
            truth_partner = None,
            temp = False,
            ):      
        ## defaults 
        if xtitle is None: 
            if cont is None: xtitle = name 
            else: xtitle = f"{cont.name} {name}"
        if short_title is None: short_title = xtitle
        if truth_partner is None: truth_partner = self
        
        ## config 
        self.name          = name
        self.cont          = cont
        self.invars        = invars or []
        self.xtitle        = xtitle
        self.short_title   = short_title
        self.xunit         = xunit                
        self.truth_partner = truth_partner
        self.temp          = temp

        ## members
        self.views = []        
        self.isint = False

        ## initialization checks
        self.__check_invars__()

        ## set unique id
        self.uid = int(VarBase.counter)
        VarBase.counter+=1
        #print(f"{self.uid:4d}: {self.get_name()}")
        
        ## add to instances if not in container
        if not temp and cont is None:
            if name in VarBase.global_instances: 
                log().warn(f"Attempt to create multiple global vars with name {name}, duplicates will not be available on lookup")
                return
            VarBase.global_instances[name] = self


    # 'Virtual' interfaces (to be implemented in derived class)
    #__________________________________________________________________________=buf=
    def get_expr(self):
        """Return the expression string (eg. for TTree::Draw)
        
        IMPORTANT: implementation must be provided by derived class.
        
        :rtype: str        
        """
        log().warn("Class derived from VarBase must provide implementation of get_expr()!")
        return None

    #__________________________________________________________________________=buf=
    def tree_init(self,tree):
        """Initialise variable to work on *tree*. Return True if success.
        
        IMPORTANT: implementation must be provided by derived class.
        
        :param tree: target tree
        :type tree: :class:`ROOT.TTree`
        :rtype: bool
        """
        log().warn("Class derived from VarBase must provide implementation of treeinit()!")
        return False

    # Concrete interfaces (functionality provided by VarBase base class)
    #__________________________________________________________________________=buf=
    def sample_init(self,sample):
        """Initialise variable to work on *sample*. Return True if success.
        
        :param sample: target sample
        :type sample: :class:`loki.core.sample.Sample`
        :rtype: bool
        """
        t = sample.get_tree()
        if not t:
            log().warn("Cannot init var on sample without valid tree") 
            return False
        return self.tree_init(t)
    
    #__________________________________________________________________________=buf=
    def add_view(self, nbins=None, xmin=None, xmax=None, name = None, ytitle = None, 
                 do_logx = False, do_logy = False, xbins = None, binnames = None):
        """Add a *view* to the variable then return the variable. 
        
        Bins are created with standard (linear) spacing provided 
        by (*nbins*, *xmin*, *xmax*). Logarithmic spacing used if 
        *do_logx* is True. Custom bin spacing can be specified via *xbins*.
                 
        Variable is returned to support multiple concatenated calls to 'add_view' 

        See :class:`loki.core.var.View` for documentation. 
        
        :param nbins: number of bins
        :type nbins: int
        :param xmin: minimum of x-axis range
        :type xmin: float        
        :param xmax: maximum of x-axis range
        :type xmax: float
        :param name: name of view
        :type name: str
        :param ytitle: y-axis title (if default not adequate)
        :type ytitle: str
        :param do_logx: use log binning and scale for x-axis
        :type do_logx: bool
        :param do_logy: use log-scale for y-axis
        :type do_logy: bool
        :param xbins: custom bin edges (overrides *nbins*, *xmin*, *xmax*)
        :type xbins: list float
        :rtype: :class:`loki.core.var.VarBase`
        """
        # unless xbins provided, check nbins, xmin, xmax
        if xbins is None:
            if None in [nbins,xmin,xmax]: 
                log().error("Must provide (nbins,xmin,xmax) or xbins to add_view")
                raise ValueError
        
        binwidth = None
        if not xbins: 
            if do_logx: 
                xbins = log_bins(nbins,xmin,xmax)
            else:       
                xbins = bins(nbins,xmin,xmax)
                binwidth = (xmax - xmin) / float(nbins)
        v = View(self, xbins, name=name, ytitle=ytitle, do_logy=do_logy, 
                 do_logx=do_logx, binwidth=binwidth, binnames=binnames)
        
        # check for duplicate
        if v.name in [itrv.name for itrv in self.views]: 
            log().warn(f"Attempt to add multiple views with non-unique name {v.name} to var {self._get_name()}")
        else: 
            self.views.append(v)
            
        return self

    #__________________________________________________________________________=buf=
    def get_name(self):
        """Return the variable name""" 
        if self.cont is None:
            return self.name
        return f"{self.cont.name}_{self.name}"

    #__________________________________________________________________________=buf=
    def get_newbranch(self):
        """Return the new branch name (eg. used on tree writeout)""" 
        if self.cont is None:
            return self.name
        return f"{self.cont.name}.{self.name}"

    #__________________________________________________________________________=buf=
    def get_view(self, name = None):
        """Return view of the variable specified by *name*. 

        Return first (default) view if *name* not passed. 
        Return None if view not found.   

        :param name: name of view 
        :type name: str 
        :rtype: :class:`loki.core.var.View`
        """
        if not self.views: 
            log().warn(f"Attempted to retrieve view from {self.get_name()} which has no views!")
            return None

        ## default view
        if name is None: 
            return self.views[0]
        
        ## specific view
        matches = [v for v in self.views if v.name == name]
        if not matches: 
            log().warn(f"Couldn't find view {name} in var {self.get_name()}!")
            return None
        return matches[0] 

    #__________________________________________________________________________=buf=
    def has_view(self, name = None):
        """Return True if view of the variable specified by *name* exists."""
        if not self.views:
            return False
        matches = [v for v in self.views if v.name == name]
        return bool(matches)
        
    #__________________________________________________________________________=buf=
    def get_xtitle(self):
        """Return the x-axis title (including unit) of the varaible

        :rtype: str
        """
        xtitle = f'{self.xtitle}'
        if self.xunit:
            xtitle = f'{self.xtitle} [{self.xunit}]'
        return xtitle

    #__________________________________________________________________________=buf=
    def get_short_title(self):
        """Return the "short title", used mainly for response variables

        Eg. in :class:`loki.core.hist.ResoProfile` we need to name 
        the y-axis something like "Tau pT Resolution", while the 
        yvar is "Reco Tau pT / True Tau pT"

        :rtype: str
        """
        return self.short_title

    #__________________________________________________________________________=buf=
    def get_inconts(self):
        """Return set of containers use by invars
        
        :rtype: set :class:`loki.core.var.Container`
        """
        if not self.invars: return set([self.cont])
        s = set()
        for v in self.invars: 
            s = s.union(v.get_inconts())
        return s

    #__________________________________________________________________________=buf=
    def get_mvinconts(self):
        """Return set of mutlivalued containers used by invars
        
        :rtype: set :class:`loki.core.var.Container`
        """
        return set([c for c in self.get_inconts() if c is not None and not c.single_valued]) 

    #__________________________________________________________________________=buf=
    def get_type(self):
        """Return the value type for the variable
        
        Note: can only be called after variable initialization
        
        :rtype: str ('f','i')
        """
        if self.is_integer(): return 'i'
        return 'f' 

    #__________________________________________________________________________=buf=
    def serialize(self):
        """Return var in string format"""
        if self.cont is None:
            return self.name
        return f"{self.cont.name}.{self.name}"

    #__________________________________________________________________________=buf=
    def is_multivalued(self):
        """Return True if from multivalued container"""
        return bool(self.get_mvinconts())

    #__________________________________________________________________________=buf=
    def is_integer(self):
        """Return True if is integer valued
        
        Note: can only be called after variable initialization
        """
        #if self.leafname is None: 
        #    log().warn(f"Attempt to call 'is_integer' on {self.get_name()} before tree initialization")
        #    return False
        return self.isint

    # 'Private' interfaces
    #__________________________________________________________________________=buf=
    def __check_invars__(self):
        """Raise error if invars contains multiple different multivalued containers"""
        log().debug(f"checking invars for {self.get_name()}...")
        if not self.invars: return
        # don't allow multiple multivalued input containers
        if len(self.get_mvinconts())>1: 
            log().error(f"For {self.get_name()}: Variables not allowed to be comprised of multiple multivalued containers!")
            raise VarError
        log().debug("invars OK!")
        return
        
    #__________________________________________________________________________=buf=
    def __hash__(self):
        """Return unique object hash (from name)

        :rtype: hash
        """
        # TODO: need to fix this to ensure it is unique
        #if self._leafname is None: 
        #    return self.get_name().__hash__()
        #return self._leafname.__hash__()
        return self.get_name().__hash__()

    #__________________________________________________________________________=buf=
    def __eq__( self, other ):
        """Define comparison operator"""
        return bool(self.__hash__() == other.__hash__())


    #____________________________________________________________
    def __and__(self,other):
        """Override ``&`` operator to combine two VarBase objects into Cuts"""
        if other is None: return self
        name = f"{self.name}_{other.name}"
        cont = self.cont
        cuts = [self,other]
        return Cuts(name,cuts,cont=cont,temp=True)

    #____________________________________________________________
    def __mul__(self,other):
        """Override ``*`` operator to combine two VarBase objects into Weights"""
        if other is None: return self
        name = f"{self.name}_{other.name}"
        cont = self.cont
        weights = [self,other]
        return Weights(name,weights,cont=cont,temp=True)

    #____________________________________________________________
    def __str__(self):
        """Override string for nice output"""
        return self.serialize()



#------------------------------------------------------------------------------=buf=
class Var(VarBase):
    """Standard variable class implementation

    Intended for using single variables as they are stored in the input tree, ie::
    
        <cont>.<var>
        
    Where *<cont>* is the input container object (passed to the base-class by the 
    *cont* argument), and *<var>* is the name of the variable. The suffix of the 
    container (eg. Aux, AuxDyn etc.) will be auto-detected from the input tree, 
    by searching for a match to the regular expression::  
    
        "{cont}\w*.{var}$"
    
    If *cont* is None, the <cont>. prefix will be dropped. 

    See :class:`loki.core.var.VarBase` for details on base class and constructor 
    arguments.

    For complex and/or multi-variable expressions, see :class:`loki.core.var.Expr`. 

    :param var: variable (branch) name in input tree (MxAOD) 
    :type var: str
    """
    #__________________________________________________________________________=buf=
    def __init__(self, name = None, var = None, **kwargs): 
        VarBase.__init__(self, name = name, **kwargs)
        ## config
        self.var = var or self.name
        ## members
        self.leafname = None

    # Implementations of 'Virtual' interfaces
    #__________________________________________________________________________=buf=
    def get_expr(self):
        """Return the expression string (eg. for TTree::Draw)
        
        Returns the name of the branch correspodning to the variable, including 
        auto-determined container suffix. 
        
        Note: should be called after `tree_init` to ensure correct branch name
        
        :rtype: str
        """
        # uninitialized
        if self.leafname is None:
            log().warn(f"Attempt to access leafname for var '{self.get_name()}' before tree initialization")
            if self.cont is None: return str(self.var)
            return f"{self.cont}.{self.var}"

        # initialized
        return self.leafname

    #__________________________________________________________________________=buf=
    def tree_init(self,tree):
        """Initialise variable to work on *tree*. Return True if success.
        
        Auto-config is used for the container suffix
        (See :func:`findleafname`)  
         
        :rtype: bool 
        """
        # tree details
        tname = tree.GetName()
        f = tree.GetCurrentFile()
        fname = f.GetName() if f else None

        # already initialized (check leafname still valid)
        if self.leafname is not None:
            if not hasleaf(tree,self.leafname):
                if fname:
                    log().error(f"Previously initialised var {self.leafname} not available in {tname} from {fname}")
                else:
                    log().error(f"Previously initialised var {self.leafname} not available in {tname}")
                return False
            return True

        # initialize
        leafname = findleafname(tree, self.var, cont=self.cont, silent=False)
        if leafname is None: 
            log().error(f"Failure initializing {self.get_name()}")
            return False 

        self.leafname = leafname
        texpr = ROOT.TTreeFormula(self.get_name(), leafname, tree)
        self.isint = texpr.IsInteger()
        del texpr        
        log().debug(f"{self.get_name()} initialized")
        return True
           
    #__________________________________________________________________________=buf=
    def get_newbranch(self):
        """Return the new branch name (eg. used on tree writeout)
        
        This overrides the functionality in VarBase, since for Var, you want 
        to keep the variable branch name as in the original tree. 
        """ 
        if self.cont is None: 
            return self.var
        return f"{self.cont.name}.{self.var}"
                                                          

#------------------------------------------------------------------------------=buf=
class Expr(VarBase):
    """Complex multi-variable expression class implementation

    This class provides the functionality to create complex and/or mutli-variable 
    expressions (including selection criteria) from existing variables. 

    The expression (*expr*) should be in a format that can be processed by the 
    `ROOT.TTree.Draw` function. The input variables are provided by the *invars* 
    argument, and they should be referenced in the expression by their index 
    ({0}, {1} etc.). The variable replacement follows the positional format of 
    :func:`string.format` (see https://docs.python.org/2/library/string.html#format-examples). 
    Expansion of the *invars* at runtime allows auto-determination of container suffixes 
    (see :class:`loki.core.var.Var`) to be propagated to higher level expressions and 
    selection criteria. Note: *invars* may also contain other *Expr* objects. 
    
    Examples::
    
        {0} * {1}
        {0} == 1
        TMath::Exp({0})
        ({0} - {1})/{1}

    See :class:`loki.core.var.VarBase` for details on base class and constructor 
    arguments.

    :param expr: variable expression (can use multiple varaibles, predefined functions) 
    :type expr: str
    :param invars: list of input variables (or other expressions) as used in expression 
    :type invars: list :class:`loki.core.var.VarBase`
    :param kwargs: key-word arguments to pass to :class:`VarBase` 
    :type kwargs: key-word arguments
    """
    #__________________________________________________________________________=buf=
    def __init__(self, name = None, expr = None, invars = None, **kwargs):
        VarBase.__init__(self, name = name, invars = invars, **kwargs)      
        ## config
        self.expr = expr   
        ## members     
        self.exprstr = None
        self.namestr = None

    # Implementations of 'Virtual' interfaces
    #__________________________________________________________________________=buf=
    def get_expr(self):
        """Return the variable string for TTree::Draw
        
        Replaces variable references ({0}, {1} etc) in *expr* string 
        by their own expression. Allows dynamic functionality of 
        :class:`loki.core.var.Var` to be propagated at run time. 
        
        :rtype: str
        """
        if self.namestr: return self.namestr
        elif self.exprstr: return self.exprstr        
        log().warn(f"Attempt to access expr for var '{self.get_name()}' before tree initialization")
        return self.get_name()

    #__________________________________________________________________________=buf=
    def tree_init(self,tree):
        """Initialise variable to work on *tree*. Return True if success.
        
        Returns True if all *invars* initialized correctly. 
        """
        # tree details
        tname = tree.GetName()
        f = tree.GetCurrentFile()
        fname = f.GetName() if f else None
        
        # already initialized as name-match (check leafname still valid)
        if self.namestr:
            if not hasleaf(tree,self.namestr):
                if fname:
                    log().error(f"Previously initialised var {self.namestr} not available in {tname} from {fname}")
                else:
                    log().error(f"Previously initialised var {self.namestr} not available in {tname}")
                return False
            return True
        
        # attempt name-match initialization            
        if not self.exprstr:  
            namestr = findleafname(tree, self.name, cont=self.cont, silent=True)        
            if namestr:
                texpr = ROOT.TTreeFormula(self.get_name(), namestr, tree)
                self.isint = texpr.IsInteger()
                del texpr
                self.namestr = namestr 
                return True
        
        # standard initialize
        status = [v.tree_init(tree) for v in self.invars]
        if False in status:
            log().error(f"Failed to initialize {self.get_name()}")
            return False 
        exprstr = self.expr.format(*[v.get_expr() for v in self.invars])
        # first initialization
        if self.exprstr is None:
            texpr = ROOT.TTreeFormula(self.get_name(), exprstr, tree)
            if not texpr.GetNdim(): 
                log().error(f"Invalid expression in {self.get_name()}: {exprstr}")
                return False
            self.isint = texpr.IsInteger()
            del texpr        
        self.exprstr = exprstr
        return True
        

#------------------------------------------------------------------------------=buf=
class Cuts(VarBase):
    """Class implementation for expression of multiple selection criteria

    The list of selection criteria (*invars*) are each evaluated and combined 
    with an AND condition.   
    
    See :class:`loki.core.var.VarBase` for details on base class and 
    constructor arguments.

    :param invars: list of input criteria (variables, expressions or invars) 
    :type invars: list :class:`loki.core.var.VarBase`
    :param kwargs: key-word arguments to pass to :class:`VarBase` 
    :type kwargs: key-word arguments
    """
    #__________________________________________________________________________=buf=
    def __init__(self, name = None, cuts = None, **kwargs):
        VarBase.__init__(self, name = name, invars = cuts, **kwargs)
        ## members     
        self.exprstr = None
        self.namestr = None

    # Implementations of 'Virtual' interfaces        
    #__________________________________________________________________________=buf=
    def get_expr(self):
        """Return the variable string for TTree::Draw
        
        Each of the input cut expressions is evaluated and combined via an AND 
        operator (&&). Allows dynamic functionality of :class:`loki.core.var.Var` 
        to be propagated at run time. 
        
        :rtype: str
        """
        if self.namestr: return self.namestr
        elif self.exprstr: return self.exprstr        
        log().warn(f"Attempt to access expr for var '{self.get_name()}' before tree initialization")
        return self.get_name()

    #__________________________________________________________________________=buf=
    def tree_init(self,tree):
        """Initialise variable to work on *tree*. Return True if success.
        
        Returns True if all input *invars* initialized correctly. 
        """
        # tree details
        tname = tree.GetName()
        f = tree.GetCurrentFile()
        fname = f.GetName() if f else None
        
        # already initialized as name-match (check leafname still valid)
        if self.namestr:
            if not hasleaf(tree,self.namestr):
                if fname:
                    log().error(f"Previously initialised var {self.namestr} not available in {tname} from {fname}")
                else:
                    log().error(f"Previously initialised var {self.namestr} not available in {tname}")
                return False
            return True
        
        # attempt name-match initialization (only if not temp variable)            
        if not self.temp and not self.exprstr:  
            namestr = findleafname(tree, self.name, cont=self.cont, silent=True)        
            if namestr:
                texpr = ROOT.TTreeFormula(self.get_name(), namestr, tree)
                self.isint = texpr.IsInteger()
                del texpr
                self.namestr = namestr 
                return True

        # standard initialize
        status = [v.tree_init(tree) for v in self.invars]
        if False in status:
            log().error(f"Failed to initialize {self.get_name()}")
            return False
        if self.invars: 
            cuts = [f"({c.get_expr()})" for c in self.invars]
            exprstr = "&&".join(cuts)
        else: 
            exprstr = "1"
        # first initialization
        if self.exprstr is None:
            ## Note: this doesn't work :(
            #for v in self.invars: 
            #    if not v.is_integer(): 
            #        log().error("Cuts must consist of integer expressions!")
            #        log().error(f"Failed to initialize {self.get_name()}")
            #        return False
            self.isint = True        
        self.exprstr = exprstr
        return True    


#------------------------------------------------------------------------------=buf=
class Weights(VarBase):
    """Class implementation for expression of multiple invars

    The list of invars (*invars*) are each evaluated and combined 
    by the product operator.   
    
    See :class:`loki.core.var.VarBase` for details on base class and 
    constructor arguments.

    :param invars: list of input invars (variables, expressions or invars) 
    :type invars: list :class:`loki.core.var.VarBase`
    :param kwargs: key-word arguments to pass to :class:`VarBase` 
    :type kwargs: key-word arguments
    """
    #__________________________________________________________________________=buf=
    def __init__(self, name = None, weights = None, **kwargs):
        VarBase.__init__(self, name = name, invars = weights, **kwargs)
        ## members     
        self.exprstr = None
        self.namestr = None
        
    # Implementations of 'Virtual' interfaces
    #__________________________________________________________________________=buf=
    def get_expr(self):
        """Return the variable string for TTree::Draw
        
        Each of the input weight expressions is evaluated and combined via the 
        product operator (*). Allows dynamic functionality of :class:`loki.core.var.Var` 
        to be propagated at run time. 
        
        :rtype: str
        """
        if self.namestr: return self.namestr
        elif self.exprstr: return self.exprstr        
        log().warn(f"Attempt to access expr for var '{self.get_name()}' before tree initialization")
        return self.get_name()

    #__________________________________________________________________________=buf=
    def tree_init(self,tree):
        """Initialise variable to work on *tree*. Return True if success.
        
        Returns True if all input *invars* initialized correctly. 
        """
        # tree details
        tname = tree.GetName()
        f = tree.GetCurrentFile()
        fname = f.GetName() if f else None
        
        # already initialized as name-match (check leafname still valid)
        if self.namestr:
            if not hasleaf(tree,self.namestr):
                if fname:
                    log().error(f"Previously initialised var {self.namestr} not available in {tname} from {fname}")
                else:
                    log().error(f"Previously initialised var {self.namestr} not available in {tname}")
                return False
            return True
        
        # attempt name-match initialization (only if not temp variable)            
        if not self.temp and not self.exprstr:  
            namestr = findleafname(tree, self.name, cont=self.cont, silent=True)        
            if namestr:
                texpr = ROOT.TTreeFormula(self.get_name(), namestr, tree)
                self.isint = texpr.IsInteger()
                del texpr
                self.namestr = namestr 
                return True

        # standard initialize 
        status = [v.tree_init(tree) for v in self.invars]
        if False in status:
            log().error(f"Failed to initialize {self.get_name()}")
            return False
        if self.invars: 
            cuts = [f"({c.get_expr()})" for c in self.invars]
            exprstr = "*".join(cuts)
        else: 
            exprstr = "1"
        self.exprstr = exprstr
        return True


#------------------------------------------------------------------------------=buf=
class StaticExpr(VarBase):
    """Class for static variable expressions (should be avoided for standard use) 
    
    The class returns the exact expression it is given. It cannot be given input 
    variables or a container, and therefore does not support dynamic expansion
    of the expression at runtime.   
      
    See :class:`loki.core.var.VarBase` for details on base class and constructor 
    arguments.

    For complex and/or multi-variable expressions, see :class:`loki.core.var.Expr`. 

    :param var: variable (branch) name in input tree (MxAOD) 
    :type var: str
    """
    #__________________________________________________________________________=buf=
    def __init__(self, name = None, var = None, **kwargs): 
        VarBase.__init__(self, name = name, **kwargs)
        ## config 
        self.var = var if var is not None else self.name
        ## memebrs
        self.isinitialized = False

    # Implementations of 'Virtual' interfaces
    #__________________________________________________________________________=buf=
    def get_expr(self):
        """Return the expression string (eg. for TTree::Draw)

        Directly returns self.var
        
        :rtype: str
        """
        return self.var

    #__________________________________________________________________________=buf=
    def tree_init(self,tree):
        """Initialise variable to work on *tree*. Return True if success.
        
        Auto-config is used for the container suffix
        (See :func:`findleafname`)  
         
        :rtype: bool 
        """
        # removed re-check since it is invalid for complex expressions
        # TODO: need to revisit choice to remove
        '''
        if not hasleaf(tree, self.var): 
            log().error(f"Static var {self.var} not available, failed initialization!")
            return False
        '''
        if not self.isinitialized: 
            texpr = ROOT.TTreeFormula(self.get_name(), self.var, tree)
            if not texpr.GetNdim(): 
                log().error(f"Invalid expression in {self.get_name()}: {self.var}")
                return False                        
            self.isint = texpr.IsInteger()
            del texpr
            self.isinitialized = True        
            log().debug(f"{self.get_name()} initialized")
        return True
       
    #__________________________________________________________________________=buf=
    def get_newbranch(self):
        """Return the new branch name (eg. used on tree writeout)
        
        This overrides the functionality in VarBase, since for StaticExpr, you want 
        to use the exact var name without adding a container. 
        """ 
        return self.name


#------------------------------------------------------------------------------=buf=
class View(object):
    """Class that provides a specific view (binning) for a given variable 

    :param var: parent variable 
    :type var: :class:`loki.core.var.VarBase`    
    :param xbins: list of bin edges
    :type xbins: float list    
    :param name: unique identifier
    :type name: str
    :param ytitle: y-axis title to be used with variable (default to Nevents)
    :type ytitle: str
    :param do_logy: if variable should be plotted with log-scale on y-axis
    :type do_logy: bool 
    :param do_logx: if variable should be plotted with log-scale on x-axis
    :type do_logx: bool
    :param binwidth: width of bins (if fixed)
    :type binwidth: float
    """
    #__________________________________________________________________________=buf=
    def __init__(self, 
            var,
            xbins,            
            name    = None,
            ytitle  = None,
            do_logy = False,
            do_logx = False,
            binwidth = None,
            binnames = None,
            ):
      
        ## config 
        self.var     = var
        self.xbins   = xbins        
        self.name    = name or "default"        
        self.ytitle  = ytitle
        self.do_logy = do_logy
        self.do_logx = do_logx
        self.binwidth = binwidth
        self.fixedwidth = binwidth is not None
        self.binnames = binnames
        if binnames: 
            assert len(binnames) <= len(xbins), f"binnames must not be longer than xbins in var: {self.get_name()}"

    #__________________________________________________________________________=buf=
    def get_bins(self):
        """Return list of bin edges
                
        :rtype: float list
        """
        return list(self.xbins)

    #__________________________________________________________________________=buf=
    def get_name(self):
        """Return view name, format: "<var>_<view>"
                
        :rtype: str
        """
        return f"{self.var.get_name()}_{self.name}"

    #__________________________________________________________________________=buf=
    def get_truth_partner(self):
        """Access to self.var.get_expr()"""
        if self.var.truth_partner is None: return None
        # return same view of truth partner
        # TODO: may need to add some protection that 
        # truth partner view is identical, or get 
        # rid of them completely!
        return self.var.truth_partner.get_view(self.name)

    #__________________________________________________________________________=buf=
    def get_xmax(self):
        """Return maximum x-value
        
        :rtype: float
        """
        return self.xbins[-1]

    #__________________________________________________________________________=buf=
    def get_xmin(self):
        """Return minimum x-value
        
        :rtype: float
        """
        return self.xbins[0]

    #__________________________________________________________________________=buf=
    def get_ytitle(self):
        """Return the y-axis title (including bin width) of the variable.

        If :attr:`View.ytitle` is not set will return "Events / <bin width>"

        :rtype: str
        """
        if self.ytitle: return self.ytitle
        if not self.fixedwidth: 
            log().debug( 'plot has custom binning, cant include bin width in yaxis title' )
            return 'Events'
        bin_width = self.binwidth
        bin_width_str = f'{bin_width:.1g}'
        xunit = self.var.xunit
        if bin_width >= 10: bin_width_str = f'{bin_width:.3g}'
        if bin_width == 1:
            if xunit: 
                return f'Events / {xunit}'
            return 'Events'
        elif xunit:
            return f'Events / {bin_width_str} {xunit}'
        return f'Events / {bin_width_str}'

    #__________________________________________________________________________=buf=
    def serialize(self):
        """Return view in string format"""
        return f"{self.var.serialize()}:{self.name}"

    #__________________________________________________________________________=buf=
    def new_hist(self, yvar=None, zvar=None, name=None):
        """Return an empty histogram customized for this variable.
        
        :rtype: :class:`ROOT.TH1`
        """
        # create hist
        args = histargs(self,yvar,zvar,name)
        h = new_hist(*args)
        
        # set binnames
        if self.binnames: 
            log().debug(f"Setting bin labels: {self.binnames}")
            set_axis_binnames(h.GetXaxis(), self.binnames)
        if yvar and yvar.binnames: 
            log().debug(f"Setting bin labels: {yvar.binnames}")
            set_axis_binnames(h.GetYaxis(), yvar.binnames)
        if zvar and zvar.binnames: 
            log().debug(f"Setting bin labels: {zvar.binnames}")
            set_axis_binnames(h.GetZaxis(), zvar.binnames)
            
        return h

    #__________________________________________________________________________=buf=
    def frame(self,pad, xmin = None, ymin = None, xmax = None, ymax = None,
              xtitle = None, ytitle = None, yvar = None):
        """Return a frame for the variable

        If *xmin* and *xmax* not provided will be determined from variable.
        *ymin* and *ymax* should be provided, otherwise dummy 0 and 1 are used.

        :param pad: pad (or canvas) on which to draw the frame
        :type pad: :class:`ROOT.TPad`
        :param xmin: x-axis minimum
        :type xmin: float
        :param xmax: x-axis maximum
        :type xmax: float
        :param ymin: y-axis minimum
        :type ymin: float
        :param ymax: y-axis maximum
        :type ymax: float
        :param xtitle: x-axis title 
        :type xtitle: str        
        :param ytitle: y-axis title 
        :type ytitle: str
        :param yvar: y-axis variable view
        :type yvar: :class:`loki.core.var.View`

        """
        # determine boundaries
        if xmin == None and xmax is not None: xmin = self.get_xmin() 
        if xmax == None and xmin is not None: xmax = self.get_xmax()
        if ymin == None: ymin = 0.
        if ymax == None: ymax = 1.

        # determine axis titles
        xtitle = xtitle or self.get_xtitle()
        ytitle = ytitle or self.get_ytitle()

        # build and return frame
        #return pad.DrawFrame(xmin,ymin,xmax,ymax, f';{xtitle};{ytitle}')
        pad.cd()
        name = f"fr_{self.get_name()}"
        if yvar: name += f"_{yvar.get_name()}"
        fr = self.new_hist(yvar=yvar,name=name)
        if xmin is not None or xmax is not None: 
            fr.GetXaxis().SetRangeUser(xmin,xmax)
        fr.GetYaxis().SetRangeUser(ymin,ymax)
        fr.GetXaxis().SetTitle(xtitle)
        fr.GetYaxis().SetTitle(ytitle)
        fr.SetTitle("")
        fr.Draw()
        return fr

    ## Copied interfaces from self.var
    #__________________________________________________________________________=buf=
    def get_expr(self):
        """Access to self.var.get_expr()"""
        return self.var.get_expr() 

    #__________________________________________________________________________=buf=
    def get_xtitle(self):
        """Access to self.var.get_xtitle()"""
        return self.var.get_xtitle()

    #__________________________________________________________________________=buf=
    def get_short_title(self):
        """Access to self.var.get_short_title()"""
        return self.var.get_short_title()

    #__________________________________________________________________________=buf=
    def __hash__(self):
        """Return unique object hash (from name)

        :rtype: hash
        """
        return self.get_name().__hash__()

    #__________________________________________________________________________=buf=
    def __eq__( self, other ):
        """Define comparison operator"""
        return bool(self.__hash__() == other.__hash__())

    #____________________________________________________________
    def __str__(self):
        """Override string for nice output"""
        return self.serialize()


#------------------------------------------------------------------------------=buf=
class Container(object):
    """Class that represents an xAOD object container
    
    The name of the container should not include the 'Aux' or 'Dyn' suffixes; 
    they will be auto-determined on a variable by variable basis from the input 
    tree by the :class:`loki.core.var.Var`. 
    
    Variables already existing in the container in the input tree can be registered 
    by :func:`add_var`.
    
    Complex and/or multi-variable expressions (including selection criteria) can 
    be created and added to the container with :func:`add_expr`. 
    
    Groups of selection criteria can be created using :func:`add_cuts`.
    
    Groups of weight expressions can be created using :func:`add_weights`.
    
    :param name: name of the container
    :type name: str
    :param single_valued: if container only ever has one value per event
    :type single_valued: bool
    """
    instances = dict()
    #__________________________________________________________________________=buf=
    def __init__(self, name, single_valued=False):
        # config 
        self.name = name
        self.single_valued = single_valued

        # members
        self.vars = []

        # add to global instances        
        if name in Container.instances: 
            log().warn(f"Attempt to create multiple containers with name {name}, duplicates will not be available on lookup")
            return
        Container.instances[name] = self

    #__________________________________________________________________________=buf=
    def get_var(self, name): 
        """Get variable by name
        
        :rtype: :class:`loki.core.var.Var`
        """ 
        matches = [v for v in self.vars if v.name == name]
        if not matches: return None
        return matches[0]

    #__________________________________________________________________________=buf=
    def has_var(self, name): 
        """Return True if variable in container"""
        return self.get_var(name) is not None

    #__________________________________________________________________________=buf=
    def add_var(self, name, var = None, xtitle = None, xunit = None, 
               short_title = None, truth_partner = None): 
        """Adds a new simple variable to container and returns it.
        
        See :class:`loki.core.var.Var` for details.
        
        :rtype: :class:`loki.core.var.Var`
        """ 
        # check duplicate
        if name in [v.name for v in self.vars]: 
            log().warn(f"Attempting to add duplicate var {name} to container {self.name}")
            return None  
        
        # create var              
        v = Var(name, var=var, xtitle=xtitle, xunit=xunit, cont=self, 
                short_title=short_title, truth_partner=truth_partner)
        self.vars.append(v)
        
        # decorate
        setattr(self, name, v)

        return v

    #__________________________________________________________________________=buf=
    def add_expr(self, name, expr = None, invars = None, xtitle = None, xunit = None, 
               short_title = None, truth_partner = None): 
        """Adds complex and/or multi-variable expression to container and returns it.
        
        See :class:`loki.core.var.Expr` for details. 
        
        :rtype: :class:`loki.core.var.Expr`
        """
        # check duplicate 
        if name in [v.name for v in self.vars]: 
            log().warn(f"Attempting to add duplicate var {name} to container {self.name}")
            return None                
            
        # create expression    
        v = Expr(name, expr=expr, invars=invars, xtitle=xtitle, xunit=xunit, 
                 cont=self, short_title=short_title, truth_partner=truth_partner)
        self.vars.append(v)
        
        # decorate
        setattr(self, name, v)

        return v

    #__________________________________________________________________________=buf=
    def add_cuts(self, name, cuts = None): 
        """Adds expression of compound selection criteria to container and returns it.
        
        See :class:`loki.core.var.Cuts` for details
        
        :rtype: :class:`loki.core.var.Cuts`
        """ 
        # check duplicate 
        if name in [v.name for v in self.vars]: 
            log().warn(f"Attempting to add duplicate var {name} to container {self.name}")
            return None                
            
        # create invars        
        v = Cuts(name, cuts = cuts, cont=self)
        self.vars.append(v)
        
        # decorate
        setattr(self, name, v)

        return v

    #__________________________________________________________________________=buf=
    def add_weights(self, name, weights = None): 
        """Adds expression of compound invars to container and returns it.
        
        See :class:`loki.core.var.Weights` for details
        
        :rtype: :class:`loki.core.var.Weights`
        """ 
        # check duplicate 
        if name in [v.name for v in self.vars]: 
            log().warn(f"Attempting to add duplicate var {name} to container {self.name}")
            return None                
            
        # create invars        
        v = Weights(name, weights = weights, cont=self)
        self.vars.append(v)
        
        # decorate
        setattr(self, name, v)

        return v

    #__________________________________________________________________________=buf=
    def del_var(self, name): 
        """Delete variable"""
        v = self.get_var(name)
        if not v: 
            log().warn(f"Can't delete variable {name}")
            return
        self.vars.remove(v)
        del v


#------------------------------------------------------------------------------=buf=
class VarError(Exception):
    """Error class for initialization failure in :class:`loki.core.var.VarBase` objects"""
    def __str__(self):
        return repr("Error initializing variables")


#------------------------------------------------------------------------------=buf=
def hasleaf(tree, leaf):
    """Return True if *tree* contains *leaf*

    :param tree:
    :type tree: :class:`ROOT.TTree`
    :param leaf:
    :type leaf: str
    :rtype: bool
    """
    return bool(tree.GetLeaf(leaf))


#------------------------------------------------------------------------------=buf=
def search_leaves(tree, leaf_regex):
    """Return True if *tree* contains *leaf*

    :param tree:
    :type tree: :class:`ROOT.TTree`
    :param leaf:
    :type leaf: str
    :rtype: bool
    """
    leaves = [l.GetName() for l in tree.GetListOfLeaves()]
    matches = []
    regex = re.compile(leaf_regex)
    for l in leaves: 
        match = regex.match(l)
        if match: matches.append(l)
    return matches

#__________________________________________________________________________=buf=
def findleafname(tree, varname, cont=None, silent=False):
    """Find the variable name (*varname*) in the input *tree* 
    
    Implements auto-config of the container suffix (eg. Aux, AuxDyn etc.) by 
    searching for a branch in the tree matching the following expression::   
        
        "{cont}\w*.{var}$"
          
    
    If *cont* is None, {var} is used directly.
          
    :param tree: input tree 
    :type tree: :class:`ROOT.TTree`
    :param varname: variable name
    :type varname: str
    :param cont: variable container
    :type cont: :class:`loki.core.var.Container`
    :param silent: suppress all logging output
    :type silent: bool
    """
    # tree details
    tname = tree.GetName()
    f = tree.GetCurrentFile()
    fname = f.GetName() if f else None 

    # var without parent container
    if cont is None: 
        if hasleaf(tree,varname):
            if not silent: log().debug(f"{varname} initialized")
            return varname
        else: 
            if not silent: 
                if f: 
                    log().error(f"Variable {varname} missing in {tname} from {fname}")
                else:
                    log().error(f"Variable {varname} missing in {tname}")
            return None
            
    # var with parent container
    leaf_regex = f"{cont.name}\w*.{varname}$"
    leaves = search_leaves(tree,leaf_regex)    
    if leaves:
        leafname = leaves[0]
        if not silent:  
            if len(leaves)>1: 
                log().warning(f"Found multiple leaves {leaves} matching {varname}")
            log().debug(f"{leafname} initialized")
        return leafname
    
    # failure for var with partent container
    if not silent: 
        leafname = f"{cont.name}.{varname}"
        if f: 
            log().error(f"Variable {leafname} missing in {tname} from {fname}")
        else:
            log().error(f"Variable {leafname} missing in {tname}")
    return None


#____________________________________________________________
def find_container(name):
    """Return container by name
    
    :param name: container name
    :type name: str
    :rtype: :class:`Container`
    """
    return Container.instances.get(name, None)


#____________________________________________________________
def find_variable(name):
    """Return variable by name

    :param name: variable name
    :type name: str    
    :rtype: :class:`VarBase` sub-class (None if not found)    
    """
    if name is None: return None
    if name.count(".") > 1: 
        log().warn("Variable name cannot contain multiple periods (ie '.')")
        return None
    # container variable
    elif name.count(".") == 1: 
        (cname, vname) = name.split('.')
        cont = find_container(cname)
        if cont is None: return None
        return cont.get_var(vname)
    
    # global variable
    return VarBase.global_instances.get(name,None)

#____________________________________________________________
def get_variable(name):
    """Return variable by name or create StaticExpr if not found
    
    :param name: variable name
    :type name: str
    :rtype: :class:`VarBase` sub-class
    """
    if name is None: return None
    if isinstance(name, VarBase): return name
    return find_variable(name) or StaticExpr(name)


#____________________________________________________________
def get_variables(names):
    """Return list of variables by name or create StaticExpr if not found
    
    :param names: list of variable names
    :type names: list str
    :rtype: list :class:`VarBase` subclass
    """
    return [get_variable(v) for v in names]

#____________________________________________________________
def find_view(name):
    """Return view by name

    :param name: view name (format "var:view")
    :type name: str    
    :rtype: :class:`View` sub-class (None if not found)    
    """
    if name is None: return None
    if isinstance(name, View): return name
    if name.count(":") > 1: 
        log().warn("View name connot contain multiple colons (ie ':')")
        return None
    elif name.count(":") == 1: 
        (varname, viewname) = name.split(":")
        var = find_variable(varname)
        if not var: return None
        if not var.has_view(viewname): return None
        return var.get_view(viewname)
    else: 
        var = find_variable(name)
        if not var: return None
        if not var.views: return None
        return var.get_view()


#____________________________________________________________
def get_view(view_str):
    """Return variable view by name or create using tuple

    Eg. for *view_str* is 'TauJets.pt:log' returning the 'log' view for 
    TauJets.pt or 'TauJets.eta' returning the default view for TauJets.eta.
    
    Can also specify a new view binning in format: VAR:NBINS;XMIN;XMAX
    
    The View will receive the name 'NBINS;XMIN;XMAX' 
    
    Note: vars don't have to be predefined. Undefined vars will be created on the 
    fly using :class:`loki.core.var.StaticExpr`. 
    
    
    :param view_str: view string: 'VAR:VIEW' or 'VAR:NBINS;XMIN;XMAX'
    :type view_str: str
    """
    if isinstance(view_str, View): return view_str
    
    viewargs = None
    # no view provided: attempt to get default view
    # var must be predefined (no StaticExpr)
    if not view_str.count(":"): 
        varname = view_str.strip()
        var = find_variable(varname)
        if not var: 
            log().error(f"Requested VAR {varname} not found! If no view provided, var must be predefined")
            return None
        view = var.get_view()
        if not view: 
            log().error(f"Default VIEW for VAR {varname} not found!")
        return view
    
    # view tuple provided: 
    (varname,viewname) = [v.strip() for v in view_str.split(':')]
    if viewname.count(";"):
        d = [v.strip() for v in viewname.split(';')] 
        viewargs = (int(d[0]), float(d[1]), float(d[2]))
        if not len(viewargs) == 3:
            log().error("View args must be in format 'nbins;xmin;xmax'") 
            return None
        var = get_variable(varname)
        var.add_view(*viewargs, name=viewname)
        return var.get_view(viewname)
    
    # named view provided
    var = find_variable(varname)
    if not var: 
        log().error(f"Requested VAR {varname} not found! Cannot create named view")
        return None
    view = var.get_view(viewname)
    if not view: 
        log().error(f"Requested VIEW {viewname} for VAR {varname} not found!")
    return view        
        
        
#____________________________________________________________
def default_weight():
    """Return default weight"""
    w = find_variable("noweight")
    if w is None: 
        w = Expr("noweight","1")
    return w


#____________________________________________________________
def default_cut():
    """Return default cut"""
    c = find_variable("nocut")
    if c is None: 
        c = Expr("nocut","1")
    return c



## EOF
