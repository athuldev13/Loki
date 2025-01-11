# encoding: utf-8
"""
loki.common.samples
~~~~~~~~~~~~~~~~~~~

Definition of samples (using :class:`loki.core.sample.Sample`).

Common weighting schemes are defined for main samples: 

* *wx1* - mc event weights and xsec scaling
* *wx2* - xsec scaling (no event weights)
* *ws* - stat-based scaling (scale to number of nominal mc events)
* *unw* - unweighted

"""
__author__    = "Will Davey"
__email__     = "will.davey@cern.ch"
__created__   = "2012-10-31"
__copyright__ = "Copyright 2016 Will Davey"
__license__   = "GPL http://www.gnu.org/licenses/gpl.html"

## modules

from loki.common import vars
from loki.common import cuts
from loki.common import styles
from loki.core.sample import Sample, HistScaler

# Common weights
#-----------------------------------------------------------------------------
scaler = HistScaler()
scaler_nevents = HistScaler(skim_hist_bin=1)
weight_mc = vars.event.get_var("weight_mc")

Dummy = Sample(name = 'Dummy', xsec = 1, regex="XXXDUMMYXXX", sty=styles.Ztautau)


# Weighting Schemes
#-----------------------------------------------------------------------------
def create_wx1_sample(s):
    """Retrun new version of sample with mc event weights and xsec scaling applied"""
    global scaler, weight_mc
    name = f"{s.name}_wx1"
    regex = s.regex or f"*{s.name}*"
    weight = weight_mc & s.weight 
    return Sample(name=name, regex=regex, sel=s.sel, weight=weight, xsec=s.xsec, scaler=scaler)

def create_wx2_sample(s):
    """Retrun new version of sample with xsec scaling applied (no event weights)"""
    global scaler_nevents
    name = f"{s.name}_wx2"
    regex = s.regex or f"*{s.name}*"
    return Sample(name=name, regex=regex, sel=s.sel, weight=s.weight, xsec=s.xsec, scaler=scaler_nevents)

def create_ws_sample(s):
    """Retrun new version of sample scaled to nominal number of mc events"""
    global scaler_nevents
    name = f"{s.name}_ws"
    regex = s.regex or f"*{s.name}*"
    xsec = float(s.mcevents)
    return Sample(name=name, regex=regex, sel=s.sel, weight=s.weight, xsec=xsec, scaler=scaler_nevents)

def remove_dytautau_mass_overlap(s):
    """Remove mass overlap in DYtautau from inclusive Ztautau sub-sample"""
    s.daughters[0].sel = vars.event.Ztautau_lowmass
    
    

#-----------------------------------------------------------------------------
# DYtautau / ee
# Cross section: 
#     * inclusive: https://twiki.cern.ch/twiki/bin/view/AtlasProtected/MC15ZjetsPowPy8InclSamplesPMG
#     * high-mass: https://twiki.cern.ch/twiki/bin/view/AtlasProtected/MC15ZjetsPowPy8SliceSamplesPMG
#-----------------------------------------------------------------------------
#: Inclusive Ztautau 
Ztautau = Sample(name = 'Ztautau', xsec = 1950.6, mcevents = 20000000, sty=styles.Ztautau)

#: Low-mass Ztautau
Ztautau_lowmass = Sample(name = 'Ztautau_lowmass',regex="*Ztautau*", sel=vars.event.Ztautau_lowmass,
                         xsec = 1950.6, mcevents = 20000000, sty=styles.Ztautau)

# high-mass DYtautau
DYtautau_120M180   = Sample(name = 'DYtautau_120M180',   xsec = 17.479,      mcevents = 150000)
DYtautau_180M250   = Sample(name = 'DYtautau_180M250',   xsec = 2.9213,      mcevents = 150000)
DYtautau_250M400   = Sample(name = 'DYtautau_250M400',   xsec = 1.082,       mcevents = 150000)
DYtautau_400M600   = Sample(name = 'DYtautau_400M600',   xsec = 0.1955,      mcevents = 150000)
DYtautau_600M800   = Sample(name = 'DYtautau_600M800',   xsec = 0.037401,    mcevents = 150000)
DYtautau_800M1000  = Sample(name = 'DYtautau_800M1000',  xsec = 0.010607,    mcevents = 150000)
DYtautau_1000M1250 = Sample(name = 'DYtautau_1000M1250', xsec = 0.0042585,   mcevents = 150000)
DYtautau_1250M1500 = Sample(name = 'DYtautau_1250M1500', xsec = 0.001422,    mcevents = 150000)
DYtautau_1500M1750 = Sample(name = 'DYtautau_1500M1750', xsec = 0.00054524,  mcevents =  50000)
DYtautau_1750M2000 = Sample(name = 'DYtautau_1750M2000', xsec = 0.00022992,  mcevents =  50000)
DYtautau_2000M2250 = Sample(name = 'DYtautau_2000M2250', xsec = 0.00010386,  mcevents =  50000)
DYtautau_2250M2500 = Sample(name = 'DYtautau_2250M2500', xsec = 0.000049403, mcevents =  50000)
DYtautau_2500M2750 = Sample(name = 'DYtautau_2500M2750', xsec = 0.000024454, mcevents =  50000)
DYtautau_2750M3000 = Sample(name = 'DYtautau_2750M3000', xsec = 0.00001249,  mcevents =  50000)
DYtautau_3000M3500 = Sample(name = 'DYtautau_3000M3500', xsec = 0.000010031, mcevents =  50000)
DYtautau_3500M4000 = Sample(name = 'DYtautau_3500M4000', xsec = 0.000002934, mcevents =  50000)
DYtautau_4000M4500 = Sample(name = 'DYtautau_4000M4500', xsec = 0.000000898, mcevents =  50000)
DYtautau_4500M5000 = Sample(name = 'DYtautau_4500M5000', xsec = 0.000000281, mcevents =  50000)
DYtautau_5000M     = Sample(name = 'DYtautau_5000M',     xsec = 0.000000126, mcevents =  50000)
DYtautau_highmass_samples = [
    DYtautau_120M180,
    DYtautau_180M250,DYtautau_250M400,DYtautau_400M600,
    DYtautau_600M800,DYtautau_800M1000,DYtautau_1000M1250,
    DYtautau_1250M1500,DYtautau_1500M1750,DYtautau_1750M2000,
    DYtautau_2000M2250,DYtautau_2250M2500,DYtautau_2500M2750,
    DYtautau_2750M3000,DYtautau_3000M3500,DYtautau_3500M4000,
    DYtautau_4000M4500,DYtautau_4500M5000,DYtautau_5000M,
    ]
DYtautau_samples = [Ztautau_lowmass] + DYtautau_highmass_samples
#DYtautau_samples = DYtautau_highmass_samples

#: DYtautau (high-mass only)
DYtautau_highmass = Sample(name='DYtautau_highmass', sty=styles.DYtautau,daughters=DYtautau_highmass_samples) 

#: DYtautau (full, no weights)
DYtautau_unw = Sample(name='DYtautau', sty=styles.DYtautau,
    daughters=DYtautau_samples) 

#: DYtautau (full, xsec weight scheme 1)
DYtautau_wx1 = Sample(name='DYtautau_wx1', sty=styles.DYtautau, 
    daughters=[create_wx1_sample(s) for s in DYtautau_samples])

#: DYtautau (full, xsec weight scheme 2)
DYtautau_wx2 = Sample(name='DYtautau_wx2', sty=styles.DYtautau, 
    daughters=[create_wx2_sample(s) for s in DYtautau_samples])

#: DYtautau (full, mcstat-based weight)
DYtautau_ws = Sample(name='DYtautau_ws', sty=styles.DYtautau, 
    daughters=[create_ws_sample(s) for s in DYtautau_samples])

#: DYtautau default sample
DYtautau = DYtautau_ws


#-----------------------------------------------------------------------------
# Gamma->tautau (our savior)
#-----------------------------------------------------------------------------
#: Gammatautau 
Gammatautau = Sample(name = 'Gammatautau', sty=styles.Ztautau)


# Electron background
#-----------------------------------------------------------------------------
#: Inclusive Zee 
Zee = Sample(name = 'Zee', xsec = 1950.6, sty=styles.Zee)


#: Inclusive Zee 
Zee = Sample(name = 'Zee', xsec = 1950.6, mcevents = 20000000, sty=styles.Zee)

#: Low-mass Zee
Zee_lowmass = Sample(name = 'Zee_lowmass',regex="*Zee*", 
                         xsec = 1950.6, mcevents = 20000000, sty=styles.Zee)

# high-mass DYee
DYee_120M180   = Sample(name = 'DYee_120M180',   xsec = 17.479,      mcevents = 150000)
DYee_180M250   = Sample(name = 'DYee_180M250',   xsec = 2.9213,      mcevents = 150000)
DYee_250M400   = Sample(name = 'DYee_250M400',   xsec = 1.082,       mcevents = 150000)
DYee_400M600   = Sample(name = 'DYee_400M600',   xsec = 0.1955,      mcevents = 150000)
DYee_600M800   = Sample(name = 'DYee_600M800',   xsec = 0.037401,    mcevents = 150000)
DYee_800M1000  = Sample(name = 'DYee_800M1000',  xsec = 0.010607,    mcevents = 150000)
DYee_1000M1250 = Sample(name = 'DYee_1000M1250', xsec = 0.0042585,   mcevents = 150000)
DYee_1250M1500 = Sample(name = 'DYee_1250M1500', xsec = 0.001422,    mcevents = 150000)
DYee_1500M1750 = Sample(name = 'DYee_1500M1750', xsec = 0.00054524,  mcevents =  50000)
DYee_1750M2000 = Sample(name = 'DYee_1750M2000', xsec = 0.00022992,  mcevents =  50000)
DYee_2000M2250 = Sample(name = 'DYee_2000M2250', xsec = 0.00010386,  mcevents =  50000)
DYee_2250M2500 = Sample(name = 'DYee_2250M2500', xsec = 0.000049403, mcevents =  50000)
DYee_2500M2750 = Sample(name = 'DYee_2500M2750', xsec = 0.000024454, mcevents =  50000)
DYee_2750M3000 = Sample(name = 'DYee_2750M3000', xsec = 0.00001249,  mcevents =  50000)
DYee_3000M3500 = Sample(name = 'DYee_3000M3500', xsec = 0.000010031, mcevents =  50000)
DYee_3500M4000 = Sample(name = 'DYee_3500M4000', xsec = 0.000002934, mcevents =  50000)
DYee_4000M4500 = Sample(name = 'DYee_4000M4500', xsec = 0.000000898, mcevents =  50000)
DYee_4500M5000 = Sample(name = 'DYee_4500M5000', xsec = 0.000000281, mcevents =  50000)
DYee_5000M     = Sample(name = 'DYee_5000M',     xsec = 0.000000126, mcevents =  50000)
DYee_highmass_samples = [
    DYee_120M180,
    DYee_180M250,DYee_250M400,DYee_400M600,
    DYee_600M800,DYee_800M1000,DYee_1000M1250,
    DYee_1250M1500,DYee_1500M1750,DYee_1750M2000,
    DYee_2000M2250,DYee_2250M2500,DYee_2500M2750,
    DYee_2750M3000,DYee_3000M3500,DYee_3500M4000,
    DYee_4000M4500,DYee_4500M5000,DYee_5000M,
    ]
DYee_samples = [Zee_lowmass] + DYee_highmass_samples
#DYee_samples = DYee_highmass_samples

#: DYee (high-mass only)
DYee_highmass = Sample(name='DYee_highmass', sty=styles.DYee,daughters=DYee_highmass_samples) 

#: DYee (full, no weights)
DYee_unw = Sample(name='DYee', sty=styles.DYee,
    daughters=DYee_samples) 

#: DYee (full, xsec weight scheme 1)
DYee_wx1 = Sample(name='DYee_wx1', sty=styles.DYee, 
    daughters=[create_wx1_sample(s) for s in DYee_samples])

#: DYee (full, xsec weight scheme 2)
DYee_wx2 = Sample(name='DYee_wx2', sty=styles.DYee, 
    daughters=[create_wx2_sample(s) for s in DYee_samples])

#: DYee (full, mcstat-based weight)
DYee_ws = Sample(name='DYee_ws', sty=styles.DYee, 
    daughters=[create_ws_sample(s) for s in DYee_samples])

#: DYee default sample
DYee = DYee_ws


# Muon background
#-----------------------------------------------------------------------------
#: Inclusive Zee
Zmumu = Sample(name = 'Zmumu', xsec = 1950.6, sty=styles.Zmumu)


#: Inclusive Zee
Zmumu = Sample(name = 'Zmumu', xsec = 1950.6, mcevents = 20000000, sty=styles.Zmumu)

#: Low-mass Zee
Zmumu_lowmass = Sample(name = 'Zmumu_lowmass',regex="*Zmumu*",
                         xsec = 1950.6, mcevents = 20000000, sty=styles.Zmumu)

# high-mass DYmumu
DYmumu_120M180   = Sample(name = 'DYmumu_120M180',   xsec = 17.479,      mcevents = 150000)
DYmumu_180M250   = Sample(name = 'DYmumu_180M250',   xsec = 2.9213,      mcevents = 150000)
DYmumu_250M400   = Sample(name = 'DYmumu_250M400',   xsec = 1.082,       mcevents = 150000)
DYmumu_400M600   = Sample(name = 'DYmumu_400M600',   xsec = 0.1955,      mcevents = 150000)
DYmumu_600M800   = Sample(name = 'DYmumu_600M800',   xsec = 0.037401,    mcevents = 150000)
DYmumu_800M1000  = Sample(name = 'DYmumu_800M1000',  xsec = 0.010607,    mcevents = 150000)
DYmumu_1000M1250 = Sample(name = 'DYmumu_1000M1250', xsec = 0.0042585,   mcevents = 150000)
DYmumu_1250M1500 = Sample(name = 'DYmumu_1250M1500', xsec = 0.001422,    mcevents = 150000)
DYmumu_1500M1750 = Sample(name = 'DYmumu_1500M1750', xsec = 0.00054524,  mcevents =  50000)
DYmumu_1750M2000 = Sample(name = 'DYmumu_1750M2000', xsec = 0.00022992,  mcevents =  50000)
DYmumu_2000M2250 = Sample(name = 'DYmumu_2000M2250', xsec = 0.00010386,  mcevents =  50000)
DYmumu_2250M2500 = Sample(name = 'DYmumu_2250M2500', xsec = 0.000049403, mcevents =  50000)
DYmumu_2500M2750 = Sample(name = 'DYmumu_2500M2750', xsec = 0.000024454, mcevents =  50000)
DYmumu_2750M3000 = Sample(name = 'DYmumu_2750M3000', xsec = 0.00001249,  mcevents =  50000)
DYmumu_3000M3500 = Sample(name = 'DYmumu_3000M3500', xsec = 0.000010031, mcevents =  50000)
DYmumu_3500M4000 = Sample(name = 'DYmumu_3500M4000', xsec = 0.000002934, mcevents =  50000)
DYmumu_4000M4500 = Sample(name = 'DYmumu_4000M4500', xsec = 0.000000898, mcevents =  50000)
DYmumu_4500M5000 = Sample(name = 'DYmumu_4500M5000', xsec = 0.000000281, mcevents =  50000)
DYmumu_5000M     = Sample(name = 'DYmumu_5000M',     xsec = 0.000000126, mcevents =  50000)
DYmumu_highmass_samples = [
    DYmumu_120M180,
    DYmumu_180M250,DYmumu_250M400,DYmumu_400M600,
    DYmumu_600M800,DYmumu_800M1000,DYmumu_1000M1250,
    DYmumu_1250M1500,DYmumu_1500M1750,DYmumu_1750M2000,
    DYmumu_2000M2250,DYmumu_2250M2500,DYmumu_2500M2750,
    DYmumu_2750M3000,DYmumu_3000M3500,DYmumu_3500M4000,
    DYmumu_4000M4500,DYmumu_4500M5000,DYmumu_5000M,
    ]
DYmumu_samples = [Zee_lowmass] + DYmumu_highmass_samples
#DYmumu_samples = DYmumu_highmass_samples

#: DYmumu (high-mass only)
DYmumu_highmass = Sample(name='DYmumu_highmass', sty=styles.DYmumu,daughters=DYmumu_highmass_samples)

#: DYmumu (full, no weights)
DYmumu_unw = Sample(name='DYmumu', sty=styles.DYmumu,
    daughters=DYmumu_samples)

#: DYmumu (full, xsec weight scheme 1)
DYmumu_wx1 = Sample(name='DYmumu_wx1', sty=styles.DYmumu,
    daughters=[create_wx1_sample(s) for s in DYmumu_samples])

#: DYmumu (full, xsec weight scheme 2)
DYmumu_wx2 = Sample(name='DYmumu_wx2', sty=styles.DYmumu,
    daughters=[create_wx2_sample(s) for s in DYmumu_samples])

#: DYmumu (full, mcstat-based weight)
DYmumu_ws = Sample(name='DYmumu_ws', sty=styles.DYmumu,
    daughters=[create_ws_sample(s) for s in DYmumu_samples])

#: DYmumu default sample
DYmumu = DYmumu_ws




#-----------------------------------------------------------------------------
# Higgs samples 
#-----------------------------------------------------------------------------
ggH125 = Sample(name = 'ggH125', xsec = 1.0, sty=styles.ggH125)
VBFH125 = Sample(name = 'VBFH125', xsec = 1.0, sty=styles.VBFH125)

#-----------------------------------------------------------------------------
# MC dijets
# Cross section: 
#     * https://twiki.cern.ch/twiki/bin/view/AtlasProtected/XsecSummaryMultijet
#-----------------------------------------------------------------------------
#jetjet_JZ0W = Sample(name = 'jetjet_JZ0W', xsec = 80302080000.0)
jetjet_JZ1W = Sample(name = 'jetjet_JZ1W', xsec = 52696671.6,  mcevents = 2000000)
jetjet_JZ2W = Sample(name = 'jetjet_JZ2W', xsec = 809379.648,  mcevents = 2000000)
jetjet_JZ3W = Sample(name = 'jetjet_JZ3W', xsec = 8455.49202,  mcevents = 8000000)
jetjet_JZ4W = Sample(name = 'jetjet_JZ4W', xsec = 134.9080666, mcevents = 8000000)
jetjet_JZ5W = Sample(name = 'jetjet_JZ5W', xsec = 4.200831425, mcevents = 8000000)
jetjet_JZ6W = Sample(name = 'jetjet_JZ6W', xsec = 0.242119405, mcevents = 2000000)
jetjet_JZ7W = Sample(name = 'jetjet_JZ7W', xsec = 0.006369576, mcevents = 2000000)
jetjet_JZ8W = Sample(name = 'jetjet_JZ8W', xsec = 0.006351453, mcevents = 1000000)
jetjet_JZ9W = Sample(name = 'jetjet_JZ9W', xsec = 0.000236729, mcevents = 1000000)
#jetjet_JZ10W = Sample(name = 'jetjet_JZ10W', xsec = 0.00000705)
#jetjet_JZ11W = Sample(name = 'jetjet_JZ11W', xsec = 0.000000114)
#jetjet_JZ12W = Sample(name = 'jetjet_JZ12W', xsec = 0.00000000041468)
jetjet_samples = [
    jetjet_JZ1W, jetjet_JZ2W, jetjet_JZ3W, jetjet_JZ4W, 
    jetjet_JZ5W, jetjet_JZ6W, jetjet_JZ7W, jetjet_JZ8W, 
    jetjet_JZ9W, 
    ]

#: Multijet (full, MC, no weights)
Multijet_unw = Sample("Multijet",sty=styles.Multijet, daughters=jetjet_samples)

#: Multijet (full, xsec weight scheme 1)
Multijet_wx1 = Sample(name='Multijet_wx1', sty=styles.Multijet, 
    daughters=[create_wx1_sample(s) for s in jetjet_samples])

#: Multijet (full, xsec weight scheme 2)
Multijet_wx2 = Sample(name='Multijet_wx2', sty=styles.Multijet, 
    daughters=[create_wx2_sample(s) for s in jetjet_samples])

#: Multijet (full, mcstat-based weight)
Multijet_ws = Sample(name='Multijet_ws', sty=styles.Multijet, 
    daughters=[create_ws_sample(s) for s in jetjet_samples])

#: Multijet default sample
Multijet = Multijet_wx1



#-----------------------------------------------------------------------------
# Flat ntuple samples 
Signal     = Sample(name="Signal",     sty=styles.Signal,     weight=vars.weight)
Background = Sample(name="Background", sty=styles.Background, weight=vars.weight)



#-----------------------------------------------------------------------------
#: default signal sample
sample = DYtautau
#: default background sample
bkg = Multijet
#: default electron background sample
bkg_ele = DYee
#: default muon background sample
bkg_muon = DYmumu


## EOF
