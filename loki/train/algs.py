# encoding: utf-8
"""
loki.train.algs.py
~~~~~~~~~~~~~~~~~~

Subclass implementations of :class:`~loki.train.alg.AlgBase`

"""
__author__    = "Will Davey"
__email__     = "will.davey@cern.ch"
__created__   = "2016-07-20"
__copyright__ = "Copyright 2016 Will Davey"
__license__   = "GPL http://www.gnu.org/licenses/gpl.html"


## modules
import os
import pkgutil
import random
from array import array
from ROOT import TFile, TCut, TMVA, TH2, TGraph, TGraph2D, TNamed, TParameter

from loki.common import vars
from loki.core.hist import RootDrawable, Hist
from loki.core.histutils import normalize, convert_hist_to_2dhist, frange
from loki.core.logger import log
from loki.core.sample import Sample
from loki.core.var import get_variable, get_variables, find_view, get_view
from loki.core.process import samples2dmatrix
from loki.train.alg import AlgBase



# - - - - - - - - - - - - - - -  class defs - - - - - - - - - - - - - - - - - #

# ------------------------------------------------------------------------------=buf=
class TMVABase(AlgBase):
    """Base-class providing an interface for algorithm training with TMVA

    The predict method is provided as it is generic across all TMVA implementations.
    The train method must be implemented in the subclass. A number of helper functions
    are also provided.

    Set your algorithm type with *tmvatype*.

    The algorithm options (*algopts*) are passed to the TMVA algorithm (classifier/regressor).
    They are converted to a single configuration string based on their value
    as follows:

        * None - excluded from option string
        * True - key only included
        * False - key only included with preceeding ! (ie 'not')
        * else - "key:value" included

    The factory options (*factopts*) are passed to the TMVA Factory.

    For a full set of algorithm and Factory options see the
    `TMVA Users Guide <http://tmva.sourceforge.net/docu/TMVAUsersGuide.pdf>`_.

    *wspath* and *info* are not to be set by the user (see :class:`~loki.train.alg.AlgBase`)

    :param name: algorithm name
    :type name: str
    :param tmvatype: type of classifier, should match a type in TMVA.Types, but with the preceding 'k' removed (default: 'BDT' = TMVA.Types.kBDT)
    :type tmvatype: str
    :param algopts: options passed to TMVA Algorithm (Classifier/Regressor)
    :type algopts: dict
    :param factopts: options passed to TMVA Factory (eg. {"Silent": True})
    :type factopts: dict
    :param invars: input variables
    :type invars: list :class:`~loki.core.var.VarBase` subclass
    :param cname: alg name for internal use
    :type cname: str
    :param kw: key-word args passed to :class:`~loki.train.alg.AlgBase`
    """

    # __________________________________________________________________________=buf=
    def __init__(self, name=None, wspath=None, info=None, tmvatype=None,
                 valtype=None, algopts=None, factopts=None, invars=None, cname=None):
        if name is None: name = "TMVAAlg"
        if valtype is None: valtype = 'f'
        AlgBase.__init__(self, name=name, wspath=wspath, info=info, valtype=valtype)

        # set defaults
        if algopts is None: algopts = dict()
        if factopts is None: factopts = dict()
        if invars is None: invars = list()
        if tmvatype is None: tmvatype = "BDT"
        factopts.setdefault("V", False)
        factopts.setdefault("Silent", False)
        factopts.setdefault("Color", True)
        factopts.setdefault("DrawProgressBar", True)
        factopts.setdefault("Transformations", None)
        algopts.setdefault("H", False)
        algopts.setdefault("V", False)
        algopts.setdefault("NegWeightTreatment", "IgnoreNegWeightsInTraining")

        # process complex types (Sample done automatically)
        invars = get_variables(invars)

        # set attributes
        self.tmvatype = tmvatype
        self.algopts = algopts
        self.factopts = factopts
        self.invars = invars
        self.cname = cname

        # members
        self.values = []

    # Subclass overrides
    # __________________________________________________________________________=buf=
    def __subclass_predict__(self, s):
        """Sub-class specific prediction implementation

        "tree2array gives you a strucutred array which is analogous to a array
        of c-structs meaning effectivey your shape is (number of events, 1)
        but the tmva thing wants (number of events, number of variables)"
        http://stackoverflow.com/questions/5957380/convert-structured-array-to-regular-numpy-array

        """
        fmodel = self.__get_fmodel_path__()

        # checks
        if not fmodel:
            log().error("No model file, cannot predict")
            return None
        if not s:
            log().error("No input sample, cannot predict")
            return None

        # initialize TMVA reader
        t = s.get_tree()
        r = TMVA.Reader("")
        values = []
        for var in self.invars:
            var.tree_init(t)
            val = array('f', [0])
            values.append(val)
            r.AddVariable(var.get_expr(), val)
        r.BookMVA(self.cname, fmodel)
        self.values = values

        # crunch the numbers
        if pkgutil.find_loader("root_numpy"):
            # use root-numpy if available
            from root_numpy.tmva import evaluate_reader
            import numpy as np
            inputs = s.get_ndarray(invars=self.invars, noweight=True)
            # Cast structured array to only contain float32 fields
            dtype = [(fname, np.float32) for fname, ftype in inputs.dtype.descr]
            inputs = inputs.astype(dtype, copy=False)
            # Reshape structured array to ndarray
            reshaped = inputs.view(np.float32).reshape(inputs.shape + (-1,))
            output = evaluate_reader(r, self.cname, reshaped)
            from loki.core.process import ndarray2array
            output = ndarray2array(output)
        else:
            # python based predict
            log().warn("Using python-loop because root_numpy not available. Suggest to source setup_dev.sh")
            inputs = s.get_arrays(invars=self.invars, noweight=True)
            self.reader = r
            output = self.__predict_python_loop__(inputs)

        return output

    # __________________________________________________________________________=buf=
    def __predict_single__(self, invals):
        """Sub-class specific prediction implementation"""
        for i, val in enumerate(invals):
            self.values[i][0] = val
        return self.reader.EvaluateMVA(self.cname)

    # Helper functions
    # __________________________________________________________________________=buf=
    def __get_algtype__(self):
        """Return option string for the Classifier"""
        return f'k{self.tmvatype}'

    # __________________________________________________________________________=buf=
    def __get_optstr__(self, optdict):
        """Converts dictionary into TMVA formatted option string

        Value types are treated as follows:

        * None - excluded from option string
        * True - key only included
        * False - key only included with preceeding ! (ie 'not')
        * else - "key:value" included
        """
        # determine (tmva) option string from *optdict* dict
        optstrs = []
        for k, v in optdict.items():
            if v is None: continue
            if v is True:
                optstrs.append(k)
            elif v is False:
                optstrs.append(f"!{k}")
            else:
                optstrs.append(f"{k}={v}")
        optstr = str(":".join(optstrs))
        return optstr

    # __________________________________________________________________________=buf=
    def __get_factory_optstr__(self):
        """Return option string for TMVA Factory"""
        return self.__get_optstr__(self.factopts)

    # __________________________________________________________________________=buf=
    def __get_alg_optstr__(self):
        """Return option string for the Classifier"""
        return self.__get_optstr__(self.algopts)

    # __________________________________________________________________________=buf=
    def __get_original_model_fname__(self):
        """Return path of the classifier model configration (overwrite in subclass)"""
        return f"dataset/weights/{self.name}_{self.cname}.weights.xml"

    # __________________________________________________________________________=buf=
    def __get_original_plots_fname__(self):
        """Return path of the classifier model configration (overwrite in subclass)"""
        return "TMVA.root"
        # return f"{self.name}_plots.root"


#------------------------------------------------------------------------------=buf=
class TMVAClassifier(TMVABase):
    """Interface for classifier training with TMVA 

    A description of the generic interaction with TMVA is provided in the base-class
    :class:`TMVABase`.

    For a full set of Classifier and Factory options see the 
    `TMVA Users Guide <http://tmva.sourceforge.net/docu/TMVAUsersGuide.pdf>`_.  

    Signal/background training/testing samples should be provided.
    If *sig_test* and *bkg_test* are not supplied, TMVA will split 
    *sig_train* and *bkg_train* in half to create the testing samples.

    *wspath* and *info* are not to be set by the user (see :class:`~loki.train.alg.AlgBase`)  
    
    :param name: algorithm name
    :type name: str
    :param tmvatype: type of classifier, should match a type in TMVA.Types, but with the preceding 'k' removed (default: 'BDT' = TMVA.Types.kBDT)
    :type tmvatype: str
    :param algopts: options passed to TMVA Classifier
    :type algopts: dict
    :param factopts: options passed to TMVA Factory (eg. {"Silent": True})
    :type factopts: dict
    :param invars: input variables
    :type invars: list :class:`~loki.core.var.VarBase` subclass
    :param sig_train: signal training sample
    :type sig_train: :class:`~loki.core.sample.Sample`
    :param bkg_train: background training sample
    :type bkg_train: :class:`~loki.core.sample.Sample`
    :param sig_test: signal testing sample
    :type sig_test: :class:`~loki.core.sample.Sample`
    :param bkg_test: background testing sample
    :type bkg_test: :class:`~loki.core.sample.Sample`
    :param kw: key-word args passed to :class:`~loki.train.alg.AlgBase`
    """
    #__________________________________________________________________________=buf=
    def __init__(self, name = None, wspath = None, info = None,
                 tmvatype = None, algopts = None, factopts = None, 
                 invars = None, sig_train = None, bkg_train = None, 
                 sig_test = None, bkg_test = None): 
        if name is None: name = "TMVAClassifier"
        TMVABase.__init__(self, name=name, wspath=wspath, info=info,
                          tmvatype=tmvatype, algopts=algopts, factopts=factopts,
                          invars=invars, cname="classifier")

        # set defaults
        if sig_train is None: sig_train = Sample("sig_train", weight=vars.weight, files=[])
        if bkg_train is None: bkg_train = Sample("bkg_train", weight=vars.weight, files=[])
        if sig_test is None: sig_test = Sample("sig_test", weight=vars.weight, files=[])
        if bkg_test is None: bkg_test = Sample("bkg_test", weight=vars.weight, files=[])
        self.factopts.setdefault("AnalysisType", "Classification")

        # set attributes        
        self.sig_train = sig_train
        self.bkg_train = bkg_train
        self.sig_test = sig_test
        self.bkg_test = bkg_test


    # Subclass overrides
    #__________________________________________________________________________=buf=
    def __subclass_train__(self):
        """Train the classifier
        
        Concrete implementation of the base-class interface
        """
        ## configuration
        fname_plots    = self.__get_original_plots_fname__()
        fname_model    = self.__get_original_model_fname__()            
        factory_optstr = self.__get_factory_optstr__()
        alg_optstr     = self.__get_alg_optstr__()
        mvatypestr     = self.__get_algtype__()
                
        # pre-train checks
        if not self.ispersistified(): 
            log().error("TMVAClassifier must be persistified before training (call 'saveas')")
            return False
        if not self.invars: 
            log().error("No input vars defined, cannot train!")
            return False        
        if not hasattr(TMVA.Types, mvatypestr):
            log().error(f"Invalid TMVA classifier type: {mvatypestr}")
            return False
        mvatype = getattr(TMVA.Types, mvatypestr) 
        
        # get samples with abspath
        sig_train = self.__get_sample_worker__(self.sig_train)
        bkg_train = self.__get_sample_worker__(self.bkg_train)
        sig_test = self.__get_sample_worker__(self.sig_test) if self.sig_test.files else None
        bkg_test = self.__get_sample_worker__(self.bkg_test) if self.bkg_test.files else None
        samples = [s for s in [sig_train, bkg_train, sig_test, bkg_test] if s is not None]
        if False in [self.__check_sample__(s) for s in samples]: return False

        # configure data-loader
        dl = TMVA.DataLoader("dataset")

        # set input trees
        tsig = sig_train.get_tree()
        tbkg = bkg_train.get_tree()
        if not (sig_test and bkg_test): # only train
            dl.SetInputTrees(tsig, tbkg, 1.0, 1.0)
        else:                                       # test and train
            tsig_test = sig_test.get_tree()
            tbkg_test = bkg_test.get_tree()             
            dl.AddSignalTree    (tsig,      1.0, TMVA.Types.kTraining)
            dl.AddBackgroundTree(tbkg,      1.0, TMVA.Types.kTraining)
            dl.AddSignalTree    (tsig_test, 1.0, TMVA.Types.kTesting)
            dl.AddBackgroundTree(tbkg_test, 1.0, TMVA.Types.kTesting)

        # set weights
        if sig_train.weight:
            sig_train.weight.tree_init(tsig) 
            dl.SetSignalWeightExpression(sig_train.weight.get_expr())
        if bkg_train.weight:
            bkg_train.weight.tree_init(tbkg)
            dl.SetBackgroundWeightExpression(bkg_train.weight.get_expr())

        # register variables
        for var in self.invars: 
            var.tree_init(tsig)
            dl.AddVariable(var.get_expr(), var.xtitle, var.xunit or "", var.get_type().upper())

        # configure regressor / factory
        fout = TFile.Open(fname_plots, "RECREATE")
        f = TMVA.Factory(self.name, fout, factory_optstr)
        f.BookMethod(dl, mvatype, self.cname, alg_optstr)
        
        ## train this puppy
        f.TrainAllMethods()
        
        ## test this puppy
        f.TestAllMethods()
        
        ## evaluate this puppy
        f.EvaluateAllMethods()

        ## move outputs to workspace
        fout.Close()
        self.__finalize_training_outputs__(fname_model, [fname_plots])

        return True



# ------------------------------------------------------------------------------=buf=
class TMVARegressor(TMVABase):
    """Interface for regression training with TMVA

    A description of the generic interaction with TMVA is provided in the base-class
    :class:`TMVABase`.

    For a full set of Classifier and Factory options see the
    `TMVA Users Guide <http://tmva.sourceforge.net/docu/TMVAUsersGuide.pdf>`_.

    Signal training/testing samples should be provided.
    If *sig_test* is not supplied, TMVA will split *sig_train* in half to create
    the testing sample.

    *wspath* and *info* are not to be set by the user (see :class:`~loki.train.alg.AlgBase`)

    :param name: algorithm name
    :type name: str
    :param tmvatype: type of classifier, should match a type in TMVA.Types, but with the preceding 'k' removed (default: 'BDT' = TMVA.Types.kBDT)
    :type tmvatype: str
    :param algopts: options passed to TMVA Classifier
    :type algopts: dict
    :param factopts: options passed to TMVA Factory (eg. {"Silent": True})
    :type factopts: dict
    :param invars: input variables
    :type invars: list :class:`~loki.core.var.VarBase` subclass
    :param sig_train: signal training sample
    :type sig_train: :class:`~loki.core.sample.Sample`
    :param sig_test: signal testing sample
    :type sig_test: :class:`~loki.core.sample.Sample`
    :param kw: key-word args passed to :class:`~loki.train.alg.AlgBase`
    """

    # __________________________________________________________________________=buf=
    def __init__(self, name=None, wspath=None, info=None,
                 tmvatype=None, algopts=None, factopts=None,
                 invars=None, target=None, sig_train=None, sig_test=None):
        if name is None: name = "TMVARegressor"
        TMVABase.__init__(self, name=name, wspath=wspath, info=info,
                          tmvatype=tmvatype, algopts=algopts, factopts=factopts,
                          invars=invars, cname="regressor")

        # set defaults
        if sig_train is None: sig_train = Sample("sig_train", weight=vars.weight, files=[])
        if sig_test is None: sig_test = Sample("sig_test", weight=vars.weight, files=[])
        self.factopts.setdefault("AnalysisType", "Regression")

        # process complex types (Sample done automatically)
        target = get_variable(target)

        # set attributes
        self.target = target
        self.sig_train = sig_train
        self.sig_test = sig_test

    # Subclass overrides
    # __________________________________________________________________________=buf=
    def __subclass_train__(self):
        """Train the regressor

        Concrete implementation of the base-class interface
        """
        ## configuration
        fname_plots = self.__get_original_plots_fname__()
        fname_model = self.__get_original_model_fname__()
        factory_optstr = self.__get_factory_optstr__()
        alg_optstr = self.__get_alg_optstr__()
        mvatypestr = self.__get_algtype__()

        # pre-train checks
        if not self.ispersistified():
            log().error("TMVARegressor must be persistified before training (call 'saveas')")
            return False
        if not self.invars:
            log().error("No input vars defined, cannot train!")
            return False
        if not self.target:
            log().error("No target defined, cannot train!")
            return False
        if not hasattr(TMVA.Types, mvatypestr):
            log().error(f"Invalid TMVA classifier type: {mvatypestr}")
            return False
        mvatype = getattr(TMVA.Types, mvatypestr)

        # get samples with abspath
        sig_train = self.__get_sample_worker__(self.sig_train)
        sig_test = self.__get_sample_worker__(self.sig_test) if self.sig_test.files else None
        samples = [s for s in [sig_train, sig_test] if s is not None]
        if False in [self.__check_sample__(s) for s in samples]: return False


        # configure data-loader
        dl = TMVA.DataLoader("dataset")

        # set input trees
        tsig = sig_train.get_tree()
        dl.AddRegressionTree(tsig, 1.0, TMVA.Types.kTraining)
        if sig_test:  # test tree also
            tsig_test = sig_test.get_tree()
            dl.AddRegressionTree(tsig_test, 1.0, TMVA.Types.kTesting)

        # set weights
        if sig_train.weight:
            sig_train.weight.tree_init(tsig)
            dl.SetWeightExpression(sig_train.weight.get_expr(), "Regression")

        # register variables
        for var in self.invars:
            var.tree_init(tsig)
            dl.AddVariable(var.get_expr(), var.xtitle, var.xunit or "", var.get_type().upper())
        self.target.tree_init(tsig)
        dl.AddTarget(self.target.get_expr(), self.target.xtitle, self.target.xunit or "")

        # configure regressor / factory
        fout = TFile.Open(fname_plots, "RECREATE")
        f = TMVA.Factory(self.name, fout, factory_optstr)
        f.BookMethod(dl, mvatype, self.cname, alg_optstr)

        ## train this puppy
        f.TrainAllMethods()

        ## test this puppy
        f.TestAllMethods()

        ## evaluate this puppy
        f.EvaluateAllMethods()

        ## move outputs to workspace
        fout.Close()
        self.__finalize_training_outputs__(fname_model, [fname_plots])

        return True


#------------------------------------------------------------------------------=buf=
class XGBClassifier(AlgBase):
    """Interface for classifier training with XGBoost 
    
    The algorithm options (*algopts*) are passed to xgboost. 
    
    For a full set of BDT options see the 
    `XGBoost parameters <https://xgboost.readthedocs.io/en/latest//parameter.html>`_. 
    For details on the python API see
    `XGBoost Python API <https://xgboost.readthedocs.io/en/latest/python/python_api.html>`_. 
        
    Algorithm specific options:
         
    * *algopts['num_boost_round']* - is a particularly important option for XGBoost. 
      It specifies the number of iterations of additional boosting to be performed.
    * *algopts['early_stopping_rounds']* - if specified, testing data must be provided. 

    *wspath* and *info* are not to be set by the user (see :class:`~loki.train.alg.AlgBase`)  
    
    :param name: algorithm name
    :type name: str
    :param algopts: options passed to TMVA Classifier
    :type algopts: dict
    :param invars: input variables
    :type invars: list :class:`~loki.core.var.VarBase` subclass
    :param sig_train: signal training sample
    :type sig_train: :class:`~loki.core.sample.Sample`
    :param bkg_train: background training sample
    :type bkg_train: :class:`~loki.core.sample.Sample`
    :param sig_test: signal testing sample
    :type sig_test: :class:`~loki.core.sample.Sample`
    :param bkg_test: background testing sample
    :type bkg_test: :class:`~loki.core.sample.Sample`
    :param kw: key-word args passed to :class:`~loki.train.alg.AlgBase`    
    """
    #__________________________________________________________________________=buf=
    def __init__(self, name=None, wspath = None, info = None, 
                 algopts = None, invars = None,
                 sig_train = None, bkg_train = None, 
                 sig_test = None, bkg_test = None):    
        if name is None: name = "XGBDT"
        AlgBase.__init__(self, name=name, wspath=wspath, info=info, valtype='f')        
        
        # set defaults
        if algopts is None: algopts = dict() 
        if invars is None: invars = list()
        if sig_train is None: sig_train = Sample("sig_train", weight=vars.weight, files=[])
        if bkg_train is None: bkg_train = Sample("bkg_train", weight=vars.weight, files=[])
        if sig_test is None: sig_test = Sample("sig_test", weight=vars.weight, files=[])
        if bkg_test is None: bkg_test = Sample("bkg_test", weight=vars.weight, files=[])
        algopts.setdefault("num_boost_round", 100)
        algopts.setdefault("objective", "binary:logistic")
        algopts.setdefault("tree_method", "approx")
        algopts.setdefault("sketch_eps", 0.005)
        algopts.setdefault("eval_metric", ["auc", "rmse"])

        # process complex types (Sample done automatically)
        invars = get_variables(invars)
        
        # set attributes
        self.algopts = algopts
        self.invars = invars
        self.sig_train = sig_train
        self.bkg_train = bkg_train
        self.sig_test = sig_test
        self.bkg_test = bkg_test
        
        # members
        self.cname = "classifier"

    #__________________________________________________________________________=buf=
    def __subclass_train__(self):
        """Train the classifier"""
        ## configuration
        fname_model     = f"{self.name}.model"
        algopts         = dict(self.algopts)
        num_boost_round = algopts.pop("num_boost_round", None)
        early_stopping_rounds = algopts.pop("early_stopping_rounds", None)

        # pre-train checks
        if not self.ispersistified(): 
            log().error("XGBClassifier must be persistified before training (call 'saveas')")
            return False
        if not self.invars: 
            log().error("No input vars defined, cannot train!")
            return False
        if not pkgutil.find_loader("xgboost"):
            log().error("Cannot use XGBClassifier without xgboost lib. Try source setup_dev.sh")
            return False
        if early_stopping_rounds is not None:
            early_stopping_rounds = int(early_stopping_rounds)
            if not (self.sig_test.files and self.bkg_test.files): 
                log().warn("Early stopping requires testing samples!")
 
        # get samples with abspath
        sig_train = self.__get_sample_worker__(self.sig_train)
        bkg_train = self.__get_sample_worker__(self.bkg_train)
        sig_test = self.__get_sample_worker__(self.sig_test) if self.sig_test.files else None
        bkg_test = self.__get_sample_worker__(self.bkg_test) if self.bkg_test.files else None
        samples = [s for s in [sig_train, bkg_train, sig_test, bkg_test] if s is not None]
        if False in [self.__check_sample__(s) for s in samples]: return False

        # format trees into arrays
        log().info("Preparing input data...")
        dtrain = samples2dmatrix(sig_train, bkg_train, self.invars)
        if sig_test and bkg_test:
            dtest = samples2dmatrix(sig_test, bkg_test, self.invars)
            watchlist = [(dtrain, "train"), (dtest, "test")]
        else:
            watchlist = [(dtrain, "train")]
        
        # train
        log().info("Starting xgboost train...")
        import xgboost
        bst = xgboost.train(algopts, dtrain, num_boost_round, watchlist, 
                            early_stopping_rounds = early_stopping_rounds)

        # write output
        if os.path.exists(fname_model):
            log().warn(f"Overwriting existing model file: {fname_model}")
        bst.save_model(fname_model)
        
        ## move outputs to workspace
        self.__finalize_training_outputs__(fname_model, None)

        return True

    #__________________________________________________________________________=buf=
    def __subclass_predict__(self, s, it=None, itfrac=None):
        """Sub-class specific prediction implementation 
                 
        :param it: boost iteration to use
        :type it: int
        :param itfrac: boost iteration to use, as fraction of max iteration
        :type itfrac: float
        """
        fmodel = self.__get_fmodel_path__()
        
        # checks
        if not pkgutil.find_loader("xgboost"):
            log().error("Cannot use XGBClassifier without xgboost lib. Try source setup_dev.sh")
            return None        
        if not fmodel: 
            log().error("No model file, cannot predict")
            return None        
        if not s: 
            log().error("No input sample, cannot predict")
            return None
        
        import xgboost
        import numpy as np
        # prepare data
        inputs = s.get_ndarray(invars=self.invars, noweight=True)
        # Cast structured array to only contain float32 fields
        dtype = [(fname, np.float32) for fname, ftype in inputs.dtype.descr]
        inputs = inputs.astype(dtype, copy=False)
        # Reshape structured array to ndarray
        reshaped = inputs.view(np.float32).reshape(inputs.shape + (-1,))
        dmatrix = xgboost.DMatrix(reshaped)

        # prepare bdt
        bst = xgboost.Booster(model_file=fmodel)
        
        # get boost iteration number
        boost_it = None
        if it is not None: 
            boost_it = it
        elif itfrac is not None: 
            best_it = bst.attr("best_iteration") or self.algopts["num_boost_round"] 
            boost_it = int(float(itfrac) * float(best_it))

        # predict    
        if boost_it is not None: 
            output = bst.predict(dmatrix, ntree_limit=boost_it)
        else:         
            output = bst.predict(dmatrix)        

        # convert back to standard python array
        """tree2array gives you a strucutred array which is analogous to a array 
        of c-structs meaning effectivey your shape is (number of events, 1)
        but the tmva thing wants (number of events, number of variables)"
        http://stackoverflow.com/questions/5957380/convert-structured-array-to-regular-numpy-array"""
        from loki.core.process import ndarray2array
        output = ndarray2array(output)
        return output

    #__________________________________________________________________________=buf=
    def get_var_name(self, it=None, itfrac=None):
        """Return unique var name based on kw args passed to the predict method"""
        name = str(self.name)
        if it is not None: 
            name += f"i{it:d}"
        elif itfrac is not None: 
            name += "f{:02d}".format(int(float(itfrac) * 100.))
        return name


#------------------------------------------------------------------------------=buf=
class MVScoreTuner(AlgBase):
    """Working point tuner and score flattener 
    
    The train method extracts fixed efficiency working points for the specified 
    discriminant (*disc*). The efficiency can be flattened against up to 2 
    auxiliary variables (*xvar* and *yvar*). After training, the pass/fail 
    decisions of the working points can be predicted by passing the *eff* 
    argument to the predict function, or the working points can be used to 
    predict a 'flattened discriminant' which is transformed to have a uniform 
    distribution on [0,1].
    
    Cut extraction (training): 
    
    The cuts to apply to the discriminant are extracted as a 1D or 2D 
    parameterization against the dependent var(s). For each target efficiency 
    ranging from 1-99%, a graph and a histogram parameterization are saved to 
    the model file.
        
    If you want to extend a 1D parameterization to a 2D parameterization
    using dummy values for the second variable, the extremes in the 
    second variable can be provided by *yvals2d*. 
    
    If the cut should be applied in reverse (ie. cut < disc), set 
    *reverse=True*.  
    

    Working point prediction: 

    To predict pass/fail decisions for a flattened working point, passt the *eff* 
    argument to the predict method (must be an integer in the range [1,99]). 


    Flat score prediction: 
    
    By default, the predict function returns a flattened discriminant, transformed 
    to be uniform on [0,1].

    *wspath* and *info* are not to be set by the user (see :class:`~loki.train.alg.AlgBase`)  
    
    :param name: algorithm name
    :type name: str
    :param disc: discriminant 
    :type disc: :class:`~loki.core.var.View`
    :param xvar: first dependent variable 
    :type xvar: :class:`~loki.core.var.View`
    :param yvar: second dependent variable 
    :type yvar: :class:`~loki.core.var.View`
    :param reverse: apply the mv score cut in reverse
    :type reverse: bool
    :param smooth: smoothing option, currently only valid for 2D (eg. k3a, k5a, k5b ) 
    :type smooth: str
    :param usehist: set False to use graph-based cut parameterisation (NOT recommended, as it returns 0 outside the graph boundary)  
    :type usehist: bool
    :param yvals2d: list of dummy values to extend 1D parameterization to 2D
    :type yvals2d: tuple (float, float)
    :param sig_train: signal training sample
    :type sig_train: :class:`~loki.core.sample.Sample`
    :param kw: key-word args passed to :class:`~loki.train.alg.AlgBase`    
    """
    #__________________________________________________________________________=buf=
    def __init__(self, name=None, wspath = None, info = None, 
                 sig_train = None, disc = None, xvar = None, yvar = None, 
                 reverse = None, smooth = None, usehist = None, yvals2d = None):    
        if name is None: name = "MVScoreTuner"
        AlgBase.__init__(self, name=name, wspath=wspath, info=info, valtype='f')
        
        # set defaults
        if sig_train is None: sig_train = Sample("sig_train", weight=vars.weight, files=[])
        if usehist is None: usehist = True
        
        # process complex types (Sample done automatically)
        disc = get_view(disc)
        xvar = get_view(xvar)
        if yvar: yvar = get_view(yvar)
        if reverse is None: reverse = False

        # set attributes
        self.sig_train = sig_train
        self.disc = disc
        self.xvar = xvar
        self.yvar = yvar
        self.reverse = reverse
        self.smooth = smooth
        self.usehist = usehist
        self.yvals2d = yvals2d        
        
    # Subclass overrides
    #__________________________________________________________________________=buf=
    def __subclass_train__(self):
        """Train the classifier"""
        # config
        fname_model = "model.root"
        reverse = self.reverse
        disc = self.disc
        xvar = self.xvar
        yvar = self.yvar
        smooth1D = smooth2D = None
        if self.smooth: 
            if yvar: smooth2D = self.smooth
            else:    smooth1D = self.smooth

        # pre-train checks
        if not self.ispersistified(): 
            log().error("MVScoreTuner must be persistified before training (call 'saveas')")
            return False        
        if not disc:
            log().error("No disc view configured")
            return False 
        if not xvar: 
            log().error("No xvar view configured")
            return False 

        # get samples with abspath
        s = self.__get_sample_worker__(self.sig_train)
        if not self.__check_sample__(s): return False

        # define working point extractor
        wpe = WorkingPointExtractor(s, disc=disc, xvar=xvar, yvar=yvar, 
              reverse=reverse, smooth1D=smooth1D, smooth2D=smooth2D)

        # process
        from loki.core.process import Processor
        p = Processor(ncores=1)
        p.process(wpe)
        p.draw_plots()
    
        from loki.core.file import OutputFileStream 
        ofstream = OutputFileStream(fname_model)
        ofstream.write(wpe)
        ofstream.f.Close()
        
        ## move outputs to workspace
        self.__finalize_training_outputs__(fname_model, None)

        return True

    #__________________________________________________________________________=buf=
    def __subclass_predict__(self, s, eff=None):
        """Sub-class specific prediction implementation
                
        :param eff: working point efficiency in percentage 
        :type eff: int
        """
        fmodel = self.__get_fmodel_path__()
        disc = self.disc.var
        xvar = self.xvar.var
        yvar = self.yvar.var if self.yvar else None
        usehist = self.usehist
        
        # checks 
        if not fmodel: 
            log().error("No model file, cannot predict")
            return None
        if not s: 
            log().error("No input sample, cannot predict")
            return None
        if not s.files: 
            log().error("No input files, cannot predict")
            return None
        if not disc:
            log().error("No disc view configured, cannot predict")
            return None 
        if not xvar: 
            log().error("No xvar view configured, cannot predict")
            return None 
                
        # retrieve graph / hist        
        f = TFile.Open(fmodel)
        if not f: 
            log().error(f"Error opening config file {fmodel}.")
            return None
        graphs = []
        gname = "h" if usehist else "g"
        if yvar: gname+="2"
        gname += "_{0:02d}"        
        for i in range(0,100):
            gname_temp = gname.format(i)
            g = f.Get(gname_temp)
            if not g: 
                log().debug(f"Failed to retrieve graph {gname_tmep} from config file {self.fconfig}")
                continue
            g = g.Clone()
            if usehist or isinstance(g, TGraph2D): 
                g.SetDirectory(0)
            graphs += [(float(i)/100., g)]
        f.Close()

        # get x-y limits
        if usehist: 
            xlims = (min([g.GetXaxis().GetXmin() for (i,g) in graphs]), 
                     max([g.GetXaxis().GetBinCenter(g.GetNbinsX()) for (i,g) in graphs]))
        else: 
            xlims = (min([g.GetXaxis().GetXmin() for (i,g) in graphs]), 
                     max([g.GetXaxis().GetXmax() for (i,g) in graphs]))
        if yvar:
            if usehist: 
                ylims = (min([g.GetYaxis().GetXmin() for (i,g) in graphs]), 
                         max([g.GetYaxis().GetBinCenter(g.GetNbinsY()) for (i,g) in graphs]))
            else:      
                ylims = (min([g.GetYaxis().GetXmin() for (i,g) in graphs]), 
                         max([g.GetYaxis().GetXmax() for (i,g) in graphs]))        


        # python based predict        
        self.xlims = xlims
        if yvar: self.ylims = ylims
        if eff: 
            gname_temp = gname.format(int(eff))
            gscan = [g[1] for g in graphs if g[1].GetName() == gname_temp]
            if not gscan: 
                log().error(f"Couldn't find graph with name {gname_temp}")
                return None 
            self.g = gscan[0]
            self.__predict_single__ = self.__predict_single_eff__
            self.valtype = 'i'
        else:
            self.graphs = graphs
            self.__predict_single__ = self.__predict_single_score__
            self.valtype = 'f'
        
        # extract inputs
        if yvar: invars = [disc,xvar,yvar]
        else:    invars = [disc,xvar] 
        inputs = s.get_arrays(invars=invars, noweight=True)
        
        # predict output
        return self.__predict_python_loop__(inputs)

    #__________________________________________________________________________=buf=
    def get_var_name(self, eff=None):
        """Return unique var naem based on kw args passed to the predict method
        
        :param eff: working point efficiency in percentage 
        :type eff: int
        """
        name = str(self.name)
        if eff is None:
            name += "Score"
        else:
            name += f"Eff{int(eff):02d}"
        return name
    
    #__________________________________________________________________________=buf=
    def __predict_single_score__(self, invals):
        """Sub-class specific prediction implementation for flat score"""
        # pre-process values
        disc = invals[0] 
        x = min(self.xlims[1], max(self.xlims[0], invals[1]))
        if self.yvar: 
            y = min(self.ylims[1], max(self.ylims[0], invals[2]))
                
        # calculate flattened disc
        cut_lo = None
        eff_lo = None
        cut_hi = None
        eff_hi = None
        for (eff,g) in self.graphs:
            if self.yvar: 
                cut = g.Interpolate(x,y)
            else: 
                if self.usehist: cut = g.Inerpolate(x)
                else:            cut = g.Eval(x)
            if cut <= disc and ((not cut_lo) or abs(cut-disc) < abs(cut_lo-disc)): 
                eff_lo = eff
                cut_lo = cut
            elif cut > disc and ((not cut_hi) or abs(cut-disc) < abs(cut_hi-disc)):
                eff_hi = eff
                cut_hi = cut

            # early break if both lo/hi cuts found
            if cut_hi is not None and cut_lo is not None: break
            
        assert (cut_hi is not None or cut_lo is not None), "Must have at least upper or lower efficiency boundary!"
         
        ## default upper boundary    
        if cut_hi is None:  
            cut_hi = 1.1
            eff_hi = 0.0
        ## default lower boundary            
        if cut_lo is None: 
            cut_lo = -1.1 
            eff_lo = 1.0
            
        # disc higher than default upper boundary (rare)
        if disc > cut_hi:
            newdisc = cut_lo
        # disc lower than default lower boundary (rare)            
        elif disc < cut_lo:
            newdisc = cut_hi
        # disc inside boundaries            
        else:             
            newdisc = self.__transform__(disc, cut_lo, eff_lo, cut_hi, eff_hi)
            
        return newdisc

    #__________________________________________________________________________=buf=
    def __predict_single_eff__(self, invals):
        """Sub-class specific prediction implementation for working point"""                
        # pre-process values
        disc = invals[0] 
        x = min(self.xlims[1], max(self.xlims[0], invals[1]))
        if self.yvar: 
            y = min(self.ylims[1], max(self.ylims[0], invals[2]))
                
        # calculate cut decision
        if self.yvar:
            if self.usehist:
                cut = self.g.Interpolate(x,y)
            else: 
                cut = self.g.Interpolate(x,y)
        else: 
            if self.usehist: 
                cut = self.g.Interpolate(x)
            else: 
                cut = self.g.Eval(x)
        if self.reverse: 
            result = disc < cut
        else: 
            result = disc > cut

        return result
        
    #__________________________________________________________________________=buf=
    def __transform__(self, disc, cut_lo, eff_lo, cut_hi, eff_hi):
        """Interpolate discriminant between two efficiency boundaries"""
        newdisc = 1. - eff_lo - (disc - cut_lo)/(cut_hi - cut_lo) * (eff_hi - eff_lo)
        if self.reverse: newdisc = 1.0 - newdisc
        return newdisc



#------------------------------------------------------------------------------=buf=
class WorkingPointExtractor(RootDrawable):
    """Extracts fixed efficiency working point parameterisations 
    
    TODO: merge into MVScoreTuner
        
    The cuts to apply to the discriminant (*disc*) are extracted 
    as a 1D or 2D parameterization against the dependent var(s)
    *xvar* (and *yvar*). For each target efficiency in *target_effs*
    a graph and a histogram parameterization are saved to the 
    output file.
    
    A preselection (*sel*) can be specified. If a different 
    selection is required in the deominator used to define the
    efficiency (eg. if the efficiency should be calculated 
    w.r.t. truth taus), the corresponding selection (*sel_tot*) 
    and dependent vars (*xvar_tot*, *yvar_tot*) should be provided.  
    
    If you want to extend a 1D parameterization to a 2D parameterization
    using dummy values for the second variable, they extremes in the 
    second variable can be provided by *yvals2d*. 
    
    If the cut should be applied in reverse (ie. cut < disc), set 
    *reverse=True*.  
    
    
    Details below taken from Nico Madysa's original implementation: 
    
    
    Multivariate analysis (MVA) methods are used for classification of
    particles.
    They distinguish between charged tau leptons (signal or mc) and
    QCD jets (background or data).
    
    This distinction or, preferrably called, "classification" is done via
    a score.
    Each particle is given a score, rating how tau-like it is.
    The goal is to give high scores to tau leptons and low scores to
    QCD jets.
    
    In order to transition from continuous scores to discrete classes, we
    decide on a certain "score cut". The MVA considers particles with
    a score higher than this cut to be signal taus, and particles with
    a score lower than this cut to be background (or fake taus).
    
    Since we want to be able to adjust the signal efficiency
    (identified taus divided by all true taus), we have to calculate the
    correct score cut for each "working point".
    
    Our observation is that particles with a high transverse momentum pT are
    more likely to have a high score than those with low pT.
    For various reasons, this is undesirable.
    
    Thus, the score cut is a function not only of the signal efficiency,
    but also of pT.
    And we choose this score cut in such a manner, that, when applying it
    for a working point, the curve signal_efficiency(truth_pt) will be
    as flat as possible.
    
    
    :param sample: sample
    :type sample: :class:`~loki.core.sample.Sample`
    :param target_effs: list of target efficiencies
    :type target_eff: list float
    :param disc: discriminant variable view
    :type disc: :class:`~loki.core.var.View`
    :param xvar: first dependent variable view
    :type xvar: :class:`~loki.core.var.View`
    :param yvar: second dependent variable view
    :type yvar: :class:`~loki.core.var.View`
    :param sel: selection
    :type sel: :class:`~loki.core.var.VarBase`
    :param xvar_tot: denominator first dependent variable view
    :type xvar_tot: :class:`~loki.core.var.View`
    :param yvar_tot: denominator second dependent variable view
    :type yvar_tot: :class:`~loki.core.var.View`
    :param sel_tot: denominator selection
    :type sel_tot: :class:`~loki.core.var.VarBase`
    :param tag: tag to be included in output graph/histogram names
    :type tag: str
    :param yvals2d: list of dummy values to extend 1D parameterization to 2D
    :type yvals2d: list float
    :param reverse: apply cut in reverse (disc < cut)
    :type reverse: bool
    :param smooth1D: smoothing option when using 1 aux var (not currently implemented) 
    :type smooth: str    
    :param smooth2D: smoothing option when using 2 aux vars (eg. k3a, k5a, k5b ) 
    :type smooth: str

    """
    #__________________________________________________________________________=buf=
    def __init__(self,sample, target_effs=None, disc=None, xvar=None, yvar=None,  
                 sel=None, xvar_tot=None, yvar_tot=None, sel_tot=None, tag=None,
                 yvals2d=None, reverse=False, smooth1D=None, smooth2D=None):
        RootDrawable.__init__(self)
        # defaults
        if target_effs is None: target_effs = frange(0.00,1.00,0.01)
        # config
        self.target_effs = target_effs
        self.disc = disc
        self.xvar = xvar
        self.yvar = yvar
        self.tag = tag
        self.yvals2d = yvals2d
        self.reverse = reverse
        self.smooth1D = smooth1D
        self.smooth2D = smooth2D

        allowed_smooth1D = [None]
        assert smooth1D in allowed_smooth1D, f"smooth1D must be one of: {str(allowed_smooth1D)}"
        
        allowed_smooth2D = [None, "k3a", "k5a", "k5b"]
        assert smooth2D in allowed_smooth2D, f"smooth2D must be one of: {str(allowed_smooth2D)}"
        
        # hists
        hname = "h_wpextractor"
        if tag: hname += f"_{tag}"
        if yvar: # 2D dependence
            self.hist = Hist(sample=sample,xvar=xvar,yvar=yvar,zvar=disc,sel=sel,name=hname)
        else:    # 1D dependence
            self.hist = Hist(sample=sample,xvar=xvar,yvar=disc,sel=sel,name=hname)
        self.add_subrd(self.hist) 
        self.hist_tot = None
        if xvar_tot or yvar_tot or sel_tot:
            if yvar: 
                if None in [xvar_tot, yvar_tot, sel_tot]: 
                    log().warn("Must provide complete set of (xvar_tot, yvar_tot, sel_tot) to WorkingPointExtractor")
                else: 
                    self.hist_tot = Hist(sample=sample,xvar=xvar_tot,yvar=yvar_tot,sel=sel_tot,name=hname+"_tot")
                    self.add_subrd(self.hist_tot)
            else: 
                if None in [xvar_tot, sel_tot]: 
                    log().warn("Must provide complete set of (xvar_tot, sel_tot) to WorkingPointExtractor")
                else: 
                    self.hist_tot = Hist(sample=sample,xvar=xvar_tot,sel=sel_tot,name=hname+"_tot")
                    self.add_subrd(self.hist_tot)
        
        # memebers
        self._rootobjs = []

    #__________________________________________________________________________=buf=
    def build_rootobj(self):
        """Build the working point graphs"""
        
        ## input hists
        h = self.hist.rootobj()
        h_tot = None
        if self.hist_tot: h_tot = self.hist_tot.rootobj()

        ## create working point graphs/hists
        for te in self.target_effs:
            #g_cuts = self.__get_cut_graph__(h, te, h_total=h_tot)
            #h_cuts = self.__convert_cut_graph_to_hist__(g_cuts)
            h_cuts = self.__get_cut_hist__(h, te, h_total=h_tot)
            h_cuts.SetDirectory(0)
            self.__smooth_hist__(h_cuts)
            g_cuts = self.__convert_cut_hist_to_graph__(h_cuts)
            self._rootobjs.append(h_cuts)
            self._rootobjs.append(g_cuts)
            # create dummy 2D extension
            if not self.yvar and self.yvals2d is not None:
                hname2 = "h2"+str(g_cuts.GetName())[1:] 
                ybin_edges = []
                for i in range(len(self.yvals2d)-1):
                    y1 = self.yvals2d[i]
                    y2 = self.yvals2d[i+1] 
                    ybin_edges.append(y1 - (y2-y1)/2)
                ybin_edges.append(y1 + (y2-y1)/2)
                h2_cuts = convert_hist_to_2dhist(h_cuts,ybin_edges,name=hname2)
                h2_cuts.SetDirectory(0)
                self._rootobjs.append(h2_cuts)
                
                g2_cuts = self.__convert_cut_hist_to_graph__(h2_cuts) 
                self._rootobjs.append(g2_cuts)
            

    #__________________________________________________________________________=buf=
    def write(self,f):
        """Write ROOT objects to file
        
        Override baseclass function to write multiple objects
        
        :param f: file
        :type f: :class:`ROOT.TFile`
        """
        # write config
        disc = TNamed("disc", self.disc.var.get_newbranch())
        xvar = TNamed("xvar", self.xvar.var.get_newbranch())
        f.WriteTObject(disc)
        f.WriteTObject(xvar)
        if self.yvar: 
            yvar = TNamed("yvar", self.yvar.var.get_newbranch())
            f.WriteTObject(yvar)
        rev = TParameter(bool)("reverse",self.reverse)
        f.WriteTObject(rev)
        
        # write efficiency graphs
        for ro in self._rootobjs: 
            if not f.Get(ro.GetName()): 
                f.WriteTObject(ro)
                
        # write input hists
        for o in self._subrds: 
            o.write(f)

    # Internal functions
    #__________________________________________________________________________=buf=
    def __get_cuts__(self, h, target_eff, h_total=None):
        """Returns a list of tuples (*x*, *cut*)
        
        The tuples represent the bin centers in the dependent variable, *x*, 
        and the cut values, *cut*, required to reach the target efficiency, 
        *target_eff*.  
        
        If the efficiency should be calculated w.r.t. a different selection 
        than is applied in *h* (eg. if you want to calculate the efficiency 
        w.r.t truth) *h_total* can be specified, which is a 1D histogram 
        in the dependent variable.
          
        Uses :func:`__find_score_cut__`
        
        :param h: 2D hist of discriminant vs dependent variable
        :type h: :class:`ROOT.TH2`
        :param target_eff: target efficiency
        :type target_eff: float
        :param h_total: 1D hist of dependent variable before selection
        :type h_total: :class:`ROOT.TH1`
        :rtype: list of tuple (float, float)
        """
        min_cut = h.GetYaxis().GetBinLowEdge(1)
        cuts = []
        for i_bin in range(1,h.GetNbinsX()+1): 
            h_proj = h.ProjectionY("_py", i_bin,i_bin)
            # normalise
            if h_total: 
                ntot = h_total.GetBinContent(i_bin)
                if ntot: h_proj.Scale(1./ntot)
            else: 
                normalize(h_proj)    
            cut = self.__find_score_cut__(h_proj,target_eff)
            
            ## throw error if efficiency not reached
            if cut is False:
                xmin = h.GetXaxis().GetBinLowEdge(i_bin)
                xmax = h.GetXaxis().GetBinLowEdge(i_bin+1)
                # use previous cut
                if len(cuts): 
                    cut = cuts[-1][1]
                # use mincut                    
                else: 
                    cut = min_cut
                log().warn(f"Failed to reach target eff: {target_eff:.3f} for x-bin ({xmin},{xmax}), using cut: {cut}")
                #raise ValueError(f"Failed to reach target eff:{target_eff:.3f} for x-bin ({xmin},{xmax})!") 
                
            var = h.GetXaxis().GetBinCenter(i_bin)
            cuts.append([var,cut])
        return cuts

    #__________________________________________________________________________=buf=    
    def __find_score_cut__(self, h, target_eff):
        """Return discriminant score cut for target efficiency                 
        
        If target not reached 'False' is returned. 
        
        :param h: (normalized) 1D hist of discriminant
        :type h: :class:`ROOT.TH1`
        :param target_eff: target efficiency
        :type target_eff: float
        :rtype: float
        
        """
        # Code gets error-prone if the overflow bin contains enough events
        # to satisfy target efficiency.
        last_bin = h.GetNbinsX()+1
        if h.GetBinContent(last_bin) > target_eff:
            return False
            #raise ValueError("Overflow bin is too full")
        # Iterate over all bins.
        # Stop when we've met target efficiency.
        integral = 0.0
        if self.reverse: 
            for i_bin in range(last_bin+1):
                integral += h.GetBinContent(i_bin)
                # restrict precision in comparison to avoid floating point problems on 100%
                if float(f"{integral:.3f}")>=float(f"{target_eff:.3f}"):
                    return h.GetBinLowEdge(i_bin+1)            
        else: 
            for i_bin in reversed(range(last_bin+1)):
                integral += h.GetBinContent(i_bin)
                # restrict precision in comparison to avoid floating point problems on 100%
                if float(f"{integral:.3f}")>=float(f"{target_eff:.3f}"):
                    return h.GetBinLowEdge(i_bin)
        
        return False
        #raise ValueError("Not all target efficiencies reached")

    #__________________________________________________________________________=buf=
    def __get_cut_hist_1D__(self, h, target_eff, h_total=None):
        """Return a 1D hist parameterizing the cut values against xvar. 
        
        See :func:`__get_cuts__` for arg details
        
        :rtype: :class:`ROOT.TH1`
        """
        if self.tag: hname = f"h_{self.tag}_{target_eff*100.0:02.0f}"
        else:        hname = f"h_{target_eff*100.0:02.0f}"
        cuts = self.__get_cuts__(h,target_eff,h_total)
        hnew = h.ProjectionX(hname)
        hnew.Reset()
        for i in range(len(cuts)): 
            hnew.SetBinContent(i+1, cuts[i][1])
            hnew.SetBinError(i+1,0)
        return hnew

    #__________________________________________________________________________=buf=
    def __get_cut_hist_2D__(self, h, target_eff, h_total=None):
        """Return a 2D hist parameterizing the cut value against xvar, yvar.
        
        See :func:`__get_cuts__` for arg details
        
        :rtype: :class:`ROOT.TH2`
        """
        if self.tag:
            hname = f"h2_{self.tag}_{target_eff*100.0:02.0f}"
        else:
            hname = f"h2_{target_eff*100.0:02.0f}"
        hnew = h.Project3D("yx")
        hnew.Reset()
        hnew.SetName(hname)
        #print "bins x: ", hnew.GetNbinsX(), ", binsy: ", hnew.GetNbinsY()
        
        # loop over y-bins and project xz
        for iy in range(1, h.GetNbinsY()+1):
            log().debug(f"Projecting y-bin {iy:d}: [{h.GetYaxis().GetBinLowEdge(iy):f}, {h.GetYaxis().GetBinLowEdge(iy+1):f}]")
            h.GetYaxis().SetRange(iy,iy)
            htemp = h.Project3D("zx")
            h.GetYaxis().SetRange() #reset range
            if h_total: 
                pname = f"{h_total.GetName()}_x{iy:d}"
                htemp_total = h_total.ProjectionX(pname, iy, iy)
            else: htemp_total = None
            cuts = self.__get_cuts__(htemp,target_eff,htemp_total)
            for ix in range(1, h.GetNbinsX()+1): 
                hnew.SetBinContent(ix, iy, cuts[ix-1][1])
            
        return hnew

    #__________________________________________________________________________=buf=
    def __get_cut_hist__(self, h, target_eff, h_total=None):
        """Return a hist parameterizing cut values against the dependent variable(s)

        See :func:`__get_cuts__` for arg details
        
        :rtype: :class:`ROOT.TH1` or :class:`ROOT.TH2`
        """        
        if self.yvar: 
            return self.__get_cut_hist_2D__(h, target_eff, h_total=h_total)
        else: 
            return self.__get_cut_hist_1D__(h, target_eff, h_total=h_total)
    
    #__________________________________________________________________________=buf=    
    def __convert_cut_graph_to_hist__(self, g):
        """Convert graph cut parameterization to hist parameterization"""
        if isinstance(g,TGraph2D): 
            h = self.xvar.new_hist(yvar=self.yvar, name = 'h' + str(g.GetName())[1:])
            for i in range(1,h.GetNbinsX()+1):
                x = h.GetXaxis().GetBinCenter(i) 
                for j in range(1,h.GetNbinsY()+1): 
                    y = h.GetYaxis().GetBinCenter(j)
                    h.SetBinContent(i,j,g.Interpolate(x,y))
        else: 
            h = self.xvar.new_hist(name = 'h' + str(g.GetName())[1:])
            for i in range(1,h.GetNbinsX()+1):
                x = h.GetXaxis().GetBinCenter(i) 
                h.SetBinContent(i,g.Eval(x))
        return h

    #__________________________________________________________________________=buf=    
    def __convert_cut_hist_to_graph__(self, h):
        """Convert graph cut parameterization to hist parameterization"""
        if isinstance(h,TH2): g = TGraph2D(h)
        else:                      g = TGraph(h)
        g.SetName('g' + str(h.GetName())[1:])
        return g

    #__________________________________________________________________________=buf=    
    def __smooth_hist__(self, h):
        """Convert graph cut parameterization to hist parameterization"""
        if self.yvar and self.smooth2D: 
            h.Smooth(1, self.smooth2D)
        elif self.smooth1D:
            log().warn("Smoothing for 1D hists not yet implemented")       


#------------------------------------------------------------------------------=buf=
class Reweighter(AlgBase):
    """Calculate distribution-based reweight from reference (*ref*) to 
    target (*tar*) sample.
    
    This algorithm does not need to be persistified to train. Also, 
    the predict method can be called directly and the train will be 
    initiated if not already called.     

    The result can be multiplied by an existing weight variable (*prodvar*), 
    eg. if you want to update a generic weight branch. 
 
    *wspath* and *info* are not to be set by the user (see :class:`~loki.train.alg.AlgBase`)  
    
    :param name: algorithm name
    :type name: str
    :param var: reweight variable 
    :type var: :class:`~loki.core.var.View`
    :param prodvar:  existing weight variable to multiply to reweight
    :type prodvar: :class:`~loki.core.var.VarBase` subclass
    :param tar: target sample
    :type tar: :class:`~loki.core.sample.Sample`
    :param ref: refecence sample
    :type ref: :class:`~loki.core.sample.Sample`
    :param kw: key-word args passed to :class:`~loki.train.alg.AlgBase`    
    """
    #__________________________________________________________________________=buf=
    def __init__(self, name=None, wspath = None, info = None, 
                 var = None, prodvar = None, tar = None, ref = None):
        if name is None: name = "Reweighter"
        AlgBase.__init__(self, name=name, wspath=wspath, info=info, valtype='f')
        
        # set defaults
        if var is None: var = vars.taus.ptGeV.get_view("weight")
        if tar is None: tar = Sample("tar", weight=vars.weight, files=[])
        if ref is None: ref = Sample("ref", weight=vars.weight, files=[])
        
        # process complex types (Sample done automatically)
        var = find_view(var)
        prodvar = get_variable(prodvar)
        
        # set attributes
        self.var = var
        self.prodvar = prodvar
        self.tar = tar
        self.ref = ref
        
        # private members
        self.g = None

    #__________________________________________________________________________=buf=
    def __subclass_train__(self):
        """Train the classifier"""
        fname_model = "Weighter.root"
        var = self.var

        # pre-train checks
        if not var: 
            log().error("Input var not defined, cannot train!")
            return False

        # get samples with abspath
        tar = self.__get_sample_worker__(self.tar)
        ref = self.__get_sample_worker__(self.ref)
        samples = [s for s in [tar, ref] if s is not None]
        if False in [self.__check_sample__(s) for s in samples]: return False


        # get ratio hist
        from loki.core.hist import Ratio
        h_tar = Hist(sample=tar, xvar=var, name = "h_tar")
        h_ref = Hist(sample=ref, xvar=var, name = "h_ref")
        g_ratio = Ratio(h_ref,h_tar,owner=True, name="g_ratio")
        from loki.core.process import Processor
        p = Processor(ncores=1)
        p.process(g_ratio)
        self.g = g_ratio.rootobj()
    
        # persistify    
        if self.ispersistified(): 
            from loki.core.file import OutputFileStream 
            ofstream = OutputFileStream(fname_model)
            ofstream.write(g_ratio)
            self.__finalize_training_outputs__(fname_model, None)
        
        return True
    
    #__________________________________________________________________________=buf=
    def __subclass_predict__(self, s):
        """Initialize calculator to work on *tree*"""
        if not self.g:
            fmodel = self.__get_fmodel_path__()
            try: 
                f = TFile.Open(fmodel)
                g = f.Get("g_ratio")
                assert g
                self.g = g
            except:
                log().info("Auto train for predict")
                self.train()
                
        if not self.g: 
            log().error("Failure ")
            return None

        # prepare input range
        self.xmin = min([self.g.GetX()[i] for i in range(self.g.GetN())])
        self.xmax = max([self.g.GetX()[i] for i in range(self.g.GetN())])

        if self.prodvar: invars = [self.var.var, self.prodvar]
        else:            invars = [self.var.var] 
        inputs = s.get_arrays(invars=invars, noweight=True)
        
        return self.__predict_python_loop__(inputs)
        
    #__________________________________________________________________________=buf=
    def __predict_single__(self, invals):
        """Evaluate based on the input values (*invals*)"""
        x = max(self.xmin, min(self.xmax, invals[0])) # force x value into range
        w = self.g.Eval(x)
        if len(invals)>1: w*=invals[1]
        return w

# ------------------------------------------------------------------------------=buf=
class Random(AlgBase):
    """Testing alg - just returns random value uniform on [0,1)

    :param name: algorithm name
    :type name: str
    :param kw: key-word args passed to :class:`~loki.train.alg.AlgBase`
    """

    # __________________________________________________________________________=buf=
    def __init__(self, name=None, wspath=None, info=None):
        if name is None: name = "Random"
        AlgBase.__init__(self, name=name, wspath=wspath, info=info, valtype='f')

    # __________________________________________________________________________=buf=
    def __subclass_train__(self):
        """Train the classifier"""
        log().info("Doesn't need train")

    # __________________________________________________________________________=buf=
    def __subclass_predict__(self, s):
        """Initialize calculator to work on *tree*"""
        n = s.get_nevents()
        inputs = [["dummy", [0]*n]]
        return self.__predict_python_loop__(inputs)

    # __________________________________________________________________________=buf=
    def __predict_single__(self, invals):
        """Evaluate based on the input values (*invals*)"""
        return random.random()

## EOF
