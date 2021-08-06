# -*- coding: utf-8 -*-
"""
Created on Fri 4 June 2021
@author: Jeff Cooke

Utility functions for analysing timeseries information.
"""

import tsData_utils as tsu
import pandas as pd
import numpy as np

#plots on the client
from bokeh.layouts import gridplot
from bokeh.plotting import figure, show, output_notebook
from bokeh.models import ColumnDataSource, FactorRange, HoverTool
from bokeh.transform import factor_cmap

def runAnalysis(requestType='Hilltop', 
                base_url=None, 
                file=None, 
                site=None, 
                measurement=None, 
                from_date=None, 
                to_date=None):
    """
    Main Analysis function.
    
    Outputs graphs for display
    """
    
    # Get the data
    data = tsu.getData(requestType='Hilltop', 
                   base_url=base_url, 
                   file=file, 
                   site=site, 
                   measurement=measurement, 
                   from_date=from_date, 
                   to_date=to_date)
    
    # Calculate the rate of change
    
    data['ValueDiff'] = data['Value'].diff().fillna(0)
    data['TimeDiff'] = data['DateTime'].diff().astype('timedelta64[s]').fillna(1)
    data['Rate of Change'] = data['ValueDiff'].div(data['TimeDiff'])
    
    # Calculate the 'spikiness', the difference between the value and the averate of the adjacent values.  A simplified second derivative.
    data['Value-1'] = data['Value'].shift(+1)
    data['Value+1'] = data['Value'].shift(-1)
    data['Spikiness'] = data['Value'] - ((data['Value-1'] + data['Value+1']) / 2)
    data['Spikiness'] = data['Spikiness'].fillna(0)
    
    # plot the data
    p = plot_timeseries(data=data)
    f = plot_single_flow_duration_curve(data=data)
    rc = plot_single_flow_duration_curve(data=data, field='Rate of Change', absolute=True)
    s = plot_single_flow_duration_curve(data=data, field='Spikiness', absolute=True)
    
    show(p)
    show(f)
    show(rc)
    show(s)
    

def plot_timeseries(data=pd.DataFrame()):
    if data.empty:
        print("Plot has no data associated with it")
        
    # Create a plotting dataframe
    plot_df = data[['DateTime', 'Measurement', 'Value']].copy()
    
    source = ColumnDataSource(data=plot_df)
    
    measurementName = plot_df['Measurement'][0]
    
            
    TOOLTIPS = [
        #("index", "$index"),
        ("time", "@DateTime{%F %T}"),
        ("value", "@Value"),
        ]

    p1 = figure(x_axis_type="datetime", \
                title=measurementName + " Time Series.", \
                plot_height=300, \
                plot_width=600, \
                tools=['pan', 'box_zoom', 'wheel_zoom', 'undo', 'redo', 'reset', 'save'] \
                #source = source,\
                )
        
    #p1.toolbar.active_inspect = [hover, crosshair]
    p1.grid.grid_line_alpha=0.3
    p1.xaxis.axis_label = 'Time'
    p1.yaxis.axis_label = 'Observation Value'

    p1.line(x = 'DateTime', y = 'Value',  legend_label='Data', color='#a6bddb', source=source)
    p1.circle(x = 'DateTime', y='Value', size=2, color='#2b8cbe', alpha=1, source=source)
        
    p1.add_tools(HoverTool(tooltips=TOOLTIPS, formatters={'@DateTime': 'datetime', }))
    
    return p1
    #show(gridplot([[p1]], )) #plot_width=800, plot_height=400))
    
    
def plot_single_flow_duration_curve(data=pd.DataFrame(), field='Value', absolute=False):
    """
    Plots a single fdc into an ax.
    Modified from https://stackoverflow.com/questions/49304516/plotting-a-flow-duration-curve-for-a-range-of-several-timeseries-in-python/49304517#:~:text=Plotting%20a%20flow%20duration%20curve%20for%20a%20range%20of%20several%20timeseries%20in%20Python,-python%20matplotlib%20time&text=Flow%20duration%20curves%20are%20a,often%20certain%20values%20are%20reached.

    :param ax: matplotlib subplot object
    :param timeseries: list like iterable
    :param kwargs: dict, keyword arguments for matplotlib

    return: subplot object with a flow duration curve drawn into it
    """
    if data.empty:
        print("Plot has no data associated with it")
    
    if absolute:
        timeseries = np.abs(data[field].tolist())   
    else:
        timeseries = data[field].tolist() 
    #timeseries = data.tolist()    
    
    # Get the probability
    exceedence = np.arange(1., len(timeseries) + 1) / len(timeseries)
    exceedence *= 100
    
    # Create a plotting dataframe
    
    
    plot_df = pd.DataFrame({'exceedence': exceedence, 
                            #'value': sorted(timeseries, reverse=True)})
                            'value': np.sort(timeseries)[::-1]})
    source = ColumnDataSource(data=plot_df)
    
    measurementName = data['Measurement'][0]
    
    TOOLTIPS = [
        #("index", "$index"),
        ("exceedence", "@exceedence"),
        ("value", "@value"),
        ]

    fd = figure(title="Percentage exceedence curve for " + field +" of " + measurementName, \
                plot_height=300, \
                plot_width=600, \
                tools=['pan', 'box_zoom', 'wheel_zoom', 'undo', 'redo', 'reset', 'save'] \
                #source = source,\
                )
        
    #p1.toolbar.active_inspect = [hover, crosshair]
    fd.grid.grid_line_alpha=0.3
    fd.xaxis.axis_label = 'Percentage Of Values Exceeding.'
    fd.yaxis.axis_label = field +" of " + measurementName

    fd.line(x = 'exceedence', y = 'value',  legend_label='Data', color='#a6bddb', source=source)
    fd.circle(x = 'exceedence', y = 'value', size=2, color='#2b8cbe', alpha=1, source=source)
        
    fd.add_tools(HoverTool(tooltips=TOOLTIPS, formatters={'@DateTime': 'datetime', }))
    # Plot the curve, check for empty kwargs
    #if kwargs is not None:
    #    ax.plot(exceedence, sorted(timeseries, reverse=True), **kwargs)
    #else:
    #    ax.plot(exceedence, sorted(timeseries, reverse=True))
    
    return fd
