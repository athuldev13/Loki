# encoding: utf-8
"""
loki.core.style
~~~~~~~~~~~~~~~

This module provides a class for defining and applying styles
to ROOT objects
"""
__author__    = "Will Davey"
__email__     = "will.davey@cern.ch"
__created__   = "2016-02-21"
__copyright__ = "Copyright 2016 Will Davey"
__license__   = "GPL http://www.gnu.org/licenses/gpl.html"


## modules
from loki.core.logger import log

# - - - - - - - - - - - class defs  - - - - - - - - - - - - #
#------------------------------------------------------------
class Style():
    """Class to store and set style for ROOT hists/graphs etc.
 
    *stylekw* is an arbitrary set of named arguments intended
    to correspond to ROOT hist/graph style parameters, eg.: 
    Style(name="Signal",FillColor=ROOT.kBlack,LineStyle=4)

    They must be the same as used in the Setter/Getter functions
    for the object the style is applied to: TH1, TGraph, etc...

    For more info on passing arbitrary named parameters in python, 
    check out: http://stackoverflow.com/questions/1769403/understanding-kwargs-in-python

    :param name: simple text name for style
    :type name: str
    :param tlatex: TLatex formatted name for style
    :type tlatex: str
    :param drawopt: option to be used with Object::Draw() 
    :type drawopt: str
    :param stylekw: style options to be passed to your ROOT Object 
    :type stylekw: named argument list (arg1=val1,...,argN=valN)
    """

    #____________________________________________________________
    def __init__(self, name = None, tlatex = None, drawopt = None,
            **stylekw):
        self.name        = name
        self.tlatex      = tlatex or name
        self.drawopt     = drawopt 
        self.stylekw     = stylekw
        
        # set default options
        stylekw.setdefault("LineWidth",2)
        
        # attach options as attributes
        for key, value in stylekw.items():
            setattr(self,key,value)

    #____________________________________________________________
    def apply(self,h):
        """Apply style parameters to ROOT object

        :param h: ROOT object
        :type h: ROOT drawable object TH1, TGraph, etc...
        """
        #h.name = self.name
        #h.tlatex = self.tlatex
        #h.drawopt = self.drawopt
        for hprop,value in self.stylekw.items(): 
            if not value is None:
                try: 
                    getattr(h, f'Set{hprop}')(value)
                except: 
                    log().error(f"Invalid style option: {hprop}")
                    exit(1)

    #____________________________________________________________
    def __add__(self,other):
        """``+`` operator for Style objects (rvalue preference)
        
        I.e. the object on the right-hand side of the ``+``
        operator will override any properties in common with 
        the object on the left-hand side
        """
        kwargs = dict()
        kwargs.update(self.__dict__)
        kwargs.update(other.__dict__)
        if "stylekw" in kwargs: del kwargs["stylekw"]
        return Style(**kwargs)


#____________________________________________________________
def default_style():
    """Return default :class:`Style`"""
    return Style(name="Default", LineColor=1,MarkerColor=1,MarkerStyle=20)

## EOF
