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

def load_and_process_metal_data(path="Old_Gang_beck_raw_data_2025.xlsx"):
    """Load raw data, convert metals to µg/L, and compute site‐level summary stats."""
    # Load main data
    ogb_raw_metal_df = pd.read_excel(path)
    
    # Identify metal columns
    priority_metals = [
        'Cadmium (Cd)', 'Lead (Pb)', 'Nickel (Ni)', 'Zinc (Zn)',
        'Cobalt (Co)', 'Boron (B)', 'Manganese (Mn)', 'Iron (Fe)',
        'Chromium (Cr)', 'Copper (Cu)', 'Silver (Ag)'
    ]
    
    # ensure they actually exist
    metal_cols = [m for m in priority_metals if m in ogb_raw_metal_df.columns]
    if len(metal_cols) < len(priority_metals):
        missing = set(priority_metals) - set(metal_cols)
        raise KeyError(f"Missing expected metal columns: {missing}")
    
    # Convert mg/L → µg/L
    ogb_raw_metal_df[metal_cols] = ogb_raw_metal_df[metal_cols] * 1000
    
    # Derive a clean site name by stripping anything after 'repeat'
    ogb_raw_metal_df['Site'] = ogb_raw_metal_df['Label'].str.replace(r'\s*repeat.*$', '', regex=True)
    
    # Compute summary statistics (mean & SEM) per site
    summary = (
        ogb_raw_metal_df
        .groupby('Site')[metal_cols]
        .agg(['mean', 'sem'])
        .reset_index()
    )
    # flatten MultiIndex columns
    summary.columns = [
        'Site'
    ] + [
        f"{metal}_{stat}" 
        for metal, stat in summary.columns.tolist()[1:]
    ]
    
    # Save processed data and summary
    ogb_raw_metal_df.to_csv("converted_metals_micrograms.csv", index=False)
    summary.to_csv("summary_statistics_by_site.csv", index=False)
    
    return ogb_raw_metal_df, summary

if __name__ == "__main__":
    processed_df, summary_df = load_and_process_metal_data()
    print("Processed data head:")
    print(processed_df.head())
    print("\nSummary statistics head:")
    print(summary_df.head())