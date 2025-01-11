LOKI = loki
FDISC = "--disc TauJets.GNNScore:fine"
FXVAR = "--xvar TauJets.pt"
FYVAR = "--yvar TauJets.mu"
PRONG = 1p
EFF = 90
FNAME = /afs/cern.ch/user/a/asudhaka/eos_space/flattening_folder/root_files/${PRONG}_gtt_mod.root
${LOKI} tune ${FDISC} ${FXVAR} ${FYVAR} --fname ${FNAME} ${FSELFLAT} -o tune_${PRONG}_2D.root -t 0.${EFF}

