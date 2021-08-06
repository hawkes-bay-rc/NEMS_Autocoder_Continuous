# -*- coding: utf-8 -*-
"""
Created on Fri 4 June 2021
@author: Jeff Cooke

Utility functions for accessing data and information from time series servers.
"""

# Added hilltop library
#from hilltoppy import web_service as ws
# Development version (local)
import web_service as ws
import pandas as pd


def getSiteList(requestType='Hilltop', base_url=None, file=None):
    """
    Get a list of sites from a timeseries server.
    
    Keyword arguments:
    requestType -- Options are 'Hilltop'.  The type of server that the request is to.
    base_url -- The server endpoint (bulk of the url)
    file -- The file, or last part of the url after the last /
    
    Returns:
    A list of sites, or an empty list if there is a problem obtaining the site list.
    """
    
    if requestType == 'Hilltop':
        # Do a Hilltop SiteList call and extract the site names from it to a list
        try:
            siteList = ws.site_list(base_url, file)['SiteName'].tolist()
            return siteList
        except:
            # There was a problem with the request, return an empty list
            return []
    else:
        # The request type isn't supported so raise an error
        raise NameError('Acceptable requestTypes are Hilltop.')

        
def getMeasurementList(requestType='Hilltop', base_url=None, file=None, site=None, tstype='Standard'):
    """
    Get a list of measurements for a site from a timeseries server.
    
    Keyword arguments:
    requestType -- Options are 'Hilltop'.  The type of server that the request is to.
    base_url -- The server endpoint (bulk of the url).
    file -- The file, or last part of the url after the last /.
    site -- The site that you want the measurement list for.
    tstype -- (optional) The type of timeseries to return, Standard or All
    
    Returns:
    A list of sites, or an empty list if there is a problem obtaining the site list.
    """
    
    if requestType == 'Hilltop':
        # Do a Hilltop MeasurementList call and extract the site names from it to a list
        try:
            measurementList = ws.measurement_list(base_url=base_url, 
                                                  hts=file, 
                                                  site=site, 
                                                  tstype=tstype).index.get_level_values('Measurement').tolist()
            return measurementList
        except:
            # There was a problem with the request, return an empty list
            return []
    else:
        # The request type isn't supported so raise an error
        raise NameError('Acceptable requestTypes are Hilltop.')    
        

def getData(requestType='Hilltop', base_url=None, file=None, site=None, measurement=None, from_date=None, to_date=None):
    """
    Get dataframe of results for a site and measurement from a timeseries server.
    
    Keyword arguments:
    requestType -- Options are 'Hilltop'.  The type of server that the request is to.
    base_url -- The server endpoint (bulk of the url).
    file -- The file, or last part of the url after the last /.
    site -- The site that you want the data for.
    measurement -- The measurement that you want the data for.
    from_date -- The date that you want to request data from.
    to_date -- The date that you want to request data upto.
    
    Returns:
    A pandas dataframe of timeseries results (datetime as the index), or an empty dataframe if there is a problem obtaining the data.
    """
    if requestType == 'Hilltop':
        #data = pd.DataFrame()
        
        try:
            data = ws.get_data(base_url=base_url, 
                           hts=file, 
                           site=site, 
                           measurement=measurement, 
                           from_date=from_date, 
                           to_date=to_date).reset_index()
        
            # Add a column containing the value as a string
            data['valStr'] = data['Value'].astype('str')
            # Ensure that the value is numeric
            data['Value'] = pd.to_numeric(data['Value'])
        except:
            data = pd.DataFrame()
    else:
        raise NameError('Acceptable requestTypes are Hilltop.') 
    return data
        
        
# Code for old functions below as they may be useful in the future.        
"""
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
    #myHqObj = {"Command": "PDist","Site": "HAWQi","Measurement": "Barometric Pressure","From": "2015-01-01","To": "2020-01-01"}
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
        
"""