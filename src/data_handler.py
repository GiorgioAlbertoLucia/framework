'''
    Classes to manage input data
'''

from abc import ABC, abstractmethod

import uproot
import pandas as pd
from hipe4ml.tree_handler import TreeHandler

from ..utils.terminal_colors import TerminalColors as tc

class DataHandler:

    def __init__(self):
        return NotImplemented
    
    @abstractmethod
    def _open(self):
        return NotImplemented


class TableHandler(DataHandler): 
    '''
        Class to open data from AO2D.root files generated with a O2Physics table producer
    '''
    def __init__(self, inFilePath: str, treeName: str, dirPrefix: str, **kwargs):

        self.inFilePath = inFilePath
        if type(self.inFilePath) is str:
            self.inData = self._open(inFilePath, treeName, dirPrefix, **kwargs)
        elif type(self.inFilePath) is list:
            dfs = []
            for f in inFilePath:
                dfs.append(self._open(f, treeName, dirPrefix, **kwargs))
            self.inData = pd.concat(dfs)

    def _open(self, inFilePath: str, treeName: str, dirPrefix: str, **kwargs):

        if inFilePath.endswith('.root'):
            
            print(tc.GREEN+'[INFO]: '+tc.RESET+'Opening '+tc.UNDERLINE+tc.CYAN+f'{inFilePath}'+tc.RESET)
            print(tc.GREEN+'[INFO]: '+tc.RESET+'Using tree '+tc.GREEN+f'{treeName}'+tc.RESET+' and directory prefix '+tc.GREEN+f'{dirPrefix}'+tc.RESET)
            th = TreeHandler(inFilePath, treeName, folder_name=dirPrefix, **kwargs)
            return th.get_data_frame()

        else:   raise ValueError(tc.RED+'[ERROR]:'+tc.RESET+' File extension not supported')

class TaskHandler(DataHandler):
    '''
        Class to open data from AO2D.root files generated with a O2Physics task
    '''

    def __init__(self, inFilePath: str, mainDir: str):

        self.inFilePath = inFilePath
        self.mainDir = mainDir
        self.inData = self._open(inFilePath)[mainDir]

    def _open(self, inFilePath):

        if inFilePath.endswith('.root'):
            
            print(tc.GREEN+'[INFO]: '+tc.RESET+'Opening '+tc.UNDERLINE+tc.CYAN+f'{inFilePath}'+tc.RESET)
            print(tc.GREEN+'[INFO]: '+tc.RESET+'Using main directory '+tc.GREEN+f'{self.mainDir}'+tc.RESET)
            return uproot.open(inFilePath)

        else:   raise ValueError('File extension not supported')


