#!/usr/bin/env python
# coding: utf-8

# In[ ]:


# Name: LocateRestaurants.py
# Description: Count restaurants within 0.5 mile of each segment's centroid in a given road network of Sacramento using ArcGIS Pro
# Requirements: Network Analyst Extension
# Uses: arcpy, os, dbfread
# Given files: a) shape files Sacramento CA's road network; b) shape files of restaurants in Sacramento    

"""
Task can be accomplished using ArcGIS environment in 3 steps:
1. Obtain a network dataset
    My insitutional ArcGIS pro installation does not allow network dataset (ND) creation. I did this using ArcMap  
2. Run Network Analysis using Closest Facility (CF)
    a. Filter out restaurants beyond 200 feet from the network
    b. Create centroids from segments to be used as incidents in CF analysis
    c. Add restaurants as Facilities, and centroids as Incidents to network 
    d. Run CF
3. Postprocess obtained files to extract desired results i.e. segment, restaurant counts (0.5 miles from seg centroid)  
"""

# Import system modules
import arcpy
import os
import pandas as pd
from arcpy import env


    
"""
1. Create Network Dataset
"""
workspace = r"C:\Users\ahk53\Box\MyProject\GIST2" 
# manually created using ArcMap 
net_dat = os.path.join(r"C:\Users\ahk53\Box\MyProject\MyProject.gdb", "Net", "Net_ND")

"""
2. Run Network Analysis using Closest Facility
"""
# Set local variables
env.overwriteOutput = True
network = os.path.join(workspace, "sacramento_network.shp") 
restaurants =  os.path.join(workspace, "sacramento_restaurants.shp")

"""
2.a. Filter out restaurants beyond 200 feet from the network
"""

# arguments for Select by Location (SbL) 
# match those within distance of 200 ft
MATCH = "WITHIN_A_DISTANCE"
RADIUS = "200 Feet"

# Select by Location format: SelectLayerByLocation(in_layer, {overlap_type}, 
# {select_features}, {search_distance}, {selection_type}, {invert_spatial_relationship})
rest_200 = arcpy.management.SelectLayerByLocation(restaurants, 
                                                  MATCH, network, RADIUS)                

"""
2.b. Create centroids from segments to be used as incidents in CF analysis
"""
centroids = os.path.join(workspace, "segment_centers.shp")
# Feature (i.e. segment) to Point
arcpy.FeatureToPoint_management(network, centroids, 
                                "CENTROID")

"""
2.c. Create the Network Analysis Layer
"""
NETWORK_LAYER = "RestaurantsHalfMile" 
MODE = "Driving Time"
DIRECTION = "TO_FACILITIES"
MAX_REST = 100 # set an arbitrary number 100 as maximum restaurants to track in vicinity of centroid
DIST_CUTOFF = 804 #meters
VISUALIZE_ROUTES_AS = "STRAIGHT_LINES"

# Make a Network Analyst layer for CF analysis
result_object = arcpy.na.MakeClosestFacilityAnalysisLayer(net_dat, NETWORK_LAYER, MODE, DIRECTION, DIST_CUTOFF, MAX_REST, 
                                          None, "#", "#", VISUALIZE_ROUTES_AS)


"""
2.d. Add restaurants as Facilities and centroids as Incidents to network
"""
# Set the variables to call the tool
facilities = rest_200 #locate restaurants i.e. facilites that fall within 200 ft
incidents = centroids # from the centroids i.e. incidents

#Get the layer object from the result object. The closest facility layer can
#now be referenced using the layer object.
layer_object = result_object.getOutput(0)

#Get the names of all the sublayers within the closest facility layer.
sublayer_names = arcpy.na.GetNAClassNames(layer_object)
#Stores the layer names that we will use later
facilities_layer_name = sublayer_names["Facilities"]
incidents_layer_name = sublayer_names["Incidents"]

#Load the restaurants as Facilities using the default field mappings and
#search tolerance
arcpy.na.AddLocations(layer_object, facilities_layer_name,
                        facilities)

#Load the centroids as Incidents
arcpy.na.AddLocations(layer_object, incidents_layer_name, 
                      incidents)

"""
2.e. Run CF analysis
"""
#Solve the closest facility layer
arcpy.na.Solve(layer_object)

"""
3. Post-processing Route file generated from CF analysis to extract desired results i.e. 
segment, restaurant counts (0.5 miles from seg centroid).
Routes map each instance of Incident (centroids) to Facility (restaurant)
"""
 
output_table =  os.path.join(workspace, "GIST2.gdb", "output")
# export attribute table of Routes  
arcpy.management.CopyRows(r"RestaurantsHalfMile\Routes", output_table, '')

# convert data to DBF
arcpy.conversion.TableToDBASE(output_table, r"C:\Users\ahk53\Box\MyProject\GIST2")

# read the Data in DBF version
table = DBF("output.dbf")

# convert DBF to dataframe
frame = pd.DataFrame(iter(table))
# choose relevant columns - IncidentID (segment centroids), facility_ID (restaurants)
frame.head()
output = frame[frame.columns[[5, 0]]

#read the network file to merge with output
network_DF = DBF("GIST2/sacramento_network.dbf")
network_DF = pd.DataFrame(iter(tmp))

#Get counts of each Centroid to get how many restaurants it goes to
summary = output.groupby(['IncidentID'])[['FacilityID']].count().reset_index()
summary.columns = ['IncidentID', 'Num_Restaurants']
summary.head

# prepare to merge summary table (restaurant numbers) with the network (which has segments)
TOTAL_SEGS = network_DF.shape[0]
network_DF['key'] = pd.Series(range(1, TOTAL_SEGS+1))

# merge               
Result = pd.merge(network_DF, summary, how = 'left', left_on = ['key'], right_on = ['IncidentID'])
Result = Result[['SEGMENT', 'Num_Restaurants']]

# fill NaN values with 0 and write the file
Result['Num_Restaurants'] = Result['Num_Restaurants'].fillna(0) 
Result.to_csv("sac_restCount_halfMile_frmCentroid.csv", header = Result.columns)


# In[ ]:





# In[ ]:




