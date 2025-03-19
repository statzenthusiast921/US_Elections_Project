import pandas as pd
import numpy as np
import dash
from dash import dash_table
from dash import dcc
from dash import html
import os
from urllib.request import urlopen
import json
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State 
import plotly.express as px
import plotly.graph_objects as go


#Read in datasets
#1.) Full Elections Data

url1 = 'https://raw.githubusercontent.com/statzenthusiast921/US_Elections_Project/refs/heads/main/Data/FullElectionsData_updated2025.csv'

elections = pd.read_csv(url1, encoding="latin1")
elections['fips_code_lz'] = np.where(
    elections['fips_code_lz'].astype(str).str.len() == 4,
    '0' + elections['fips_code_lz'].astype(str),
    elections['fips_code_lz'].astype(str)
)

#2 and #3.) Cluster Data
url2 = 'https://raw.githubusercontent.com/statzenthusiast921/US_Elections_Project/refs/heads/main/Data/THECluster2012.csv'
url3 = 'https://raw.githubusercontent.com/statzenthusiast921/US_Elections_Project/refs/heads/main/Data/THECluster2016.csv'
url4 = 'https://raw.githubusercontent.com/statzenthusiast921/US_Elections_Project/refs/heads/main/Data/THECluster2020.csv'


election2012_filtered = pd.read_csv(url2, encoding="latin1")
election2016_filtered = pd.read_csv(url3, encoding="latin1")
election2020_filtered = pd.read_csv(url4, encoding="latin1")

#----- Fix fips code so we can plot stuff
election2012_filtered['fips_code_lz'] = np.where(
    election2012_filtered['fips_code_lz'].astype(str).str.len() == 4,
    '0' + election2012_filtered['fips_code_lz'].astype(str),
    election2012_filtered['fips_code_lz'].astype(str)
)

election2016_filtered['fips_code_lz'] = np.where(
    election2016_filtered['fips_code_lz'].astype(str).str.len() == 4,
    '0' + election2016_filtered['fips_code_lz'].astype(str),
    election2016_filtered['fips_code_lz'].astype(str)
)

election2020_filtered['fips_code_lz'] = np.where(
    election2020_filtered['fips_code_lz'].astype(str).str.len() == 4,
    '0' + election2020_filtered['fips_code_lz'].astype(str),
    election2020_filtered['fips_code_lz'].astype(str)
)

election_choices = ['2012 Election', '2016 Election', '2020 Election']


url5 = 'https://raw.githubusercontent.com/statzenthusiast921/US_Elections_Project/refs/heads/main/Data/vote_totals_2024.csv'
preds = pd.read_csv(url5)
preds['year'] = 2024

preds['dem_votes_actuals_formatted'] = preds['dem_votes_actuals'].copy()
preds['dem_votes_actuals_formatted'] = preds['dem_votes_actuals_formatted'].astype(float).map("{:,.0f}".format)

preds['dem_votes_preds_formatted'] = preds['dem_votes_preds'].copy()
preds['dem_votes_preds_formatted'] = preds['dem_votes_preds_formatted'].astype(float).map("{:,.0f}".format)

preds['gop_votes_actuals_formatted'] = preds['gop_votes_actuals'].copy()
preds['gop_votes_actuals_formatted'] = preds['gop_votes_actuals_formatted'].astype(float).map("{:,.0f}".format)

preds['gop_votes_preds_formatted'] = preds['gop_votes_preds'].copy()
preds['gop_votes_preds_formatted'] = preds['gop_votes_preds_formatted'].astype(float).map("{:,.0f}".format)

preds['fips_code_lz'] = np.where(
    preds['fips_code_lz'].astype(str).str.len() == 4,
    '0' + preds['fips_code_lz'].astype(str),
    preds['fips_code_lz'].astype(str)
)
preds['dem_gop_actuals_total'] = preds['dem_votes_actuals'] + preds['gop_votes_actuals']
preds['dem_gop_preds_total'] = preds['dem_votes_preds'] + preds['gop_votes_preds']

preds['per_dem_preds'] = preds['dem_votes_preds'] /preds['dem_gop_preds_total']
preds['per_gop_preds'] = preds['gop_votes_preds'] /preds['dem_gop_preds_total']

preds['per_dem_actuals'] = preds['dem_votes_actuals'] /preds['dem_gop_actuals_total']
preds['per_gop_actuals'] = preds['gop_votes_actuals'] /preds['dem_gop_actuals_total']

preds['margin_actuals'] = abs(preds['gop_votes_actuals'] - preds['dem_votes_actuals'])
preds['margin_preds'] = abs(preds['gop_votes_preds'] - preds['dem_votes_preds'])

preds['perc_margin_actuals'] = preds['margin_actuals'] /(preds['dem_gop_actuals_total'])
preds['perc_margin_preds'] = preds['margin_preds'] /(preds['dem_gop_preds_total'])


preds['perc_margin_actuals_formatted'] = preds['perc_margin_actuals'].copy()
preds['perc_margin_actuals_formatted'] = preds['perc_margin_actuals_formatted'].astype(float).map("{:.1%}".format)

preds['perc_margin_preds_formatted'] = preds['perc_margin_preds'].copy()
preds['perc_margin_preds_formatted'] = preds['perc_margin_preds_formatted'].astype(float).map("{:.1%}".format)




#----- Join lat/lon on preds df
elections_latlon = elections[['fips_code_lz','year','Dem_EV','Rep_EV','Lat','Lon','AvgLat','AvgLon']]
preds = pd.merge(preds, elections_latlon, how='left', on=['year','fips_code_lz'])

#----- Create win column
state_preds = preds.groupby('state_name')[['dem_votes_preds', 'gop_votes_preds']].sum().reset_index()
state_preds['win'] = np.where(
    state_preds['dem_votes_preds'] > state_preds['gop_votes_preds'], "Democratic", "Republican"
)
state_preds = state_preds[['state_name','win']]
preds = pd.merge(preds, state_preds, how='left', on=['state_name'])

#----- Fix Virginia Lat/Lons
mask1 = (preds['state_name'] == "Virginia") & (preds['AvgLat'].isna())
preds.loc[mask1, 'AvgLat'] = -78.517302

mask2 = (preds['state_name'] == "Virginia") & (preds['AvgLon'].isna())
preds.loc[mask2, 'AvgLon'] = 37.563641

#----- Prediction dataset for 2028
url6 = 'https://raw.githubusercontent.com/statzenthusiast921/US_Elections_Project/refs/heads/main/Data/df2028.csv'
preds2028 = pd.read_csv(url6)
preds2028['year'] = 2028

preds2028.drop(columns=['Avglat'], inplace=True)
preds2028['fips_code_lz'] = preds2028['fips_code_lz'].astype('str')
preds2028['fips_code_lz'] = np.where(
    preds2028['fips_code_lz'].str.len() == 4,
    "0" + preds2028['fips_code_lz'],
    preds2028['fips_code_lz']
)



coords = preds[['fips_code_lz','AvgLon','AvgLat','Lon','Lat']].drop_duplicates()
preds2028 = pd.merge(preds2028, coords, how = 'left', on = ['fips_code_lz'])

preds2028['dem_votes_formatted'] = preds2028['dem_votes'].copy()
preds2028['dem_votes_formatted'] = preds2028['dem_votes_formatted'].astype(float).map("{:,.0f}".format)

preds2028['gop_votes_formatted'] = preds2028['gop_votes'].copy()
preds2028['gop_votes_formatted'] = preds2028['gop_votes_formatted'].astype(float).map("{:,.0f}".format)

preds2028['perc_margin_formatted'] = preds2028['perc_margin'].copy()
preds2028['perc_margin_formatted'] = preds2028['perc_margin_formatted'].astype(float).map("{:,.0f}".format)

#----- Fix Virginia coordinates
mask3 = (preds2028['state_name'] == "Virginia") & (preds2028['AvgLat'].isna())
preds2028.loc[mask3, 'AvgLat'] = -78.517302

mask4 = (preds2028['state_name'] == "Virginia") & (preds2028['AvgLon'].isna())
preds2028.loc[mask4, 'AvgLon'] = 37.563641


#----- Fix fips code in 2024 for Virginia
fips_va_2028 = preds2028[preds2028['state_name']=="Virginia"][['state_name','county_name','fips_code_lz']]
fips_va_2028_renamed = fips_va_2028.rename(columns={'fips_code_lz': 'correct_fips'})
preds = preds.merge(fips_va_2028_renamed, on=['state_name', 'county_name'], how='left')
preds['fips_code_lz'] = preds.apply(
    lambda row: row['correct_fips'] if (row['state_name'] == 'Virginia' and row['fips_code_lz'] == '99999') else row['fips_code_lz'],
    axis=1
)



#----- Get Lat/Lon in for VA for both 2024 and 2028 preds
va_lat_lon = elections[elections['state_name']=="Virginia"][['state_name','county_name','fips_code_lz','Lat','Lon']].drop_duplicates()
va_lat_lon_renamed = va_lat_lon.rename(
    columns={
        'Lat': 'Lat_update', 
        'Lon': 'Lon_update'
    }
)

# Function to update a dataset
def update_lat_lon(df):
    df = df.merge(va_lat_lon_renamed, on=['state_name', 'county_name', 'fips_code_lz'], how='left')
    df['Lat'] = df['Lat_update'].combine_first(df['Lat'])
    df['Lon'] = df['Lon_update'].combine_first(df['Lon'])
    return df.drop(columns=['Lat_update', 'Lon_update'])

preds = update_lat_lon(preds)
preds2028 = update_lat_lon(preds2028)


#Fix cluster columns

# 1. get rid of cluster 0
election2012_filtered['cluster'] = election2012_filtered['cluster']+1
election2016_filtered['cluster'] = election2016_filtered['cluster']+1
election2020_filtered['cluster'] = election2020_filtered['cluster']+1


election2012_filtered['cluster'] = election2012_filtered['cluster'].astype('str')
election2016_filtered['cluster'] = election2016_filtered['cluster'].astype('str')
election2020_filtered['cluster'] = election2020_filtered['cluster'].astype('str')

#2.)
election2012_filtered['% GOP'] = (election2012_filtered['per_gop']*100).round(1)
election2012_filtered['% DEM'] = (election2012_filtered['per_dem']*100).round(1)

election2016_filtered['% GOP'] = (election2016_filtered['per_gop']*100).round(1)
election2016_filtered['% DEM'] = (election2016_filtered['per_dem']*100).round(1)

election2020_filtered['% GOP'] = (election2020_filtered['per_gop']*100).round(1)
election2020_filtered['% DEM'] = (election2020_filtered['per_dem']*100).round(1)
#3.)
election2012_filtered['% White'] = election2012_filtered['White_Perc'].round(1)
election2016_filtered['% White'] = election2016_filtered['White_Perc'].round(1)
election2020_filtered['% White'] = election2020_filtered['White_Perc'].round(1)


election2012_filtered['% Black'] = election2016_filtered['Black_Perc'].round(1)
election2016_filtered['% Black'] = election2016_filtered['Black_Perc'].round(1)
election2020_filtered['% Black'] = election2020_filtered['Black_Perc'].round(1)



#4.)
election2012_filtered['% High School Diploma'] = election2012_filtered['HSGrad_Perc'].round(1)
election2016_filtered['% High School Diploma'] = election2016_filtered['HSGrad_Perc'].round(1)
election2020_filtered['% High School Diploma'] = election2020_filtered['HSGrad_Perc'].round(1)

election2012_filtered['% Bachelors Degree'] = election2012_filtered['Bach_Perc'].round(1)
election2016_filtered['% Bachelors Degree'] = election2016_filtered['Bach_Perc'].round(1)
election2020_filtered['% Bachelors Degree'] = election2020_filtered['Bach_Perc'].round(1)

#5.)
election2012_filtered['% Women'] = election2012_filtered['Female_Perc'].round(1)
election2016_filtered['% Women'] = election2016_filtered['Female_Perc'].round(1)
election2020_filtered['% Women'] = election2020_filtered['Female_Perc'].round(1)

#6.)
election2012_filtered['Unemployment Rate'] = election2012_filtered['Unemp_Rate'].round(1)
election2016_filtered['Unemployment Rate'] = election2016_filtered['Unemp_Rate'].round(1)
election2020_filtered['Unemployment Rate'] = election2020_filtered['Unemp_Rate'].round(1)

#7.)
election2012_filtered['% Margin'] = (election2012_filtered['perc_margin']).astype(float).map("{:.1%}".format)
election2016_filtered['% Margin'] = (election2016_filtered['perc_margin']).astype(float).map("{:.1%}".format)
election2020_filtered['% Margin'] = (election2020_filtered['perc_margin']).astype(float).map("{:.1%}".format)

#Create new columns
elections['gop_win']=np.where(elections['per_gop']>elections['per_dem'], 1, 0)
elections['dem_win']=np.where(elections['per_dem']>elections['per_gop'], 1, 0)
elections['match_vote']=np.where(
                            ((elections['Dem_EV']>elections['Rep_EV']) & 
                            (elections['per_dem']>elections['per_gop'])) |

                            ((elections['Rep_EV']>elections['Dem_EV']) &
                            (elections['per_gop']>elections['per_dem'])),1,0)
elections['other_perc'] = 1 - elections['gop_demperc']
elections['other_perc_formatted'] = elections['other_perc'].copy()
elections['other_perc_formatted'] = elections['other_perc_formatted'].astype(float).map("{:.1%}".format)

elections['perc_margin_formatted'] = elections['perc_margin'].copy()
elections['perc_margin_formatted'] = elections['perc_margin_formatted'].astype(float).map("{:.1%}".format)





#Rename columns for table #1
elections.rename(columns={'state_name': 'State', 
                          'county_name': 'County', 
                          'gop_votes': 'GOP Votes',
                          'year': 'Year',
                          'margin': 'Margin',
                          'perc_margin_formatted': '% Margin',
                          'dem_votes': 'DEM Votes'}, inplace=True)

elections['GOP Votes'] = elections['GOP Votes'].apply(lambda x : "{:,}".format(x))
elections['DEM Votes'] = elections['DEM Votes'].apply(lambda x : "{:,}".format(x))
elections['Margin'] = elections['Margin'].apply(lambda x : "{:,}".format(x))
elections['County'] = np.where(
    elections['County'].str.contains(r'\bSt\.', regex=True), 
    elections['County'].str.replace(r'\bSt\.', 'Saint', regex=True), 
    elections['County']
)

#Formalize table order
table_show = elections[["State","County","Year","DEM Votes","GOP Votes","Margin","% Margin"]]
table_show['Year'] = table_show['Year'].astype(str)



#Assign styles to tabs
tabs_styles = {
    'height': '44px'
}
tab_style = {
    'borderBottom': '1px solid #d6d6d6',
    'padding': '6px',
    'fontWeight': 'bold',
    'color':'white',
    'backgroundColor': '#222222'

}

tab_selected_style = {
    'borderTop': '1px solid #d6d6d6',
    'borderBottom': '1px solid #d6d6d6',
    'backgroundColor': '#626ffb',
    'color': 'white',
    'padding': '6px'
}

#Load in shape files for choropleth maps
with urlopen('https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json') as response:
    counties = json.load(response)

#create objects to be used with interactive components
year_choices = elections['Year'].unique()
state_choices = elections['State'].sort_values().unique()
state_choices2 = state_choices[state_choices != 'Alaska']

county_choices = elections['County'].sort_values().unique()


#Create a dictionary of state-county key-value pairs for clustering dropdowns
elections2012 = elections[elections['Year']==2012]
elections2016 = elections[elections['Year']==2016]
elections2020 = elections[elections['Year']==2020]


state_to_county = elections.groupby('State')['County'].agg(list).to_dict()
state_to_county2012 = elections2012.groupby('State')['County'].agg(list).to_dict()
state_to_county2016 = elections2016.groupby('State')['County'].agg(list).to_dict()
state_to_county2020 = elections2020.groupby('State')['County'].agg(list).to_dict()

app = dash.Dash(__name__,
                #external_stylesheets=[dbc.themes.SANDSTONE],
                assets_folder=os.path.join(os.curdir,"assets")
                )
server = app.server
app.layout = html.Div([
    dcc.Tabs(
        #colors={"primary": "gold","border": "white"},
        children=[
#Tab #1 --> Welcome Tab
        dcc.Tab(label='Welcome',value='tab-1',style=tab_style, selected_style=tab_selected_style,
               children=[
                   html.Div([
                       html.H1(dcc.Markdown('''**Welcome To My US Presidential Elections Dashboard!**'''),style={'color':'white'}),
                       html.Br()
                   ]),
                   
                   html.Div([
                        html.P(dcc.Markdown('''**What is the purpose of this dashboard?**'''),style={'color':'white'}),
                   ],style={'text-decoration': 'underline'}),
                   html.Div([
                       html.P("This dashboard attempts to answer several questions:",style={'color':'white'}),
                       html.P("1.) How has the United States vote for President has changed over time?",style={'color':'white'}),
                       html.P("2.) What are the characteristics of counties that vote similarly?",style={'color':'white'}),
                       html.P("3.) What will the results of the next election look like?",style={'color':'white'})

                   ]),
                   html.Div([
                       html.P(dcc.Markdown('''**What data is being used for this analysis?**'''),style={'color':'white'}),
                   ],style={'text-decoration': 'underline'}),
                   
                   html.Div([
                       html.P(["Data from each US presidential election from 1960 to 2024 was included in this analysis.  Most of the data was gathered from this ", html.A("Github repository",href="https://github.com/cilekagaci/us-presidential-county-1960-2016")," covering elections from 1960 to 2016.  Data for the 2020 election was obtained from this ",html.A(" repository.",href="https://github.com/tonmcg/US_County_Level_Election_Results_08-20")]),
                       html.P(["To inform the clustering algorithm, county-level socioeconomic data was pulled from this link" ,html.A(" here ",href="https://www.ahrq.gov/sdoh/data-analytics/sdoh-data.html"), "from the Agency for Healthcare Research and Quality."])
                   ]),
                   html.Div([
                       html.P(dcc.Markdown('''**What are the limitations of this data?**''')),
                   ],style={'text-decoration': 'underline'}),
                   html.Div(
                       children=[
                        html.P("Data was pulled from multiple sources and combined.  The data sources may have had different standards and/or methods of collecting and maintaining information."),
                        html.P(["Further, data for Alaska was available, but was not presented with the standard FIPS county code identifier, therefore it was not conducive for regular plotting procedures. Thus, vote estimates from this ", html.A('link',href="https://github.com/tonmcg/US_County_Level_Election_Results_08-20/issues/2"), " were used to take advantage of their consistency with the FIPS county code format.  This was used as the authorative source of data for Alaska, which only had data from 1960 through 2016."])
                        ]
                    )


               ]),
#Tab #2 --> All Data Tab
        dcc.Tab(label='All Data',value='tab-2',style=tab_style, selected_style=tab_selected_style,
                children=[
                    dash_table.DataTable(id='table',
                                        columns=[{"name": i, "id": i} for i in table_show.columns],
                                        style_data_conditional=[{
                                            'if': {'row_index': 'odd'},'backgroundColor': 'rgb(248, 248, 248)'}
                                        ],
                                        style_header={'backgroundColor': 'rgb(230, 230, 230)','fontWeight': 'bold'},
                                        filter_action='native',
                                        style_data={'width': '150px', 'minWidth': '150px', 'maxWidth': '150px','overflow': 'hidden','textOverflow': 'ellipsis'},
                                        sort_action='native',sort_mode="multi",
                                        page_action="native", page_current= 0,page_size= 20,                     
                                        data=table_show.to_dict('records')
                    )
               ]),
#Tab #3 --> Electoral Country Map Tab
        dcc.Tab(label="National Results",value='tab-3',style=tab_style, selected_style=tab_selected_style,
            children=[
                #Modal Instructions 1
                html.Div([
                    dbc.Button("Click Here for Instructions", id="open1",color='secondary',style={"fontSize":18}),
                    dbc.Modal([
                        dbc.ModalHeader("Instructions"),
                        dbc.ModalBody(
                            children=[
                                html.P("To the right of this button, you will find the controls for this page.  You can select any election year from 1960 to 2024 to change the map below."),
                                html.P("Use the radio button to change between the county map and the vote total map.")
                            ]
                        ),
                        dbc.ModalFooter(
                            dbc.Button("Close", id="close1", className="ml-auto")
                        ),
                    ],id="modal1"),
                ],style={'width': '25%','display': 'inline-block','vertical-align': 'top'}),
                html.Div([
                    dcc.Slider(id='slider1',
                               min=year_choices.min(),
                               max=year_choices.max(),
                               step=4,
                               marks={1960: '1960',
                                      1964: '1964',
                                      1968: '1968',
                                      1972: '1972',
                                      1976: '1976',
                                      1980: '1980',
                                      1984: '1984',
                                      1988: '1988',
                                      1992: '1992',
                                      1996: '1996',
                                      2000: '2000',
                                      2004: '2004',
                                      2008: '2008',
                                      2012: '2012',
                                      2016: '2016',
                                      2020: '2020',
                                      2024: '2024'
                                    },
                              value=year_choices.max()
                    )
                ],style={'width': '50%','display': 'inline-block','textAlign': 'center','vertical-align':'top'}),
                #Spacing
                html.Div([
                    html.P('')
                ],style={'width':'10%','display': 'inline-block'}),
                html.Div([
                    dbc.RadioItems(
                        id='radio1',
                        options=[
                            {'label': ' Vote % Map', 'value': 'Vote % Map'},
                            {'label': ' Vote Total Map', 'value': 'Vote Total Map'}
                        ],
                        value='Vote % Map',
                        labelStyle={'display': 'inline-block','text-align': 'left'}
                    )
                ],style={'width': '15%','display': 'inline-block'}),
                html.Div([
                    #dcc.Loading(
                        dcc.Graph(id='us_map')
                    #)
                ],style={'width': '100%','display': 'inline-block','text-align': 'left'}),
                html.Div([
                    dcc.Graph(id='ev_graph')
                ],style={'width': '100%','display': 'inline-block','text-align': 'center'})
            ]
        ),
#Tab #4 --> County Level Results Tab
        dcc.Tab(label="State Results",value='tab-4',style=tab_style, selected_style=tab_selected_style,
            children=[
              #Modal Instructions 2
                html.Div([
                    dbc.Button("Click Here for Instructions", id="open2",color='secondary',style={"fontSize":18}),
                    dbc.Modal([
                        dbc.ModalHeader("Instructions"),
                        dbc.ModalBody(
                            children=[
                                html.P("To the right of this button, you will find the controls for this page.  You can select any election year from 1960 to 2024 to change the map below."),
                                html.P("Choose a state from the dropdown menu to view results by county for your preferred state."),
                                html.P("If you click on any county on the map, the graph on the right will populate with the % of the vote earned by the two major parties plotted over time for the selected county.")
                            ]
                        ),
                        dbc.ModalFooter(
                            dbc.Button("Close", id="close2", className="ml-auto")
                        ),
                    ],id="modal2"),
                ],style={'width': '25%','display': 'inline-block','vertical-align': 'top'}),
                #Control Panel
                html.Div([
                    dcc.Slider(id='slider2',
                               min=year_choices.min(),
                               max=year_choices.max(),
                               step=4,
                               marks={1960: '1960',
                                      1964: '1964',
                                      1968: '1968',
                                      1972: '1972',
                                      1976: '1976',
                                      1980: '1980',
                                      1984: '1984',
                                      1988: '1988',
                                      1992: '1992',
                                      1996: '1996',
                                      2000: '2000',
                                      2004: '2004',
                                      2008: '2008',
                                      2012: '2012',
                                      2016: '2016',
                                      2020: '2020',
                                      2024: '2024'
                                    },
                              value=year_choices.max()
                    ),
                ],style={'width': '50%','display': 'inline-block','text-align': 'center'}),
                #Spacing
                html.Div([
                    html.P('')
                ],style={'width':'10%','display':'inline-block'}),
                html.Div([
                    dcc.Dropdown(
                        id='dropdown1',
                        options=[{'label': i, 'value': i} for i in state_choices],
                        value=state_choices[0]
                    )
                ],style={'width': '15%','display': 'inline-block','text-align': 'center'}),
                html.Div([
                    dbc.Row(id='card_state_county_header'),
                    dbc.Row(id='card_state_county_details')
                ]),
                #State Map with County Choropleth
                html.Div([
                    #dcc.Loading(
                        dcc.Graph(id='state_map')
                    #)
                ],style={'width': '50%','display': 'inline-block','text-align': 'center'}),
                #Party Line % Graph
                html.Div([
                    dcc.Graph(id='party_line_graph')
                ],style={'width': '50%','display': 'inline-block','text-align': 'center'}),
                html.Pre(id='click-data')
            ]
        ),
#Tab #5 --> Clustering Tab
        dcc.Tab(label="Clustering",value='tab-5',style=tab_style, selected_style=tab_selected_style,
            children=[
            #Modal Instructions #3
                html.Div([
                    dbc.Button("Click Here for Instructions", id="open3",color='secondary',style={"fontSize":18}),
                    dbc.Modal([
                        dbc.ModalHeader("Instructions"),
                        dbc.ModalBody(
                            children=[
                                html.P("To the right of this button, you will find the controls for this page.  Select a state from the first dropdown box, and then select a county from the second dropdown box.  These selections should populate the map below showing other counties that were contained in the same cluster."),
                                html.P("Use the radio button to change between clusters calculated for the 2012 election vs. the 2016 election.")
                            ]
                        ),
                        dbc.ModalFooter(
                            dbc.Button("Close", id="close3", className="ml-auto")
                        ),
                    ],id="modal3"),
                ],style={'width': '25%','display': 'inline-block','vertical-align': 'top'}),
                html.Div([
                    #State Dropdown
                    dcc.Dropdown(
                        id='dropdown2',
                        options=[{'label': i, 'value': i} for i in state_choices],
                        value=state_choices[0]
                    )
                ],style={'width':'25%','display':'inline-block','vertical-align': 'top'}),
                html.Div([
                    #County Dropdown which is populated from state dropdown
                    dcc.Dropdown(
                        id='dropdown3',
                        options=[{'label': i, 'value': i} for i in county_choices],
                        value=county_choices[0]
                    )
                ],style={'width':'25%','display':'inline-block','vertical-align': 'top'}),
                #Spacing
                html.Div([
                    html.P('')
                ],style={'width':'10%','display':'inline-block'}),
                html.Div([
                    #Choose between 2012, 2016, 2020 election years
                    dcc.Dropdown(
                        # Formally radio2
                        id='dropdown4',
                        options=[{'label': i, 'value': i} for i in election_choices],
                        value=election_choices[0]
                    )
                  
                ],style={'width':'15%','display':'inline-block','vertical-align':'top','text-align': 'left'}),

                html.Div([
                    dbc.Row(id='cluster_county_header'),
                    dbc.Row(id='cluster_stats_card_row')
                ],style={'width': '100%','display': 'inline-block','text-align': 'left','vertical-align':'top'}),


                #Cluster Map
                html.Div([
                    #dcc.Loading(
                        dcc.Graph(id='cluster_map')
                    #)
                ],style={'width': '100%','display': 'inline-block','text-align': 'left','vertical-align':'top'}),
        
                #Modal Instructions #4
                html.Div([
                    dbc.Row(dbc.Button('Click Here for Full Cluster Details',size='lg',id='open4')),
                    dbc.Modal(
                        children=[
                            dbc.ModalHeader("Detailed Cluster Statistics"),
                            dbc.ModalBody(
                                children=[
                                    html.P(id="cluster_modal_text",style={'overflow':'auto','maxHeight':'400px'})
                                ]
                            ),
                            dbc.ModalFooter(
                                dbc.Button("Close", id="close4", className="ml-auto")
                            ),
                        ],id="modal4")
                ],style={'width':'100%','display':'inline-block'})             
            ]
        ),
#Tab #6 --> Prediction 2024 Evaluation Tab
        dcc.Tab(label="2024 Evaluation",value='tab-6',style=tab_style, selected_style=tab_selected_style,
                 children=[
            #Modal Instructions #5
                html.Div([
                    dbc.Button("Click Here for Instructions", id="open5",color='secondary',style={"fontSize":18}),
                    dbc.Modal([
                        dbc.ModalHeader("Instructions"),
                        dbc.ModalBody(
                            children=[
                                html.P("To the right of this button, you will find the controls for this page."),
                                html.P("Click on the 'Country View' button to see the 2024 predictions at the national level."),
                                html.P("Click on the 'State View' button to see the 2024 predictions at a specific state level.  \
                                        Click the counties on the map in this view to see the predictions for a specific county.")
                            ]
                        ),
                        dbc.ModalFooter(
                            dbc.Button("Close", id="close5", className="ml-auto")
                        ),
                    ],id="modal5"),
                ],style={'width': '25%','display': 'inline-block','vertical-align': 'top'}),
                #Title - need something in the middle for symmetry
                html.Div([
                    html.P(dcc.Markdown('''**2024 US Presidential Election Predictions**'''))
                ],style={'width':'50%','display': 'inline-block','fontSize':20,'vertical-align': 'top','text-align': 'center'}),
                #Spacing
                html.Div([
                    html.P('')
                ],style={'width':'10%','display':'inline-block'}),
                #Change View Radio Button
                html.Div([
                    dbc.RadioItems(
                        id='radio3',
                        options=[
                            {'label': ' Country View', 'value': 'Country View'},
                            {'label': ' State View', 'value': 'State View'}
                        ],
                        value='Country View',
                        labelStyle={'display': 'inline-block'}
                    )
                ],style={'width':'15%','display':'inline-block','vertical-align':'top','text-align': 'left'}),
                html.Div([
                    dbc.Row(id="preds_card_row_header"),
                    dbc.Row(id="preds_card_row_totals")
                ],style={'width': '100%','display': 'inline-block'}),
                #Dropdown and Map
                html.Div(
                    children=[
                        dcc.Dropdown(
                            id='dropdown5',
                            options=[{'label': i, 'value': i} for i in state_choices2],
                            value=state_choices2[0]
                        ),
                ],style={'width': '100%','display': 'inline-block','text-align': 'left','vertical-align':'top'}),
                html.Div([
                        dcc.Graph(id='predictions_map2024')
                ],style={'width': '50%','display': 'inline-block','text-align': 'left','vertical-align':'top'}),
                html.Div([
                        dcc.Graph(id='actuals_v_preds2024')
                ],style={'width': '50%','display': 'inline-block','text-align': 'left','vertical-align':'top'})
        
           
                ]
            ),
        #Tab #7 --> Prediction 2028  Tab
        dcc.Tab(label="2028 Predictions",value='tab-7',style=tab_style, selected_style=tab_selected_style,
                 children=[
            #Modal Instructions #5
                html.Div([
                    dbc.Button("Click Here for Instructions", id="open6",color='secondary',style={"fontSize":18}),
                    dbc.Modal([
                        dbc.ModalHeader("Instructions"),
                        dbc.ModalBody(
                            children=[
                                html.P("To the right of this button, you will find the controls for this page."),
                                html.P("Click on the 'Country View' button to see the 2024 predictions at the national level."),
                                html.P("Click on the 'State View' button to see the 2024 predictions at a specific state level.  \
                                        Click the counties on the map in this view to see the predictions for a specific county.")
                            ]
                        ),
                        dbc.ModalFooter(
                            dbc.Button("Close", id="close6", className="ml-auto")
                        ),
                    ],id="modal6"),
                ],style={'width': '25%','display': 'inline-block','vertical-align': 'top'}),
                #Title - need something in the middle for symmetry
                html.Div([
                    html.P(dcc.Markdown('''**2028 US Presidential Election Predictions**'''))
                ],style={'width':'50%','display': 'inline-block','fontSize':20,'vertical-align': 'top','text-align': 'center'}),
                #Spacing
                html.Div([
                    html.P('')
                ],style={'width':'10%','display':'inline-block'}),
                #Change View Radio Button
                html.Div([
                    dbc.RadioItems(
                        id='radio4',
                        options=[
                            {'label': ' Country View', 'value': 'Country View'},
                            {'label': ' State View', 'value': 'State View'}
                        ],
                        value='Country View',
                        labelStyle={'display': 'inline-block'}
                    )
                ],style={'width':'15%','display':'inline-block','vertical-align':'top','text-align': 'left'}),
                html.Div([
                    dbc.Row(id="preds_card_row_header_2028"),
                    dbc.Row(id="preds_card_row_totals_2028")
                ],style={'width': '100%','display': 'inline-block'}),
                #Dropdown and Map
                html.Div(
                    children=[
                        dcc.Dropdown(
                            id='dropdown6',
                            options=[{'label': i, 'value': i} for i in state_choices],
                            value=state_choices[0]
                        ),
                ],style={'width': '100%','display': 'inline-block','text-align': 'left','vertical-align':'top'}),
                html.Div([
                        dcc.Graph(id='predictions_map2028')
                ],style={'width': '50%','display': 'inline-block','text-align': 'left','vertical-align':'top'}),
                html.Div([
                        dcc.Graph(id='comparison_2024_v_2028')
                ],style={'width': '50%','display': 'inline-block','text-align': 'left','vertical-align':'top'})
        
        
           
                ]
        )

    ])
])


#Configure Reactivity for Tab Colors

@app.callback(Output('tabs-content-inline', 'children'),
              Input('tabs-styled-with-inline', 'value'))

def render_content(tab):
    if tab == 'tab-1':
        return html.Div([
            html.H3('Tab content 1')
        ])
    elif tab == 'tab-2':
        return html.Div([
            html.H3('Tab content 2')
        ])
    elif tab == 'tab-3':
        return html.Div([
            html.H3('Tab content 3')
        ])
    elif tab == 'tab-4':
        return html.Div([
            html.H3('Tab content 4')
        ])
    elif tab == 'tab-5':
        return html.Div([
            html.H3('Tab content 4')
        ])
    elif tab == 'tab-6':
        return html.Div([
            html.H3('Tab content 4')
        ])



#Configure Reactivity for Country Map on Tab 3
@app.callback(
    Output('us_map','figure'),
    #Output('loading','children'),
    Input('slider1','value'),
    Input('radio1','value'))

def update_vote_map(year_select,radio_select):
        new_df = elections[elections['Year']==year_select]
        if "Vote % Map" in radio_select:

            fig = px.choropleth_mapbox(new_df, geojson=counties, 
                                locations='fips_code_lz', 
                                color='per_gop',
                                hover_name="County", 
                                color_continuous_scale="balance",
                                mapbox_style="carto-positron",

                                zoom=3, center = {"lat": 37.0902, "lon": -95.7129},
                                opacity=0.5,
                                hover_data = {
                                    "fips_code_lz":False,
                                    "per_gop":False,
                                    "State":True,
                                    "County":True,
                                    "DEM Votes":True,
                                    "GOP Votes":True,
                                    "% Margin":True
                                },
                                labels={'State':'State',
                                    'County':'County',
                                    'DEM Votes':'Democratic Votes',
                                    'GOP Votes':'Republican Votes',
                                    '% Margin':'% Margin'}
                                )
            fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0},coloraxis_showscale=True)
            fig.update_coloraxes(colorbar=dict(title='D - R Scale',showticklabels=False))

            return fig

        else:
            fig = px.scatter_mapbox(new_df, lat="Lon", lon="Lat", hover_name="County", 
                            color_continuous_scale="balance",
                            color="per_gop",
                            hover_data = {
                                    "gop_dem_total":False,
                                    "Lon":False,
                                    "Lat":False,
                                    "fips_code_lz":False,
                                    "per_gop":False,
                                    "State":True,
                                    "County":True,
                                    "DEM Votes":True,
                                    "GOP Votes":True,
                                    "% Margin":True
                            },
                            labels={'State':'State',
                                    'County':'County',
                                    'DEM Votes':'Democratic Votes',
                                    'GOP Votes':'Republican Votes',
                                    '% Margin':'% Margin'},
                            size = "gop_dem_total",
                            zoom=3,center = {"lat": 37.0902, "lon": -95.7129})
            fig.update_layout(mapbox_style="carto-positron",margin={"r":0,"t":0,"l":0,"b":0})
            fig.update_coloraxes(colorbar=dict(title='D - R Scale',showticklabels=False))

            return fig

#Configure Reactivity for EV Map on Tab 3
@app.callback(
    Output('ev_graph','figure'),
    Input('slider1','value'))

def update_ev_graph(year_select):
        new_df = elections[elections['Year']==year_select]

        Dem = ['Democratic']
        Rep = ['Republican']


        fig = go.Figure(data=[
            go.Bar(name='Dem', y=Dem, x=new_df['Dem_EV'],orientation='h'),
            go.Bar(name='Rep', y=Rep, x=new_df['Rep_EV'],orientation='h')

        ])
        fig.add_vline(x=270,line_width=4, line_dash="dash")

        # Change the bar mode
        fig.update_layout(barmode='group',
                          showlegend=False,
                          margin={"r":0,"t":0,"l":0,"b":0},
                          height=150,
                          xaxis_title="Electoral Votes"            
        )
    
        return fig

#Configure Reactivity for State/County Map on Tab 4
@app.callback(
    Output('state_map','figure'),
    Input('dropdown1','value'),
    Input('slider2','value'))

def update_state_county_map(state_select,year_select):
        new_df = elections[elections['State']==state_select]
        new_df2 = new_df[new_df['Year']==year_select]
        new_df2['perc_margin'] = new_df2['perc_margin'].astype(float).map("{:.1%}".format)

        avg_lat = new_df2['AvgLat'].mean()
        avg_lon = new_df2['AvgLon'].mean()

        #Zoom In 1 from Main Group
        if 'Rhode Island' in state_select or 'Connecticut' in state_select \
            or 'Massachusetts' in state_select or 'Delaware' in state_select or 'Vermont' in state_select \
            or 'Maryland' in state_select or 'New Jersey' in state_select:
        
            fig = px.choropleth_mapbox(new_df2, geojson=counties, 
                                    locations='fips_code_lz', 
                                    #----- This color argument needs to be set at country level
                                    #----- counties are using only state range for colors
                                    color='per_gop',
                                    range_color=(elections['per_gop'].min(), elections['per_gop'].max()),  

                                    color_continuous_scale="balance",
                                    mapbox_style="carto-positron",
                                    hover_name="County", 
                                    zoom=6,center = {"lat": avg_lon, "lon": avg_lat},opacity=0.5,
                                    labels={'DEM Votes':'Democratic Votes',
                                            'GOP Votes':'Republican Votes',
                                            'perc_margin':'% Margin'},
                                    hover_data = {
                                        "fips_code_lz":False,
                                        "per_gop":False,
                                        "State":False,
                                        "County":False,
                                        "DEM Votes":True,
                                        "GOP Votes":True,
                                        "perc_margin":True
                                    })
            fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0},coloraxis_showscale=False)            
                
            return fig

        elif 'District of Columbia' in state_select:
            fig = px.choropleth_mapbox(new_df2, geojson=counties, locations='fips_code_lz',
                                    color='per_gop',
                                    range_color=(elections['per_gop'].min(), elections['per_gop'].max()), 
                                    color_continuous_scale="balance",
                                    mapbox_style="carto-positron",hover_name="County", 
                                    zoom=8, center = {"lat": avg_lon, "lon": avg_lat},opacity=0.5,
                                    labels={'DEM Votes':'Democratic Votes',
                                            'GOP Votes':'Republican Votes',
                                            'perc_margin':'% Margin'},
                                    hover_data = {
                                        "fips_code_lz":False,
                                        "per_gop":False,
                                        "State":False,
                                        "County":False,
                                        "DEM Votes":True,
                                        "GOP Votes":True,
                                        "perc_margin":True
                                    })
            fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0},coloraxis_showscale=False)
            #fig.update_geos(fitbounds="locations")    
            return fig

        elif 'Alaska' in state_select:
            fig = px.choropleth_mapbox(new_df2, geojson=counties, locations='fips_code_lz', color='per_gop',
                                    color_continuous_scale="balance",mapbox_style="carto-positron",hover_name="County", zoom=2, 
                                    range_color=(elections['per_gop'].min(), elections['per_gop'].max()), 

                                    center = {"lat": avg_lon, "lon": avg_lat},opacity=0.5,
                                    labels={'DEM Votes':'Democratic Votes',
                                            'GOP Votes':'Republican Votes',
                                            'perc_margin':'% Margin'},
                                    hover_data = {
                                        "fips_code_lz":False,
                                        "per_gop":False,
                                        "State":False,
                                        "County":False,
                                        "DEM Votes":True,
                                        "GOP Votes":True,
                                        "perc_margin":True
                                    }
                                    )
            fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0},coloraxis_showscale=False)
            #fig.update_geos(fitbounds="locations")    

            return fig

        #Zoom Out One More from Main Pack Group
        elif 'California' in state_select or 'Texas' in state_select:
            fig = px.choropleth_mapbox(new_df2, geojson=counties, locations='fips_code_lz', color='per_gop',
                                    color_continuous_scale="balance", mapbox_style="carto-positron",hover_name="County", 
                                    zoom=4, center = {"lat": avg_lon, "lon": avg_lat}, opacity=0.5,
                                    range_color=(elections['per_gop'].min(), elections['per_gop'].max()), 
                                    labels={'DEM Votes':'Democratic Votes',
                                            'GOP Votes':'Republican Votes',
                                            'perc_margin':'% Margin'},
                                    hover_data = {
                                        "fips_code_lz":False,
                                        "per_gop":False,
                                        "State":False,
                                        "County":False,
                                        "DEM Votes":True,
                                        "GOP Votes":True,
                                        "perc_margin":True
                                    })
            fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0},coloraxis_showscale=False)
            #fig.update_geos(fitbounds="locations")    

            return fig
        else:
            fig = px.choropleth_mapbox(new_df2, geojson=counties, locations='fips_code_lz', color='per_gop',
                                    color_continuous_scale="balance",mapbox_style="carto-positron",hover_name="County", 
                                    zoom=5, center = {"lat": avg_lon, "lon": avg_lat},opacity=0.5,
                                    range_color=(elections['per_gop'].min(), elections['per_gop'].max()), 
                                    labels={'DEM Votes':'Democratic Votes',
                                            'GOP Votes':'Republican Votes',
                                            'perc_margin':'% Margin'},
                                    hover_data = {
                                        "fips_code_lz":False,
                                        "per_gop":False,
                                        "State":False,
                                        "County":False,
                                        "DEM Votes":True,
                                        "GOP Votes":True,
                                        "perc_margin":True
                                    })
            fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0},coloraxis_showscale=False)
            return fig

#Configure Reactivity for Party Line on Tab 4
@app.callback(
    Output('party_line_graph','figure'),
    Input('dropdown1','value'),
    Input('state_map','clickData')
)

def update_party_line_graph(state_select,click_county_select):

        if click_county_select:
            new_df = elections[elections['State']==state_select]
            county_id = click_county_select['points'][0]['customdata'][3]
            new_df2 = new_df[new_df['County']==county_id]

            counties = new_df["County"].values
            if county_id not in counties:
                new_df = elections[elections["State"] == state_select]
                county_id = new_df["County"].iloc[0]
                new_df2 = new_df[new_df["County"] == county_id]
        else:
            new_df = elections[elections['State']==state_select]
            county_id = new_df['County'].iloc[0]
            new_df2 = new_df[new_df['County']==county_id]

        fig = go.Figure()

        fig.add_trace(go.Scatter(x=new_df2['Year'], y=new_df2['per_dem'], name = 'DEM %',
                         line=dict(color='royalblue', width=4)))
        fig.add_trace(go.Scatter(x=new_df2['Year'], y=new_df2['per_gop'], name = 'GOP %',
                         line=dict(color='firebrick', width=4)))
        fig.update_layout(
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="auto",
                x=0.5
            ),
            title=f"Results from {county_id}, {state_select}"
        )
        fig.update_layout(
            title={'x':0.5,'xanchor': 'center','yanchor': 'top'},
            yaxis_tickformat = '%'
        )
        fig.update_yaxes(tickformat=".0%")


        return fig


#Configure reactivity for state-county cards
@app.callback(
    Output('card_state_county_header','children'),
    Output('card_state_county_details','children'),
    Input('dropdown1','value'),
    Input('state_map','clickData'))

def update_cards_for_state_stats(state_select,click_county_select):
    
    if click_county_select:
        new_df = elections[elections['State']==state_select]
        county_id = click_county_select['points'][0]['customdata'][3]
        new_df2 = new_df[new_df['County']==county_id]

        counties = new_df["County"].values
        if county_id not in counties:
            new_df = elections[elections["State"] == state_select]
            county_id = new_df["County"].iloc[0]
            new_df2 = new_df[new_df["County"] == county_id]
    else:
        new_df = elections[elections['State']==state_select]
        county_id = new_df['County'].iloc[0]
        new_df2 = new_df[new_df['County']==county_id]

    card1 = dbc.Card([
        dbc.CardBody([
            html.H5(f'{county_id} Metrics', className="card-title"),
        ])
    ],
    style={'display': 'inline-block',
           'width': '100%',
           'text-align': 'center',
           'background-color': '#70747c',
           'color':'white',
           'fontWeight': 'bold',
           'fontSize':16},
    outline=True)

    card2 = dbc.Card([
        dbc.CardBody([
            html.P('Voted for Winner'),
            html.H6(f'{new_df2["match_vote"].sum()} out of {new_df2.shape[0]} Elections'),
        ])
    ],
    style={'display': 'inline-block',
           'width': '20%',
           'text-align': 'center',
           'background-color': '#70747c',
           'color':'white',
           'fontWeight': 'bold',
           'fontSize':16},
    outline=True)

    card3 = dbc.Card([
        dbc.CardBody([
            html.P('Voted for Democrat'),
            html.H6(f'{new_df2["dem_win"].sum()} out of {new_df2.shape[0]} Elections'),
        ])
    ],
    style={'display': 'inline-block',
           'width': '20%',
           'text-align': 'center',
           'background-color': '#70747c',
           'color':'white',
           'fontWeight': 'bold',
           'fontSize':16},
    outline=True)

    card4 = dbc.Card([
        dbc.CardBody([
            html.P('Voted for Republican'),
            html.H6(f'{new_df2["gop_win"].sum()} out of {new_df2.shape[0]} Elections'),
        ])
    ],
    style={'display': 'inline-block',
           'width': '20%',
           'text-align': 'center',
           'background-color': '#70747c',
           'color':'white',
           'fontWeight': 'bold',
           'fontSize':16},
    outline=True)

    card5 = dbc.Card([
        dbc.CardBody([
            html.P('Closest Election'),
            html.H6(f"{new_df2[new_df2['perc_margin']==new_df2['perc_margin'].min()]['% Margin'].values[0]} margin in \
                      {new_df2[new_df2['perc_margin']==new_df2['perc_margin'].min()]['Year'].values[0]}"),
        ])
    ],
    style={'display': 'inline-block',
           'width': '20%',
           'text-align': 'center',
           'background-color': '#70747c',
           'color':'white',
           'fontWeight': 'bold',
           'fontSize':16},
    outline=True)

    card6 = dbc.Card([
        dbc.CardBody([
            html.P('Largest Third Party Vote'),
            html.H6(f"{new_df2[new_df2['other_perc']==new_df2['other_perc'].max()]['other_perc_formatted'].values[0]} of votes in \
                      {new_df2[new_df2['other_perc']==new_df2['other_perc'].max()]['Year'].values[0]}"),
        ])
    ],
    style={'display': 'inline-block',
           'width': '20%',
           'text-align': 'center',
           'background-color': '#70747c',
           'color':'white',
           'fontWeight': 'bold',
           'fontSize':16},
    outline=True)

    return (card1) , (card2, card3, card4, card5, card6)

#Configure reactivity for dynamic dropboxes - 1st one informs the 2nd
@app.callback(
    Output('dropdown3', 'options'),
    Output('dropdown3', 'value'),
    Input('dropdown4','value'),
    Input('dropdown2', 'value'))
def set_county_options(dd4,selected_state):
    if '2012 Election' in dd4:
        return [{'label': i, 'value': i} for i in state_to_county2012[selected_state]], state_to_county2012[selected_state][0]
    elif '2016 Election' in dd4:
        return [{'label': i, 'value': i} for i in state_to_county2016[selected_state]], state_to_county2016[selected_state][0]
    else:
        return [{'label': i, 'value': i} for i in state_to_county2020[selected_state]], state_to_county2020[selected_state][0]


#Configure reactivity for cluster map
@app.callback(
    Output('cluster_map','figure'),
    Input('dropdown4','value'),
    Input('dropdown2','value'),
    Input('dropdown3','value')
)
def cluster_map(dd4, dd_select_state, dd_select_county):

    if '2012 Election' in dd4:
        e_data = election2012_filtered
        state_data = e_data[e_data['state_name']==dd_select_state]
        county_data = state_data[state_data['county_name']==dd_select_county]
        filtered = e_data[e_data['cluster']==county_data['cluster'].values[0]]

    elif '2016 Election' in dd4:
        e_data = election2016_filtered
        state_data = e_data[e_data['state_name']==dd_select_state]
        county_data = state_data[state_data['county_name']==dd_select_county]
        filtered = e_data[e_data['cluster']==county_data['cluster'].values[0]]
    else:
        e_data = election2020_filtered
        state_data = e_data[e_data['state_name']==dd_select_state]
        county_data = state_data[state_data['county_name']==dd_select_county]
        filtered = e_data[e_data['cluster']==county_data['cluster'].values[0]]

    filtered['GOP Votes'] = filtered['gop_votes'].map("{:,.0f}".format)
    filtered['DEM Votes'] = filtered['dem_votes'].map("{:,.0f}".format)
                                                        

    fig = px.choropleth_mapbox(filtered, geojson=counties, locations='fips_code_lz', color='cluster',
                                hover_name="county_name", 
                                color_continuous_scale="Viridis",
                                mapbox_style="carto-positron",
                                hover_data = {
                                    "fips_code_lz":False,
                                    "state_name":True,
                                    "DEM Votes":True,
                                    "GOP Votes":True,
                                    "% Margin":True,

                                },
                                labels={'cluster':'Cluster',
                                        'state_name':'State',
                                        'DEM Votes':'Democratic Votes',
                                        'GOP Votes':'Republican Votes',
                                        'perc_margin':'% Margin'},
                                zoom=3, center = {"lat": 37.0902, "lon": -95.7129},
                                opacity=0.5)
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0},showlegend=False)
    return fig


#Configure reactivity for cluster card header 
@app.callback(
    Output('cluster_county_header','children'),
    Input('dropdown4','value'),
    Input('dropdown2','value'),
    Input('dropdown3','value')
)

def cluster_header(dd4,dd_state,dd_county):

    if '2012 Election' in dd4:
        e_data = election2012_filtered
        state_data = e_data[e_data['state_name']==dd_state]
        county_data = state_data[state_data['county_name']==dd_county]

    elif '2016 Election' in dd4: 
        e_data = election2016_filtered
        state_data = e_data[e_data['state_name']==dd_state]
        county_data = state_data[state_data['county_name']==dd_county]
    else:
        e_data = election2020_filtered
        state_data = e_data[e_data['state_name']==dd_state]
        county_data = state_data[state_data['county_name']==dd_county]

    metrics_card_title = dbc.Card([
        dbc.CardBody([
            html.H5(f"{county_data['county_name'].values[0]} belongs to Cluster #{county_data['cluster'].values[0]}.  Below are the median cluster metrics:", className="card-title"),
        ])
    ],
    style={'display': 'inline-block',
           'width': '100%',
           'text-align': 'center',
           'background-color': '#70747c',
           'color':'white',
           'fontWeight': 'bold',
           'fontSize':16},
    outline=True)

    return metrics_card_title

#Configure reactivity for cluster stats row
@app.callback(
    Output('cluster_stats_card_row','children'),
    Input('dropdown4','value'),
    Input('dropdown2','value'),
    Input('dropdown3','value')
)

def cluster_stats_row(dd4,dd_state,dd_county):

    if '2012 Election' in dd4:
        e_data = election2012_filtered
        state_data = e_data[e_data['state_name']==dd_state]
        county_data = state_data[state_data['county_name']==dd_county]
        filtered = e_data[e_data['cluster']==county_data['cluster'].values[0]]

    elif '2016 Election' in dd4: 
        e_data = election2016_filtered
        state_data = e_data[e_data['state_name']==dd_state]
        county_data = state_data[state_data['county_name']==dd_county]
        filtered = e_data[e_data['cluster']==county_data['cluster'].values[0]]
    else:
        e_data = election2020_filtered
        state_data = e_data[e_data['state_name']==dd_state]
        county_data = state_data[state_data['county_name']==dd_county]
        filtered = e_data[e_data['cluster']==county_data['cluster'].values[0]]


    gop_formatted = f"{filtered['% GOP'].median():,.1f}%"
    dem_formatted = f"{filtered['% DEM'].median():,.1f}%"

    income_formatted = f"${filtered['PC_PI'].median():,.2f}"
    unemp_formatted = f"{filtered['Unemp_Rate'].median():,.1f}%"
    pop_formatted = f"{filtered['Pop'].median():,.0f}"
    
    card1 = dbc.Card([
        dbc.CardBody([
            html.H6('% DEM Vote', className="card-title"),
            html.P(dem_formatted)
        ])
    ],
    style={'display': 'inline-block',
           'width': '20%',
           'text-align': 'center',
           'background-color': '#70747c',
           'color':'white',
           'fontWeight': 'bold',
           'fontSize':16},
    outline=True)

    card2 = dbc.Card([
        dbc.CardBody([
            html.H6('% GOP Vote', className="card-title"),
            html.P(gop_formatted)
        ])
    ],
    style={'display': 'inline-block',
           'width': '20%',
           'text-align': 'center',
           'background-color': '#70747c',
           'color':'white',
           'fontWeight': 'bold',
           'fontSize':16},
    outline=True)


    card3 = dbc.Card([
        dbc.CardBody([
            html.H6('Per Capita Income', className="card-title"),
            html.P(income_formatted)
        ])
    ],
    style={'display': 'inline-block',
           'width': '20%',
           'text-align': 'center',
           'background-color': '#70747c',
           'color':'white',
           'fontWeight': 'bold',
           'fontSize':16},
    outline=True)


    
    card4 = dbc.Card([
        dbc.CardBody([
            html.H6('% Unemployed', className="card-title"),
            html.P(unemp_formatted)
        ])
    ],
    style={'display': 'inline-block',
           'width': '20%',
           'text-align': 'center',
           'background-color': '#70747c',
           'color':'white',
           'fontWeight': 'bold',
           'fontSize':16},
    outline=True)

    card5 = dbc.Card([
        dbc.CardBody([
            html.H6('Population', className="card-title"),
            html.P(pop_formatted)
        ])
    ],
    style={'display': 'inline-block',
           'width': '20%',
           'text-align': 'center',
           'background-color': '#70747c',
           'color':'white',
           'fontWeight': 'bold',
           'fontSize':16},
    outline=True)
    
    return (card1, card2, card3, card4, card5)  





#Configure reactivity for detailed cluster stats modal
@app.callback(
    Output('cluster_modal_text','children'),
    Input('dropdown4','value'),
    Input('dropdown2','value'),
    Input('dropdown3','value')
)

def cluster_stats_modal_text2(dd4,dd_state,dd_county):

    if '2012 Election' in dd4:
        e_data = election2012_filtered
        state_data = e_data[e_data['state_name']==dd_state]
        county_data = state_data[state_data['county_name']==dd_county]
        filtered = e_data[e_data['cluster']==county_data['cluster'].values[0]]

    elif '2016 Election' in dd4: 
        e_data = election2016_filtered
        state_data = e_data[e_data['state_name']==dd_state]
        county_data = state_data[state_data['county_name']==dd_county]
        filtered = e_data[e_data['cluster']==county_data['cluster'].values[0]]
    else: 
        e_data = election2020_filtered
        state_data = e_data[e_data['state_name']==dd_state]
        county_data = state_data[state_data['county_name']==dd_county]
        filtered = e_data[e_data['cluster']==county_data['cluster'].values[0]]


    perc_dem_formatted = f"{filtered['% DEM'].median():,.1f}%"
    perc_gop_formatted = f"{filtered['% GOP'].median():,.1f}%"

    perc_hs_dip_formatted = f"{filtered['HSGrad_Perc'].median():,.1f}"
    perc_bach_deg_formatted = f"{filtered['Bach_Perc'].median():,.1f}"
    perc_grad_deg_formatted = f"{filtered['GradDeg_Perc'].median():,.1f}"

    perc_women_formatted = f"{filtered['Female_Perc'].median():,.1f}"
    perc_white_formatted = f"{filtered['White_Perc'].median():,.1f}"
    perc_black_formatted = f"{filtered['Black_Perc'].median():,.1f}"
    perc_amer_ind_formatted = f"{filtered['AmInd_Perc'].median():,.1f}"
    perc_asian_formatted = f"{filtered['Asian_Perc'].median():,.1f}"
    perc_hispanic_formatted = f"{filtered['Hisp_Perc'].median():,.1f}"
    perc_for_born_formatted = f"{filtered['Vet_Perc'].median():,.1f}"
    perc_veteran_formatted = f"{filtered['Foreign_Perc'].median():,.1f}"
    age_formatted = f"{filtered['Median_Age'].median():,.1f}"

    per_capita_income_formatted = f"${filtered['PC_PI'].median():,.2f}"
    perc_unemployed_formatted = f"{filtered['Unemp_Rate'].median():.1f}%"
    household_size_formatted = f"{filtered['HH_Size'].median():.1f}"
    gini_formatted = f"{filtered['Gini_Index'].median():.1f}"
    #violent_crime_formatted = f"{filtered['Violent Crime'].median():.1f}"

    population_formatted = f"{filtered['Pop'].median():,.0f}"
    land_area_formatted = f"{filtered['SQM_AreaLand'].median():,.1f}"


    cluster_modal_text = html.P(
        children=[
            dcc.Markdown('''**Vote Share**'''), 
            f"1.) % of vote earned by Democrats: {perc_dem_formatted}",
            html.Br(),
            f"2.) % of vote earned by Republicans: {perc_gop_formatted}",
            html.Br(),
            html.Br(),
            dcc.Markdown('''**Education**'''), 
            f"1.) % of population with a High School Diploma: {perc_hs_dip_formatted}%",
            html.Br(),
            f"2.) % of population with a Bachelors Degree: {perc_bach_deg_formatted}%",
            html.Br(),
            f"3.) % of population with a Graduate Degree: {perc_grad_deg_formatted}%",
            html.Br(),
            html.Br(),
            dcc.Markdown('''**Demographics**'''),
            f"1.) % of population that are Women: {perc_women_formatted}%",
            html.Br(),
            f"2.) % of population that are White: {perc_white_formatted}%",
            html.Br(),
            f"3.) % of population that are Black: {perc_black_formatted}%",
            html.Br(),
            f"4.) % of population that are American Indian: {perc_amer_ind_formatted}%",
            html.Br(),
            f"5.) % of population that are Asian: {perc_asian_formatted}%",
            html.Br(),
            f"6.) % of population that are Hispanic: {perc_hispanic_formatted}%",
            html.Br(),
            f"7.) % of population that are Veterans: {perc_veteran_formatted}%",
            html.Br(),
            f"8.) % of population that were not born in the US: {perc_for_born_formatted}%",
            html.Br(),
            f"9.) Median Age: {age_formatted}",
            html.Br(),
            html.Br(),
            dcc.Markdown('''**Economics**'''),
            f"1.) Per Capita Income: {per_capita_income_formatted}",
            html.Br(),
            f"2.) % Unemployed: {perc_unemployed_formatted}",
            html.Br(),
            f"3.) Household Size: {household_size_formatted}",
            html.Br(),
            f"4.) Gini Index of Income Inequality: {gini_formatted}",
            html.Br(),
            #f"5.) Violent Crime Reports per 100,000 people: {violent_crime_formatted}",
            html.Br(),
            html.Br(),
            dcc.Markdown('''**Population Density**'''),
            f"1.) Population: {population_formatted}",
            html.Br(),
            f"2.) Land Area in Square Miles: {land_area_formatted}",
            html.Br(),
        ]
    )

    return cluster_modal_text

#Configure Reactivity for Prediction State/County Map on Tab 6
@app.callback(
    Output('predictions_map2024','figure'),
    Output('dropdown5','style'),
    Input('radio3','value'),
    Input('dropdown5','value'))

def update_pred_map(radio_select, state_select):
        new_df = preds[preds['state_name']==state_select]
        new_df['perc_margin_preds'] = new_df['perc_margin_preds'].astype(float).map("{:.1%}".format)


        avg_lat = new_df['AvgLat'].mean()
        avg_lon = new_df['AvgLon'].mean()

        new_df['dem_votes_preds'] = new_df['dem_votes_preds'].astype(float).map("{:,.0f}".format)
        new_df['gop_votes_preds'] = new_df['gop_votes_preds'].astype(float).map("{:,.0f}".format)



        if 'State View' in radio_select:

            #Zoom In 1 from Main Group
            if 'Rhode Island' in state_select or 'Connecticut' in state_select \
            or 'Massachusetts' in state_select or 'Delaware' in state_select or 'Vermont' in state_select \
            or 'Maryland' in state_select or 'New Jersey' in state_select:
            
        
                fig = px.choropleth_mapbox(new_df, 
                                    geojson=counties, 
                                    locations='fips_code_lz', 
                                    color='per_gop_preds',
                                    range_color=(preds['per_gop_preds'].min(), preds['per_gop_preds'].max()),  
                                    color_continuous_scale="balance",
                                    mapbox_style="carto-positron",
                                    hover_name="county_name", 
                                    zoom=6, 
                                    center = {"lat": avg_lon, "lon": avg_lat},
                                    opacity=0.5,
                                    labels={'dem_votes_preds':'Democratic Votes',
                                            'gop_votes_preds':'Republican Votes',
                                            'perc_margin_preds':'% Margin'},
                                    hover_data = {
                                        "fips_code_lz":False,
                                        "per_gop_preds":False,
                                        "state_name":False,
                                        "county_name":False,
                                        "dem_votes_preds":True,
                                        "gop_votes_preds":True,
                                        "perc_margin_preds":True
                                    }
                                    )
                fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
                fig.update_coloraxes(colorbar=dict(title='D - R Scale',showticklabels=False))
                    
                return (fig), ({'display': 'inline-block', 'width': '100%'})

            elif 'District of Columbia' in state_select:
                fig = px.choropleth_mapbox(new_df, geojson=counties, 
                                    locations='fips_code_lz', 
                                    color='per_gop_preds',
                                    range_color=(preds['per_gop_preds'].min(), preds['per_gop_preds'].max()),  
                                    color_continuous_scale="balance",
                                    mapbox_style="carto-positron",
                                    hover_name="county_name", 
                                    zoom=8, 
                                    center = {"lat": avg_lon, "lon": avg_lat},
                                    opacity=0.5,
                                    labels={'dem_votes_preds':'Democratic Votes',
                                            'gop_votes_preds':'Republican Votes',
                                            'perc_margin_preds':'% Margin'},
                                    hover_data = {
                                        "fips_code_lz":False,
                                        "per_gop_preds":False,
                                        "state_name":False,
                                        "county_name":False,
                                        "dem_votes_preds":True,
                                        "gop_votes_preds":True,
                                        "perc_margin_preds":True
                                    }
                                    )
                fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
                fig.update_coloraxes(colorbar=dict(title='D - R Scale',showticklabels=False))
                    
                return (fig), ({'display': 'inline-block', 'width': '100%'})
            elif 'Alaska' in state_select:
                fig = px.choropleth_mapbox(new_df, 
                                    geojson=counties, 
                                    locations='fips_code_lz', 
                                    color='per_gop_preds',
                                    range_color=(preds['per_gop_preds'].min(), preds['per_gop_preds'].max()),  
                                    color_continuous_scale="balance",
                                    mapbox_style="carto-positron",
                                    hover_name="county_name", 
                                    zoom=2, 
                                    center = {"lat": avg_lon, "lon": avg_lat},
                                    opacity=0.5,
                                    labels={'dem_votes_preds':'Democratic Votes',
                                            'gop_votes_preds':'Republican Votes',
                                            'perc_margin_preds':'% Margin'},
                                    hover_data = {
                                        "fips_code_lz":False,
                                        "per_gop_preds":False,
                                        "state_name":False,
                                        "county_name":False,
                                        "dem_votes_preds":True,
                                        "gop_votes_preds":True,
                                        "perc_margin_preds":True
                                    }
                                    )
                fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
                fig.update_coloraxes(colorbar=dict(title='D - R Scale',showticklabels=False))
                    
                return (fig), ({'display': 'inline-block', 'width': '100%'})

            elif 'California' in state_select or 'Nevada' in state_select or \
                 'Texas' in state_select or 'Minnesota' in state_select or \
                 'Michigan' in state_select or 'Florida' in state_select or 'Idaho' in state_select:

                fig = px.choropleth_mapbox(new_df, geojson=counties, 
                                    locations='fips_code_lz', 
                                    color='per_gop_preds',
                                    range_color=(preds['per_gop_preds'].min(), preds['per_gop_preds'].max()),  
                                    color_continuous_scale="balance",
                                    mapbox_style="carto-positron",
                                    hover_name="county_name", 
                                    zoom=4, 
                                    center = {"lat": avg_lon, "lon": avg_lat},
                                    opacity=0.5,
                                    labels={'dem_votes_preds':'Democratic Votes',
                                            'gop_votes_preds':'Republican Votes',
                                            'perc_margin_preds':'% Margin'},
                                    hover_data = {
                                        "fips_code_lz":False,
                                        "per_gop_preds":False,
                                        "state_name":False,
                                        "county_name":False,
                                        "dem_votes_preds":True,
                                        "gop_votes_preds":True,
                                        "perc_margin_preds":True
                                    }
                                    )
                fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
                fig.update_coloraxes(colorbar=dict(title='D - R Scale',showticklabels=False))
                    
                return (fig), ({'display': 'inline-block', 'width': '100%'})
            else:
                fig = px.choropleth_mapbox(new_df, geojson=counties, 
                                    locations='fips_code_lz', 
                                    color='per_gop_preds',
                                    range_color=(preds['per_gop_preds'].min(), preds['per_gop_preds'].max()),  
                                    color_continuous_scale="balance",
                                    mapbox_style="carto-positron",
                                    hover_name="county_name", 
                                    zoom=5, 
                                    center = {"lat": avg_lon, "lon": avg_lat},
                                    opacity=0.5,
                                    labels={'dem_votes_preds':'Democratic Votes',
                                            'gop_votes_preds':'Republican Votes',
                                            'perc_margin_preds':'% Margin'},
                                    hover_data = {
                                        "fips_code_lz":False,
                                        "per_gop_preds":False,
                                        "state_name":False,
                                        "county_name":False,
                                        "dem_votes_preds":True,
                                        "gop_votes_preds":True,
                                        "perc_margin_preds":True
                                    }
                                    )
                fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
                fig.update_coloraxes(colorbar=dict(title='D - R Scale',showticklabels=False))
                    
                return (fig), ({'display': 'inline-block', 'width': '100%'})

        else:

            fig = px.scatter_mapbox(preds, lat="Lon", lon="Lat", 
                                        hover_name="county_name", 
                                        color_continuous_scale="balance",
                                        color="per_gop_preds",
                                        range_color=(preds['per_gop_preds'].min(), preds['per_gop_preds'].max()),  
                                        hover_data = {
                                                "dem_gop_preds_total":False,
                                                "Lon":False,
                                                "Lat":False,
                                                "fips_code_lz":False,
                                                "per_gop_preds":False,
                                                "state_name":True,
                                                "county_name":False,
                                                "dem_votes_preds_formatted":True,
                                                "gop_votes_preds_formatted":True,
                                                "perc_margin_preds_formatted":True
                                        },
                                        labels={'state_name':'State',
                                                'dem_votes_preds_formatted':'Democratic Votes',
                                                'gop_votes_preds_formatted':'Republican Votes',
                                                'perc_margin_preds_formatted':'% Margin'},
                                        size = "dem_gop_preds_total",
                                        zoom=2,center = {"lat": 37.0902, "lon": -95.7129})
            fig.update_layout(
                mapbox_style="carto-positron",
                margin={"r":0,"t":0,"l":0,"b":0},
                height=400
            )
            fig.update_coloraxes(
                colorbar=dict(
                    title='D - R Scale',
                    showticklabels=False
                )
            )

            return (fig), ({'display': 'none'})

#Configure reactivity for prediction card stats
@app.callback(
    Output('preds_card_row_header','children'),
    Output('preds_card_row_totals','children'),
    Input('dropdown5','value'),
    Input('radio3','value'),
    Input('predictions_map2024','clickData'))

def update_card_county_preds(state_select,radio_select,click_county_select):

        if click_county_select:
            new_df = preds[preds['state_name']==state_select]
            county_id = click_county_select['points'][0]['customdata'][3]
            new_df2 = new_df[new_df['county_name']==county_id]

            counties = new_df["county_name"].values
            if county_id not in counties:
                new_df = preds[preds["state_name"] == state_select]
                county_id = new_df["county_name"].iloc[0]
                new_df2 = new_df[new_df["county_name"] == county_id]
        else:
            new_df = preds[preds['state_name']==state_select]
            county_id = new_df['county_name'].iloc[0]
            new_df2 = new_df[new_df['county_name']==county_id]


        new_df2['per_dem_preds'] = new_df2['per_dem_preds'].astype(float).map("{:.1%}".format)
        new_df2['per_gop_preds'] = new_df2['per_gop_preds'].astype(float).map("{:.1%}".format)
        winner = new_df2['win'].values[0]
        e_votes = 287

        # country_summary = preds.groupby('state_name').first().reset_index()
        # country_gop = country_summary[country_summary['win']=="Republican"]
        # country_dem = country_summary[country_summary['win']=="Democratic"]

        state_name = new_df2['state_name'].values[0]

        state_summary_predict = preds.groupby('state_name')[['dem_votes_preds', 'gop_votes_preds']].sum().reset_index()
        predict_winner = state_summary_predict[['dem_votes_preds', 'gop_votes_preds']].sum().to_frame().T
        dem_pred_total = int(predict_winner['dem_votes_preds'].values[0])
        gop_pred_total = int(predict_winner['gop_votes_preds'].values[0])
        pred_country_winner = str(np.where(dem_pred_total > gop_pred_total, "Democratic", "Republican"))

        if 'State View' in radio_select:

            card1 = dbc.Card([
                dbc.CardBody([
                    html.H5(f'The {winner} candidate wins {state_name}.', className="card-title")
                ])
            ],
            style={'display': 'inline-block',
                'width': '100%',
                'text-align': 'center',
                'background-color': '#70747c',
                'color':'white',
                'fontWeight': 'bold',
                'fontSize':16},

            outline=True)

            card2 = dbc.Card([
                dbc.CardBody([
                    html.P(f'Total {state_select} DEM Votes'),
                    html.H6(f"{new_df['dem_votes_preds'].sum():,.0f}", className="card-title"),
                ])
            ],
            style={'display': 'inline-block',
                'width': '25%',
                'text-align': 'center',
                'background-color': '#70747c',
                'color':'white',
                'fontWeight': 'bold',
                'fontSize':16},
            outline=True)

            card3 = dbc.Card([
                dbc.CardBody([
                    html.P(f'Total {state_select} GOP Votes'),
                    html.H6(f"{new_df['gop_votes_preds'].sum():,.0f}", className="card-title"),

                ])
            ],
            style={'display': 'inline-block',
                'width': '25%',
                'text-align': 'center',
                'background-color': '#70747c',
                'color':'white',
                'fontWeight': 'bold',
                'fontSize':16},
            outline=True)

            card4 = dbc.Card([
                dbc.CardBody([
                    html.P(f'% DEM Vote in {county_id}'),
                    html.H6(new_df2['per_dem_preds'], className="card-title"),
                ])
            ],
            style={'display': 'inline-block',
                'width': '25%',
                'text-align': 'center',
                'background-color': '#70747c',
                'color':'white',
                'fontWeight': 'bold',
                'fontSize':16},
            outline=True)

            card5 = dbc.Card([
                dbc.CardBody([
                    html.P(f'% GOP Vote in {county_id}'),
                    html.H6(new_df2['per_gop_preds'], className="card-title"),
                ])
            ],
            style={'display': 'inline-block',
                'width': '25%',
                'text-align': 'center',
                'background-color': '#70747c',
                'color':'white',
                'fontWeight': 'bold',
                'fontSize':16},
            outline=True)


    

            return (card1), (card2, card3, card4, card5)
        else:
            card6 = dbc.Card([
                dbc.CardBody([
                    html.H5(f'The {pred_country_winner} candidate was predicted to win the 2024 election with {e_votes} electoral votes.', className="card-title"),
                    html.H6(f'*Alaska vote totals excluded from popular vote.', className="card-title")

                ])
            ],
            style={'display': 'inline-block',
                'width': '100%',
                'text-align': 'center',
                'background-color': '#70747c',
                'color':'white',
                'fontWeight': 'bold',
                'fontSize':16},
            outline=True)

            card7 = dbc.Card([
                dbc.CardBody([
                    html.P('DEM Electoral College Votes'),
                    html.H6(287, className="card-title"),
                ])
            ],
            style={'display': 'inline-block',
                'width': '25%',
                'text-align': 'center',
                'background-color': '#70747c',
                'color':'white',
                'fontWeight': 'bold',
                'fontSize':16},
            outline=True)

            card8 = dbc.Card([
                dbc.CardBody([
                    html.P('GOP Electoral College Votes'),
                    html.H6(251, className="card-title"),

                ])
            ],
            style={'display': 'inline-block',
                'width': '25%',
                'text-align': 'center',
                'background-color': '#70747c',
                'color':'white',
                'fontWeight': 'bold',
                'fontSize':16},
            outline=True)


            card9 = dbc.Card([
                dbc.CardBody([
                    html.P('DEM Popular Vote'),
                    html.H6(f"{preds['dem_votes_preds'].sum():,.0f}", className="card-title"),
                ])
            ],
            style={'display': 'inline-block',
                'width': '25%',
                'text-align': 'center',
                'background-color': '#70747c',
                'color':'white',
                'fontWeight': 'bold',
                'fontSize':16},
            outline=True)

            card10 = dbc.Card([
                dbc.CardBody([
                    html.P('GOP Popular Vote'),
                    html.H6(f"{preds['gop_votes_preds'].sum():,.0f}", className="card-title"),

                ])
            ],
            style={'display': 'inline-block',
                'width': '25%',
                'text-align': 'center',
                'background-color': '#70747c',
                'color':'white',
                'fontWeight': 'bold',
                'fontSize':16},
            outline=True)


           
            return (card6), (card7, card8, card9, card10)



#Configure Reactivity for Actual vs. Predicted Margin
@app.callback(
    Output('actuals_v_preds2024','figure'),
    Input('radio3','value'),
    Input('dropdown5','value'))

def actual_v_pred_margin(radio_select, state_select):

    preds['noabs_margin_preds'] = preds['dem_votes_preds'] - preds['gop_votes_preds']
    preds['noabs_margin_actuals'] = preds['dem_votes_actuals'] - preds['gop_votes_actuals']
    preds['win_updated'] = np.where(preds['dem_votes_actuals']>preds['gop_votes_actuals'], 'DEM','GOP')
    preds['hover_name'] = preds['county_name'] + ', ' + preds['state_name']

    if 'Country View' in radio_select:
        fig = px.scatter(
            preds,
            x = 'noabs_margin_preds', y = 'noabs_margin_actuals',
            color = 'win_updated',
            color_discrete_map={
                'DEM': 'blue',
                'GOP': 'red'
            },
            hover_name="hover_name", 
            hover_data = {
                "state_name":True
            },
            labels={
                'state_name':'State',
                'win_updated':'Winner',
                'noabs_margin_preds':'Predicted Margin',
                'noabs_margin_actuals':'Actual Margin',
            }
        )
        fig.add_shape(
            type='line',
            x0=0, x1=0,
            y0=preds['noabs_margin_actuals'].min(), y1=preds['noabs_margin_actuals'].max(),
            line=dict(color='gray', width=1, dash='dash')
        )

        fig.add_shape(
            type='line',
            x0=preds['noabs_margin_preds'].min(), x1=preds['noabs_margin_preds'].max(),
            y0=0, y1=0,
            line=dict(color='gray', width=1, dash='dash')
        )

        fig.update_layout(
            xaxis_title="Predicted Margin",
            yaxis_title="Actual Margin",
            legend=dict(
                x=1,
                y=0,
                xanchor='right',
                yanchor='bottom',
                bgcolor='rgba(0,0,0,0)'  
            ),
            title=dict(
                text="Actual Margin vs. Predicted Margin", 
                x=0.5, 
                xanchor='center'
            )     
        )

        return fig

    else:

        filtered_df = preds[preds['state_name']==state_select]

        # Compute dynamic range with buffer
        x_min = filtered_df['noabs_margin_preds'].min()
        x_max = filtered_df['noabs_margin_preds'].max()
        y_min = filtered_df['noabs_margin_actuals'].min()
        y_max = filtered_df['noabs_margin_actuals'].max()

        # Add a buffer (e.g., 10% of the range, or a fixed minimum buffer)
        x_range = x_max - x_min
        y_range = y_max - y_min

        buffer_x = max(0.1 * x_range, 5)  # ensure a minimum padding of 5 if data is clustered
        buffer_y = max(0.1 * y_range, 5)

        # Force inclusion of zero in range
        x_lower = min(x_min - buffer_x, 0)
        x_upper = max(x_max + buffer_x, 0)
        y_lower = min(y_min - buffer_y, 0)
        y_upper = max(y_max + buffer_y, 0)

        fig = px.scatter(
            filtered_df,
            x = 'noabs_margin_preds', y = 'noabs_margin_actuals',
            color = 'win_updated',
            color_discrete_map={
                'DEM': 'blue',
                'GOP': 'red'
            },
            hover_name="county_name", 
            hover_data = {
                "state_name":True
            },
            labels={
                'state_name':'State',
                'win_updated':'Winner',
                'noabs_margin_preds':'Predicted Margin',
                'noabs_margin_actuals':'Actual Margin'
            }
          
        )

        fig.update_layout(
            legend=dict(
                x=1,
                y=0,
                xanchor='right',
                yanchor='bottom',
                bgcolor='rgba(0,0,0,0)' 
            ),
            xaxis=dict(
                title='Predicted Margin', 
                range=[x_lower, x_upper]
            ),
            yaxis=dict(
                title='Actual Margin', 
                range=[y_lower, y_upper]
            ),
            title=dict(
                text="Actual Margin vs. Predicted Margin", 
                x=0.5, 
                xanchor='center'
            )            
        )
        fig.add_shape(
            type='line',
                x0=0, x1=0,
                y0=y_lower, y1=y_upper,
                line=dict(color='gray', width=2, dash='dash'),
                xref='x', yref='y'
        )

        fig.add_shape(
            type='line',
            x0=x_lower, x1=x_upper,
            y0=0, y1=0,
            line=dict(color='gray', width=2, dash='dash'),
            xref='x', yref='y'
        )

        return fig
        


#----- 2028 Prediction Tab

@app.callback(
    Output('predictions_map2028','figure'),
    Output('dropdown6','style'),
    Input('radio4','value'),
    Input('dropdown6','value'))

def update_pred_map2028(radio_select, state_select):

        new_df = preds2028[preds2028['state_name']==state_select]
        new_df['perc_margin'] = new_df['perc_margin'].astype(float).map("{:.1%}".format)

        avg_lat = new_df['AvgLat'].mean()
        avg_lon = new_df['AvgLon'].mean()

        new_df['dem_votes'] = new_df['dem_votes'].astype(float).map("{:,.0f}".format)
        new_df['gop_votes'] = new_df['gop_votes'].astype(float).map("{:,.0f}".format)

        if 'State View' in radio_select:

            #Zoom In 1 from Main Group
            if 'Rhode Island' in state_select or 'Connecticut' in state_select \
            or 'Massachusetts' in state_select or 'Delaware' in state_select or 'Vermont' in state_select \
            or 'Maryland' in state_select or 'New Jersey' in state_select:
            
        
                fig = px.choropleth_mapbox(new_df, 
                                    geojson=counties, 
                                    locations='fips_code_lz', 
                                    color='per_gop',
                                    range_color=(preds2028['per_gop'].min(), preds2028['per_gop'].max()),  
                                    color_continuous_scale="balance",
                                    mapbox_style="carto-positron",
                                    hover_name="county_name", 
                                    zoom=6, 
                                    center = {"lat": avg_lon, "lon": avg_lat},
                                    opacity=0.5,
                                    labels={'dem_votes':'Democratic Votes',
                                            'gop_votes':'Republican Votes',
                                            'perc_margin':'% Margin'},
                                    hover_data = {
                                        "fips_code_lz":False,
                                        "per_gop":False,
                                        "state_name":False,
                                        "county_name":False,
                                        "dem_votes":True,
                                        "gop_votes":True,
                                        "perc_margin":True
                                    }
                                    )
                fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
                fig.update_coloraxes(colorbar=dict(title='D - R Scale',showticklabels=False))
                    
                return (fig), ({'display': 'inline-block', 'width': '100%'})

            elif 'District of Columbia' in state_select:
                fig = px.choropleth_mapbox(new_df, geojson=counties, 
                                    locations='fips_code_lz', 
                                    color='per_gop',
                                    range_color=(preds2028['per_gop'].min(), preds2028['per_gop'].max()),  
                                    color_continuous_scale="balance",
                                    mapbox_style="carto-positron",
                                    hover_name="county_name", 
                                    zoom=8, 
                                    center = {"lat": avg_lon, "lon": avg_lat},
                                    opacity=0.5,
                                    labels={'dem_votes':'Democratic Votes',
                                            'gop_votes':'Republican Votes',
                                            'perc_margin':'% Margin'},
                                    hover_data = {
                                        "fips_code_lz":False,
                                        "per_gop":False,
                                        "state_name":False,
                                        "county_name":False,
                                        "dem_votes":True,
                                        "gop_votes":True,
                                        "perc_margin":True
                                    }
                                    )
                fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
                fig.update_coloraxes(colorbar=dict(title='D - R Scale',showticklabels=False))
                    
                return (fig), ({'display': 'inline-block', 'width': '100%'})
            elif 'Alaska' in state_select:
                fig = px.choropleth_mapbox(new_df, 
                                    geojson=counties, 
                                    locations='fips_code_lz', 
                                    color='per_gop',
                                    range_color=(preds2028['per_gop'].min(), preds2028['per_gop'].max()),  
                                    color_continuous_scale="balance",
                                    mapbox_style="carto-positron",
                                    hover_name="county_name", 
                                    zoom=2, 
                                    center = {"lat": avg_lon, "lon": avg_lat},
                                    opacity=0.5,
                                    labels={'dem_votes':'Democratic Votes',
                                            'gop_votes':'Republican Votes',
                                            'perc_margin':'% Margin'},
                                    hover_data = {
                                        "fips_code_lz":False,
                                        "per_gop":False,
                                        "state_name":False,
                                        "county_name":False,
                                        "dem_votes":True,
                                        "gop_votes":True,
                                        "perc_margin":True
                                    }
                                    )
                fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
                fig.update_coloraxes(colorbar=dict(title='D - R Scale',showticklabels=False))
                    
                return (fig), ({'display': 'inline-block', 'width': '100%'})

            elif 'California' in state_select or 'Nevada' in state_select or \
                 'Texas' in state_select or 'Minnesota' in state_select or \
                 'Michigan' in state_select or 'Florida' in state_select or 'Idaho' in state_select:

                fig = px.choropleth_mapbox(new_df, geojson=counties, 
                                    locations='fips_code_lz', 
                                    color='per_gop',
                                    range_color=(preds2028['per_gop'].min(), preds2028['per_gop'].max()),  
                                    color_continuous_scale="balance",
                                    mapbox_style="carto-positron",
                                    hover_name="county_name", 
                                    zoom=4, 
                                    center = {"lat": avg_lon, "lon": avg_lat},
                                    opacity=0.5,
                                    labels={'dem_votes':'Democratic Votes',
                                            'gop_votes':'Republican Votes',
                                            'perc_margin':'% Margin'},
                                    hover_data = {
                                        "fips_code_lz":False,
                                        "per_gop":False,
                                        "state_name":False,
                                        "county_name":False,
                                        "dem_votes":True,
                                        "gop_votes":True,
                                        "perc_margin":True
                                    }
                                    )
                fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
                fig.update_coloraxes(colorbar=dict(title='D - R Scale',showticklabels=False))
                    
                return (fig), ({'display': 'inline-block', 'width': '100%'})
            else:
                fig = px.choropleth_mapbox(new_df, geojson=counties, 
                                    locations='fips_code_lz', 
                                    color='per_gop',
                                    range_color=(preds2028['per_gop'].min(), preds2028['per_gop'].max()),  
                                    color_continuous_scale="balance",
                                    mapbox_style="carto-positron",
                                    hover_name="county_name", 
                                    zoom=5, 
                                    center = {"lat": avg_lon, "lon": avg_lat},
                                    opacity=0.5,
                                    labels={'dem_votes':'Democratic Votes',
                                            'gop_votes':'Republican Votes',
                                            'perc_margin':'% Margin'},
                                    hover_data = {
                                        "fips_code_lz":False,
                                        "per_gop":False,
                                        "state_name":False,
                                        "county_name":False,
                                        "dem_votes":True,
                                        "gop_votes":True,
                                        "perc_margin":True
                                    }
                                    )
                fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
                fig.update_coloraxes(colorbar=dict(title='D - R Scale',showticklabels=False))
                    
                return (fig), ({'display': 'inline-block', 'width': '100%'})

        else:

            fig = px.scatter_mapbox(preds2028, lat="Lon", lon="Lat", 
                                        hover_name="county_name", 
                                        color_continuous_scale="balance",
                                        color="per_gop",
                                        range_color=(preds2028['per_gop'].min(), preds2028['per_gop'].max()),  
                                        hover_data = {
                                                "gop_dem_total":False,
                                                "Lon":False,
                                                "Lat":False,
                                                "fips_code_lz":False,
                                                "per_gop":False,
                                                "state_name":True,
                                                "county_name":False,
                                                "dem_votes_formatted":True,
                                                "gop_votes_formatted":True,
                                                "perc_margin_formatted":True
                                        },
                                        labels={'state_name':'State',
                                                'dem_votes_formatted':'Democratic Votes',
                                                'gop_votes_formatted':'Republican Votes',
                                                'perc_margin_formatted':'% Margin'},
                                        size = "gop_dem_total",
                                        zoom=3,
                                        center = {"lat": 37.0902, "lon": -95.7129})
            fig.update_layout(mapbox_style="carto-positron",
                                        margin={"r":0,"t":0,"l":0,"b":0},
                                        height=400)
            fig.update_coloraxes(colorbar=dict(title='D - R Scale',showticklabels=False))

            return (fig), ({'display': 'none'})

#Configure reactivity for prediction card stats
@app.callback(
    Output('preds_card_row_header_2028','children'),
    Output('preds_card_row_totals_2028','children'),
    Input('dropdown6','value'),
    Input('radio4','value'),
    Input('predictions_map2028','clickData'))

def update_card_county_preds2028(state_select,radio_select,click_county_select):

        if click_county_select:
            new_df = preds2028[preds2028['state_name']==state_select]
            county_id = click_county_select['points'][0]['customdata'][3]
            new_df2 = new_df[new_df['county_name']==county_id]

            counties = new_df["county_name"].values
            if county_id not in counties:
                new_df = preds2028[preds2028["state_name"] == state_select]
                county_id = new_df["county_name"].iloc[0]
                new_df2 = new_df[new_df["county_name"] == county_id]
        else:
            new_df = preds2028[preds2028['state_name']==state_select]
            county_id = new_df['county_name'].iloc[0]
            new_df2 = new_df[new_df['county_name']==county_id]


        new_df2['per_dem'] = new_df2['per_dem'].astype(float).map("{:.1%}".format)
        new_df2['per_gop'] = new_df2['per_gop'].astype(float).map("{:.1%}".format)
        winner = str(np.where(new_df['dem_votes'].sum()>new_df['gop_votes'].sum(),"Democratic","Republican"))    
        e_votes = 302

        #country_summary = preds2028.groupby('state_name').first().reset_index()
        #country_gop = country_summary[country_summary['win']=="Republican"]
        #country_dem = country_summary[country_summary['win']=="Democratic"]

        state_name = new_df2['state_name'].values[0]

        state_summary_predict = preds2028.groupby('state_name')[['dem_votes', 'gop_votes']].sum().reset_index()
        predict_winner = state_summary_predict[['dem_votes', 'gop_votes']].sum().to_frame().T
        dem_pred_total = int(predict_winner['dem_votes'].values[0])
        gop_pred_total = int(predict_winner['gop_votes'].values[0])
        pred_country_winner = str(np.where(dem_pred_total > gop_pred_total, "Democratic", "Republican"))

        if 'State View' in radio_select:

            card1 = dbc.Card([
                dbc.CardBody([
                    html.H5(f'The {winner} candidate wins {state_name}.', className="card-title")
                ])
            ],
            style={'display': 'inline-block',
                'width': '100%',
                'text-align': 'center',
                'background-color': '#70747c',
                'color':'white',
                'fontWeight': 'bold',
                'fontSize':16},

            outline=True)

            card2 = dbc.Card([
                dbc.CardBody([
                    html.P(f'Total {state_select} DEM Votes'),
                    html.H6(f"{new_df['dem_votes'].sum():,.0f}", className="card-title"),
                ])
            ],
            style={'display': 'inline-block',
                'width': '25%',
                'text-align': 'center',
                'background-color': '#70747c',
                'color':'white',
                'fontWeight': 'bold',
                'fontSize':16},
            outline=True)

            card3 = dbc.Card([
                dbc.CardBody([
                    html.P(f'Total {state_select} GOP Votes'),
                    html.H6(f"{new_df['gop_votes'].sum():,.0f}", className="card-title"),

                ])
            ],
            style={'display': 'inline-block',
                'width': '25%',
                'text-align': 'center',
                'background-color': '#70747c',
                'color':'white',
                'fontWeight': 'bold',
                'fontSize':16},
            outline=True)

            card4 = dbc.Card([
                dbc.CardBody([
                    html.P(f'% DEM Vote in {county_id}'),
                    html.H6(new_df2['per_dem'], className="card-title"),
                ])
            ],
            style={'display': 'inline-block',
                'width': '25%',
                'text-align': 'center',
                'background-color': '#70747c',
                'color':'white',
                'fontWeight': 'bold',
                'fontSize':16},
            outline=True)

            card5 = dbc.Card([
                dbc.CardBody([
                    html.P(f'% GOP Vote in {county_id}'),
                    html.H6(new_df2['per_gop'], className="card-title"),
                ])
            ],
            style={'display': 'inline-block',
                'width': '25%',
                'text-align': 'center',
                'background-color': '#70747c',
                'color':'white',
                'fontWeight': 'bold',
                'fontSize':16},
            outline=True)


    

            return (card1), (card2, card3, card4, card5)
        else:
            card6 = dbc.Card([
                dbc.CardBody([
                    html.H5(f'The {pred_country_winner} candidate is predicted to win the 2028 election with {e_votes} electoral votes.', className="card-title"),

                ])
            ],
            style={'display': 'inline-block',
                'width': '100%',
                'text-align': 'center',
                'background-color': '#70747c',
                'color':'white',
                'fontWeight': 'bold',
                'fontSize':16},
            outline=True)

            card7 = dbc.Card([
                dbc.CardBody([
                    html.P('DEM Electoral College Votes'),
                    html.H6(236, className="card-title"),
                ])
            ],
            style={'display': 'inline-block',
                'width': '25%',
                'text-align': 'center',
                'background-color': '#70747c',
                'color':'white',
                'fontWeight': 'bold',
                'fontSize':16},
            outline=True)

            card8 = dbc.Card([
                dbc.CardBody([
                    html.P('GOP Electoral College Votes'),
                    html.H6(302, className="card-title"),

                ])
            ],
            style={'display': 'inline-block',
                'width': '25%',
                'text-align': 'center',
                'background-color': '#70747c',
                'color':'white',
                'fontWeight': 'bold',
                'fontSize':16},
            outline=True)


            card9 = dbc.Card([
                dbc.CardBody([
                    html.P('DEM Popular Vote'),
                    html.H6(f"{preds2028['dem_votes'].sum():,.0f}", className="card-title"),
                ])
            ],
            style={'display': 'inline-block',
                'width': '25%',
                'text-align': 'center',
                'background-color': '#70747c',
                'color':'white',
                'fontWeight': 'bold',
                'fontSize':16},
            outline=True)

            card10 = dbc.Card([
                dbc.CardBody([
                    html.P('GOP Popular Vote'),
                    html.H6(f"{preds2028['gop_votes'].sum():,.0f}", className="card-title"),

                ])
            ],
            style={'display': 'inline-block',
                'width': '25%',
                'text-align': 'center',
                'background-color': '#70747c',
                'color':'white',
                'fontWeight': 'bold',
                'fontSize':16},
            outline=True)


           
            return (card6), (card7, card8, card9, card10)


#Configure modal reactivity - open up
@app.callback(
    Output("modal1", "is_open"),
    [Input("open1", "n_clicks"), 
    Input("close1", "n_clicks")],
    [State("modal1", "is_open")],
)

def toggle_modal2(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open

@app.callback(
    Output("modal2", "is_open"),
    [Input("open2", "n_clicks"), 
    Input("close2", "n_clicks")],
    [State("modal2", "is_open")],
)

def toggle_modal2(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open

@app.callback(
    Output("modal3", "is_open"),
    [Input("open3", "n_clicks"), 
    Input("close3", "n_clicks")],
    [State("modal3", "is_open")],
)

def toggle_modal3(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open


@app.callback(
    Output("modal4", "is_open"),
    [Input("open4", "n_clicks"), 
    Input("close4", "n_clicks")],
    [State("modal4", "is_open")],
)

def toggle_modal4(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open


@app.callback(
    Output("modal5", "is_open"),
    [Input("open5", "n_clicks"), 
    Input("close5", "n_clicks")],
    [State("modal5", "is_open")],
)

def toggle_modal5(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open


@app.callback(
    Output("modal6", "is_open"),
    [Input("open6", "n_clicks"), 
    Input("close6", "n_clicks")],
    [State("modal6", "is_open")],
)

def toggle_modal6(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open
# @app.callback(Output('click-data', 'children'),
#     [Input('state_map', 'clickData')])
# def display_click_data(map_click):
#     return json.dumps(map_click, indent=2)

app.run_server(host='0.0.0.0',port='8057')
# if __name__=='__main__':
# 	app.run_server()