# importing required libraries
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
#%matplotlib inline
from sklearn.cluster import KMeans

#Load in elections data
elections = pd.read_excel("/Users/jonzimmerman/Desktop/Data Projects/Elections Project/Data/FullElectionsData.xlsx",
                   dtype={"fips_code_lz": str})

#Filter by appropriate year
elections2012 = elections[elections['year']==2012]
elections2016 = elections[elections['year']==2016]

#Join cluster data on election data
#cluster_data2012 = pd.read_excel("/Users/jonzimmerman/Desktop/Data Projects/Elections Project/Data//Cluster Data/ClusterData2012.xlsx", dtype={"fips_code_lz": str})
cluster_data2016 = pd.read_excel("/Users/jonzimmerman/Desktop/Data Projects/Elections Project/Data/Cluster Data/ClusterData2016.xlsx", dtype={"fips_code_lz": str})

elections_full = pd.merge(elections2016,cluster_data2016,how="left",on="fips_code_lz")
# print(elections2016.shape)
# print(cluster_data2016.shape)
# print(elections_full.shape)

elections_full.head()



X=elections_full[['per_gop','per_dem','PC_PI','Pop','Unemp_Rate','Median_Age','Female_Perc','White_Perc','Black_Perc','AmInd_Perc','Asian_Perc','Hisp_Perc','Vet_Perc','Foreign_Perc','Gini_Index','HH_Size','HSGrad_Perc','Bach_Perc','GradDeg_Perc','ViolentCrime','SQM_AreaLand']]

X.describe()
X = X.dropna()

corr = X.corr()

import seaborn as sns
ax = sns.heatmap(
    corr, 
    vmin=-1, vmax=1, center=0,
    cmap=sns.diverging_palette(20, 220, n=200),
    square=True
)
ax.set_xticklabels(
    ax.get_xticklabels(),
    rotation=45,
    horizontalalignment='right'
)

# standardizing the data
from sklearn.preprocessing import StandardScaler
scaler = StandardScaler()
data_scaled = scaler.fit_transform(X)


# defining the kmeans function with initialization as k-means++
kmeans = KMeans(n_clusters=2, init='k-means++')

# fitting the k means algorithm on scaled data
kmeans.fit(data_scaled)


# inertia on the fitted data
kmeans.inertia_


# fitting multiple k-means algorithms and storing the values in an empty list
SSE = []
for cluster in range(1,20):
    kmeans = KMeans(n_jobs = -1, n_clusters = cluster, init='k-means++')
    kmeans.fit(data_scaled)
    SSE.append(kmeans.inertia_)

# converting the results into a dataframe and plotting them
frame = pd.DataFrame({'Cluster':range(1,20), 'SSE':SSE})
plt.figure(figsize=(12,6))
plt.plot(frame['Cluster'], frame['SSE'], marker='o')
plt.xlabel('Number of clusters')
plt.ylabel('Inertia')



# k means using 8 clusters and k-means++ initialization
kmeans = KMeans(n_jobs = -1, n_clusters = 15, init='k-means++')
kmeans.fit(data_scaled)
pred = kmeans.predict(data_scaled)


frame = pd.DataFrame(data_scaled)
frame['cluster'] = pred
frame['cluster'].value_counts()

clusters = frame['cluster']

elections_full = elections_full.dropna()
elections_full['cluster'] = clusters.values


#elections_full.to_csv(r'/Users/jonzimmerman/Desktop/Data Projects/Elections Project/Data/Cluster Data/THECluster2016.csv',index=False)

# from urllib.request import urlopen
# import json
# with urlopen('https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json') as response:
#     counties = json.load(response)
# import plotly.express as px

# elections_filtered = elections_full[elections_full['cluster']==6]

# fig = px.choropleth_mapbox(elections_filtered, geojson=counties, locations='fips_code_lz', color='cluster',
#                                 hover_name="county_name", 
#                                 color_continuous_scale="Viridis",
#                                 range_color=(0, 21),
#                                 mapbox_style="carto-positron",
#                                 zoom=3, center = {"lat": 37.0902, "lon": -95.7129},
#                                 opacity=0.5)
                                


# fig.show()
            


