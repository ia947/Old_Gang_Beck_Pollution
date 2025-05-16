# -*- coding: utf-8 -*-
"""
Created on Wed May 14 12:21:21 2025

@author: isaac
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.io.img_tiles as cimgt
import seaborn as sns
import os
from SALib.sample import saltelli
from SALib.analyze import sobol
from tabulate import tabulate
from matplotlib.colors import LinearSegmentedColormap, BoundaryNorm

###############################
###### DATA LOADING & PREP #####
###############################

def load_and_process_metal_data():
    """Load and preprocess all required datasets"""
    # Load main data
    ogb_raw_df = pd.read_excel("OGB_raw_no_repeat.xlsx")
    
    # Identify metal columns (columns G to AC in the original data)
    metal_columns = ogb_raw_df.columns[6:29]
    
    # Convert metal values from mg/L to µg/L
    ogb_raw_df[metal_columns] = ogb_raw_df[metal_columns] * 1000
    
    # Save the results (optional)
    ogb_raw_df.to_csv('converted_metals_micrograms.csv', index=False)
    
    # Show confirmation
    print("Conversion complete. Columns converted:")
    print(list(metal_columns))
    
    
    return ogb_raw_df