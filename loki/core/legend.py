# encoding: utf-8
"""
loki.core.legend
~~~~~~~~~~~~~~~~

This module provides implementations for making legends. The new classes 
improve upon TLegend. 
"""
__author__    = "Will Davey"
__email__     = "will.davey@cern.ch"
__created__   = "2016-02-22"
__copyright__ = "Copyright 2016 Will Davey"
__license__   = "GPL http://www.gnu.org/licenses/gpl.html"



## modules
from ROOT import TLegend

# - - - - - - - - - - - class defs  - - - - - - - - - - - - #
#------------------------------------------------------------
class MetaLegend(object):
    """A better TLegend class that increases in height as you call AddEntry.

    Stolen of Ryan Reece's 'metaroot' package: https://svnweb.cern.ch/trac/penn/browser/PennTau/metaroot

    No more than one of *x1* and *x2*, and one of *y1* and *y2* should 
    be defined. 

    :param width: width of the legend
    :type width: float
    :param height: height of one entry
    :type height: float
    :param x1: left edge of legend
    :type x1: float
    :param x2: right edge of legend
    :type x2: float
    :param y1: bottom edge of legend
    :type y1: float
    :param y2: top edge of legend
    :type y2: float
    :param border: size of the border
    :type border: int
    :param fill_color: fill color of the legend
    :type fill_color: ROOT.Color_t
    :param fill_style: fill style of the legend
    :type fill_style: int
    :param ncol: number of columns in the legend
    :type ncol: int

    """ 

#______________________________________________________________________________
    def __init__(self, 
            width=None, 
            height=None,
            x1=None, 
            y1=None,
            x2=None, 
            y2=None,
            border=None, 
            fill_color=None, 
            fill_style=None,
            ncol=None,
            ):
        width = width or float(ncolumn) * 0.30
        height = height or 0.05
        border = border or 0
        fill_color = fill_color or 0
        fill_style = fill_style or 0
        ncol = ncol or 1
        
        # horizontal position
        if x1 == x2 == None:
            x2 = 0.93
            x1 = x2 - width
        elif x1 == None:
            x1 = x2 - width
        elif x2 == None:
            x2 = x1 + width
        
        # vertical position
        if y1 == y2 == None:
            y2 = 0.93
            y1 = y2 - width
        elif y1 == None:
            y1 = y2 - width
        elif y2 == None:
            y2 = y1 + width

        # build TLegend
        self.tleg = TLegend(x1, y1, x2, y2)
        self.tleg.SetBorderSize(border)
        self.tleg.SetFillColor(fill_color)
        self.tleg.SetFillStyle(fill_style)
        self.tleg.SetNColumns(ncol)
        self.tleg.SetTextFont(42)
        self.width = width
        self.height = height # per entry
        self._has_drawn = False

#______________________________________________________________________________
    def AddEntry(self, obj, label='', option='P'):
        """Add entry to legend and resize accordingly

        :param obj: object corresponding to new entry
        :type obj: ROOT drawable object (eg :class:`ROOT.TH1` or :class:`ROOT.TGraph`)
        :param label: name of entry in legend
        :type label: str
        :param option: legend option 
        :type option: str [allowed "F","P","L"]
        """
        self.tleg.AddEntry(obj, label, option)
        self.resize()

#______________________________________________________________________________
    def Draw(self):
        """Draw the legend"""
        self.resize()
        self.tleg.Draw()
        self._has_drawn = True

#______________________________________________________________________________
    def resize(self):
        """Resize the legend"""
        if self._has_drawn:
            y2 = self.tleg.GetY2NDC()
            self.tleg.SetY1NDC(y2 - (self.height * self.tleg.GetNRows()) - 0.01)
        else:
            y2 = self.tleg.GetY2()
            self.tleg.SetY1(y2 - (self.height * self.tleg.GetNRows()) - 0.01)
    

#------------------------------------------------------------
class TopLegend(object):
    """Legend designed to fit in the space above the plot
   
    If *rowmax* is specified, legend will expand number of columns to fit 
    new entries. 
    If *colmax* is specified, legend will expand number of rows to fit 
    new entries.

    :param rowmax: maximum number of rows in legend 
    :type rowmax: int
    :param colmax: maximum number of columns in legend 
    :type colmax: int
    :param y1: bottom edge of legend
    :type y1: float
    :param cushion: size of buffer space for legend border 
    :type cushion: float 

    """ 

#______________________________________________________________________________
    def __init__(self, 
            rowmax=None,
            colmax=None,
            y1=None, 
            cushion=None,
            ):
        self.rowmax = rowmax or 2
        self.colmax = colmax or 2
        self.textsizemax = 20
        # set dimensions
        cushion = cushion or 0.02
        x1 = 0.2
        x2 = 0.9
        y1 = y1 or 0.9
        y2 = 1.0
        y1+=cushion
        y2-=cushion
        
        # build TLegend
        self.tleg = TLegend(x1, y1, x2, y2)
        self.tleg.SetBorderSize(0)
        self.tleg.SetFillColor(0)
        self.tleg.SetFillStyle(0)
        self.tleg.SetTextFont(43)
        self.tleg.SetTextSize(self.textsizemax)
        #if colmax: self.tleg.SetNColumns(colmax)
        self._nentries=0
#______________________________________________________________________________
    def AddEntry(self, obj, label='', option='P'):
        """Add entry to legend and resize accordingly

        :param obj: object corresponding to new entry
        :type obj: ROOT drawable object (eg :class:`ROOT.TH1` or :class:`ROOT.TGraph`)
        :param label: name of entry in legend
        :type label: str
        :param option: legend option 
        :type option: str [allowed "F","P","L"]
        """
        self._nentries+=1
        self.resize()
        self.tleg.AddEntry(obj, label, option)
#______________________________________________________________________________
    def Draw(self):
        """Draw the legend"""
        #self.tleg.SetTextSize(self.textsizemax)
        self.tleg.Draw()
        

#______________________________________________________________________________
    def resize(self):
        """Resize the legend"""
        #if self._nentries<3: 
        #    self.tleg.SetTextSize(self.textsizemax)
        n = self._nentries
        if self.colmax:
            self.tleg.SetNColumns(min(self.colmax, n))
        else: 
            row = self.rowmax
            ncol = (n+n%row)/row
            self.tleg.SetNColumns(ncol)
            

# - - - - - - - - - - function defs - - - - - - - - - - - - #
#____________________________________________________________
def build_legend(hists, labels, opts, type="top", **kwargs):
    """Creates a legend of given *type* from a list of hists (or graphs)

    *type* options:

    - "meta": :class:`MetaLegend`
    - "top": :class:`TopLegend`
    
    :param hists: objects corresponding to legend entries
    :type hists: list of drawable objects (eg :class:`ROOT.TH1` or :class:`ROOT.TGraph`)
    :param labels: entry names
    :type labels: str list
    :param opts: legend options for entries 
    :type opts: str list [allowed "F","P","L"]
    :param type: legend type 
    :type type: str 
    :param kwargs: key-word arguments passed to :class:`MetaLegend`
    :type kwargs: key-word arguments 
    :rtype: :class:`MetaLegend`

    """
    assert len(hists) == len(labels) == len(opts), "hists, labels, opts incompatible in 'build_legend'"
    assert type in ["meta", "top"], f"invalid type {type} in 'build_legend'"
    if type == "meta": leg = MetaLegend(**kwargs)
    if type == "top": leg = TopLegend(**kwargs)
    for h, lab, opt in zip(hists, labels, opts):
        leg.AddEntry(h, label=lab, option=opt)
    return leg

## EOF
