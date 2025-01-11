# encoding: utf-8
"""
run.py
~~~~~~

<Description of module goes here...>

"""
__author__    = "Will Davey"
__email__     = "will.davey@cern.ch"
__created__   = "2017-02-07"
__copyright__ = "Copyright 2017 Will Davey"
__license__   = "GPL http://www.gnu.org/licenses/gpl.html"



## modules
import os
from loki.core.logger import log
from loki.common import vars
taus = vars.taus
from loki.utils.helpers import import_module
import_module(os.path.join(os.path.dirname(__file__), "defs.py"))

# - - - - - - - - - - - - - - - global defs - - - - - - - - - - - - - - - - #
etaregs = ["Bar", "End1", "End23"]
samps = ["sig_train", "sig_test", "bkg_train", "bkg_test"]


# bdt options
bdtopts = {
    "NTrees": 400,
    "nCuts": 200,
    "Shrinkage": 0.1,
    "UseYesNoLeaf": False,
    "DoBoostMonitor": True,
    "UseBaggedBoost": True,
    "PruneMethod": "NoPruning",
    "MinNodeSize": 0.1,
    "BaggedSampleFraction": 0.6,
    "MaxDepth": 6,
    "BoostType": "Grad",
    "SeparationType": "GiniIndex"
    }


# input variables
bdtvars = dict()
bdtvars["Bar"] = [
    taus.absleadTrackEta,
    taus.leadTrackDeltaEta,
    taus.leadTrackDeltaPhi,
    taus.EMFracFixed,
    taus.etHotShotWinOverPtLeadTrk,
    taus.centFrac,
    taus.etOverPtLeadTrk,
    taus.hadLeakFracFixed,
    taus.PSFrac,
    taus.leadTrackProbHT,
    ]
bdtvars["End1"] = list(bdtvars["Bar"])
bdtvars["End23"] = [v for v in bdtvars["Bar"] if v is not taus.leadTrackProbHT]


# flattening options
workingpoints = {
    "Loose": 95,
    "Medium": 85,
    "Tight": 75
    }
depvarx = taus.pt.get_view("flat_r21")
depvary = taus.absleadTrackEta.get_view("flat_r21")


# dependent variables (for efficiency profiles)
depvars = [
    taus.ptGeV.get_view("weight"),
    taus.eta.get_view(),
    taus.absleadTrackEta.get_view("fine"),
    taus.mu.get_view(),
    taus.nVtx.get_view(),
    ]


# styles
from loki.common.styles import red, black, fullcircle, fullsquare
from loki.core.style import Style
sty_hist_sig_train = Style("SigTrain", tlatex="Sig (train)", LineColor=red,
                           LineStyle=2, FillStyle=3004, FillColor=red, drawopt="HIST")
sty_hist_bkg_train = Style("BkgTrain", tlatex="Bkg (train)", LineColor=black,
                           LineStyle=2, FillStyle=3005, FillColor=black, drawopt="HIST")
sty_hist_sig_test = Style("SigTest", tlatex="Sig (test)", LineColor=red,
                          MarkerColor=red, MarkerStyle=fullcircle)
sty_hist_bkg_test = Style("BkgTest", tlatex="Bkg (test)", LineColor=black,
                          MarkerColor=black, MarkerStyle=fullsquare)


# - - - - - - - - - - - - - - - function defs - - - - - - - - - - - - - - - - #
def main():
    """Main function - parses command line arguments and executes requested function"""
    # define arg parser
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--indir",  default="",
        help="Directory containing the input sample ntuples")
    parser.add_argument("--outdir", default="",
        help="Directory containing the decorated sample ntuples")
    parser.add_argument("--algdir", default="",
        help="Directory containing algorithms")
    parser.add_argument("-m", "--mode", default="all",
        choices = ["all", "spawn-bdt", "train-bdt", "deco-bdt", "plot-bdt",
                   "merge", "tune-wp", "deco-wp", "plot-wp"],
        help="Running mode (default: all)")
    parser.add_argument("-p", "--prefix", default="NewEle",
        help="Prefix for algorithm names")
    parser.add_argument("-f", "--force", action="store_true",
        help="Force retrain/redecorate")
    funcs = {"all": run_all, "spawn-bdt": spawn_bdt,
             "train-bdt": train_bdt, "deco-bdt": deco_bdt, "plot-bdt": make_bdt_plots,
             "merge": merge_regs,
             "tune-wp": tune_wp, "deco-wp": deco_wp, "plot-wp": make_wp_plots}

    # parse and exec
    args = parser.parse_args()
    from loki.core.setup import setup
    setup()
    if not funcs[args.mode](args):
        log().error("Failed")
    else:
        log().info("Finished successfully")


## helper functions
def get_fname_in(dir=None, reg=None, samp=None):
    """Return input filename

    :param dir: input file directory
    :param reg: eta region name
    :param samp: sample name (eg. "sig_train")
    """
    fin_fmt = "{dir}/Eta{reg}/{samp}.root"
    return os.path.abspath(fin_fmt.format(dir=dir or ".", reg=reg, samp=samp))

def get_fname_out(dir=None, reg=None, samp=None):
    """Return output filename

    :param dir: output file directory
    :param reg: eta region name
    :param samp: sample name (eg. "sig_train")
    """
    fout_fmt = "{dir}/Eta{reg}/{samp}_deco.root"
    return os.path.abspath(fout_fmt.format(dir=dir or ".", reg=reg, samp=samp))

def get_fname_merge(dir=None, samp=None):
    """Return eta-merged filename

    :param dir: merged file directory
    :param samp: sample name (eg. "sig_train")
    """
    fout_fmt = "{dir}/{samp}_deco.root"
    return os.path.abspath(fout_fmt.format(dir=dir or ".", samp=samp))

def get_algname_bdt(dir=None, reg=None, prefix=None):
    """Return BDT algorithm workspace name

    :param dir: algorithm directory
    :param reg: eta region name
    :param prefix: algorithm prefix
    """
    bdtalg_fmt = "{dir}/{prefix}BDTScore{reg}.alg"
    return os.path.abspath(bdtalg_fmt.format(dir=dir or ".", reg=reg, prefix=prefix))

def get_algname_flat(dir=None, prefix=None):
    """Return score flattening algorithm workspace name

    :param dir: algorithm directory
    :param prefix: algorithm prefix
    """
    flatalg_fmt = "{dir}/{prefix}Flat.alg"
    return os.path.abspath(flatalg_fmt.format(dir=dir or ".", prefix=prefix))

def get_varname_bdt(prefix=None):
    """Return name of new BDT variable

    :param prefix: algorithm prefix
    """
    bdtvar_fmt = "{prefix}BDTScore"
    return bdtvar_fmt.format(prefix=prefix)

def get_varname_flat(prefix=None):
    """Return name of new flattend BDT score variable

    :param prefix: algorithm prefix
    """
    flatvar_fmt = "{prefix}Flat"
    return flatvar_fmt.format(prefix=prefix)

def get_var_bdt(prefix=None):
    """Return view of new BDT variable used for flattening

    :param prefix: algorithm prefix
    """
    name = get_varname_bdt(prefix)
    if not hasattr(vars, name):
        from loki.core.var import Var
        from loki.core.histutils import log_bins
        # define reverse-log binning needed to flatten sharply peaked grad-boost bdt score
        xmin = -1.01
        xmax = 1.01
        start = 0.01
        w = xmax - xmin
        bins_grad_bdt = list(reversed([xmax - (v - start) for v in log_bins(1000, start, start + w)]))
        v = Var(name)
        v.add_view(xbins=bins_grad_bdt, name="flat_r21")
        v.add_view(xbins=bins_grad_bdt, name="roc")
        setattr(vars, name, v)
    return getattr(vars, name).get_view("flat_r21")


## exec functions
def spawn_bdt(args):
    """Spawns EleBDT configurations for eta-regions"""
    from loki.core.sample import Sample
    from loki.train import algs
    import shutil
    for reg in etaregs:
        bdtname = get_varname_bdt(prefix=args.prefix)
        wspath = get_algname_bdt(dir=args.algdir, reg=reg, prefix=args.prefix)

        # check if exists
        if os.path.exists(wspath):
            if args.force:
                log().info("Removing existing {}".format(os.path.relpath(wspath)))
                shutil.rmtree(wspath, ignore_errors=True)
            else:
                log().info("Skipping {}, already exists. Use --force to overwrite.".format(os.path.relpath(wspath)))
                continue

        # create samples
        sample_dict = dict()
        for samp in samps:
            path = get_fname_in(dir=args.indir, reg=reg, samp=samp)
            if not os.path.exists(path):
                log().warning("Ntuple {} does not exist.".format(path))
            sample_dict[samp] = Sample(name=samp, files=[path], weight=vars.weight)

        # Build & spawn BDTs
        alg = algs.TMVAClassifier(name=bdtname, tmvatype="BDT", invars=bdtvars[reg],
                                  algopts=bdtopts, **sample_dict)
        if not alg.saveas(wspath):
            return False

    return True


def train_bdt(args):
    """Trains all untrained BDTS"""
    from loki.train import algs
    from loki.train.alg import load
    for reg in etaregs:
        ws = get_algname_bdt(dir=args.algdir, reg=reg, prefix=args.prefix)
        alg = load(ws)
        if not alg:
            log().warn("Failure loading workspace: {}, skipping train".format(os.path.relpath(ws)))
            continue
        if not args.force and alg.info.get("trained", False):
            log().info("{} already trained, skipping...".format(os.path.relpath(ws)))
        elif not alg.train():
            log().error("Failure training {}".format(os.path.relpath(ws)))
            return False
        elif not alg.save():
            log().error("Failure saving {}".format(os.path.relpath(ws)))
            return False

    return True


def deco_bdt(args):
    """Decorates the BDT scores onto the testing samples"""
    from loki.train import algs
    from loki.train.alg import load
    from loki.train.ntup import decorate_ntup
    from loki.core.helpers import mkdir_p
    from loki.core.sample import Sample
    import shutil
    for reg in etaregs:
        # load and check alg
        ws = get_algname_bdt(dir=args.algdir, reg=reg, prefix=args.prefix)
        alg = load(ws)
        if not alg:
            log().warn("Failure loading workspace: {}, skipping deco".format(ws))
            continue
        if not alg.info.get("trained", False):
            log().warning("{} not trained, skipping...".format(ws))
            continue

        for samp in samps:
            src = get_fname_in(dir=args.indir, reg=reg, samp=samp)
            dest = get_fname_out(dir=args.outdir, reg=reg, samp=samp)

            # copy in to out files
            if not os.path.exists(dest):
                # Copy testing sample for decoration
                mkdir_p(os.path.dirname(dest))
                log().info("Copying {src} to {dest}".format(src=src, dest=dest))
                shutil.copyfile(src, dest)

            # check for existing deco
            s = Sample(files=[dest])
            if s.has_varname(alg.get_var_name()) and not args.force:
                log().info("Will not overwrite existing var {} in {} (use --force)" \
                           .format(alg.get_var_name(), os.path.relpath(dest)))
                continue

            # decorate
            if not decorate_ntup(dest, alg, overwrite=True):
                log().error("Failed to decorate BDT score")
                return False

    return True


def merge_regs(args):
    """Merge eta regions"""
    import subprocess
    for samp in samps:
        infiles = [get_fname_out(dir=args.outdir, reg=reg, samp=samp) for reg in etaregs]
        merge = get_fname_merge(dir=args.outdir, samp=samp)

        if not args.force and os.path.exists(merge):
            log().info("Merge {} already exists, skipping".format(os.path.relpath(merge)))
            continue
        else:
            try:
                subprocess.call("hadd -f {} {}".format(merge, " ".join(infiles)), shell=True)
            except:
                log().error("Failed to create merge: {}".format(os.path.relpath(merge)))
                return False

    return True


def tune_wp(args):
    """Tunes the working points"""
    from loki.train import algs
    from loki.train.alg import load
    from loki.core.sample import Sample
    disc = get_var_bdt(args.prefix)
    flatname = get_varname_flat(prefix=args.prefix)
    ws = get_algname_flat(dir=args.algdir, prefix=args.prefix)

    # spawn alg
    if not os.path.exists(ws):
        fname = get_fname_merge(dir=args.outdir, samp="sig_test")
        sig_test = Sample(name="sig_train", files=[fname], weight=vars.weight)

        alg = algs.MVScoreTuner(name=flatname, sig_train=sig_test, disc=disc,
            xvar=depvarx, yvar=depvary, reverse=False, smooth=False, usehist=True)
        if not alg.saveas(ws): return False
    else:
        alg = load(ws)

    # train alg
    if not args.force and alg.info.get("trained", False):
        log().info("{} already trained, skipping...".format(os.path.relpath(ws)))
    elif not alg.train(): return False
    elif not alg.save():  return False

    return True


def deco_wp(args):
    """Decorates the working points"""
    from loki.train import algs
    from loki.train.alg import load
    from loki.train.ntup import decorate_ntup
    from loki.core.sample import Sample
    ws = get_algname_flat(dir=args.algdir, prefix=args.prefix)
    alg = load(ws)
    if not alg:
        log().warn("Failure loading workspace: {}, skipping deco".format(ws))
        return False

    if not alg.info.get("trained", False):
        log().warn("{} not trained, skipping...".format(ws))
        return False

    for samp in samps:
        fname = get_fname_merge(dir=args.outdir, samp=samp)
        s = Sample(files=[fname])
        for wp, eff in workingpoints.items():
            # check for existing deco
            if s.has_varname(alg.get_var_name(eff=eff)) and not args.force:
                log().info("Will not overwrite existing var {} in {} (use --force)" \
                           .format(alg.get_var_name(eff=eff), os.path.relpath(fname)))
                continue
            # deco
            if not decorate_ntup(fname, alg, eff=eff, overwrite=True):
                log().error("Failed to decorate WP")
                return False

        # check for existing deco
        if s.has_varname(alg.get_var_name()) and not args.force:
            log().info("Will not overwrite existing var {} in {} (use --force)" \
                       .format(alg.get_var_name(), os.path.relpath(fname)))
            continue
        # deco
        if not decorate_ntup(fname, alg, overwrite=True):
            log().error("Failed to decorate Flat Score")
            return False

    return True


def make_bdt_plots(args):
    """Make BDT score plots"""
    from loki.core.hist import Hist, ROCCurve
    from loki.core.plot import Plot
    from loki.core.process import Processor
    from loki.core.file import OutputFileStream
    from loki.core.sample import Sample
    from loki.core.style import Style
    from loki.common.styles import style_list

    # Variables
    invars = [w.get_view() for w in set([v for reg in etaregs for v in bdtvars[reg]])]

    # Discriminants
    disc_new = get_var_bdt(args.prefix).var
    disc_new.add_view(40, -1.01, 1.01, name="coarse")
    disc_new.add_view(1000, -1.01, 1.01, name="roc")
    taus.BDTEleScore.add_view(1000, 0., 1.01, name="roc")
    discs = [
        taus.BDTEleScore.get_view(),
        disc_new.get_view("coarse"),
        ]

    plots = []
    for reg in etaregs:
        sig_train = Sample("sig_train", files=[get_fname_out(dir=args.outdir, reg=reg, samp="sig_train")],
                           sty=sty_hist_sig_train, weight=vars.weight)
        bkg_train = Sample("bkg_train", files=[get_fname_out(dir=args.outdir, reg=reg, samp="bkg_train")],
                           sty=sty_hist_bkg_train, weight=vars.weight)
        sig_test  = Sample("sig_test",  files=[get_fname_out(dir=args.outdir, reg=reg, samp="sig_test")],
                           sty=sty_hist_sig_test,  weight=vars.weight)
        bkg_test  = Sample("bkg_test",  files=[get_fname_out(dir=args.outdir, reg=reg, samp="bkg_test")],
                           sty=sty_hist_bkg_test,  weight=vars.weight)

        # score distributions
        for disc in discs:
            prefix = "Eta{reg}_{disc}".format(disc=disc.var.get_name(), reg=reg)
            h_sig_train = Hist(name="h_{}_sig_train".format(prefix), xvar=disc, sample=sig_train)
            h_bkg_train = Hist(name="h_{}_bkg_train".format(prefix),xvar=disc, sample=bkg_train)
            h_sig_test  = Hist(name="h_{}_sig_test".format(prefix), xvar=disc, sample=sig_test)
            h_bkg_test  = Hist(name="h_{}_bkg_test".format(prefix), xvar=disc, sample=bkg_test)
            p    = Plot("Overlay_{}".format(prefix), [h_sig_train, h_bkg_train, h_sig_test, h_bkg_test], extra_labels=[reg])
            plog = Plot("Overlay_{}_logy".format(prefix), [h_sig_train, h_bkg_train, h_sig_test, h_bkg_test], extra_labels=[reg], logy=True)
            plots += [p,plog]

        # score vs input scatters
        for var in invars:
            prefix = "Eta{reg}_{var}".format(var=var.var.get_name(), reg=reg)
            hsig = Hist(name="h_{}_sig".format(prefix), xvar=var, sample=sig_test)
            hbkg = Hist(name="h_{}_bkg".format(prefix), xvar=var, sample=bkg_test)
            p = Plot("Dist_"+prefix, [hsig,hbkg], extra_labels=[reg])
            plots+=[p]

            for disc in discs:
                prefix = "Eta{reg}_{disc}_vs_{var}".format(disc=disc.var.get_name(), var=var.var.get_name(), reg=reg)
                h2 = Hist(name="h_"+prefix, xvar=disc, yvar=var, sample=sig_test)
                p = Plot("Scatter_"+prefix, [h2], extra_labels=[reg])
                plots+=[p]

        # rocs
        if discs:
            rocs = []
            for i, disc in enumerate(discs):
                prefix = "Eta{reg}_{disc}".format(disc=disc.var.get_name(), reg=reg)
                color = style_list[i].LineColor
                sty_test  = Style("RocTest",  tlatex="{} (test)".format(disc.var.get_name()),  LineColor=color, LineWidth=3, drawopt="L", MarkerStyle=0)
                sty_train = Style("RocTrain", tlatex="{} (train)".format(disc.var.get_name()), LineColor=color, LineWidth=2, LineStyle=2, drawopt="L", MarkerStyle=0)
                roc_train = ROCCurve(name="h_{}_roc_train".format(prefix), sample=sig_train, bkg=bkg_train, xvar=disc.var.get_view("roc"), sty=sty_train, noleg=True)
                roc_test  = ROCCurve(name="h_{}_roc_test".format(prefix), sample=sig_test, bkg=bkg_test, xvar=disc.var.get_view("roc"), sty=sty_test)
                rocs+=[roc_train, roc_test]
            p_roc = Plot("ROC_Eta{reg}".format(reg=reg), rocs, logy=True, extra_labels=[reg])
            plots += [p_roc]

    proc = Processor()
    proc.draw_plots(plots)

    ofstream = OutputFileStream("canvases_bdt.root")
    ofstream.write(plots)

    return True


def make_wp_plots(args):
    """Make working point plots"""
    from loki.core.hist import Hist, EffProfile
    from loki.core.plot import Plot
    from loki.core.var import Var
    from loki.core.process import Processor
    from loki.core.file import OutputFileStream
    from loki.core.sample import Sample
    from loki.common import styles
    from loki.train import algs
    from loki.train.alg import load

    # get tuning alg
    ws = get_algname_flat(dir=args.algdir, prefix=args.prefix)
    alg = load(ws)
    if not alg:
        log().warn("Failure loading workspace: {}, skipping deco".format(ws))
        return

    # define samples
    sig_train = Sample("sig_train", files=[get_fname_merge(dir=args.outdir, samp="sig_train")],
                       sty=styles.SignalTrain, weight=vars.weight)
    bkg_train = Sample("bkg_train", files=[get_fname_merge(dir=args.outdir, samp="bkg_train")],
                       sty=styles.BackgroundTrain, weight=vars.weight)
    sig_test = Sample("sig_test", files=[get_fname_merge(dir=args.outdir, samp="sig_test")],
                      sty=styles.SignalTest, weight=vars.weight)
    bkg_test = Sample("bkg_test", files=[get_fname_merge(dir=args.outdir, samp="bkg_test")],
                      sty=styles.BackgroundTest, weight=vars.weight)

    plots = []

    # efficiency plots
    for (wpname, wpeff) in workingpoints.items():
        tag = wpname
        tar = "Target Eff: {:02d}%".format(int(wpeff * 100.))
        extra_labels = [tag, tar]
        sel = Var(alg.get_var_name(eff=wpeff), temp=True)
        for depvar in depvars:
            prefix = "{disc}_{wpname}_vs_{depvar}".format(
                disc=args.prefix, wpname=wpname, depvar=depvar.var.get_name())
            h_sig_train = EffProfile(name="h_{}_sig_train".format(prefix), sample=sig_train, xvar=depvar, sel_pass=sel)
            h_bkg_train = EffProfile(name="h_{}_bkg_train".format(prefix), sample=bkg_train, xvar=depvar, sel_pass=sel)
            h_sig_test  = EffProfile(name="h_{}_sig_test".format(prefix),  sample=sig_test,  xvar=depvar, sel_pass=sel)
            h_bkg_test  = EffProfile(name="h_{}_bkg_test".format(prefix),  sample=bkg_test,  xvar=depvar, sel_pass=sel)
            psig = Plot("SigEff_{}".format(prefix), [h_sig_train, h_sig_test], extra_labels=extra_labels, ymin=0., ymax=1.2)
            pbkg = Plot("FakeRate_{}".format(prefix), [h_bkg_train, h_bkg_test], extra_labels=extra_labels, ymin=0.)
            plots += [psig, pbkg]

    # flat score distribution
    disc = Var(alg.get_var_name(), temp=True).add_view(40, 0., 1.01)
    view = disc.get_view()
    h_sig_train = Hist(name="h_{}_sig_train".format(prefix), xvar=view, sample=sig_train, sty=sty_hist_sig_train)
    h_bkg_train = Hist(name="h_{}_bkg_train".format(prefix), xvar=view, sample=bkg_train, sty=sty_hist_bkg_train)
    h_sig_test = Hist(name="h_{}_sig_test".format(prefix), xvar=view, sample=sig_test, sty=sty_hist_sig_test)
    h_bkg_test = Hist(name="h_{}_bkg_test".format(prefix), xvar=view, sample=bkg_test, sty=sty_hist_bkg_test)
    p = Plot("Overlay_{}".format(disc.get_name()), [h_sig_train, h_bkg_train, h_sig_test, h_bkg_test])
    plog = Plot("Overlay_{}_logy".format(disc.get_name()), [h_sig_train, h_bkg_train, h_sig_test, h_bkg_test], logy=True)
    plots += [p, plog]

    proc = Processor()
    proc.draw_plots(plots)

    ofstream = OutputFileStream("canvases_wp.root")
    ofstream.write(plots)

    return True

def run_all(args):
    """Runs all steps"""

    from threading import Thread

    #for f in (spawn_bdt, train_bdt, deco_bdt, make_bdt_plots, merge_regs, tune_wp, deco_wp, make_wp_plots):
    for f in (spawn_bdt, train_bdt, deco_bdt, merge_regs, tune_wp, deco_wp):
        log().info("")
        log().info("-----> Executing {}".format(f.__name__))

        #t = Thread(target=f, args=(args,))
        #t.start()
        #t.join()

        if not f(args):
            log().error("Encountered failure in step, aborting!")
            return False

    return True






if __name__ == "__main__": main()
## EOF
