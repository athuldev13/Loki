import argparse
import glob
import os
import shutil

from loki.core.setup import setup
from loki.core.logger import log
from loki.core.sample import Sample
from loki.core.var import Var
from loki.train import algs
from loki.train.alg import load
from loki.train.ntup import decorate_ntup
from loki.common import vars

# Module containing new variables and binnings
from loki.utils.helpers import import_module
import_module(os.path.join(os.path.dirname(__file__), "defs.py"))

taus = vars.taus

# BDT setup
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

# Input variables for the BDT
bdtvars = {
    "1P": [
        taus.centFrac,
        taus.etOverPtLeadTrk,
        taus.innerTrkAvgDist,
        taus.absipSigLeadTrk,
        taus.SumPtTrkFrac,
        taus.EMPOverTrkSysP,
        taus.ptRatioEflowApprox,
        taus.mEflowApprox,
        taus.ptIntermediateAxis_clamped
    ],
    "3P": [
        taus.centFrac,
        taus.innerTrkAvgDist,
        taus.dRmax,
        taus.trFlightPathSig,
        taus.massTrkSys,
        taus.EMPOverTrkSysP,
        taus.ptRatioEflowApprox,
        taus.mEflowApprox,
        taus.SumPtTrkFrac,
        taus.ptIntermediateAxis_clamped
    ]
}

# Naming scheme for samples
ntuples = {
    "1P": {
        "sig_train": "sig1P_train_outl.root",
        "sig_test": "sig1P_test.root",
        "bkg_train": "bkg1P_weight_train_outl.root",
        "bkg_test": "bkg1P_weight_test.root"
    },
    "3P": {
        "sig_train": "sig3P_train_outl.root",
        "sig_test": "sig3P_test.root",
        "bkg_train": "bkg3P_weight_train_outl.root",
        "bkg_test": "bkg3P_weight_test.root"
    }
}

# Working point efficiencies
workingpoints = {
    "1P": {
        "VeryLoose": 95,
        "Loose": 85,
        "Medium": 75,
        "Tight": 60
    },
    "3P": {
        "VeryLoose": 95,
        "Loose": 75,
        "Medium": 60,
        "Tight": 45
    }
}

# BDT score for pt & mu flattening
bdtscore1p = Var("JetBDTScore1P")
bdtscore1p.add_view(1000, -1., 1., name="flat_r21")
bdtscore3p = Var("JetBDTScore3P")
bdtscore3p.add_view(1000, -1., 1., name="flat_r21")


def file_suffix(fname, suffix):
    """Appends a suffix to a filename.

    >>> file_suffix("ntuples/sig1P.root", "_deco")
    'ntuples/sig1P_deco.root'
    """
    name, ext = os.path.splitext(fname)
    fname = name + suffix + ext
    return fname


def spawn_bdt(args):
    """Spawns 1- and 3-prong Tau-ID BDT configurations"""
    for prong in ntuples:
        # Sample dictionary mapping sig./bkg. train/test samples to loki
        # samples
        sample_dict = dict()
        for name, fname in ntuples[prong].items():
            path = os.path.abspath(os.path.join(args.indir, fname))
            if not os.path.exists(path):
                log().warning("Ntuple {} does not exist.".format(path))
            sample_dict[name] = Sample(name=name, files=[path],
                                       weight=vars.weight)

        # Build & spawn BDTs
        alg = algs.TMVAClassifier(name="JetBDTScore{}".format(prong),
                                  tmvatype="BDT", invars=bdtvars[prong],
                                  algopts=bdtopts, **sample_dict)
        wspath = os.path.join(args.outdir, "JetBDT{}.alg".format(prong))
        alg.saveas(wspath)


def train_bdt(args):
    """Trains all untrained BDTS"""
    workspaces = glob.glob(os.path.join(args.indir, "JetBDT[1,3]P.alg"))
    if not workspaces:
        log().warning("No workspaces found.")
    for ws in workspaces:
        alg = load(ws)
        if alg.info.get("trained", False):
            log().info("{} already trained, skipping...".format(ws))
        elif not alg.train():
            log().error("Failure training {}".format(ws))
        else:
            alg.save()


def deco_bdt(args):
    """Decorates the BDT scores onto the testing samples"""
    workspaces = glob.glob(os.path.join(args.indir, "JetBDT[1,3]P.alg"))
    if not workspaces:
        log().warning("No workspaces found.")
    for ws in workspaces:
        alg = load(ws)
        if not alg.info.get("trained", False):
            log().warning("{} not trained, skipping...".format(ws))
            continue

        try:
            sigf, = alg.sig_test.files
            bkgf, = alg.bkg_test.files
        except ValueError:
            log().error("Only one file per testing sample supported.")
            continue

        for f in (sigf, bkgf):
            fname = file_suffix(os.path.basename(f), "_deco")
            dest = os.path.join(args.outdir, fname)
            # Copy testing sample for decoration
            log().info("Copying {src} to {dest}".format(src=f, dest=dest))
            shutil.copyfile(f, dest)

            # Decorate
            if not decorate_ntup(dest, alg, overwrite=True):
                log().error("Failed to decorate BDT score")
                exit(1)


def tune_wp(args):
    """Tunes the working points"""
    for prong in workingpoints:
        # Spawn algorithms
        name, ext = os.path.splitext(ntuples[prong]["sig_test"])
        fname = name + "_deco" + ext
        sig_path = os.path.join(args.indir, fname)
        sig_test = Sample(name="sig_test", files=[sig_path],
                          weight=vars.weight)

        if prong == "1P":
            disc = bdtscore1p.get_view("flat_r21")
        else:
            disc = bdtscore3p.get_view("flat_r21")

        xvar = taus.get_var("pt").get_view("flat_r21")
        yvar = taus.get_var("mu").get_view("flat_r21")

        alg = algs.MVScoreTuner(
            name="FlatScore{}".format(prong), sig_train=sig_test, disc=disc,
            xvar=xvar, yvar=yvar, reverse=False, smooth=False, usehist=True)

        wspath = os.path.join(args.outdir, "FlatJetBDT{}.alg".format(prong))
        alg.saveas(wspath)

        if not alg.train():
            log().error("Failure training {}".format(wspath))
            continue

        alg.save()


def deco_wp(args):
    """Decorates the working points"""
    workspaces = glob.glob(os.path.join(args.indir, "FlatJetBDT[1,3]P.alg"))
    if not workspaces:
        log().warning("No workspaces found.")
    for ws in workspaces:
        alg = load(ws)
        prong = "1P" if "1P" in alg.name else "3P"
        if not alg.info.get("trained", False):
            log().warning("{} not trained, skipping...".format(ws))
            continue

        try:
            sigf, = alg.sig_train.files
        except ValueError:
            log().warning("Only one sample supported")
            continue

        # Infer background sample from alg's signal sample
        if "1P" in os.path.basename(sigf):
            bkgf = file_suffix(ntuples["1P"]["bkg_test"], "_deco")
        elif "3P" in os.path.basename(sigf):
            bkgf = file_suffix(ntuples["3P"]["bkg_test"], "_deco")
        else:
            log().error("Background sample for WP decoration could not be "
                        "inferred")
            continue

        bkgf = os.path.join(os.path.dirname(sigf), bkgf)

        # Copy files and decorate WPs
        for f in (sigf, bkgf):
            dest = file_suffix(os.path.basename(f), "_wp")
            dest = os.path.join(args.outdir, dest)
            shutil.copyfile(f, dest)

            # Decorate
            for wp, eff in workingpoints[prong].items():
                if not decorate_ntup(dest, alg, eff=eff, overwrite=True):
                    log().error("Failed to decorate WP")
                    exit(1)


def run_all(args):
    """Runs all steps"""
    # Spawn training from args.indir to args.outdir
    spawn_bdt(args)

    # Run remaining steps in same directory
    args = argparse.Namespace(indir=args.outdir, outdir=args.outdir)
    for f in (train_bdt, deco_bdt, tune_wp, deco_wp):
        f(args)


def get_args():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    # all
    all_parser = subparsers.add_parser(
        "all",
        help="Executes all actions")
    all_parser.add_argument(
        "--indir", default="",
        help="Directory containing the ntuples")
    all_parser.add_argument(
        "--outdir", default="",
        help="Directory where all outputs will be saved")
    all_parser.set_defaults(func=run_all)

    # spawn-bdt
    spawn_bdt_parser = subparsers.add_parser(
        "spawn-bdt",
        help="Spawns BDT configurations")
    spawn_bdt_parser.add_argument(
        "--indir", default="",
        help="Directory containing training and testing ntuples")
    spawn_bdt_parser.add_argument(
        "--outdir", default="",
        help="Directory for workspace outputs")
    spawn_bdt_parser.set_defaults(func=spawn_bdt)

    # train-bdt
    train_bdt_parser = subparsers.add_parser(
        "train-bdt",
        help="Trains the BDTs")
    train_bdt_parser.add_argument(
        "--indir", default="",
        help="Directory containing the BDT workspaces")
    train_bdt_parser.set_defaults(func=train_bdt)

    # deco-bdt
    deco_bdt_parser = subparsers.add_parser(
        "deco-bdt",
        help="Decorates BDT scores")
    deco_bdt_parser.add_argument(
        "--indir", default="",
        help="Directory containing the trained algorithms")
    deco_bdt_parser.add_argument(
        "--outdir", default="",
        help="Directory where the decorated ntuples will be saved")
    deco_bdt_parser.set_defaults(func=deco_bdt)

    # tune-wp
    tune_wp_parser = subparsers.add_parser(
        "tune-wp",
        help="Trains the pt & mu flattening")
    tune_wp_parser.add_argument(
        "--indir", default="",
        help="Directory containing the ntuples with decorated BDT scores")
    tune_wp_parser.add_argument(
        "--outdir", default="",
        help="Directory where the tunings will be saved")
    tune_wp_parser.set_defaults(func=tune_wp)

    # deco-wp
    deco_wp_parser = subparsers.add_parser(
        "deco-wp",
        help="Decorates flat efficiency working points")
    deco_wp_parser.add_argument(
        "--indir", default="",
        help="Directory containing the flattening workspaces")
    deco_wp_parser.add_argument(
        "--outdir", default="",
        help="Output directory for the ntuples with decorated working points")
    deco_wp_parser.set_defaults(func=deco_wp)

    return parser.parse_args()


if __name__ == "__main__":
    args = get_args()
    setup()
    args.func(args)

