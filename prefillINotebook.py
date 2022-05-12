#interactive sessions
from ipywidgets import interact, interactive, fixed, interact_manual, Layout
from datetime import datetime
import ipywidgets as widgets
import pandas as pd
import requests
import xml.etree.ElementTree as ET
import json
import csv


from bokeh.layouts import gridplot
from bokeh.plotting import figure, show, output_notebook
from bokeh.models import ColumnDataSource, FactorRange, HoverTool
from bokeh.transform import factor_cmap
from bokeh.io import push_notebook

import tsData_utils as tsu
import tsAnalysis as ta

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

qc_df = pd.DataFrame()

# Set the initial options
serverOptions = widgets.Text(value="https://data.hbrc.govt.nz/EnviroData/", description="Server")
# fileOptions = widgets.Text(value="EMAR.hts", description="File")
fileOptions = widgets.Text(value="Telemetry.hts", description="File")

#siteOptions = widgets.Dropdown(options=sites,value="HAWQi")
#siteOptions = widgets.Dropdown(options=ws.site_list(serverOptions.value, 
#                                                    fileOptions.value)['SiteName'].tolist(), value='HAWQi')
siteOptions = widgets.Dropdown(options=tsu.getSiteList(requestType='Hilltop', 
                                                   base_url=serverOptions.value, 
                                                   file=fileOptions.value), 
                               value='HAWQi')
#measurementOptions = widgets.Dropdown(options=ws.measurement_list(serverOptions.value, 
#                                                                  fileOptions.value, 
#                                                                  site='HAWQi').index.get_level_values('Measurement').tolist())
measurementOptions = widgets.Dropdown(options=tsu.getMeasurementList(requestType='Hilltop', 
                                                                 base_url=serverOptions.value, 
                                                                 file=fileOptions.value, 
                                                                 site=siteOptions.value))
                                                                  #site='HAWQi')
#Check data options
# Sites and measurements come from optionsList and server calls


def getOptionList(fieldName='Site'):
    #Takes a type of Site, Measurement, CheckSite or CheckMeasurement and returns a list of distinct values from the optionsList
    if fieldName in ['Site', 'Measurement', 'checkSite', 'checkMeasurement']:
        #Import the options list
        optionsList = pd.read_csv('optionsList.csv')
        # Get the list of unique values from the column.
        return set(optionsList[fieldName].dropna().tolist())
    else:
        raise NameError('Acceptable fieldNames are Site, Measurement, checkSite, checkMeasurement.')

        

checkServerOptions = widgets.Text(value=serverOptions.value, description="Server")
checkFileOptions = widgets.Text(value="EMARContinuousCheck.hts", description="File")

# Need to add the checkSites from the optionsList file here too (without NaN)

#serverCheckSites = ws.site_list(checkServerOptions.value, checkFileOptions.value)['SiteName'].tolist()
serverCheckSites = tsu.getSiteList(requestType='Hilltop', base_url=checkServerOptions.value, file=checkFileOptions.value)                       
extraCheckSites = list(getOptionList(fieldName='checkSite') - set(serverCheckSites))
checkSiteOptions = widgets.Dropdown(options=(serverCheckSites + extraCheckSites), value='HAWQi')

# Need to add the checkMeasurements from the optionsList file here too (without NaN)
#serverCheckMeasurements = ws.measurement_list(checkServerOptions.value, 
#                                                                  checkFileOptions.value, 
#                                                                  site='HAWQi', 
#                                                                  tstype='All').index.get_level_values('Measurement').tolist()
serverCheckMeasurements = tsu.getMeasurementList(requestType='Hilltop', 
                                             base_url=checkServerOptions.value, 
                                             file=checkFileOptions.value, 
                                             #site='HAWQi', 
                                             site=checkSiteOptions.value,
                                             tstype='All')
extraCheckMeasurements = list(getOptionList(fieldName='checkMeasurement') - set(serverCheckMeasurements))
checkMeasurementOptions = widgets.Dropdown(options=(serverCheckMeasurements + extraCheckMeasurements))

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


sDate = widgets.DatePicker(value=datetime.strptime("2020-01-01", "%Y-%m-%d"))
eDate = widgets.DatePicker(value=datetime.strptime("2020-02-01", "%Y-%m-%d"))


# Processing Options
interpolationFlag = widgets.Checkbox(value=False, description='Interpolate', disabled=False, indent=True)
    
gapThreshold = widgets.IntText(value=10800,style=style)
interpolationAllowance = widgets.IntText(value=5,style=style)


# Status
optStatus = widgets.HTML(value="Default Options")



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


def processingSelector(GapThreshold, InterpolationAllowance):
    #global prInterpolation
    #prInterpolation = Interpolation
    global prGapThreshold
    prGapThreshold = GapThreshold
    global prInterpolationAllowance
    prInterpolationAllowance = InterpolationAllowance
    
    
# Define functions that update the site and measurement lists

def updateSites(change):
    if change['old'] == change['new']:
        return
    siteOptions.disabled = True
    runBtn.disabled = True
    
    
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
    
    measurementOptions.disabled = False
    runBtn.disabled = False
    

def updateCheckSites(change):
    if change['old'] == change['new']:
        return
    checkSiteOptions.disabled = True
    runBtn.disabled = True
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
    # Read the options from the csv file
    opt = pd.read_csv('optionsList.csv')
    se = serverOptions.value
    f = fileOptions.value
    s = siteOptions.value
    m = measurementOptions.value
    
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
    
    checkSiteOptions.disabled = False
    checkMeasurementOptions.disabled = False
    runBtn.disabled = False
    

fileOptions.observe(updateSites, 'value')    
siteOptions.observe(updateMsmt, 'value')
#measurementOptions.observe(updateRange)
measurementOptions.observe(updateOptions)


checkFileOptions.observe(updateCheckSites, 'value')    
checkSiteOptions.observe(updateCheckMsmt, 'value')

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


def plot_results(data, title, test_name):
    if data.empty:
    #if qc_df.empty:
        print("Plot has no data associated with it")
        
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
            plot_results(data=qc_df, title=title, test_name='NEMS_verificationFreq')
        elif x=="verification accuracy":
            title = "NEMS verification accuracy - "+siteOptions.value+" HBRC"
            plot_results(data=qc_df, title=title, test_name='NEMS_verificationAccuracy')
            
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
            plot_NEMS_results(data=qc_df, data_set="all")
            
        elif x=="Clean Data":
            # NEMS Plot, all data
            plot_NEMS_results(data=qc_df, data_set="clean")
        

    except Exception as e :
        print("Please run the tests first, thanks",e)
        

def plot_NEMS_results(data, data_set):
    if data.empty: # == None:
        print("Please run the code first")
        return
    #global qc_df    
    
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
        p1.circle(x = 'DateTime', y='Value', size=4, legend_field='Action', color='#800080' , alpha=1, 
                  source=ColumnDataSource(data=plotting_df[plotting_df['Action']=="Drop"].dropna()))
        
        p1.add_tools(HoverTool(tooltips=TOOLTIPS, formatters={'@DateTime': 'datetime', }))
        global nem
        nem = show(gridplot([[p1]], ), notebook_handle=True) #plot_width=800, plot_height=400))
    except Exception as e :
        print("Please run the tests first, thanks\n",e, 'is the Error !#')
        print('This error might occur when the program is run in batch mode')


def on_runBtn_clicked(b):
    output.clear_output()
    with output:
        print("Please note that data is pulled pulled out live from the server and be patient.")
        #qb.runTests()
        #global data
        #global checkData
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
    
        checkData = tsu.getData(requestType='Hilltop', 
                            base_url=checkServerOptions.value, 
                            file=checkFileOptions.value, 
                            site=checkSiteOptions.value, 
                            measurement = checkMeasurementOptions.value, 
                            from_date=chkStartDate, 
                            to_date=str(eDate.value))
        
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
        
        p1 = plotStats(qc_results=qc_results, std='qartod')
        #print(data.head())
        p2 = plotStats(qc_results=qc_results, std='nems')
    
        #p3 = plot_NEMS_results()
        # Map the NEMS Codes and create qc df that is available for later use
        global qc_df
        temp_df = nq.mapNEMScodes(qc_results=qc_results, data=data)
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



def on_saveBtn_clicked(b):
    optList = [datetime.now().strftime("%d/%m/%Y %H:%M:%S"), \
               serverOptions.value, \
               fileOptions.value, \
               siteOptions.value, \
               measurementOptions.value, \
               checkServerOptions.value, \
               checkFileOptions.value, \
               checkSiteOptions.value, \
               checkMeasurementOptions.value, \
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
               interpolationAllowance.value]
    #print(optList)
    #"""
    with open('optionsList.csv', mode='a', newline='') as options_list:
        options_writer = csv.writer(options_list, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

        options_writer.writerow(optList)
    #  """  

    
def on_outputBtn_clicked(b):
    # Write csv file of the results
    nq.writeHilltopCsv(data=qc_df, outOption=outOptions.value)
    

runBtn.on_click(on_runBtn_clicked)
saveBtn.on_click(on_saveBtn_clicked)
outputBtn.on_click(on_outputBtn_clicked)    

analysisBtn.on_click(on_analysisBtn_clicked)