# encoding: utf-8
"""
loki.common.plotgen.py
~~~~~~~~~~~~~~~~~~~~~~

TODO: description 

"""
__author__    = "Will Davey"
__email__     = "will.davey@cern.ch"
__created__   = "2016-02-21"
__copyright__ = "Copyright 2016 Will Davey"
__license__   = "GPL http://www.gnu.org/licenses/gpl.html"

from copy import deepcopy
from loki.common import cuts, styles, vars
from loki.common.vars import taus, truetaus
from loki.core.hist import Profile, EffProfile, Hist, ROCCurve, ResoProfile
from loki.core.logger import log
from loki.core.plot import Plot



# - - - - - - - - - - - plot creators  - - - - - - - - - - - - #
#______________________________________________________________________________=buf=
def create_eff_profiles(samples, depvars=None, tag=None, **kw):
    """Return list of reco/id efficiency profile plots
    
    Default mode is engaged if only one sample is specified in *samples*. 
    Then profiles for each working point are overlayed in each plot. 
    
    Multisample mode is engaged if multiple samples are specified in *samples*. 
    Then profiles for each sample are overlayed and a separate plot is made for 
    each working point. This mode also includes a ratio panel to compare 
    perforamnce across samples.    
    
    :param samples: input samples
    :type samples: list :class:`loki.core.sample.Sample`
    :param depvars: dependent variables 
    :type depvars: list :class:`loki.core.var.Var`
    :param tag: identifying string for plot names
    :type tag: str
    :param kw: key-word args for the plots or their RootDrawables
    :rtype: list :class:`loki.core.plot.Plot`
    """
    # split kw args into Plot and RootDrawable
    kwplot = dict()
    kwrd = dict()
    plot_args = list(Plot.__init__.__code__.co_varnames)[1:]
    for (k,v) in kw.items(): 
        if k in plot_args: kwplot[k] = v
        else:              kwrd[k] = v
     
    # generate plots
    plots = []
    for var in depvars:
        rdname = "h_eff_{tag}_{{sname}}_vs_{var}".format(tag=tag, var=var.get_name())
        rds = [EffProfile(name=rdname.format(sname=s.name), sample=s, xvar=var, **kwrd) 
               for s in samples]
        pname = "Eff_{tag}_vs_{var}".format(tag=tag, var=var.get_name())
        lbls = kwplot.pop("extra_labels", []) + [tag]
        plots += [Plot(pname, rds, extra_labels=lbls, **kwplot)]

    return plots 



#______________________________________________________________________________=buf=
def create_res_profiles(samples, depvars=None, tag=None, **kw):
    """Return list of resolution/closure profile plots

    Default mode is engaged if only one sample is specified in *samples*. 
    Then profiles for each alg are overlayed in each plot. 
    
    Multisample mode is engaged if multiple samples are specified in *samples*. 
    Then profiles for each sample are overlayed and a separate plot is made for 
    each alg. This mode also includes a ratio panel to compare 
    perforamnce across samples.
    
    :param sample: input samples
    :type sample: list :class:`loki.core.sample.Sample`
    :param depvars: dependent variables 
    :type depvars: list :class:`loki.core.tag.Var`
    :param tag: unique identifier (for prof/plot names)
    :type tag: str
    :param kw: key-word args for the plots or their RootDrawables    
    :rtype: list :class:`loki.core.plot.Plot`
    """
    # split kw args into Plot and RootDrawable
    kwplot = dict()
    kwrd = dict()
    plot_args = list(Plot.__init__.__code__.co_varnames)[1:]
    for (k,v) in kw.items(): 
        if k in plot_args: kwplot[k] = v
        else:              kwrd[k] = v

    yvar = kw.pop("yvar")
    mode = kw.pop("mode")

    # generate plots
    plots = []
    for var in depvars:
        rdname = "h_reso_{tag}_{{sname}}_{yvar}_{mode}_vs_{var}".format(tag=tag, 
                    yvar=yvar.var.get_name(), mode=mode, var=var.get_name())
        rds = [ResoProfile(name=rdname.format(sname=s.name), sample=s, xvar=var, **kwrd) 
               for s in samples]
        pname = "ResProfile_{tag}_{yvar}_{mode}_vs_{var}".format(tag=tag, 
                    yvar=yvar.var.get_name(), mode=mode, var=var.get_name())
        lbls = kwplot.pop("extra_labels", []) + [tag]
        plots += [Plot(pname, rds, extra_labels=lbls, **kwplot)]

    return plots 






'''
#______________________________________________________________________________=buf=
def create_tid_variable_dists(samples,tidvars=None,sel=None,prongs=None,
                              normalize=True,dir="variables",tag=None):
    """Return list of variable distribution overlay plots
    
    :param samples: samples to overlay
    :type samples: list :class:`loki.core.sample.Sample`
    :param tidvars: variables to plot 
    :type tidvars: list :class:`loki.core.var.Var`
    :param sel: selection to apply
    :type sel: :class:`loki.core.cut.Cut` 
    :param prongs: number of prongs (typically 1 or 3)
    :type prongs: int
    :param normalize: normalize the distributions to unit area
    :type normalize: bool
    :param dir: target canvas directory for saving plots 
    :type dir: str
    :rtype: list :class:`loki.core.plot.Plot`
    """  
    # set defaults  
    if prongs == 1: 
        from loki.common.vars import tidvars_1p as default_tidvars
        prongstr = "1P"
        pronglbl = "1-prong"
        if sel is None: 
            sel = taus.baseline1PNoTruth
    elif prongs == 3: 
        from loki.common.vars import tidvars_3p as default_tidvars
        prongstr = "3P"
        pronglbl = "3-prong"
        if sel is None: 
            sel = taus.baseline3PNoTruth
    else:   
        from loki.common.vars import tidvars as default_tidvars
        #prongstr = "AllProng"
        #pronglbl = "All prongs"
        prongstr = ""
        pronglbl = None
        if sel is None: 
            sel = taus.baseline
    if tidvars is None:
        tidvars = default_tidvars            
    if not isinstance(samples,list): 
        samples = [samples]

    # make plots                    
    plots = []
    for var in tidvars:
        # make a hist for each sample and add to plot  
        hists = []
        for s in samples: 
            hist_name = "%s%s%s"%(var.get_name(), prongstr, s.name)
            if tag: hist_name+=tag
            h = Hist(sample = s, name = hist_name, xvar = var, sel = sel, 
                     normalize = normalize)
            hists.append(h)
        plot_name = "%s%s"%(var.get_name(), prongstr)
        if tag: plot_name+=tag
        if normalize: plot_name += "_normalised"
        plot = Plot(plot_name, hists, extra_labels=pronglbl,dir=dir)
        plots.append(plot)
        plot_log = Plot(plot_name+"_log", hists, extra_labels=pronglbl,dir=dir, logy=True)
        plots.append(plot_log)

    return plots 


#______________________________________________________________________________=buf=
def create_tid_profiles(sample,tidvars=None,depvars=None,sel=None,prongs=None,
                        dir="profiles",tag=None):
    """Return list of variable distribution overlay plots
    
    :param samples: samples to overlay
    :type samples: list :class:`loki.core.sample.Sample`
    :param tidvars: variables to plot 
    :type tidvars: list :class:`loki.core.var.Var`
    :param depvars: dependent variables 
    :type depvars: list :class:`loki.core.var.Var`    
    :param sel: selection to apply
    :type sel: :class:`loki.core.cut.Cut` 
    :param prongs: number of prongs (typically 1 or 3)
    :type prongs: int
    :param dir: target canvas directory for saving plots 
    :type dir: str
    :rtype: list :class:`loki.core.plot.Plot`
    """  
    # set defaults  
    if depvars is None: 
        from loki.common.vars import depvars    
    if prongs == 1: 
        from loki.common.vars import tidvars_1p as default_tidvars
        prongstr = "1P"
        pronglbl = "1-prong"
        if sel is None: 
            sel = taus.baseline1PNoTruth
    elif prongs == 3: 
        from loki.common.vars import tidvars_3p as default_tidvars
        prongstr = "3P"
        pronglbl = "3-prong"
        if sel is None: 
            sel = taus.baseline3PNoTruth
    else:   
        from loki.common.vars import tidvars as default_tidvars
        prongstr = "AllProng"
        pronglbl = "All prongs"
        if sel is None: 
            sel = taus.baseline
    if tidvars is None:
        tidvars = default_tidvars            

    # make plots                    
    plots = []
    for var in tidvars:
        for depvar in depvars:
            # make a hist for each sample and add to plot               
            hist_name = "%s_vs_%s_%s%s"%(var.get_name(), depvar.get_name(), prongstr, sample.name)
            if tag: hist_name+=tag
            p = Profile(sample = sample, name = hist_name, 
                        xvar = depvar, yvar = var, sel = sel)
            plot_name = "%s_vs_%s_%s"%(var.get_name(), depvar.get_name(), prongstr)
            if tag: plot_name+=tag
            plot = Plot(plot_name, [p], extra_labels=pronglbl,dir=dir)
            plots.append(plot)

    return plots 



#______________________________________________________________________________=buf=
def create_roc(sample,bkg,
               sel_sig_1p=None,sel_bkg_1p=None,sel_sig_total_1p=None,
               sel_sig_3p=None,sel_bkg_3p=None,sel_sig_total_3p=None,
               tag=None,
               ):
    """Create ROC curves for 1-prong/3-prong taus
    
    Note: maybe better to pass 1p/3p selection as dict, like for wpdefs. 
    Then easy to modify (eg. plot ROCs for 5-way decay modes)
    
    :param sel_sig_1p:  signal selection (1-prong)
    :type sel_sig_1p: :class:`loki.core.cut.Cut`
    :param sel_bkg_1p:  background selection (1-prong)
    :type sel_bkg_1p: :class:`loki.core.cut.Cut`
    :param sel_sig_total_1p:  optional denominator selection for 1-prong signal (eg. to include reco. eff.)
    :type sel_sig_total_1p: :class:`loki.core.cut.Cut`
    :param sel_sig_3p:  signal selection (3-prong)
    :type sel_sig_3p: :class:`loki.core.cut.Cut`
    :param sel_bkg_3p:  background selection (3-prong)
    :type sel_bkg_3p: :class:`loki.core.cut.Cut`
    :param sel_sig_total_3p:  optional denominator selection for 3-prong signal (eg. to include reco. eff.)
    :type sel_sig_total_3p: :class:`loki.core.cut.Cut`
    :param tag: identifying string for plot names
    :type tag: str
    :rtype: list :class:`loki.core.plot.Plot`
    """
    if not sample.is_active():
        log().warn("No signal input files, skipping ROC plots...")
        return []
    if not bkg.is_active(): 
        log().warn("No background input files, skipping ROC plots...")
        return []             
                  
    # set defaults  
    if sel_sig_1p is None: sel_sig_1p = taus.baseline1P
    if sel_bkg_1p is None: sel_bkg_1p = taus.baseline1PNoTruth
    if sel_sig_3p is None: sel_sig_3p = taus.baseline3P
    if sel_bkg_3p is None: sel_bkg_3p = taus.baseline3PNoTruth
    xvar = taus.RNNJetScore.get_view("fine")

    # make a hist for each sample and add to plot
    rocname = "ROCMyWorld{0}"
    if tag: rocname+=tag
    roc1p = ROCCurve(sample,bkg,xvar = xvar,
                   sel_sig = sel_sig_1p, sel_bkg = sel_bkg_1p,
                   sel_sig_total = sel_sig_total_1p,
                   sty = styles.ROC1P,
                   name = rocname.format("1P"))
    roc3p = ROCCurve(sample,bkg,xvar = xvar,
                   sel_sig = sel_sig_3p, sel_bkg = sel_bkg_3p,
                   sel_sig_total = sel_sig_total_3p,
                   sty = styles.ROC3P,
                   name = rocname.format("3P"))
    plot_name = "ROC"
    if tag: plot_name+=tag
    plot = Plot(plot_name, [roc1p,roc3p], dir="roc", logy=True)
    return [plot] 
    return []


#______________________________________________________________________________=buf=
def create_roc_eveto(sample,bkg,
               sel_sig_1p=None,sel_bkg_1p=None,sel_sig_total_1p=None,
               tag=None,
               ):
    """Create ROC curves for 1-prong/3-prong taus
    
    TODO: merge this with *create_roc* (should be just one roc function)
    Note: maybe better to pass 1p/3p selection as dict, like for wpdefs. 
    Then easy to modify (eg. plot ROCs for 5-way decay modes)
    
    :param sel_sig_1p:  signal selection (1-prong)
    :type sel_sig_1p: :class:`loki.core.cut.Cut`
    :param sel_bkg_1p:  background selection (1-prong)
    :type sel_bkg_1p: :class:`loki.core.cut.Cut`
    :param sel_sig_total_1p:  optional denominator selection for 1-prong signal (eg. to include reco. eff.)
    :type sel_sig_total_1p: :class:`loki.core.cut.Cut`
    :param tag: identifying string for plot names
    :type tag: str
    :rtype: list :class:`loki.core.plot.Plot`
    """
    if not sample.is_active():
        log().warn("No signal input files, skipping ROC plots...")
        return []
    if not bkg.is_active(): 
        log().warn("No background input files, skipping ROC plots...")
        return []             
                  
    # set defaults  
    if sel_sig_1p is None: sel_sig_1p = taus.baseline1PNoTruth
    if sel_bkg_1p is None: sel_bkg_1p = taus.baseline1PNoTruth
    xvar = taus.RNNEleScore.get_view("fine")

    # make a hist for each sample and add to plot
    rocname = "EleRNNROCCurve{0}"
    if tag: rocname+=tag
    roc1p = ROCCurve(sample,bkg,xvar = xvar,
                   sel_sig = sel_sig_1p, sel_bkg = sel_bkg_1p,
                   sel_sig_total = sel_sig_total_1p,
                   sty = styles.ROC1P,
                   #reverse=True, #Not needed anymore
                   name = rocname.format("1P"))
    plot_name = "EleRNNROC"
    if tag: plot_name+=tag
    plot = Plot(plot_name, [roc1p], dir="roc", logy=True)
    return [plot] 
    return []



#______________________________________________________________________________=buf=
def create_roc_comparisons(sig,bkg,mvavars=None):
    """Create ROC curve comparisons for mva variables
    
    :param sig: signal sample
    :type sig: :class:`loki.core.sample.Sample`
    :param bkg: background sample
    :type bkg: :class:`loki.core.sample.Sample`
    :param vars: list of views of mva outputs to compare
    :type vars: list :class:`loki.core.var.View`        
    :rtype: list :class:`loki.core.plot.Plot`
    """

    style_list = styles.style_list
    rocs = []
    for (i, v) in enumerate(mvavars):
        name = v.var.name 
        sty = deepcopy(style_list[i])
        sty.name = name
        sty.tlatex = name
        sty.drawopt = "L"
        sty.LineWidth = 3
        rocs.append(ROCCurve(sig,bkg,xvar=v, name=name, sty=sty))
    p_roc = Plot("ROCComparison", rocs, dir="roc", logy=True)
    return [p_roc]


#______________________________________________________________________________=buf=
def baseline_plots(sample,bkg,lvl=0):
    """Return the baseline set of tau id plots"""
    plots = []

    ## level 0
    plots += create_eff_profiles_wrt_truth(sample,depvars=vars.depvars_base,prongs=1,tag="Lvl0")
    plots += create_eff_profiles_wrt_truth(sample,depvars=vars.depvars_base,prongs=3,tag="Lvl0")
    plots += create_eff_profiles(bkg,wpdefs=IDWP1P_for_fakes,depvars=vars.depvars_reco_base,
                                 prongs=1,wrt=False,tag="Lvl0_FakeRate",fakes=True)
    plots += create_eff_profiles(bkg,wpdefs=IDWP3P_for_fakes,depvars=vars.depvars_reco_base,
                                 prongs=3,wrt=False,tag="Lvl0_FakeRate",fakes=True)   
    plots += create_tid_variable_dists([sample,bkg],prongs=1,tidvars=[taus.RNNJetScore.get_view()],
                                       dir="basics", tag="Lvl0")
    plots += create_tid_variable_dists([sample,bkg],prongs=3,tidvars=[taus.RNNJetScore.get_view()],
                                       dir="basics", tag="Lvl0")
    

    ## level 1
    if lvl >= 1:    
        plots += create_eff_profiles_wrt_truth(sample,prongs=1,tag="Lvl1")
        plots += create_eff_profiles_wrt_truth(sample,prongs=3,tag="Lvl1")
        plots += create_eff_profiles_wrt_reco(sample,prongs=1,tag="Lvl1")
        plots += create_eff_profiles_wrt_reco(sample,prongs=3,tag="Lvl1")    
        plots += create_eff_profiles(bkg,wpdefs=IDWP1P_for_fakes,depvars=vars.depvars_reco,
                                     prongs=1,wrt=False,tag="Lvl1_FakeRate",fakes=True)
        plots += create_eff_profiles(bkg,wpdefs=IDWP3P_for_fakes,depvars=vars.depvars_reco,
                                     prongs=3,wrt=False,tag="Lvl1_FakeRate",fakes=True)
        plots += create_roc(sample,bkg,tag="Lvl1")
        plots += create_roc(sample,bkg, 
                            sel_sig_total_1p=truetaus.baseline1P,
                            sel_sig_total_3p=truetaus.baseline3P,
                            tag="Lvl1_WRTTruth")
        plots += create_tid_variable_dists([sample,bkg],prongs=1,tidvars=vars.depvars_reco,
                                           dir="basics",tag="Lvl1")
        plots += create_tid_variable_dists([sample,bkg],prongs=3,tidvars=vars.depvars_reco,
                                           dir="basics",tag="Lvl1")        

    ## level 2
    if lvl >= 2: 
        plots += create_tid_variable_dists([sample,bkg],prongs=1,tag="Lvl2")
        plots += create_tid_variable_dists([sample,bkg],prongs=3,tag="Lvl2")        
        plots += create_tid_profiles(sample,prongs=1,tag="Lvl2")
        plots += create_tid_profiles(sample,prongs=3,tag="Lvl2")
        plots += create_tid_profiles(sample,prongs=1,sel=taus.baseline1PNoTruth&taus.ptVeryHigh,
                                     dir="profiles_highpt",tag="Lvl2")
        plots += create_tid_profiles(sample,prongs=3,sel=taus.baseline3PNoTruth&taus.ptVeryHigh,
                                     dir="profiles_highpt",tag="Lvl2")
        
    ## level 3
    if lvl >= 3: 
        plots += create_tid_variable_dists([sample,bkg],prongs=1,tidvars=vars.tidvars_1p,
                                           dir="variables_uncorr",tag="Lvl3")
        plots += create_tid_variable_dists([sample,bkg],prongs=3,tidvars=vars.tidvars_3p,
                                           dir="variables_uncorr",tag="Lvl3")
        plots += create_tid_profiles(sample,prongs=1,tidvars=vars.tidvars_1p,
                                     dir="profiles_uncorr",tag="Lvl3")
        plots += create_tid_profiles(sample,prongs=3,tidvars=vars.tidvars_3p,
                                     dir="profiles_uncorr",tag="Lvl3")
        plots += create_tid_profiles(sample,prongs=1,sel=taus.baseline1PNoTruth&taus.ptVeryHigh,
                                     tidvars=vars.tidvars_1p,dir="profiles_highpt_uncorr",tag="Lvl3")
        plots += create_tid_profiles(sample,prongs=3,sel=taus.baseline3PNoTruth&taus.ptVeryHigh,
                                     tidvars=vars.tidvars_3p,dir="profiles_highpt_uncorr",tag="Lvl3")
            
                
    return plots   


#______________________________________________________________________________=buf=
def comparison_plots(samples, lvl=0):
    """Return tau id sample comparison plots"""
    depvars = vars.depvars_coarse
    plots = []
    plots += create_eff_profiles_wrt_truth(samples,prongs=1, depvars=depvars, wps=["Reco"])
    plots += create_eff_profiles_wrt_truth(samples,prongs=3, depvars=depvars, wps=["Reco"])
    plots += create_eff_profiles_wrt_reco(samples,prongs=1, depvars=depvars, wps=["Loose","Medium","Tight"])
    plots += create_eff_profiles_wrt_reco(samples,prongs=3, depvars=depvars, wps=["Loose","Medium","Tight"])    
    return plots
    

#______________________________________________________________________________=buf=
def baseline_ele_plots(sample,bkg,lvl=0):
    """Return the baseline set of electron veto plots"""
    plots = []
    global EleRNN1P_wrt_reco, EleRNN1P_for_fakes
    sel_base = EleRNN1P_for_fakes[0][1]["sel_total"]
    
    ## level 0
    plots += create_eff_profiles_wrt_reco(sample,prongs=1,wpdefs=EleRNN1P_wrt_reco,
                                          depvars=vars.depvars_base, tag="Lvl0_EleRNNEffWRTReco")
    plots += create_eff_profiles(bkg,wpdefs=EleRNN1P_for_fakes,depvars=vars.depvars_reco_base,
                                 prongs=1,wrt=False,tag="Lvl0_EleRNNFakeRate",fakes=True)
    plots += create_tid_variable_dists([sample,bkg],prongs=1,sel=sel_base,
                                       tidvars=[taus.RNNEleScore.get_view()])    
    
    ## level 1
    if lvl>=1:    
        plots += create_eff_profiles_wrt_reco(sample,prongs=1,wpdefs=EleRNN1P_wrt_reco,
                                              tag="EleRNNEffWRTReco")
        plots += create_eff_profiles(bkg,wpdefs=EleRNN1P_for_fakes,wrt=False,fakes=True,
                                     depvars=vars.depvars_reco,prongs=1,tag="EleRNNFakeRate")
        plots += create_roc_eveto(sample,bkg)
        plots += create_tid_variable_dists([sample,bkg],prongs=1,sel=sel_base,
                                           tidvars=vars.evetovars_1p)
                
    return plots   


#______________________________________________________________________________=buf=
def comparison_ele_plots(samples,lvl=0):
    """Return electron veto sample comparison plots"""
    depvars = vars.depvars_coarse
    plots = []
    plots += create_eff_profiles_wrt_reco(samples,prongs=1,depvars=depvars,wpdefs=EleRNN1P_wrt_reco,tag="EleRNNEffWRTReco")    
    return plots
    
'''

## EOF
