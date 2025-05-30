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
from matplotlib.colors import ListedColormap

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

# Define flow rates (L/s) for specific sites
flow_rates = {
    'Hard LV': 12.20,         # Hard Level
    'SPENCE level': 1.09,     # Spence Level
    'River Swale DS': 10400,  # River Swale
    'River Swale US': 10400   # Assume same flow for upstream/downstream
}

# Convert to annual flow (L/year)
annual_flow = {site: rate * 31536000 for site, rate in flow_rates.items()}  # 31,536,000 seconds/year

# Add annual flow to summary_df
summary_df['Annual Flow (L/year)'] = summary_df['Site'].map(annual_flow)

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

cadmium_results = []
for _, row in summary_df.iterrows():
    site = row['Site']
    hardness = row['Hardness (mg/L CaCO3)_mean']
    mean_cd = row['Cadmium (Cd)_mean']
    flow = row['Annual Flow (L/year)']
    
    # Skip sites without flow data (NaN)
    if pd.isna(flow):
        continue
    
    # Calculate annual load (kg/year)
    cd_load_kg_year = (mean_cd * flow) / 1e9  # µg/L * L/year → kg/year
    
    # Determine EQS based on hardness
    if hardness < 40:
        eqs_data = eqs_priority[eqs_priority['Chemical'] == 'Cadmium water hardness less than 40 milligrams'].iloc[0]
    elif 40 <= hardness < 50:
        eqs_data = eqs_priority[eqs_priority['Chemical'] == 'Cadmium water hardness 40mg to less than 50mg'].iloc[0]
    elif 50 <= hardness < 100:
        eqs_data = eqs_priority[eqs_priority['Chemical'] == 'Cadmium water hardness 50mg to less than 100mg'].iloc[0]
    elif 100 <= hardness < 200:
        eqs_data = eqs_priority[eqs_priority['Chemical'] == 'Cadmium water hardness 100mg to less than 200mg'].iloc[0]
    else:
        eqs_data = eqs_priority[eqs_priority['Chemical'] == 'Cadmium water hardness 200mg or more'].iloc[0]
    
    # Compare to concentration and annual load thresholds
    cadmium_results.append({
        'Site': site,
        'Metal': 'Cadmium (Cd)',
        'Mean Concentration (µg/L)': mean_cd,
        'Annual Load (kg/year)': cd_load_kg_year,
        'Threshold Type': 'AA-EQS Annual Load',
        'Threshold (kg/year)': 5,
        'Exceedance': cd_load_kg_year > 5 or mean_cd > eqs_data['AA-EQS (micrograms per litre)']
    })

# Existing concentration-based results
main_results_df = pd.DataFrame(results)
cadmium_load_df = pd.DataFrame(cadmium_results)

# Combine and save
final_results = pd.concat([main_results_df, cadmium_load_df], ignore_index=True)
final_results.to_csv('eqs_exceedance_report.csv', index=False)

# Print summary
print("\n=== Exceedance Summary ===")
print(final_results[['Site', 'Metal', 'Exceedance']].groupby(['Site', 'Metal']).max().unstack())





############################################

# Ensure output directory exists
OUTPUT_DIR = "figures"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Load data
summary_df = pd.read_csv("summary_statistics_by_site.csv")
results_df = pd.read_csv("eqs_exceedance_report.csv")

# Bar plots with error bars and thresholds
def plot_metal_barplots(summary_df, results_df, output_dir=OUTPUT_DIR):
    metals = sorted(results_df['Metal'].unique())
    for metal in metals:
        # Identify mean and SEM columns
        mean_col = next((c for c in summary_df.columns if c.startswith(metal) and c.endswith('_mean')), None)
        sem_col = next((c for c in summary_df.columns if c.startswith(metal) and c.endswith('_sem')), None)
        if not mean_col or not sem_col:
            continue
        df_m = summary_df[['Site', mean_col, sem_col]].copy()
        # Build threshold and exceedance dicts
        thr_df = results_df[results_df['Metal'] == metal].drop_duplicates('Site')[['Site', 'Threshold (µg/L)', 'Exceedance']]
        df_m = df_m.merge(thr_df, on='Site', how='left')
        # Plot
        fig, ax = plt.subplots(figsize=(10, 6))
        x = np.arange(len(df_m))
        # Colours: green below EQS, red above
        bar_colors = df_m['Exceedance'].map({False: '#2ca02c', True: '#d62728'})
        ax.bar(x, df_m[mean_col], yerr=df_m[sem_col], capsize=5,
               color=bar_colors, edgecolor='black')
        # EQS threshold line in dark blue
        ax.plot(x, df_m['Threshold (µg/L)'], linestyle='--', linewidth=2,
                color='darkblue', label='EQS Threshold')
        # Labels and title
        ax.set_xticks(x)
        ax.set_xticklabels(df_m['Site'], rotation=45, ha='right')
        ax.set_ylabel('Concentration (µg/L)')
        ax.set_title(f'{metal} Concentrations vs. EQS')
        ax.legend()
        plt.tight_layout()
        # Save
        fname = f"{metal.replace(' ', '_').replace('(','').replace(')','').replace('/','_')}_barplot.png"
        fig.savefig(os.path.join(output_dir, fname), dpi=300)
        plt.close(fig)

# Heatmap of exceedances
def plot_exceedance_heatmap(results_df, output_dir=OUTPUT_DIR):
    # Use pivot_table to handle any duplicate site-metal entries
    pivot = results_df.pivot_table(
        index='Site',
        columns='Metal',
        values='Exceedance',
        aggfunc='max',
        fill_value=False
    )
    data = pivot.astype(int)
    fig, ax = plt.subplots(figsize=(12, 8))
    sns.heatmap(
        data,
        cmap=ListedColormap(['#ffffff', '#d73027']),
        linewidths=0.5,
        linecolor='gray',
        cbar=False,
        ax=ax
    )
    ax.set_title('EQS Exceedance Heatmap')
    ax.set_xlabel('Metal')
    ax.set_ylabel('Site')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    fig.savefig(os.path.join(output_dir, 'exceedance_heatmap.png'), dpi=300)
    plt.close(fig)


# Define flow rates (L/s) for key sites
flow_rates = {
    "Hard LV": 12.20,          # Hard Level adit
    "SPENCE level": 1.09,       # Spence Level adit
    "River Swale US": 10400     # River Swale upstream
}

# UK annual significant load thresholds (kg/year) for SPECIFIC METALS
uk_annual_limits = {
    "Cadmium (Cd)": 5,   # Match EXACTLY how Cadmium appears in your column names
    "Lead (Pb)": 2000, 
    "Zinc (Zn)": 2500
}

def calculate_annual_loads(summary_df, flow_rates):
    """Calculate annual loads for sites with known flow rates."""
    load_sites = summary_df[summary_df["Site"].isin(flow_rates.keys())].copy()
    
    for metal_col in load_sites.columns:
        if "_mean" in metal_col:
            # Extract FULL metal name from column (e.g. "Cadmium (Cd)_mean" → "Cadmium (Cd)")
            full_metal_name = metal_col.split("_")[0]  
            load_sites[f"{full_metal_name}_load_kg_yr"] = load_sites.apply(
                lambda row: row[metal_col] * flow_rates[row["Site"]] * 0.031536,
                axis=1
            )
    return load_sites

# Generate compliance report
compliance = []
load_results = calculate_annual_loads(summary_df, flow_rates)

for _, row in load_results.iterrows():
    site = row["Site"]
    for metal, limit in uk_annual_limits.items():
        load_col = f"{metal}_load_kg_yr"  # Now matches "Cadmium (Cd)_load_kg_yr"
        if load_col in load_results.columns:
            load = row[load_col]
            compliance.append({
                "Site": site,
                "Metal": metal,
                "Annual Load (kg/yr)": load,
                "UK Limit (kg/yr)": limit,
                "Exceedance (%)": (load / limit) * 100
            })

compliance_df = pd.DataFrame(compliance)
compliance_df.to_csv("annual_load_compliance.csv", index=False)


def plot_annual_loads(compliance_df, output_dir="figures"):
    plt.figure(figsize=(12, 7))
    
    # Pivot data for better plotting
    plot_df = compliance_df.melt(
        id_vars=["Site", "Metal"],
        value_vars=["Annual Load (kg/yr)", "UK Limit (kg/yr)"],
        var_name="Type",
        value_name="Value"
    )
    
    # Create grouped bars
    sns.barplot(
        data=plot_df,
        x="Site",
        y="Value",
        hue="Metal",
        palette={"Cadmium (Cd)": "#d62728", "Lead (Pb)": "#2ca02c", "Zinc (Zn)": "#ff7f0e"},
        dodge=True  # Group bars for same metal together
    )
    
    # Add threshold line and annotations
    plt.axhline(5, color='#d62728', linestyle=':', alpha=0.5, label='Cadmium Limit')
    plt.axhline(2000, color='#2ca02c', linestyle=':', alpha=0.5, label='Lead Limit')
    plt.axhline(2500, color='#ff7f0e', linestyle=':', alpha=0.5, label='Zinc Limit')
    
    # Formatting
    plt.yscale('log')  # Use log scale for better visibility
    plt.ylabel("Annual Load (kg/year)")
    plt.title("Metal Loads vs UK Regulatory Limits")
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.savefig(f"{output_dir}/annual_load_comparison.png", dpi=300)
    plt.close()
plot_annual_loads(compliance_df)


def plot_ph_vs_sulfate(processed_df, output_dir="figures"):
    """Scatter plot of pH vs. sulfate to show NMD relationships."""
    plt.figure(figsize=(10, 6))
    
    # Handle NaN values in 'Site' and convert to string
    processed_df['Site'] = processed_df['Site'].fillna('Unknown').astype(str)
    
    # Extract data
    x = processed_df['pH']
    y = processed_df['Sulfate (SO4)']
    sites = processed_df['Site']
    
    # Color adit sites differently (check for NaN/strings safely)
    colors = [
        '#d62728' if ('Hard' in site) or ('SPENCE' in site) 
        else '#1f77b4' 
        for site in sites
    ]
    
    # Plot
    plt.scatter(x, y, c=colors, s=100, edgecolor='k', alpha=0.8)
    
    # Labels and annotations
    plt.xlabel('pH', fontsize=12)
    plt.ylabel('Sulfate (mg/L)', fontsize=12)
    plt.title('pH vs. Sulfate: Neutral Mine Drainage Signatures', fontsize=14)
    plt.grid(alpha=0.3)
    
    # Add reference text
    plt.text(7.5, 20, 'High sulfate ⇨ Active sulfide weathering\n'
             'Neutral pH ⇨ Carbonate buffering', 
             bbox=dict(facecolor='white', alpha=0.9))
    
    # Legend
    plt.scatter([], [], c='#d62728', edgecolor='k', label='Adit Discharges')
    plt.scatter([], [], c='#1f77b4', edgecolor='k', label='Other Sites')
    plt.legend(frameon=True, loc='upper left')
    
    plt.tight_layout()
    plt.savefig(f"{output_dir}/ph_vs_sulfate_scatter.png", dpi=300)
    plt.close()

# Run all plots
def main():
    plot_metal_barplots(summary_df, results_df)
    plot_exceedance_heatmap(results_df)
    plot_ph_vs_sulfate(processed_df)

if __name__ == '__main__':
    main()
