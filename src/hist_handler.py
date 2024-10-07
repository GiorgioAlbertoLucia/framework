'''
    Class to create histograms from a given dataset
'''

import numpy as np
from abc import ABC, abstractmethod

from ROOT import TH1F, TH2F, TFile, TH1

from .axis_spec import AxisSpec
from .hist_info import HistLoadInfo

class THist:
    '''
        Creates a THnF, where n is the size of axisSpecs
    '''
    def __init__(self, axisSpecs):

        self.__hist = None
        if len(axisSpecs) == 1:     self.__hist = TH1F(axisSpecs[0].name, axisSpecs[0].title, axisSpecs[0].nbins, axisSpecs[0].xmin, axisSpecs[0].xmax)
        elif len(axisSpecs) == 2:   self.__hist = TH2F(axisSpecs[0].name, axisSpecs[0].title, axisSpecs[0].nbins, axisSpecs[0].xmin, axisSpecs[0].xmax, axisSpecs[1].nbins, axisSpecs[1].xmin, axisSpecs[1].xmax)
        else:                       raise ValueError('Lenght of the axes specifics list must be one or two')

    @property
    def hist(self): return self.__hist
        



class HistHandler(ABC):

    def __init__(self, inData):
        self.inData = inData

    @classmethod
    def createInstance(cls, inData):
        if str(type(inData)) == "<class 'uproot.reading.ReadOnlyDirectory'>":   return UprootHistHandler(inData)
        elif str(type(inData)) == "<class 'pandas.core.frame.DataFrame'>":      return DFHistHandler(inData)
        else:                                                                   raise ValueError('Data type not supported. Input data has type '+str(type(inData)))

    @classmethod
    def loadHist(cls, histInfo: HistLoadInfo) -> TH1:
        '''
            Load histogram from file
        '''
        histFile = TFile(histInfo.hist_file_path)
        hist = histFile.Get(histInfo.hist_name)
        hist.SetDirectory(0)
        histFile.Close()

        return hist

    @abstractmethod
    def buildTH1(self, xVariable, axisSpecX): 
        return NotImplemented

    @abstractmethod
    def buildTH2(self, xVariable, yVariable, axisSpecX, axisSpecY):
        return NotImplemented

    @abstractmethod
    def buildEfficiency(self, xVariable, yVariable, axisSpecX):
        return NotImplemented

    def buildEfficiency(self, partialHist, totalHist):

        if 'TH1' in str(type(partialHist)):
            
            axisSpecX = AxisSpec(partialHist.GetNbinsX(), partialHist.GetXaxis().GetXmin(), partialHist.GetXaxis().GetXmax(), partialHist.GetName()+'Eff', partialHist.GetName()+'Efficiency')
            hEff = THist([axisSpecX]).hist

            for xbin in range(1, totalHist.GetNbinsX()):
                if totalHist.GetBinContent(xbin) > 0:

                    eff = partialHist.GetBinContent(xbin)/totalHist.GetBinContent(xbin)
                    effErr = 0.
                    if eff < 1: effErr = np.sqrt(eff*(1-eff)/totalHist.GetBinContent(xbin))
                    
                    hEff.SetBinContent(xbin, eff)
                    hEff.SetBinError(xbin, effErr)

            return hEff

        elif 'TH2' in str(type(partialHist)):

            axisSpecX = AxisSpec(partialHist.GetNbinsX(), partialHist.GetXaxis().GetXmin(), partialHist.GetXaxis().GetXmax(), partialHist.GetName()+'Eff', partialHist.GetName()+' Efficiency')
            axisSpecY = AxisSpec(partialHist.GetNbinsY(), partialHist.GetYaxis().GetXmin(), partialHist.GetYaxis().GetXmax(), partialHist.GetName()+'Eff', partialHist.GetName()+' Efficiency')
            hEff = THist([axisSpecX, axisSpecY]).hist 

            for ybin in range(1, partialHist.GetNbinsY() + 1):   
                for xbin in range(1, totalHist.GetNbinsX()):
                    if totalHist.GetBinContent(xbin) > 0:
                    
                        eff = partialHist.GetBinContent(xbin, ybin)/totalHist.GetBinContent(xbin)
                        effErr = 0.
                        if eff < 1: effErr = np.sqrt(eff*(1-eff)/totalHist.GetBinContent(xbin))
                    
                        hEff.SetBinContent(xbin, ybin, eff)
                        hEff.SetBinError(xbin, ybin, effErr)
            
            return hEff
        
        else:   raise ValueError('Invalid partialHist type. Accepted typs are TH1 and TH2')

    def setLabels(self, hist, labels, axis: str):
        '''
            Set labels on histogram axis from dictionary (corresponding value on axis: label to be set)
        '''

        tmp_hist = hist.Clone()
        hist.Reset()
        if axis == 'x':
            for val, label in labels.items():   hist.GetXaxis().SetBinLabel(val+1, label)
        elif axis == 'y':
            for val, label in labels.items():   hist.GetYaxis().SetBinLabel(val+1, label)
        else:   
            raise ValueError('Only accepted axis values are "x", "y"')
        
        if 'TH1' in str(type(tmp_hist)):
            for ibin in range(1, tmp_hist.GetNbinsX()+1):
                hist.SetBinContent(ibin, tmp_hist.GetBinContent(ibin))
                hist.SetBinError(ibin, tmp_hist.GetBinError(ibin))
        elif 'TH2' in str(type(tmp_hist)):
            for ibin in range(1, tmp_hist.GetNbinsX()+1):
                for jbin in range(1, tmp_hist.GetNbinsY()+1):
                    hist.SetBinContent(ibin, jbin, tmp_hist.GetBinContent(ibin, jbin))
                    hist.SetBinError(ibin, jbin, tmp_hist.GetBinError(ibin, jbin))
        else:   raise ValueError('Invalid histogram type')
        
        return hist

class DFHistHandler(HistHandler):

    def __init__(self, inData):
        self.inData = inData

    def buildTH1(self, xVariable: str, axisSpecX: AxisSpec) -> TH1F:
        hist = THist([axisSpecX]).hist
        for x in self.inData[xVariable]:    hist.Fill(x)
        return hist
    
    def buildTH2(self, xVariable: str, yVariable: str, axisSpecX: AxisSpec, axisSpecY: AxisSpec) -> TH1F:
        hist = THist([axisSpecX, axisSpecY]).hist
        for x, y in zip(self.inData[xVariable], self.inData[yVariable]):    hist.Fill(x, y)
        return hist

        

class UprootHistHandler(HistHandler):

    def __init__(self, inData):
        self.inData = inData

    def buildTH1(self, name: str) -> TH1F:
        return self.inData[name].to_pyroot()
    
    def buildTH2(self, name: str) -> TH1F:
        return self.inData[name].to_pyroot()
        