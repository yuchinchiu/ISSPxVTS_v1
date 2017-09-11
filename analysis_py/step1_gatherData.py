# -*- coding: utf-8 -*-
"""
Created on Tue Aug  1 09:03:53 2017

@author: yc180

This script go through all the log/txt in the folder and extract data to build a "group" DataFrame for later analysis
The output are two files: gpData.pkl & gpSbjInfo.pkl

"""

import os
import glob
import pandas as pd
import numpy as np
from copy import copy
from extractData import extractDataFromCSV

workingDir = os.path.dirname(os.path.realpath(__file__))
os.chdir("..")
# go up one level to the experiment directory

dataDir = os.getcwd() + os.sep + 'data' + os.sep + 'v1_batches' + os.sep  # where the log/txt files are located
csvDir  = os.getcwd() + os.sep + 'data' + os.sep + 'v1_csv' + os.sep

# run the following function to extract missing data from CSV files
extractDataFromCSV(dataDir, csvDir)


fileList     = glob.glob(dataDir +  "*.log")
infofileList = glob.glob(dataDir +  "*.txt")


gpSbjInfo=pd.DataFrame()


colNames=['runId','stim','stimUnique','stimCat','trialType','swProb','task','response','sbjResp','sbjACC','sbjRT']
gpData = pd.DataFrame(np.empty((0,len(colNames)),dtype=int), columns=colNames)
SCNT=0

for f in range(0,len(fileList),1):
    SCNT=SCNT+1
    D=np.genfromtxt(fileList[f],delimiter=',',dtype=int)
    D=pd.DataFrame(np.transpose(np.reshape(D,(len(colNames),int(D.shape[0]/len(colNames))))),columns=colNames)
    D['sbjId']=SCNT
    D['bkType']=1
    D.loc[D.trialType==2,'bkType']=2
    
    txtFileName = fileList[f][:-3]+ "txt"
    # read in the corresponding text file and extract SRmapping, etc
    sbjInfo=np.genfromtxt(txtFileName, delimiter=":", dtype=str)
    sbjInfo=pd.DataFrame(np.transpose(sbjInfo))
    sbjInfo.columns = sbjInfo.iloc[0]
    sbjInfo.drop([0],axis=0,inplace=True)
    SRmapping = sbjInfo.loc[1,'SRmapping'].split(',') 
    # 0 was the index that become header, hasn't reset index, so taking 1
    sbjInfo['sbjId']=SCNT
    sbjInfo.index = sbjInfo.sbjId
    sbjInfo.drop('sbjId',axis=1,inplace=True)
    # figure which task subject performed based on left/right hand 
    D.loc[(D['trialType']==2) & (D['sbjResp']==int(SRmapping[0])),'task']=1
    D.loc[(D['trialType']==2) & (D['sbjResp']==int(SRmapping[1])),'task']=1
    D.loc[(D['trialType']==2) & (D['sbjResp']==int(SRmapping[2])),'task']=2
    D.loc[(D['trialType']==2) & (D['sbjResp']==int(SRmapping[3])),'task']=2
    # figure out 'correct response' based on the task inferred
    # stimCat 1-4 'large living'-'large-nonliving'-small-living,-small-nonliving
    for trial in range(0,len(D),1):
        if D.loc[trial,'trialType']==2:
            if D.loc[trial,'task']==1:  # larger/smaller task
                if (D.loc[trial,'stimCat']==1)|(D.loc[trial,'stimCat']==2):
                    D.loc[trial,'response']=int(SRmapping[0])
                else:
                    D.loc[trial,'response']=int(SRmapping[1])
            else: # living vs. nonliving task
                if (D.loc[trial,'stimCat']==1)|(D.loc[trial,'stimCat']==3):
                    D.loc[trial,'response']=int(SRmapping[2])
                else:
                    D.loc[trial,'response']=int(SRmapping[3])                
    
    # figure out switch/repeat for the voluntary 
    
    firstTrial=np.where(D.loc[:,'trialType']==2)[0][0]  # first voluntary trial
    currentTask = D.loc[firstTrial,'task']
    D.loc[firstTrial,'trialType'] = 1  # consider the first voluntary trial as switch
    for trial in range(firstTrial+1,len(D),1):
        if D.loc[trial,'task']==currentTask:
            D.loc[trial,'trialType']=0
        else:
            D.loc[trial,'trialType']=1
            currentTask=D.loc[trial,'task']
    
    D.loc[(D.loc[:,'sbjResp']==D.loc[:,'response']),'sbjACC']=1
    D.loc[(D.loc[:,'sbjResp']!=D.loc[:,'response']),'sbjACC']=0
    
    gpSbjInfo = pd.concat([gpSbjInfo,sbjInfo],axis=0)
    gpData=pd.concat([gpData,D],axis=0)

# convert codings to categorical variables with meaningful names
gpData['trialType2']=copy(gpData['trialType'])  # preserve 0,1 to calcuate switch rate for VTS task
gpData.bkType.replace(1,'cued', inplace=True)
gpData.bkType.replace(2,'choice', inplace=True)
gpData.trialType.replace(0,'repeat', inplace=True)
gpData.trialType.replace(1,'switch', inplace=True)
gpData.swProb.replace(25,'sw25%', inplace=True)
gpData.swProb.replace(75,'sw75%', inplace=True)
gpData.task.replace(1,'size', inplace=True)
gpData.task.replace(2,'animacy', inplace=True)

gpData['bkType']   = pd.Categorical(gpData.bkType, categories=['cued','choice'],ordered=True)
gpData['swProb']   = pd.Categorical(gpData.swProb, categories=['sw25%','sw75%'],ordered=True)
gpData['trialType']= pd.Categorical(gpData.trialType, categories=['repeat','switch'],ordered=True)

# output DataFrame
os.chdir(workingDir)  # scripts directory
gpData.to_pickle('gpData.pkl')
gpData.to_pickle('gpSbjInfo.pkl')
print(SCNT)