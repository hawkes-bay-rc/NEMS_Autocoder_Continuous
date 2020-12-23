import pandas as pd
import QaBay as qb

import json

stnList = pd.read_csv('autoProcess.csv') 
print(stnList.head())

#this will be super slow but given the small list of rows it will be alright
##https://stackoverflow.com/questions/16476924/how-to-iterate-over-rows-in-a-dataframe-in-pandas
for index, row in stnList.iterrows():
    qb.siteSelector(row["site"],row["measurement"],row["startTime"],row["endTime"])
    qb.configParams(row["resolution"],row["timeGap"],row["accuracyThreshold"],row["accuracyBandwidth"],row["grossRangeFailBelow"],row["grossRangeFailAbove"],row["grossRangeSuspectBelow"],row["grossRangeSuspectAbove"],row["Flatline tolerance"],row["flatline suspect period"],row["flatline fail period"],row["rate of Change threshold"],row["spike Suspect threshold"],row["spikeFailThreshold"])
    qb.runTests()
    
qb.data['QARTOD'] = qb.qc_results['qartod']['aggregate'].data
qb.data.head()
qb.data.to_csv(qb.mySite+'-'+qb.myMeasurement+'.csv',index=False)