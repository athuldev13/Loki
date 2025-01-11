/**
 * LokiSelector.h
 * ~~~~~~~~~~~~~~
 * Implements LokiSelector.
 *
 * The LokiSelector is designed to process a TTree
 * from a single input file, filling a set of user
 * defined histograms. The histograms are added to
 * the selector via the AddHist function in the
 * form of the LokiHist1D/2D/3D classes. The
 * histograms are saved to an output file
 * (*fout_name*) whose name is passed to the
 * selector constructor.
 *
 * The hists use the TTreeFormula functionality
 * to calculate their axis variables, selection
 * and weights. The selector collects the
 * formulas, removes duplicates, and uses the
 * TTreeFormulaManager to sync the formulae so
 * that they all return the same number of values
 * per event. Because of this, the variables
 * used to define the formulae in the selector
 * should not come from more than one multi-valued
 * container. Eg. you can plot TauJets.pt
 * (multi-valued) vs EventInfo.mu (single-valued),
 * in which case the mu values will be replicated
 * for each tau candidate. However, you cannot
 * plot TauJets.pt (multi-valued) vs TrueTaus.pt
 * (multi-valued) since the two containers are
 * not guaranteed to have the same length, and
 * the behavior of the syncing is not well defined.
 *
 * Currently the selector can only be used to process
 * a single TTree in local mode.
 *
 * Does not work with TChain because the underlying
 * TTreeFormula's need to be updated when switching to
 * the next file in the chain, however, ROOT only calls the
 * Notify() function on tree update, which does not
 * actually provide access to the TTree, furthermore,
 * the fChain variable is forced to be a null pointer
 * in this method (go figure).
 *
 * Does not work with PROOF, not exactly sure why,
 * but returns status code -1.
 *
 *
 * Author    : "Will Davey"
 * Email     : "will.davey@cern.ch"
 * Created   : 2017-02-22
 * Copyright : "Copyright 2016 Will Davey"
 * License   : "GPL http://www.gnu.org/licenses/gpl.html"
 */

//////////////////////////////////////////////////////////
// This class has been automatically generated on
// Thu Feb 16 08:26:15 2017 by ROOT version 6.06/02
// from TTree CollectionTree/xAOD event tree
// found on file: user.wdavey.10675614._000015.output.root
//////////////////////////////////////////////////////////

#ifndef LokiSelector_h
#define LokiSelector_h

#include <TROOT.h>
#include <TChain.h>
#include <TFile.h>
#include <TSelector.h>
#include <TTreeFormula.h>
#include <TTreeFormulaManager.h>
#include "LokiHist.h"
#include <vector>



class LokiSelector : public TSelector {
public :
  TTree       *fChain = 0;  //!pointer to the analyzed TTree or TChain
  TTreeFormulaManager* manager = 0; //!
  std::string fout_name;

  LokiSelector(TTree * /*tree*/ =0)
    : fout_name("temp.root")
  { }
  LokiSelector(std::string fout_name)
    : fout_name(fout_name)
  { }
  virtual ~LokiSelector() { }
  virtual Int_t  Version() const { return 2; }
  virtual void   Begin(TTree *tree);
  virtual void   SlaveBegin(TTree *tree);
  virtual void   Init(TTree *tree);
  virtual Bool_t  Notify();
  virtual Bool_t  Process(Long64_t entry);
  virtual Int_t  GetEntry(Long64_t entry, Int_t getall = 0) 
  { 
    return fChain ? fChain->GetTree()->GetEntry(entry, getall) : 0; 
  }
  virtual void   SetOption(const char *option) { fOption = option; }
  virtual void   SetObject(TObject *obj) { fObject = obj; }
  virtual void   SetInputList(TList *input) { fInput = input; }
  virtual TList  *GetOutputList() const { return fOutput; }
  virtual void   SlaveTerminate();
  virtual void   Terminate();
  
  void AddHist(LokiHist1D* h); 
  void AddHist(LokiHist2D* h); 
  void AddHist(LokiHist3D* h); 

  std::vector<LokiHist1D*> hists1D; //!
  std::vector<LokiHist2D*> hists2D; //!
  std::vector<LokiHist3D*> hists3D; //!
  std::map<std::string, TTreeFormula*> fmap; //!
  bool fIsInit = false; //!

private: 
  TTreeFormula* GetFormula(std::string name, TTree* tree);


  ClassDef(LokiSelector,1);

};

#endif

#ifdef LokiSelector_cxx
ClassImp(LokiSelector)
TTreeFormula* LokiSelector::GetFormula(std::string name, TTree* tree)
{
  if( name == "" ) return 0;
  // add to map if not present
  if( fmap.find(name) == fmap.end() ){
    fmap.insert(std::pair<std::string,TTreeFormula*>(
      name, new TTreeFormula(name.c_str(), name.c_str(), tree)));
  }
  // update tree if already exists
  else{
    //fmap[name]->SetTree(tree);
  }
  return fmap[name];
}
void LokiSelector::Init(TTree *tree)
{
  // The Init() function is called when the selector needs to initialize
  // a new tree or chain. Typically here the reader is initialized.
  // It is normally not necessary to make changes to the generated
  // code, but the routine can be extended by the user if needed.
  // Init() will be called many times when running on PROOF
  // (once per file to be processed).

  //if( fIsInit ) return;
  for( auto kv : fmap ){
	  delete kv.second;
  }
  fmap.clear();
  //if( manager ) delete manager;

  manager = new TTreeFormulaManager();

  // load histogram formulae
  for ( LokiHist1D* h : hists1D ){
    h->fx = GetFormula(h->xvar, tree);
    h->fsel = GetFormula(h->sel, tree);
    h->fwei = GetFormula(h->wei, tree);
  }
  for ( LokiHist2D* h : hists2D ){
    h->fx = GetFormula(h->xvar, tree);
    h->fy = GetFormula(h->yvar, tree);
    h->fsel = GetFormula(h->sel, tree);
    h->fwei = GetFormula(h->wei, tree);
  }
  for ( LokiHist3D* h : hists3D ){
    h->fx = GetFormula(h->xvar, tree);
    h->fy = GetFormula(h->yvar, tree);
    h->fz = GetFormula(h->zvar, tree);
    h->fsel = GetFormula(h->sel, tree);
    h->fwei = GetFormula(h->wei, tree);
  }
 
  // load formulae into manager and switch off non-used branches
  // 25.05.21 mmlynari temporary workaround to read Aux and AuxDyn
/*
  tree->SetBranchStatus("*", 0);
  for( auto& kv : fmap ){
    manager->Add(kv.second);
    // get set of all input branches
    for(int i=0; i<kv.second->GetNcodes(); i++){
      kv.second->GetLeaf(i)->GetBranch()->SetStatus(1);
    } 
  }
*/
  // sync the formulae so that all have the same number of entries per event 
  manager->Sync();

  //fIsInit = true;
}

Bool_t LokiSelector::Notify()
{
  // The Notify() function is called when a new file is opened. This
  // can be either for a new TTree in a TChain or when when a new TTree
  // is started when using PROOF. It is normally not necessary to make changes
  // to the generated code, but the routine can be extended by the
  // user if needed. The return value is currently not used.

  return kTRUE;
}


#endif // #ifdef LokiSelector_cxx
