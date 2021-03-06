# -*- coding: utf-8 -*-
"""
Created on Tue Aug  1 11:29:56 2017

@author: yc180
"""
#%%
import pandas as pd
import numpy as np
import scipy.stats as stats
import seaborn as sns
import matplotlib.pyplot as plt
import os
from copy import copy

workingDir = os.path.dirname(os.path.realpath(__file__))
os.chdir(workingDir)

gpData = pd.read_pickle('v2\gpData_v2.pkl')

gpResult  = pd.DataFrame(np.empty((0,0),dtype=int))
gpResult2 = pd.DataFrame(np.empty((0,0),dtype=int))
gpResult3 = pd.DataFrame(np.empty((0,0),dtype=int))

gpData_valid = pd.DataFrame(np.empty((0,0),dtype=int))
gpData_invalid = pd.DataFrame(np.empty((0,0),dtype=int))

#gpRT=pd.DataFrame(np.empty((0,1),dtype=int))

overallACC = pd.DataFrame(np.unique(gpData.sbjId),dtype=int,columns=['sbjId'])
overallACC['meanACC']=np.nan
excludeSbj=[]
goodSbj=[]

#%% do a fist pass to exclude subjects with low cued task accuracy
gpData['sbjRT2'] = copy(gpData.sbjRT)
gpData.loc[gpData.sbjRT2<350, 'sbjRT']  = np.nan
gpData.loc[gpData.sbjRT2<350, 'sbjACC'] = 0

totalSCNT = len(np.unique(gpData.sbjId))

for S in np.unique(gpData.sbjId):
    D = gpData.loc[gpData.sbjId==S]    
    if D[D.bkType=='cued'].sbjACC.mean()*100 > 85:
        goodSbj.append(S)
    else:
        excludeSbj.append(S)


#%%
ISSP = pd.DataFrame(np.unique(gpData.sbjId),dtype=int,columns=['sbjId'])

for S in goodSbj:
    D = gpData.loc[gpData.sbjId==S]
    #
    gpData_valid = pd.concat([gpData_valid, D], axis=0)
    #
    sbjMeans = pd.DataFrame(D.groupby(['bkType','swProb','trialType']).sbjACC.mean()*100)
    sbjMeans['sbjRT']=pd.DataFrame(D.loc[D.sbjACC==1,:].groupby(['bkType','swProb','trialType']).sbjRT.mean())
    sbjMeans['sbjId']=S
    gpResult = pd.concat([gpResult,sbjMeans],axis=0)
    if sbjMeans.sbjACC.std()>30:   ## if set at 10, there'll be about 10 subjects being excluded due to this criteria
        excludeSbj.append(S)
    #
    sbjMeans.reset_index(inplace=True)
    RT = sbjMeans.sbjRT
    ISSP.loc[ISSP[ISSP.sbjId==S].index, 'issp']=RT[1]-RT[0]-(RT[3]-RT[2])    
    ISSP.loc[ISSP[ISSP.sbjId==S].index, 'issp_choice'] = RT[5]-RT[4]-(RT[7]-RT[6])
    #
    sbjMeans2 = pd.DataFrame(D[D['bkType']=='choice'].groupby('swProb').trialType2.mean()*100)    
    sbjMeans2['sbjId']=S
    gpResult2 = pd.concat([gpResult2,sbjMeans2],axis=0)        
    
    sbjMeans3 = pd.DataFrame(D[D['bkType']=='choice'].groupby(['swProb','runId']).trialType2.mean()*100)
    sbjMeans3['sbjId']=S
    gpResult3 = pd.concat([gpResult3,sbjMeans3],axis=0)
    
    if (sum(sbjMeans3.trialType2<=15) + sum(sbjMeans3.trialType2>=85))>=1:  # one of the block swRate was zero...
        excludeSbj.append(S)
    # 
    ISSP.loc[ISSP[ISSP.sbjId==S].index, 'sw25%_swRate'] = sbjMeans2.trialType2[0]
    ISSP.loc[ISSP[ISSP.sbjId==S].index, 'sw75%_swRate'] = sbjMeans2.trialType2[1]

# MUST INCLUDE RESET_INDEX, OTHERWISE THE BELOW exclude subject chuck will be order

gpResult.reset_index(inplace=True)
gpResult2.reset_index(inplace=True)
gpResult3.reset_index(inplace=True)
gpData_valid.reset_index(inplace=True)

#%%

gpData_invalid = pd.DataFrame(np.empty((0,0),dtype=int))
for S in excludeSbj:    
    gpResult.drop(gpResult[gpResult.sbjId==S].index, axis=0, inplace=True)
    gpResult2.drop(gpResult2[gpResult2.sbjId==S].index, axis=0, inplace=True)
    gpResult3.drop(gpResult3[gpResult3.sbjId==S].index, axis=0, inplace=True)
    ISSP.drop(ISSP[ISSP.sbjId==S].index,axis=0, inplace=True)    
    gpData_invalid = pd.concat([gpData_invalid, gpData_valid[gpData_valid.sbjId==S]],axis=0)
    gpData_valid.drop(gpData_valid[gpData_valid.sbjId==S].index, axis=0, inplace=True)
    
    
    
gpResult.reset_index(inplace=True)
gpResult2.reset_index(inplace=True)
gpResult3.reset_index(inplace=True)

fig = plt.figure(figsize=(16,5))
sns.factorplot(x='swProb',y='sbjACC',data=gpResult,hue='trialType',col='bkType')
sns.factorplot(x='swProb',y='sbjRT', data=gpResult,hue='trialType',col='bkType')

# sns.factorplot("Sex", "Survived", hue="Pclass", data=dfTrain)

gpResult2.rename(columns={'trialType2':'VolSwRate'},inplace=True)
fig = plt.figure(figsize=(5,5))
sns.boxplot(x='swProb',y='VolSwRate',data=gpResult2)

# quick paired t-test
a = np.array(gpResult2[gpResult2.swProb=='sw25%'].VolSwRate)
b = np.array(gpResult2[gpResult2.swProb=='sw75%'].VolSwRate)
tt = stats.ttest_rel(a,b)
tvalue = tt.statistic
print(tt.pvalue)

validSCNT=np.unique(gpResult.sbjId).shape[0]
print(validSCNT)

# quick 1 sample ttest on ISSP (essentially the interaction) against 0
ISSP_inX=stats.ttest_1samp(ISSP.issp,0)
print(ISSP_inX.pvalue)

ISSP_c_inX=stats.ttest_1samp(ISSP.issp_choice,0)
print(ISSP_c_inX.pvalue)

#%%
gpResult3.rename(columns={'trialType2':'VolSwRate'},inplace=True)
fig = plt.figure(figsize=(5,5))
sns.factorplot(x='runId',y='VolSwRate', hue='swProb',data=gpResult3)
# 
a = np.array(gpResult3[(gpResult3.swProb=='sw25%') & (gpResult3.runId==9)].VolSwRate)
b = np.array(gpResult3[(gpResult3.swProb=='sw75%') & (gpResult3.runId==9)].VolSwRate)
tt2 = stats.ttest_rel(a,b)


print(totalSCNT)

gpData_valid.to_csv('validgpData_v1.csv',encoding='utf-8', index=False)
gpData_invalid.to_csv('invalidgpData_v1.csv',encoding='utf-8', index=False)
