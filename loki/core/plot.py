# encoding: utf-8
"""
loki.core.plot
~~~~~~~~~~~~~~

This module provides implementation of plot classes designed to draw complete
canvases, including the histograms/graphs, legends, and text decorations.

The base class :class:`Plot` does the drawing of the canvas and decorations,
providing a uniform style. 

The derived classes provide an easy interface to generate the input ROOT
drawable objects, such as histograms, efficiency graphs, resolution graphs,
etc.

"""
__author__    = "Will Davey"
__email__     = "will.davey@cern.ch"
__created__   = "2016-02-21"
__copyright__ = "Copyright 2016 Will Davey"
__license__   = "GPL http://www.gnu.org/licenses/gpl.html"

## modules
import os
import ROOT
import loki
import loki.core.histutils as histutils
import loki.core.legend as legend
from loki.core.hist import Ratio
from loki.core.logger import log

# - - - - - - - - - - - class defs  - - - - - - - - - - - - #
#------------------------------------------------------------
class Plot():
    """Base plotting class.

    This is where the magic happens.

    :param name: unique identifier 
    :type name: str
    :param rds: ROOT drawable objects
    :type rds: list :class:`loki.core.hist.RootDrawable`
    :param stack_rds: hists to add to stack
    :type stack_rds: list :class:`loki.core.hist.Hist`
    :param square: make canvas square
    :type square: bool
    :param ymin: y-axis minimum value (to override default)
    :type ymin: float
    :param ymax: y-axis maximum value (to override default)
    :type ymax: float
    :param ytitle: title of the y-axis (to override default)
    :type ytitle: str
    :param logy: use log scale on y-axis
    :type logy: bool
    :param rmin: ratio minimum value (to override default)
    :type rmin: float
    :param rmax: ratio maximum value (to override default)
    :type rmax: float    
    :param fexts: file extensions to save (eg. "pdf")
    :type fexts: str list
    :param topmargin: space at top reserved for legend
    :type topmargin: float
    :param atlas_label: text to accompany "ATLAS" label (if None, no ATLAS will be drawn)
    :type atlas_label: str
    :param extra_labels: extra text to add to the plot 
    :type extra_labels: str list
    :param stack: stack *rds* (only if *rds* of type :class:`loki.core.hist.Hist`. DEPRECATED, use stack_rds)
    :type stack: bool
    :param stack_normalize: normalize each bin in the stack to unity
    :type stack_normalize: bool
    :param doratio: add ratios of *rds* in the lower panel 
    :type doratio: bool
    :param dir: dir to place canvases 
    :type dir: str
    """
    #____________________________________________________________
    def __init__(self,
                 name,
                 rds = None,
                 stack_rds=None,
                 square = True,
                 ymin = None,
                 ymax = None,
                 ytitle = None,
                 logy = None,                 
                 rmin = None,
                 rmax = None,
                 fexts = None,
                 topmargin = None,
                 atlas_label = "Simulation Internal",
                 extra_labels = None,
                 dologos = True,
                 stack = None,
                 stack_normalize = False,
                 doratio = False,
                 dir = None,
                 ):
        # deprecated option, but keep same functionality
        if stack:
            stack_rds = rds
            rds = None

        # config
        self.name = name
        self.rds = rds or []
        self.stack_rds = stack_rds or []
        self.ymin = ymin
        self.ymax = ymax
        self.ytitle = ytitle
        self.logy = logy
        self.rmin = rmin
        self.rmax = rmax        
        self.ch = 700 if square else 500
        self.cw = 700
        self.fexts = fexts or ["pdf"]
        self.topmargin = topmargin or 0.15
        self.atlas_label = atlas_label
        if extra_labels is not None and not isinstance(extra_labels,list):
            extra_labels = [extra_labels]
        self.extra_labels = extra_labels
        self.stack_normalize = stack_normalize
        self.dologos = dologos
        self.doratio = doratio
        self.dir = dir
        self.rsplit = 0.3
        self.size_title = 32
        self.size_label = 28
        self.font = 43

        # TODO: protect?
        if not (rds or stack_rds):
            log().fatal(f"Plot {name} has not drawable objects")
            exit(1)
        self.rd0 = rds[0] if rds else stack_rds[0]
        self.xvar = self.rd0.xvar
        self.yvar = self.rd0.yvar
        self.canvas = None
        self.leg = None
        self.ratio_rds = []
        
        # create ratios
        if doratio:
            self.__create_ratios__()

    #____________________________________________________________
    def draw(self):
        """Draw and save the plot"""
        if self.no_rds_valid():
            log().warn(f"{self.name} has no valid drawable objects, skipping plot draw.")
            return
        if not self.all_rds_valid():
            log().warn(f"{self.name} has some invalid drawable objects, attempting plot draw anyway.")
        
        # build stack now (incase renormalization affects frame range)
        if self.stack_rds:
            self.__make_stack__()

        # draw canvas
        if self.doratio: 
            self.__draw_ratio__()
        else: 
            self.__draw_standard__()

    #____________________________________________________________
    def write(self,fout):
        """Write ROOT objects to file
        
        Canvas is written directly to file, subobjects written to 
        "hists" dir.
        
        :param fout: file
        :type fout: :class:`ROOT.TFile`
        """
        if self.no_rds_valid():
            log().warn(f"{self.name} has no valid drawable objects, skipping write.")
            return
        if not self.all_rds_valid():
            log().warn(f"{self.name} has some invalid drawable objects, attempting write anyway.")
        
        # create sub-directory
        if self.dir is not None:
            path = self.dir.strip("/")
            if not fout.GetDirectory(path): 
                fout.mkdir(path)
            fout = fout.GetDirectory(path)
        
        if not self.canvas: 
            log().warn(f"{self.name} has no canvas, can't write")
        else:         
            fout.WriteTObject(self.canvas)
        # write sub-objects to hist dir
        hdir = fout.GetDirectory("hists")
        if not hdir: hdir = fout.mkdir("hists")
        for rd in self.rds + self.stack_rds + self.ratio_rds:
            if not rd.is_valid(): continue 
            rd.write(hdir)
        

    #____________________________________________________________
    def get_component_hists(self):
        """Returns a list of hists from the drawables
        
        :rtype: list :class:`loki.core.hist.Hist`
        """
        hists = []
        for rd in self.rds + self.stack_rds + self.ratio_rds:
            hists += rd.get_component_hists()
        return hists
    
    #____________________________________________________________
    def build_rootobj(self):
        """Build ROOT objects for all associated drawables"""
        for rd in self.rds + self.stack_rds + self.ratio_rds:
            rd.build_rootobj()

    #____________________________________________________________
    def all_rds_valid(self):
        """Returns True if all rds valid"""
        return (False not in [r.is_valid() for r in self.rds+self.stack_rds+self.ratio_rds])
    
    #____________________________________________________________
    def no_rds_valid(self):
        """Returns True if no rds valid"""
        return (True not in [r.is_valid() for r in self.rds+self.stack_rds+self.ratio_rds])

    #____________________________________________________________
    def __draw_standard__(self):
        """Underlying draw function for standard single pad plot"""
        log().debug("in Plot.__draw_standard__")
        
        # make the canvas
        log().debug("building canvas...")
        cname = f"c_{self.name}"
        c = ROOT.TCanvas(cname,cname,self.cw,self.ch)  

        if self.dologos:
            self.__make_loki_watermark__(c)
        
        # make upper pad
        p1 = ROOT.TPad("p1","top pad",0.,0.,1.,1.)
        p1.SetTopMargin(self.topmargin)
        p1.SetFillStyle(0)
        p1.SetFrameFillStyle(0)
        p1.Draw()
        p1.cd()
                
        # draw the frame
        log().debug("drawing frame...")
        xtitle = self.rd0.get_xtitle()
        ytitle = self.rd0.get_ytitle()
        p1.fr = self.xvar.frame(p1,
                ymin=self.__get_ymin__(),
                ymax=self.__get_ymax__(),
                xtitle=xtitle,
                ytitle=ytitle,
                yvar = self.yvar,
                )
        xa = p1.fr.GetXaxis()
        ya = p1.fr.GetYaxis()
        self.__set_axis_text_attrs__(xa)
        self.__set_axis_text_attrs__(ya)
        xa.SetTitleOffset(1.6)
        ya.SetTitleOffset(1.7)
                
        # fill canvas
        self.__fill_upper_pad__(p1)        
        
        # save canvas
        self.__save_canvas__(c)
        self.canvas = c
        self.pad1 = p1
        
        log().debug("finished __draw_standard__")

    #____________________________________________________________
    def __draw_ratio__(self):
        """Underlying draw function for ratio plot"""
        if self.no_rds_valid():
            log().warn(f"{self.name} has no valid drawable objects, skipping plot draw.")
            return
        if not self.all_rds_valid():
            log().warn(f"{self.name} has some invalid drawable objects, attempting plot draw anyway.")
        
        # make the canvas
        cname = f"c_{self.name}"
        c = ROOT.TCanvas(cname,cname,self.cw,self.ch)
        
        # make upper pad        
        p1 = ROOT.TPad("p1","top pad",0.0,self.rsplit,1.,1.)
        p1.SetTopMargin(self.topmargin)
        p1.SetBottomMargin(0.02)
        p1.Draw()
        
        # make lower pad
        p2 = ROOT.TPad("pad2","bottom pad",0,0,1,self.rsplit)
        p2.SetTopMargin(0.02)
        p2.SetBottomMargin(0.40)
        p2.Draw()
        
        # make upper frame and configure axes
        p1.cd()
        ytitle = self.rds[0].get_ytitle()
        p1.fr = self.xvar.frame(p1,
                ymin=self.__get_ymin__(),
                ymax=self.__get_ymax__(),
                xtitle="",
                ytitle=ytitle,
                )
        xa = p1.fr.GetXaxis()
        ya = p1.fr.GetYaxis()
        self.__set_axis_text_attrs__(xa, blank=True)
        self.__set_axis_text_attrs__(ya)        
        ya.SetTitleOffset(1.7)

        # make lower frame and configure axes
        p2.cd()
        p2.SetGridy()
        xtitle = self.rds[0].get_xtitle()
        rtitle = "Ratio"
        p2.fr = self.xvar.frame(p2,
                ymin=self.__get_rmin__(),
                ymax=self.__get_rmax__(),
                xtitle=xtitle,
                ytitle=rtitle,
                )
        rxa = p2.fr.GetXaxis()
        rya = p2.fr.GetYaxis()
        self.__set_axis_text_attrs__(rxa)
        self.__set_axis_text_attrs__(rya)                                
        rxa.SetTitleOffset(3.8)
        rxa.SetTickLength(0.06)        
        rya.SetTitleOffset(1.7)
        rya.SetNdivisions(505)

        # fill pads
        self.__fill_upper_pad__(p1)
        self.__fill_lower_pad__(p2)

        # finalize
        self.__save_canvas__(c)
        self.canvas = c
        self.pad1 = p1
        self.pad2 = p2

    #____________________________________________________________
    def __make_legend__(self):
        """Build and return the legend

        :rtype: :class:`loki.core.legend.TopLegend`
        """
        rds = [rd for rd in self.rds if not rd.noleg]
        stack_rds = [rd for rd in self.stack_rds if not rd.noleg]

        hists = [rd.rootobj() for rd in rds + stack_rds]
        labels = [rd.sty.tlatex for rd in rds + stack_rds]
        dopts = ["PL"]*len(rds) + ["F"] * len(stack_rds)

        #l = legend.make_meta(self.hists,labels,dopts,ncol=2,width=0.8,height=0.05,x1=0.2,y2=0.97)
        #l = legend.make_top(self.hists,labels,dopts,colmax=3,y1=1.0-self.topmargin)
        l = legend.build_legend(hists,labels,dopts,type="top",y1=1.0-self.topmargin)
        self.leg = l
        return l

    #____________________________________________________________
    def __make_atlas_label__(self):
        """Draw ATLAS label"""
        # if self.atlas_label set to None, then dont draw
        if self.atlas_label is None: return
        latex = ROOT.TLatex()
        latex.SetNDC()
        latex.SetTextFont(73)
        latex.SetTextSize(24)
        tx = 0.20
        ty = 1.0-self.topmargin-0.055 # first row
        #ty = 1.0-self.topmargin-0.1 # second row
        latex.DrawLatex(tx,ty,"ATLAS")
        if self.atlas_label: 
            watlas=0.12
            latex.SetTextFont(43)
            # side-by-side
            latex.DrawLatex(tx+watlas,ty,self.atlas_label)
            # under
            #latex.DrawLatex(tx,ty-0.04,self.atlas_label)

    #____________________________________________________________
    def __make_extra_labels__(self):
        """Draw extra text decorations"""
        # combine extra lables
        extra_labels = []
        for rd in self.rds: extra_labels += rd._extra_labels
        if self.extra_labels: extra_labels += self.extra_labels
        
        # draw labels
        latex = ROOT.TLatex()
        latex.SetNDC()
        latex.SetTextFont(43)
        latex.SetTextSize(24)
        latex.SetTextAlign(31)
        th = 0.04
        tx = 0.90
        ty = 1.0-self.topmargin-0.055
        for l in extra_labels:
            latex.DrawLatex(tx,ty,l)
            ty-=th


    #____________________________________________________________
    def __make_loki_watermark__(self, p):
        """Draw loki watermark"""
        # load image
        dir_name = os.path.dirname(os.path.abspath(loki.__file__))        
        #file_name = os.path.relpath(os.path.join(dir_name, "../logos", 'loki01.gif'))

        # Original logos
        #file_loki = os.path.relpath(os.path.join(dir_name, "../logos", 'loki03_app.gif'))
        #file_thor = os.path.relpath(os.path.join(dir_name, "../logos", 'thor01_app.gif'))

        # New style logos
        file_loki = os.path.relpath(os.path.join(dir_name, "../logos", 'loki07_bnw.png'))
        file_thor = os.path.relpath(os.path.join(dir_name, "../logos", 'thor05.png'))


        if not os.path.exists(file_thor):
            log().debug(f"Loki Watermark {file_thor} missing!")
            return
        if not os.path.exists(file_thor):
            log().debug(f"THOR Watermark {file_thor} missing!")
            return

        img_loki = ROOT.TImage.Open(file_loki)
        if not img_loki: 
            log().debug(f"Watermark {file_loki} missing!")
            return

        img_thor = ROOT.TImage.Open(file_thor)
        if not img_thor: 
            log().debug(f"Watermark {file_thor} missing!")
            return

        # create pad
        #tw = 0.18
        #th = 0.10
        #tx = 0.16
        #ty = 1.0-self.topmargin-0.15
        
        # new app logo
        tw = 0.06
        th = 0.06
        tx = 0.19
        txgap = -0.01
        ty = 1.0-self.topmargin-0.06
        
        # draw pads and images
        p.cd()
        pw_thor = ROOT.TPad("waterpad_thor","waterpad_thor",tx,ty-th,tx+tw,ty)
        pw_loki = ROOT.TPad("waterpad_loki","waterpad_loki",tx+tw+txgap,ty-th,tx+2*tw+txgap,ty)
        for pw in [pw_thor, pw_loki]: 
            pw.SetFillStyle(0)
            pw.Draw()
        pw_thor.cd()
        img_thor.Draw()
        pw_loki.cd()
        img_loki.Draw()        
        p.cd()
        
        # save watermark
        self.waterpad_loki = pw_loki
        self.watermark_loki = img_loki
        self.waterpad_thor = pw_thor
        self.watermark_thor = img_thor
        
        # return
        p.cd()

    #____________________________________________________________
    def __make_stack__(self):
        """Build and return the :class:`ROOT.THStack`"""
        hstack = ROOT.THStack()
        if self.stack_normalize:
            hists = [rd.rootobj() for rd in self.stack_rds]
            htotal = histutils.sum_hists(hists)
            for h in hists: 
                for i_bin in range(0,h.GetNbinsX()+2):
                    ntotal = htotal.GetBinContent(i_bin)
                    n = h.GetBinContent(i_bin)
                    en = h.GetBinError(i_bin)
                    f = n / ntotal if ntotal else 0.0
                    ef = en / ntotal if ntotal else 0.0
                    h.SetBinContent(i_bin,f)
                    h.SetBinError(i_bin,ef)
            htotal.Delete()            
        for rd in reversed(self.stack_rds):
            if not rd.stackable: continue 
            hstack.Add(rd.rootobj())
        self.hstack = hstack
        return hstack

    #____________________________________________________________
    def __create_ratios__(self):
        """Create Ratios"""
        if self.stack_rds:
            pass
            # TODO: implement stack ratio in this order
            #  - make sum-hist object (for stack)
            #  - create ratio of first rd with sum
            #  - add sum as uncertainty band
        else:
            for rd in self.rds[1:]:
                ratio = Ratio(rd_num=rd,rd_den=self.rds[0])
                self.ratio_rds.append(ratio)
        #self.rds += self.ratio_rds
    
    #____________________________________________________________
    def __get_ymax__(self):
        """Return the maximum value for the y-axis range"""
        ymax = self.ymax
        logy = self.logy or self.xvar.do_logy
        if ymax is None:
            # if 2d objects present get max from y-axis
            highdims = [rd for rd in self.rds if rd.get_dimension()>1]
            if highdims: 
                ymax = highdims[0].yvar.get_xmax()
            
            # otherwise use max y-value 
            else:
                hists = [rd.rootobj() for rd in self.rds]
                # get max hist value
                if self.stack_normalize: 
                    ymax = 1.0
                elif self.stack_rds:
                    stack_hists = [rd.rootobj() for rd in self.stack_rds]
                    htotal = histutils.sum_hists(stack_hists)
                    ymax = histutils.get_ymax_list(hists+[htotal])
                    htotal.Delete()
                else:
                    ymax = histutils.get_ymax_list(hists) 
                
                # correct for log/lin scale
                if logy: ymax*=10.0
                else:    ymax*=1.2

        return ymax

    #____________________________________________________________
    def __get_ymin__(self):
        """Return the minimum value for the y-axis range"""
        ymin = self.ymin
        logy = self.logy or self.xvar.do_logy
        if ymin is None:
            # if 2d objects present get min from y-axis
            highdims = [rd for rd in self.rds if rd.get_dimension()>1]
            if highdims: 
                ymin = highdims[0].yvar.get_xmin()
            
            # otherwise use min y-value 
            else:             
                hists = [rd.rootobj() for rd in self.rds]
                # get min hist value
                if self.stack_normalize: 
                    ymin = 0.0
                elif self.stack_rds:
                    stack_hists = [rd.rootobj() for rd in self.stack_rds]
                    htotal = histutils.sum_hists(stack_hists)
                    ymin = histutils.get_ymin_list(hists+[htotal], nozero=logy)
                    htotal.Delete()
                else:  
                    ymin = histutils.get_ymin_list(hists,nozero=logy) 
                
                # correct for log/lin scale
                if logy and ymin <= 0.: 
                    log().warn("Attempting to use logy with y-range <= 0")
                    ymin = 0.001 

        return ymin

    #____________________________________________________________
    def __get_rmax__(self):
        """Return the maximum value for the ratio"""
        rmax = self.rmax
        if rmax is None:
            hists = [rd.rootobj() for rd in self.ratio_rds]
            rmin = histutils.get_ymin_list(hists)
            rmax = histutils.get_ymax_list(hists)
            maxd = max([abs(1.0-rmin), abs(1.0-rmax)])
            rmax = 1.0 + 1.1 * maxd 
            #rmax += 0.1 * (rmax-rmin)
        return rmax

    #____________________________________________________________
    def __get_rmin__(self):
        """Return the minimum value for the ratio"""
        rmin = self.rmin
        if rmin is None:
            hists = [rd.rootobj() for rd in self.ratio_rds]
            rmin = histutils.get_ymin_list(hists)
            rmax = histutils.get_ymax_list(hists)
            maxd = max([abs(1.0-rmin), abs(1.0-rmax)])
            rmin = 1.0 - 1.1 * maxd             
            #rmin -= 0.1 * (rmax-rmin) 
        return rmin

    #____________________________________________________________
    def __set_axis_text_attrs__(self,a,blank=False):
        """Set axis text attributes"""
        if blank: 
            a.SetTitleSize(0)            
            a.SetLabelSize(0)
        else:     
            a.SetTitleFont(self.font)
            a.SetTitleSize(self.size_title)
            a.SetLabelFont(self.font)
            a.SetLabelSize(self.size_label)

    #____________________________________________________________
    def __fill_upper_pad__(self,p):
        """TODO: describe"""
        log().debug("filling upper pad...")
        p.cd()       
        if self.logy or self.xvar.do_logy: p.SetLogy()                  
        if self.xvar.do_logx: p.SetLogx()
        
        # draw the ROOT objects
        if self.stack_rds:
            self.hstack.Draw("SAME,HIST")
        for rd in self.rds: rd.draw()
        p.RedrawAxis()

        # draw the legend
        if len(self.rds+self.stack_rds) > 1:
            l = self.__make_legend__()
            l.Draw()

        # draw text decorations
        self.__make_atlas_label__()
        self.__make_extra_labels__()

    #____________________________________________________________
    def __fill_lower_pad__(self,p):
        """Draw objects on the lower (ratio) pad"""
        log().debug("filling lower pad...")
        p.cd()
        if self.xvar.do_logx: p.SetLogx() 
        for rd in self.ratio_rds: rd.draw()
        p.RedrawAxis()

    #____________________________________________________________
    def __save_canvas__(self,c):
        """Save canvas"""
        log().debug("saving canvas...")
        for ext in self.fexts: 
            fname = f"{c.GetName()}.{ext}"
            log().debug(f"attempting to save {fname}...")
            c.SaveAs(fname) 
            log().info(f"Written {fname}")


## EOF
