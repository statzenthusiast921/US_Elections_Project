import pandas as pd
import numpy as np
from pandas.core.frame import DataFrame 
#from statsmodels.tsa.ar_model import AutoReg
from statsmodels.tsa.arima.model import ARIMA
#import pmdarima as pm


#Read in datasets
elections = pd.read_excel("/Users/jonzimmerman/Desktop/Data Projects/Elections Project/Data/FullElectionsData.xlsx",
                   dtype={"fips_code_lz": str})



#break out into dem vs. gop datasets
votes_data = elections[['state_name','fips_code_lz','dem_votes','gop_votes']]
#gop_votes_data = elections[['state_name','fips_code_lz','gop_votes']]

#Remove rows with no 2020 data (mostly Alaska)
s = votes_data.groupby("fips_code_lz").dem_votes.size().le(2)
no_votes = s[s].index.tolist()


filter_out = ~votes_data['fips_code_lz'].isin(no_votes)
filtered_votes = votes_data[filter_out]
#Remove problematic Hawaii county (only 2 rows of data)
#filtered_votes = filtered_votes[filtered_votes['fips_code_lz']!="15005"]


# test=filtered_dem.groupby(['fips_code_lz']).agg(['count'])
county = filtered_votes[filtered_votes['fips_code_lz']=='49021']

#Loop through data by county and predict 2024 results
forecasts = {}

# in each turn e.g., group == "A", values are [10, 18, 20, 36]
for group, values in county.groupby("fips_code_lz").gop_votes:
    # form the model and fit
    #Autoregressive (AR) Model
    #model = AutoReg(values, lags=1)

    #Moving Average (MA) Model
    #model = ARIMA(values, order=(0, 0, 1))

    #ARMA Model
    model = ARIMA(values, order=(1, 0, 1))

    result = model.fit()

    # predict
    prediction = result.forecast(steps=1)
    
    # store
    forecasts[group] = prediction

# after `for` ends, convert to DataFrame
all_predictions = pd.DataFrame(forecasts)
preds = all_predictions.T
preds.reset_index(inplace=True)
preds

# #Print out predictions - save to file
preds.to_excel("/Users/jonzimmerman/Desktop/demARIMA_predictions2024.xlsx",
             sheet_name='preds')  
