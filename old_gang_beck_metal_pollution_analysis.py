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
    ogb_raw_df.to_csv("converted_metals_micrograms.csv", index=False)
    
    # Show confirmation
    print("Conversion complete. Columns converted:")
    print(list(metal_columns))
    
    
    return ogb_raw_df

# Load converted metal concentration dataframe
converted_metals_micrograms_df = pd.read_csv("converted_metals_micrograms.csv")
print(converted_metals_micrograms_df)

# Calculate water hardness in mg/L of CaCO3
# Formula: Water Hardness = 2.5 * [Ca] + 4.1 * [Mg]
# Ensure Calcium (Ca) and Magnesium (Mg) are in mg/L (divide by 1000 if in µg/L)
converted_metals_micrograms_df['Hardness (mg/L CaCO3)'] = (2.5 * (converted_metals_micrograms_df['Calcium (Ca)'] / 1000) + (4.1 * (converted_metals_micrograms_df['Magnesium (Mg)'] / 1000)))

# Filter the relevant metals from the earlier list against EQS contents
priority_metals = ['Cadmium (Cd)', 'Lead (Pb)', 'Nickel (Ni)', 'Zinc (Zn)', 
                   'Cobalt (Co)', 'Boron (B)', 'Manganese (Mn)', 'Iron (Fe)', 
                   'Chromium (Cr)', 'Copper (Cu)', 'Silver (Ag)']
conv_metals_df_filtered = converted_metals_micrograms_df[['Unnamed: 0', 'Grid Ref', 'Hardness (mg/L CaCO3)'] + priority_metals]
print(conv_metals_df_filtered)