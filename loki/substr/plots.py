# encoding: utf-8
"""
loki.substr.plots.py
~~~~~~~~~~~~~~~~~~~~

Configuration of standard substructure plots. 

Note: currently no "ishad" criterion on match in numerator (wrt truth) since
applied in MxAOD production.

"""
__author__    = "Will Davey"
__email__     = "will.davey@cern.ch"
__created__   = "2016-02-21"
__copyright__ = "Copyright 2016 Will Davey"
__license__   = "GPL http://www.gnu.org/licenses/gpl.html"



## modules
from loki.common import styles, vars
from loki.common.cuts import taus
from loki.core.hist import EffProfile, Hist, MigrationMatrix
from loki.core.plot import Plot


# - - - - - - - - - - - decay mode classification efficiencies - - - - - - - - - - - - #
# Decay mode classification efficiencies with respect to reco 
classification_defs = [ 
    ("1P0N"  , {"sel_total":taus.baseline & taus.mode1P0NTruth, 
                "sel_pass" :taus.baseline & taus.mode1P0NTruth & taus.mode1P0N, 
                "sty"      :styles.m1P0N}),
    ("1P1N"  , {"sel_total":taus.baseline & taus.mode1P1NTruth,
                "sel_pass" :taus.baseline & taus.mode1P1NTruth & taus.mode1P1N, 
                "sty"      :styles.m1P1N}),
    ("1PXN"  , {"sel_total":taus.baseline & taus.mode1PXNTruth, 
                "sel_pass" :taus.baseline & taus.mode1PXNTruth & taus.mode1PXN, 
                "sty"      :styles.m1PXN}),
    ("3P0N"  , {"sel_total":taus.baseline & taus.mode3P0NTruth, 
                "sel_pass" :taus.baseline & taus.mode3P0NTruth & taus.mode3P0N, 
                "sty"      :styles.m3P0N}),
    ("3PXN"  , {"sel_total":taus.baseline & taus.mode3PXNTruth, 
                "sel_pass" :taus.baseline & taus.mode3PXNTruth & taus.mode3PXN, 
                "sty"      :styles.m3PXN}),
    ]

# Proto decay mode classification efficiencies with respect to reco 
proto_classification_defs = [ 
    ("1P0N"  , {"sel_total":taus.baseline & taus.mode1P0NTruth, 
                "sel_pass" :taus.baseline & taus.mode1P0NTruth & taus.mode1P0NProto, 
                "sty"      :styles.m1P0N}),
    ("1P1N"  , {"sel_total":taus.baseline & taus.mode1P1NTruth,
                "sel_pass" :taus.baseline & taus.mode1P1NTruth & taus.mode1P1NProto, 
                "sty"      :styles.m1P1N}),
    ("1PXN"  , {"sel_total":taus.baseline & taus.mode1PXNTruth, 
                "sel_pass" :taus.baseline & taus.mode1PXNTruth & taus.mode1PXNProto, 
                "sty"      :styles.m1PXN}),
    ("3P0N"  , {"sel_total":taus.baseline & taus.mode3P0NTruth, 
                "sel_pass" :taus.baseline & taus.mode3P0NTruth & taus.mode3P0NProto, 
                "sty"      :styles.m3P0N}),
    ("3PXN"  , {"sel_total":taus.baseline & taus.mode3PXNTruth, 
                "sel_pass" :taus.baseline & taus.mode3PXNTruth & taus.mode3PXNProto, 
                "sty"      :styles.m3PXN}),
    ]
    

# - - - - - - - - - - - plot creator  - - - - - - - - - - - - #
#______________________________________________________________________________=buf=
def create_eff_plots(sample,wpdefs=None,depvars=None,wps=None,tag=None):
    """Return list of decay mode classification efficiency profile plots
    
    :param sample: sample
    :type sample: :class:`loki.core.sample.Sample`
    :param wpdefs: ID working point definitions 
    :type wpdefs: tuple (see :data:`IDWP1P_wrt_truth`)
    :param depvars: dependent variables 
    :type depvars: list :class:`loki.core.var.Var`
    :param wps: filter provided working-points by name
    :type wps: list str
    :param tag: tag to distinguish plot if making mutltiple with different settings
    :type tag: str
    :rtype: list :class:`loki.core.plot.Plot`
    """
    # set defaults    
    if wpdefs is None: 
        global classification_defs 
        wpdefs = classification_defs 
    if depvars is None:
        depvars = vars.depvars 

    # profile name template
    prof_name = "ClassEff{wp}{var}"
    # plot name template
    plot_name = "ClassEff{var}"
    extra_lables = None
    if tag: 
        prof_name += "_"+tag
        plot_name += "_"+tag
        extra_lables = [tag]

    # make plots
    plots = []
    for var in depvars:
        profiles = []
        for (wp,args) in wpdefs: 
            if wps and wp not in wps: continue
            fullargs = args.copy()
            fullargs["xvar"] = var
            # make profile
            p = EffProfile(sample=sample,
                           name=prof_name.format(wp=wp,var=var.get_name()),                           
                           **fullargs)
            profiles.append(p)
            
        # make plot
        plot = Plot(plot_name.format(var=var.get_name()),
                    profiles,extra_labels=extra_lables,
                    dir="efficiencies",
                    ymin=0.0,ymax=1.0)
        plots.append(plot)
    return plots 


#______________________________________________________________________________=buf=
def create_decay_mode_split_distributions(sample,wpdefs=None,tidvars=None,wps=None,
                                          stack=True,normalize=None,stack_normalize=None,
                                          tag=None):
    """Return list of decay mode classification efficiency profile plots
    
    :param sample: sample
    :type sample: :class:`loki.core.sample.Sample`
    :param wpdefs: decay mode classification definitions 
    :type wpdefs: tuple (see :data:`classification_defs`)
    :param tidvars: variables to plot 
    :type tidvars: list :class:`loki.core.var.Var`
    :param wps: filter provided working-points by name
    :type wps: list str
    :param stack: stack distributions from different decay modes
    :type stack: bool
    :param stack_normalize: normalize each bin of stack separately
    :type stack_normalize: bool
    :rtype: list :class:`loki.core.plot.Plot`
    """
    # set defaults
    if wpdefs is None: 
        global classification_defs 
        wpdefs = classification_defs 
    if tidvars is None:  
        tidvars = []
        tidvars += vars.tidvars
        tidvars += [vars.taus.numTrack.get_view()]

    # hist name template
    hist_name = "{wp}{var}"
    # plot name template
    plot_name = "TruthDecayModeSplit{var}"
    if tag is not None:
        hist_name += tag
        plot_name += tag

    # make plots
    plots = []
    for var in tidvars: 
        hists = []
        # make hists
        for (wp,args) in wpdefs: 
            if wps and wp not in wps: continue
            fullargs = {
                    "xvar":var,
                    "sel":args["sel_total"],
                    "sty":args["sty"],
                    "normalize":normalize,
                    }
            p = Hist(sample=sample,
                     name=hist_name.format(wp=wp,var=var.get_name()),
                     **fullargs)
            hists.append(p)
            
        # make plot
        plot = Plot(plot_name.format(var=var.get_name()),hists,
                    stack=stack,stack_normalize=stack_normalize,
                    dir="variables")
        plots.append(plot)

    return plots 




#______________________________________________________________________________=buf=
def create_matrix_plots(sample,yvar=None,sel=None,rownorm=False,tag=None):
    """Return list of decay mode classification efficiency matrix plots
    
    :param sample: sample
    :type sample: :class:`loki.core.sample.Sample`
    :param yvar: reco decay mode variable 
    :type yvar: :class:`loki.core.var.View`
    :param sel: selection
    :type sel: :class:`loki.core.cut.VarBase`    
    :param rownorm: toggle row-normalization (ie 'purity' matrix)
    :type rownorm: bool
    :param tag: tag to distinguish plot if making mutltiple with different settings
    :type tag: str
    :rtype: list :class:`loki.core.plot.Plot`
    """
    # set defaults
    xvar = taus.decayModeTruth.get_view()    
    if yvar is None:
        yvar = taus.decayMode.get_view()
    if sel is None: 
        sel = taus.baseline & taus.isSubCand & taus.isSubCandTruth
    
    mode = "Purity" if rownorm else "Eff"
    hname = f"MigrationMatrix{mode}_{yvar.get_name()}"
    if tag: hname+=tag
    pname = "Plot" + hname
    h = MigrationMatrix(name=hname, sample=sample, xvar=xvar, yvar=yvar, sel=sel, rownorm=rownorm)
    p = Plot(name=pname,rds=[h], ymax=6)
    return [p]


#______________________________________________________________________________=buf=
def baseline_plots(sample,lvl=0):
    """Return the baseline set of tau substructure plots"""
    plots = []
    
    ## level 0
    plots += create_matrix_plots(sample,tag="Lvl0")
    plots += create_eff_plots(sample,depvars=vars.depvars_base,tag="Lvl0")
    
    ## level 1
    if lvl >= 1: 
        plots += create_eff_plots(sample,tag="Lvl1")
        
    ## level 2
    if lvl >= 2:
        plots += create_decay_mode_split_distributions(sample,tag="Lvl2")    
    
    return plots


## EOF
