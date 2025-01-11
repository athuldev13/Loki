#define LokiSelector_cxx
// The class definition in LokiSelector.h has been generated automatically
// by the ROOT utility TTree::MakeSelector(). This class is derived
// from the ROOT class TSelector. For more information on the TSelector
// framework see $ROOTSYS/README/README.SELECTOR or the ROOT User Manual.


// The following methods are defined in this file:
//   Begin():      called every time a loop on the tree starts,
//              a convenient place to create your histograms.
//   SlaveBegin():  called after Begin(), when on PROOF called only on the
//              slave servers.
//   Process():    called for each event, in this function you decide what
//              to read and fill your histograms.
//   SlaveTerminate: called at the end of the loop on the tree, when on PROOF
//              called only on the slave servers.
//   Terminate():   called at the end of the loop on the tree,
//              a convenient place to draw/fit your histograms.
//
// To use this file, try the following session on your Tree T:
//
// root> T->Process("LokiSelector.C")
// root> T->Process("LokiSelector.C","some options")
// root> T->Process("LokiSelector.C+")
//


#include "LokiSelector.h"
#include <TH2.h>
#include <TStyle.h>
#include <TH1F.h>
#include <TH2F.h>
#include <TH3F.h>
//#include <iostream>

void LokiSelector::AddHist(LokiHist1D* h)
{
  hists1D.push_back(h); 
}

void LokiSelector::AddHist(LokiHist2D* h)
{
  hists2D.push_back(h); 
}

void LokiSelector::AddHist(LokiHist3D* h)
{
  hists3D.push_back(h); 
}

void LokiSelector::Begin(TTree * /*tree*/)
{
  // The Begin() function is called at the start of the query.
  // When running with PROOF Begin() is only called on the client.
  // The tree argument is deprecated (on PROOF 0 is passed).

  TString option = GetOption();

  // Add LokiHists to inputs to stream to worker nodes
  TList* inputs = new TList();
  for ( LokiHist1D* h : hists1D ) inputs->Add(h);
  for ( LokiHist2D* h : hists2D ) inputs->Add(h);
  for ( LokiHist3D* h : hists3D ) inputs->Add(h);
  SetInputList(inputs);

}

void LokiSelector::SlaveBegin(TTree * /*tree*/)
{
  // The SlaveBegin() function is called after the Begin() function.
  // When running with PROOF SlaveBegin() is called on each slave server.
  // The tree argument is deprecated (on PROOF 0 is passed).

  //TString option = GetOption();
  fIsInit = false;

  //std::cout << "In SlaveBegin" << std::endl;
  // rebuild hists from streamed inputs (for PROOF worker nodes)
  hists1D.clear();
  hists2D.clear();
  hists3D.clear();
  fmap.clear();
  TIter next(fInput);
  while(TObject* o = next() ){
	  if     ( o->IsA() == LokiHist1D::Class() ) hists1D.push_back( (LokiHist1D*)o);
	  else if( o->IsA() == LokiHist2D::Class() ) hists2D.push_back( (LokiHist2D*)o);
	  else if( o->IsA() == LokiHist3D::Class() ) hists3D.push_back( (LokiHist3D*)o);
  }

  // Initialize hists
  //manager = new TTreeFormulaManager();
  for ( LokiHist1D* h : hists1D ){
    h->Init();
    fOutput->Add(h->h);
  }
  for ( LokiHist2D* h : hists2D ){
    h->Init();
    fOutput->Add(h->h);
  }
  for ( LokiHist3D* h : hists3D ){
    h->Init();
    fOutput->Add(h->h);
  }
}

Bool_t LokiSelector::Process(Long64_t entry)
{
  // The Process() function is called for each entry in the tree (or possibly
  // keyed object in the case of PROOF) to be processed. The entry argument
  // specifies which entry in the currently loaded tree is to be processed.
  // When processing keyed objects with PROOF, the object is already loaded
  // and is available via the fObject pointer.
  //
  // This function should contain the \"body\" of the analysis. It can contain
  // simple or elaborate selection criteria, run algorithms on the data
  // of the event and typically fill histograms.
  //
  // The processing can be stopped by calling Abort().
  //
  // Use fStatus to set the return value of TTree::Process().
  //
  // The return value is currently not used.

  //fReader.SetEntry(entry);

  GetEntry(entry);
  size_t n = manager->GetNdata();
  for( auto h : hists1D ) h->Fill(n);
  for( auto h : hists2D ) h->Fill(n);
  for( auto h : hists3D ) h->Fill(n);

  return kTRUE;
}

void LokiSelector::SlaveTerminate()
{
  // The SlaveTerminate() function is called after all entries or objects
  // have been processed. When running with PROOF SlaveTerminate() is called
  // on each slave server.

}

void LokiSelector::Terminate()
{
  // The Terminate() function is the last function to be called during
  // a query. It always runs on the client, it can be used to present
  // the results graphically or save the results to file.

  //std::cout << "fname_out: " << fout_name << std::endl;
  TFile* fout = TFile::Open(fout_name.c_str(), "RECREATE");
  TIter next(fOutput);
  while(TObject* o = next() ) {
      if(o->InheritsFrom(TH1::Class()))
    	  fout->WriteTObject(o);
  }
  fout->Close();

}
