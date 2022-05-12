# -*- coding: utf-8 -*-
"""
Created on Tue Nov  3 10:05:41 2020
Functions for working with Hilltop depth profile data.

@author: Jeff Cooke
"""
# print("Functions loaded")
# Import the required packages
import pandas as pd
import requests
from bs4 import BeautifulSoup


# Define a function to get depth profile data
def get_depth_profile(endPoint, site, measurement, timeFrom, timeTo=""):
    """
    gets the depth profile data from the Hilltop server and returns it as a Pandas dataframe.
    """
    # End time is optional, so create url differently depending whether it's given or not.
    if timeTo == "":
        myWebRequest =  endPoint + 'Service=Hilltop&Request=GetData&Site='+site+'&Measurement='+measurement+'&From='+timeFrom
    else:
        myWebRequest =  endPoint + 'Service=Hilltop&Request=GetData&Site='+site+'&Measurement='+measurement+'&From='+timeFrom+'&To='+timeTo
    
    #print(myWebRequest)
    
    # Request info from the url and store it    
    r = requests.get(myWebRequest)   
    # Parse the data using Beautiful Soup
    tree = BeautifulSoup(r.content, "lxml")
    # Create an empty pandas dataframe to hold the output
    data = pd.DataFrame()
    # process the tree, for each survey
    for s in tree.find_all("section"):
        # extract the survey time
        surveytime = pd.to_datetime(str(s.surveytime.string),infer_datetime_format=True) #force the bs4 string to python string and convert to date time dtype
        #surveytime = s.surveytime.string
        # process the data
        for d in s.find_all("data"):
            # Create a list of depths
            depth1 = [o.string for o in d.find_all("o")]
            # Create a list of values
            value1 = [i.string for i in d.find_all("i1")]
            # Get the number of rows, so that the other data can be duplicated
            nr = len(depth1)
            # Create a dataframe for each survey
            surv = {"site": [site for p in range(0, nr)],
                    "measurement": [measurement for p in range(0, nr)],
                    "surveytime": [surveytime for p in range(0, nr)], 
                    "depth": depth1, 
                    "value": value1}
            # Append the survey data to output dataframe
            data = data.append(pd.DataFrame(data=surv, columns=["site", "measurement", "surveytime", "depth", "value"] ))
    data["depth"] = pd.to_numeric(data["depth"])
    data["value"] = pd.to_numeric(data["value"])
    
    #print(data.head())
    # Return the data        
    return data


def summary_at_depth(data, depth, margin=1):
    """
    Takes the depth profile data from a get_depth_profile request, a depth of interest and a margin (optional, default 1). 
    Returns a dataframe of the summary of the min, mean and max of the depths and values in the range depth +- margin. 
    Useful for quality assurance of the data and interpolation.
    """
    upper_d = depth + margin
    lower_d = depth - margin
    subset = data[(data.depth >= lower_d) & (data.depth <= upper_d)]
    summary = subset.groupby(
                           ['site', 'measurement', 'surveytime']
                            ).agg(
                                {
                                 'depth': ['min', 'mean', 'max'],     # depth stats
                                 'value': ['min', 'mean', 'max']  # value stats
                                }
                                )
    
    return summary

def applyFunction(group):
    group.set_index('depth', inplace = True)
    group.interpolate(method= 'values', inplace = True)
    group.reset_index(inplace = True)
    #print(group.head(3))
    return group

def result_at_depth(data, depth, margin=0):
    """
    Takes the depth profile data from a get_depth_profile request, a depth of interest and a margin (optional, default 0). 
    Returns a dataframe of the results at the depths between depth +- margin, including an interpolated result for the depth 
    of interest.  The default margin is 0 and this will return the interpolated values at the depth requested.
    """
    # Checks to add
    # depth is numeric
    # depth is within the range of depths for each site and survey
    # data has only one site and one measurement
    # print(depth)
    
    # copy the data
    working = data.copy()
    # Add rows into the dataframe with the desired depth and NA for the values
    times = working.surveytime.unique()
    site = working["site"].iloc[0]
    meas = working["measurement"].iloc[0]
    ntimes = len(times)
    newData = {"site": [site for p in range(0, ntimes)],
               "measurement": [meas for p in range(0, ntimes)],
                "surveytime": times, 
                "depth": [depth for p in range(0, ntimes)] 
                    }
    # Create new dataframe
    newdf = pd.DataFrame(data=newData, columns=["site", "measurement", "surveytime", "depth"])
    #print(newdf)
    
    # Append the new data frame to the original with values for depth as nan, to be interpolated
    fulldf = working.append(newdf, ignore_index=True, sort=False)
    #print(fulldf)
    
    # Make sure that the depth column is float
    fulldf["depth"] = fulldf["depth"].astype('float')
    # Sort the dataframe
    fulldf = fulldf.sort_values(by=["site", "measurement", "surveytime", "depth"]) #, ignore_index=True)
    
    # fulldf = fulldf[(fulldf['depth'] >= 4.6) & (fulldf['depth'] <= 5.4)]
    # Reindex ready for interpolation
    ########fulldf = fulldf.set_index('depth')
    # Use interpolation (on the index) to fill in the gaps using group by too
    fulldf = fulldf.groupby('surveytime').apply(lambda group: group.interpolate(method= 'values'))
    ########fulldf = fulldf.groupby('surveytime').apply(lambda group: applyFunction(group))
    fulldf.reset_index(drop=True,inplace=True)
    #fulldf = fulldf.groupby('surveytime').apply(lambda group: group.reset_index().drop_duplicates(subset='index', keep='last', inplace=True).set_index('index', inplace=True).sort_index().interpolate(method= 'values'))
    # Reset the index
    #############fulldf = fulldf.reset_index()
    # Check whether a single depth result, or a range of results is wanted
    if margin == 0:
         # Extract the results at the desired depth
        depthRes = fulldf[(fulldf.depth == depth)]
    else:
        # Extract a wider range for checking
        depthRes = fulldf[(fulldf.depth >= depth - margin) & (fulldf.depth <= depth + margin)]
    
    # Return the results
    return depthRes