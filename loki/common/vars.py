# encoding: utf-8
"""
loki.common.vars
~~~~~~~~~~~~~~~~

Definition of variables

"""
__author__    = "Will Davey"
__email__     = "will.davey@cern.ch"
__created__   = "2016-02-20"
__copyright__ = "Copyright 2016 Will Davey"
__license__   = "GPL http://www.gnu.org/licenses/gpl.html"



## modules
from loki.core.var import Container, Var, Expr, default_weight

# - - - - - - - - - - - globals  - - - - - - - - - - - - #
# Standard binnings
#===================
bins_pt_def    = [  51, 20.,  1000.  ]
bins_pt_low    = [  20, 20.,   100.  ]
bins_pt_log    = [  10, 20.,  2000.  ]
bins_pt_weight = [  20, 20.,  2000.  ]
bins_pt_eveto  = [  20, 20.,  1000.  ]
bins_pt_eveto_coarse  = [  10, 20.,  1000.  ]
bins_pt_weight15 = [22, 15.,  2000.  ]
bins_eta       = [  25, -2.5,    2.5 ]
bins_abseta    = [  25,  0.,     2.5 ]
bins_pt_res    = [1000,  0.,     2.  ]
bins_eta_res   = [1000, -0.05,   0.05]
bins_prongs    = [  10,  0.,    10.  ]
bins_decaymode = [   5,  0.,     5.  ]
bins_bdtScores = [ 100, -1.,     1.  ]

xbins_abseta = [0.0, 0.05, 0.3, 0.6, 0.8, 1.15, 1.37, 1.52, 1.81, 2.01, 2.30, 2.50]
#xbins_abseta = [0., 0.3, 0.8, 1.37, 1.52, 2.0, 2.3, 2.5]
xbins_abseta_eveto = [0.0, 1.37, 1.52, 2.0, 2.3, 2.5]
xbins_abseta_eveto_fine = [0.0, 0.6, 0.8, 1.15, 1.37, 1.52, 1.81, 2.01, 2.37, 2.47]
xbins_pt_tid = [20000., 25178., 31697., 39905., 50237., 63245., 79621., 100000., 
                130000., 200000., 316978., 502377., 796214., 1261914., 2000000.]

binnames_decaymode = [
    "1p0n", 
    "1p1n",
    "1pXn",
    "3p0n",
    "3pXn",
    ]
binnames_decaymode_fancy = [
    "#it{h}^{#pm}", 
    "#it{h}^{#pm}#scale[0.5]{ }#it{#pi}^{0}",
    "#it{h}^{#pm}#scale[0.5]{ }#geq2#it{#pi}^{0}",
    "3#it{h}^{#pm}",
    "3#it{h}^{#pm}#scale[0.5]{ }#geq1#it{#pi}^{0}",
    ]



# Unit Conversions
#===================
MeV2GeV = 1.e-3



# - - - - - - - - - - - function defs  - - - - - - - - - - - - #
def dot(l,m):
    """Return dot product of lists *l* and *m*"""
    return [a*b for (a,b) in zip(l,m)]

#------------------------------------------------------------------------------=buf=
def add_ptviews(var, MeV=False):
    """Add standard pt-binnings to *var*"""
    if MeV: scale = [1, 1000., 1000.]
    else:   scale = [1, 1., 1.]
    var.add_view(*dot(bins_pt_def,scale)) \
       .add_view(*dot(bins_pt_low,scale), name="low") \
       .add_view(*dot(bins_pt_log,scale), name="log", do_logx=True) \
       .add_view(*dot(bins_pt_weight,scale), name="weight", do_logx=True) \
       .add_view(*dot(bins_pt_weight15,scale), name="weight15", do_logx=True) \
       .add_view(*dot(bins_pt_eveto,scale), name="eveto", do_logx=True) \
       .add_view(*dot(bins_pt_eveto_coarse,scale), name="eveto_coarse", do_logx=True)

#------------------------------------------------------------------------------=buf=
# - - - - - - - - - - - variable defs  - - - - - - - - - - - - #
# Containers
#===================
#: EventInfo container
event = Container("EventInfo", single_valued=True)
#: Reco Tau container
taus = Container("TauJets")
#: True Tau container
truetaus = Container("TruthTaus")
#: Tau Track Container
tautracks = Container("TauTracks")

#===================
#: dummy variable
dummyvar = Expr('Dummy', '0.5', invars=[], xtitle = 'Dummy').add_view(1,0.,1.)

#: efficiency axis definition
effvar = Var('efficiency', xtitle = 'Efficiency').add_view(1,0.,1.)

#: default weight (no weight)
noweight = default_weight()

#: weight variable (used in flat ntuples)
weight = Var("weight")

#: pt re-weight variable (used in flat ntuples)
taus.add_var('weight_pt')


# Event Variables
#===================
#: average interactions per bunch crossing
event.add_var('mu', 'averageInteractionsPerCrossing', 'Average Interactions Per Bunch Crossing') \
     .add_view(80,-0.5,79.5) \
     .add_view(20,-0.5,39.5,"tid")
     
#: MC event weights (multi-valued: typically don't use this directly)
event.add_var('mcEventWeights', 'mcEventWeights')
#: MC event weight (had to hack to specify first array value) 
event.add_expr("weight_mc", "{0}[0]", invars=[event.mcEventWeights])
#: Truth resonance mass
event.add_var('truth_resonance_mass','truth_resonance_mass', 'Truth resonance mass', xunit="MeV")
event.add_expr('truth_resonance_massGeV','{0}/1000.', [event.truth_resonance_mass], 
               'Truth resonance mass', xunit="GeV") \
     .add_view(100,0.,5000.)


# Reco Tau Core/Kinematic Variables
#==================================
#: number of primary vertices (note: attached to tau objects in MxAOD)
taus.add_var('nVtx', 'nVtxPU', 'Number of primary vertices') \
    .add_view(40, -0.5, 39.5) \
    .add_view(15, 5., 35., "tid")

#: average interactions per bunch crossing (note: attached to tau objects in MxAOD)
taus.add_var('mu', 'mu', 'Average Interactions Per Bunch Crossing') \
     .add_view(80,-0.5,79.5) \
     .add_view(20,-0.5,39.5,"tid")

#: Reco tau number of core tracks 
taus.add_var('numTrack', 'nTracks', 'Reco Tau Num Track') \
    .add_view(*bins_prongs)

#: Reco tau decay mode 
taus.add_var('decayMode', 'PanTau_DecayMode', 'Reco Tau Decay Mode') \
    .add_view(*bins_decaymode, binnames=binnames_decaymode)

#: Reco tau decay mode proto 
taus.add_var('decayModeProto', 'pantau_CellBasedInput_DecayModeProto', 'Reco Tau Decay Mode Proto') \
    .add_view(*bins_decaymode, binnames=binnames_decaymode)

#: Reco tau :math:`p_{T}`
taus.add_var('pt', 'pt', 'Reco Tau p_{T}', xunit="MeV")
add_ptviews(taus.pt,MeV=True)
taus.add_expr('ptGeV', '{0}/1000.', [taus.pt], 'Reco Tau p_{T}', xunit="GeV")
add_ptviews(taus.ptGeV)

#: Reco tau :math:`p_{T}` (PanTau)
taus.add_var('ptPanTau', 'ptPanTauCellBased', 'PanTau Tau p_{T}', xunit="MeV")
add_ptviews(taus.ptPanTau,MeV=True)
taus.add_expr('ptPanTauGeV', '{0}/1000.', [taus.ptPanTau], 'PanTau Tau p_{T}', xunit="GeV")
add_ptviews(taus.ptPanTauGeV)

#: Reco tau :math:`p_{T}` (FinalCalib)
taus.add_var('ptFinalCalib', 'ptFinalCalib', 'Final Tau p_{T}', xunit="MeV")
add_ptviews(taus.ptFinalCalib,MeV=True)
taus.add_expr('ptFinalCalibGeV', '{0}/1000.', [taus.ptFinalCalib], 'Final Tau p_{T}', xunit="GeV")
add_ptviews(taus.ptFinalCalibGeV)

#: Reco tau :math:`p_{T}` (Combined)
taus.add_var('ptCombined', 'pt_combined', 'Combined Tau p_{T}', xunit="MeV")
add_ptviews(taus.ptCombined,MeV=True)
taus.add_expr('ptCombinedGeV', '{0}/1000.', [taus.ptCombined], 'Combined Tau p_{T}', xunit="GeV")
add_ptviews(taus.ptCombinedGeV)

#: Reco tau :math:`\eta`
taus.add_var('eta', 'eta', 'Reco Tau #eta') \
    .add_view(*bins_eta)

#: Reco tau :math:`|\eta|`
taus.add_expr('abseta', 'abs({0})', [taus.eta], 'Reco Tau |#eta|') \
    .add_view(xbins=xbins_abseta) \
    .add_view(xbins=xbins_abseta_eveto, name="eveto")

#: Reco tau :math:`\eta` (FinalCalib)
taus.add_var('etaFinalCalib', 'etaFinalCalib', 'Final Tau #eta') \
    .add_view(*bins_eta)

#: Reco tau track :math:`\eta`
taus.add_var("leadTrackEta", "leadTrackEta", "Lead track #eta") \
    .add_view(*bins_eta)

#: Reco tau track :math:`|\eta|`
taus.add_var('absleadTrackEta', 'ABS_ETA_LEAD_TRACK', 'Reco Tau |#eta|') \
    .add_view(xbins=xbins_abseta) \
    .add_view(xbins=xbins_abseta_eveto, name="eveto") \
    .add_view(*bins_abseta, name="fine")
    
#taus.add_expr("absleadTrackEta", "abs({0})", [taus.leadTrackEta], "Lead track |#eta|") \
#    .add_view(xbins=xbins_abseta) \
#    .add_view(xbins=xbins_abseta_eveto, name="eveto")

    
#: Reco tau :math:`\phi`
taus.add_var('phi', 'phi', 'Reco Tau #phi') \
    .add_view(*bins_eta)

#: Reco tau :math:`\phi` (FinalCalib)
taus.add_var('phiFinalCalib', 'phiFinalCalib', 'Final Tau #phi') \
    .add_view(*bins_eta)


# Tau ID Variables
#============================
taus.add_var("isTauFlags", "isTauFlags")
#: Reco tau RNN Jet score
taus.add_var('RNNJetScore', 'RNNJetScore', 'Reco Tau RNN Jet Score') \
    .add_view(50, 0., 1.) \
    .add_view(1000, 0., 1., name="fine")
taus.add_var('RNNJetScoreSigTrans', 'RNNJetScoreSigTrans', 'Reco Tau Flattened RNN Jet Score') \
    .add_view(50, 0., 1.)
taus.add_var('etOverPtLeadTrk')            .add_view(20, 0., 10.0)
taus.add_var('ipSigLeadTrk')               .add_view(20, -10., 10.0)
taus.add_expr('absipSigLeadTrk','abs({0})', invars=[taus.ipSigLeadTrk]).add_view(20, 0., 10.0)
taus.add_var('trFlightPathSig')            .add_view(20, 0., 10.0)
taus.add_var('massTrkSys', xunit="MeV")    .add_view(20, 0., 5000.0)
taus.add_var('dRmax')                      .add_view(20, 0., 0.2)
taus.add_var('ChPiEMEOverCaloEME')         .add_view(20, -3.0, 3.0)
taus.add_var('EMPOverTrkSysP')             .add_view(20, 0., 10.0)
taus.add_var('ptRatioEflowApprox')         .add_view(20, 0., 5.0)
taus.add_var('mEflowApprox', xunit="MeV")  .add_view(20, 0., 5000.0)
taus.add_var('centFrac')                   .add_view(20, 0., 1.2)
taus.add_var('innerTrkAvgDist')            .add_view(20, 0., 0.2)
taus.add_var('SumPtTrkFrac')               .add_view(20, 0., 2.0)

taus.add_expr("etPtAsymm", "({0} - 1) / ({0} + 1)", [taus.etOverPtLeadTrk]) \
    .add_view(20, -1., 1.)


# Electron Rejection Variables
#============================
#: Reco tau BDT Ele score
taus.add_var('RNNEleScore', 'RNNEleScore', 'Reco Tau R22 RNN Ele Score') \
    .add_view(50, 0., 1.) \
    .add_view(1000, 0., 1., name="fine")
taus.add_var('RNNEleScoreSigTrans', 'RNNEleScoreSigTrans', 'Reco Tau Flattened R22 RNN Ele Score') \
    .add_view(50, 0., 1.) \
    .add_view(1000, 0., 1., name="fine")
    
taus.add_var("leadTrackProbHT", "leadTrackProbHT", "Lead track eProbHT") \
    .add_view(20, 0., 1.)
taus.add_var("leadTrackDeltaEta","TAU_ABSDELTAETA","Tau-track #eta distance") \
    .add_view(20, 0., 0.2)
taus.add_var("leadTrackDeltaPhi","TAU_ABSDELTAPHI","Tau-track #phi distance") \
    .add_view(20, 0., 0.2)
taus.add_var("PSFrac","PSSFraction","PS") \
    .add_view(20, 0., 1.)

# new fixed variables
taus.add_var("etHotShotDR1").add_view(20, 0, 50000)
taus.add_var("etHotShotWin").add_view(20, 0, 50000)
taus.add_var("etHotShotDR1OverPtLeadTrk").add_view(20, 0, 2.0)
taus.add_var("etHotShotWinOverPtLeadTrk").add_view(20, 0, 2.0)
taus.add_var("EMFracFixed").add_view(20, 0., 2.)
taus.add_var("hadLeakFracFixed").add_view(20, -0.1, 1.9)


# broken / deprecated / unused variables
taus.add_var("etEMOverPtLeadTrk","sumEMCellEtOverLeadTrkPt","#it{E}_{T}^{EM} / Lead track #it{p}_{T}") \
    .add_view(20, 0., 10.)
taus.add_var("secMaxStripEt", "secMaxStripEt", "Max stip-cell #it{E}_{T}", xunit="MeV") \
    .add_view(20, 0., 30.)
taus.add_expr("maxStripFrac","{0} / {1}", [taus.secMaxStripEt,taus.pt]) \
    .add_view(20, 0., 2.e-4)
taus.add_var("hadLeakEt","HADLEAKET","hadLeakEt") \
    .add_view(20, 0., 1.5)
taus.add_expr("hadLeadFrac","{0} / {1}", [taus.hadLeakEt,taus.pt]) \
    .add_view(20, 0., 3.e-5)
taus.add_var("secMaxStripEtOverPt", "TAU_SEEDTRK_SECMAXSTRIPETOVERPT", "TAU_SEEDTRK_SECMAXSTRIPETOVERPT") \
    .add_view(20, 0, 2.0)
taus.add_var("EMFrac", "EMFRACTIONATEMSCALE_MOVEE3", "EM fraction") \
    .add_view(20, 0., 1.)
taus.add_var("HTFrac", "TAU_TRT_NHT_OVER_NLT", "High Threshold Hit fraction") \
    .add_view(20, 0., 1.)




# True Tau Variables
#===================
#: True tau number of prongs
truetaus.add_var('numProng', 'numCharged', 'True Tau Num Prong') \
    .add_view(*bins_prongs)

## TODO: get decay mode attached to true taus

#: True tau visible :math:`p_{T}` 
truetaus.add_var('pt', 'pt_vis', 'True Tau p_{T}', xunit="MeV")
add_ptviews(truetaus.pt,MeV=True)
truetaus.add_expr('ptGeV', '{0}/1000.', [truetaus.pt], 'True Tau p_{T}', xunit="GeV")
add_ptviews(truetaus.ptGeV)

#: True tau visible :math:`\eta`
truetaus.add_var('eta', 'eta_vis', 'True Tau #eta') \
    .add_view(*bins_eta)

#: True tau visible :math:`|\eta|`
truetaus.add_expr('abseta', 'abs({0})', [truetaus.eta], 'True Tau |#eta|') \
    .add_view(xbins=xbins_abseta) \
    .add_view(xbins=xbins_abseta_eveto, name="eveto")

#: True tau visible :math:`\phi`
truetaus.add_var('phi', 'phi_vis', 'True Tau #phi') \
    .add_view(*bins_eta)


# Reco Tau Truth Match Variables
#===============================
#: Reco tau truth-match number of prongs
taus.add_var('numProngTruth', 'truthProng', 'True Tau Num Prong', truth_partner = truetaus.numProng) \
    .add_view(*bins_prongs)

#: Reco tau truth-match decay mode 
taus.add_var('decayModeTruth', 'truthDecayMode', 'True Tau Decay Mode') \
    .add_view(*bins_decaymode, binnames=binnames_decaymode)

#: Reco tau truth-match visible :math:`p_{T}`
taus.add_var('ptTruth', 'truthPtVis', 'True Tau p_{T}', 
            xunit="MeV", truth_partner = truetaus.pt)
add_ptviews(taus.ptTruth,MeV=True)
taus.add_expr('ptTruthGeV', '{0}/1000.', [taus.ptTruth], 'True Tau p_{T}', 
            xunit="GeV", truth_partner = truetaus.ptGeV)
add_ptviews(taus.ptTruthGeV)

#: Reco tau truth-match visible :math:`\eta`
taus.add_var('etaTruth', 'truthEtaVis', 'True Tau #eta', truth_partner = truetaus.eta) \
    .add_view(*bins_eta)

#: Reco tau truth-match visible :math:`|\eta|`
taus.add_expr('absetaTruth', 'abs({0})', [taus.etaTruth], 'True Tau |#eta|', truth_partner = truetaus.abseta) \
    .add_view(xbins=xbins_abseta) \
    .add_view(xbins=xbins_abseta_eveto, name="eveto")

#: Reco tau truth-match visible :math:`\phi`
taus.add_var('phiTruth', 'truthPhiVis', 'True Tau #phi', truth_partner = truetaus.phi) \
    .add_view(*bins_eta)
    

# Reco Tau Response Variables
#============================ 
#: Reco tau baseline Energy Resolution
taus.add_expr('ptRes', '({0})/({1})', [taus.pt,taus.ptTruth], 'Reco Tau p_{T} / True Tau p_{T}', short_title = "Tau p_{T}") \
    .add_view(*bins_pt_res)

#: Reco tau PanTau Energy Resolution 
taus.add_expr('ptPanTauRes', '({0})/({1})', [taus.ptPanTau,taus.ptTruth], 'Reco Tau p_{T} / True Tau p_{T}', short_title = "Tau p_{T}") \
    .add_view(*bins_pt_res)

#: Reco tau FinalCalib Energy Resolution 
taus.add_expr('ptFinalCalibRes', '({0})/({1})', [taus.ptFinalCalib,taus.ptTruth], 'Reco Tau p_{T} / True Tau p_{T}', short_title = "Tau p_{T}") \
    .add_view(*bins_pt_res)

#: Reco tau Combined Energy Resolution 
taus.add_expr('ptCombinedRes', '({0})/({1})', [taus.ptCombined,taus.ptTruth], 'Reco Tau p_{T} / True Tau p_{T}', short_title = "Tau p_{T}") \
    .add_view(*bins_pt_res)

#: Reco tau baseline Eta Resolution 
taus.add_expr('etaRes', '{0}-{1}', [taus.eta,taus.etaTruth], 'Reco Tau #eta - True Tau #eta', short_title = "Tau #eta") \
    .add_view(*bins_eta_res)

#: Reco tau FinalCalib Eta Resolution
taus.add_expr('etaFinalCalibRes', '{0}-{1}', [taus.etaFinalCalib,taus.etaTruth], 'Reco Tau #eta - True Tau #eta', short_title = "Tau #eta") \
    .add_view(*bins_eta_res)

#: Reco tau baseline Phi Resolution 
taus.add_expr('phiRes', '{0}-{1}', [taus.phi,taus.phiTruth], 'Reco Tau #phi - True Tau #phi', short_title = "Tau #phi") \
    .add_view(*bins_eta_res)

#: Reco tau FinalCalib Eta Resolution
taus.add_expr('phiFinalCalibRes', '{0}-{1}', [taus.phiFinalCalib,taus.phiTruth], 'Reco Tau #phi - True Tau #phi', short_title = "Tau #phi") \
    .add_view(*bins_eta_res)


# Tau Track Variables
#===============================
#: Truth track type
tautracks.add_var('TruthType','TruthType','truth track type') \
    .add_view(7, -0.5, 6.5)
tautracks.add_expr('TruthTypeCombined','({0} == 1)*1 + ({0} == 2)*2 + ({0} == 3)*3 + ({0} == 0 || {0} >= 4)*4',
                   [tautracks.TruthType], 'truth track type') \
    .add_view(4, 0.5, 4.5, binnames=["TT", "CT", "IT", "FT"])

#: Reco classification track type
tautracks.add_var('flagSet','flagSet','classification flag bit set')
tautracks.add_var('tauTruthProng','tauTruthProng','prongness of true tau')
tautracks.add_var('RecoType', 'RecoType', 'reco track type') \
    .add_view(5, 0.5, 5.5, binnames=["TT", "CT", "IT", "FT", ""])

#: track jet sed variables
tautracks.add_var('jetSeedPt','jetSeedPt','pt of tau jet seed')
tautracks.add_expr('jetSeedPtGeV', '{0}/1000.', [tautracks.jetSeedPt], 'pt of tau jet seed', xunit="GeV") \
    .add_view(*bins_pt_def) \
    .add_view(*bins_pt_low, name="low") \
    .add_view(*bins_pt_log, name="log", do_logx=True)
    
tautracks.add_var('jetSeedEta','jetSeedEta','eta of tau jet seed') \
    .add_view(*bins_eta)
tautracks.add_var('jetSeedPhi','jetSeedPhi','phi of tau jet seed') \
    .add_view(*bins_eta)

tautracks.add_var("trackEta")\
    .add_view(100,-3., 3. )
tautracks.add_var("z0sinThetaTJVA")
tautracks.add_expr("absz0sinThetaTJVA", "abs({0})", [tautracks.z0sinThetaTJVA], "tau track |z0sinThetaTJVA|")\
    .add_view(100, 0., 500., do_logy=True)
tautracks.add_var("rConv")\
    .add_view(100, 0., 100., name="low")\
    .add_view(100, 0., 450000., name="log", do_logy=True)
tautracks.add_var("rConvII")\
    .add_view(100, -350000., 450000., name="log", do_logy=True)\
    .add_view(100, -100., 100., name="low" )\
    .add_view(100, -150., 0., do_logy=True, name="neg" )\
    .add_view(100, 0., 150., do_logy=True, name="pos" )
tautracks.add_var("dRJetSeedAxis")\
    .add_view(100, 0., 0.62 )
tautracks.add_var("d0")
tautracks.add_expr("absd0", "abs({0})", [tautracks.d0], "tau track |d0|")\
    .add_view(100, 0., 180., do_logy=True)
tautracks.add_var("qOverP")\
    .add_view(100, -0.0028, 0.0028 )
tautracks.add_var("numberOfInnermostPixelLayerHits")\
    .add_view(5, -0.5, 4.5 )
tautracks.add_var("numberOfPixelSharedHits")\
    .add_view(9, -0.5, 8.5, do_logy=True)
tautracks.add_var("numberOfSCTSharedHits")\
    .add_view(14, -0.5, 13.5, do_logy=True)
tautracks.add_var("numberOfTRTHits")\
    .add_view(81, -0.5, 80.5 )
tautracks.add_var("eProbabilityHT")\
    .add_view(100, 0., 1. )
tautracks.add_var("truthMatchProbability")\
    .add_view(200, 0.05, 1.01, do_logy=True)
tautracks.add_var("IsHadronicTrack")\
    .add_view(2, 0, 2 )
tautracks.add_var("IsHadronicTrackDecayDepth")\
    .add_view(2, -0.5, 1.5 )
tautracks.add_var("numberOfPixelHits")\
    .add_view(12, -0.5, 11.5 )
tautracks.add_var("numberOfPixelDeadSensors")\
    .add_view(4, -0.5, 3.5 )
tautracks.add_var("numberOfSCTHits")\
    .add_view(24, -0.5, 23.5 )
tautracks.add_var("numberOfSCTDeadSensors")\
    .add_view(5, -0.5, 4.5, do_logy=True)
tautracks.add_var("numberOfPixelHoles")\
    .add_view(3, -0.5, 2.5 )
tautracks.add_var("numberOfSCTHoles")\
    .add_view(4, -0.5, 3.5 )
tautracks.add_expr("nPixHits", "{0}+{1}", [tautracks.numberOfPixelHits, tautracks.numberOfPixelDeadSensors])
tautracks.add_expr("nSiHits", "{0}+{1}+{2}+{3}", [tautracks.numberOfPixelHits, tautracks.numberOfPixelDeadSensors,
                                                  tautracks.numberOfSCTHits, tautracks.numberOfSCTDeadSensors])

# - - - - - - - - - - - variable lists  - - - - - - - - - - - - #
#: list of dependent variables for profiles 
depvars = [taus.ptTruthGeV.get_view("log"), 
           taus.ptTruthGeV.get_view("low"), 
           taus.etaTruth.get_view(), 
           taus.mu.get_view(), 
           #taus.nVtx.get_view(), 
           ]

#: list of dependent variables for profiles (coarse binned eg. for systematics)
depvars_coarse = [taus.ptTruthGeV.get_view("log"),
                  taus.absetaTruth.get_view(),
                  ]

#: list of reco-level only dependent variables (eg. for fakes)
depvars_reco = [taus.ptGeV.get_view("log"), 
                taus.ptGeV.get_view("low"),
                taus.eta.get_view(),
                taus.mu.get_view(),
                taus.nVtx.get_view(),
                ]

#: list of reco-level only dependent variables for profiles (coarse binned eg. for systematics)
depvars_reco_coarse = [taus.ptGeV.get_view("log"),
                       taus.abseta.get_view(),
                       ]

#: list of dependent vars for baseline (prio0) plots 
depvars_base = [taus.ptTruthGeV.get_view("log")]
depvars_reco_base = [taus.ptGeV.get_view("log")]

#: list of 1-prong tau identification variables (not pileup corrected)
tidvars_1p = [v.get_view() for v in [
        taus.RNNJetScore,
        taus.centFrac,        
        taus.etOverPtLeadTrk,
        taus.innerTrkAvgDist,
        taus.absipSigLeadTrk,    
        taus.SumPtTrkFrac,
        taus.ChPiEMEOverCaloEME,
        taus.EMPOverTrkSysP,
        taus.ptRatioEflowApprox,
        taus.mEflowApprox,        
        ]
    ]

#: list of 3-prong tau identification variables (not pileup corrected)
tidvars_3p = [v.get_view() for v in [
        taus.RNNJetScore,
        taus.centFrac,
        taus.etOverPtLeadTrk,
        taus.innerTrkAvgDist,
        taus.dRmax,
        taus.trFlightPathSig,
        taus.massTrkSys,
        taus.ChPiEMEOverCaloEME,
        taus.EMPOverTrkSysP,
        taus.ptRatioEflowApprox,
        taus.mEflowApprox,        
        ]    
    ]

#: list of 1-prong tau electron rejection variables
evetovars_1p = [v.get_view() for v in [
        taus.RNNEleScore,
        taus.absleadTrackEta,
        taus.leadTrackDeltaEta, 
        taus.leadTrackDeltaPhi,
        taus.centFrac, 
        taus.etOverPtLeadTrk,
        taus.etEMOverPtLeadTrk,
        taus.etPtAsymm, 
        taus.innerTrkAvgDist,
        taus.EMFrac, 
        #taus.HTFrac, ##TODO: check that this is no longer used 
        taus.leadTrackProbHT, 
        taus.secMaxStripEt, 
        taus.maxStripFrac, 
        taus.PSFrac, 
        taus.hadLeakEt, 
        taus.hadLeadFrac,
        taus.ChPiEMEOverCaloEME,
        taus.secMaxStripEtOverPt,
        taus.etHotShotDR1, 
        taus.etHotShotWin,
        taus.etHotShotDR1OverPtLeadTrk, 
        taus.etHotShotWinOverPtLeadTrk,
        taus.EMFracFixed,
        taus.hadLeakFracFixed,        
        #taus.etHadAtEMScale, 
        #taus.etEMAtEMScale, 
        #taus.CORRFTRK,   
        ]
    ]

evetovars_3p = list(evetovars_1p)

 
#: list of tau identification variables
tidvars = list(set(tidvars_1p+tidvars_3p))
evetovars = list(evetovars_1p)
 
# EOF
