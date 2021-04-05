!#/usr/bin/python
# -*- coding: utf-8 -*-
"""
Updated on WED Dec  23 13:30:00 NZT
Implementation wrapper for HAWQi dataprocessing using QARTOD

@author: Karunakar
"""
#this code has to be used in conjunction with the notebook

import pandas as pd
import numpy as np
import numpy.ma as ma
import requests
import operator
from datetime import datetime
#fast parser https://stackoverflow.com/questions/1912434/how-do-i-parse-xml-in-python
import xml.etree.ElementTree as ET
import json

#Get Qartod
from ioos_qc.config import QcConfig
from ioos_qc import qartod

#interactive sessions
from ipywidgets import interact, interactive, fixed, interact_manual
import ipywidgets as widgets

#plots on the client
from bokeh.layouts import gridplot
from bokeh.plotting import figure, show, output_notebook
from bokeh.models import ColumnDataSource, FactorRange
from bokeh.transform import factor_cmap
try :
    output_notebook()
except Exception as e:
    print(e)
    print('Not running from notebook?')
    
#clear the plots before new ones
from IPython.display import clear_output

#import Qartod flags
qFlags = qartod.QartodFlags()
"""qFlags.GOOD, qFlags.FAIL, qFlags.SUSPECT"""

#import hill_depth by Jeff Cooke
import hill_depth as hd
#import hill_depthV01 as hd

#Hilltop connector
#data from telemetry is processed and sent to all sites, so telemetry api.
apiRoot="https://data.hbrc.govt.nz/EnviroData/Telemetry.hts?service=Hilltop"

#variables - all are strings here
mySite = None
myMeasurement = None
myStartDate = None
myEndDate = None
emailId = None

data = None #dataframe sits in this variable

extraPlotsPlease = False #variable to indicate add additional points to plots
extraPlotData = None #data to the plots !! how about this is none being used as a proxy to initiate extra plots
def runTests():
    global qc_results
    #print (qc_config)
    global extraPlotsPlease
    global extraPlotData
    global data
        
    # Run QC
    qc = QcConfig(qc_config)
    qc_results =  qc.run(
        inp=data[myMeasurement],
        tinp=data['timestamp'].values 
    )
    
    #NEMS tests
    #gap test
    timDiff = list(map(operator.sub, data['timestamp'].values[1:],data['timestamp'].values[:-1]))
    samplingMask_gapData = np.insert(np.array([qFlags.FAIL if x>np.timedelta64(timeLimit_NEMS,'m') \
                                               else qFlags.GOOD for x in timDiff]), 0, 1, axis=0) #prepend for start to be true
    #print(samplingMask_gapData)
    qc_results['qartod']['NEMS_gapData'] = ma.masked_array(samplingMask_gapData)
    qc_results['qartod']['aggregate'][qc_results['qartod']['NEMS_gapData']==qFlags.FAIL]=qFlags.FAIL
    
    
    ## resolution tests
    #print(data[myMeasurement].dtype)
    samplingMask_resolution = []
    for x in data[myMeasurement]:
        if('.' in x):
            temp = x.split('.')
            if(len(temp[1])>= decimalReq_NEMS) :
                samplingMask_resolution.append(qFlags.GOOD)
            else:
                samplingMask_resolution.append(qFlags.FAIL)
        else :
            samplingMask_resolution.append(qFlags.FAIL)
    qc_results['qartod']['NEMS_resolution'] = ma.masked_array(samplingMask_resolution)
    ## update the aggregate masked array.
    qc_results['qartod']['aggregate'][qc_results['qartod']['NEMS_resolution']==qFlags.FAIL]=qFlags.FAIL
    
    ##Accuracy tests - connecting the continuous and discrete data sets
    if(mySite == 'HAWQi'):
        with open('hawqiContDiscrtMapping.json') as json_file:
            mapFile = json.load(json_file)
            for item in mapFile:
                #print(item['HAWQi'], myMeasurement)
                endPoint = "https://data.hbrc.govt.nz/EnviroData/EMAR.hts?"
                siteName = "HAWQi NSWQ"
                precTSeries = None #place holder

                if(item['HAWQi'] == myMeasurement):
                    #print(item['var']),item['depth']);
                    if item['var'] == 'compute':
                        print('not implemented yet')
                        print('the following error is intentional')
                        if 'Salinity' in item['HAWQi'] : #and NaN == NaN:
                            precTSeries = checkCTD(endPoint,siteName,item)
                            #print(precTSeries)
                    else :
                        extraPlotData = getObsSummary(endPoint,siteName,item)
                        extraPlotsPlease = "accuracy"
                    
                    #print(precTSeries.dtypes)
                    precTSeries.drop_duplicates(inplace=True,subset=["surveytime"])
                    #print(precTSeries)
                    samplingMask_accuracy = sampleTimeDepth(precTSeries)

                    #print(samplingMask_accuracy)
                    qc_results['qartod']['NEMS_accuracy'] = ma.masked_array(samplingMask_accuracy)
                    ## update the aggregate masked array.
                    qc_results['qartod']['aggregate'][qc_results['qartod']['NEMS_accuracy']==qFlags.FAIL]=qFlags.FAIL
    
    #qc_results
    plotStats()
    #print(data.head())
    
def fetchData():
    #print('fetching data: ',mySite,myMeasurement,myStartDate,myEndDate)
    global data
    timeList = []
    obsList = []
    #get the observation data for each site
    requestType = "GetData"
    myWebRequest =  apiRoot + '&Request='+requestType+'&Site='+mySite+'&Measurement='+myMeasurement+'&From='+myStartDate+'&To='+myEndDate
    r = requests.get(myWebRequest)
    #print(r.text)
    root = ET.fromstring(r.content)
    for child in root.iter('E'):
        #print(child.tag,child.attrib)
        for miter in child.iter('*'):
            #print(miter.tag,miter.text)
            if miter.tag == 'T':
                timeList.append(np.datetime64(datetime.strptime(miter.text,'%Y-%m-%dT%H:%M:%S')))#.timestamp()))
                #timeList.append(datetime.strptime(miter.text,'%Y-%m-%dT%H:%M:%S').timestamp())
            if miter.tag == 'I1':
                obsList.append(miter.text)
    
    df={'timestamp':np.array(timeList), myMeasurement:np.array(obsList)}
    data = pd.DataFrame (df, columns = ['timestamp',myMeasurement])

def getObsSummary(endPoint,siteName,item):
    measurementName = item['var'] #you should have an idea of what you are querying
    profileData = hd.get_depth_profile(endPoint=endPoint, site=siteName, \
                                   measurement='['+measurementName+']', timeFrom=myStartDate, timeTo=myEndDate)
    #print(profileData.head())
    sub = hd.result_at_depth(data=profileData, depth=float(item['depth']))
    precTSeries = (sub[["surveytime","value"]].sort_values(by=["surveytime"]))\
                    .rename(columns={"value":myMeasurement})
    #precTSeries.drop_duplicates(inplace=True) #this throws a warning in __future__, search for alternatives
    ##https://pandas.pydata.org/pandas-docs/stable/user_guide/indexing.html#returning-a-view-versus-a-copy

    summary = hd.summary_at_depth(data=profileData, depth=float(item['depth']))
    minAtDep = (pd.DataFrame(summary.to_records())[["surveytime","('value', 'min')"]])\
                    .rename(columns={"('value', 'min')":'sum-'+myMeasurement}) #col name issue by flattening
    maxAtDep = (pd.DataFrame(summary.to_records())[["surveytime","('value', 'max')"]])\
                    .rename(columns={"('value', 'max')":myMeasurement})
    sumAtDep = (pd.concat([minAtDep,maxAtDep])).reset_index(drop=True).sort_values(by=["surveytime"])
    #print(sumAtDep)
    return {"x":sumAtDep["surveytime"], "y":sumAtDep[myMeasurement]}
    
def checkCTD(endPoint,siteName,item):
    #gsw is the TEOS2010 package for seawater state of equation, pip install it https://github.com/TEOS-10/GSW-Python
    #import gsw
    #importing here is funny, but the system system should not fail if it fails to import this library.
    #It looks like the library has migrated to a different version.
    
    #print('conductivity')
    measurementName = 'Specific Conductivity (Depth Profile)'
    profileData = hd.get_depth_profile(endPoint=endPoint, site=siteName, \
                               measurement='['+measurementName+']', timeFrom=myStartDate, timeTo=myEndDate)
    profileData.to_csv('HawqiRawC.csv',index=False)
    sub = hd.result_at_depth(data=profileData, depth=float(item['depth']))
    condTSeries = (sub[["surveytime","value"]].sort_values(by=["surveytime"]))\
                .rename(columns={"value":"conductivity"})
    condTSeries.drop_duplicates(inplace=True,subset=["surveytime"])
    print(condTSeries)

    #print('temperature')
    measurementName = 'Water Temperature (Depth Profile)'
    profileData = hd.get_depth_profile(endPoint=endPoint, site=siteName, \
                               measurement='['+measurementName+']', timeFrom=myStartDate, timeTo=myEndDate)
    ##profileData.to_csv('HawqiRawT.csv',index=False)
    sub = hd.result_at_depth(data=profileData, depth=float(item['depth']))
    tempTSeries = (sub[["surveytime","value"]].sort_values(by=["surveytime"]))\
                .rename(columns={"value":"temperature"})
    tempTSeries.drop_duplicates(inplace=True,subset=["surveytime"])
    print(tempTSeries)

    #print('pressure')
    measurementName = 'Pressure mbars (Depth Profile)'
    profileData = hd.get_depth_profile(endPoint=endPoint, site=siteName, \
                               measurement='['+measurementName+']', timeFrom=myStartDate, timeTo=myEndDate)
    ##profileData.to_csv('HawqiRawP.csv',index=False)
    #print(profileData.dtypes)

    #profileData = profileData.drop_duplicates(subset=["surveytime","depth"])
    #profileData.reset_index()
    
    sub = hd.result_at_depth(data=profileData, depth=float(item['depth']))
    #print(sub[pd.isnull(sub['value'])])
    presTSeries = (sub[["surveytime","value"]].sort_values(by=["surveytime"]))\
                .rename(columns={"value":"pressure"})
    presTSeries.drop_duplicates(inplace=True,subset=["surveytime"])
    print(presTSeries)

    #merge dataframes to make a single dataset and pass it to GSW
    ctDf = condTSeries.merge(tempTSeries, left_on="surveytime",right_on="surveytime")
    ctpDf = ctDf.merge(presTSeries, left_on="surveytime",right_on="surveytime")
    print(ctpDf)

    #print(ctpDf["pressure"],np.subtract(np.multiply(ctpDf["pressure"],1/100),10.135))
    SP = gsw.SP_from_C(np.multiply(ctpDf["conductivity"],1/1E3), ctpDf["temperature"], 
                       np.multiply(ctpDf["pressure"],1/100))
    myData = {"surveytime":ctpDf["surveytime"],
              myMeasurement:SP}
    precTSeries = pd.DataFrame(data=myData ,columns=["surveytime",myMeasurement])
                            
    
def sampleTimeDepth(precTSeries):
    global data
    
    #samplingMask_accuracy
    samplingMask_accuracy = np.repeat(qFlags.UNKNOWN, len(data))
    #print(samplingMask_accuracy)
    """
    The thought of appending the survey time to the oringinal observation data frame is quite intriguing.
    Making a copy of large dataset would demand more contagious memory and is not optimal
    Since processing time is not a major issue as of now, sticking to the filtering version
    """
    #filter 10 times sampling rate on both sides of obs, to create a short version of data for imputation, easier handling.
    #iterating over data frames is super slow, so extracting the time part to a list/array
    for fieldVisit in precTSeries["surveytime"]:
        dLo = accuBWidth_NEMS * -1*np.timedelta64(timeLimit_NEMS,'m') + fieldVisit
        dHi = accuBWidth_NEMS * np.timedelta64(timeLimit_NEMS,'m') + fieldVisit
        redData = data[data['timestamp'].between(dLo,dHi)]
        redData.drop_duplicates(inplace=True) #this throws a warning in __future__, search for alternatives

        if (len(redData[redData['timestamp']>fieldVisit]) > 0) and (len(redData[redData['timestamp']<fieldVisit]) > 0):
            temp = pd.DataFrame(data={"timestamp":np.array([fieldVisit]),
                                      myMeasurement:np.array([float("NaN")])}, columns=["timestamp",myMeasurement])
                                        #strong casting variables
            redData = redData.append(temp).set_index("timestamp")
            redData[myMeasurement] = redData[myMeasurement].apply(pd.to_numeric)
            redData = redData.sort_values(by=["timestamp"])
            #since we have only 2 columns and timestamps are already well defined
            redData[myMeasurement].interpolate(method='values',inplace=True)
            #uses index in interpolation
            redData = redData.reset_index()
            #timeStamp in Observation data just before imputation
            mIdx = (redData.index[(redData["timestamp"]==fieldVisit).shift(-1).fillna(False)])
            #index fetched

            if abs(float(redData[myMeasurement][redData["timestamp"]==fieldVisit])- \
                   float(precTSeries[myMeasurement][precTSeries["surveytime"]==fieldVisit])) < accuThresh_NEMS:
                samplingMask_accuracy[int(mIdx[0]):] = qFlags.GOOD
            else:
                samplingMask_accuracy[int(mIdx[0]):] = qFlags.FAIL

    return samplingMask_accuracy

###-------------------------------------------------------------------------------------
# This section here is specific to writing the NEMS codes back to files and get them into the hilltop
# These are tested in a notebook
###-------------------------------------------------------------------------------------
def writeHilltopFormat(data=data):
    if data is None:
        print("Please run the code first")
    data = mapNEMScodes(data)
    #format according to Jeff Cooke's mail
    data['Measurement'] = myMeasurement
    data.rename(columns={myMeasurement:'Value'}, inplace=True)
    data = data[['timestamp','Measurement','Value','QC','Comment']] #reorganising the column position
    data.to_csv(mySite+'-'+myMeasurement+'.csv',index=False)

def mapNEMScodes(data):
    #global data
    data['QC'] = qc_results['qartod']['aggregate'].data
    myMap = {
        float(qFlags.GOOD):600,
        float(qFlags.SUSPECT):400,
        float(qFlags.FAIL):200
    }
    data = data.replace({'QC':myMap})
    
    #print(qc_results['qartod'].keys())
    df = pd.DataFrame(qc_results['qartod'], columns=qc_results['qartod'].keys())
    df = df.drop(['aggregate'], axis=1)
    #df = df.where(df == qFlags.GOOD, df.columns.to_series(), axis=1)
    for i in df.columns:
        df[i].loc[(df[i] != qFlags.GOOD)] = i
    df['comment'] = df[df.columns].apply(lambda x: ' '.join([str(a) for a in x if a !=1 ]), axis=1)
    data['Comment'] = df['comment']
    #print(df.head())
    return data
    
###-------------------------------------------------------------------------------------
# This section here deals with the interactive interfaces made available to notebook
# These are tested in a notebook
###-------------------------------------------------------------------------------------
runOk = None
def siteSelector(Site,Measurement,StartDate,EndDate):
    global mySite
    mySite = Site
    print('please wait for the right options to load')
    global myMeasurement
    myMeasurement = Measurement
    global myStartDate
    global myEndDate
    myStartDate = str(StartDate)
    myEndDate = str(EndDate)
    if myStartDate and myEndDate :
        fetchData()

accuThresh_NEMS = None
accuBWidth_NEMS = None
def configParams(resolution,
                 timeGap,
                 accuracyThreshold,
                 accuracyBandwidth,
                 grossRangeFailBelow,
                 grossRangeFailAbove,
                 grossRangeSuspectBelow,
                 grossRangeSuspectAbove,
                 flatLineTolerance,
                 flatLineSuspectThreshold,
                 flatLineFailThreshold,
                 rateOfChangeThreshold,
                 spikeSuspectThreshold,
                 spikeFailThreshold):
    global qc_config
    global timeLimit_NEMS
    global decimalReq_NEMS
    global accuThresh_NEMS
    global accuBWidth_NEMS
    
    # QC configuration
    # For sea water temperature in degrees C
    # This configuration is used to call the corresponding method in the ioos_qc library
    # See documentation for description of each test and its inputs:
    #   https://ioos.github.io/ioos_qc/api/ioos_qc.html#module-ioos_qc.qartod
    qc_config = {
        'qartod': {
          "gross_range_test": {
            "fail_span": [grossRangeFailBelow, grossRangeFailAbove], #[5,25],
            "suspect_span": [grossRangeSuspectBelow, grossRangeSuspectAbove], #[10,22]
          },
          "flat_line_test": {
            "tolerance": flatLineTolerance, #0.001,
            "suspect_threshold": flatLineSuspectThreshold, #10800, #3 hours
            "fail_threshold": flatLineFailThreshold, #21600     #6 hours - semi diurnal changes
          },
            "rate_of_change_test": {
            "threshold": rateOfChangeThreshold, #0.001
          },
          "spike_test": {
            "suspect_threshold": spikeSuspectThreshold, #0.8,
            "fail_threshold": spikeFailThreshold #3
          },
          "aggregate": {}
        }
    }
    
    #NEMS tests config goes here
    ##data gap
    timeLimit_NEMS = timeGap #15 #minutes
    decimalReq_NEMS = resolution #1
    accuThresh_NEMS = accuracyThreshold
    accuBWidth_NEMS = accuracyBandwidth

    
###-------------------------------------------------------------------------------------
# This section here deals with all the plotting functions
# The implementation is not finalised yet, so please don't use it
###-------------------------------------------------------------------------------------
# Method to plot QC results using Bokeh
#plot_results(data, myMeasurement, qc_results, title, 'NEMS_gapData')
def plot_results(data, var_name, results, title, test_name):
    if data.empty:
        print("Plot have no data associated with it")

    time = data['timestamp']
    obs = data[var_name]
    qc_test = results['qartod'][test_name]

    qc_pass = np.ma.masked_where(qc_test != 1, obs)
    qc_suspect = np.ma.masked_where(qc_test != 3, obs)
    qc_fail = np.ma.masked_where(qc_test != 4, obs)
    qc_notrun = np.ma.masked_where(qc_test != 2, obs)

    p1 = figure(x_axis_type="datetime", title=test_name + ' : ' + title)
    p1.grid.grid_line_alpha=0.3
    p1.xaxis.axis_label = 'Time'
    p1.yaxis.axis_label = 'Observation Value'

    p1.line(time, obs,  legend_label='obs', color='#A6CEE3')
    p1.circle(time, qc_notrun, size=2, legend_label='qc not run', color='gray', alpha=0.2)
    p1.circle(time, qc_pass, size=4, legend_label='qc pass', color='green', alpha=0.5)
    p1.circle(time, qc_suspect, size=4, legend_label='qc suspect', color='orange', alpha=0.7)
    p1.circle(time, qc_fail, size=6, legend_label='qc fail', color='red', alpha=1.0)

    #output_file("qc.html", title="qc example")
    show(gridplot([[p1]], )) #plot_width=800, plot_height=400))

def doExtraPlots(detailedPlot, myData):
    if detailedPlot=="accuracy":
        clear_output(wait=True)
        p1.cross(myData["x"],myData["y"], line_width=5)
        show(gridplot([[p1]], ))
    
# the following are the actual interfaces made available for plotting
def doTestPlots(x="aggregate"):

    global data
    #print(data.dtypes)
    
    try:
        if x=="gap data":
            title = "NEMS gapData - "+mySite+" HBRC"
            plot_results(data, myMeasurement, qc_results, title, 'NEMS_gapData')
        elif x=="resolution":
            title = "NEMS resolution - "+mySite+" HBRC"
            plot_results(data, myMeasurement, qc_results, title, 'NEMS_resolution')
        elif x=="accuracy":
            title = "NEMS accuracy - "+mySite+" HBRC"
            plot_results(data, myMeasurement, qc_results, title, 'NEMS_accuracy')
            
            if extraPlotsPlease != None :
                doExtraPlots(extraPlotsPlease, extraPlotData)
            
        elif x=="gross range":
            title = myMeasurement + " gross range test - "+mySite+" HBRC"
            plot_results(data, myMeasurement, qc_results, title, 'gross_range_test')
        elif x=="flat line":
            title = myMeasurement +" flat line test - "+mySite+" HBRC"
            plot_results(data, myMeasurement, qc_results, title, 'flat_line_test')
        elif x=="rate of change":
            title = myMeasurement +" rate of change test - "+mySite+" HBRC"
            plot_results(data, myMeasurement, qc_results, title, 'rate_of_change_test')
        elif x=="spike":
            title = myMeasurement +" spike test - "+mySite+" HBRC"
            plot_results(data, myMeasurement, qc_results, title, 'spike_test')
        else :#if x=="aggregate":
            # QC Aggregate flag
            title = myMeasurement +" aggregate - "+mySite+" HBRC"
            plot_results(data, myMeasurement, qc_results, title, 'aggregate')

    except Exception as e :
        print("Please run the tests first, thanks\n",e, 'is the Error !#')
        print('This error might occur when the program is run in batch mode')
        #print(data.head())

def plotStats():
    global p
    clear_output(wait=True)
    
    myTests = qc_results['qartod'].keys()
    myFlags = [x for x in dir(qFlags) if ('_' not in x)] #assuming _ words are restricted
    x = [ (test, flags) for test in myTests for flags in myFlags ]
    
    counts = []
    for y in x:
        counts.append(len([x for x in qc_results['qartod'][y[0]] if x == getattr(qFlags,y[1])])/len(qc_results['qartod'][y[0]])*100)
    
    source = ColumnDataSource(data=dict(x=x,counts=counts))
    
    p = figure(x_range=FactorRange(*x), plot_height=350, title="Percentage of flag types for each test case",
            )
    
    palette = ["red","green","azure","orange","grey"]
    p.vbar(x='x', top='counts', width=0.85, source=source, line_color="white",
        fill_color=factor_cmap('x', palette=palette, factors=myFlags, start=1, end=2))
    
    p.y_range.start = 0
    p.x_range.range_padding = 0.1
    p.xaxis.major_label_orientation = 1
    p.xgrid.grid_line_color = None
    p.plot_width = 1200
    
    show(p)
    
###-------------------------------------------------------------------------------------
# The idea here is to send the outputs to an interested party
# The implementation is not finalised yet, so please don't use it
###-------------------------------------------------------------------------------------
def emailResult():
    emailId = False #disabled for now till we figure out the hbrc smtp or something else
    if emailId:
        output_file(mySite+'-'+myMeasurement+".html")
        save(p)
        
        import smtplib, ssl
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart

        sender_email = "karunakar.kintada@hbrc.govt.nz"
        receiver_email = emailId
        password = pswd #input("Type your password and press enter:")

        message = MIMEMultipart("alternative")
        message["Subject"] = "Report on site QARTOD-NEMS tests - reg"
        message["From"] = sender_email
        message["To"] = receiver_email

        # Create the plain-text and HTML version of your message
        text = """Please check the validation of the datasets"""
        html = open(mySite+'-'+myMeasurement+".html", "r").read()
        
        # Turn these into plain/html MIMEText objects
        part1 = MIMEText(text, "plain")
        part2 = MIMEText(html, "html")

        # Add HTML/plain-text parts to MIMEMultipart message
        # The email client will try to render the last part first
        message.attach(part1)
        message.attach(part2)
    
        # Create secure connection with server and send email
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("outlook.office365.com", 995,context=context) as server:
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, message.as_string())