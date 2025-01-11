#include "LokiHist.h"
#include <TStyle.h>
#include <TH1F.h>
#include <TH2F.h>
#include <TH3F.h>

#if !defined(__CINT__)
ClassImp(LokiHist1D)
ClassImp(LokiHist2D)
ClassImp(LokiHist3D)
#endif

// LokiHist1D Implemenation
LokiHist1D::LokiHist1D() 
  : TObject()
  , xvar("")
  , sel("")
  , wei("")
  , hash("")
  , h(0)
  , fx(0)
  , fsel(0)
  , fwei(0)
{}

LokiHist1D::LokiHist1D(
    std::string hash, 
    std::string xvar, 
    std::vector<float> xbins,
    std::string sel, 
    std::string wei) 
  : TObject()
  , xvar(xvar)
  , sel(sel)
  , wei(wei)
  , hash(hash)
  , xbins(xbins)
  , h(0)
  , fx(0)
  , fsel(0)
  , fwei(0)
{}

void LokiHist1D::Init()
{
  if(not h){
    h = new TH1F(hash.c_str(),"",xbins.size()-1, &(xbins[0])); 
    h->Sumw2();
  }
}

void LokiHist1D::Fill(size_t n)
{
  for( size_t i=0; i<n; i++){
    if(fsel and not fsel->EvalInstance(i)) continue;
    float weight = fwei ? fwei->EvalInstance(i) : 1.0;
    h->Fill(fx->EvalInstance(i),weight);
  }
}


// LokiHist2D Implemenation
LokiHist2D::LokiHist2D() 
  : TObject()
  , xvar("")
  , yvar("")
  , sel("")
  , wei("")
  , hash("")
  , h(0)
  , fx(0)
  , fy(0)
  , fsel(0)
  , fwei(0)
{}

LokiHist2D::LokiHist2D(
    std::string hash, 
    std::string xvar, 
    std::vector<float> xbins,
    std::string yvar, 
    std::vector<float> ybins,
    std::string sel, 
    std::string wei) 
  : TObject()
  , xvar(xvar)
  , yvar(yvar)
  , sel(sel)
  , wei(wei)
  , hash(hash)
  , xbins(xbins)
  , ybins(ybins)
  , h(0)
  , fx(0)
  , fy(0)
  , fsel(0)
  , fwei(0)
{}

void LokiHist2D::Init()
{
  if(not h){
    h = new TH2F(hash.c_str(),"",
                 xbins.size()-1, &(xbins[0]),
                 ybins.size()-1, &(ybins[0])
                 ); 
    h->Sumw2();
  }
}

void LokiHist2D::Fill(size_t n)
{
  for( size_t i=0; i<n; i++){
    if(fsel and not fsel->EvalInstance(i)) continue;
    float weight = fwei ? fwei->EvalInstance(i) : 1.0;
    h->Fill(fx->EvalInstance(i),
            fy->EvalInstance(i),
            weight);
  }
}


// LokiHist3D Implemenation
LokiHist3D::LokiHist3D() 
  : TObject()
  , xvar("")
  , yvar("")
  , zvar("")
  , sel("")
  , wei("")
  , hash("")
  , h(0)
  , fx(0)
  , fy(0)
  , fz(0)
  , fsel(0)
  , fwei(0)
{}

LokiHist3D::LokiHist3D(
    std::string hash, 
    std::string xvar, 
    std::vector<float> xbins,
    std::string yvar, 
    std::vector<float> ybins,
    std::string zvar, 
    std::vector<float> zbins,
    std::string sel, 
    std::string wei) 
  : TObject()
  , xvar(xvar)
  , yvar(yvar)
  , zvar(zvar)
  , sel(sel)
  , wei(wei)
  , hash(hash)
  , xbins(xbins)
  , ybins(ybins)
  , zbins(zbins)
  , h(0)
  , fx(0)
  , fy(0)
  , fz(0)
  , fsel(0)
  , fwei(0)
{}


void LokiHist3D::Init()
{
  if(not h){
    h = new TH3F(hash.c_str(),"",
                 xbins.size()-1, &(xbins[0]),
                 ybins.size()-1, &(ybins[0]),
                 zbins.size()-1, &(zbins[0])
                 ); 
    h->Sumw2();
  }
}

void LokiHist3D::Fill(size_t n)
{
  for( size_t i=0; i<n; i++){
    if(fsel and not fsel->EvalInstance(i)) continue;
    float weight = fwei ? fwei->EvalInstance(i) : 1.0;
    h->Fill(fx->EvalInstance(i),
            fy->EvalInstance(i),
            fz->EvalInstance(i),
            weight);
  }
}

