# Old Gang Beck Metal Pollution Analysis

A reproducible Python workflow to process raw metal concentration data, compare site-level means against environmental quality standards (EQS), and generate clear visualizations (bar charts & heatmap) for exceedance reporting.

---

## Repository Structure

    .
    ├── data/
    │   ├── Old_Gang_beck_raw_data_2025.xlsx
    │   ├── freshwater_specific_pollutants_EQS_filtered.csv
    │   └── freshwater_priority_hazardous_EQS_filtered.csv
    │
    ├── results/
    │   ├── converted_metals_micrograms.csv
    │   ├── summary_statistics_by_site.csv
    │   └── eqs_exceedance_report.csv
    │
    ├── figures/
    │   ├── Cadmium_Cd_barplot.png
    │   ├── Zinc_Zn_barplot.png
    │   ├── …
    │   └── exceedance_heatmap.png
    │
    ├── old_gang_beck_metal_pollution_analysis.py
    ├── README.md
    └── requirements.txt

---

## Quickstart

1. **Clone the repo**  
       git clone https://github.com/yourusername/old-gang-beck-metal-pollution.git  
       cd old-gang-beck-metal-pollution

2. **Install dependencies**  
       pip install -r requirements.txt

3. **Place data files**  
   Copy your raw Excel and EQS CSV files into the `data/` folder.

4. **Run the analysis**  
       python old_gang_beck_metal_pollution_analysis.py

   - Generates processed CSVs in `results/`  
   - Produces bar charts & heatmap PNGs in `figures/`

---

## Structure and Workflow

### 1. Data Loading & Processing
- Reads `Old_Gang_beck_raw_data_2025.xlsx`  
- Cleans column names, converts metal units (mg/L → µg/L)  
- Calculates water hardness (Ca & Mg)  
- Groups by site to compute **mean** & **SEM**  
- Saves `converted_metals_micrograms.csv` & `summary_statistics_by_site.csv`

### 2. EQS Comparison
- Loads filtered EQS tables (`freshwater_specific_pollutants_EQS_filtered.csv`, `freshwater_priority_hazardous_EQS_filtered.csv`)  
- Builds lookup for AA-EQS and MAC-EQS values  
- Applies hardness-adjusted AA-EQS for Cadmium  
- Flags exceedances per site–metal and writes `eqs_exceedance_report.csv`

### 3. Visualization
- **Bar Charts** (`plot_metal_barplots`):  
  - Mean ± SEM per site  
  - Bars **green** (compliant) or **red** (exceedance)  
  - Dark-blue dashed line at the EQS threshold  
- **Heatmap** (`plot_exceedance_heatmap`):  
  - Binary exceedance matrix  
  - Red cells for exceedance, white for compliant  

---

## Requirements

Listed in `requirements.txt`:

    numpy
    pandas
    matplotlib
    seaborn
    cartopy
    SALib
    tabulate

Install via:

    pip install -r requirements.txt

---

## Usage Examples

    from old_gang_beck_metal_pollution_analysis import load_and_process_metal_data

    # 1. Preprocess raw data
    processed_df, summary_df = load_and_process_metal_data('data/Old_Gang_beck_raw_data_2025.xlsx')

    # 2. Generate results & figures
    if __name__ == '__main__':
        main()

---

## Configuration

- **Input paths**: Modify top-of-script `path=` arguments for alternate file locations.  
- **Output folders**: Change `OUTPUT_DIR` if you wish to save figures elsewhere.  
- **Metals list**: Add or remove priority metals in the `priority_metals` list to customise the analysis.

---

## License & Citation

This code is released under the MIT License. Please cite as:

> Isaac Abbott. (2025). _Old Gang Beck Metal Pollution Analysis_ (Version 1.0) [Software]. GitHub. https://github.com/ia947/Old_Gang_Beck_Pollution

---


## Author

**Isaac Abbott**  
– University of York, BSc Environmental Geography (3rd Year)  
– [ia947@york.ac.uk]  
