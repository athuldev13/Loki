# encoding: utf-8
"""
loki.trk.plots.py
~~~~~~~~~~~~~~~~~~~~

Configuration of standard tracking plots. 

"""
__author__    = "Dirk Duschinger"
__email__     = "dirk.duschinger@cern.ch"
__created__   = "2016-07-18"
__copyright__ = "Copyright 2016 Dirk Duschinger"
__license__   = "GPL http://www.gnu.org/licenses/gpl.html"


## modules
from loki.core.plot import Plot 
from loki.common import cuts, styles, vars
from loki.common.cuts import taus
from loki.core.hist import EffProfile, ResoProfile, Hist, MigrationMatrix
from loki.common.vars import taus, truetaus, tautracks, event
from loki.core.style import Style

# - - - - - - - - - - - plot creators  - - - - - - - - - - - - #
#______________________________________________________________________________=buf=
def create_track_classification_efficiency(sample, var, truth_prong):
    """Return list of reco/id efficiency profile plots

    Plots are always made for a particular truth prong tau, either 1p or 3p.

    A plot comparing efficiencies of taus being produced with the number of
    tracks provided in the list reco_prong_list is produced (w/o ratio plot).

    :param samples: input samples
    :type samples: list :class:`loki.core.sample.Sample`
    :param var: distribution for x-axis
    :type var: var :class:`loki.core.var.var`
    :param truth_prong: number of prong
    :type truth_prong: string
    """

    # axis settings
    ymin = .01
    ymax = 1.2
    logy = False

    plots = list()
    profiles = list()

    plname = "TrackClassificationEff_{var}".format(var = var.var.name)
    if var.name != "default":
        plname+="_"+var.name

    track_class_list = ["TT","CT","IT","FT"]
    for index, track_class in enumerate(track_class_list):
        total_cut = getattr(tautracks, f"true_{track_class}") & getattr(tautracks, f"mode{truth_prong}")

        # fix for TRT samples generated with mu>40
        if var.var.name != "mu":
            total_cut = total_cut & event.mu40
        
        pass_cut = total_cut & getattr(tautracks, f"reco_{track_class}")
        p = EffProfile(sample    = sample,
                       xvar      = var,
                       sel_pass  = pass_cut,
                       sel_total = total_cut
                      )
        profiles.append(p)
        index += 1
        marker_index = index
        if index > 4: index+=1
        if index > 9: index+=1
        p.sty = Style(track_class, LineColor=index,MarkerColor=index,MarkerStyle=19+marker_index,drawopt="P,E1")
    # create plot
    if truth_prong: 
        plname += f"_{truth_prong}"
    plot = Plot(plname, profiles, extra_labels=["#sqrt{s}=13TeV", f"truth {truth_prong}"], dir="efficiencies",
                ymin=ymin,ymax=ymax, logy=logy)
    plots.append(plot)

    return plots

#______________________________________________________________________________=buf=
def create_track_classification_efficiency_matrix(sample, truth_prong):
    """
    Return list of track classification matrix plots
    
    :param sel: selection
    :type sel: :class:`loki.core.cut.VarBase`    
    :param rownorm: toggle row-normalization (ie 'purity' matrix)
    :type rownorm: bool
    """

    sel  = None
    rownorm = None
    extra_labels = None

    plots = list()

    xvar = tautracks.TruthTypeCombined.get_view()
    yvar = tautracks.RecoType.get_view()
    mode  = "Purity" if rownorm else "Eff"
    hname = "MigrationMatrix{0}_TrackType".format(mode)
    if truth_prong:
        hname += "_{0}".format(truth_prong)
        sel = getattr(tautracks,"mode{0}".format(truth_prong))
        extra_labels = ["truth {0}".format(truth_prong)]
    h = MigrationMatrix(name=hname, sample=sample, xvar=xvar, yvar=yvar, sel=sel, rownorm=rownorm)
    plot = Plot(name=hname,rds=[h], extra_labels=extra_labels)
    plots.append(plot)

    return plots

#______________________________________________________________________________=buf=
def create_prongness_efficiency_all_prong_modes(sample,
                                                var,
                                                truth_prong,
                                                reco_prong_list,
                                                reco_type):
    """Return list of reco/id efficiency profile plots

    Plots are always made for a particular truth prong tau, either 1p or 3p.

    A plot comparing efficiencies of taus being produced with the number of
    tracks provided in the list reco_prong_list is produced (w/o ratio plot).
        
    :param samples: input samples
    :type samples: list :class:`loki.core.sample.Sample`
    :param var: distribution for x-axis
    :type var: var :class:`loki.core.var.var`
    :param truth_prong: number of prong (typically 1 or 3)
    :type truth_prong: int
    :param reco_prong_list: number of prong (typically 1 or 3)
    :type reco_prong_list: list
    :param truth_prong: number of prong (typically 1 or 3)
    :type truth_prong: int

    """

    # axis settings
    ymin = 0.0
    ymax = 1.2
    logy = False

    plots = list()
    profiles = list()

    plname = f"Tau{reco_type}RecoEff_{var.var.name}"
    if var.name != "default":
        plname+="_"+var.name

    total_cut = taus.baseline & getattr(taus, f"mode{truth_prong}Truth")

    # fix for TRT samples generated with mu>40
    if var.var.name != "mu":
         total_cut = total_cut & event.mu40

    for ind_prong, reco_prong in enumerate(reco_prong_list):
        pass_cut = total_cut & getattr(taus, f"mode{reco_prong}")
        p = EffProfile(sample    = sample,
                       xvar      = var,
                       sel_pass  = pass_cut,
                       sel_total = total_cut
                      )
        profiles.append(p)
        ind_prong += 1
        marker_index = ind_prong
        if ind_prong > 4: ind_prong+=1
        if ind_prong > 9: ind_prong+=1
        p.sty = Style(f"Reco {reco_prong}", LineColor=ind_prong,MarkerColor=ind_prong,MarkerStyle=19+marker_index,drawopt="P,E1")
    # create plot
    if truth_prong: 
        plname += f"_{truth_prong}"
    plot = Plot(plname, profiles, extra_labels=["#sqrt{s}=13TeV", f"truth {truth_prong}"], dir="efficiencies",
                ymin=ymin,ymax=ymax, logy=logy)
    plots.append(plot)

    return plots 

#______________________________________________________________________________=buf=
def create_prongness_efficiency_vs_old_reco(sample,
                                            var,
                                            truth_prong):
    """Return list of reco/id efficiency profile plots

    Plots are always made for a particular truth prong tau, either 1p or 3p.

    An efficiency comparison plot between new track classification and old tau
    track reconstruction is made including a ratio plot.
        
    :param samples: input samples
    :type samples: list :class:`loki.core.sample.Sample`
    :param var: distribution for x-axis
    :type var: var :class:`loki.core.var.var`
    :param truth_prong: number of prong (typically 1 or 3)
    :type truth_prong: int
    """

    # axis settings
    ymin = 0.0
    ymax = 1.2
    logy = False

    plots = list()
    profiles = list()

    plname = "TauMVAvsCUTRecoEff_{var}".format(var = var.var.name)
    if var.name != "default":
        plname+="_"+var.name

    doratio = True
    reco_prong_list = [truth_prong+"Old", truth_prong]
    total_cut = taus.baseline & getattr(taus, f"mode{truth_prong}Truth")

    # fix for TRT samples generated with mu>40
    if var.var.name != "mu":
         total_cut = total_cut & event.mu40

    for ind_prong, reco_prong in enumerate(reco_prong_list):
        pass_cut = total_cut & getattr(taus, f"mode{reco_prong}")
        p = EffProfile(sample    = sample,
                       xvar      = var,
                       sel_pass  = pass_cut,
                       sel_total = total_cut
                      )
        profiles.append(p)
        ind_prong += 1
        marker_index = ind_prong
        if ind_prong > 4: ind_prong+=1
        if ind_prong > 9: ind_prong+=1
        p.sty = Style(f"Reco {reco_prong}", LineColor=ind_prong,MarkerColor=ind_prong,MarkerStyle=19+marker_index,drawopt="P,E1")

    # create plot
    if truth_prong:
        plname += f"_{truth_prong}"
    plot = Plot(plname, profiles, extra_labels=["#sqrt{s}=13TeV", f"truth {truth_prong}"], dir="efficiencies",
                ymin=ymin,ymax=ymax, logy=logy, doratio = True)
    plots.append(plot)

    return plots 

#______________________________________________________________________________=buf=
def create_prongness_efficiency_comparison(samples,
                                           var,
                                           truth_prong,
                                           old_reco = False):
    """Return list of reco/id efficiency profile plots

    Plots are always made for a particular truth prong tau, either 1p or 3p.

    Efficiency comparison plots between the track clasifications are produced
    including a ratio plot.
        
    :param samples: input samples
    :type samples: list :class:`loki.core.sample.Sample`
    :param var: distribution for x-axis
    :type var: var :class:`loki.core.var.var`
    :param truth_prong: number of prong (typically 1 or 3)
    :type truth_prong: int
    """

    # axis settings
    ymin = 0.0
    ymax = 1.2
    logy = False

    plots = list()
    profiles = list()

    lSyst = []
    for sample in samples:
        lSyst.append(sample.name.replace("DYtautau_",""))
    plname = "TauComparisonRecoEff_{systs}_{var}".format(systs="_".join(lSyst),var = var.var.name)
    if old_reco:
        plname = "TauComparisonOldRecoEff_{systs}_{var}".format(systs="_".join(lSyst),var = var.var.name)
    if var.name != "default":
        plname+="_"+var.name

    total_cut = taus.baseline & getattr(taus, f"mode{truth_prong}Truth")

    # fix for TRT samples generated with mu>40
    if var.var.name != "mu":
         total_cut = total_cut & event.mu40
        
    for ind_sample, sample in enumerate(samples):
        if not old_reco: pass_cut = total_cut & getattr(taus, f"mode{truth_prong}")
        else:            pass_cut = total_cut & getattr(taus, f"mode{truth_prong}Old")
        p = EffProfile(sample    = sample,
                       name      = sample.name.replace("DYtautau_",""), 
                       xvar      = var,
                       sel_pass  = pass_cut,
                       sel_total = total_cut
                      )
        profiles.append(p)
        ind_sample += 1
        marker_index = ind_sample
        if ind_sample > 4: ind_sample+=1
        if ind_sample > 9: ind_sample+=1
        p.sty = Style(sample.name.replace("DYtautau_",""),
                      LineColor=ind_sample,
                      MarkerColor=ind_sample,
                      MarkerStyle=19+marker_index,
                      drawopt="P,E1")
    # create plot
    if truth_prong: 
        plname += f"_{truth_prong}"
    plot = Plot(plname, profiles, extra_labels=["#sqrt{s}=13TeV", f"truth {truth_prong}"], dir="efficiencies",
                ymin=ymin,ymax=ymax, logy=logy, doratio = True)
    plots.append(plot)

    return plots 

#______________________________________________________________________________=buf=
def create_tau_variable_plots(sample):
    """ Return list of tau track variable plots """
    
    plots = list()
    var_list = [tautracks.jetSeedPtGeV.get_view(),
                tautracks.jetSeedPtGeV.get_view("low"),
                tautracks.jetSeedPtGeV.get_view("log"),
                tautracks.trackEta.get_view(),
                tautracks.absz0sinThetaTJVA.get_view(),
                tautracks.rConv.get_view("low"),
                tautracks.rConv.get_view("log"),
                tautracks.rConvII.get_view("low"),
                tautracks.rConvII.get_view("log"),
                tautracks.rConvII.get_view("neg"),
                tautracks.rConvII.get_view("pos"),
                tautracks.dRJetSeedAxis.get_view(),
                tautracks.absd0.get_view(),
                tautracks.qOverP.get_view(),
                tautracks.numberOfInnermostPixelLayerHits.get_view(),
                tautracks.numberOfPixelSharedHits.get_view(),
                tautracks.numberOfSCTSharedHits.get_view(),
                tautracks.numberOfTRTHits.get_view(),
                tautracks.eProbabilityHT.get_view(),
                tautracks.numberOfPixelHits.get_view(),
                tautracks.numberOfPixelDeadSensors.get_view(),
                tautracks.numberOfSCTHits.get_view(),
                tautracks.numberOfSCTDeadSensors.get_view(),
                tautracks.truthMatchProbability.get_view(),
                tautracks.IsHadronicTrack.get_view(),
                tautracks.IsHadronicTrackDecayDepth.get_view(),
                tautracks.numberOfPixelHoles.get_view(),
                tautracks.numberOfSCTHoles.get_view(),
               ]

    # variables with track selection
    tracktype_list = ["TT", "CT", "IT", "FT"]

    for var in var_list:
        profiles = list()
        plname = "TauTracks_" + var.var.name
        if var.name != "default":
            plname += "_" + var.name
        
        for index, tracktype in enumerate(tracktype_list):
            sel = getattr(tautracks, "true_{0}".format(tracktype))
            p = Hist(sample = sample,
                     xvar   = var,
                     sel    = sel,
                     normalize = True
                    )
            profiles.append(p)
            index += 1
            marker_index = index
            if index > 4: index+=1
            if index > 9: index+=1
            p.sty = Style(sel.xtitle, LineColor=index,MarkerColor=index,MarkerStyle=19+marker_index,drawopt="P,E1")

        plot = Plot(plname, profiles)
        plots.append(plot)

    
    # # variables without selection
    # for var in var_list:
    #     plname = "TauTracks_" + var.var.name
    #     if var.name != "default":
    #         plname += "_" + var.name
    #     p = Hist(sample = sample, xvar = var, normalize = True)
        
    #     plot = Plot(plname, rds=[p])
    #     plots.append(plot)


    return plots

#______________________________________________________________________________=buf=
def baseline_plots(sample,lvl=0):
    """Return the baseline set of tau track plots"""
    
    plots = []
    tau_var_list = list()
    if lvl >= 0:
        tau_var_list.append(taus.ptTruthGeV.get_view())
        tau_var_list.append(taus.ptTruthGeV.get_view("low"))
    if lvl >= 1:
        tau_var_list.append(taus.etaTruth.get_view())
        tau_var_list.append(taus.phiTruth.get_view())
        tau_var_list.append(event.mu.get_view())
        tau_var_list.append(taus.nVtx.get_view())
    
    tautrack_var_list = list()
    if lvl >= 1:
        tautrack_var_list.append(tautracks.jetSeedPtGeV.get_view())
        tautrack_var_list.append(tautracks.jetSeedPtGeV.get_view("low"))
    if lvl >= 2:
        tautrack_var_list.append(tautracks.jetSeedEta.get_view())
        tautrack_var_list.append(tautracks.jetSeedPhi.get_view())
        tautrack_var_list.append(event.mu.get_view())
    
    truth_prong_list = ["1P","3P"]#,None]
    mva_reco_prong_list = ["0P","1P","2P","3P","4P"]
    cut_reco_prong_list = ["0POld","1POld","2POld","3POld","4POld"]
    for var in tau_var_list:
        for truth_prong in truth_prong_list:
            if lvl>=0: plots += create_prongness_efficiency_vs_old_reco(sample = sample, var = var, truth_prong = truth_prong)
            if lvl>=1: plots += create_prongness_efficiency_all_prong_modes(sample = sample, var = var, truth_prong = truth_prong, reco_prong_list = mva_reco_prong_list, reco_type = "MVA")
            if lvl>=2: plots += create_prongness_efficiency_all_prong_modes(sample = sample, var = var, truth_prong = truth_prong, reco_prong_list = cut_reco_prong_list, reco_type = "CUT")
            pass
    for var in tautrack_var_list:
        for truth_prong in truth_prong_list:
            plots += create_track_classification_efficiency(sample = sample, var = var, truth_prong = truth_prong)

    # matrix plots
    plots += create_track_classification_efficiency_matrix(sample = sample, truth_prong = None)
    if lvl>=1:
        for truth_prong in truth_prong_list:
            plots += create_track_classification_efficiency_matrix(sample = sample, truth_prong = truth_prong)

    # tau variable plots
    if lvl>=3: plots += create_tau_variable_plots(sample = sample)

    return plots

#______________________________________________________________________________=buf=
def comparison_plots(samples, lvl=0):
    """Return tau id sample comparison plots"""
    plots = []
    tau_var_list = list()
    if lvl >= 0:
        tau_var_list.append(taus.ptTruthGeV.get_view("log"))
        tau_var_list.append(taus.ptTruthGeV.get_view("low"))
    if lvl >= 1:
        tau_var_list.append(taus.etaTruth.get_view())
        tau_var_list.append(taus.phiTruth.get_view())
        tau_var_list.append(event.mu.get_view())
        tau_var_list.append(taus.nVtx.get_view())

    truth_prong_list = ["1P","3P"]#,None]
    for var in tau_var_list:
        for truth_prong in truth_prong_list:
            if lvl >= 0: plots += create_prongness_efficiency_comparison(samples = samples, var = var, truth_prong = truth_prong)
            if lvl >= 1: plots += create_prongness_efficiency_comparison(samples = samples, var = var, truth_prong = truth_prong, old_reco = True)

    return plots

# EOF
