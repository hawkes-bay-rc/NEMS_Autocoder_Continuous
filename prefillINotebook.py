#interactive sessions
from ipywidgets import interact, interactive, fixed, interact_manual, Layout
import ipywidgets as widgets
import pandas as pd
import requests
import xml.etree.ElementTree as ET
import json

# Added hilltop library
from hilltoppy import web_service as ws

style = {'description_width': '70%'}

apiOptions = widgets.Dropdown(options=['Telemetry','All Sites'],value="All Sites")

apiRoot = "https://data.hbrc.govt.nz/EnviroData/EMAR.hts?service=Hilltop"
def selectStatApi(api):
    if api == 'Telemetry':
        apiRoot="https://data.hbrc.govt.nz/EnviroData/Telemetry.hts?service=Hilltop"
    else :
        apiRoot="https://data.hbrc.govt.nz/EnviroData/EMAR.hts?service=Hilltop" #don't know why EMAR

#some widgets to be dynamically filled def's here
import QaBay as qb

#get all the sites for requisite measurement type
#sites = []

"""
def getSites():
    requestType = "SiteList"
    apiRoot="https://data.hbrc.govt.nz/EnviroData/Telemetry.hts?service=Hilltop" #sites from Telemetry as we're processing them
    myWebRequest =  apiRoot + '&Request='+requestType
    #print(myWebRequest)
    r = requests.get(myWebRequest)
    #print(r.text)

    root = ET.fromstring(r.content)
    for child in root.iter('*'):
        #print(child.tag,child.attrib)
        if child.tag == 'Site':
            sites.append(child.attrib['Name'])
    #print('sites: ',sites)

"""
#prefetch the available sites
# getSites()
# as dataframe
base_url = 'https://data.hbrc.govt.nz/EnviroData'
hts = 'EMAR.hts'
sitedf = ws.site_list(base_url, hts, location=True)
sites = sitedf['SiteName'].tolist()

"""
def measList(site):
    measurements = []
    #print('fetching measurements')
    #get all the sites for requisite measurement type
    requestType = "MeasurementList"
    myWebRequest =  apiRoot + '&Request='+requestType + '&Site='+site
    #print(myWebRequest)
    r = requests.get(myWebRequest)
    #print(r.text)
    measurements = []
    root = ET.fromstring(r.content)
    for child in root.iter('*'):
        #print(child.tag,child.attrib)
        if child.tag == 'Measurement':
            measurements.append(child.attrib['Name'])
    #print('measurements: ',measurements)
    return measurements
"""

siteOptions = widgets.Dropdown(options=sites,value="HAWQi")
measurementOptions = widgets.Dropdown()

grfbSlot = widgets.IntText(value=5,style=style)
grfaSlot = widgets.IntText(value=25,style=style)
grsbSlot = widgets.IntText(value=10,style=style)
grsaSlot = widgets.IntText(value=22,style=style)

fltSlot = widgets.FloatText(value=0.001,style=style)
rocSlot = widgets.FloatText(value=0.001,style=style)

sDate = widgets.DatePicker(value=pd.to_datetime('2015-01-01'))
eDate = widgets.DatePicker(value=pd.to_datetime('2020-01-01'))


# Define a function that updates the content of y based on what we select for x
def updateMsmt(*args):
    measurementOptions.disabled = True
    button.disabled = True
    
    #measurementOptions.options = measList(siteOptions.value)
    measdf = ws.measurement_list(base_url, hts, siteOptions.value)
    
    measurementOptions.options = measdf.index.get_level_values('Measurement').tolist()
    
    measurementOptions.disabled = False
    button.disabled = False

def updateRange(*args):
    grfbVal, grfaVal, grsbVal, grsaVal = getMsmtPDist(siteOptions.value,
                            measurementOptions.value,
                            sDate.value, eDate.value)
    
    grfbSlot.value = grfbVal
    grfaSlot.value = grfaVal
    grsbSlot.value = grsbVal
    grsaSlot.value = grsaVal
    
    rocSlot.vlaue = getAnnMinMax(siteOptions.value,
                                        measurementOptions.value,
                                        sDate.value, eDate.value)
    
siteOptions.observe(updateMsmt)
measurementOptions.observe(updateRange)

#Add a run button to make sure that system is not overloaded by auto processing
button = widgets.Button(description="Run")
output = widgets.Output()
def on_button_clicked(b):
    with output:
        print("Please note that data is pulled pulled out live from the server and be patient.")
        qb.runTests()

button.on_click(on_button_clicked)


def getAnnMinMax(site,measurement,dateStart,dateEnd):
    myWebRequest =  apiRoot + "&Request=Hydro"
    #get the range of values to be applied
    myHqObj = {
        "Command" : "PEXT",
        "Site" : site,
        "Measurement" : str(measurement),
        "From" : str(dateStart),
        "To" : str(dateEnd),
        #"Month" : "July",
        "Yearly" : "true"
    }
    
    headers = {"Content-Type": "application/json"}
    params = {"Service":"Hilltop", "Request":"Hydro"}
    r = requests.post(myWebRequest, json = myHqObj, headers=headers, params=params)
    #print(r.text)
    
    myRateChange = []
    root = ET.fromstring(r.content)
    #print(root)
    if len(root.findall("Error")) > 0:
        print('Could not fetch the range, please specify yourself')
        return -1,-1
    else :
        for node in root:
            if node.tag == 'AnnualData':
                for child in node:
                    if child.tag == 'Row':
                        #print(child.attrib)
                        temp = child.text.split(',')
                        valLow = float(temp[3])
                        timeLow = float(temp[4])
                        valHi = float(temp[5])
                        timeHi = float(temp[6])
                        #print((valHi-valLow)/((timeHi-timeLow)))
                        try:
                            myRateChange.append((valHi-valLow)/(timeHi-timeLow))
                        except Exception as e:
                            print('Interpolation error, issue with hydro query')
                            print(e)
                            myRateChange.append(float(np.nan))
    #return max(min(myRateChange),0.001),max(max(myRateChange),0.001) #make sure no negative values turn up
    return max(myRateChange)*2
    
def getMsmtPDist(site,measurement,dateStart,dateEnd):
    myWebRequest =  apiRoot + "&Request=Hydro"
    #"https://data.hbrc.govt.nz/EnviroData/Telemetry.hts?Service=Hilltop&Request=Hydro" #
    #lprint(myWebRequest)
    #get the range of values to be applied
    """myHqObj = {"Command": "PDist","Site": "HAWQi","Measurement": "Barometric Pressure","From": "2015-01-01","To": "2020-01-01"}"""
    myHqObj = {
        "Command" : "PDist",
        "Site" : site,
        "Measurement" : str(measurement),
        "From" : str(dateStart),
        "To" : str(dateEnd)
    }
    
    headers = {"Content-Type": "application/json"}
    params = {"Service":"Hilltop", "Request":"Hydro"}
    r = requests.post(myWebRequest, json = myHqObj, headers=headers, params=params)
    #print(r.text)
    
    root = ET.fromstring(r.content)
    #print(root)
    if len(root.findall("Error")) > 0:
        print('Could not fetch the range, please specify yourself')
        return -1,-1,-1,-1
    else :
        for node in root:
            if node.tag == 'PDF':
                for child in node:
                    if child.tag == 'Min':
                        grfbVal = float(child.text)
                    if child.tag == 'Max':
                        grfaVal = float(child.text)
                    if child.tag == 'Mean':
                        myMean = float(child.text)
                    if child.tag == 'StdDev': #parametric??
                        myStdev = float(child.text)
        
        grsbVal = myMean - myStdev
        grsaVal = myMean + myStdev
        
        return grfbVal, grfaVal, ((grsbVal<grfbVal)*grfbVal or grsbVal), ((grsaVal>grfaVal)*grfaVal or grsaVal)
        #return -1,-1,-1,-1