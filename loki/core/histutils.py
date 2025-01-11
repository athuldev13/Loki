# encoding: utf-8
"""
loki.core.histutils
~~~~~~~~~~~~~~~~~~~

Assorted helper functions for ROOT TH1 and TGraph objects
"""
__author__    = "Will Davey"
__email__     = "will.davey@cern.ch"
__created__   = "2012-11-13"
__copyright__ = "Copyright 2012 Will Davey"
__license__   = "GPL http://www.gnu.org/licenses/gpl.html"



## modules
import ctypes
import itertools
import math
from array import array
import ROOT
from loki.core.logger import log


# - - - - - - - - - - function defs - - - - - - - - - - - - #
#______________________________________________________________________________=buf=
def bins(nbins,xmin,xmax):
    """Returns list of bin edges

    :param nbins: number of bins
    :type nbins: int
    :param xmin: first bin low edge 
    :type xmin: float
    :param xmin: last bin high edge
    :type xmin: float
    :rtype: float list
    """
    return [float(i) / float(nbins) * (xmax - xmin) + xmin for i in range(nbins + 1)]

#______________________________________________________________________________=buf=
def log_bins(nbins,xmin,xmax):
    """Returns list of log-separated bin edges

    :param nbins: number of bins
    :type nbins: int
    :param xmin: first bin low edge 
    :type xmin: float
    :param xmin: last bin high edge
    :type xmin: float
    :rtype: float list
    """
    xmin_log = math.log(xmin)
    xmax_log = math.log(xmax)
    bins = [float(i) / float(nbins) * (xmax_log - xmin_log) \
                + xmin_log for i in range(nbins + 1)]
    bins = [math.exp(x) for x in bins]
    return bins

#______________________________________________________________________________=buf=
def frange(x1,x2,x):
    """Returns values from *x1* to *x2* separated by *x*
    
    It's like range(x1,x2,x) but can take decimal x.
    """
    while x1 < x2:
        yield x1
        x1+=x

#______________________________________________________________________________=buf=
def custom_bins(ranges):
    """Returns list of bin edges from tuples of ranges 
    
    Create your own awesome binning by joining ranges 
    with differnt bin widths together. 
    
    Just define your ranges as a list of tuples:: 
    
        [(nbins1,xmin1,xmax1),(nbins2,xmax1,xmax2)...]
    
    :param ranges: tuples describing binning in consecutive ranges
    :type ranges: list of tuples, each of format (nbins,xmin,xmax)
    """
    range_tuples = [frange(x1,x2,x) for (x1,x2,x) in ranges]
    return list(itertools.chain.from_iterable(range_tuples))

#______________________________________________________________________________=buf=
def integral_and_error(hist, xmin = None, xmax = None):
    """Returns histogram integral and error in range [xmin,xmax]
    
        - By default does not include underflow/overflow.
        - If *xmax* coincides with a new bin edge, that bin will not be included. 

    :param hist: 1D histogram 
    :type hist: :class:`ROOT.TH1`
    :param xmin: integral starting x-value
    :type xmin: float
    :param xmax: integral ending x-value
    :type xmax: float
    :rtype: (float,float)
    """
    axis = hist.GetXaxis()
    bin1 = 1
    if xmin: bin1 = axis.FindBin(xmin)
    bin2 = hist.GetNbinsX()
    if xmax: 
        bin2 = axis.FindBin(xmax)
        if axis.GetBinLowEdge(bin2)==xmax: bin2 = bin2-1
    error = ctypes.c_double(0.)
    integ = hist.IntegralAndError(bin1, bin2, error)
    return integ, error


#______________________________________________________________________________=buf=
def integral(hist, xmin = None, xmax = None):
    """Wrapper for :func:`integral_and_error` returning only integral"""
    return integral_and_error(hist, xmin, xmax)[0]


#______________________________________________________________________________=buf=
def full_integral_and_error(hist):
    """Returns histogram integral and error including underflow/overflow

    :param hist: 1D, 2D or 3D histogram 
    :type hist: :class:`ROOT.TH1`
    :rtype: (float,float)
    """
    err = ctypes.c_double(0.)
    if isinstance(hist,ROOT.TH3):
        return [hist.IntegralAndError(0, hist.GetNbinsX()+1, 
                                      0, hist.GetNbinsY()+1,
                                      0,hist.GetNbinsZ()+1, 
                                      err), err]
    elif isinstance(hist,ROOT.TH2):
        return [hist.IntegralAndError(0, hist.GetNbinsX() + 1, 
                                      0, hist.GetNbinsY()+1,
                                      err), err]
    elif isinstance(hist,ROOT.TH1):
        return [hist.IntegralAndError(0, hist.GetNbinsX() + 1, err), err]
    log().warn('Cannot integrate non TH1/2/3 object!')
    return [0.0, 0.0]


#______________________________________________________________________________=buf=
def full_integral(hist):
    """Wrapper for :func:`full_integral_and_error` returning only integral"""
    return full_integral_and_error(hist)[0]


#______________________________________________________________________________=buf=
def normalize(hist):
    """Normalize a histogram to unit area

    :param hist: histogram
    :type hist: :class:`ROOT.TH1`
    """
    n = full_integral(hist)
    if hist and n: hist.Scale(1. / n)


#______________________________________________________________________________=buf=
def is_weighted(hist):
    """Return True if hist is weighted

    :param hist: histogram
    :type hist: :class:`ROOT.TH1`
    :rtype: bool
    """
    n = float(hist.GetEntries())
    s = float(full_integral(hist))
    return (n != s)


#______________________________________________________________________________=buf=
def get_xmin(h):
    """Return the minimum x-value of a histogram or graph

    :param h: histogram or graph
    :type h: :class:`ROOT.TH1` or :class:`ROOT.TGraph`
    :rtype: float
    """
    if isinstance(h,ROOT.TH1): return h.GetXaxis().GetBinLowEdge(1)
    if isinstance(h,ROOT.TGraph):
        return min([h.GetX()[i] for i in range(h.GetN())])
    log().warn(f"Invalid type {h.__class__.__name__} for get_xmin!")
    return 0.0 


#______________________________________________________________________________=buf=
def get_xmax(h):
    """Return the maximum x-value of a histogram or graph

    :param h: histogram or graph
    :type h: :class:`ROOT.TH1` or :class:`ROOT.TGraph`
    :rtype: float
    """
    if isinstance(h,ROOT.TH1): return h.GetXaxis().GetBinUpEdge(h.GetNbinsX())
    if isinstance(h,ROOT.TGraph):
        return max([h.GetX()[i] for i in range(h.GetN())])
    if isinstance(h,ROOT.TF1): return h.GetMaximum()
    log().warn(f"Invalid type {h.__class__.__name__} for get_xmax!")
    return 0.0 

#______________________________________________________________________________=buf=
def get_hist_ymin_nozero(h):
    """Return minimum content of non-zero hist bins

    :param h: histogram
    :type h: :class:`ROOT.TH1`
    """
    bins = []
    for i in range(1,h.GetNbinsX()+1):
        n = h.GetBinContent(i)
        if n==0.0: continue
        bins.append(n) 
    if len(bins)==0: return 0.0
    return min(bins)

#______________________________________________________________________________=buf=
def __get_ymin__(h, nozero=False):
    """Return the minimum y-value of a histogram or graph

    :param h: histogram or graph
    :type h: :class:`ROOT.TH1` or :class:`ROOT.TGraph`
    :rtype: float
    """
    ymin = 0.
    if isinstance(h,ROOT.TH1):
        if nozero: ymin = get_hist_ymin_nozero(h)
        else: ymin = h.GetMinimum()
    elif isinstance(h,ROOT.TGraph):
        if h.GetN(): 
            ymin = min([h.GetY()[i] for i in range(h.GetN())])
    elif isinstance(h,ROOT.TF1): 
        ymin = h.GetMinimum()
    else: 
        log().warn(f"Invalid type {h.__class__.__name__} for __get_ymin__!")
    if nozero and ymin <= 0.0: 
        ymin = 0.001
    return ymin


#______________________________________________________________________________=buf=
def __get_ymax__(h):
    """Return the maximum y-value of a histogram or graph

    :param h: histogram or graph
    :type h: :class:`ROOT.TH1` or :class:`ROOT.TGraph`
    :rtype: float
    """
    if isinstance(h,ROOT.TH1): return h.GetMaximum()
    if isinstance(h,ROOT.TGraph):
        if not h.GetN(): return 0.
        return max([h.GetY()[i] for i in range(h.GetN())])
    elif isinstance(h,ROOT.TF1): 
        return h.GetMaximum()    
    log().warn(f"Invalid type {h.__class__.__name__} for __get_ymax__!")
    return 0.


#______________________________________________________________________________=buf=
def get_xmin_list(hlist):
    """Return the minimum x-value from a list of histograms or graphs

    :param hlist: histogram or graph list (can be mixed)
    :type hlist: :class:`ROOT.TH1` or :class:`ROOT.TGraph` list
    :rtype: float
    """
    return min([get_xmin(h) for h in hlist])


#______________________________________________________________________________=buf=
def get_xmax_list(hlist):
    """Return the maximum x-value from a list of histograms or graphs

    :param hlist: histogram or graph list (can be mixed)
    :type hlist: :class:`ROOT.TH1` or :class:`ROOT.TGraph` list
    :rtype: float
    """
    return max([get_xmax(h) for h in hlist])


#______________________________________________________________________________=buf=
def get_ymin_list(hlist, nozero=False):
    """Return the minimum y-value from a list of histograms or graphs

    :param hlist: histogram or graph list (can be mixed)
    :type hlist: :class:`ROOT.TH1` or :class:`ROOT.TGraph` list
    :rtype: float
    """
    return min([__get_ymin__(h,nozero) for h in hlist])


#______________________________________________________________________________=buf=
def get_ymax_list(hlist):
    """Return the maximum y-value from a list of histograms or graphs

    :param hlist: histogram or graph list (can be mixed)
    :type hlist: :class:`ROOT.TH1` or :class:`ROOT.TGraph` list
    :rtype: float
    """
    return max([__get_ymax__(h) for h in hlist])


#______________________________________________________________________________=buf=
def sum_hists(hlist):
    """Return the sum of a list of histograms

    :param hlist: histogram 
    :type hlist: :class:`ROOT.TH1` list
    :rtype: :class:`ROOT.TH1`
    """
    out_hist = None
    for hist in hlist:
        if not out_hist: out_hist = hist.Clone()
        else:
            ## if next hist has more bins, expand
            if hist.GetNbinsX() != out_hist.GetNbinsX():
                out_hist = merge_diff_hists(hist,out_hist)
            else:
                out_hist.Add(hist)
    return out_hist


#______________________________________________________________________________=buf=
def merge_diff_hists(h1,h2):
    """Return the sum of two histograms with different bin edges 

    The assumption is that the bins in one histogram are a subset 
    of the bins in the other histogram (ie one histogram is an 
    extended version of the other). 

    **Warning: this will break if the histograms dont have at 
    least a common subset of bins**

    :param h1: first histogram 
    :type h1: :class:`ROOT.TH1`
    :param h2: second histogram 
    :type h2: :class:`ROOT.TH1`
    :rtype: :class:`ROOT.TH1`
    """
    # split hists in subset and extended 
    if h1.GetNbinsX()>h2.GetNbinsX(): 
        h = h1.Clone()
        hother = h2
    else: 
        h = h2.Clone()
        hother = h1
   
    warned=False
    # sum overlapping bins  
    for i in range(0,hother.GetNbinsX()+1):
        # check for bin edge match
        if (h.GetBinLowEdge(i) != hother.GetBinLowEdge(i)) and not warned: 
            log().warning("Trying to merge hists with discrepent bin edges")
            warned=True
       
        # sum content
        n = h.GetBinContent(i) + hother.GetBinContent(i)
        en = math.sqrt(pow(h.GetBinError(i),2) + pow(hother.GetBinError(i),2))
        h.SetBinContent(i,n)
        h.SetBinError(i,en)
    return h


#______________________________________________________________________________=buf=
def divide_hists(h_num, h_den, name=None, eff=False):
    """Return ratio hist using TH1::Divide

    :param h_num: numerator histogram
    :type h_num: :class:`ROOT.TH1`
    :param h_den: denominator histogram 
    :type h_den: :class:`ROOT.TH1`
    :param name: name for new hist
    :type name: str
    :param eff: if True use Binomial option
    :type eff: bool
    :rtype: :class:`ROOT.TH1`
    """
    h = h_num.Clone()
    if eff: 
        h.Divide(h_num, h_den, 1., 1., 'B')
    else: 
        h.Divide(h_den)
    h.SetName(name or 'h_ratio')
    h.GetXaxis().SetTitle(h_num.GetXaxis().GetTitle())
    h.GetYaxis().SetTitle('Ratio')
    return h


#______________________________________________________________________________=buf=
def divide_graphs(g_num, g_den, name=None):
    """Return ratio of two graphs

    :param g_num: numerator graph
    :type g_num: :class:`ROOT.TGraph`
    :param g_den: denominator graph 
    :type g_den: :class:`ROOT.TGraph`
    :param name: name for new graph
    :type name: str
    :rtype: :class:`ROOT.TGraph`
    """
    # check graph compatibility
    if not graphs_compatible(g_num, g_den): 
        log().warn(f"Trying to divide incompatible graphs: {g_num.GetName()}, {g_den.GetName()}")

    # construct and return graph
    g = ROOT.TGraphAsymmErrors()
    g.SetName(name or 'g_ratio')
    g.GetXaxis().SetTitle(g_num.GetXaxis().GetTitle())
    g.GetYaxis().SetTitle('Ratio')
    for i in range(g_num.GetN()):
        x = g_num.GetX()[i]
        if get_graph_point(g_den,x) is None: continue
        y_num = g_num.GetY()[i]
        y_den = g_den.Eval(x)
        y = y_num / y_den if y_den else 0.0

        ey_up = ey_dn = ex_up = ex_dn = 0.0
        if y_num and y_den:
            ey_up = math.sqrt(pow(g_num.GetErrorYhigh(i)/y_num,2) + pow(g_den.GetErrorYlow(i)/y_den,2)) * y
            ey_dn = math.sqrt(pow(g_num.GetErrorYlow(i) / y_num, 2) + pow(g_den.GetErrorYhigh(i) / y_den, 2)) * y
            ex_up = g_num.GetErrorXhigh(i)
            ex_dn = g_num.GetErrorXlow(i)

        n = g.GetN()
        g.SetPoint(n, x, y)
        g.SetPointError(n, ex_dn, ex_up, ey_dn, ey_up)


    return g


#______________________________________________________________________________=buf=
def graphs_compatible(g1, g2):
    """Retrun True if graphs are compatible

    Checks size and x-values

    :param g1: numerator graph
    :type g1: :class:`ROOT.TGraph`
    :param g1: denominator graph 
    :type g1: :class:`ROOT.TGraph`
    """
    if g1.GetN() != g2.GetN(): return False
    for i in range(g1.GetN()): 
        if g1.GetX()[i] != g2.GetX()[i]: return False
    return True


#______________________________________________________________________________=buf=
def get_graph_point(g, x):
    """Retrun index of graph (*g*) point with *x* value, None if no match.

    :param g: numerator graph
    :type g: :class:`ROOT.TGraph`
    :param x: x value 
    :type x: float
    :rtype: int
    """
    for i in range(g.GetN()): 
        if g.GetX()[i] == x: return i
    return None


#______________________________________________________________________________=buf=
def make_eff_graph(h_pass, h_total, name=None):
    """Return efficiency graph using Bayes divide

    :param h_pass: numerator histogram
    :type h_pass: :class:`ROOT.TH1`
    :param h_total: denominator histogram 
    :type h_total: :class:`ROOT.TH1`
    :param name: name for new graph
    :type name: str
    :rtype: :class:`ROOT.TGraphAsymErrors`
    """
    g = ROOT.TGraphAsymmErrors()
    g.Divide(h_pass,h_total, 'cl=0.683 b(1,1) mode')
    g.SetName(name or 'g_eff')
    g.GetXaxis().SetTitle(h_pass.GetXaxis().GetTitle())
    g.GetYaxis().SetTitle('Efficiency')
    g.GetXaxis().SetRangeUser(h_total.GetXaxis().GetXmin(), h_total.GetXaxis().GetXmax())
    return g


#______________________________________________________________________________=buf=
def make_eff_hist(h_pass, h_total, name=None):
    """Return efficiency hist using TH1::Divide

    The Binomial option "B" is used.

    :param h_pass: numerator histogram
    :type h_pass: :class:`ROOT.TH1`
    :param h_total: denominator histogram 
    :type h_total: :class:`ROOT.TH1`
    :param name: name for new graph
    :type name: str
    :rtype: :class:`ROOT.TH1`
    """
    h = divide_hists(h_pass, h_total, name=name or "h_eff", eff=True)
    h.GetYaxis().SetTitle('Efficiency')
    return h


#______________________________________________________________________________=buf=
def make_eff(h_pass, h_total, name=None):
    """Return efficiency graph or hist depending on whether hists are weighted

    Update: currently always return graph. 

    :param h_pass: numerator histogram
    :type h_pass: :class:`ROOT.TH1`
    :param h_total: denominator histogram 
    :type h_total: :class:`ROOT.TH1`
    :param name: name for new graph
    :type name: str
    :rtype: :class:`ROOT.TGraphAsymErrors` or :class:`ROOT.TH1`
    """
    if is_weighted(h_pass) or is_weighted(h_total): 
        return make_eff_hist(h_pass,h_total,name)
    return make_eff_graph(h_pass,h_total,name)


#______________________________________________________________________________=buf=
def get_median(h):
    """Returns median of a histogram (*h*)
  
    :param h: 
    :type h: :class:`ROOT.TH1`
    :rtype: float 
    """
    x = array('d', [0.5])
    y = array('d', [0.])
    if h.Integral() == 0.0: return 0.0
    h.GetQuantiles(1, y, x)
    return y[0]


#______________________________________________________________________________=buf=
def get_mode(h):
    """Returns mode of a histogram (*h*)
  
    :param h: 
    :type h: :class:`ROOT.TH1`
    :rtype: float 
    """
    return h.GetBinCenter(h.GetMaximumBin())


#______________________________________________________________________________=buf=
def get_window_mode(h,w=0.05):
    """Returns mode of a histogram (*h*) in a sliding window of fractional width (*w*).
  
    :param h: 
    :type h: :class:`ROOT.TH1`
    :param w: fractional width of sliding window
    :type w: float
    :rtype: float 
    """
    if integral(h)<=0.0: return 0.0
    xmin = get_xmin(h)
    xmax = get_xmax(h)
    window = w * (xmax - xmin)
    values = []
    for i in range(1,h.GetNbinsX()+1):
        bincenter = h.GetBinCenter(i)
        #print(f"bin center: {bincenter}, window: {window}")
        n = integral(h,bincenter-window/2.0,bincenter+window/2.0)    
        values.append([bincenter,n])
    values = sorted(values,key=lambda x:x[1],reverse=True)
    #print "\nSUMMARY"
    #for (bincenter,n) in values:
    #    print(f"{bincenter}, {n}")
    return values[0][0]


#______________________________________________________________________________=buf=
def get_rms(h):
    """Returns rms (really sdev) of a histogram (*h*)
  
    :param h: 
    :type h: :class:`ROOT.TH1`
    :rtype: float 
    """
    return h.GetRMS()


#______________________________________________________________________________=buf=
def get_quantile_width(h,cl=0.68):
    """Returns width of a symmetric interval containing at least the *cl* around 
    the mean of a histogram (*h*)
  
    :param h: 
    :type h: :class:`ROOT.TH1`
    :param cl: confidence level 
    :type cl: float
    :rtype: float 
    """
    q1 = (1. - cl) / 2.
    q2 = 1. - q1
    x = array('d', [q1, q2])
    y = array('d', [0., 0.])
    if h.Integral() == 0.0: return 0.0
    h.GetQuantiles(2, y, x)
    width = (y[1] - y[0]) / 2.0
    return width


#______________________________________________________________________________=buf=
def get_quantile_width_and_error(h,cl=0.68, debug=False):
    """Returns width and error of a symmetric interval containing at least 
    the *cl* around the mean of a histogram (*h*)
 
    The error is estimated by fitting the histogram with a sum of three 
    Gaussians and then throwing pseudo-experiments

    **Warning: not guaranteed to work on any histogram, in fact, only 
    verified to work on some energy resolution distributions**

    :param h: 
    :type h: :class:`ROOT.TH1`
    :param cl: confidence level 
    :type cl: float
    :param debug: do debug output 
    :type debug: bool 
    :rtype: float 
    """
    import numpy
    
    n = h.Integral()
    bin_width = h.GetBinWidth(1)
    nmax = n / bin_width
    # don't run if low stats
    if n<500.0: return (0.0,0.0)
 
    ## fit hist with sum of 3 gaussians (fits energy resolution well)
    fitmin = 0.8
    fname  =  "[0]*TMath::Gaus(x,[1],[2])"
    fname += "+[3]*TMath::Gaus(x,[4],[5])"
    fname += "+[6]*TMath::Gaus(x,[7],[8])"
    f = ROOT.TF1("ftemp",fname,-fitmin,fitmin)
    f.SetParLimits(0, 0.0 ,nmax)
    f.SetParLimits(1,-0.05,0.05)
    f.SetParameter(2, 0.02)
    f.SetParLimits(2, 0.01,0.05)
    f.SetParLimits(3, 0.0 ,nmax)
    f.SetParLimits(4,-0.10,0.10)
    f.SetParameter(5, 0.10)
    f.SetParLimits(5, 0.01,0.20)
    f.SetParLimits(6, 0.0 ,nmax)
    f.SetParLimits(7,-0.20,0.20)
    f.SetParameter(8, 0.5)
    f.SetParLimits(8, 0.01,1.00)
    f.SetLineColor(ROOT.kRed)
    f.SetNpx(1000)
    h.Fit(f,"RQL")
    h.Fit(f,"RQL")
    if debug: 
        h.Draw()
        ROOT.gStyle.SetOptFit(1111)
        ROOT.gStyle.SetOptStat(11111111)
        #ROOT.gPad.SetLogy()
        ROOT.gPad.SetRightMargin(0.4)
        h.GetXaxis().SetNdivisions(505)
        h.GetXaxis().SetRangeUser(-0.1, 0.1)
        ROOT.gPad.SaveAs("c_fit_bin.pdf")
 
    # setup quantiles
    q1 = (1. - cl) / 2.
    q2 = 1. - q1
    x = array('d', [q1, q2])
    y = array('d', [0., 0.])
 
    # get quantile width from fit
    if debug:
        #h.GetQuantiles(2, y, x)
        f.GetQuantiles(2, y, x)
        width = (y[1] - y[0]) / 2.0
        log().debug(f"quantiles from fit: c0: {y[0]:.3f}, c1: {y[1]:.3f}")
        log().debug(f"width from fit: {width}")
    
    ## get standard quantile width
    width = get_quantile_width(h, cl)
 
    ## get quantile uncertainties from toys
    htemp = h.Clone("htemp")
    toywidths = array('d',[])
    for itoy in range(100):
        htemp.Reset()
        #for i in range(int(n)): htemp.Fill(f.GetRandom())
        for ibin in range(1,htemp.GetNbinsX()+1):
            func = f.Integral(htemp.GetBinLowEdge(ibin), htemp.GetBinLowEdge(ibin+1)) / bin_width
            binn = ROOT.gRandom.Poisson(func)
            htemp.SetBinContent(ibin, binn)
            htemp.SetBinError(ibin, math.sqrt(binn))
            if debug: 
                log().debug(f"ibin {ibin}, norig: {h.GetBinContent(ibin)}, nfit: {func}, ntoy: {binn}")
 
        htemp.GetQuantiles(2, y, x)
        toywidth = (y[1] - y[0]) / 2.0
        toywidths.append(toywidth)
        if debug:
            log().debug(f"toy width: {width}")
            htemp.Draw()
            ROOT.gPad.SaveAs("hwidths.pdf")
    #width = numpy.mean(widths)
    #width = numpy.median(widths)
    error = numpy.std(toywidths)
 
    if debug:
        xmin = min(toywidths)
        xmax = max(toywidths)
        x1 = xmin-0.05*(xmax-xmin)
        x2 = xmax+0.05*(xmax-xmin)
        hdist = ROOT.TH1F("hdist",";width;trials",100,x1,x2)
        for x in toywidths: hdist.Fill(x)
        hdist.Draw()
        ROOT.gPad.SaveAs("c_widths.pdf")
        width = hdist.GetMean()
 
    log().debug(f"toy result: {width} +- {error}")
    htemp.Delete()
    f.Delete()
    return (width,error)


#______________________________________________________________________________=buf=
def get_fit_width(h,nrms=None):
    """Returns standard deviation of Gaussian fit to histogram (*h*) 
  
    :param h: 
    :type h: :class:`ROOT.TH1`
    :param nrms: fit range in number of standard deviations around the mean 
    :type nrms: float
    :rtype: float 
    """
    nrms = nrms or 1.0 
    if not h.GetEntries(): return 0.0
    sdev = h.GetRMS()
    mean = h.GetMean()
    h.Fit("gaus","RQ","",mean - float(nrms) * sdev, mean + float(nrms) * sdev)
    f = h.GetFunction("gaus")
    return f.GetParameter(2)


#______________________________________________________________________________=buf=
def get_fit_mean(h,nrms=None):
    """Returns mean of Gaussian fit to histogram (*h*) 
  
    :param h: 
    :type h: :class:`ROOT.TH1`
    :param nrms: fit range in number of standard deviations around the mean 
    :type nrms: float
    :rtype: float 
    """
    nrms = nrms or 0.5 
    if h.Integral() < 10.0: return h.GetMean()
    if not h.GetEntries(): return 0.0
    sdev = h.GetRMS()
    mean = h.GetMean()
    fitresult = h.Fit("gaus","RQS","", mean - float(nrms) * sdev, mean + float(nrms) * sdev)
    if not fitresult.IsValid(): return 0.0
    f = h.GetFunction("gaus")
    return f.GetParameter(1)


#______________________________________________________________________________=buf=
def get_profile(h2,ycalc,name="g_profile",**kwargs):
    """Returns y-axis profile using :func:`get_quantile_width`

    The ycalc function name can be one of: 
    
    - median (:func:`get_median`)
    - mode (:func:`get_mode`)
    - rms (:func:`get_rms`)
    - quantile_width (:func:`get_quantile_width`)
    - quantile_width_and_error (:func:`get_quantile_width_and_error`)
    - fit_width (:func:`get_fit_width`)
    - fit_mean (:func:`get_fit_mean`)

    :param h2: scatter histogram 
    :type h2: :class:`ROOT.TH2`
    :param ycalc: y-value calculator function
    :name ycalc: str 
    :param name: profile graph name 
    :type name: str
    :param kwargs: key-word arguments passed to *ycalc* function
    :type kwargs: key-word arguments 
    :rtype: :class:`ROOT.TGraph` (or :class:`ROOT.TGraphErrors`)
    """
    # arrays to store graph points
    x_arr = array('d', [])
    y_arr = array('d', [])
    ey_arr = array('d', [])

    # look up ycalc function
    ycalc_name = f"get_{ycalc}"
    if ycalc_name not in globals(): 
        log().warn(f"No ycalc function with name {ycalc_name}")
        return None
    f = globals()[ycalc_name]

    # loop over x-bins
    for ix in range(1, h2.GetNbinsX() + 1):
        # get projection in y (in current x-bin) 
        h_temp = h2.ProjectionY(f"{name}_slice{ix}", ix, ix)

        # get x-value
        x = h2.GetXaxis().GetBinCenter(ix)
        x_arr.append(x)

        # get y-value (and error if provided)
        ydata = f(h_temp,**kwargs)
        if not isinstance(ydata,list): ydata = [ydata]
        if len(ydata)>0: y_arr.append(ydata[0])
        if len(ydata)>1: ey_arr.append(ydata[0])
        
        # remove temp profile hist
        h_temp.Delete()

    # create graph with no errors
    if not ey_arr: 
        g = ROOT.TGraph(len(x_arr), x_arr, y_arr)
    # create graph with errors
    elif ey_arr:
        ex_arr = array('d',[0.] * len(x_arr))
        g = ROOT.TGraphErrors(len(x_arr), x_arr, y_arr, ex_arr, ey_arr)
    g.SetName(name)
    return g


#______________________________________________________________________________=buf=
def get_inbuilt_rms_profile(h,name="g_scan"):
    """Returns y-axis profile using the "s" option of TH2::ProfileX() 

    :param h: scatter histogram 
    :type h: :class:`ROOT.TH2`
    :param name: profile graph name 
    :type name: str
    :rtype: :class:`ROOT.TGraph`
    """
    x_arr = array('d',[])
    y_arr = array('d',[])
    profile = h.ProfileX(f"{name}_profile", 1, -1, "s")
    for ix in range(1,h.GetNbinsX()+1):
        x_arr.append(profile.GetBinCenter(ix))
        y_arr.append(profile.GetBinError(ix))
    g = ROOT.TGraph(len(x_arr),x_arr,y_arr)
    g.SetName(name)
    return g


#______________________________________________________________________________=buf=
def create_roc_graph(h_sig,h_bkg,effmin=None,name="g_roc",normalize=True,reverse=False):
    """Returns y-axis profile using the "s" option of TH2::ProfileX() 

    :param h_sig: signal histogram 
    :type h_sig: :class:`ROOT.TH1`
    :param h_bkg: background histogram 
    :type h_bkg: :class:`ROOT.TH1`    
    :param effmin: minimum signal efficiency 
    :type effmin: float
    :param name: roc curve graph name 
    :type name: str
    :rtype: :class:`ROOT.TGraph`
    """

    # get total normalisation
    nsig_tot = full_integral(h_sig)
    nbkg_tot = full_integral(h_bkg)
    if (nsig_tot <=0) or (nbkg_tot <= 0):  
        return None

    # loop over hist, calculating efficiency/rejection
    xarr = array('d',[])
    yarr = array('d',[])
    nbins = h_sig.GetNbinsX()
    for ibin in range(0,nbins+2): 
        if reverse: 
            nsig = h_sig.Integral(0, ibin)
            nbkg = h_bkg.Integral(0, ibin)
        else:     
            nsig = h_sig.Integral(ibin,nbins+2)
            nbkg = h_bkg.Integral(ibin,nbins+2)

        esig = nsig 
        if normalize: esig /= nsig_tot
        rbkg = nbkg_tot / nbkg if nbkg else 1.e7
        
        if effmin is not None and esig < effmin: continue
        
        xarr.append(esig)
        yarr.append(rbkg)

    g = ROOT.TGraph(len(xarr),xarr,yarr)
    g.SetName(name)
    return g

#______________________________________________________________________________=buf=
def convert_graph_to_2dgraph(g, yvals, name=None):
    """Returns a TGraph2D from a TGraph by duplicating the graph at each point in *yvals*"""
    current_xvals = [g.GetX()[i] for i in range(g.GetN())]
    current_yvals = [g.GetY()[i] for i in range(g.GetN())]
    new_yvals = []
    for yval in yvals: new_yvals += [yval]*len(current_xvals)    
    xarr = array('d',current_xvals*len(yvals))
    yarr = array('d',new_yvals)
    zarr = array('d',current_yvals*len(yvals)) 
    g2 = ROOT.TGraph2D(len(xarr),xarr,yarr,zarr)
    if name: g2.SetName(name)
    return g2


#______________________________________________________________________________=buf=
def convert_hist_to_2dhist(h, ybins, name=None):
    """Returns a TH2 from a TH1 by duplicating the hist at each point in *ybins*"""
    if not name: name = "h2"
    xbins = array('f', [h.GetBinLowEdge(i) for i in range(i,h.GetNbinsX()+1)])
    ybins = array('f', ybins)
    h2 = ROOT.TH2F(name,name,len(xbins)-1,xbins,len(ybins)-1,ybins)
    for ix in range(1,h2.GetNbinsX()+1):
        for iy in range(1,h2.GetNbinsY()+1):
            h2.SetBinContent(ix,iy,h.GetBinContent(ix))
            h2.SetBinError(ix,iy,h.GetBinError(ix))
    return h2


#______________________________________________________________________________=buf=
def new_hist(name, xbins, ybins = None, zbins = None, 
             xtitle = None, ytitle = None, ztitle = None):
    """Return an empty 1D/2D/3D histogram 

    Sumw2 is always set.

    Note: have removed rebin functionality. If desired may bring back in future using
    h.SetBit(ROOT.TH1.kCanRebin)

    Used to read:
    "If the binning isn't set, will use the `kCanRebin` option
    to allow on-fly resizing of the histogram as events are 
    added. Useful for figuring out appropriate ranges for new
    variables."

    :param name: name of histogram
    :type name: str
    :param xbins: x-axis bin edges
    :type xbins: list float
    :param ybins: y-axis bin edges
    :type ybins: list float
    :param zbins: z-axis bin edges
    :type zbins: list float
    :param xtitle: x-axis title 
    :type xtitle: str
    :param ytitle: y-axis title 
    :type ytitle: str
    :param ztitle: z-axis title 
    :type ztitle: str
    :rtype: :class:`ROOT.TH1`
    """
    # 3D hist
    if zbins:
        if not ybins: 
            log().error("Must provide ybins with zbins")
            raise ValueError             
        h = ROOT.TH3F(name, name,
                len(xbins) - 1, array('f', xbins),
                len(ybins) - 1, array('f', ybins),
                len(zbins) - 1, array('f', zbins),
                )        
    # 2D hist
    elif ybins:
        h = ROOT.TH2F(name, name,
                len(xbins) - 1, array('f', xbins),
                len(ybins) - 1, array('f', ybins),
                )        
    # 1D hist
    else:
        h = ROOT.TH1F(name, name,
                len(xbins) - 1, array('f', xbins)
                )        
    
    # titles
    if xtitle: h.GetXaxis().SetTitle(xtitle)
    if ytitle: h.GetYaxis().SetTitle(ytitle)
    if ztitle: h.GetZaxis().SetTitle(ztitle)
    
    # weighted histogram
    h.Sumw2()
    return h


#______________________________________________________________________________=buf=
def histargs(xvar, yvar=None, zvar=None, name=None):
    """Converts set of variable Views into list of arguments for 
    :func:`loki.core.histutils.new_hist`
    
    :param xvar: the x-axis variable view
    :type xvar: :class:`loki.core.var.View`    
    :param yvar: the y-axis variable view
    :type yvar: :class:`loki.core.var.View`
    :param zvar: the z-axis variable view
    :type zvar: :class:`loki.core.var.View`        
    :param name: unique identifier for histogram (default with be provided if None)
    :type name: str
    :rtype: tuple
    """

    xbins = xvar.xbins
    ybins = yvar.xbins if yvar else None
    zbins = zvar.xbins if zvar else None
    xtitle = xvar.get_xtitle()
    ytitle = yvar.get_xtitle() if yvar else None
    ztitle = zvar.get_xtitle() if zvar else None
    if name is None:            
        if zvar and not yvar: 
            log().error("Must provide yvar with zvar")
            raise ValueError
        elif zvar:               
            name = f'h3_{xvar.get_name()}_{yvar.get_name()}_{zvar.get_name()}'
        elif yvar:
            name = f'h2_{xvar.get_name()}_{yvar.get_name()}'
        else:
            name = f'h_{xvar.get_name()}'
    return (name, xbins, ybins, zbins, xtitle, ytitle, ztitle)


#______________________________________________________________________________=buf=
def set_axis_binnames(axis, binnames):
    """Set bin names for histogram  
    
    :param axis: axis
    :type axis: :class:`ROOT.TAxis`    
    :param binnames: bin names
    :type binnames: list str
    """
    assert len(binnames) <= axis.GetNbins(), "binnames longer than axis bins"
    for i in range(axis.GetNbins()):  
        axis.SetBinLabel(i+1,binnames[i])





## EOF
