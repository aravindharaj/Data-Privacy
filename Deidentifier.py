#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
import copy
import matplotlib.pyplot as plt

from scipy.stats import entropy


class AttributeType(object):
    
    Identifier = 'Identifier'
    QuasiIdentifier = 'QuasiIdentifier'
    Sensitive = 'Sensitive'
    Choices = (('1.Identifier',Identifier),
               ('2.QuasiIdentifier',QuasiIdentifier),
               ('3.Sensitive',Sensitive))

class Interval:
    
    def __init__(self,start,end):
        self.start = start
        self.end = end

    def encode(self):
        self.interval = str(self.start)+'-'+str(self.end)
        return self.interval
        
    def decode(self,interval):
        self.min,self.max = interval.split('-')
        return self.min,self.max
    
class Anonymize:
    
    def __init__(self,anonymity,sensitivity,dataset,attribute_type):
        self.anonymity = anonymity
        self.sensitivity = sensitivity
        self.dataset = dataset
        self.opendata = dataset
        self.attribute_type = attribute_type
        self._anonymize()
        
    def _get_attribute_type(self):
        
        self.attribute_type = []
        for attrtype in AttributeType.Choices:
            print(attrtype[0])
        headers = self.dataset.columns
        for header in headers:
            while True:
                try:
                    _attrtype = int(input('Enter type of the attribute '+header+' '))
                except ValueError:
                    print("Please enter only above mentioned values.")
                    continue
                else:
                    if _attrtype<=3 and _attrtype>=1:
                        self.attribute_type.append((header,AttributeType.Choices[_attrtype-1][1]))
                        break
                    print("Please enter only above mentioned values.")
                    continue
        return self.attribute_type
     
    def _anonymize(self):
        
        quasiIdentifierHeader = []
        sensitiveIdentifierHeader = []
        
        for attrtype in self.attribute_type:
            if attrtype[1]==AttributeType.Identifier:
                self.opendata=self.opendata.drop(attrtype[0],axis=1)
            elif attrtype[1]==AttributeType.QuasiIdentifier:
                quasiIdentifierHeader.append(attrtype[0])
            else:
                sensitiveIdentifierHeader.append(attrtype[0])
        
        numericQuasiIdentifierHeader=[ident for ident in quasiIdentifierHeader 
                                      if type(self.opendata[ident][0]) in 
                                               [np.int,np.int0,np.int8,np.int16,
                                                np.int32,np.int64,np.float,
                                                np.float32,np.float64,np.float128] ]
                                                
        categoricalQuasiIdentifierHeader=list(set(quasiIdentifierHeader)
                                            -set(numericQuasiIdentifierHeader))
                                          
        quasiGeneralizer = {}
        
        for ident in categoricalQuasiIdentifierHeader:
            while True:
                ans = input('Do you want generalize '+ident+'?(y/n)')
                if ans.lower()=='y':
                    value_set = set(self.opendata[ident])
                    quasiGeneralizer[ident]={}                    
                    if(len(value_set)<=2):
                        ans = input('Please Enter a Generalized name for '+repr(value_set)+':')
                        quasiGeneralizer[ident]['Second']=ans
                    else:
                        while True:
                            for index,val in enumerate(value_set):
                                print(index,val)
                            answer = input('Please Enter Indices separated by space ')
                            answer = answer.split(' ')
                            generalList = []                        
                            for ans in answer:
                                generalList.append(list(value_set)[int(ans)])
                            answer = input('Please Enter a Generic Name for it:')
                            if 'First' not in quasiGeneralizer[ident].keys():
                                quasiGeneralizer[ident]['First']={}
                            quasiGeneralizer[ident]['First'][answer]=generalList
                            value_set = value_set - set(generalList)
                            if len(value_set)==0:
                                break
                        ans = input('Please Enter a Generalized name for all:')
                        quasiGeneralizer[ident]['Second']=ans
                    print(quasiGeneralizer)
                    break
                if ans.lower()=='n':
                    quasiGeneralizer[ident]={}
                    break
                print("Please enter y or n.")
                continue
        
        maxi = 0
        for header in numericQuasiIdentifierHeader:
            if maxi<len(set(self.opendata[header])):
                maxUniqueHeader=header
                maxi = len(set(self.opendata[header]))
        
        self.maxUnique = maxUniqueHeader
            
        self.opendata = self.opendata.sort_values(maxUniqueHeader)
        self.opendata = self.opendata.reset_index(drop=True)
        
        sensitiveList = []
        for ident in sensitiveIdentifierHeader:
            sensitiveList.append(list(self.opendata[ident]))
            
        self.sensitiveList=copy.deepcopy(sensitiveIdentifierHeader)
        index=[]
        length=0
        while True:
            prelength = length
            for i in range(0,len(sensitiveList[0])-length+1):
                unique=[]
                for j in range(0,len(sensitiveList)):
                    unique.append(len(set(sensitiveList[j][length:(length+i)])))
                
                flag = True
                for val in unique:
                    if val<self.sensitivity:
                        flag = False
                        break

                if flag and i>=self.anonymity:
                    index.append((length,length+i-1))
                    length=length+i
                    while True:
                        if (length)!=len(sensitiveList[0]) and self.opendata[maxUniqueHeader][length-1]==self.opendata[maxUniqueHeader][length]:
                            length = length+1
                            start,end = index.pop()
                            index.append((start,length-1))
                        else:
                            break
                    break
            if prelength==length:                                
                start,end = index.pop()
                index.append((start,length+i-1))
                break
        
        table=[]
        for i in range(len(index)):
            row=[]
            col=Interval(self.opendata[maxUniqueHeader][index[i][0]],
                         self.opendata[maxUniqueHeader][index[i][1]]).encode()
            self.opendata.loc[index[i][0]:index[i][1],maxUniqueHeader]=col
            row.append(col)
            subData = self.opendata.iloc[index[i][0]:index[i][1]]
            for ident in numericQuasiIdentifierHeader:
                if ident!=maxUniqueHeader:
                    start=subData[ident].min()
                    end=subData[ident].max()
                    col=Interval(start,end).encode()
                    row.append(col)
                    self.opendata.loc[index[i][0]:index[i][1],ident]=col
            for ident in categoricalQuasiIdentifierHeader:
                if('First' in quasiGeneralizer[ident].keys()):
                    flag =False                    
                    identDict = quasiGeneralizer[ident]['First']                    
                    generalName = ''                    
                    for val in subData[ident]:
                        if(flag):
                            break
                        for key in identDict:
                            if val in identDict[key]:
                                if generalName=='':
                                    generalName=key
                                elif key!=generalName:
                                    flag = True
                                    break
                    if(flag):
                        row.append(quasiGeneralizer[ident]['Second'])
                        self.opendata.loc[index[i][0]:index[i][1],ident]=quasiGeneralizer[ident]['Second']
                    else:
                        row.append(generalName)
                        self.opendata.loc[index[i][0]:index[i][1],ident]=generalName
                elif('Second' in quasiGeneralizer[ident].keys()):
                    row.append(quasiGeneralizer[ident]['Second'])
                    self.opendata.loc[index[i][0]:index[i][1],ident]=quasiGeneralizer[ident]['Second']
                else:
                    row.append('*')
            table.append(row)
        print(table)
                
        
    def getOpenData(self):
        return self.opendata
        
    def getMaxUniqueIdentifier(self):
        return self.maxUnique
        
    def getSensitiveList(self):
        return self.sensitiveList
        
class Deidentifier:
    
    def __init__(self,dataset):
        self.dataset = dataset
        self.maxEntropy = self._maxEntropy(len(self.dataset)) 
        self._removeIdentifier()
        self.attribute_type = self._get_attribute_type()
        self.RiskUtilityList=[]
        self.RiskUtility=[]        
        for k in range(5,20):
            self.Anonymity = Anonymize(k,3,self.dataset,self.attribute_type)        
            self.opendata = self.Anonymity.getOpenData()
            self.maxUniqueIdentifier = self.Anonymity.getMaxUniqueIdentifier()
            self.sensitiveList = self.Anonymity.getSensitiveList()
            self.RiskUtilityList.append(self._calculateEntropyForGroup())
        self.RiskUtilityList = np.array(self.RiskUtilityList).T
        for index in range(len(self.sensitiveList)):
            RiskList = np.array(self.RiskUtilityList[index][0]).T
            DataUtilityList = np.array(self.RiskUtilityList[index][1]).T
            dataFrame=pd.DataFrame()
            dataFrame['Risk']=100-RiskList
            dataFrame['DataUtility']=DataUtilityList
            dataFrame['k']=list(range(5,20))
            self.RiskUtility.append(dataFrame)
            plt.plot(self.RiskUtility[index]['k'],self.RiskUtility[index]['DataUtility'],'r',
                 self.RiskUtility[index]['k'],self.RiskUtility[index]['Risk'],'b')
                
        
    def _get_attribute_type(self):
        
        self.attribute_type = []
        for attrtype in AttributeType.Choices:
            print(attrtype[0])
        headers = self.dataset.columns
        for header in headers:
            while True:
                try:
                    _attrtype = int(input('Enter type of the attribute '+header+' '))
                except ValueError:
                    print("Please enter only above mentioned values.")
                    continue
                else:
                    if _attrtype<=3 and _attrtype>=1:
                        self.attribute_type.append((header,AttributeType.Choices[_attrtype-1][1]))
                        break
                    print("Please enter only above mentioned values.")
                    continue
        return self.attribute_type
        
    def _calculateEntropy(self,column):
        return entropy(column.value_counts()/len(column))
 
    def _maxEntropy(self,length):
        return entropy(np.ones(length)/length)
        
    def _removeIdentifier(self):
        headers = self.dataset.columns           
        for header in headers:
            if(self._calculateEntropy(self.dataset[header])>=self.maxEntropy*0.8):
                self.dataset=self.dataset.drop(header,axis=1)
                
    def _calculateEntropyForGroup(self):
        nUnique = set(self.opendata[self.maxUniqueIdentifier])
        groupEntropy=[]        
        risks=[]        
        maxEntropySensitive = self._maxEntropySensitive()
        for unique in nUnique:
            group = self.dataset.loc[self.opendata[self.maxUniqueIdentifier]==unique]
            groupEntropy.append(self._calculateGroupEntropy(group))
            risks.append(list((np.array(self._klDivergence(group))/maxEntropySensitive)*100))
        groupEntropy = np.array(groupEntropy).T
        risks = np.array(risks).T
        dataUtility = []
        maxRisk = []
        for index in range(len(groupEntropy)):
            avg  = np.average(groupEntropy[index])
            #dataUtility.append(((maxEntropySensitive[index]-avg)/maxEntropySensitive[index])*100)
            dataUtility.append(((self.maxEntropy-avg)/self.maxEntropy)*100)
            maxRisk.append(max(risks[index]))          
        return [maxRisk,dataUtility]
                
    def _calculateUtility(self,risks):
        for index in range(len(risks)):
            pass
        
    def _calculateGroupEntropy(self,group):
        groupEntropy = []
        for sensitive in self.sensitiveList:
            groupEntropy.append(self._calculateEntropy(group[sensitive]))
        return groupEntropy

    def _maxEntropySensitive(self):
        entropyList = []
        for sensitive in self.sensitiveList:
                attrCount = len(set(self.dataset[sensitive]))
                entropyList.append(self._maxEntropy(attrCount))
        return entropyList
    
    def _klDivergence(self,group):
        entropyList = []
        for sensitive in self.sensitiveList:
                attrCount = len(set(self.dataset[sensitive]))
                p = list(group[sensitive].value_counts()/len(group))
                while len(p)!=attrCount:
                    p.append(0)
                q = np.ones(attrCount)/attrCount
                entropyList.append(entropy(p,q))
        return entropyList
        
    def getOpenData(self):
        return self.opendata
    
    def getRiskUtility(self):
        return self.RiskUtility
        
        
    