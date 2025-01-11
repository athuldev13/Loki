# encoding: utf-8
"""
loki.core.hist
~~~~~~~~~~~~~~

This module provides the definitions of the RootDrawable objects.  

"""
__author__    = "Will Davey"
__email__     = "will.davey@cern.ch"
__created__   = "2012-11-04"
__copyright__ = "Copyright 2012 Will Davey"
__license__   = "GPL http://www.gnu.org/licenses/gpl.html"



## modules
import ROOT
from loki.core.histutils import make_eff, get_profile, integral, normalize
from loki.core.histutils import full_integral, create_roc_graph, divide_graphs
from loki.core.histutils import divide_hists, histargs
from loki.core.logger import log
from loki.core.style import default_style
from loki.common.vars import dummyvar, effvar

# - - - - - - - - - - - class defs  - - - - - - - - - - - - #

#------------------------------------------------------------
class RootDrawable():
    """Abstract base class for all ROOT drawable objects

    The function ``build_rootobj`` should be overridden in the 
    derived class with the specific implementation to construct 
    the ROOT drawable object. 
    
    The ROOT drawable object can be constructed from sub-drawables 
    (eg. the efficiency graph class :class:`EffProfile` is constructed 
    by drawing the pass and total hists and dividing them). 
    Sub-drawables should be declared in the constructor, eg::
     
        self.add_subrd(h_pass)
        self.add_subrd(h_total)   
    
    If *yvar* (*zvar*) is specified, will function as a 2D (3D) object. 
    The y-axis range will be set to the yvar range when drawing.
    
    :param xvar: x-axis variable view
    :type xvar: :class:`loki.core.var.View`
    :param yvar: y-axis variable view
    :type yvar: :class:`loki.core.var.View`
    :param zvar: z-axis variable view
    :type zvar: :class:`loki.core.var.View`            
    :param sty: style
    :type sty: :class:`loki.core.style.Style`
    :param name: name
    :type name: str
    :param stackable: whether it can be added to a :class:`ROOT.THStack`
    :type stackable: bool
    :param drawopt: default draw option
    :type drawopt: str
    :param noleg: don't put in legend (default: False)
    :type noleg: bool
    """
    #____________________________________________________________
    def __init__(self,xvar=None,yvar=None,zvar=None,sty=None,name=None,
                 stackable=False,drawopt=None,noleg=False):
        # config
        self.xvar = xvar
        self.yvar = yvar
        self.zvar = zvar
        self.sty = sty or default_style()
        self.name = name    
        self.stackable = stackable
        self.drawopt = drawopt
        self.noleg = noleg

        # members
        self._rootobj = None
        self._subrds = []
        self._extra_labels = []

    #____________________________________________________________
    def draw(self):
        """Draw the ROOT object on canvas with chosen options"""
        # base draw option
        drawopts = ["SAME"]
        # add draw option from style if specified
        if self.sty and self.sty.drawopt: 
            drawopts += [self.sty.drawopt]
        elif self.drawopt: 
            drawopts += [str(self.drawopt)]
        # check for _rootobj
        if not self._rootobj: 
            log().warn(f"{self.name} trying to draw null rootobj! Skipping...")
            return None
        
        drawopt = ",".join(drawopts)
        return self._rootobj.Draw(drawopt)
 
    #____________________________________________________________
    def rootobj(self):
        """Returns the raw ROOT drawable object 
        :rtype: :class:`ROOT.TH1` or :class:`ROOT.TGraph` (or derivatives)
        """
        return self._rootobj

    #____________________________________________________________
    def set_rootobj(self,o):
        """Setter for raw ROOT drawable object
        
        :param o: root drawable object
        :type o: :class:`ROOT.TH1` or :class:`ROOT.TGraph` (or derivative)
        """
        if not o: 
            log().warn(f"{self.name} trying to set null rootobj!")
            return
        if self.sty: self.sty.apply(o)
        self._rootobj = o

    #____________________________________________________________
    def is_valid(self):
        """Returns true if rootobj is valid (not None)"""
        return (self._rootobj is not None)

    #____________________________________________________________
    def add_subrd(self,rd):
        """Declare sub drawable object
        
        :param rd: sub drawable object
        :type rd: :class:`RootDrawable`
        """
        self._subrds.append(rd)

    #____________________________________________________________
    def write(self,f):
        """Write ROOT objects to file
        
        :param f: file
        :type f: :class:`ROOT.TFile`
        """
        if not f.Get(self._rootobj.GetName()): 
            f.WriteTObject(self._rootobj)
        for o in self._subrds: 
            o.write(f)

    #____________________________________________________________
    def get_component_hists(self):
        """Return list of component hists
        
        Recursively calls through sub :class:`RootDrawable` objects yielding 
        objects of derived type :class:`Hist`
        
        :rtype: list :class:`Hist`
        """
        hists = []
        for rd in self._subrds:
            hists += rd.get_component_hists()
        return hists
    
    #____________________________________________________________
    def build_rootobj(self):
        """Build the ROOT object to be drawn
        
        Should be overridden in derived class with specific implementation
        to construct drawable object
        """
        pass

    #____________________________________________________________
    def get_xtitle(self):
        """Returns the x-axis title
        
        Default is to use x-title from x-variable.
        Can be overridden for specific implementations (eg. ''Efficiency'')

        :rtype: str
        """
        return self.xvar.get_xtitle()

    #____________________________________________________________
    def get_ytitle(self):
        """Returns the y-axis title
        
        Default is to use y-title from x-variable (ie Events / bin width)
        Can be overridden for specific implementations (eg. ''Efficiency'')

        :rtype: str
        """
        return self.xvar.get_ytitle()

    #____________________________________________________________
    def get_dimension(self):
        """Returns the dimension of the object
        
        :rtype: int
        """
        if self.yvar is not None: return 2
        return 1


#------------------------------------------------------------
class Hist(RootDrawable):
    """Class for 1D/2D/3D histograms
    
    :param sample: input event sample
    :type sample: :class:`loki.core.sample.Sample`
    :param xvar: x-axis varaible view
    :type xvar: :class:`loki.core.var.View`
    :param yvar: y-axis varaible view (for 2D hists)
    :type yvar: :class:`loki.core.var.View`
    :param zvar: z-axis varaible view (for 3D hists)
    :type zvar: :class:`loki.core.var.View`    
    :param sel: selection
    :type sel: :class:`loki.core.var.VarBase`
    :param weight: weight expression
    :type weight: :class:`loki.core.var.VarBase`
    :param normalize: normalize the histogram integral to unity
    :type normalize: bool
    :param sty: style
    :type sty: :class:`loki.core.style.Style`
    :param kwargs: key-word arguments passed to :class:`RootDrawable`
    :type kwargs: key-word arguments 
    """
    #____________________________________________________________
    def __init__(self,sample=None,xvar=None,yvar=None,zvar=None, 
                 sel=None,weight=None,normalize=False,sty=None,
                 **kwargs):
        RootDrawable.__init__(self,xvar=xvar,yvar=yvar,zvar=zvar,
                              sty=sty or sample.sty, 
                              stackable=True,
                              drawopt = "COL" if yvar else "",
                              **kwargs)
        # config
        self.sample = sample
        self.sel = sel
        self.weight = weight
        self.normalize = normalize
    
        if (yvar and not xvar) or (zvar and not (xvar and yvar)): 
            log().warn(f"Malformed hist: {self.name}")
    
    #____________________________________________________________
    def new_hist(self,name=None):
        """Return empty TH1F/TH2F/TH3F for xvar/yvar/zvar"""
        if name is None: name = self.name
        return self.xvar.new_hist(yvar=self.yvar, zvar=self.zvar, name = name)

    #____________________________________________________________
    def histargs(self,name=None):
        """Returns list of arguments for :func:`loki.core.histutils.new_hist`"""
        return histargs(self.xvar,self.yvar,self.zvar,name=name)
     
    #____________________________________________________________
    def get_component_hists(self):
        """Returns itself in list"""
        return [self]

    #____________________________________________________________
    def build_rootobj(self):
        """Postprocess the histogram object"""
        if self.normalize: 
            normalize(self._rootobj)

    #____________________________________________________________
    def get_ytitle(self):
        """Returns y-axis title for hist"""
        if self.yvar is not None: 
            return self.yvar.get_xtitle()
        return self.xvar.get_ytitle()


#------------------------------------------------------------
class HistProxy(RootDrawable):
    """Class for performing mathematical operations on histograms

    The class will generate a 'proxy' histogram from a repeated
    mathematical operation (*op*) on a list of input histograms
    (*hists*).

    :param hists: histogram objects
    :type hists: :class:`loki.core.hist.Hist` or :class:`loki.core.hist.HistProxy`
    :param op: operation (\+, \-, \*, \/)
    :type op: str
    :param sty: style
    :type sty: :class:`loki.core.style.Style`
    :param owner: own the input histograms
    :type owner: bool
    :param kwargs: key-word arguments passed to :class:`RootDrawable`
    :type kwargs: key-word arguments
    """

    # ____________________________________________________________
    def __init__(self, hists=None, op=None, sty=None, **kwargs):
        h0 = hists[0]
        RootDrawable.__init__(self, xvar=h0.xvar, sty=sty or h0.sty,
                              drawopt=h0.drawopt, stackable=True, **kwargs)
        self.hists = hists
        self.op = op
        for h in hists:
            for o in h.get_component_hists():
                self.add_subrd(o)

        allowed_ops = ['+', '-', '*', '/']
        assert op in allowed_ops, f"HistProxy invalid operator: {op}, must be in {allowed_ops}"

    # ____________________________________________________________
    def build_rootobj(self):
        """Build the ratio graph"""
        # process inputs
        for h in self.hists: h.build_rootobj()
        #if self.owner:
        #    # if owner, need to explicitly build the root objects
        #    for h in self.hists: h.build_rootobj()
        #else:
        #    # otherwise they should have been built prior
        #    # TODO: can break if order wrong, implement job sequence awareness?
        #    for h in self.hists:
        #        if not h.is_valid():
        #            log().error("Inputs for HistProxy not available, make sure they're scheduled")
        #            return

        # construct root drawable
        h0 = self.hists[0]
        hname = self.name or f"h_proxy_{h0.name}"
        ro = self.hists[0].rootobj().Clone(hname)
        for h_i in self.hists[1:]:
            ro_i = h_i.rootobj()
            if ro_i.GetNbinsX() == ro.GetNbinsX():
                if   self.op == '+': ro.Add(ro_i)
                elif self.op == '-': ro.Add(ro_i, -1)
                elif self.op == '*': ro.Multiply(ro_i)
                elif self.op == '/': ro.Divide(ro_i)
            elif ro_i.GetNbinsX() == 1:
                if   self.op == '*': ro.Scale(ro_i.Integral())
                elif self.op == '/': ro.Scale(1. / ro_i.Integral())
                else:
                    log().error(f"Invalid HistProxy scalar operation: {self.op}, must be * or /")
                    return
            else:
                log().error("Incompatible bins in HistProxy")
                return
        self.set_rootobj(ro)

    # ____________________________________________________________
    def get_ytitle(self):
        """Returns y-axis title for ratio"""
        return self.hists[0].get_ytitle()


        #------------------------------------------------------------
class Profile(RootDrawable):
    """Class for variable profiles
        
    Uses Hist to build TH2 and then retrieves profile.
        
    :param sample: input event sample
    :type sample: :class:`loki.core.sample.Sample`
    :param xvar: dependent variable view
    :type xvar: :class:`loki.core.var.View`
    :param yvar: resolution/closure variable view  
    :type yvar: :class:`loki.core.var.View`
    :param sel: selection 
    :type sel: :class:`loki.core.var.VarBase`
    :param weight: weight expression
    :type weight: :class:`loki.core.var.VarBase`
    :param kwargs: key-word arguments passed to :class:`RootDrawable`
    :type kwargs: key-word arguments         
    """
    #____________________________________________________________
    def __init__(self,sample=None,xvar=None,yvar=None,sel=None,
                 weight=None,sty=None,**kwargs):
        RootDrawable.__init__(self,xvar=xvar,sty=sty or sample.sty,
                              drawopt="P,E1", **kwargs)
        # config
        #self.yvar = yvar #TODO: remove
        
        # members
        self.h2 = Hist(sample=sample,xvar=xvar,yvar=yvar,sel=sel,weight=weight)
        self.add_subrd(self.h2)
 
    #____________________________________________________________
    def build_rootobj(self):
        """Build the resolution profile"""
        pname = f"p_{self.name}_{self.h2.xvar.name}_{self.h2.yvar.name}"
        profile = self.h2.rootobj().ProfileX(pname)
        self.set_rootobj(profile)

    #____________________________________________________________
    def get_ytitle(self):
        """Returns y-axis title for profile"""
        return f"<{self.h2.yvar.get_xtitle()}>"

    #____________________________________________________________
    def fit(self):
        """Fit profile with pol1 function"""
        p = self.rootobj()
        fname = f"f_{self.name}_{self.h2.xvar.name}_{self.h2.yvar.name}"
        f = ROOT.TF1(fname,"[0] + [1]*x",self.xvar.get_xmin(),self.xvar.get_xmax())
        f.SetParameter(0,p.GetMean(2))
        f.SetParameter(1,0.0)
        p.Fit(f,"R")
        self._fit = f

                       
#------------------------------------------------------------
class EffProfile(RootDrawable):
    """Class for efficiency profiles
    
    The class will generate an efficiency graph for the defined
    numerator (*sel_pass*) and denominator (*sel_total*)
    selection. The efficiency is plotted as a function of the 
    dependent variable (*var_total* and *var_pass*). The efficiency 
    is calculated by generating histograms for the numerator and the 
    denominator and then dividing them using the Bayes divide method. 
    
    Note: the numerator and denominator are drawn separately, 
    and if the denominator is defined using truth objects
    (eg. truth-tau visible pT), *xvar_total* must be specified 
    (as different from *xvar*, eg. reco-tau match visible pT). 
    For convenience, any variables that have truth-level 
    counterparts, store the counterpart in the *truth_partner*
    attribute. This varible is used to draw the denominator, which loops 
    over truth objects (truth taus in the denominator and reco taus 
    in the numerator).  
    
    :param sample: input event sample
    :type sample: :class:`loki.core.sample.Sample`
    :param xvar: x-axis variable view
    :type xvar: :class:`loki.core.var.View`
    :param xvar_total: x-axis variable view for denominator if needed (for eff w.r.t. truth)
    :type xvar_total: :class:`loki.core.var.View`
    :param sel_pass: numerator selection 
    :type sel_pass: :class: `loki.core.var.VarBase`
    :param sel_total: denominator selection 
    :type sel_total: :class:`loki.core.var.VarBase`
    :param weight: weight expression
    :type weight: :class:`loki.core.var.VarBase`
    :param sty: style
    :type sty: :class:`loki.core.style.Style`
    :param kwargs: key-word arguments passed to :class:`RootDrawable`
    :type kwargs: key-word arguments     
    """
    #____________________________________________________________
    def __init__(self, sample=None, 
                 xvar=None, xvar_total=None,
                 sel_pass=None, sel_total=None,
                 weight=None, sty=None, **kwargs):
        RootDrawable.__init__(self,xvar=xvar,sty=sty or sample.sty,
                              drawopt="P,E1",**kwargs)
        if xvar_total is None: xvar_total = xvar
        # members
        self.h_pass  = Hist(sample=sample, xvar=xvar,       sel=sel_pass,  weight=weight, name=f"{self.name}Pass")
        self.h_total = Hist(sample=sample, xvar=xvar_total, sel=sel_total, weight=weight ,name=f"{self.name}Total")
        self.add_subrd(self.h_pass)
        self.add_subrd(self.h_total)
 
    #____________________________________________________________
    def build_rootobj(self):
        """Build the efficiency graph"""
        ## create efficiency graph
        #g = make_eff_graph(self.h_pass.rootobj(),self.h_total.rootobj(),self.name)
        g = make_eff(self.h_pass.rootobj(),self.h_total.rootobj(),self.name)
        self.set_rootobj(g)
        npass  = integral(self.h_pass.rootobj())
        ntotal = integral(self.h_total.rootobj())
        eff = npass / ntotal if ntotal else 0.0
        log().debug(f"{self.name} efficiency: {eff:.3f}")
    
    #____________________________________________________________
    def get_ytitle(self):
        """Returns y-axis title for efficiency profiles"""
        return "Efficiency" 


#------------------------------------------------------------
class ROCCurve(RootDrawable):
    """Class for ROC curves
    
    The class will generate an efficiency graph for the defined
    numerator (*sel_pass*) and denominator (*sel_total*)
    selection. The efficiency is plotted as a function of the 
    dependent variable (*var_total* and *var_pass*). The efficiency 
    is calculated by generating histograms for the numerator and the 
    denominator and then dividing them using the Bayes divide method. 
    
    Note: the numerator and denominator are drawn separately, 
    and if the denominator is defined using truth objects
    (eg. truth-tau visible pT), *xvar_total* must be specified 
    (as different from *xvar*, eg. reco-tau match visible pT). 
    For convenience, any variables that have truth-level 
    counterparts, store the counterpart in the *truth_partner*
    attribute. This varible is used to draw the denominator, which loops 
    over truth objects (truth taus in the denominator and reco taus 
    in the numerator).  
    
    :param sample: input signal sample
    :type sample: :class:`loki.core.sample.Sample`
    :param bkg: input background sample
    :type bkg: :class:`loki.core.sample.Sample`
    :param xvar: discriminant variable view
    :type xvar: :class:`loki.core.var.View`
    :param sel_sig: signal selection
    :type sel_sig: :class: `loki.core.var.VarBase`
    :param sel_sig_total: signal denominator selection (if different from numerator) 
    :type sel_sig_total: :class:`loki.core.var.VarBase`
    :param sel_bkg: background selection
    :type sel_bkg: :class: `loki.core.var.VarBase`
    :param reverse: force cut to be in reverse (default: auto determined)
    :type reverse: bool
    :param weight: weight expression
    :type weight: :class:`loki.core.var.VarBase`
    :param sty: style
    :type sty: :class:`loki.core.style.Style`
    :param kwargs: key-word arguments passed to :class:`RootDrawable`
    :type kwargs: key-word arguments     
    """
    #____________________________________________________________
    def __init__(self, sample=None,bkg=None, 
                 xvar=None, 
                 sel_sig=None, sel_sig_total=None, 
                 sel_bkg=None,
                 reverse = None,
                 weight=None, sty=None, **kwargs):
        RootDrawable.__init__(self,xvar=effvar.get_view(),sty=sty or sample.sty,
                              drawopt="L",**kwargs)
        # members
        self.h_sig = Hist(sample=sample, xvar=xvar, sel=sel_sig, weight=weight, name=f"{self.name}Sig")
        self.h_bkg = Hist(sample=bkg,    xvar=xvar, sel=sel_bkg, weight=weight, name=f"{self.name}Bkg")
        self.h_sig_total = None            
        self.add_subrd(self.h_sig)
        self.add_subrd(self.h_bkg)
        if sel_sig_total: 
            self.h_sig_total = Hist(sample=sample, xvar=dummyvar.get_view(), sel=sel_sig_total, weight=weight, name=f"{self.name}SigTotal")
            self.add_subrd(self.h_sig_total)
        self.reverse = reverse            
            
    #____________________________________________________________
    def build_rootobj(self):
        """Build the ROC curve"""
        ## normalize inputs correctly
        if self.h_sig_total: 
            total = full_integral(self.h_sig_total.rootobj())
            if total: self.h_sig.rootobj().Scale(1. / total )
        else:
            normalize(self.h_sig.rootobj()) 
        normalize(self.h_bkg.rootobj())        
        
        ## auto determine if reverse cut required
        if self.reverse is None: 
            if self.h_sig.rootobj().GetMean() < self.h_bkg.rootobj().GetMean(): 
                self.reverse = True
            else:
                self.reverse = False
        
        ## create ROC curve
        g = create_roc_graph(self.h_sig.rootobj(), self.h_bkg.rootobj(), 
                             effmin=0.05, name=self.name,normalize=False,
                             reverse=self.reverse)
        self.set_rootobj(g)

    #____________________________________________________________
    def get_xtitle(self):
        """Returns the x-axis title for ROC curve"""
        return "Efficiency"
    
    #____________________________________________________________
    def get_ytitle(self):
        """Returns y-axis title for ROC curve"""
        return "Rejection" 


#------------------------------------------------------------
class ResoProfile(RootDrawable):
    """Class for resolution/closure profiles
        
    The class will generate a resolution/closure profile graph
    of the residual (*yvar*) plotted as a function of the 
    dependent variable (*xvar*). 
    The resolution profile is calculated by generating a 
    2D histogram of resolution vs dependent variable, 
    slicing in bins of the dependent variable and then 
    calculating the resolution/closure in each slice. 
    The method of the resolution/closure calculation can 
    be specified by *mode*. 
 
    Available options are:  
         
    - median
    - mode
    - winmode (sliding window mode, w=0.05)
    - rms
    - core (quantile_width with cl=0.68)
    - tail (quantile_width with cl=0.95)
    - core_band (quantile_width_and_error with cl=0.68)
    - tail_band (quantile_width_and_error with cl=0.95)
    - fit_width
    - fit_mean

    They correspond to particular configurations passed to 
    :func:`loki.core.histutils.get_profile`

    :param sample: input event sample
    :type sample: :class:`loki.core.sample.Sample`
    :param xvar: dependent variable view
    :type xvar: :class:`loki.core.var.View`
    :param yvar: resolution/closure variable view
    :type yvar: :class:`loki.core.var.View`
    :param sel: selection 
    :type sel: :class:`loki.core.var.VarBase`
    :param weight: weight expression
    :type weight: :class:`loki.core.var.VarBase`
    :param mode: mode to calculate the resolution/closure
    :type mode: str 
    :param kwargs: key-word arguments passed to :class:`RootDrawable`
    :type kwargs: key-word arguments         
    """
    #____________________________________________________________
    def __init__(self,sample=None,xvar=None,yvar=None,sel=None,
                 weight=None, mode=None,sty=None,**kwargs):
        RootDrawable.__init__(self,xvar=xvar,sty=sty or sample.sty,
                              drawopt="P,E1", **kwargs)
        # config
        self.mode = mode
        #self.yvar = yvar #TODO: remove
        
        # members
        self.h2 = Hist(sample=sample,xvar=xvar,yvar=yvar,sel=sel,weight=weight)
        self.add_subrd(self.h2)
        self.mode_names = {
                "median"   : "Linearity (Med)",
                "mode"     : "Linearity (MPV)",
                "winmode"  : "Linearity (wMPV)",
                "rms"      : "Resolution (RMS)",
                "core"     : "Resolution (68)",
                "tail"     : "Resolution (95)", 
                "core_err" : "Resolution (68)",
                "tail_err" : "Resolution (95)",
                "fit_width": "Resolution (Fit)",
                "fit_mean" : "Linearity (Fit)",
                }
        assert mode in self.mode_names, f"Invalid mode {mode}"
 
    #____________________________________________________________
    def build_rootobj(self):
        """Build the resolution profile"""
        ## create efficiency graph
        gname = f"g_{self.name}_{self.h2.xvar.name}_{self.h2.yvar.name}_{self.mode}"
        h2 = self.h2.rootobj() 
        if   self.mode == "median":  
            g = get_profile(h2,"median",name=gname)
        elif self.mode == "mode":  
            g = get_profile(h2,"mode",name=gname)
        elif self.mode == "winmode":  
            g = get_profile(h2,"window_mode",name=gname)
        elif self.mode == "rms":  
            g = get_profile(h2,"rms",name=gname)
        elif self.mode == "core":  
            g = get_profile(h2,"quantile_width",name=gname,cl=0.68)
        elif self.mode == "tail":  
            g = get_profile(h2,"quantile_width",name=gname,cl=0.95)
        elif self.mode == "core_err":  
            g = get_profile(h2,"quantile_width_and_error",name=gname,cl=0.68)
        elif self.mode == "tail_err":  
            g = get_profile(h2,"quantile_width_and_error",name=gname,cl=0.95)
        elif self.mode == "fit_width":  
            g = get_profile(h2,"fit_width",name=gname)
        elif self.mode == "fit_mean":  
            g = get_profile(h2,"fit_mean",name=gname)
        self.set_rootobj(g)

    #____________________________________________________________
    def get_ytitle(self):
        """Returns y-axis title for reso profiles"""
        return f"{self.h2.yvar.get_short_title()} {self.mode_names[self.mode]}"


#------------------------------------------------------------
class MigrationMatrix(RootDrawable):
    """Class for classification migration matrices

    TODO: write description
        
    The class will generate a resolution/closure profile graph
    of the residual (*yvar*) plotted as a function of the 
    dependent variable (*xvar*). 
    The resolution profile is calculated by generating a 
    2D histogram of resolution vs dependent variable, 
    slicing in bins of the dependent variable and then 
    calculating the resolution/closure in each slice. 
    The method of the resolution/closure calculation can 
    be specified by *mode*. 
 
    Available options are:  
         
    - median
    - mode
    - winmode (sliding window mode, w=0.05)
    - rms
    - core (quantile_width with cl=0.68)
    - tail (quantile_width with cl=0.95)
    - core_band (quantile_width_and_error with cl=0.68)
    - tail_band (quantile_width_and_error with cl=0.95)
    - fit_width
    - fit_mean

    They correspond to particular configurations passed to 
    :func:`loki.core.histutils.get_profile`

    :param sample: input event sample
    :type sample: :class:`loki.core.sample.Sample`
    :param xvar: dependent variable view
    :type xvar: :class:`loki.core.var.View`
    :param yvar: resolution/closure variable view
    :type yvar: :class:`loki.core.var.View`
    :param sel: selection 
    :type sel: :class:`loki.core.var.VarBase`
    :param weight: weight expression
    :type weight: :class:`loki.core.var.VarBase`
    :param mode: mode to calculate the resolution/closure
    :type mode: str 
    :param kwargs: key-word arguments passed to :class:`RootDrawable`
    :type kwargs: key-word arguments         
    """
    #____________________________________________________________
    def __init__(self,sample=None,xvar=None,yvar=None,sel=None,
                 weight=None, rownorm=False, **kwargs):
        RootDrawable.__init__(self,xvar=xvar,yvar=yvar,drawopt="COL,TEXT",**kwargs)
        # config
        self.rownorm = rownorm
        
        # members
        self.h2 = Hist(sample=sample,xvar=xvar,yvar=yvar,sel=sel,weight=weight)
        self.add_subrd(self.h2)
        self.diagonal = 0.0
    #____________________________________________________________
    def build_rootobj(self):
        """Build the resolution profile"""
        ## create efficiency graph
        h2 = self.h2.rootobj()
        tag = "RowNorm" if self.rownorm else "ColNorm"
        hname = f"h_{self.name}_{self.h2.xvar.name}_{self.h2.yvar.name}_{tag}"
        h = h2.Clone(hname)
        h.SetMarkerSize(2.0)
        h.SetMinimum(0.)
        h.SetMaximum(100.)
        
        # diagonal fraction
        if h.Integral():
            size = min(h.GetNbinsX(),h.GetNbinsY())
            diag = sum([h.GetBinContent(i+1,i+1) for i in range(size)])
            tot  = sum([h.GetBinContent(i+1,j+1) for i in range(size) for j in range(size)])
            if tot: 
                self.diagonal = diag / tot * 100.0 
        
        if self.rownorm:
            for iy in range(1,h.GetNbinsY()+1):
                total = sum([h.GetBinContent(ix,iy) for ix in range(1,h.GetNbinsX()+1)])
                for ix in range(1,h.GetNbinsX()+1):
                    if not total: 
                        n = en = 0.0
                    else:
                        n = h.GetBinContent(ix,iy) / total * 100.0
                        en = h.GetBinError(ix,iy) / total * 100.0
                    h.SetBinContent(ix,iy,n)
                    h.SetBinError(ix,iy,en)
        else:
            for ix in range(1,h.GetNbinsX()+1):
                total = sum([h.GetBinContent(ix,iy) for iy in range(1,h.GetNbinsY()+1)])
                for iy in range(1,h.GetNbinsY()+1):
                    if not total: 
                        n = en = 0.0
                    else:
                        n = h.GetBinContent(ix,iy) / total * 100.0
                        en = h.GetBinError(ix,iy) / total * 100.0
                    h.SetBinContent(ix,iy,n)
                    h.SetBinError(ix,iy,en)

        # build extra labels
        self._extra_labels += [f"Diagonal: {self.diagonal:.1f}%"]
        if self.rownorm: self._extra_labels.append("Purity")
        else:            self._extra_labels.append("Efficiency")
        
        self.set_rootobj(h)

    #____________________________________________________________
    def get_ytitle(self):
        """Returns y-axis title for migration matrices"""
        return str(self.yvar.get_xtitle())



#------------------------------------------------------------
class Ratio(RootDrawable):
    """Class for ratios
    
    The class will generate a ratio between the numerator
    (*rd_num*) and denominator (*rd_den*) RootDrawable 
    objects. The underlying drawables can be both TGraph or 
    both TH1, but not a mixture.   
    
    :param rd_num: numerator object
    :type rd_num: :class:`loki.core.hist.RootDrawable`
    :param rd_den: denominator object
    :type rd_den: :class:`loki.core.hist.RootDrawable` 
    :param sty: style
    :type sty: :class:`loki.core.style.Style`
    :param owner: own the input histograms
    :type owner: bool 
    :param kwargs: key-word arguments passed to :class:`RootDrawable`
    :type kwargs: key-word arguments     
    """
    #____________________________________________________________
    def __init__(self, rd_num = None, rd_den = None, sty = None, owner = False, **kwargs):
        RootDrawable.__init__(self, xvar = rd_num.xvar, sty = sty or rd_num.sty,
                              drawopt=rd_num.drawopt,**kwargs)
        self.rd_num = rd_num
        self.rd_den = rd_den
        self.owner = owner
        if owner: 
            self.add_subrd(rd_num)
            self.add_subrd(rd_den)
 
    #____________________________________________________________
    def build_rootobj(self):
        """Build the ratio graph"""
        # process inputs
        if self.owner: 
            # if owner, need to explicitly build the root objects
            self.rd_num.build_rootobj()
            self.rd_den.build_rootobj()
        else:
            # otherwise they should have been built prior
            # TODO: can break if order wrong, implement job sequence awareness?
            if not self.rd_num.is_valid(): 
                log().error("Inputs for Ratio not available, make sure they're scheduled")
                return
            if not self.rd_den.is_valid(): 
                log().error("Inputs for Ratio not available, make sure they're scheduled")
                return

        # construct root drawable
        g_num = self.rd_num.rootobj()
        g_den = self.rd_den.rootobj()
        gname = self.name or f"g_ratio_{self.rd_num.name}"
        if isinstance(g_num, ROOT.TH1): g_num = ROOT.TGraphErrors(g_num)
        if isinstance(g_den, ROOT.TH1): g_den = ROOT.TGraphErrors(g_den)
        g = divide_graphs(g_num,g_den,gname)
        self.set_rootobj(g)
    
    #____________________________________________________________
    def get_ytitle(self):
        """Returns y-axis title for ratio"""
        return "Ratio"


#------------------------------------------------------------
class Fit(RootDrawable):
    """Class for fits
    
    Performs a fit to a RootDrawable object (*rd*). The function is defined
    by the expression *expr*. 

    :param rd: object to fit
    :type rd: :class:`loki.core.hist.RootDrawable`
    :param expr: fit function formula 
    :type expr: str
    :param owner: own the input root drawable object
    :type owner: bool 
    :param sty: style
    :type sty: :class:`loki.core.style.Style`
    :param kwargs: key-word arguments passed to :class:`RootDrawable`
    :type kwargs: key-word arguments         
    """
    #____________________________________________________________
    def __init__(self,rd=None, expr=None, owner=None, sty=None, **kwargs):
        RootDrawable.__init__(self,xvar=rd.xvar,sty=sty or rd.sty, drawopt="L", **kwargs)
        # config
        self.rd = rd
        self.expr = expr
        self.owner = owner
        
        # members
        if owner: 
            self.add_subrd(rd)
 
    #____________________________________________________________
    def build_rootobj(self):
        """Build the resolution profile"""        
        # process inputs
        if self.owner: 
            # if owner, need to explicitly build the root objects
            self.rd.build_rootobj()
        else:
            # otherwise they should have been built prior
            # TODO: can break if order wrong, implement job sequence awareness?
            if not self.rd.is_valid(): 
                log().error("Inputs for Fit not available, make sure they're scheduled")
                return
        h = self.rd.rootobj()
                
        # create fit function
        fname = self.name or f"f_fit_{self.rd.name}"
        f = ROOT.TF1(fname,self.expr,self.xvar.get_xmin(),self.xvar.get_xmax())
        # TODO: implement configurabel fitting range
        # TODO: implement configurable starting parameter values
        h.Fit(f,"R")
        self.set_rootobj(f)

    #____________________________________________________________
    def get_ytitle(self):
        """Returns y-axis title for profile"""
        return self.rd.get_ytitle()


## EOF
