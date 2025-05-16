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
    
    # Clean column names (critical step!)
    ogb_raw_metal_df.columns = ogb_raw_metal_df.columns.str.strip()
    
    # Calculate water hardness FIRST
    ogb_raw_metal_df['Hardness (mg/L CaCO3)'] = (
        2.5 * (ogb_raw_metal_df['Calcium (Ca)'] / 1000) + 
        4.1 * (ogb_raw_metal_df['Magnesium (Mg)'] / 1000)
    )
    
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
        .groupby('Site')[metal_cols + ['Hardness (mg/L CaCO3)']]  # ADD HARDNESS HERE
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

processed_df, summary_df = load_and_process_metal_data()


# Load your summary statistics (from previous step)
summary_df = pd.read_csv("summary_statistics_by_site.csv")

# Load EQS thresholds
eqs_specific = pd.read_csv("freshwater_specific_pollutants_EQS_filtered.csv")
eqs_priority = pd.read_csv("freshwater_priority_hazardous_EQS_filtered.csv")

# Combine EQS data
eqs_combined = pd.concat([eqs_specific, eqs_priority], ignore_index=True)

eqs_dict = {}
for _, row in eqs_combined.iterrows():
    chem = row['Chemical']
    aa_eqs = row['AA-EQS (micrograms per litre)']
    mac_eqs = row['MAC-EQS (micrograms per litre)']
    eqs_dict[chem] = {'AA-EQS': aa_eqs, 'MAC-EQS': mac_eqs}

# Add Cadmium's annual load limit
eqs_dict['Cadmium'] = {'Annual Load Limit (kg)': 5}
for key in eqs_dict:
    if 'Cadmium water hardness' in key:
        eqs_dict[key]['Annual Load Limit (kg)'] = 5

results = []

# Iterate through each metal
for metal_col in summary_df.columns:
    if '_mean' in metal_col:
        # Extract metal name (e.g., "Cadmium (Cd)_mean" → "Cadmium")
        metal = metal_col.split('_')[0]
        chem = metal.split(' (')[0]  # General chemical name
        
        # Skip if no EQS data
        if chem not in eqs_dict:
            continue
            
        # Get thresholds
        aa_threshold = eqs_dict[chem].get('AA-EQS', np.nan)
        mac_threshold = eqs_dict[chem].get('MAC-EQS', np.nan)
        
        # Compare to AA-EQS (priority) or MAC-EQS if AA is NaN
        threshold = aa_threshold if not pd.isna(aa_threshold) else mac_threshold
        threshold_type = 'AA-EQS' if not pd.isna(aa_threshold) else 'MAC-EQS'
        
        # Check exceedance for all sites
        exceedance = summary_df[metal_col] > threshold
        
        # Record results
        for site, value, exceeds in zip(summary_df['Site'], summary_df[metal_col], exceedance):
            results.append({
                'Site': site,
                'Metal': metal,
                'Mean Concentration (µg/L)': value,
                'Threshold Type': threshold_type,
                'Threshold (µg/L)': threshold,
                'Exceedance': exceeds
            })
            
# Load hardness-mapped Cadmium EQS (from previous steps)
# Assuming you have a column 'Hardness (mg/L CaCO3)' in summary_df

#cadmium_results = []
#for _, row in summary_df.iterrows():
#    site = row['Site']
#    hardness = row['Hardness (mg/L CaCO3)']
#    mean_cd = row['Cadmium (Cd)_mean']
    
    # Determine EQS based on hardness
#    if hardness < 40:
#        eqs_data = eqs_priority[eqs_priority['Chemical'] == 'Cadmium water hardness less than 40 milligrams'].iloc[0]
#    elif 40 <= hardness < 50:
#        eqs_data = eqs_priority[eqs_priority['Chemical'] == 'Cadmium water hardness 40mg to less than 50mg'].iloc[0]
#    elif 50 <= hardness < 100:
#        eqs_data = eqs_priority[eqs_priority['Chemical'] == 'Cadmium water hardness 50mg to less than 100mg'].iloc[0]
#    elif 100 <= hardness < 200:
#        eqs_data = eqs_priority[eqs_priority['Chemical'] == 'Cadmium water hardness 100mg to less than 200mg'].iloc[0]
#    else:
#        eqs_data = eqs_priority[eqs_priority['Chemical'] == 'Cadmium water hardness 200mg or more'].iloc[0]
    
    # Compare
#    cadmium_results.append({
#        'Site': site,
#        'Metal': 'Cadmium (Cd)',
#        'Mean Concentration (µg/L)': mean_cd,
#        'Threshold Type': 'AA-EQS',  # All Cadmium EQS entries have AA-EQS
#        'Threshold (µg/L)': eqs_data['AA-EQS (micrograms per litre)'],
#        'Exceedance': mean_cd > eqs_data['AA-EQS (micrograms per litre)']
#    })

# Convert to DataFrames
main_results_df = pd.DataFrame(results)
#cadmium_df = pd.DataFrame(cadmium_results)

# Combine and save
#final_results = pd.concat([main_results_df, cadmium_df], ignore_index=True)
final_results = pd.concat([main_results_df], ignore_index=True)
final_results.to_csv('eqs_exceedance_report.csv', index=False)

# Print summary
print("\n=== Exceedance Summary ===")
print(final_results[['Site', 'Metal', 'Exceedance']].groupby(['Site', 'Metal']).max().unstack())