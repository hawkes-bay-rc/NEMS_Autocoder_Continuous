#interactive sessions
from ipywidgets import interact, interactive, fixed, interact_manual, Layout
from datetime import datetime
import ipywidgets as widgets
import pandas as pd
import requests
import xml.etree.ElementTree as ET
import json
import csv
import os

from bokeh.layouts import gridplot
from bokeh.plotting import figure, show, output_notebook
from bokeh.models import ColumnDataSource, FactorRange, HoverTool
from bokeh.transform import factor_cmap
from bokeh.io import push_notebook

import tsData_utils as tsu
import tsAnalysis as ta
import config as config

#clear the plots before new ones
from IPython.display import clear_output, display, Markdown


# Added hilltop library
#from hilltoppy import web_service as ws
# Development version (local)
#import web_service as ws

style = {'description_width': '70%'}
# Set wider column width to prevent truncation of strings
pd.options.display.max_colwidth = 100

"""
apiOptions = widgets.Dropdown(options=['Telemetry','All Sites'],value="All Sites")

apiRoot = "https://data.hbrc.govt.nz/EnviroData/EMAR.hts?service=Hilltop"
def selectStatApi(api):
    if api == 'Telemetry':
        apiRoot="https://data.hbrc.govt.nz/EnviroData/Telemetry.hts?service=Hilltop"
    else :
        apiRoot="https://data.hbrc.govt.nz/EnviroData/EMAR.hts?service=Hilltop" #don't know why EMAR

#some widgets to be dynamically filled def's here
"""
import nemsQc as nq

#get all the sites for requisite measurement type
#sites = []


#Holder function for interactive widget
def statusFunction(Status):
    return Status


def getDefaults():
    # Open the run log
    runs = pd.read_csv('Logs/runLog.csv')
    # Get the current user
    user = os.getlogin()
    # Filter to the latest run for the current user
    runs = runs[runs['User']==user]
    latest = runs.tail(1)
    # If there is a latest run use it, otherwise use config file defaults
    if len(latest) > 0:
        defaults = {
            "server": latest['Server'].to_string(index=False),
            "file": latest['File'].to_string(index=False),
            "site": latest['Site'].to_string(index=False),
            "measurement": latest['Measurement'].to_string(index=False),
            "startTime": latest['StartTime'].to_string(index=False),
            "endTime": latest['EndTime'].to_string(index=False),
            "checkServer": latest['checkServer'].to_string(index=False),
            "checkFile": latest['checkFile'].to_string(index=False),
            "checkSite": latest['checkSite'].to_string(index=False),
            "checkMeasurement": latest['checkMeasurement'].to_string(index=False),
            "checkServer2": latest['checkServer'].to_string(index=False), # note same as data server
            "checkFile2": latest['checkFile2'].to_string(index=False),
            "checkSite2": latest['checkSite2'].to_string(index=False),
            "checkMeasurement2": latest['checkMeasurement2'].to_string(index=False),
        }
    else:
        defaults = {
            "server": config.serverBase,
            "file": config.serverFile,
            "site": config.defaultSite,
            "measurement": "",
            "startTime": config.startDate,
            "endTime": config.endDate,
            "checkServer": config.serverBase,
            "checkFile": config.checkFile,
            "checkSite": config.defaultSite,
            "checkMeasurement": "",
            "checkServer2": "",
            "checkFile2": "",
            "checkSite2": "",
            "checkMeasurement2": "",
        }
    
    return defaults


defaults = getDefaults()

qc_df = pd.DataFrame()

# Set the initial options
serverOptions = widgets.Text(value=defaults["server"], description="Server")
fileOptions = widgets.Dropdown(options=config.serverList, 
                               value=defaults["file"], 
                               description="File")
siteOptions = widgets.Combobox(options=tsu.getSiteList(requestType=config.requestType, 
                                                   base_url=serverOptions.value, 
                                                   file=fileOptions.value), 
                               value=defaults["site"])


#serverOptions = widgets.Text(value=config.serverBase, description="Server")
#serverOptions = widgets.Text(value="https://data.hbrc.govt.nz/EnviroData/", description="Server")
# fileOptions = widgets.Text(value="EMAR.hts", description="File")
#fileOptions = widgets.Text(value="Telemetry.hts", description="File")
#fileOptions = widgets.Dropdown(options=config.serverList, 
#                               value=config.serverFile, 
#                               description="File")

#siteOptions = widgets.Dropdown(options=sites,value="HAWQi")
#siteOptions = widgets.Dropdown(options=ws.site_list(serverOptions.value, 
#                                                    fileOptions.value)['SiteName'].tolist(), value='HAWQi')
#siteOptions = widgets.Dropdown(options=tsu.getSiteList(requestType='Hilltop', 
#siteOptions = widgets.Combobox(options=tsu.getSiteList(requestType=config.requestType, 
#                                                   base_url=serverOptions.value, 
#                                                   file=fileOptions.value), 
#                               value=config.defaultSite)
#                               value='HAWQi')
#measurementOptions = widgets.Dropdown(options=ws.measurement_list(serverOptions.value, 
#                                                                  fileOptions.value, 
#                                                                  site='HAWQi').index.get_level_values('Measurement').tolist())
#measurementOptions = widgets.Dropdown(options=tsu.getMeasurementList(requestType='Hilltop', 
measurementOptions = widgets.Combobox(options=tsu.getMeasurementList(requestType=config.requestType, 
                                                                 base_url=serverOptions.value, 
                                                                 file=fileOptions.value, 
                                                                 site=siteOptions.value)
                                     ,value = defaults["measurement"])
                                                                  #site='HAWQi')    
#Check data options
# Sites and measurements come from optionsList and server calls


def getOptionList(fieldName='Site'):
    #Takes a type of Site, Measurement, CheckSite or CheckMeasurement and returns a list of distinct values from the optionsList
    if fieldName in ['Site', 'Measurement', 'checkSite', 'checkMeasurement','checkSite2', 'checkMeasurement2']:
        #Import the options list
        optionsList = pd.read_csv('optionsList.csv')
        # Get the list of unique values from the column.
        return set(optionsList[fieldName].dropna().tolist())
    else:
        raise NameError('Acceptable fieldNames are Site, Measurement, checkSite, checkMeasurement, checkSite2, checkMeasurement2.')

  
checkServerOptions = widgets.Text(value=serverOptions.value, description="Server")
checkFileOptions = widgets.Dropdown(options=config.checkFileList, 
                                    value=defaults["checkFile"], 
                                    #value=config.checkFile, 
                                    description="File")
#checkFileOptions = widgets.Text(value="EMARContinuousCheck.hts", description="File")

# Need to add the checkSites from the optionsList file here too (without NaN)

#serverCheckSites = ws.site_list(checkServerOptions.value, checkFileOptions.value)['SiteName'].tolist()
#serverCheckSites = tsu.getSiteList(requestType='Hilltop', base_url=checkServerOptions.value, file=checkFileOptions.value) 
serverCheckSites = tsu.getSiteList(requestType=config.requestType, base_url=checkServerOptions.value, file=checkFileOptions.value) 

extraCheckSites = list(getOptionList(fieldName='checkSite') - set(serverCheckSites))
#checkSiteOptions = widgets.Dropdown(options=(serverCheckSites + extraCheckSites), value='HAWQi')
checkSiteOptions = widgets.Combobox(options=(serverCheckSites + extraCheckSites), 
                                    value=defaults["checkSite"])
                                    #value=config.defaultSite)

# Need to add the checkMeasurements from the optionsList file here too (without NaN)
#serverCheckMeasurements = ws.measurement_list(checkServerOptions.value, 
#                                                                  checkFileOptions.value, 
#                                                                  site='HAWQi', 
#                                                                  tstype='All').index.get_level_values('Measurement').tolist()
#serverCheckMeasurements = tsu.getMeasurementList(requestType='Hilltop', 
serverCheckMeasurements = tsu.getMeasurementList(requestType=config.requestType, 
                                             base_url=checkServerOptions.value, 
                                             file=checkFileOptions.value, 
                                             #site='HAWQi', 
                                             site=checkSiteOptions.value,
                                             tstype='All')
extraCheckMeasurements = list(getOptionList(fieldName='checkMeasurement') - set(serverCheckMeasurements))
checkMeasurementOptions = widgets.Combobox(options=(serverCheckMeasurements + extraCheckMeasurements),
                                          value=defaults["checkMeasurement"])

#Secondary Check Data Checkbox
chk2Box = widgets.Checkbox(
    value=False,
    description='Extra Check Data',
    disabled=False,
    indent=False
)

# Add options for a second check measurement, could be from a different service, set to blank for all
checkServerOptions2 = widgets.Text(value=defaults["checkServer2"], description="Server")

checkFileOptions2 = widgets.Combobox(options=config.checkFileList, value=defaults["checkFile2"], description="File")

# Check if there is a second check measurement server and file, if not default to blank lists
if(checkServerOptions2.value == "" or checkFileOptions2.value =="" or checkFileOptions2.value == None):
    
    #set options to blank lists
    #serverCheckSites2 = [""]
    #extraCheckSites2 = [""]
    # Site list 
    checkSiteOptions2 = widgets.Combobox(options=[""], value="")
    #serverCheckMeasurements2 = [""]
    #extraCheckMeasurements = [""]
    # Measurement list
    checkMeasurementOptions2 = widgets.Combobox(options=[""])
    checkFileOptions2.layout.visibility = 'hidden'
    checkSiteOptions2.layout.visibility = 'hidden'
    checkMeasurementOptions2.layout.visibility = 'hidden'
    chk2Box.value = False
else:
    #Get list for sites list drop down
    
    serverCheckSites2 = tsu.getSiteList(requestType=config.requestType, base_url=checkServerOptions2.value, file=checkFileOptions2.value) 
    extraCheckSites2 = list(getOptionList(fieldName='checkSite2') - set(serverCheckSites))
    # Site list 
    checkSiteOptions2 = widgets.Combobox(options=(serverCheckSites2 + extraCheckSites2))
    #Get list options for second check measurement
    serverCheckMeasurements2 = tsu.getMeasurementList(requestType=config.requestType, 
                                             base_url=checkServerOptions2.value, 
                                             file=checkFileOptions2.value, 
                                             #site='HAWQi', 
                                             site=checkSiteOptions2.value,
                                             tstype='All')
    extraCheckMeasurements2 = list(getOptionList(fieldName='checkMeasurement2') - set(serverCheckMeasurements2))
    # Measurement list
    checkMeasurementOptions2 = widgets.Combobox(options=(serverCheckMeasurements2 + extraCheckMeasurements2))
    chk2Box.value = True



# NEMS Options
nemsopt = pd.read_csv('NEMS_Continuous_Parameters.csv')
nemsStd = widgets.Dropdown(options=pd.unique(nemsopt['NEMS_Standard']).tolist(), value='Not Available')
#resolution = widgets.IntText(value=1,style=style)
#timeGap = widgets.IntText(value=15,style=style)
#accuracyThreshold = widgets.FloatText(value=0.8,style=style)
#accuracyBandwidth = widgets.IntText(value=5,style=style)

# Qartod Options
#grfbSlot = widgets.IntText(value=5,style=style)
#grfaSlot = widgets.IntText(value=25,style=style)
#grsbSlot = widgets.IntText(value=10,style=style)
#grsaSlot = widgets.IntText(value=22,style=style)
grfbSlot = widgets.FloatText(value=5,style=style)
grfaSlot = widgets.FloatText(value=25,style=style)
grsbSlot = widgets.FloatText(value=10,style=style)
grsaSlot = widgets.FloatText(value=22,style=style)

fltSlot = widgets.FloatText(value=0.001,style=style)
rocSlot = widgets.FloatText(value=0.001,style=style)

flatLineSuspectThreshold = widgets.IntText(value=10800,style=style)
flatLineFailThreshold = widgets.IntText(value=21600,style=style)

spikeSuspectThreshold = widgets.FloatText(value=0.33,style=style)
spikeFailThreshold = widgets.FloatText(value=1,style=style)

#sDate = widgets.DatePicker(value=pd.to_datetime('2020-01-01'))
#eDate = widgets.DatePicker(value=pd.to_datetime('2020-02-01'))

#sDate = widgets.DatePicker(value=datetime.strptime("2020-01-01", "%Y-%m-%d"))
#eDate = widgets.DatePicker(value=datetime.strptime("2020-02-01", "%Y-%m-%d"))

#sDate = widgets.DatePicker(value=datetime.strptime(config.startDate, "%Y-%m-%d"))
#eDate = widgets.DatePicker(value=datetime.strptime(config.endDate, "%Y-%m-%d"))
                                                   
sDate = widgets.DatePicker(value=datetime.strptime(defaults["startTime"].split()[0], "%Y-%m-%d"))
eDate = widgets.DatePicker(value=datetime.strptime(defaults["endTime"].split()[0], "%Y-%m-%d"))

# Processing Options
interpolationFlag = widgets.Checkbox(value=False, description='Interpolate', disabled=False, indent=True)
    
gapThreshold = widgets.IntText(value=10800,style=style)
interpolationAllowance = widgets.IntText(value=5,style=style)

maxCodeOptions = widgets.Dropdown(options=['600', '500', '400', '200'], 
                                  value='600')      

# Status
optStatus = widgets.HTML(value="Default Options")

defaultSaveStatus = '<b style="color:orange;">Options not saved.<b>'
saveStatus = widgets.HTML(value=defaultSaveStatus)

# Define a data Selector for use in the Jupyter Notebook
def siteSelector(Server, File, Site,Measurement,StartDate,EndDate):
    global myServer
    myServer = Server
    global myFile
    myFile = File
    global mySite
    mySite = Site
    print('please wait for the right options to load')
    global myMeasurement
    myMeasurement = Measurement
    global myStartDate
    global myEndDate
    myStartDate = str(StartDate)
    myEndDate = str(EndDate)
    #if mySite and myMeasurement and myStartDate and myEndDate :
    #    fetchData()
    
        
#Define a check data selector for use in the Jupyter Notebook       
def checkSelector(Server, File, Site, Measurement):
    global chServer
    chServer = Server
    global chFile
    chFile = File
    global chSite
    chSite = Site
    #print('please wait for the right options to load')
    global chMeasurement
    chMeasurement = Measurement
    #global myStartDate
    #global myEndDate
    #myStartDate = str(StartDate)
    #myEndDate = str(EndDate)
    #if chSite and chMeasurement and myStartDate and myEndDate :
    #    fetchCheckData()

    
#Define a secod check data selector for use in the Jupyter Notebook, assume same server     
def checkSelector2(File, Site, Measurement):
    #global chServer
    #chServer = Server
    global chFile2
    chFile2 = File
    global chSite2
    chSite2 = Site
    #print('please wait for the right options to load')
    global chMeasurement2
    chMeasurement2 = Measurement
    

def processingSelector(GapThreshold, InterpolationAllowance, MaxQCCode):
    #global prInterpolation
    #prInterpolation = Interpolation
    global prGapThreshold
    prGapThreshold = GapThreshold
    global prInterpolationAllowance
    prInterpolationAllowance = InterpolationAllowance
    global prMaxCode
    prMaxCode = MaxQCCode
    
# Define functions that update the site and measurement lists

def updateSites(change):
    if change['old'] == change['new']:
        return
    siteOptions.disabled = True
    runBtn.disabled = True
    #Change save status value to default, options changed
    saveStatus.value = defaultSaveStatus
    
    sitelist = tsu.getSiteList(requestType='Hilltop', 
                           base_url=serverOptions.value, 
                           file=fileOptions.value)
    #sitedf = ws.site_list(base_url=serverOptions.value, hts=fileOptions.value)               
    #siteOptions.index = None
    #siteOptions.options = sitedf['SiteName'].tolist()
    siteOptions.options = sitelist                                  
    if "HAWQi" in siteOptions.options:
        siteOptions.value = "HAWQi"
    
    siteOptions.disabled = False
    runBtn.disabled = False



def updateMsmt(change):
    if change['old'] == change['new']:
        return
    measurementOptions.disabled = True
    runBtn.disabled = True
    
    #Change save status value to default, options changed
    saveStatus.value = defaultSaveStatus
    # measurementOptions.options = measList(siteOptions.value)
    # measdf = ws.measurement_list(base_url, hts, siteOptions.value)
    if siteOptions.value:
        # measdf = ws.measurement_list(base_url=serverOptions.value, hts=fileOptions.value, site=siteOptions.value)
        # measurementOptions.index = None
        # measurementOptions.options = measdf.index.get_level_values('Measurement').tolist()
        measlist = tsu.getMeasurementList(requestType='Hilltop', 
                                      base_url=serverOptions.value, 
                                      file=fileOptions.value, 
                                      site=siteOptions.value)
        measurementOptions.options = measlist
        
        #Modify check measurement too
        if siteOptions.value in checkSiteOptions.options:
            # Set site to the same as the data one
            checkSiteOptions.value = siteOptions.value
        else:
            # Set the site blank
            checkSiteOptions.value = ""
            
        #Modify secondary check measurement too
        if siteOptions.value in checkSiteOptions2.options:
            # Set site to the same as the data one
            checkSiteOptions2.value = siteOptions.value
        else:
            # Set the file and site blank
            checkFileOptions2.value = ""
            checkSiteOptions2.value = ""
    
    measurementOptions.disabled = False
    runBtn.disabled = False
    

def updateCheckSites(change):
    if change['old'] == change['new']:
        return
    checkSiteOptions.disabled = True
    runBtn.disabled = True
    #Change save status value to default, options changed
    saveStatus.value = defaultSaveStatus
    # checksitedf = ws.site_list(base_url=checkServerOptions.value, hts=checkFileOptions.value)
    # checksitelist = ws.site_list(base_url=checkServerOptions.value, hts=checkFileOptions.value)['SiteName'].tolist()
    checksitelist = tsu.getSiteList(requestType='Hilltop', base_url=checkServerOptions.value, file=checkFileOptions.value)
    checkSiteOptions.index = None
    #checkSiteOptions.options = checksitedf['SiteName'].tolist()
    # The sites and or measurements can have [] in them so create variable to allow combination
    extraCheckSites = list(getOptionList(fieldName='checkSite') - set(checksitelist))
    checkSiteOptions.options = checksitelist + extraCheckSites
    if "HAWQi" in checkSiteOptions.options:
        checkSiteOptions.value = "HAWQi"
    
    checkSiteOptions.disabled = False
    runBtn.disabled = False



def updateCheckMsmt(change):
    if change['old'] == change['new']:
        return
    checkMeasurementOptions.disabled = True
    runBtn.disabled = True
    #Change save status value to default, options changed
    saveStatus.value = defaultSaveStatus
    #measurementOptions.options = measList(siteOptions.value)
    #measdf = ws.measurement_list(base_url, hts, siteOptions.value)
    if checkSiteOptions.value:
        #checkmeasdf = ws.measurement_list(base_url=checkServerOptions.value, 
        #                                  hts=checkFileOptions.value, 
        #                                  site=checkSiteOptions.value, 
        #                                  tstype='All')
        #checkmeaslist = ws.measurement_list(base_url=checkServerOptions.value, 
        #                                  hts=checkFileOptions.value, 
        #                                  site=checkSiteOptions.value, 
        #                                  tstype='All').index.get_level_values('Measurement').tolist()
        checkmeaslist = tsu.getMeasurementList(requestType='Hilltop', 
                                           base_url=checkServerOptions.value, 
                                           file=checkFileOptions.value, 
                                           #site='HAWQi', 
                                           site=checkSiteOptions.value,
                                           tstype='All')
        checkMeasurementOptions.index = None
        #checkMeasurementOptions.options = checkmeasdf.index.get_level_values('Measurement').tolist()
        extraCheckMeasurements = list(getOptionList(fieldName='checkMeasurement') - set(checkmeaslist))
        checkMeasurementOptions.options = checkmeaslist + extraCheckMeasurements
    
    checkMeasurementOptions.disabled = False
    runBtn.disabled = False

    
def updateCheckSites2(change):
    if change['old'] == change['new']:
        return
    checkSiteOptions2.disabled = True
    runBtn.disabled = True
    #Change save status value to default, options changed
    saveStatus.value = defaultSaveStatus
    # checksitedf = ws.site_list(base_url=checkServerOptions.value, hts=checkFileOptions.value)
    # checksitelist = ws.site_list(base_url=checkServerOptions.value, hts=checkFileOptions.value)['SiteName'].tolist()
    if checkFileOptions2.value == "" or checkFileOptions2.value == None:
        checkSiteOptions2.value = ""
    else:
        checksitelist2 = tsu.getSiteList(requestType='Hilltop', base_url=checkServerOptions.value, file=checkFileOptions2.value)
        checkSiteOptions2.index = None
        #checkSiteOptions.options = checksitedf['SiteName'].tolist()
        # The sites and or measurements can have [] in them so create variable to allow combination
        extraCheckSites2 = list(getOptionList(fieldName='checkSite2') - set(checksitelist2))
        checkSiteOptions2.options = checksitelist2 + extraCheckSites2
        if "HAWQi" in checkSiteOptions2.options:
            checkSiteOptions2.value = "HAWQi"
    
    checkSiteOptions2.disabled = False
    runBtn.disabled = False



def updateCheckMsmt2(change):
    if change['old'] == change['new']:
        return
    checkMeasurementOptions2.disabled = True
    runBtn.disabled = True
    #Change save status value to default, options changed
    saveStatus.value = defaultSaveStatus
    #measurementOptions.options = measList(siteOptions.value)
    #measdf = ws.measurement_list(base_url, hts, siteOptions.value)
    if checkSiteOptions2.value:
        # Make sure check box ticked, so all visible
        chk2Box.value = True
        
        #checkmeasdf = ws.measurement_list(base_url=checkServerOptions.value, 
        #                                  hts=checkFileOptions.value, 
        #                                  site=checkSiteOptions.value, 
        #                                  tstype='All')
        #checkmeaslist = ws.measurement_list(base_url=checkServerOptions.value, 
        #                                  hts=checkFileOptions.value, 
        #                                  site=checkSiteOptions.value, 
        #                                  tstype='All').index.get_level_values('Measurement').tolist()
        checkmeaslist2 = tsu.getMeasurementList(requestType='Hilltop', 
                                           base_url=checkServerOptions.value, 
                                           file=checkFileOptions2.value, 
                                           #site='HAWQi', 
                                           site=checkSiteOptions2.value,
                                           tstype='All')
        checkMeasurementOptions2.index = None
        #checkMeasurementOptions.options = checkmeasdf.index.get_level_values('Measurement').tolist()
        extraCheckMeasurements2 = list(getOptionList(fieldName='checkMeasurement2') - set(checkmeaslist2))
        checkMeasurementOptions2.options = checkmeaslist2 + extraCheckMeasurements2
    else:
        #If no site set measurement to blank
        checkMeasurementOptions2.index = None
    
    checkMeasurementOptions2.disabled = False
    runBtn.disabled = False
    
    
"""    
def updateRange(*args):
    grfbVal, grfaVal, grsbVal, grsaVal = getMsmtPDist(siteOptions.value,
                            measurementOptions.value,
                            sDate.value, eDate.value)
    
    grfbSlot.value = grfbVal
    grfaSlot.value = grfaVal
    grsbSlot.value = grsbVal
    grsaSlot.value = grsaVal
    
    rocSlot.value = getAnnMinMax(siteOptions.value,
                                        measurementOptions.value,
                                        sDate.value, eDate.value)
"""    

def updateOptions(change):
    if change['old'] == change['new']:
        return
    checkSiteOptions.disabled = True
    checkMeasurementOptions.disabled = True
    runBtn.disabled = True
    #Change save status value to default, options changed
    saveStatus.value = defaultSaveStatus
        
    # Read the options from the csv file
    opt = pd.read_csv('optionsList.csv')
    se = serverOptions.value
    f = fileOptions.value
    s = siteOptions.value
    m = measurementOptions.value
    
    # Change check measurement values to None
    checkMeasurementOptions.value = ""
    checkMeasurementOptions2.value = ""
    checkFileOptions2.value = ""
    checkSiteOptions2.value = ""
    
    subset = opt[(opt['Server']==se) & (opt['File']==f) & (opt['Site']==s) & (opt['Measurement']==m)]
    if len(subset) > 0:
        opt_latest = subset.tail(1)
        optStatus.value = '<b style="color:green;">Latest options loaded<b>'
        #print("Latest options loaded")
    
    else:
        #print("No saved options, checking for measurement defaults.")
        optStatus.value = '<b>No saved options, checking for measurement defaults.<b>'
        default = opt[(opt['Site']=='Default') & (opt['Measurement']==m)]
        if len(default) > 0:
            optStatus.value = '<b style="color:orange;">Default options loaded, please check and change if required.<b>'
            opt_latest = default.tail(1)
        
        else:
            #print("No default options, please manually define.")
            optStatus.value = '<b style="color:red;">No default options, please manually define.<b>'
            opt_latest = pd.DataFrame()

    if len(opt_latest) == 1:
        # If there are entries for check data then load them
        if not pd.isna(opt_latest['checkServer']).any():
            checkServerOptions.value = opt_latest['checkServer'].to_string(index=False) 
        if not pd.isna(opt_latest['checkFile']).any():    
            checkFileOptions.value = opt_latest['checkFile'].to_string(index=False) 
        if not pd.isna(opt_latest['checkSite']).any():    
            checkSiteOptions.value = opt_latest['checkSite'].to_string(index=False) 
        if not pd.isna(opt_latest['checkMeasurement']).any():    
            checkMeasurementOptions.value = opt_latest['checkMeasurement'].to_string(index=False) 
        if not pd.isna(opt_latest['checkFile2']).any():    
            checkFileOptions2.value = opt_latest['checkFile2'].to_string(index=False) 
        if not pd.isna(opt_latest['checkSite2']).any():    
            checkSiteOptions2.value = opt_latest['checkSite2'].to_string(index=False) 
        if not pd.isna(opt_latest['checkMeasurement2']).any():    
            checkMeasurementOptions2.value = opt_latest['checkMeasurement2'].to_string(index=False) 
        nemsStd.value = opt_latest['nemsStandard'].to_string(index=False)  
        #resolution.value = opt_latest['resolution']
        #timeGap.value = opt_latest['timeGap']
        #accuracyThreshold.value = opt_latest['accuracyThreshold']
        #accuracyBandwidth.value = opt_latest['accuracyBandwidth']
        grfbSlot.value = opt_latest['grossRangeFailBelow']
        grfaSlot.value = opt_latest['grossRangeFailAbove']
        grsbSlot.value = opt_latest['grossRangeSuspectBelow']
        grsaSlot.value = opt_latest['grossRangeSuspectAbove']
        fltSlot.value = opt_latest['flatLineTolerance']
        flatLineSuspectThreshold.value = opt_latest['flatLineSuspectThreshold']
        flatLineFailThreshold.value = opt_latest['flatLineFailThreshold']
        rocSlot.value = opt_latest['rateOfChangeThreshold']
        spikeSuspectThreshold.value = opt_latest['spikeSuspectThreshold']
        spikeFailThreshold.value = opt_latest['spikeFailThreshold']
        interpolationFlag.value = False if opt_latest['interpolate'].to_string(index=False) == 'False' else True
        gapThreshold.value = opt_latest['processGapThreshold']
        interpolationAllowance.value = opt_latest['processIntAllowance']
        
        if 'maxCode' in opt_latest:
            if not pd.isna(opt_latest['maxCode']).any():    
                maxCodeOptions.value = opt_latest['maxCode'].to_string(index=False)
        
        
    
    checkSiteOptions.disabled = False
    checkMeasurementOptions.disabled = False
    runBtn.disabled = False
    

def updateCheckOptions2(change):
    if change['old'] == change['new']:
        return
    #Change save status value to default, options changed
    saveStatus.value = defaultSaveStatus
    if chk2Box.value:
        checkFileOptions2.layout.visibility = 'visible'
        checkSiteOptions2.layout.visibility = 'visible'
        checkMeasurementOptions2.layout.visibility = 'visible'
    else:
        checkFileOptions2.layout.visibility = 'hidden'
        checkSiteOptions2.layout.visibility = 'hidden'
        checkMeasurementOptions2.layout.visibility = 'hidden'

    
fileOptions.observe(updateSites, 'value')    
siteOptions.observe(updateMsmt, 'value')
#measurementOptions.observe(updateRange)
measurementOptions.observe(updateOptions)


checkFileOptions.observe(updateCheckSites, 'value')    
checkSiteOptions.observe(updateCheckMsmt, 'value')

checkFileOptions2.observe(updateCheckSites2, 'value')    
checkSiteOptions2.observe(updateCheckMsmt2, 'value')

chk2Box.observe(updateCheckOptions2, 'value')

#siteOptions.change(updateMsmt)
#measurementOptions.change(updateOptions)

#Add save button to save the variables.
saveBtn = widgets.Button(description="Save")
#Add a run button to make sure that system is not overloaded by auto processing
runBtn = widgets.Button(description="Run")
output = widgets.Output()

#Add an output to csv button
outOptions = widgets.RadioButtons(
    options=['Clean', 'All'],
    value='Clean',
    # rows=10,
    description='Output Data:',
    disabled=False
)

outputBtn = widgets.Button(description="Output")

#Add a run button to make sure that system is not overloaded by auto processing
analysisBtn = widgets.Button(description="Analyse")
analysisOutput = widgets.Output()


def plotStats(qc_results, std='qartod'):
    #global p
    clear_output(wait=True)
    
    myTests = qc_results[std].keys()
    #myTests = qc_results['qartod'].keys()
    myFlags = [x for x in dir(nq.qFlags) if ('_' not in x)] #assuming _ words are restricted
    x = [ (test, flags) for test in myTests for flags in myFlags ]
    
    counts = []
    for y in x:
        #counts.append(len([x for x in qc_results['qartod'][y[0]] if x == getattr(qFlags,y[1])])/len(qc_results['qartod'][y[0]])*100)
        counts.append(len([x for x in qc_results[std][y[0]] if x == getattr(nq.qFlags,y[1])])/len(qc_results[std][y[0]])*100)
    
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
    
    #show(p)
    return p


def plot_results(data, title, test_name, chkData=pd.DataFrame()):
    if data.empty:
    #if qc_df.empty:
        print("Plot has no data associated with it")
        
    if chkData.empty: #== None:
        chkData = pd.DataFrame(columns=['DateTime', 'Measurement', 'Value'])
        
    # Create a plotting dataframe
    plot_df = data[['DateTime', 'Measurement', 'Value', 'OriginalValue', test_name]].copy()
    #plot_df = qc_df[['DateTime', 'Measurement', 'Value', test_name]].copy()
    plot_df.rename(columns={test_name:'Flag'}, inplace=True)
    
    qc_map = pd.DataFrame(data={'Flag': [1, 2, 3, 4, 9], 'QualityFlag': ['Good', 'Unknown', 'Suspect', 'Fail', 'Missing']})
    plot_df = pd.merge(plot_df, qc_map, how="left", on=["Flag"])
    #plot_df['Flag'].astype('str')
    #print(plot_df.dtypes)
    #print(plot_df.head())
    source = ColumnDataSource(data=plot_df)
    chkSource = ColumnDataSource(data=chkData[['DateTime', 'Value']].copy())
    
    measurementName = plot_df['Measurement'][0]
    
    result_cmap = factor_cmap('QualityFlag', \
                              palette=['green', 'black', 'orange', 'red', 'gray'], \
                              factors=['Good', 'Unknown', 'Suspect', 'Fail', 'Missing'])
        
    TOOLTIPS = [
        ("index", "$index"),
        ("time", "@DateTime{%F %T}"),
        ("value", "@OriginalValue{0.0000}"),
        ("Flag", "@QualityFlag"),
        ("Export value", "@Value{0.0000}"),
        ]

    p1 = figure(x_axis_type="datetime", \
                title=measurementName + " : " + title, \
                plot_height=500, \
                plot_width=900, \
                tools=['pan', 'box_zoom', 'wheel_zoom', 'undo', 'redo', 'reset', 'save'] \
                #source = source,\
                )
        
    #p1.toolbar.active_inspect = [hover, crosshair]
    p1.grid.grid_line_alpha=0.3
    p1.xaxis.axis_label = 'Time'
    p1.yaxis.axis_label = 'Observation Value'

    p1.line(x = 'DateTime', y = 'OriginalValue',  legend_label='Data', color='#A6CEE3', source=source)
    p1.circle(x = 'DateTime', y='OriginalValue', size=2, legend_field='QualityFlag', color=result_cmap, alpha=1, source=source)
    p1.diamond(x = 'DateTime', y='Value', size=4, legend_label='Check', color='black' , alpha=1, 
                  source=chkSource)
        
    p1.add_tools(HoverTool(tooltips=TOOLTIPS, formatters={'@DateTime': 'datetime', }))
    global res    
    res = show(gridplot([[p1]], ), notebook_handle=True) #plot_width=800, plot_height=400))
    return p1


"""
def doThePlots(x=None):
    if qc_df.empty: # == None:
        print("Please run the tests first")
        return
    try:
        if x=="gap data":
            title = "NEMS gapData - "+siteOptions.value+" HBRC"
            plot_results(data=qc_df, title=title, test_name='NEMS_gapData')
        elif x=="resolution":
            title = "NEMS resolution - "+siteOptions.value+" HBRC"
            plot_results(data=qc_df, title=title, test_name='NEMS_resolution')
        elif x=="verification frequency":
            title = "NEMS verification frequency - "+siteOptions.value+" HBRC"
            plot_results(data=qc_df, title=title, test_name='NEMS_verificationFreq')
        elif x=="verification accuracy":
            title = "NEMS verification accuracy - "+siteOptions.value+" HBRC"
            plot_results(data=qc_df, title=title, test_name='NEMS_verificationAccuracy')
            
            #if extraPlotsPlease != None :
            #    qb.doExtraPlots(extraPlotsPlease, extraPlotData)
            
        elif x=="gross range":
            title = "Gross range test - "+siteOptions.value+" HBRC"
            plot_results(data=qc_df, title=title, test_name='gross_range_test')
        elif x=="flat line":
            title = "Flat line test - "+siteOptions.value+" HBRC"
            plot_results(data=qc_df, title=title, test_name='flat_line_test')
        elif x=="rate of change":
            title = "Rate of change test - "+siteOptions.value+" HBRC"
            plot_results(data=qc_df, title=title, test_name='rate_of_change_test')
        elif x=="spike":
            title = "Spike test - "+siteOptions.value+" HBRC"
            plot_results(data=qc_df, title=title, test_name='spike_test')
        elif x=="aggregate":
            # QC Aggregate flag
            title = "Aggregate - "+siteOptions.value+" HBRC"
            plot_results(data=qc_df, title=title, test_name='aggregate')
        
        # Add in the NEMS plot options
        elif x=="All Data":
            # NEMS Plot, all data
            plot_NEMS_results(data=qc_df, data_set="all")
            
        elif x=="Clean Data":
            # NEMS Plot, all data
            plot_NEMS_results(data=qc_df, data_set="clean")
        

    except Exception as e :
        print("Please run the tests first, thanks",e)
"""
        
def doBasePlots(x="gross range"):
    if qc_df.empty: # == None:
        print("Please run the tests first")
        return
    try:
        if x=="gross range":
            title = "Gross range test - "+siteOptions.value+" HBRC"
            plot_results(data=qc_df, title=title, test_name='gross_range_test')
        elif x=="flat line":
            title = "Flat line test - "+siteOptions.value+" HBRC"
            plot_results(data=qc_df, title=title, test_name='flat_line_test')
        elif x=="rate of change":
            title = "Rate of change test - "+siteOptions.value+" HBRC"
            plot_results(data=qc_df, title=title, test_name='rate_of_change_test')
        elif x=="spike":
            title = "Spike test - "+siteOptions.value+" HBRC"
            plot_results(data=qc_df, title=title, test_name='spike_test')
        elif x=="aggregate":
            # QC Aggregate flag
            title = "Aggregate - "+siteOptions.value+" HBRC"
            plot_results(data=qc_df, title=title, test_name='aggregate')     

    except Exception as e :
        print("Please run the tests first, thanks",e)
        
        
def doNemsPlots(x="gap data"):
    if qc_df.empty: # == None:
        print("Please run the tests first")
        return
    try:
        if x=="gap data":
            title = "NEMS gapData - "+siteOptions.value+" HBRC"
            plot_results(data=qc_df, title=title, test_name='NEMS_gapData')
        elif x=="resolution":
            title = "NEMS resolution - "+siteOptions.value+" HBRC"
            plot_results(data=qc_df, title=title, test_name='NEMS_resolution')
        elif x=="verification frequency":
            title = "NEMS verification frequency - "+siteOptions.value+" HBRC"
            plot_results(data=qc_df, title=title, test_name='NEMS_verificationFreq', chkData=checkData)
        elif x=="verification accuracy":
            title = "NEMS verification accuracy - "+siteOptions.value+" HBRC"
            plot_results(data=qc_df, title=title, test_name='NEMS_verificationAccuracy', chkData=checkData)
            
            #if extraPlotsPlease != None :
            #    qb.doExtraPlots(extraPlotsPlease, extraPlotData)        

    except Exception as e :
        print("Please run the tests first, thanks",e)
        

def doOverallPlots(x="All Data"):
    if qc_df.empty: # == None:
        print("Please run the tests first")
        return
    try:
        if x=="All Data":
            # NEMS Plot, all data
            plot_NEMS_results(data=qc_df, data_set="all", chkData=checkData)
            
        elif x=="Clean Data":
            # NEMS Plot, all data
            plot_NEMS_results(data=qc_df, data_set="clean", chkData=checkData)
        

    except Exception as e :
        print("Please run the tests first, thanks",e)
        

def plot_NEMS_results(data, data_set, chkData=pd.DataFrame()):
    if data.empty: # == None:
        print("Please run the code first")
        return
    #global qc_df   
    
    if chkData.empty: #== None:
        chkData = pd.DataFrame(columns=['DateTime', 'Measurement', 'Value'])
    
    try:
        #qc_df = mapNEMScodes()
        
        if(data_set=="all"):
            #source = ColumnDataSource(data=qc_df)
            plotting_df = data[['DateTime', 'Measurement', 'Value', 'QC', 'Action', 'OriginalValue']].copy()
            #plotting_df = data.copy()
        elif(data_set=="clean"):
            #source = ColumnDataSource(data=qc_df[qc_df['Action']=="Keep"])
            plotting_df = data[data['Action'] != "Drop"].copy()
        else:
            #source = ColumnDataSource(data=qc_df)
            #plotting_df = data.copy()
            plotting_df = data[['DateTime', 'Measurement', 'Value', 'QC', 'Action', 'OriginalValue']].copy()
            print("Valid options are 'all' or 'clean'.  Showing all results.")
        
        source = ColumnDataSource(data=plotting_df)
        chkSource = ColumnDataSource(data=chkData[['DateTime', 'Value']].copy())
        
        qc_cmap = factor_cmap('QC', \
                              palette=['#8B5A00', '#D3D3D3', '#FFA500', '#00BFFF', '#006400'], \
                              factors=['200', '300', '400', '500', '600'])
        
        TOOLTIPS = [
            ("index", "$index"),
            ("time", "@DateTime{%F %T}"),
            ("value", "@Value{0.0000}"),
            ("QC", "@QC"),
            ("Original Value", "@OriginalValue{0.0000}"),
            ]

        p1 = figure(x_axis_type="datetime", \
                    title='Final NEMS Coded Results', \
                    plot_height=500, \
                    plot_width=900, \
                    tools=['pan', 'box_zoom', 'wheel_zoom', 'undo', 'redo', 'reset', 'save'] \
                    #source = source,\
                    )
        
        #p1.toolbar.active_inspect = [hover, crosshair]
        p1.grid.grid_line_alpha=0.3
        p1.xaxis.axis_label = 'Time'
        p1.yaxis.axis_label = 'Observation Value'

        p1.line(x = 'DateTime', y = 'Value',  legend_label='Value', color='#A6CEE3', source=source)
        #p1.circle(x = 'DateTime', y='Value', size=2, legend_field='QC', alpha=1, source=source)
        #p1.circle(x = 'DateTime', y='Value', size=2, legend_field='QC', color=qc_cmap , alpha=1, source=source)
        p1.circle(x = 'DateTime', y='Value', size=2, legend_field='QC', color=qc_cmap , alpha=1, \
                  source=ColumnDataSource(data=plotting_df.dropna()))
        p1.circle(x = 'DateTime', y='Value', size=3, legend_field='Action', color='#800080' , alpha=1, 
                  source=ColumnDataSource(data=plotting_df[plotting_df['Action']=="Drop"].dropna()))
        
        p1.diamond(x = 'DateTime', y='Value', size=4, legend_label='Check', color='black' , alpha=1, 
                  source=chkSource)
        
        p1.add_tools(HoverTool(tooltips=TOOLTIPS, formatters={'@DateTime': 'datetime', }))
        global nem
        nem = show(gridplot([[p1]], ), notebook_handle=True) #plot_width=800, plot_height=400))
    except Exception as e :
        print("Please run the tests first, thanks\n",e, 'is the Error !#')
        print('This error might occur when the program is run in batch mode')


def on_runBtn_clicked(b):
    output.clear_output()
    # Data Status
    
    #Save to runlog
    save_options(filename = 'Logs/runLog.csv')
    
    with output:
        dataStatus = widgets.HTML(value="Retrieving Data.  Please note that data is pulled pulled out live from the server and be patient.")
        display(dataStatus)
        #print("Please note that data is pulled pulled out live from the server and be patient.")
        #qb.runTests()
        #global data
        global checkData
        data = tsu.getData(requestType='Hilltop', 
                   base_url=serverOptions.value, 
                   file=fileOptions.value, 
                   site=siteOptions.value, 
                   measurement = measurementOptions.value, 
                   from_date=str(sDate.value), 
                   to_date=str(eDate.value))
    
        # Get the checkdata
        # global checkData
        # fetchCheckData()
        # Set check start date 3 months earlier than myStartDate
        chkStartDate = ((pd.to_datetime(str(sDate.value)) - pd.to_timedelta('90 days'))).strftime(format='%Y-%m-%d')
        
        #Bring in check data from primary and secondary and combine.
        checkData1 = tsu.getData(requestType='Hilltop', 
                            base_url=checkServerOptions.value, 
                            file=checkFileOptions.value, 
                            site=checkSiteOptions.value, 
                            measurement = checkMeasurementOptions.value, 
                            from_date=chkStartDate, 
                            to_date=str(eDate.value))
        
        # Get secondary check data if available
        if(checkFileOptions2.value == "" or checkSiteOptions2.value == "" or checkMeasurementOptions2.value == ""):
            checkData2 = pd.DataFrame()
        else:
            checkData2 = tsu.getData(requestType='Hilltop', 
                                base_url=checkServerOptions.value, 
                                file=checkFileOptions2.value, 
                                site=checkSiteOptions2.value, 
                                measurement = checkMeasurementOptions2.value, 
                                from_date=chkStartDate, 
                                to_date=str(eDate.value))
            
        #Combine the check datasets to a single check dataset.
        if(checkData2.empty):
            #No secondary check data so just use primary
            checkData = checkData1
        else:
            #Join the check datasets together and then order by DateTime
            checkData = pd.concat([checkData1, checkData2], ignore_index=True, sort=False)
            # Use DateTime as the index and sort it
            #checkData.set_index('DateTime', inplace = True)
            #checkData.sort_index(inplace = True)
        
        
        
        qc_config = nq.configParams_Q(grossRangeFailBelow=grfbSlot.value,
                                     grossRangeFailAbove=grfaSlot.value,
                                     grossRangeSuspectBelow=grsbSlot.value,
                                     grossRangeSuspectAbove=grsaSlot.value,
                                     flatLineTolerance=fltSlot.value,
                                     flatLineSuspectThreshold=flatLineSuspectThreshold.value,
                                     flatLineFailThreshold=flatLineFailThreshold.value,
                                     rateOfChangeThreshold=rocSlot.value,
                                     spikeSuspectThreshold=spikeSuspectThreshold.value,
                                     spikeFailThreshold=spikeFailThreshold.value)
             
        
        nemsConfig = nq.configParams_N(nemsStd=nemsStd.value)
        global qc_results
        qc_results = nq.runTests(data=data, checkData=checkData, chkStartDate=chkStartDate, qc_config=qc_config, nemsConfig=nemsConfig)
        #print(data.head())
        
        if qc_results != None:
            if checkData.empty:
                dataStatus.value = '<b style="color:orange;">Data retrieved, but no check data available.  Max code will be 400.  Consider changing time range or check data source and rerunning.<b>'
            else:
                dataStatus.value = '<b style="color:green;">Data and check data retrieved.<b>'
                
            p1 = plotStats(qc_results=qc_results, std='qartod')
            #print(data.head())
            p2 = plotStats(qc_results=qc_results, std='nems')
    
            #p3 = plot_NEMS_results()
            # Map the NEMS Codes and create qc df that is available for later use
            global qc_df
            temp_df = nq.mapNEMScodes(qc_results=qc_results, data=data, maxCode=int(maxCodeOptions.value))
            #qc_df = nq.processGaps(data=temp_df, interpolation_time_threshold=(3600*3), interpolation_allowance = 5)
            """
            qc_df = nq.processGaps(data=temp_df, \
                                   interpolate_values=interpolationFlag.value, \
                                   interpolation_time_threshold=int(gapThreshold.value), \
                                   interpolation_allowance = int(interpolationAllowance.value))
            """
        
            qc_df = nq.processGaps(data=temp_df, \
                                   interpolate_values=interpolationFlag.value, \
                                   gap_time_threshold=int(gapThreshold.value))
            
            display(dataStatus)
            show(p1)
            show(p2)
            # Added in here so that graphs clear when run button pressed.
        
            display(Markdown('## Explore Results.'))
            display(Markdown('### General Tests.'))
            display(Markdown('Select the test to see the results as a graph.'))
            qplot = interactive(doBasePlots, x=["gross range", "flat line", "rate of change","spike","aggregate"], value="gross range")
            display(qplot)
            display(Markdown('### NEMS Tests.'))
            display(Markdown('Select the test to see the results as a graph.'))
            #interact(qb.doThePlots,x=["gap data","resolution", "verification frequency", "accuracy"])
            nplot = interactive(doNemsPlots, x=["gap data","resolution", "verification frequency", "verification accuracy"], \
                                value="gap data")
            display(nplot)

            display(Markdown('### NEMS QC.'))
            display(Markdown('Graph the coded results.  Choose whether to see all results or just the ones for archiving (clean set).'))
            #interact(qb.plot_NEMS_results, data_set=widgets.Combobox(options=["all", "clean"], value="all"))
            #qcplot = interactive(pf.plot_NEMS_results, data_set=["all", "clean"], value="all")
            oplot = interactive(doOverallPlots, x=["All Data", "Clean Data"], value="All Data")
            display(oplot)
        else:
            
            dataStatus.value = '<b style="color:red;">No data available, change settings and rerun.<b>'
        
        
def on_analysisBtn_clicked(b):
    analysisOutput.clear_output()
    with analysisOutput:
        print("Please note that data is pulled pulled out live from the server and be patient.")
        ta.runAnalysis(requestType='Hilltop', 
                       base_url=serverOptions.value, 
                       file=fileOptions.value, 
                       site=siteOptions.value, 
                       measurement = measurementOptions.value, 
                       from_date=str(sDate.value), 
                       to_date=str(eDate.value))


def save_options(filename):
    optList = [datetime.now().strftime("%d/%m/%Y %H:%M:%S"), \
               serverOptions.value, \
               fileOptions.value, \
               siteOptions.value, \
               measurementOptions.value, \
               checkServerOptions.value, \
               checkFileOptions.value, \
               checkSiteOptions.value, \
               checkMeasurementOptions.value, \
               checkFileOptions2.value, \
               checkSiteOptions2.value, \
               checkMeasurementOptions2.value, \
               nemsStd.value, \
               #resolution.value, \
               #timeGap.value, \
               #accuracyThreshold.value, \
               #accuracyBandwidth.value, \
               grfbSlot.value, \
               grfaSlot.value, \
               grsbSlot.value, \
               grsaSlot.value, \
               fltSlot.value, \
               flatLineSuspectThreshold.value, \
               flatLineFailThreshold.value, \
               rocSlot.value, \
               spikeSuspectThreshold.value, \
               spikeFailThreshold.value, \
               interpolationFlag.value, \
               gapThreshold.value, \
               interpolationAllowance.value, \
               maxCodeOptions.value, \
               sDate.value, \
               eDate.value, \
               os.getlogin()]
    
    try:
        with open(filename, mode='a', newline='') as options_list:
            options_writer = csv.writer(options_list, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

            options_writer.writerow(optList)
        saveStatus.value = '<b style="color:green;">Options saved.<b>'
        # print("Options saved.")
    except Exception as e :
        saveStatus.value = '<b style="color:red;">Error saving options, make sure ' + filename + ' is not open.<b>'
        # print("Error saving options, make sure " + filename + " is not open.")
        
        
def on_saveBtn_clicked(b):
    save_options(filename = 'optionsList.csv')   

    
def on_outputBtn_clicked(b):
    # Save the options used for the output
    save_options(filename = 'optionsList.csv')
    # Write csv file of the results
    nq.writeHilltopCsv(data=qc_df, outOption=outOptions.value)
    

runBtn.on_click(on_runBtn_clicked)
saveBtn.on_click(on_saveBtn_clicked)
outputBtn.on_click(on_outputBtn_clicked)    

analysisBtn.on_click(on_analysisBtn_clicked)