# US Elections Analysis

### Description

The goal of this project was to examine the historical vote for the US President from 1960 through 2020 at a national, state, and county level.   Voting data was collected from multiple Github repositories.  Socioeconomic data was collected from the Agency for Healthcare Research and Quality.  The following bullets list out my main objectives of this project:

- Understand how the US vote for President has changed over time
- Understand the characteristics of counties that vote similarly
- Predict the results of the 2024 and 2028 US Presidential election at a county level

### App
Click [here](https://us-elections-project.onrender.com/) to view the app.  It might need a few minutes to "wake up" if it has been idle for awhile.


### Data
- [Github - County level results (1960-2016)](https://github.com/cilekagaci/us-presidential-county-1960-2016)
- [Github - County level results (2020)](https://github.com/tonmcg/US_County_Level_Election_Results_08-20)
- [Agency for Healthcare Research and Quality - County level socioeconomic data](https://www.ahrq.gov/sdoh/data-analytics/sdoh-data.html)
- [Github - Estimated county level results for Alaska](https://github.com/tonmcg/US_County_Level_Election_Results_08-20/issues/2)

### Challenges

There were two main challenges I faced when working through this project: 
- Data was pulled from multiple sources and combined.  The data sources may have had different standards and/or methods of collecting and maintaining information.
- Data for Alaska was available, but was not presented with the standard FIPS county code identifier, therefore it was not conducive to regular plotting procedures.  Instead of reporting results by counties, Alaska reports results by Boroughs, which does not map 1-1 with counties.  Further, several Boroughs are broken out into Census Areas further complicating any kind of consistent analysis over time.  Therefore, several links in the 4th bullet under the Data section above proved to be very helpful in converting the results to conform to a standard FIPS-county identifier.
