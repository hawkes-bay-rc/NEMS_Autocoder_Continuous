#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Updated on July 2021
Functions for quality coding data to NEMS, using Qartod checks as well.

Built on initial work by Karunakar in QaBay.py

@author: Jeff Cooke


"""


import pandas as pd
import numpy as np
import numpy.ma as ma

import operator
import time

from datetime import datetime, timedelta

from collections import OrderedDict

from pathlib import Path

#Get Qartod
# Temporary change to allow modifying spike detection algorithm
from ioos_qc import qartod
from ioos_qc.config import (Config, QcConfig)

from ioos_qc.utils import (
    isnan,
    isfixedlength,
    add_flag_metadata,
    great_circle_distance,
    mapdates
)

# HBQartod contains a modified qartod spike algorithm, was used in some earlier versions.
#import HBqartod as HBqartod

#Import timeseries data utility functions.  These are the functions for getting data from the servers.

import tsData_utils as tsu


# import Qartod flag mapping
#qFlags = qartod.QartodFlags()
qFlags = qartod.QartodFlags()
"""qFlags.GOOD, qFlags.FAIL, qFlags.SUSPECT"""


def resolution_ok(x, dec_required):
    """
    Check for a decimal point and that there are the right number of decimal places.
    
    Parameters
    ----------
    x : string
        The string represenatation of a number, the value to be checked.
    dec_required : int
        The required number of decimal places
    
    Returns
    -------
    Boolean
           True if there are the right number of decimal places (or more), False if there is an issue.
    """
    if('.' in x):
        # If there is one split on it
        temp = x.split('.')
        # Check that the number of figures after the decimal place is greater than or equal to the required number of decimal places.
        if(len(temp[1])>= dec_required) :
            # If the number is greater than or equal to the requirement then there is no issue, return True
            return True
        else:
       
            # Otherwise there's an issue, return False.
            return False
    else:
        # There is no decimal place then check if there should have been
        if(dec_required == 0):
            # No decimal places required, so ok, return True
            return True
        else:
            # Decimal places required, an issue, return False.
            return False

    
def decimalReq_NEMSfn(x, config):
    """
    Identify the required number of decimal places for a number, based on the bands in the NEMS configuration file.
    
    Parameters
    ----------
    x : string 
        A string represenatation of a number, the value to be checked.
    config : pandas dataframe
        Configuration dataframe to look up values in. Requires fields BandUpperLimit (int) and ResolutionDP (int).
    Returns
    -------
    int
        The number of decimal places required.
    """
    # convert x to a number
    x_val = float(x)
    # for each row in config 
    for ind in config.index:
        # if band upper limit is NaN then return ResolutionDP
        # else check if numeric x less than band upper limit and return the number of decimal places required.
        if pd.isna(config.loc[ind, 'BandUpperLimit']) or x_val < float(config.loc[ind, 'BandUpperLimit']):
            return config.loc[ind, 'ResolutionDP']
   #TODO Add error handling


def checkFrequency(checkDataTimes, expectedValFreq, chkStartDate):
    """
    Checks the frequency of the validation checks against the expected valifation frequency
    
    Parameters
    ----------
    checkDataTimes : list
        A list of date times when validation measurements occurred.
    expectedValFreq : int
        The expected validation frequency in months.
    chkStartDate : string (dd/mm/yyy)
        A string representation of a date, the date that the check data was requested from.
    Returns
    -------
    pandas dataframe
        A dataframe of checktimes and whether the validation frequency passed or not.  
        Dataframe fields are:-
        DateTime - DateTime - The dates and times that validation measurements occurred.
        ValidationTimeDiff - Duration - The time between validation measurements
        ValidationFreqStatus - Int - The Qartod Flag relating to whether the validation was done within the required time period.
    """ 
    
    # Create a working data frame with the dates in it
    workingdf = pd.DataFrame(checkDataTimes, columns = ['DateTime'])
    
    # Calculate the time difference between validation checks
    workingdf['ValidationTimeDiff'] = np.insert(list(map(operator.sub, \
                                                         workingdf['DateTime'].values[1:], \
                                                         workingdf['DateTime'].values[:-1])), \
                                                         0, \
                                                         [operator.sub(workingdf['DateTime'].values[0], pd.to_datetime(chkStartDate))], \
                                                         axis=0)
    
    # Add a column with the checks that the validation has been done within the required time.
    # Assumes that a month is 30 days
    workingdf['ValidationFreqStatus'] = np.array([qFlags.GOOD if (np.timedelta64(expectedValFreq * 30,'D') >= x) \
                                                  else qFlags.FAIL for x in workingdf['ValidationTimeDiff'].tolist()])
    
    # Return the dataframe
    return workingdf
    

def processCheckData(checkData, data, nemsConfig):
    """
    Process the check data, interpolates the data to get comparison values.
    Assesses accuracy and validation frequency for each check.
    Parameters
    ----------
    checkData : pandas dataframe
        A dataframe of checkData
    data : pandas dataframe
        A dataframe of data to be checked
    nemsConfig : pandas dataframe
        A dataframe of NEMS criteria from the relevant NEMS standard.
    Returns
    ------
    pandas dataframe 
        A Pandas dataframe of checkData with associated interpolated data values and the results of accuracy 
        and validation frequency checks.
    """
    if not checkData.empty: #checkData != None: 
        # Rename the Value column in the CheckData dataframe
        checkData = checkData.rename(columns={'Value': 'CheckValue'}) 
        # Create a working dataframe to interpolate the values 
        workingdf = pd.concat([data[['DateTime', 'Value']], checkData[['DateTime']]], ignore_index=True, sort=False)
        # Use DateTime as the index and sort it
        workingdf.set_index('DateTime', inplace = True)
        workingdf.sort_index(inplace = True)
        # Interpolate the values to get results at the time of the checks and then reset the index
        workingdf.interpolate(method= 'values', inplace = True)
        workingdf.reset_index(inplace = True)
        # global accuracyCheck
        # Create an accuracy check dataframe to help with the checks
        accuracyCheck = pd.merge(checkData, workingdf, on='DateTime')
        # Calculate the absolute difference and % difference
        accuracyCheck['AbsDiff'] = abs(accuracyCheck['CheckValue'] - accuracyCheck['Value'])
        accuracyCheck['Abs%Diff'] = 100 * accuracyCheck['AbsDiff'] / accuracyCheck['CheckValue']
        # Calculate the time difference between validations
        #accuracyCheck['ValidationTimeDiff'] = np.insert(list(map(operator.sub, \
        #                                                       accuracyCheck['DateTime'].values[1:], \
        #                                                         accuracyCheck['DateTime'].values[:-1])), 0, 0, axis=0)
        # Add fields for the results of the status checks
        #accuracyCheck['ValidationFreqStatus'] = None
        accuracyCheck['AccuracyStatus'] = None
        # For each check data point assess the accuracy and validation interval status
        for cdi in accuracyCheck.index:
            # Check each band for config parameters
            for ind in nemsConfig.index:
                if (pd.isna(nemsConfig.loc[ind, 'BandUpperLimit']) \
                    or (float(accuracyCheck.loc[cdi, 'CheckValue'])) < float(nemsConfig.loc[ind, 'BandUpperLimit'])):
                    # the band contains relevant metadata so do the comparisons
                    # verification frequency
                    #if np.timedelta64(int(nemsConfig.loc[ind, 'ValidationFrequency_mons']) \
                    #                  * 30,'D') >= accuracyCheck.loc[cdi, 'ValidationTimeDiff']:
                    #    accuracyCheck.loc[cdi, 'ValidationFreqStatus'] = qFlags.GOOD #"Good"
                    #else: 
                    #    accuracyCheck.loc[cdi, 'ValidationFreqStatus'] = qFlags.FAIL #"Fail"
            
                    # accuracy 
                    # absolute
                    # Check for a reference tolerance, if there is one use it, if not set to 0
                    if not pd.isna(nemsConfig.loc[ind, 'AccuracyReferenceTolerance%']):
                        reftol = float(nemsConfig.loc[ind, 'AccuracyReferenceTolerance%'])
                    else:
                        reftol = 0.0
                    # Do the status updates
                    if pd.isna(nemsConfig.loc[ind, 'AccuracyToleranceAbs600']):
                        #No absolute limit for 600 so use %
                        if pd.isna(nemsConfig.loc[ind, 'AccuracyTolerance%600']):
                            # There is no accuracy set so mark as Unknown
                            accuracyCheck.loc[cdi, 'AccuracyStatus'] = qFlags.UNKNOWN #"Unknown"
                        elif float(nemsConfig.loc[ind, 'AccuracyTolerance%600']) >= float(accuracyCheck.loc[cdi, 'Abs%Diff']):
                            # accuracy passes at 600 level so good
                            accuracyCheck.loc[cdi, 'AccuracyStatus'] = qFlags.GOOD #"Good"
                        elif float(nemsConfig.loc[ind, 'AccuracyTolerance%500']) >= float(accuracyCheck.loc[cdi, 'Abs%Diff']):
                            # accuracy passes at 500 level so Fair, Suspect
                            accuracyCheck.loc[cdi, 'AccuracyStatus'] = qFlags.SUSPECT #"Suspect"
                        else:
                            #accuracy fails, qc400
                            accuracyCheck.loc[cdi, 'AccuracyStatus'] = qFlags.FAIL #"Fail"
                    elif ((float(nemsConfig.loc[ind, 'AccuracyToleranceAbs600']) + \
                          (reftol * float(accuracyCheck.loc[cdi, 'CheckValue']) / 100)) >= float(accuracyCheck.loc[cdi, 'AbsDiff'])):
                        # accuracy passes at 600 level so good (takes into account accuracy tolerances if applicable)
                        accuracyCheck.loc[cdi, 'AccuracyStatus'] = qFlags.GOOD #"Good"
                    elif ((float(nemsConfig.loc[ind, 'AccuracyToleranceAbs500']) + \
                          (2 * reftol * float(accuracyCheck.loc[cdi, 'CheckValue']) / 100))>= float(accuracyCheck.loc[cdi, 'AbsDiff'])):
                        # accuracy passes at 500 level so Fair, Suspect (takes into account accuracy tolerances if applicable)
                        accuracyCheck.loc[cdi, 'AccuracyStatus'] = qFlags.SUSPECT #"Suspect"
                    else:
                        #accuracy fails, qc400
                        accuracyCheck.loc[cdi, 'AccuracyStatus'] = qFlags.FAIL #"Fail"
                    # break out of the loop
                    break
    else:
        # There was no check data so create an empty accuracy check dataframe
        accuracyCheck = pd.DataFrame()
        
    if not accuracyCheck.empty:
        return accuracyCheck  
    else:
        #return None
        return accuracyCheck


def nemsGapTest(data, nemsConfig):
    """
    Checks that the gap between readings is less than the gap required by NEMS.
    Parameters
    ----------
    data : Pandas dataframe
        A dataframe of data to be checked
    nemsConfig : Pandas Dataframe
        A dataframe of NEMS criteria from the relevant NEMS standard.
    Returns
    -------
    array
        a masked array of qartod quality flags.
    """
    
    # Get the NEMS Standard
    nemsStandard = nemsConfig['NEMS_Standard'].iloc[0]
    
    if nemsStandard != 'Not Available':
        # Get the allowed interval (assumes the same throughout) and assess
        timeLimit_NEMS = int(nemsConfig['MaxRecordInterval_mins'].iloc[0])
        timeDiff = list(map(operator.sub, data['DateTime'].values[1:],data['DateTime'].values[:-1]))
        samplingMask_gapData = np.insert(np.array([qFlags.FAIL if x>np.timedelta64(timeLimit_NEMS,'m') \
                                               else qFlags.GOOD for x in timeDiff]), 0, 1, axis=0) #prepend for start to be true
    else:
        # Set everything to fail
        samplingMask_gapData = np.array([qFlags.FAIL] * len(data['valStr']))
        
    #print(samplingMask_gapData)
    #qc_results['qartod']['NEMS_gapData'] = ma.masked_array(samplingMask_gapData)
    #qc_results['qartod']['aggregate'][qc_results['qartod']['NEMS_gapData']==qFlags.FAIL]=qFlags.FAIL
    
    # qc_results['nems'] = OrderedDict()
    #qc_results['nems']['NEMS_gapData'] = ma.masked_array(samplingMask_gapData)
    return ma.masked_array(samplingMask_gapData)


def nemsResolutionTest(data, nemsConfig):
    # Test the resolution of the readings.
    # Checks that the number of decimal places of a reading is greater than or equal to that required by NEMS.
    # data - a dataframe of data to be checked
    # nemsConfig - a dataframe of NEMS criteria from the relevant NEMS standard.
    # returns a masked array of qartod quality flags.
    
    ## resolution tests
    #print(data[myMeasurement].dtype)
    # Get the NEMS Standard
    nemsStandard = nemsConfig['NEMS_Standard'].iloc[0]
    # Check if there is a NEMS Standard, if not mark everything as FAIL
    if nemsStandard != 'Not Available':
        # set the decimals required, initially as the most required, TODO split
        decimalReq_NEMS = nemsConfig['ResolutionDP'].max()
        # If any of the results meet the resolution test then all of the results are ok.
        #samplingMask_resolution = [qFlags.GOOD if data['valStr'].apply(resolution_ok, dec_required=decimalReq_NEMS).any() \
        #                           else qFlags.FAIL] * len(data['valStr'])
        # New code to assess as go through, would be better to process in a window, similar to flat line to avoid 0 issues, but ensure that major issues identified.
        samplingMask_resolution = np.array([qFlags.GOOD if resolution_ok(x, decimalReq_NEMSfn(x=x, config=nemsConfig)) \
                                            else qFlags.FAIL for x in data['valStr'].tolist()])
    else:
        # Set everything to fail
        samplingMask_resolution = np.array([qFlags.FAIL] * len(data['valStr']))
        
    #samplingMask_resolution = [qFlags.GOOD if data[myMeasurement].apply(resolution_ok, dec_required=decimalReq_NEMS).any() \
    #                           else qFlags.FAIL] * len(data[myMeasurement])
    
    
    # Jeff recreated original, but using a function)
    # samplingMask_resolution = []
    # for x in data[myMeasurement]:
    #     if not (resolution_ok(x, decimalReq_NEMS)):
    #         samplingMask_resolution.append(qFlags.FAIL)
    #     else:
    #         samplingMask_resolution.append(qFlags.GOOD)

    
        
        # Original
        # if('.' in x):
        #     temp = x.split('.')
        #     if(len(temp[1])>= decimalReq_NEMS) :
        #         samplingMask_resolution.append(qFlags.GOOD)
        #     else:
        #         samplingMask_resolution.append(qFlags.FAIL)
        # else :
        #     samplingMask_resolution.append(qFlags.FAIL)
        
    #qc_results['qartod']['NEMS_resolution'] = ma.masked_array(samplingMask_resolution)
    ## update the aggregate masked array.
    #qc_results['qartod']['aggregate'][qc_results['qartod']['NEMS_resolution']==qFlags.FAIL]=qFlags.FAIL
    
    #qc_results['nems']['NEMS_resolution'] = ma.masked_array(samplingMask_resolution)
    return ma.masked_array(samplingMask_resolution)
    
    # change aggregate function to use qartod aggregate
    # qc_results['nems']['NEMS_aggregate'][qc_results['nems']['NEMS_resolution']==qFlags.FAIL]=qFlags.FAIL
    

def nemsVerificationFrequencyTest(checkData, data, nemsConfig, chkStartDate):
    # Verification frequency test
    # Get the NEMS Standard
    nemsStandard = nemsConfig['NEMS_Standard'].iloc[0]
    
    if nemsStandard != 'Not Available' and not checkData.empty:
        
        # Extract expected validation frequency
        expectedValFreq = nemsConfig['ValidationFrequency_mons'].iloc[0]
        # Check if there is a value, if there is then  process, there needs to be more than one check data reading as well
        if not pd.isnull(expectedValFreq) and len(checkData) > 1:
            verifFreqdf = pd.concat([data[['DateTime']], \
                                    checkFrequency(checkDataTimes=checkData['DateTime'].tolist(), \
                                                   expectedValFreq=int(expectedValFreq), \
                                                   chkStartDate=chkStartDate)], \
                                   ignore_index=True, \
                                   sort=False)
            # Use DateTime as the index and sort it
            verifFreqdf.set_index('DateTime', inplace = True)
            verifFreqdf.sort_index(inplace = True)
        
            #Fill up the AccuracyStatus column using backfill
            verifFreqdf['ValidationFreqStatus'] = verifFreqdf['ValidationFreqStatus'].fillna(method='backfill')
            #Fill up the tail of the AccuracyStatus column (after last check data) with missing 
            verifFreqdf['ValidationFreqStatus'] = verifFreqdf['ValidationFreqStatus'].fillna(qFlags.UNKNOWN)
            # Remove the check data and convert the AccuracyStatus field to a list to use as a mask
            samplingMask_veriFreq = verifFreqdf.loc[verifFreqdf['ValidationTimeDiff'].isnull(), 'ValidationFreqStatus'].tolist()
        else:
            # Set everything to MISSING
            samplingMask_veriFreq = np.array([qFlags.MISSING] * len(data['Value']))
        
    else:
        # Set everything to fail
        samplingMask_veriFreq = np.array([qFlags.FAIL] * len(data['Value']))
        
    
    #qc_results['nems']['NEMS_verificationFreq'] = ma.masked_array(samplingMask_veriFreq)
    return ma.masked_array(samplingMask_veriFreq)
    # If the test fails add to the aggregate flag as a failure
    # change aggregate function to use qartod aggregate
    #qc_results['nems']['NEMS_aggregate'][qc_results['nems']['NEMS_verificationFreq']==qFlags.FAIL]=qFlags.FAIL
    

def nemsVerificationAccuracyTest(data, accuracyCheck, nemsConfig):
    ## Accuracy Tests
    # Get the NEMS Standard
    nemsStandard = nemsConfig['NEMS_Standard'].iloc[0]
    #TODO if no check data get an error
    #if nemsStandard != 'Not Available' and accuracyCheck != None:
    if nemsStandard != 'Not Available' and not accuracyCheck.empty:
    #if nemsStandard != 'Not Available' and not checkData.empty:
        # Need a value for the mapping to work, set to good for now
        #samplingMask_accuracy = [qFlags.GOOD] * len(data['Value'])
        
        accCheckdf = pd.concat([data[['DateTime']], \
                                accuracyCheck[['DateTime', 'CheckValue', 'AccuracyStatus']]], \
                               ignore_index=True, \
                               sort=False)
        # Use DateTime as the index and sort it
        accCheckdf.set_index('DateTime', inplace = True)
        accCheckdf.sort_index(inplace = True)
        # Interpolate the values to get results at the time of the checks and then reset the index
        #workingdf.interpolate(method= 'values', inplace = True)
        #workingdf.reset_index(inplace = True)
        #Fill up the AccuracyStatus column using backfill
        accCheckdf['AccuracyStatus'] = accCheckdf['AccuracyStatus'].fillna(method='backfill')
        #Fill up the tail of the AccuracyStatus column (after last check data) with missing 
        accCheckdf['AccuracyStatus'] = accCheckdf['AccuracyStatus'].fillna(qFlags.UNKNOWN)
        # Remove the check data and convert the AccuracyStatus field to a list to use as a mask
        samplingMask_accuracy = accCheckdf.loc[accCheckdf['CheckValue'].isnull(), 'AccuracyStatus'].tolist()
          
        
    else:
        # Set everything to unknown as there is no accuracy check
        samplingMask_accuracy = np.array([qFlags.UNKNOWN] * len(data['Value']))
        
    
    # qc_results['nems']['NEMS_verificationAccuracy'] = ma.masked_array(samplingMask_accuracy)
    return ma.masked_array(samplingMask_accuracy)


def runTests(data, checkData, chkStartDate, qc_config, nemsConfig):
    
    
    if data.empty:
        #print("No data available")
        return None
    
    if checkData.empty:
        print("No Check Data - Max QC will be 400")
        
    
    
    # Run QC
    qc = QcConfig(qc_config) # Depreciated but Config doesn't have a run statement, so would need to move Run code into function here.
    #qc = Config(qc_config)
    qc_results =  qc.run(
        #inp=data[myMeasurement],
        inp=data['Value'],
        tinp=data['DateTime'].values 
    )
    # aggregate the qartod results
    qc_results['qartod']['aggregate'] = qartod.qartod_compare([qc_results['qartod']['gross_range_test'],
                                                                  qc_results['qartod']['flat_line_test'],
                                                                  qc_results['qartod']['rate_of_change_test'],
                                                                  qc_results['qartod']['spike_test']])
    
    #NEMS tests
    # Create ordered dictionary to hold NEMS results
    qc_results['nems'] = OrderedDict()
    
    # Check if there is a NEMS Standard, if not mark everything as FAIL
    nemsStandard = nemsConfig['NEMS_Standard'].iloc[0]
    
    # Process the data and check accuracy against NEMS criteria
    accuracyCheck = processCheckData(checkData=checkData, 
                                     data=data, 
                                     nemsConfig=nemsConfig)
    
    # Do the NEMS gap test
    qc_results['nems']['NEMS_gapData'] = nemsGapTest(data=data, 
                                                     nemsConfig=nemsConfig)
    
    # Do the NEMS resolution test
    qc_results['nems']['NEMS_resolution'] = nemsResolutionTest(data=data, 
                                                               nemsConfig=nemsConfig)
    
    # Do the NEMS verification frequency test.
    qc_results['nems']['NEMS_verificationFreq'] = nemsVerificationFrequencyTest(checkData=checkData, 
                                                                                data=data, 
                                                                                nemsConfig=nemsConfig,
                                                                                chkStartDate=chkStartDate)
    
    # Do the NEMS verification accuracy test
    qc_results['nems']['NEMS_verificationAccuracy'] = nemsVerificationAccuracyTest(data=data, 
                                                                                   accuracyCheck=accuracyCheck, 
                                                                                   nemsConfig=nemsConfig)
    # aggregate the nems results
    qc_results['nems']['NEMS_aggregate'] = qartod.qartod_compare([qc_results['nems']['NEMS_gapData'],
                                                                  qc_results['nems']['NEMS_resolution'],
                                                                  qc_results['nems']['NEMS_verificationFreq']])
    
    

    return qc_results
    

    
def writeHilltopCsv(data, outOption='Clean', dateTime=False):
    #data is the qc_df output from running the test
    try:
        # If outOption is Clean then Subset the dataframe so only values to keep remain.
        if outOption == 'Clean':
            statmsg = "Clean Data Selected"
            outData = data[data['Action']!="Drop"] 
            statmsg = "Subsetted Clean Data"
        else:
            # Make a copy and output everything
            statmsg = "All Data Selected"
            outData = data.copy()
            statmsg = "DF Copied"
        # Change the column names to match expected csv format
        #outData.rename(columns={'time':'timestamp', 'value':'Value'}, inplace=True)
        #Change the column order
        statmsg = "Reordering Columns"
        colnames = outData.columns.tolist()
        firstCols = ['DateTime','Site', 'Measurement','Value','QC', 'Gap', 'Action', 'OriginalValue']
        otherCols = list(set(colnames).difference(set(firstCols)))
        outData = outData[firstCols + otherCols]
        statmsg = "Columns Reordered"
        # outData = outData[['DateTime','Site', 'Measurement','Value','QC']]
        # outData = outData[['timestamp','Measurement','Value','QC','Comment', 'Action']] #reorganising the column position
        # Output the data
        # Get the site name to append to the base filename
        sitename = data['Site'].iloc[0]
        statmsg = "Saving to csv"
        currentDirectory = Path(__file__).parent
        # Add date to filename if dateTime set to True
        if dateTime:
            
            filename = sitename + '_QartodOutput_' + time.strftime("%Y%m%d_%H%M%S")  +'.csv'
        else:
            filename = sitename + '_QartodOutput.csv'
        filePath = currentDirectory / 'Outputs' / filename
        #print(filePath)
        outData.to_csv(filePath,index=False) 
    except:
        print("Please view the NEMS code graph first and make sure the output csv file is not open")
        #print(statmsg)


# New NEMS Code mapping
def mapNEMScodes(qc_results, data, maxCode=600):
    """
    Combine the data and quality code results and map these to NEMS.
    
    Parameters
    ----------
    qc_results : pandas dataframe
        A pandas dataframe of quality coded results, the output from runTests.
    data : pandas dataframe
        A pandas dataframe of the data.
    maxCode : int
        The maximum NEMS code that can be achieved for the data.
        
    -------
    A pandas dataframe
        A pandas dataframe of the data coded to NEMS, with flags for all of the tests that have been performed and their results.
    """
    # Convert qc_results to a dataframe
    qartod_df = pd.DataFrame(qc_results['qartod'], columns=qc_results['qartod'].keys())
    nems_df = pd.DataFrame(qc_results['nems'], columns=qc_results['nems'].keys())
    combined_df = pd.concat([qartod_df, nems_df], axis=1)
    #combined_df = combined_df.astype('int16')
    # Read in the mapping table from file and save as df
    mapping_df = pd.read_csv("QC_Mapping.csv", dtype={'aggregate':np.int16, \
                                                      'NEMS_verificationAccuracy':np.int16, \
                                                      'NEMS_aggregate':np.int16, \
                                                      'QC':np.int16})
    # Adjust mapping based on max code provided
    mapping_df['QC'].where(mapping_df['QC'] <= maxCode, maxCode, inplace=True)
    # Convert QC field to string data type.
    mapping_df = mapping_df.astype({"QC": str}, errors='raise') 
    
    # Join qc_results and mapping table
    full_qcdf = pd.merge(combined_df, mapping_df, how="left", on=["aggregate", "NEMS_verificationAccuracy", "NEMS_aggregate"])
    full_df = pd.concat([data, full_qcdf], axis=1)
    
    #full_df = full_df.drop(['aggregate', 'NEMS_aggregate'], axis=1)
    # Rename valStr column to OriginalValue
    full_df.rename(columns={'valStr': 'OriginalValue'}, inplace=True)
    # Change OriginalValue column to float
    full_df['OriginalValue'] = pd.to_numeric(full_df["OriginalValue"], downcast="float")
    
    return full_df


def processGaps(data, interpolate_values, gap_time_threshold): # interpolation_time_threshold, interpolation_allowance):
    """
    Interpolate spikes, and insert gap markers if missing data exceeds a time threshold.
    
    Parameters
    ----------
    data : pandas dataframe
        A pandas dataframe of quality coded results, the output from mapNEMScodes.
    interpolate_values : bool
        Whether spikes should be interpolated.  If True interpolation will be run, if False it won't be.
    gap_time_threshold : int
        The maximum length of time that data is allowed to be missing, in seconds.
    DELETE interpolation_time_threshold : int
    DELETE     The maximum length of time that data is allowed to be missing, in seconds.
    DELETE interpolation_allowance : int
    DELETE    The percentage allowance that determines whether a measured value is used, or an interpolated one is used.
    DELETE    Where the measured value is within this percentage of the interpolated value then the measured value will be used.
    Returns
    -------
    A pandas dataframe
        A pandas dataframe with interpolated results shown for data points that were 'dropped' and within the interpolation threshold, 
        and blank lines where there are gaps in the data over the interpolation threshold.
    """
    # Copy the value where Action is Keep.
    data['Interpolated Value'] = data['Value'].mask(data['Action']!='Keep')
    
    """
    # Check that the interpolation_allowance is between 0 and 100, if not then raise an exception.
    if interpolation_allowance < 0 or interpolation_allowance > 100:
        raise ValueError("interpolation_allowance must be between 0 and 100")
    """
        
    # Interpolate the data to fill the gaps if option set
    if interpolate_values:
        # Use DateTime as the index and sort it
        data.set_index('DateTime', inplace = True)
        data.sort_index(inplace = True)
        # Interpolate the values to get results at the time of the checks and then reset the index
        data.interpolate(method= 'values', inplace = True)
        data.reset_index(inplace = True)
        
    # Create a time diff column for results where Action is Keep
    timeDiff = list(map(operator.sub, data.loc[data['Action']!='Drop', 'DateTime'].values[1:], \
                        data.loc[data['Action']!='Drop', 'DateTime'].values[:-1]))
    # Insert a 0 at the start of the list
    timeDiff.insert(0, timedelta(0))
    data.loc[data['Action']!='Drop', 'GoodValueGap'] = timeDiff
    # Backfill the GoodValueGap Column
    data['GoodValueGap'] = data['GoodValueGap'].fillna(method='backfill')
    
    """
    # Assess the interpolated data, if the interpolated value is within x% of the actual then keep the original if within acceptable gap.
    # data['Interpolation_Difference'] = abs((data['Value']-data['Interpolated Value'])/data['Value'])
    data.loc[(abs((data['Value']-data['Interpolated Value'])/data['Value']) < (interpolation_allowance/100.0)) & \
             (data['Action']!='Keep') & \
             (data['GoodValueGap'] < np.timedelta64(interpolation_time_threshold,'s'))
             , 'Action'] = 'Interpolation Match'
    # Set QC for Interpolation Match data to 500 if it was 600 before.  Enclose in Try in case no results are returned.
    try:
        data.loc[(data['Action']=='Interpolation Match' and data['QC']=='600'), 'QC'] = '500'
    except Exception:
        pass
    """
    
    # Categorise whether interpolation ok or not
    """
    data.loc[((data['GoodValueGap'] < np.timedelta64(interpolation_time_threshold,'s')) & \
             (data['Action']=='Drop') & \
             interpolate_values), 'Action'] = 'Interpolated'
    """
    # Only interpolate spikes, spike_test Fail (4)
    data.loc[((data['spike_test']==4) & \
             (data['Action']=='Drop') & \
             interpolate_values), 'Action'] = 'Interpolated'
    # Set QC for interpolated data to 300
    data.loc[data['Action']=='Interpolated', 'QC'] = '300'
    # Change value to interpolated value 
    
    data.loc[(data['Action']=='Interpolated'), 'Value'] = data['Interpolated Value']
    
    # Insert blank rows above entries where the GoodValueGap is greater than the interpolation_threshold
    # Create a new column to use as an index (with spaces for new rows).
    data['Index_Increment'] = 1
    # data.loc[(data['GoodValueGap'] > np.timedelta64(interpolation_time_threshold,'s')), 'Index_Increment'] = 2
    data.loc[(data['GoodValueGap'] > np.timedelta64(gap_time_threshold,'s')), 'Index_Increment'] = 2
    data['I'] = data['Index_Increment'].cumsum()-1
    data['I'] = data['Index_Increment'].cumsum()-1
    # Get a list of indexes where the GoodValueGap is greater than the interpolation_threshold.
    """
    This didn't work, the index was wrong
    blankDf = data.loc[(data['GoodValueGap'] > np.timedelta64(interpolation_threshold,'s')), ['Site', 'Measurement', 'Action']] 
    blankDf.index.names = ['I']
    """
    # Try assigning index to one less than new index created.
    # blankDf = data.loc[(data['GoodValueGap'] > np.timedelta64(interpolation_time_threshold,'s')), ['Site', 'Measurement', 'Action', 'I']]
    blankDf = data.loc[(data['GoodValueGap'] > np.timedelta64(gap_time_threshold,'s')), ['Site', 'Measurement', 'Action', 'I']]
    blankDf['I'] = blankDf['I'] - 1
    # Add a gap marker
    blankDf['Gap'] = 'Gap'
    # set the index
    blankDf.set_index('I', inplace = True)
    # Re Index data
    data.set_index('I', inplace = True)
    # Add an empty Gap Column
    data['Gap'] = ''
    # Append the blankDf
    data = pd.concat([data, blankDf])
    data.sort_index(inplace = True)
    
    # Return the dataframe
    return data


def configParams_N(nemsStd):
    """
    Get the codified parameters relevant to the desired NEMS standard.
    
    Parameters
    ----------
    nemsStd : string
        A string describing the applicable NEMS standard.  Valid options are 
          Water Temperature - Estuarine, 
          Water Temperature - Non Estuarine,
          DO,
          DO (sat),
          Turbidity,
          Water Level - Rivers and Lakes mm - Stable Site,
          Water Level - Groundwater mm - Stable Site,
          Water Level - Sea mm - Stable Site,
          Water Level - Rivers and Lakes m - Stable Site,
          Water Level - Groundwater m - Stable Site,
          Water Level - Sea m - Stable Site,
          Water Level - Rivers and Lakes mm - Non-Stable Site,
          Water Level - Groundwater mm - Non-Stable Site,
          Water Level - Sea mm - Non-Stable Site,
          Water Level - Rivers and Lakes m - Non-Stable Site,
          Water Level - Groundwater m - Non-Stable Site,
          Water Level - Sea m - Non-Stable Site
          Not Available

    Returns
    -------
    A pandas dataframe.
        A Pandas dataframe of configuration values relevant for the NEMS standard.  A Codified version of NEMS.  Fields are:-
            NEMS_Standard
            BandUpperLimit
            ResolutionAllowed
            ResolutionDP
            Units
            MaxRecordInterval_mins
            ValidationFrequency_mons
            AccuracyToleranceAbs600
            AccuracyToleranceAbs500
            AccuracyTolerance%600
            AccuracyTolerance%500
            AccuracyReferenceTolerance%
            Notes

    """
    # Read the NEMS configurations in from a csv file.
    nemsConfigAll = pd.read_csv('NEMS_Continuous_Parameters.csv')
    
    # Filter for the rows relevant to the selected NEMS Standard.
    nemsConfig = nemsConfigAll[nemsConfigAll['NEMS_Standard'] == nemsStd]
    return nemsConfig


def configParams_Q(grossRangeFailBelow,
                 grossRangeFailAbove,
                 grossRangeSuspectBelow,
                 grossRangeSuspectAbove,
                 flatLineTolerance,
                 flatLineSuspectThreshold,
                 flatLineFailThreshold,
                 rateOfChangeThreshold,
                 spikeSuspectThreshold,
                 spikeFailThreshold):
    
    """
    Creates a  configuration disctionary for Qartod tests. 
    See documentation for description of each test and its inputs:
    https://ioos.github.io/ioos_qc/api/ioos_qc.html#module-ioos_qc.qartod
    
    Parameters
    ----------
    grossRangeFailBelow : float
        The value that a result will fail if it falls below.  Lowest value a sensor can achieve.
    grossRangeFailAbove : float
        The value that a result will fail if it goes above.  Highest value a sensor can achieve.
    grossRangeSuspectBelow : float
        The value that a result will be marked as suspect if it falls below.  Lowest value expected.
    grossRangeSuspectAbove : float
        The value that a result will be marked as suspect if it goes above.  Highest value expected.
    flatLineTolerance : int
        The number of seconds that a value is allowed to be unchanging.
    flatLineSuspectThreshold : float
        The tolerance allowed for flatline, ie the variability that would still cause results to be suspect, larger than fail threshold.
    flatLineFailThreshold : float
        The tolerance allowed for flatline, ie the variability that would cause results to fail.
    rateOfChangeThreshold : float
        The rate of change above which the value is flagged as failing.
    spikeSuspectThreshold : float
        The value that the spike test will be marked suspect above.
    spikeFailThreshold : float
        The value that the spike test will be marked fail above.
    Returns
    -------
    Dictionary
        A dictionary of configuration parameters for each Qartod test
    """    
    # QC configuration
    
    # 
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
            "fail_threshold": spikeFailThreshold, #3
            "method": 'differential',
            #"method": 'median',
          }#,
          #"aggregate": {}
        }
    }
    return qc_config

    
