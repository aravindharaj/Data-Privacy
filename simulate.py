# -*- coding: utf-8 -*-
"""
Created on Thu Apr 11 16:58:48 2019

@author: aravindha
"""
import pandas as pd
import numpy as np
import random
name = [
'Merry',
'James',
'Terry',
'Eva',
'John',
'Mark',
'Jack',
'Jessica',
'Tom',
'Lily',
'Brad',
'Julia'
]

data=pd.DataFrame(columns=['Name','Age','Gender','Zipcode','Disease'])
data['Name']=np.random.choice(name,100)
data['Age']=np.random.choice(range(20,50),100)
data['Zipcode']=np.random.choice(range(10000,10020),100)
data['Gender']=np.random.choice(['Male','Female'],100)
data['Disease']=np.random.choice(['Heart disease','Cancer','Diabetes','Kidney'],100)


