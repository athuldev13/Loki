# encoding: utf-8
"""
config.py

define data transfers for example input files

"""
__author__    = "Will Davey"
__email__     = "will.davey@cern.ch"
__created__   = "2016-02-29"
__copyright__ = "Copyright 2016 Will Davey"
__license__   = "GPL http://www.gnu.org/licenses/gpl.html"


## modules
import os
import subprocess
from loki.core.logger import log

def get_file(fname): 
    """Get test file from Will's afs area"""    
    if not os.path.exists(fname):
        log().info("Input file not accessible, checking locally...")
        newpath = os.path.basename(fname)
        if os.path.exists(newpath): 
            log().info("Found local file: %s"%(newpath))
            fname = newpath
        else: 
            log().info("Nothing found locally, attemping data-transfer...")
            cmd = "scp lxplus.cern.ch:%s ."%(fname)
            print(cmd)
            p = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE)
            print(p.communicate()[0])
            fname = newpath
            if os.path.exists(fname): 
                log().info("Transferred successfully")
            else: 
                log().error("Transferred failed! Aborting example.")
                exit(1)
    return fname

def get_file1(): 
    """Get input for example1"""
    testfile = "/eos/atlas/atlascerngroupdisk/perf-tau/MxAODs/LokiTestData/mc23_13p6TeV.801002.Py8EG_A14NNPDF23LO_Gammatautau_MassWeight.recon.AOD.e8514_s4159_r14799.root"
    return get_file(testfile)

def get_bkg_file(): 
    """Get background sample"""
    testfile = "/eos/atlas/atlascerngroupdisk/perf-tau/MxAODs/LokiTestData/mc23_13p6TeV.801169.Py8EG_A14NNPDF23LO_jj_JZ4.recon.AOD.e8514_s4159_r14799.root" 
    return get_file(testfile)

def get_samples_dir():
    """Prepare samples directory for use with FileLoader"""
    fname = get_file1()
    basedir = "/eos/atlas/atlascerngroupdisk/perf-tau/MxAODs/R22/Run2repro/TauID"
    sampledir = "group.perf-tau.MC20d_RNNID.425200.Pythia8EvtGen_A14NNPDF23LO_Gammatautau_MassWeight_v1_output.root"
    dir = os.path.join(basedir,sampledir)
    path = os.path.join(dir,fname)
    if not os.path.exists(dir): os.makedirs(dir)
    if not os.path.lexists(path):
        log().info("Creating symlinks for file2") 
        os.symlink(os.path.relpath(fname,dir), path)
    return basedir  
    











## EOF
