# encoding: utf-8
"""
loki.tauid.plots.py
~~~~~~~~~~~~~~~~~~~~

Configuration of standard Tau ID plots. 

Note: currently no "ishad" criterion on match in numerator (wrt truth) since
applied in MxAOD production.

"""
__author__    = "Will Davey"
__email__     = "will.davey@cern.ch"
__created__   = "2016-02-21"
__copyright__ = "Copyright 2016 Will Davey"
__license__   = "GPL http://www.gnu.org/licenses/gpl.html"



## modules
from copy import deepcopy
from loki.common import cuts, styles, vars
from loki.common.vars import taus, truetaus
from loki.core.hist import Profile, EffProfile, Hist, ROCCurve
from loki.core.logger import log
from loki.core.plot import Plot

# - - - - - - - - - - - working points  - - - - - - - - - - - - #
# 1-prong ID working point efficiencies with respect to truth
IDWP1P_wrt_truth = [ 
    ("Reco"  , {"sel_total":taus.baseline & taus.mode1PTruth, 
                "sel_pass" :taus.baseline & taus.mode1PTruth & taus.mode1P, 
                "sty"      :styles.Reco}),
    ("Loose" , {"sel_total":taus.baseline & taus.mode1PTruth, 
                "sel_pass" :taus.baseline & taus.mode1PTruth & taus.mode1P & taus.loose,
                "sty"      :styles.Loose}),
    ("Medium", {"sel_total":taus.baseline & taus.mode1PTruth, 
                "sel_pass" :taus.baseline & taus.mode1PTruth & taus.mode1P & taus.medium,
                "sty"      :styles.Medium}),
    ("Tight" , {"sel_total":taus.baseline & taus.mode1PTruth, 
                "sel_pass" :taus.baseline & taus.mode1PTruth & taus.mode1P & taus.tight,
                "sty"      :styles.Tight}),
    ]

# 3-prong ID working point efficiencies with respect to truth
IDWP3P_wrt_truth = [ 
    ("Reco"  , {"sel_total":taus.baseline & taus.mode3PTruth, 
                "sel_pass" :taus.baseline & taus.mode3PTruth & taus.mode3P,
                "sty"      :styles.Reco}),
    ("Loose" , {"sel_total":taus.baseline & taus.mode3PTruth, 
                "sel_pass" :taus.baseline & taus.mode3PTruth & taus.mode3P & taus.loose,
                "sty"      :styles.Loose}),
    ("Medium", {"sel_total":taus.baseline & taus.mode3PTruth, 
                "sel_pass" :taus.baseline & taus.mode3PTruth & taus.mode3P & taus.medium,
                "sty"      :styles.Medium}),
    ("Tight" , {"sel_total":taus.baseline & taus.mode3PTruth, 
                "sel_pass" :taus.baseline & taus.mode3PTruth & taus.mode3P & taus.tight,
                "sty"      :styles.Tight}),
    ]


# 1-prong ID working point efficiencies with respect to reco
IDWP1P_wrt_reco = []
for (name,args) in IDWP1P_wrt_truth[1:]:
    args_copy = dict(args)
    args_copy["sel_total"] = args_copy["sel_total"] & taus.mode1P
    IDWP1P_wrt_reco.append([name,args_copy])
     
# 3-prong ID working point efficiencies with respect to reco
IDWP3P_wrt_reco = []
for (name,args) in IDWP3P_wrt_truth[1:]:
    args_copy = dict(args)
    args_copy["sel_total"] = args_copy["sel_total"] & taus.mode3P
    IDWP3P_wrt_reco.append([name,args_copy])

# 1-prong ID working point for fake-rates
IDWP1P_for_fakes = [ 
    ("Loose" , {"sel_total":taus.baseline1PNoTruth, 
                "sel_pass" :taus.baseline1PNoTruth & taus.loose,
                "sty"      :styles.Loose}),
    ("Medium", {"sel_total":taus.baseline1PNoTruth, 
                "sel_pass" :taus.baseline1PNoTruth & taus.medium,
                "sty"      :styles.Medium}),
    ("Tight" , {"sel_total":taus.baseline1PNoTruth, 
                "sel_pass" :taus.baseline1PNoTruth & taus.tight,
                "sty"      :styles.Tight}),
    ]

# 3-prong ID working point for fake-rates
IDWP3P_for_fakes = [ 
    ("Loose" , {"sel_total":taus.baseline3PNoTruth, 
                "sel_pass" :taus.baseline3PNoTruth & taus.loose,
                "sty"      :styles.Loose}),
    ("Medium", {"sel_total":taus.baseline3PNoTruth, 
                "sel_pass" :taus.baseline3PNoTruth & taus.medium,
                "sty"      :styles.Medium}),
    ("Tight" , {"sel_total":taus.baseline3PNoTruth, 
                "sel_pass" :taus.baseline3PNoTruth & taus.tight,
                "sty"      :styles.Tight}),
    ]

# - - - - - - - - - - - eVeto working points  - - - - - - - - - - - - #
# 1-prong EleRNN efficiency with respect to reco+medium ID
EleRNN1P_wrt_reco = [ 
    ("EleRNN" , {"sel_total":taus.baseline1P & taus.medium,
                 "sel_pass" :taus.baseline1P & taus.medium & taus.EleRNNMedium,
                 "sty"      :styles.Medium}),
    ]
     
# 1-prong EleRNN for fake-rates
EleRNN1P_for_fakes = [ 
    ("EleRNN" , {"sel_total":taus.baseline1PNoTruth & taus.medium, 
                 "sel_pass" :taus.baseline1PNoTruth & taus.medium & taus.EleRNNMedium,
                 "sty"      :styles.Medium}),
    ]



# - - - - - - - - - - - plot creators  - - - - - - - - - - - - #
#______________________________________________________________________________=buf=
def create_eff_profiles(samples,wpdefs=None,depvars=None,prongs=None,wps=None,
                        wrt=False,tag="IDEff",fakes=False):
    """Return list of reco/id efficiency profile plots
    
    Default mode is engaged if only one sample is specified in *samples*. 
    Then profiles for each working point are overlayed in each plot. 
    
    Multisample mode is engaged if multiple samples are specified in *samples*. 
    Then profiles for each sample are overlayed and a separate plot is made for 
    each working point. This mode also includes a ratio panel to compare 
    perforamnce across samples.    
    
    :param samples: input samples
    :type samples: list :class:`loki.core.sample.Sample`
    :param wpdefs: ID working point definitions 
    :type wpdefs: tuple (see :data:`IDWP1P_wrt_truth`)
    :param depvars: dependent variables 
    :type depvars: list :class:`loki.core.var.Var`
    :param prongs: number of prongs (typically 1 or 3)
    :type prongs: int
    :param wps: filter provided working-points by name
    :type wps: list str
    :param wrt: calculate efficiency with respect to truth (ie xvar.get_truth_partner() for denominator)
    :type wrt: bool 
    :param tag: identifying string for plot names
    :type tag: str
    :param fakes: set plot attributes accordingly for fake-rates (rather than signal eff.)
    :type fakse: bool
    :rtype: list :class:`loki.core.plot.Plot`
    """
    assert wpdefs is not None, "Must provide list of working points 'wpdefs'"
    
    # determine if 'multisample' (or single sample)
    if not isinstance(samples,list): 
        sample = samples
        multisample = False
    elif len(samples) == 1: 
        sample = samples[0]
        multisample = False
    else:
        multisample = True

    # set defaults
    if depvars is None: 
        from loki.common.vars import depvars
    if prongs == 1: 
        prongstr = "1P"
        pronglbl = "1-prong"
    elif prongs == 3: 
        prongstr = "3P"
        pronglbl = "3-prong"
    else:   
        prongstr = "AllProng"
        pronglbl = "All prongs"
    
    # axis settings
    ymin = 0.0
    ymax = 1.0
    rmin = 0.9
    rmax = 1.1
    logy = False
    if fakes:  
        #ymin = ymax = None
        ymax = None
        #logy = True
    
    # Make the Plots
    plots = []
        
    # Multisample
    if multisample: 
        # profile name template
        prof_name = "{tag}{wp}{prongs}{var}{sname}"
        # plot name template
        plot_name = "{tag}{wp}{prongs}{var}" 

        # make separate plot for each working point and depvar
        for (wp,args) in wpdefs:
            # working point filter
            if wps and wp not in wps: continue
            args = {k:v for (k,v) in args.items() if k in ["sel_total","sel_pass"]}
            for var in depvars:
                xvar_total = var.get_truth_partner() if wrt else None
                # make profile for each sample and add to plot
                profiles = []
                for s in samples:
                    sname = s.sty.name                    
                    prname = prof_name.format(tag=tag,wp=wp,prongs=prongstr,var=var.get_name(),sname=sname)
                    profiles += [EffProfile(sample=s, name=prname, xvar=var, xvar_total=xvar_total, **args)]
                    
                # create plot
                plname = plot_name.format(tag=tag,wp=wp,prongs=prongstr,var=var.get_name())
                plot = Plot(plname, profiles, extra_labels=[pronglbl,tag],
                            dir="efficiencies", ymin=ymin,ymax=ymax, logy=logy,
                            doratio=True, rmax=rmax, rmin=rmin)
                plots.append(plot)

    # Single sample
    else: 
        # profile name template
        prof_name = "{tag}{wp}{prongs}{var}"
        # plot name template
        plot_name = "{tag}{prongs}{var}"         
                        
        # make separate plot for each depvar
        for var in depvars:
            xvar_total = var.get_truth_partner() if wrt else None
            # make profile for each working point and add to plot
            profiles = []
            for (wp,args) in wpdefs: 
                # working point filter
                if wps and wp not in wps: continue
                prname = prof_name.format(tag=tag,wp=wp,prongs=prongstr,var=var.get_name())
                p = EffProfile(sample=sample, name=prname, xvar=var, xvar_total=xvar_total,**args)
                profiles.append(p)
                
            # create plot
            plname = plot_name.format(tag=tag,prongs=prongstr,var=var.get_name())
            plot = Plot(plname, profiles, extra_labels=pronglbl, dir="efficiencies",
                        ymin=ymin,ymax=ymax, logy=logy)
            plots.append(plot)


    return plots 

#______________________________________________________________________________=buf=
def create_eff_profiles_wrt_truth(samples,wpdefs=None,depvars=None,prongs=None,
                                  wps=None,tag=None):
    """Wrapper for :func:`create_eff_profiles` with *wpdefs* defined with respect
    to truth by default. 
    """
    if wpdefs is None: 
        if prongs == 1:
            global IDWP1P_wrt_truth
            wpdefs = IDWP1P_wrt_truth
        elif prongs == 3:  
            global IDWP3P_wrt_truth
            wpdefs = IDWP3P_wrt_truth
    if tag is None: 
        tag = "IDEffWRTTruth"
    return create_eff_profiles(samples,wpdefs,depvars,prongs,wps,wrt=False,tag=tag)


#______________________________________________________________________________=buf=
def create_eff_profiles_wrt_reco(samples,wpdefs=None,depvars=None,prongs=None,
                                 wps=None,tag=None):
    """Wrapper for :func:`create_eff_profiles` with *wpdefs* defined with respect
    to reco by default. 
    """    
    if wpdefs is None: 
        if prongs == 1:
            global IDWP1P_wrt_reco
            wpdefs = IDWP1P_wrt_reco
        elif prongs == 3:  
            global IDWP3P_wrt_reco
            wpdefs = IDWP3P_wrt_reco
    if depvars is None: 
        depvars = vars.depvars_reco     
    if tag is None: 
        tag = "IDEffWRTReco"
    return create_eff_profiles(samples,wpdefs,depvars,prongs,wps,wrt=False,tag=tag)


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
            hist_name = f"{var.get_name()}{prongstr}{s.name}"
            if tag: hist_name+=tag
            h = Hist(sample = s, name = hist_name, xvar = var, sel = sel, 
                     normalize = normalize)
            hists.append(h)
        plot_name = f"{var.get_name()}{prongstr}"
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
            hist_name = f"{var.get_name()}_vs_{depvar.get_name()}_{prongstr}{sample.name}"
            if tag: hist_name+=tag
            p = Profile(sample = sample, name = hist_name, 
                        xvar = depvar, yvar = var, sel = sel)
            plot_name = f"{var.get_name()}_vs_{depvar.get_name()}_{prongstr}"
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
    plots += create_eff_profiles_wrt_truth(sample,depvars=vars.depvars_base,prongs=1,tag="Lvl0_EffWRTTruth")
    plots += create_eff_profiles_wrt_truth(sample,depvars=vars.depvars_base,prongs=3,tag="Lvl0_EffWRTTruth")
    plots += create_eff_profiles(bkg,wpdefs=IDWP1P_for_fakes,depvars=vars.depvars_reco_base,
                                 prongs=1,wrt=False,tag="Lvl0_FakeRate",fakes=True)
    plots += create_eff_profiles(bkg,wpdefs=IDWP3P_for_fakes,depvars=vars.depvars_reco_base,
                                 prongs=3,wrt=False,tag="Lvl0_FakeRate",fakes=True)   
    plots += create_tid_variable_dists([sample,bkg],prongs=1,tidvars=[taus.RNNJetScore.get_view()],
                                       dir="basics", tag="Lvl0_Dist")
    plots += create_tid_variable_dists([sample,bkg],prongs=3,tidvars=[taus.RNNJetScore.get_view()],
                                       dir="basics", tag="Lvl0_Dist")
    

    ## level 1
    if lvl >= 1:    
        plots += create_eff_profiles_wrt_truth(sample,prongs=1,tag="Lvl1_EffWRTTruth")
        plots += create_eff_profiles_wrt_truth(sample,prongs=3,tag="Lvl1_EffWRTTruth")
        plots += create_eff_profiles_wrt_reco(sample,prongs=1,tag="Lvl1_EffWRTReco")
        plots += create_eff_profiles_wrt_reco(sample,prongs=3,tag="Lvl1_EffWRTReco")    
        plots += create_eff_profiles(bkg,wpdefs=IDWP1P_for_fakes,depvars=vars.depvars_reco,
                                     prongs=1,wrt=False,tag="Lvl1_FakeRate",fakes=True)
        plots += create_eff_profiles(bkg,wpdefs=IDWP3P_for_fakes,depvars=vars.depvars_reco,
                                     prongs=3,wrt=False,tag="Lvl1_FakeRate",fakes=True)
        plots += create_roc(sample,bkg,tag="Lvl1_ROCWRTReco")
        plots += create_roc(sample,bkg, 
                            sel_sig_total_1p=taus.baseline & taus.mode1PTruth, 
                            sel_sig_total_3p=taus.baseline & taus.mode3PTruth, 
                            tag="Lvl1_ROCWRTTruth")
        plots += create_tid_variable_dists([sample,bkg],prongs=1,tidvars=vars.depvars_reco,
                                           dir="basics",tag="Lvl1_Dist")
        plots += create_tid_variable_dists([sample,bkg],prongs=3,tidvars=vars.depvars_reco,
                                           dir="basics",tag="Lvl1_Dist")        

    ## level 2
    if lvl >= 2: 
        plots += create_tid_variable_dists([sample,bkg],prongs=1,tag="Lvl2_Dist")
        plots += create_tid_variable_dists([sample,bkg],prongs=3,tag="Lvl2_Dist")        
        plots += create_tid_profiles(sample,prongs=1,tag="Lvl2_Profile")
        plots += create_tid_profiles(sample,prongs=3,tag="Lvl2_Profile")
        plots += create_tid_profiles(sample,prongs=1,sel=taus.baseline1PNoTruth&taus.ptVeryHigh,
                                     dir="profiles_highpt",tag="Lvl2_Profile")
        plots += create_tid_profiles(sample,prongs=3,sel=taus.baseline3PNoTruth&taus.ptVeryHigh,
                                     dir="profiles_highpt",tag="Lvl2_Profile")
        
    ## level 3
    if lvl >= 3: 
        plots += create_tid_variable_dists([sample,bkg],prongs=1,tidvars=vars.tidvars_1p,
                                           dir="variables_uncorr",tag="Lvl3_Dist")
        plots += create_tid_variable_dists([sample,bkg],prongs=3,tidvars=vars.tidvars_3p,
                                           dir="variables_uncorr",tag="Lvl3_Dist")
        plots += create_tid_profiles(sample,prongs=1,tidvars=vars.tidvars_1p,
                                     dir="profiles_uncorr",tag="Lvl3_Profile")
        plots += create_tid_profiles(sample,prongs=3,tidvars=vars.tidvars_3p,
                                     dir="profiles_uncorr",tag="Lvl3_Profile")
        plots += create_tid_profiles(sample,prongs=1,sel=taus.baseline1PNoTruth&taus.ptVeryHigh,
                                     tidvars=vars.tidvars_1p,dir="profiles_highpt_uncorr",tag="Lvl3_Profile")
        plots += create_tid_profiles(sample,prongs=3,sel=taus.baseline3PNoTruth&taus.ptVeryHigh,
                                     tidvars=vars.tidvars_3p,dir="profiles_highpt_uncorr",tag="Lvl3_Profile")
            
                
    return plots   


#______________________________________________________________________________=buf=
def comparison_plots(samples, lvl=0):
    """Return tau id sample comparison plots"""
    depvars = vars.depvars_coarse
    plots = []
    plots += create_eff_profiles_wrt_truth(samples,prongs=1, depvars=depvars, wps=["Reco","Loose","Medium","Tight"])
    plots += create_eff_profiles_wrt_truth(samples,prongs=3, depvars=depvars, wps=["Reco","Loose","Medium","Tight"])
    plots += create_eff_profiles_wrt_reco(samples,prongs=1, depvars=depvars, wps=["Loose","Medium","Tight"])
    plots += create_eff_profiles_wrt_reco(samples,prongs=3, depvars=depvars, wps=["Loose","Medium","Tight"])    
    return plots
    
## EOF
