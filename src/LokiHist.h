/**
 * LokiHist.h
 * ~~~~~~~~~~
 * Implements LokiHist1D, LokiHist2D and LokiHist3D.
 *
 * These classes contain the basic attributes needed
 * to define 1D, 2D and 3D histograms, using TTree::Draw
 * like expressions for the axis variables, selection
 * and weight. The TTreeFormula class is used to
 * evaluate the draw expressions. Bins are provided as
 * vectors. Objects of these classes are passed to a
 * LokiSelector, which can be used to process a TTree.
 * After processing, the corresponding ROOT object
 * (TH1F/2F/3F) is written to an output file with the
 * name specified by the LokiHist 'hash' variable.
 *
 * The Init() functions create the underlying ROOT object
 * according to the binning definition.
 *
 * The Fill(size_t n) functions fill the histogram with
 * the first 'n' values returned by the underlying
 * TTreeFormula
 *
 * Author    : "Will Davey"
 * Email     : "will.davey@cern.ch"
 * Created   : 2017-02-22
 * Copyright : "Copyright 2016 Will Davey"
 * License   : "GPL http://www.gnu.org/licenses/gpl.html"
 */
#ifndef LokiHist_h
#define LokiHist_h

#include <TObject.h>
#include <TH1.h>
#include <TH2.h>
#include <TH3.h>
#include <TTreeFormula.h>
#include <vector>
#include <string>

class LokiHist1D : public TObject {
public: 
    LokiHist1D();
    LokiHist1D(std::string hash, 
               std::string xvar, 
               std::vector<float> xbins,
               std::string sel = "",
               std::string wei = "" 
               );
    virtual ~LokiHist1D(){};

    void Init();
    void Fill(size_t n);

public :
   // config
   std::string xvar; 
   std::string sel;
   std::string wei;
   std::string hash;
   std::vector<float> xbins;

   // members
   TH1* h;
   TTreeFormula* fx;
   TTreeFormula* fsel;
   TTreeFormula* fwei;

   ClassDef(LokiHist1D,1);

};

class LokiHist2D : public TObject {
public: 
    LokiHist2D();
    LokiHist2D(std::string hash, 
               std::string xvar, 
               std::vector<float> xbins,
               std::string yvar, 
               std::vector<float> ybins,
               std::string sel = "",
               std::string wei = "");
    virtual ~LokiHist2D(){};

    void Init();
    void Fill(size_t n);

public :
   // config
   std::string xvar;
   std::string yvar;
   std::string sel;
   std::string wei;
   std::string hash;
   std::vector<float> xbins;
   std::vector<float> ybins;

   // members
   TH2* h;
   TTreeFormula* fx;
   TTreeFormula* fy;
   TTreeFormula* fsel;
   TTreeFormula* fwei;

   ClassDef(LokiHist2D,1);

};

class LokiHist3D : public TObject {
public: 
    LokiHist3D();
    LokiHist3D(std::string hash, 
               std::string xvar, 
               std::vector<float> xbins,
               std::string yvar, 
               std::vector<float> ybins,
               std::string zvar, 
               std::vector<float> zbins,
               std::string sel = "",
               std::string wei = "");
    virtual ~LokiHist3D(){};

    void Init();
    void Fill(size_t n);

public :
   // config
   std::string xvar; 
   std::string yvar; 
   std::string zvar;
   std::string sel;
   std::string wei;
   std::string hash;
   std::vector<float> xbins;
   std::vector<float> ybins;
   std::vector<float> zbins;

   // members
   TH3* h;
   TTreeFormula* fx;
   TTreeFormula* fy;
   TTreeFormula* fz;
   TTreeFormula* fsel;
   TTreeFormula* fwei;

   ClassDef(LokiHist3D,1);

};

#endif
