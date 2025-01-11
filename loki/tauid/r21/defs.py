from loki.common import vars
taus = vars.taus

# Definition of ptIntermediateAxis for use in MxAOD flattening
taus.add_var('ptIntermediateAxis').add_view(40, 20000., 2000000.)
vars.tidvars.append(taus.ptIntermediateAxis.get_view())

# Clamping max(pt, 100 Gev) of ptIntermediateAxis for Tau-ID
taus.add_expr("ptIntermediateAxis_clamped", "{0} > 100000.0 ? 100000.0 : {0}",
              invars=[taus.ptIntermediateAxis])

# Fine pt-binning for reweighting: 2.5% quantiles of the background until
# 500 GeV then bins of size ~65 Gev
pt_weight = [   20.        ,    20.81787934,    21.43923791,    21.8488418 ,
                22.21203331,    22.56221449,    22.90823828,    23.26616406,
                23.64695898,    24.05345703,    24.49377344,    25.01292461,
                25.5943632 ,    26.23693477,    26.95318938,    27.76035734,
                28.66922002,    29.70454438,    30.88700078,    32.25026742,
                33.82225339,    35.34307214,    37.09111484,    39.1364375 ,
                41.52632188,    44.34846693,    47.71140651,    51.78157891,
                56.88002083,    63.47290911,    72.2960125 ,    84.897675  ,
               103.78328698,   135.21293229,   189.1708375 ,   256.75729479,
               358.54439167,   483.9738125 ,   549.77512188,   615.57643125,
               681.37774063,   747.17905   ,   812.98035938,   878.78166875,
               944.58297813,  1010.3842875 ,  1076.18559688,  1141.98690625,
              1207.78821563,  1273.589525  ,  1339.39083437,  1405.19214375,
              1470.99345313,  1536.7947625 ,  1602.59607188,  1668.39738125,
              1734.19869062,  1800.        ]

# Convert GeV to MeV
pt_weight = [1000. * pt for pt in pt_weight]
taus.get_var("ptIntermediateAxis").add_view(xbins=pt_weight,
                                            name="reweight_r21")

# pt-binning for efficiency flattening
xbins_pt_tid = [20000., 25178., 31697., 39905., 50237., 63245., 79621., 100000.,
                130000., 200000., 316978., 502377., 796214., 1261914., 2000000.]
taus.get_var("pt").add_view(xbins=xbins_pt_tid, name="flat_r21")

# mu-binning for efficiency flattening
xbins_mu_tid = [-0.5, 10.5, 19.5, 23.5, 27.5, 31.5, 35.5, 39.5, 49.5, 61.5]
taus.get_var("mu").add_view(xbins=xbins_mu_tid, name="flat_r21")

# Cuts for outlier removal (both 1P and 3P)
taus.add_cuts("IDOutliers_common", cuts=[
    taus.add_expr("centFrac_cut", "0.0 <= {0} && {0} < 1.1",
                  invars=[taus.centFrac]),
    taus.add_expr("innerTrkAvgDist_cut", "0.0 <= {0} && {0} <= 0.4",
                  invars=[taus.innerTrkAvgDist]),
    taus.add_expr("EMPOverTrkSysP_cut", "0.0 <= {0} && {0} < 50.0",
                  invars=[taus.EMPOverTrkSysP]),
    taus.add_expr("ptRatioEflowApprox_cut", "0.0 <= {0} && {0} < 7.0",
                  invars=[taus.ptRatioEflowApprox]),
    taus.add_expr("mEflowApprox_cut", "0.0 <= {0} && {0} < 30000.0",
                  invars=[taus.mEflowApprox]),
    taus.add_expr("SumPtTrkFrac_cut", "0.0 <= {0} && {0} <= 1.0",
                  invars=[taus.SumPtTrkFrac])
])

# Cuts for outlier removal (only 1P)
taus.add_cuts("IDOutliers_1P", cuts=[
    taus.add_expr("absipSigLeadTrk_cut", "0.0 <= {0} && {0} < 35.0",
                  invars=[taus.absipSigLeadTrk]),
    taus.add_expr("etOverPtLeadTrk_cut", "0.0 <= {0} && {0} < 40.0",
                  invars=[taus.etOverPtLeadTrk])
])

# Cuts for outlier removal (only 3P)
taus.add_cuts("IDOutliers_3P", cuts=[
    taus.add_expr("dRmax_cut", "0.0 <= {0} && {0} <= 0.4",
                  invars=[taus.dRmax]),
    taus.add_expr("trFlightPathSig_cut", "-10.0 < {0} && {0} < 60.0",
                  invars=[taus.trFlightPathSig]),
    taus.add_expr("massTrkSys_cut", "0.0 <= {0} && {0} < 30000.0",
                  invars=[taus.massTrkSys])
])
