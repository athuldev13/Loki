# encoding: utf-8
"""
loki.common.cuts
~~~~~~~~~~~~~~~~
 
Definition of selection criteria. 

The selection criteria can be added to a container as an expression 
(:class:`loki.core.var.Expr`) via :func:`loki.core.var.Container.add_expr`, 
or as a single boolean variable (:class:`loki.core.var.Var`) via
:func:`loki.core.var.Container.add_var`. Multiple selection criteria can 
be combined via :func:`loki.core.var.Container.add_cuts`.

Criteria can also be defined independently from a container by calling the 
Var, Expr or Cuts constructors directly. 

Any of these selection criteria forms can also be combined together via the 
'&' operator (do not use the 'and' operator). 

"""
__author__    = "Will Davey"
__email__     = "will.davey@cern.ch"
__created__   = "2016-02-20"
__copyright__ = "Copyright 2016 Will Davey"
__license__   = "GPL http://www.gnu.org/licenses/gpl.html"



## modules
from loki.core import enums
from loki.core.var import default_cut
from loki.common.vars import taus, truetaus, event, tautracks



# - - - - - - - - - - - cut defs  - - - - - - - - - - - - #

#: default weight (no weight)
nocut = default_cut()

# Reco Tau Cuts
#==============
taus.add_var("matched", "IsTruthMatched")

# kinematic cuts 
taus.add_expr("eta25", "abs({0})<2.5", invars = [taus.eta])
taus.add_expr("vetoCrack", "( abs({0})<1.37 || abs({0}) > 1.52 )", invars = [taus.eta])
taus.add_expr("barrel", "abs({0})<1.37", invars = [taus.eta])
taus.add_expr("endcap", "abs({0})>1.52", invars = [taus.eta])

taus.add_expr("pt20", "{0}>20.0", invars = [taus.ptGeV])
taus.add_expr("pt30", "{0}>30.0", invars = [taus.ptGeV])
taus.add_expr("ptLow", "{0}>20.0 && {0}<50.0", invars = [taus.ptGeV])
taus.add_expr("ptMid", "{0}>50.0 && {0}<100.0", invars = [taus.ptGeV])
taus.add_expr("ptHigh", "{0}>100.0 && {0}<500.0", invars = [taus.ptGeV])
taus.add_expr("ptVeryHigh", "{0}>500.0", invars = [taus.ptGeV])

# truth kinematics
taus.add_expr("eta25Truth", "abs({0})<2.5", invars = [taus.etaTruth])
taus.add_expr("vetoCrackTruth", "( abs({0})<1.37 || abs({0}) > 1.52 )", invars = [taus.etaTruth])
taus.add_expr("pt20Truth", "{0}>20.0", invars = [taus.ptTruthGeV])

# prongs 
taus.add_expr("mode0P",      "{0}==0", invars = [taus.numTrack])
taus.add_expr("mode1P",      "{0}==1", invars = [taus.numTrack])
taus.add_expr("mode2P",      "{0}==2", invars = [taus.numTrack])
taus.add_expr("mode3P",      "{0}==3", invars = [taus.numTrack])
taus.add_expr("mode4P",      "{0}==4", invars = [taus.numTrack])
taus.add_expr("mode1PTruth", "{0}==1", invars = [taus.numProngTruth])
taus.add_expr("mode3PTruth", "{0}==3", invars = [taus.numProngTruth])

taus.add_expr("mode1P3PWithTruth", "( ({0}==1 && {1}==1) || ({0}==3 && {1}==3) )", invars = [taus.numTrack,taus.numProngTruth])
taus.add_expr("mode1P3PNoTruth",   "({0}==1 || {0}==3)", invars = [taus.numTrack])

# decay mode
taus.add_var('isPanTauCandidate', 'PanTau_isPanTauCandidate')
taus.add_expr("mode1P0N",      f"{{0}}=={enums.Mode_1p0n}", invars = [taus.decayMode])
taus.add_expr("mode1P1N",      f"{{0}}=={enums.Mode_1p1n}", invars = [taus.decayMode])
taus.add_expr("mode1PXN",      f"{{0}}=={enums.Mode_1pXn}", invars = [taus.decayMode])
taus.add_expr("mode3P0N",      f"{{0}}=={enums.Mode_3p0n}", invars = [taus.decayMode])
taus.add_expr("mode3PXN",      f"{{0}}=={enums.Mode_3pXn}", invars = [taus.decayMode])
taus.add_expr("mode1P0NTruth", f"{{0}}=={enums.Mode_1p0n}", invars = [taus.decayModeTruth])
taus.add_expr("mode1P1NTruth", f"{{0}}=={enums.Mode_1p1n}", invars = [taus.decayModeTruth])
taus.add_expr("mode1PXNTruth", f"{{0}}=={enums.Mode_1pXn}", invars = [taus.decayModeTruth])
taus.add_expr("mode3P0NTruth", f"{{0}}=={enums.Mode_3p0n}", invars = [taus.decayModeTruth])
taus.add_expr("mode3PXNTruth", f"{{0}}=={enums.Mode_3pXn}", invars = [taus.decayModeTruth])
taus.add_expr("isSubCand",     "{0}<5", invars = [taus.decayMode])
taus.add_expr("isSubCandTruth","{0}<5", invars = [taus.decayModeTruth])


# proto decay mode (ie from Cell-based alone without PanTau)
taus.add_expr("mode1P0NProto", f"{{0}}=={enums.Mode_1p0n}", invars = [taus.decayModeProto])
taus.add_expr("mode1P1NProto", f"{{0}}=={enums.Mode_1p1n}", invars = [taus.decayModeProto])
taus.add_expr("mode1PXNProto", f"{{0}}=={enums.Mode_1pXn}", invars = [taus.decayModeProto])
taus.add_expr("mode3P0NProto", f"{{0}}=={enums.Mode_3p0n}", invars = [taus.decayModeProto])
taus.add_expr("mode3PXNProto", f"{{0}}=={enums.Mode_3pXn}", invars = [taus.decayModeProto])

# id cuts RNN
taus.add_expr("veryloose", f"({{0}}&(1<<{enums.JetRNNSigVeryLoose}))!=0", invars = [taus.isTauFlags])
taus.add_expr("loose",     f"({{0}}&(1<<{enums.JetRNNSigLoose}))!=0",     invars = [taus.isTauFlags])
taus.add_expr("medium",    f"({{0}}&(1<<{enums.JetRNNSigMedium}))!=0",    invars = [taus.isTauFlags])
taus.add_expr("tight",     f"({{0}}&(1<<{enums.JetRNNSigTight}))!=0",     invars = [taus.isTauFlags])

# electron rejection cuts RNN
taus.add_expr("EleRNNLoose",  f"({{0}}&(1<<{enums.EleRNNLoose}))!=0",  invars = [taus.isTauFlags])
taus.add_expr("EleRNNMedium", f"({{0}}&(1<<{enums.EleRNNMedium}))!=0", invars = [taus.isTauFlags])
taus.add_expr("EleRNNTight",  f"({{0}}&(1<<{enums.EleRNNTight}))!=0",  invars = [taus.isTauFlags])


# True Tau Selection
#===================
truetaus.add_var("IsHadronicTau")
truetaus.add_expr("mode1P", "{0}==1", invars = [truetaus.numProng])
truetaus.add_expr("mode3P", "{0}==3", invars = [truetaus.numProng])
truetaus.add_expr("pt20", "{0}>20.0", invars = [truetaus.ptGeV])
truetaus.add_expr("eta25", "abs({0})<2.5", invars = [truetaus.eta])
truetaus.add_expr("vetoCrack", "( abs({0})<1.37 || abs({0}) > 1.52 )", invars = [truetaus.eta])

# cut to remove high-mass overlap with DYtautau (TODO: implement properly)
event.add_expr("Ztautau_lowmass", "{0}<120.", invars=[event.truth_resonance_massGeV])
#cZtautau_lowmass = Cut("({0}.pt_vis[0]<150.e3 && {0}.pt_vis[1]<150.e3)".format(vars.TrueTauContainerDyn))

# cut to remove boosted events from low-mass Ztautau
#cZtautau_dphi = Cut("abs(abs({0}.phi_vis[0] - {0}.phi_vis[1])-3.14)<0.5".format(vars.TrueTauContainerDyn))

# Reco Track Selection
#=====================
tautracks.add_expr('true_TT','{0} == 1', [tautracks.TruthType], 'taus')
tautracks.add_expr('true_CT','{0} == 2', [tautracks.TruthType], 'conversion')
tautracks.add_expr('true_IT','{0} == 3', [tautracks.TruthType], 'isolation')
tautracks.add_expr('true_FT','{0} == 0 || {0} >= 4', [tautracks.TruthType], 'fake')

tautracks.add_expr('reco_TT','{0} & (1<<5)', invars = [tautracks.flagSet])
tautracks.add_expr('reco_CT','{0} & (1<<7)', invars = [tautracks.flagSet])
tautracks.add_expr('reco_IT','{0} & (1<<6)', invars = [tautracks.flagSet])
tautracks.add_expr('reco_FT','{0} & (1<<8)', invars = [tautracks.flagSet])

tautracks.add_expr('mode1P','{0} == 1', invars = [tautracks.tauTruthProng])
tautracks.add_expr('mode3P','{0} == 3', invars = [tautracks.tauTruthProng])


# Bounds for ID variables 
#========================
taus.add_cuts("removeIDOutliers", cuts = [ \
    taus.add_expr("mEflowApprox_cutlow",        "{0} > -10000.", invars = [taus.mEflowApprox]),
    taus.add_expr("mEflowApprox_cuthigh",       "{0} < 40000.",  invars = [taus.mEflowApprox]),
    taus.add_expr("etOverPtLeadTrk_cuthigh",    "{0} < 30",      invars = [taus.etOverPtLeadTrk]),          
    taus.add_expr("ChPiEMEOverCaloEME_cutwin",  "abs({0})<5.",   invars = [taus.ChPiEMEOverCaloEME]),
    taus.add_expr("EMPOverTrkSysP_cuthigh",     "{0} < 30",      invars = [taus.EMPOverTrkSysP]),
    taus.add_expr("ptRatioEflowApprox_cuthigh", "{0} < 5",       invars = [taus.ptRatioEflowApprox]),           
    ])


# Combined selection criteria 
#===============================
# match criteria
taus.add_cuts("matchKin",            cuts = [taus.matched, taus.eta25Truth, taus.vetoCrackTruth, taus.pt20Truth])
taus.add_cuts("matchKinNoPt",        cuts = [taus.matched, taus.eta25Truth, taus.vetoCrackTruth])

# baseline selection
taus.add_cuts("baseline",            cuts = [taus.eta25, taus.vetoCrack, taus.pt20, taus.matchKin])
taus.add_cuts("baselineNoPt",        cuts = [taus.eta25, taus.vetoCrack, taus.matchKinNoPt])
taus.add_cuts("baseline1P",          cuts = [taus.baseline, taus.mode1P, taus.mode1PTruth])
taus.add_cuts("baseline3P",          cuts = [taus.baseline, taus.mode3P, taus.mode3PTruth])

# baseline selection for fakes
taus.add_cuts("baselineNoTruth",     cuts = [taus.eta25, taus.vetoCrack, taus.pt20])
taus.add_cuts("baseline1PNoTruth",   cuts = [taus.baselineNoTruth, taus.mode1P])
taus.add_cuts("baseline3PNoTruth",   cuts = [taus.baselineNoTruth, taus.mode3P])

# stream-specific selection
taus.add_cuts("tes1P",               cuts = [taus.baselineNoPt, taus.mode1P, taus.mode1PTruth, taus.medium])
taus.add_cuts("tes3P",               cuts = [taus.baselineNoPt, taus.mode3P, taus.mode3PTruth, taus.medium])
taus.add_cuts("tes1P3P",             cuts = [taus.baselineNoPt, taus.mode1P3PWithTruth, taus.medium])
taus.add_cuts("evetoTAU",            cuts = [taus.pt20, taus.matched, taus.eta25Truth, taus.pt20Truth, 
                                             taus.mode1P3PWithTruth, taus.medium])
taus.add_cuts("evetoELE",            cuts = [taus.pt20, taus.mode1P3PNoTruth, taus.medium])


# truth-tau selection
truetaus.add_cuts("baseline",        cuts = [truetaus.IsHadronicTau, truetaus.eta25, truetaus.vetoCrack, truetaus.pt20])
truetaus.add_cuts("baselineNoPt",    cuts = [truetaus.IsHadronicTau, truetaus.eta25])
truetaus.add_cuts("baseline1P",      cuts = [truetaus.baseline, truetaus.mode1P])
truetaus.add_cuts("baseline3P",      cuts = [truetaus.baseline, truetaus.mode3P])

# event level cuts
#========================
event.add_expr("mu40", "{0} <= 40", invars = [event.mu])

# EOF
