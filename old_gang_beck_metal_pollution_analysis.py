import numpy as np
import pandas as pd
from scipy.optimize import minimize, curve_fit
import matplotlib.pyplot as plt
import seaborn as sns
from geopy.distance import geodesic
import SALib
import PourPy as pb


################################
###### LOAD FILTERED DATA ######
################################

ogb_df = pd.read_csv("old_gang_beck_processed_2025.csv")
fw_specific_pollutants_EQS = pd.read_csv("freshwater_specific_pollutants_EQS_filtered.csv")
fw_priority_hazardous_EQS = pd.read_csv("freshwater_priority_hazardous_EQS_filtered.csv")

print(ogb_df)

