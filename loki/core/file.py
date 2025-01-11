# encoding: utf-8
"""
loki.core.file
~~~~~~~~~~~~~~

This module provides *file handler* classes
to set the input MxAOD file paths for samples.

Currently only a basic implementation is provided. 
"""
__author__    = "Will Davey"
__email__     = "will.davey@cern.ch"
__created__   = "2016-02-25"
__copyright__ = "Copyright 2016 Will Davey"
__license__   = "GPL http://www.gnu.org/licenses/gpl.html"



## modules
from glob import glob
import os
from ROOT import TFile
from loki.core.logger import log


# - - - - - - - - - - - class defs  - - - - - - - - - - - - #
#------------------------------------------------------------
class FileHandler():
    """Simple class to set input MxAOD file paths for samples.

    For each sample it adds input files matching the string: 
        `{data_path}/\*{sample}*/\*.root*`

    Ie it scans the *data_path* for sub-directories containing 
    names of the *samples* and then looks for ROOT files within 
    those directories.    

    :param data_path: path to samples directory
    :type data_path: str
    :param samples: list of Samples to find inputs for 
    :type samples: `loki.core.sample.Sample` list
    :param check: if True, filter out corrupt files
    :type check: bool
    """
    #____________________________________________________________
    def __init__(self,data_path,samples,check=True,treename=None):
        ## TODO: could make this more flexible 
        ## eg put loading in initialize function and allow configables?
        
        # check data_path
        if not os.path.exists(data_path):
            errorstr = """Specified input data path doesn't exist: {}
                    Should point to directory CONTAINING your dataset directories!""".format(data_path) 
            log().error(errorstr)
            raise IOError
        
        # load files
        total_files = []
        filepath = "{dirname}/{regex}/*.root*"
        log().info(f"Scanning {data_path}...")
        for sample in samples: 
            daughters = sample.get_final_daughters()
            for d in daughters:
                # get files for daughter
                searchstr = filepath.format(dirname=data_path,regex=d.regex)
                log().debug(f"scanning {searchstr}...")
                files = glob(searchstr)
                if check:
                    checked_files = []
                    for fname in files:
                        if not file_ok(fname):
                            log().warn(f"File {fname} corrupt, skipping...")
                        else:
                            checked_files.append(fname)
                    files = checked_files
                if not files: 
                    log().warn(f"No files found for sample {d.name}")
                    continue
                d.files = files                
                total_files += files                
                if treename is not None: d.treename = treename
                log().info(f"Found {len(files)} files for {d.name}")
                
        if not total_files: 
            errorstr = """No input files for any sample found in path {}
                    Path should point to directory CONTAINING your dataset directories!""".format(data_path)
            log().error(errorstr)
            raise IOError


#------------------------------------------------------------
class OutputFileStream():
    """Class to write ROOT objects to file
    
    Currently works with:  
    
    * :class:`loki.core.hist.RootDrawable`
    * :class:`loki.core.plot.Plot`
    
    All sub-drawable objects will also be written.
     
    :param fname: output file name
    :type fname: str
    """
    #____________________________________________________________
    def __init__(self,fname):
        try: 
            self.f = TFile.Open(fname,"RECREATE")
        except:
            log().error(f"Failed to open output stream {fname}")
            raise
            
    #____________________________________________________________
    def write(self, drawables, path=None):
        """Write drawables to file
        
        :param drawables: list of drawable objects 
        :type drawables: list :class:`loki.core.hist.RootDrawable`
        :param path: file sub-directory in which to store drawables 
        :type path: str        
        """
        # require drawables
        if drawables is None: 
            log().warn("'None' passed to OutputFileStream.write(), skipping")
            return
        
        # convert drawables to list (if single)
        if not isinstance(drawables,list): drawables = [drawables]
        
        # create sub-directory
        f = self.f
        if path is not None:
            path = path.strip("/")
            if not f.GetDirectory(path): 
                f.mkdir(path)
            f = f.GetDirectory(path)
            
        # write drawables to file
        for d in drawables: 
            d.write(f)

#______________________________________________________________________________=buf=
def file_ok(fname):
    if not os.path.exists(fname): return False
    f = TFile.Open(fname)
    if not f: return False
    if f.IsZombie() or f.TestBit(TFile.kRecovered):
        f.Close()
        return False
    return True

#______________________________________________________________________________=buf=
def get_unique_sequential_filename(fname):
    """Return unique filename with sequential suffix"""
    (filename, ext) = os.path.splitext(fname)
    n=1
    while True: 
        fname_new = "{0}_v{1:d}{2}".format(filename,n,ext)
        if not os.path.exists(fname_new): 
            return fname_new
        n+=1


        

## EOF
