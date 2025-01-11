# encoding: utf-8
"""
loki.tes.plots.py
~~~~~~~~~~~~~~~~~~~~

Configuration of standard TES/4-momentum plots. 

"""
__author__    = "Will Davey"
__email__     = "will.davey@cern.ch"
__created__   = "2016-02-21"
__copyright__ = "Copyright 2016 Will Davey"
__license__   = "GPL http://www.gnu.org/licenses/gpl.html"



## modules
from loki.common import styles, vars
from loki.common.cuts import taus
from loki.core.hist import ResoProfile, Hist
from loki.core.plot import Plot 

# - - - - - - - - - - - Resolution plots  - - - - - - - - - - - - #
# tau pt calibrations
ptres_algs = [
        ("TESLC",   {"yvar":taus.ptRes.get_view()          ,"sty":styles.TESLC}),
        ("TESSub",  {"yvar":taus.ptPanTauRes.get_view()    ,"sty":styles.TESSub}),
        ("TESFinal",{"yvar":taus.ptFinalCalibRes.get_view(),"sty":styles.TESFinal}),
        ("TESComb", {"yvar":taus.ptCombinedRes.get_view()  ,"sty":styles.TESComb}),
        ]

# Note: still to make this more flexible for adding algs and miminise code duplication
# tau eta calibrations
etares_algs = [
        ("TESLC",   {"yvar":taus.etaRes.get_view()          ,"sty":styles.TESLC}),
        ("TESFinal",{"yvar":taus.etaFinalCalibRes.get_view(),"sty":styles.TESFinal}),
        ]

# tau phi calibrations
phires_algs = [
        ("TESLC",   {"yvar":taus.phiRes.get_view()          ,"sty":styles.TESLC}),
        ("TESFinal",{"yvar":taus.phiFinalCalibRes.get_view(),"sty":styles.TESFinal}),
        ]

# tau pt profile modes
ptres_modes = ["winmode","core","tail"]

#______________________________________________________________________________=buf=
def create_res_profiles(samples,algdefs=None,depvars=None,algs=None,modes=None,
                        sel=None,tag=None):
    """Return list of resolution/closure profile plots

    Default mode is engaged if only one sample is specified in *samples*. 
    Then profiles for each alg are overlayed in each plot. 
    
    Multisample mode is engaged if multiple samples are specified in *samples*. 
    Then profiles for each sample are overlayed and a separate plot is made for 
    each alg. This mode also includes a ratio panel to compare 
    perforamnce across samples.
    
    :param sample: input samples
    :type sample: list :class:`loki.core.sample.Sample`
    :param algdefs: calibration algorithm definitions 
    :type algdefs: tuple (see :data:`ptres_algs`)
    :param depvars: dependent variables 
    :type depvars: list :class:`loki.core.tag.Var`
    :param algs: filter provided algorithms by name
    :type algs: list str
    :param modes: resolution/closure modes
    :type modes: list str (see :class:`loki.core.hist.ResoProfile` for options)
    :param sel: selection
    :type sel: :class:`loki.core.cut.VarBase`
    :param tag: unique identifier (for prof/plot names)
    :type tag: str
    :rtype: list :class:`loki.core.plot.Plot`
    """

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
    if algdefs is None: 
        global ptres_algs 
        algdefs = ptres_algs 
    if modes is None: 
        global ptres_modes
        modes = ptres_modes
    if depvars is None: 
        depvars = vars.depvars
    if sel is None: 
        sel = taus.tes1P3P

    # axis settings
    rmin = 0.9
    rmax = 1.1

    # Make the Plots
    plots = []
        
    # Multisample
    if multisample: 
        # profile name tempalte
        prof_name = "Res{mode}_{var}_vs_{depvar}_{tag}_{sname}"
        # plot name template
        plot_name = "Res{mode}_{var}_vs_{depvar}_{tag}"    
                
        # make separate plot for each depvar, mode and alg
        for depvar in depvars:
            for mode in modes:
                for (alg, args) in algdefs:
                    if algs and alg not in algs: continue
                    var = args["yvar"] 
                    # make profile for each sample and add to plot  
                    profiles = []
                    for s in samples: 
                        prname=prof_name.format(mode=mode,var=var.get_name(),depvar=depvar.get_name(),tag=tag,sname=s.name)                                    
                        profiles+=[ResoProfile(sample=s, name=prname, xvar=depvar, yvar=var,sel=sel, mode=mode)]
                                            
                    # create plot
                    (ymin,ymax) = get_corrected_yrange(var, mode)
                    plname = plot_name.format(mode=mode,var=var.get_name(),depvar=depvar.get_name(),tag=tag)
                    plots+=[Plot(plname, profiles, dir="profiles", ymin=ymin, ymax=ymax, doratio=True, rmax=rmax, rmin=rmin)]

    # Single sample
    else:     
        # profile name tempalte
        prof_name = "Res{mode}_{basename}_vs_{depvar}_{tag}_{var}" ##TODO what val to use if no algs...
        # plot name template
        plot_name = "Res{mode}_{basename}_vs_{depvar}_{tag}"
        # use name of first var as basename
        basename = [args["yvar"].get_name() for (alg,args) in algdefs][0]
        # make separate plot for each depvar and mode
        for depvar in depvars:
            for mode in modes:
                # make profile for each alg and add to plot  
                profiles = []
                for (alg,args) in algdefs: 
                    if algs and alg not in algs: continue
                    var = args["yvar"]
                    prname = prof_name.format(mode=mode,basename=basename,depvar=depvar.get_name(),tag=tag,var=var.get_name())
                    profiles+=[ResoProfile(sample=sample,name=prname,xvar=depvar,sel=sel,mode=mode,**args)]
                                    
                # create plot
                (ymin,ymax) = get_corrected_yrange(var, mode)
                plname = plot_name.format(mode=mode,basename=basename,depvar=depvar.get_name(),tag=tag)
                plots+=[Plot(plname, profiles, dir="profiles", ymin=ymin, ymax=ymax)]
    return plots 


#______________________________________________________________________________=buf=
def get_corrected_yrange(var,mode): 
    """Return corrected (ymin,ymax) for resolution profiles"""
    ymin = ymax = None
    if mode in ["median","mode","winmode"]: 
        ymin = var.get_xmin()
        ymax = var.get_xmax()
        width = (ymax - ymin)
        center = (ymax + ymin)/2.0
        ymin = center - width/10.0
        ymax = center + width/10.0
    return (ymin,ymax)

#______________________________________________________________________________=buf=
def create_resid_dists(sample,algdefs=None,algs=None,sel=None,tag="Pt"):
    """Return list of residual distribution plots
    
    :param sample: sample
    :type sample: :class:`loki.core.sample.Sample`
    :param algdefs: calibration algorithm definitions 
    :type algdefs: tuple (see :data:`ptres_algs`)
    :param algs: filter provided algorithms by name
    :type algs: list str
    :param sel: selection
    :type sel: :class:`loki.core.cut.Cut`
    :param tag: unique identifier (for prof/plot names)
    :type tag: str    
    :rtype: list :class:`loki.core.plot.Plot`
    """
    # set deaults
    if algdefs is None: 
        global ptres_algs 
        algdefs = ptres_algs 
    if sel is None: 
        sel = taus.baselineNoPt

    # hist name template
    hist_name = "Resid_{basename}_{tag}_{alg}"
    # plot name template
    plot_name = "Resid_{basename}_{tag}"
    # use name of first var as basename
    basename = [args["yvar"].get_name() for (alg,args) in algdefs][0]
    
    # create hists and plots
    plots = []
    hists = []
    for (alg,args) in algdefs: 
        if algs and alg not in algs: continue
        # create hist
        p = Hist(sample=sample,
                 name=hist_name.format(basename=basename,alg=alg,tag=tag),
                 xvar=args["yvar"],
                 sty=args["sty"],
                 sel=sel)
        hists.append(p)
        
    # create plot
    plot = Plot(plot_name.format(basename=basename,tag=tag),hists,dir="residuals")
    plots.append(plot)
    return plots 

#______________________________________________________________________________=buf=
def baseline_plots(sample,lvl=0):
    """Return the baseline set of tau energy scale plots"""
    plots = []
    
    ## level 0
    plots += create_res_profiles(sample,algs=["TESLC","TESFinal"], 
                                 depvars=vars.depvars_base, 
                                 modes=["core"], tag="Lvl0")
    plots += create_resid_dists(sample,algs=["TESLC","TESFinal"], tag="Lvl0")
    
    ## level 1
    if lvl>=1:
        prongs = ["1P","3P"]
        for prong in prongs:
            sel = getattr(taus, f"tes{prong}")
            tag = f"Lvl1_{prong}"
            plots += create_res_profiles(sample,sel=sel,tag=tag)
            plots += create_resid_dists(sample,sel=sel,tag=tag)
    
    ## level 2
    if lvl>=2:
        prongs = ["1P","3P"]
        etas = ["barrel","endcap"]
        kins = ["pt", "eta", "phi"]
        for prong in prongs:
            sel_prong = getattr(taus, f"tes{prong}")
            for eta in etas:
                sel_eta = getattr(taus,eta)
                sel = sel_prong & sel_eta
                for kin in kins:
                    algdefs = globals()[f"{kin}res_algs"]
                    tag = f"Lvl2_{prong}_{eta}"
                    plots += create_res_profiles(sample,algdefs=algdefs,sel=sel,tag=tag)
                    plots += create_resid_dists(sample,algdefs=algdefs,sel=sel,tag=tag)
    
    return plots


#______________________________________________________________________________=buf=
def comparison_plots(samples,lvl=0):
    """Return tau energy scale sample comparison plots"""
    plots = []
    depvars = vars.depvars_coarse
    
    ## level 0
    prongs = ["1P","3P"]
    etas = ["barrel","endcap"]
    kins = ["pt"]
    for prong in prongs:
        sel_prong = getattr(taus, f"tes{prong}")
        for eta in etas:
            sel_eta = getattr(taus,eta)
            sel = sel_prong & sel_eta
            for kin in kins:
                algdefs = globals()[f"{kin}res_algs"]
                tag = f"{prong}_{eta}"
                plots += create_res_profiles(samples,algdefs=algdefs,depvars=depvars,sel=sel,tag=tag)
        
    ## not higher level plots atm.
    return plots




## EOF
