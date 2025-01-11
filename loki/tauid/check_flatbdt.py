# encoding: utf-8
"""
loki.tes.check_flatbdt.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Checks of the new flattend tau ID RNN score

"""
__author__    = "Will Davey"
__email__     = "will.davey@cern.ch"
__created__   = "2016-04-14"
__copyright__ = "Copyright 2016 Will Davey"
__license__   = "GPL http://www.gnu.org/licenses/gpl.html"


## modules
from loki.core.cut import Cut
from loki.core.file import OutputFileStream, FileHandler
from loki.core.hist import Processor, HistScaler
from loki.core.setup import setup
from loki.common import vars, samples, cuts, styles
from loki.tauid.plots import create_tid_variable_dists, create_tid_profiles, create_eff_profiles, create_roc, IDWP1P_for_fakes, IDWP3P_for_fakes

# basic setup
#setup(suppress_root_msgs=False,suppress_root_errors=False)
setup()

# sample 
#sample = samples.DYtautau
#sample = samples.DYtautau_highmass
sample = samples.sig
#sample = samples.Ztautau
#bkg = samples.Multijet
bkg = samples.bkg
data_path = "/Users/wedavey/Data/MxAOD/viveiros_v31"
FileHandler(data_path,[sample,bkg])


# dep vars
RecoTauPtMVA = vars.RecoTauPt.clone(name="RecoTauPtMVA", var="ptMvaTES/1000.")
RecoTauPtMVALow = vars.RecoTauPtLow.clone(name="RecoTauPtMVALow", var="ptMvaTES/1000.")
depvars = []
#depvars += vars.depvars_reco
depvars += [vars.nVtx,vars.mu]
depvars += [RecoTauPtMVA,RecoTauPtMVALow] 


# selection
lowpt = cuts.cRecoTauPtLt30
pt2050 = cuts.cRecoTauPt20&cuts.cRecoTauPtLt50
midpt = cuts.cRecoTauPt30
highpt = cuts.cRecoTauPt500
s1p = cuts.sReco1P
s3p = cuts.sReco3P

#sel_1p = s1p&pt2050
#sel_3p = s3p&pt2050
#sel_1p = s1p&highpt
#sel_3p = s3p&highpt
sel_1p = s1p
sel_3p = s3p


## working points with flattened bdt
target_effs_1P = [0.85,0.75,0.60]
target_effs_3P = [0.75,0.60,0.45]
bdttrans = vars.RNNJetScoreSigTrans
sFlat1PLoose  = Cut(f"{bdttrans.get_var()} > {1.0-target_effs_1P[0]:.2f}")
sFlat1PMedium = Cut(f"{bdttrans.get_var()} > {1.0-target_effs_1P[1]:.2f}")
sFlat1PTight  = Cut(f"{bdttrans.get_var()} > {1.0-target_effs_1P[2]:.2f}")
sFlat3PLoose  = Cut(f"{bdttrans.get_var()} > {1.0-target_effs_3P[0]:.2f}")
sFlat3PMedium = Cut(f"{bdttrans.get_var()} > {1.0-target_effs_3P[1]:.2f}")
sFlat3PTight  = Cut(f"{bdttrans.get_var()} > {1.0-target_effs_3P[2]:.2f}")

cRecoTauPtMVA20 = Cut(f"{RecoTauPtMVA.get_var()}>20.0")

sel_1p = sel_1p&cRecoTauPtMVA20
sel_3p = sel_3p&cRecoTauPtMVA20

IDWP1P_flat = [ 
    ("Loose" , {"sel_total":cuts.sRecoAndMatch1P, 
                "sel_pass" :cuts.sRecoAndMatch1P&sFlat1PLoose,
                "sty"      :styles.Loose}),
    ("Medium", {"sel_total":cuts.sRecoAndMatch1P, 
                "sel_pass" :cuts.sRecoAndMatch1P&sFlat1PMedium,
                "sty"      :styles.Medium}),
    ("Tight" , {"sel_total":cuts.sRecoAndMatch1P, 
                "sel_pass" :cuts.sRecoAndMatch1P&sFlat1PTight,
                "sty"      :styles.Tight}),
    ]





plots = []
plots += create_tid_variable_dists([sample,bkg], tidvars=[vars.RNNJetScoreSigTrans], prongs=1, normalize=True, sel=sel_1p)
plots += create_tid_variable_dists([sample,bkg], tidvars=[vars.RNNJetScoreSigTrans], prongs=3, normalize=True, sel=sel_3p)
#plots += create_tid_profiles(sample,prongs=1,tidvars=vars.tidvars_1p,dir="profiles_uncorr",depvars=depvars,sel=sel_1p)
#plots += create_tid_profiles(sample,prongs=3,tidvars=vars.tidvars_3p,dir="profiles_uncorr",depvars=depvars,sel=sel_3p)
#plots += create_roc(sample,bkg,sel_sig_1p=sel_1p,sel_bkg_1p=sel_1p,sel_sig_3p=sel_3p,sel_bkg_3p=sel_3p)
#plots += create_eff_profiles(bkg,wpdefs=IDWP1P_for_fakes,depvars=vars.depvars_reco,prongs=1,wrt=False,tag="FakeRate",fakes=True)
#plots += create_eff_profiles(bkg,wpdefs=IDWP3P_for_fakes,depvars=vars.depvars_reco,prongs=3,wrt=False,tag="FakeRate",fakes=True)
#plots += create_eff_profiles(sample,wpdefs=IDWP1P_flat,depvars=depvars,prongs=1,wrt=False,tag="FlatBDTWPs")


scaler = None
#scaler = HistScaler()
#plots += create_tid_variable_dists([sample,bkg],prongs=1)
# process hists
ef = 1.0
#ef = 0.25
processor = Processor(event_frac=ef,scaler=scaler)
processor.draw_plots(plots)

# write out
ofstream = OutputFileStream("hists.root")
ofstream.write(plots)

## EOF
