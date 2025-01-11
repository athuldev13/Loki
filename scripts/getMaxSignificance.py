#!/usr/bin/env python

import math
import sys
import ROOT

fname = sys.argv[1]
f = ROOT.TFile.Open(fname)

hSig = f.Get("Method_BDT/classifier/MVA_classifier_effS") 
hBkg = f.Get("Method_BDT/classifier/MVA_classifier_effB")
if not hSig:
    hSig = f.Get("Method_BDT/BDT/MVA_BDT_effS") 
    hBkg = f.Get("Method_BDT/BDT/MVA_BDT_effB")
    
sigmax = 0
cutmax = None
for iBin in range(hSig.GetNbinsX()):
    S = hSig.GetBinContent( iBin )
    B = hBkg.GetBinContent( iBin )
    sig = S / math.sqrt(S+B) if S+B > 0 else 0
    if sig > sigmax:
        sigmax = sig
        cutmax = hSig.GetBinCenter(iBin)

print(" %.4f"%cutmax)
