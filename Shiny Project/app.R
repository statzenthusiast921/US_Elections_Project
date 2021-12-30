# Elections Project
# Start Date: 08.06.2021
# End Date: 10.30.2021
#----------------------------------#
library(openxlsx)
library(readxl)
library(shinyWidgets)
library(shinyBS)
library(shiny)
library(shinydashboard)
library(DT)
library(ggplot2)
library(plotly)
library(raster)
library(leaflet)
library(viridis)
library(stringr)
library(RColorBrewer)
library(tidyverse)
library(scales)


#library(lubridate)
#library(RSQLite)
#library(sqldf)
#library(scales)
#library(zoo)
#library(dplyr)
#library(htmltools)
#library(formattable)
#library(tibble)
library(readxl)


#----- Perform necessary preprocessing of data -----#



#this file needs to be in same folder as app.R

#Must import the dataset now, can't seem to load it in locally anymore or even set the directory
#setwd("Users/jonzimmerman/Desktop/Data Projects/Elections Project/Shiny")
#getwd()

#full_elections <- read_excel("Desktop/Data Projects/Elections Project/Shiny/FullElectionsData.xlsx")
#FullElectionsData=as.data.frame(read_excel("FullElectionsData.xlsx",sheet=1))

#full_elections = FullElectionsData

#cluster2012=read_excel("Desktop/Data Projects/Elections Project/Shiny/THECluster2012.xlsx",sheet=1)
#cluster2016=read_excel("Desktop/Data Projects/Elections Project/Shiny/THECluster2016.xlsx",sheet=1)
#ARMA_preds=read_excel("Desktop/Data Projects/Elections Project/Shiny/ARMA_predictions2024.xlsx",sheet=1)
#head(full_elections)
full_elections$winner <- ifelse(full_elections$Dem_EV>full_elections$Rep_EV,"DEM","GOP")
full_elections$county_winner<- ifelse(full_elections$dem_votes>full_elections$gop_votes,"DEM","GOP")
full_elections$match <-ifelse((full_elections$winner=="DEM" & full_elections$county_winner=="DEM")|
                               (full_elections$winner=="GOP" & full_elections$county_winner=="GOP"),
                              1,0)
full_elections$dem_county_winner <- ifelse(full_elections$dem_votes>full_elections$gop_votes,1,0)
full_elections$gop_county_winner <- ifelse(full_elections$dem_votes<full_elections$gop_votes,1,0)

#View(full_elections)


# Get USA polygon data
USA <- getData("GADM", country = "usa", level = 2)
USA$CountyName <- str_c(USA$NAME_2, ' ', USA$TYPE_2)



initial_counties <- subset(full_elections, full_elections$state_name == "Alabama")$county_name

my_vars <- c("state_name", "county_name", "year","dem_votes","gop_votes","margin","perc_margin")
my_table <- full_elections[my_vars]
colnames(my_table) = c('State', 'County', 'Year', 'DEM Votes', 'GOP Votes','Margin','% Margin')
year_select <- unique(full_elections$year)
state_select <- unique(full_elections$state_name)

county_select <-unique(full_elections$county_name)

state_select_usa <-unique(USA$NAME_1)

table1=as.data.frame(my_table)
table1$`% Margin`=paste(round(table1$`% Margin`*100,1),'%',sep="")
#table1$`% Margin` = label_percent()(round(table1$`% Margin`,1))
table1$`DEM Votes` = formatC(table1$`DEM Votes`,format="f",big.mark=",",digits=0)
table1$`GOP Votes` = formatC(table1$`GOP Votes`,format="f",big.mark=",",digits=0)
table1$Margin = formatC(table1$Margin,format="f",big.mark=",",digits=0)


year <- c(1960,1964,1968,1972,1976,1980,1984,1988,1992,1996,2000,2004,2008,2012,2016,2020)
dem_ev = c(303,486,191,17,297,49,13,111,370,379,266,251,365,332,227,306)
rep_ev = c(219,52,301,520,240,489,525,426,168,159,271,286,173,206,304,232)

df <- data.frame(cbind(year, dem_ev, rep_ev)) %>%
  rename(Democrat = dem_ev, Republican = rep_ev) %>%
  pivot_longer(!year, names_to = "party", values_to = "votes")

df$party <- factor(df$party, levels = c("Democrat", "Republican"))


temp2012 <- merge(USA, cluster2012,
              by.x = c("NAME_1", "CountyName"),
              by.y = c("State", "County"),
              all.x = TRUE,
              duplicateGeoms=TRUE)

temp2016 <- merge(USA, cluster2016,
                  by.x = c("NAME_1", "CountyName"),
                  by.y = c("State", "County"),
                  all.x = TRUE,
                  duplicateGeoms=TRUE)


# Define UI for application
ui <- fluidPage(
  dashboardPage(
    dashboardHeader(title=""),
    dashboardSidebar(
      sidebarMenu(
        menuItem("Welcome",
                 tabName = "welcome",
                 icon=icon("door-open")
        ),
        menuItem("All Data",
                 tabName = "AllData",
                 icon=icon("table")
        ),
        menuItem("National Results",
                 tabName = "nat_results",
                 icon=icon("flag-usa")
        ),
        menuItem("State Results",
                 tabName = "sta_results",
                 icon=icon("map-marker-alt")
        ),
        menuItem("Clustering",
                 tabName = "clustering",
                 icon=icon("users")
        ),
        menuItem("2024 Forecast",
                 tabName = "forecast",
                 icon=icon("chart-line")
        )
        
      )
    ),
    dashboardBody(
      tabItems(
#--------------------Welcome Tab-------------------#
        tabItem(
          tabName = "welcome",
          fluidPage(
            h1("Welcome to my US Presidential Elections Dashboard!"),
                    br(),
                    p(strong(tags$u("What is the purpose of this dashboard?"))),
                    p("This dashboard attempts to answer several questions:"), 
                    p(tags$ul(tags$li(div("How has the vote for President changed over time?")))),
                    p(tags$ul(tags$li(div("What are the characteristics of counties that vote similarly?")))),
                    p(tags$ul(tags$li(div("What will the results of the next election look like?")))),
                    br(),
                    p(strong(tags$u("What data is being used for this analysis"))),
                    p("Data from each US presidential election from 1960 to 2020 was included in this analysis.  Most of the data was gathered from this", a(" Github repository",href="https://github.com/cilekagaci/us-presidential-county-1960-2016")," covering elections from 1960 to 2020.  Data for the 2020 election was obtained from this", a("repository.",href="https://github.com/tonmcg/US_County_Level_Election_Results_08-20")),
                    p("County-level socioeconomic data was pulled from this link",a(" here ", href="https://www.ahrq.gov/sdoh/data-analytics/sdoh-data.html") ,"from the Agency for Healthcare Research and Quality."),
                    p(strong(tags$u("How was the data analyzed?"))),
                    p("The National and State Results tabs attempt to answer the 1st question addressed above with descriptive analyses on voting histories.  The Clustering tab attempts to answer the 2nd question by using", a("K-means clustering",href="https://en.wikipedia.org/wiki/K-means_clustering"), "to group counties with similar voting patterns and characteristics.  The 2024 Forecast tab attempts to answer the 3rd question by using an", a("ARMA(1,1)",href="https://en.wikipedia.org/wiki/Autoregressive%E2%80%93moving-average_model"),"model to predict the winner of the next US Presidential election. "),
                    p(strong(tags$u("What are the limitations of this data?"))),
                    p("Data was pulled from multiple sources and combined.  The data sources may have had different standard and/or methods of collecting and maintaining information."),
                    p("Further, data for Alaska was available, but was not presented with the standard FIPS county code identifier.  Thus, it was not conducive for regular plotting procedures.  Thus, vote estimates from this link", a("here",href="https://github.com/tonmcg/US_County_Level_Election_Results_08-20/issues/2"),"were used to take advantage of their consistency with the FIPS county code format.  This was used as the authoritative source of data for Alaska, which only had data from 1960 through 2016.")
                    
            )
          ),
#--------------------Data Tab-------------------#

        tabItem(
          tabName = "AllData",
          DTOutput("alldata")
        ),
#--------------------National Results Tab-------------------#

        tabItem(
          tabName = "nat_results",
          fluidRow(align="center",
                   column(width=4,
                            actionButton("modal1", "Click Here for Instructions", style="text-align:center",class = "btn-md")
                          ),
                   column(width=4,
                            sliderInput("slider","Choose an election year:",min=1960, max=2020, step=4,value=2020,sep="")
                          ),
                   column(width=4,
                            prettyRadioButtons(inputId = "rb1", 
                               label = "Make a selection:",
                               c("Vote % Map"="Vote % Map",
                                 "Vote Total Map"="Vote Total Map"),
                               animation = "pulse")
                          )
            
          ),
          bsModal("modal1_text", "Instructions", "modal1", size = "medium",
                  helpText("To the right of this button, you will find the controls for this page.  You can select any election year from 1960 to 2020 to change the map below."),
                  helpText('Use the radio button to change between the vote % map and the vote total map.')
                  ),
          fluidRow(
            align='center',
            leafletOutput("nat_results")
            
          ),
          fluidRow(
            align='center',
            plotlyOutput("elec_votes_bar",height="200px")
            
          )

        ),
#--------------------State Results Tab-------------------#

        tabItem(
          tabName = "sta_results",
          fluidRow(align="center",
                   column(width=4,
                        actionButton("modal2", "Click Here for Instructions", style="text-align:center",class = "btn-md")
                        ),
                   column(width=4,
                        sliderInput("slider2","Choose an election year:",min=1960, max=2020, step=4,value=2020,sep="")
                        ),
                   column(width=4,
                        selectInput(inputId = "state_select1",
                                    label="Select a state:",
                                    choices=as.list(state_select),
                                    selected = state_select[1]),
                        selectInput(inputId = "county_select_hidden",
                                    label="Select a county:",
                                    choices= county_select,
                                    selected = county_select[1]
                                    )
                   )
                   
            ),
          fluidRow(align='center',valueBoxOutput("vbox0",width=12)),
          fluidRow(align="center",splitLayout(cellWidths = c("20%","20%","20%","20%","20%"),
                                              valueBoxOutput("vbox1",width=2.4),
                                              valueBoxOutput("vbox2",width=2.4),
                                              valueBoxOutput("vbox3",width=2.4),
                                              valueBoxOutput("vbox4",width=2.4),
                                              valueBoxOutput("vbox5",width=2.4)
                                              
                                              )
                   ),
          fluidRow(
            align='center',splitLayout(cellWidths = c("50%","50%"),
                                       leafletOutput("state_results"),
                                       plotlyOutput("part_line_county_graph")
                                       )
          ),
    
          
          
          bsModal("modal2_text", "Instructions", "modal2", size = "medium",
                  helpText("To the right of this button, you will find the controls for this page. You can select any election year from 1960 to 2020 to change the map below."),
                  helpText('Choose a state from the dropdown menu to view results by county for your preferred state.'),
                  helpText('If you click on any county on the map, the graph on the right will populate with the % of the vote earned by the two major parties plotted over time for the selected county.')
          )
          ),
#--------------------Clustering Tab-------------------#
        tabItem(
          tabName = "clustering",
          fluidRow(align='center',
                   column(width=3,
                            actionButton("modal3", "Click Here for Instructions", style="text-align:center",class = "btn-md")

                          ),
                   column(width=3,
                            selectInput(inputId = "state_select2",
                                    label="Select a state:",
                                    choices=as.list(state_select),selected = state_select[1])
                          ),
                   column(width=3,
                            selectInput(inputId = "county_select1",
                                    label="Select a county:",
                                    choices = NULL)
                          ),
                   column(width=3,
                            prettyRadioButtons(inputId = "rb2", 
                                           label = "Make a selection:",
                                           c("2012 Election"="2012 Election",
                                             "2016 Election"="2016 Election"),
                                           animation = "pulse")
                   )
                        
                        
                          
                        
            
          ),
          fluidRow(align='center',valueBoxOutput("vbox0b",width=12)),
          fluidRow(align="center",splitLayout(cellWidths = c("20%","20%","20%","20%","20%"),
                                              valueBoxOutput("vbox1b",width=2.4),
                                              valueBoxOutput("vbox2b",width=2.4),
                                              valueBoxOutput("vbox3b",width=2.4),
                                              valueBoxOutput("vbox4b",width=2.4),
                                              valueBoxOutput("vbox5b",width=2.4)
                                              
          )
          ),
          fluidRow(
            leafletOutput('cluster_map')
    
            
          ),
          fluidRow(align='center',
            actionButton("modal3b", "Click Here for Full Cluster Details", style="text-align:center",class = "btn-md")
          ),
          bsModal("modal3_text", "Instructions", "modal3", size = "medium",
                  helpText("To the right of this button, you will find the controls for this page. Select a state from the first dropdown box, and then select a county from the second dropdown box. These selections should populate the map below showing other counties that were contained in the same cluster."),
                  helpText('Use the radio button to change between clusters calculated for the 2012 election vs. the 2016 election.')
          ),
          bsModal(
            "modal3b_text", "Detailed Cluster Statistics", "modal3b", size = "medium",
            helpText(htmlOutput("detailed_stats"))
          )
        ),
#--------------------Time Series Predictions Tab-------------------#

        tabItem(
          tabName = "forecast",
          fluidRow(align='center',
                   column(width=4,
                            actionButton("modal4", "Click Here for Instructions", style="text-align:center",class = "btn-md")
                          ),
                   column(width=4,
                            p(strong("2024 US Presidential Election Predictions"),style = "font-size: 150%;")
                          ),
                   column(width=4,
                            prettyRadioButtons(inputId = "rb3", 
                                           label = "Make a selection:",
                                           c("Country View"="Country View",
                                             "State View"="State View"),
                                           animation = "pulse")
                   )
            ),
          fluidRow(align='center',valueBoxOutput("vbox0c",width=12)),
          fluidRow(align="center",splitLayout(cellWidths = c("25%","25%","25%","25%"),
                                              valueBoxOutput("vbox1c",width=2.4),
                                              valueBoxOutput("vbox2c",width=2.4),
                                              valueBoxOutput("vbox3c",width=2.4),
                                              valueBoxOutput("vbox4c",width=2.4)
                                              
          )
          ),
          fluidRow(
            align='center',
            selectInput(inputId = "state_select3",
                        label="Select a state:",
                        choices=as.list(state_select),selected = state_select[1]),
          ),
          fluidRow(
            leafletOutput('prediction_map')
          ),
          bsModal("modal4_text", "Instructions", "modal4", size = "medium",
                  helpText("To the right of this button, you will find the controls for this page."),
                  helpText("Click on the 'Country View' button to see the 2024 predictions at the national level."),
                  helpText('Click on the "State View" button to see the 2024 predictions at a specific state level. Hover over the counties on the map in this view to see the predictions for a specific county.')
          )
        
            
          )
          ))))
    
# Define server logic 
server <- function(input, output, session) {
  
  
#----------ALL DATA TABLE----------#
  output$alldata=renderDT({
    datatable(table1,
              options=list(pageLength=10,
                                  lengthMenu=c(10,15,20,25)
                                  
    ),
    rownames = FALSE,
    caption = htmltools::tags$caption(
      style = "caption-side: top; text-align: center; color:black; font-weight: bold",
      'All Data'
    )) 
  })
  
#----------National Level Results Map----------#
  
  filtered_map_data=reactive({
    filter=subset(full_elections,year==input$slider)
    return(filter)
  })
  
  
  
  merge_filter <- reactive({
    temp <- merge(USA, filtered_map_data(),
                  by.x = c("NAME_1", "CountyName"), 
                  by.y = c("state_name", "county_name"),
                  all.x = TRUE)
  })
#Data for electoral college bars
  filtered_data=reactive({
    filter=subset(df,year==input$slider)
    return(filter)
  })


  #--------------------National Results Choropleth vs. Dot Plot Map -------------------#
  
  output$nat_results <-renderLeaflet({
    
    
    # Create a color palette
    palette_rev <- rev(brewer.pal(11, "RdBu"))
    
    
    mypal <- colorNumeric(palette = palette_rev, 
                          domain = merge_filter()$per_gop, 
                          na.color = "grey")
    
    mypal2=colorNumeric("RdBu",merge_filter()$perc_margin)
    
    
    switch(input$rb1,
           "Vote % Map"=
           leaflet() %>% 
              addProviderTiles(providers$CartoDB.Positron,
                              options = tileOptions(minZoom =0, maxZoom = 13),
                              group = "CartoDB.Positron") %>%
              setView(lat = 39.8283, 
                     lng = -98.5795, 
                     zoom = 3) %>%
              addPolygons(data = USA, stroke = TRUE, weight = 0.1,
                          smoothFactor = 0.2, fillOpacity = 0.8,
                          fillColor = ~mypal(merge_filter()$per_gop),
                          popup = paste("County: ", merge_filter()$CountyName, "<br>",
                                        "Democratic Votes: ", formatC(merge_filter()$dem_votes,format='d',big.mark = ","), "<br>",
                                        "Republican Votes: ", formatC(merge_filter()$gop_votes,format='d',big.mark = ","), "<br>",
                                        "Margin: ", paste0(round(merge_filter()$perc_margin*100,1),'%'), "<br>")) %>%
              addLegend(position = "bottomleft", 
                        pal = mypal, 
                        values = merge_filter()$per_gop,
                        title = "D-R Scale",
                        opacity = 1),
           "Vote Total Map"=
           
           leaflet(data=merge_filter()) %>% 
             addProviderTiles(providers$CartoDB.Positron,
                              options = tileOptions(minZoom =0, maxZoom = 13),
                              group = "CartoDB.Positron") %>%
             setView(lat = 39.8283, 
                     lng = -98.5795, 
                     zoom = 3) %>%
        
             addCircles(radius = ~(merge_filter()$gop_dem_total)/20, 
                        weight = 1, 
                        color = "black", 
                        fillColor = ~mypal(merge_filter()$per_gop),
                        lat = merge_filter()$Lon,
                        lng = merge_filter()$Lat,
                        popup = paste("County: ", merge_filter()$CountyName, "<br>",
                                      "Democratic Votes: ", formatC(merge_filter()$dem_votes,format='d',big.mark = ","), "<br>",
                                      "Republican Votes: ", formatC(merge_filter()$gop_votes,format='d',big.mark = ","), "<br>",
                                      "Margin: ", paste0(round(merge_filter()$perc_margin*100,1),"%"), "<br>"),
                        fillOpacity = 0.7,
                        group = "Points")   %>%
             addLegend(position = "bottomleft",
                       pal = mypal, 
                       values = merge_filter()$per_gop,
                       title = "D-R Scale",
                       opacity = 1)
    )
})

#--------------------Electoral Votes by Party Plot-------------------#
output$elec_votes_bar <-renderPlotly({
  
  p<-ggplotly(
    ggplot(
      data=filtered_data(),
      aes(x=party, y=votes, fill=party,
          text=paste("Party: ",party, "<br>",
                     "Electoral Votes: ", votes))) +
      scale_fill_manual(values = c("#3862ea", "#e53636")) +
      geom_bar(stat="identity")+
      coord_flip()+
      theme(legend.position="none")+
      ylab('Electoral Votes')+xlab(''),
      tooltip = c("text"))
  p
  
  
})


#----------State/County Map and Stats----------#



  #Create Datasets to use for mapping

  #Step 1: Filter by year
  year_filter=reactive({
    filter=subset(full_elections,year==input$slider2)
    return(filter)
  })

  #Step 2: Merge year filtered dataset on mapping data to use for overall color
  
  color_filter <- reactive({
    temp <- merge(USA, year_filter(),
                  by.x = c("NAME_1", "CountyName"),
                  by.y = c("state_name", "county_name"),
                  all.x = TRUE)
  })

  #Step 3: Filter down to just state level data
  state_filter=reactive({
    filter=subset(color_filter(),NAME_1==input$state_select1)
    return(filter)
  })



  #Step 4: Filter the United States map down to one state
  just_the_map=reactive({
    filter=subset(USA,NAME_1==input$state_select1)
    return(filter)
  })

  
  # reactive text 
  rv <- reactiveValues()
  
  
  # update county options on state select
  observeEvent(input$state_select1,{
    choices <- subset(full_elections, full_elections$state_name == input$state_select1)$county_name
    updateSelectInput(session,
                      "county_select_hidden",
                      choices = choices,
                      selected = choices[1])
    rv$county <- input$county_select1
  })
  
  # update county on map click
  observeEvent(input$state_results_shape_click,{
    rv$county <- input$state_results_shape_click$id
    choices <- subset(full_elections, full_elections$state_name == input$state_select1)$county_name
    updateSelectInput(session,
                      "county_select_hidden",
                      selected = input$state_results_shape_click$id)
  })
  
#Grab the county filtered data
  just_the_county <- reactive({
    #req(rv$county)
    county_data <-subset(full_elections,full_elections$state_name==input$state_select1)
    county_data <-subset(county_data,county_data$county_name==input$county_select_hidden)
    return(county_data)
    
  })
  
  
#Number of elections county voted for winner
  winner_votes <- reactive({
    #req(rv$county)
    county_data <-subset(full_elections,full_elections$state_name==input$state_select1)
    county_data <-subset(county_data,county_data$county_name==input$county_select_hidden)
    sum_matches <-sum(county_data$match)
    return(sum_matches)
    
  })
  
  
#Number of elections county voted for democrat
  dem_winner <- reactive({
    #req(rv$county)
    county_data <-subset(full_elections,full_elections$state_name==input$state_select1)
    county_data <-subset(county_data,county_data$county_name==input$county_select_hidden)
    sum_dem_wins <-sum(county_data$dem_county_winner)
    return(sum_dem_wins)
    
  })
  
#Number of elections county voted for republican
  gop_winner <- reactive({
    #req(rv$county)
    county_data <-subset(full_elections,full_elections$state_name==input$state_select1)
    county_data <-subset(county_data,county_data$county_name==input$county_select_hidden)
    sum_gop_wins <-sum(county_data$gop_county_winner)
    return(sum_gop_wins)
    
  })
  
  
#Closest vote
  closest <- reactive({
    #req(rv$county)
    county_data <-subset(full_elections,full_elections$state_name==input$state_select1)
    county_data <-subset(county_data,county_data$county_name==input$county_select_hidden)
    closest_margin <-min(county_data$perc_margin)
    return(closest_margin)
    
  })
  
  
  #Year of closest vote
  closest_year <- reactive({
    #req(rv$county)
    county_data <-subset(full_elections,full_elections$state_name==input$state_select1)
    county_data <-subset(county_data,county_data$county_name==input$county_select_hidden)
    closest_margin <-min(county_data$perc_margin)
    county_data_closest_vote <- subset(county_data,county_data$perc_margin==closest_margin)
    county_data_closest_vote_year <- county_data_closest_vote$year
    return(county_data_closest_vote_year)
    
  })
  
  
  #Largest Combined 3rd Party Vote
  max_third_party <- reactive({
    #req(rv$county)
    county_data <-subset(full_elections,full_elections$state_name==input$state_select1)
    county_data <-subset(county_data,county_data$county_name==input$county_select_hidden)
    county_data$third_party <- 1-(county_data$gop_demperc)
    max_third_party <- max(county_data$third_party)
    
    return(max_third_party)
    
  })
  
  
  #Year of Largest Combined 3rd Party Vote
  max_third_party_year <- reactive({
    #req(rv$county)
    county_data <-subset(full_elections,full_elections$state_name==input$state_select1)
    county_data <-subset(county_data,county_data$county_name==input$county_select_hidden)
    county_data$third_party <- 1-(county_data$gop_demperc)
    max_third_party <- max(county_data$third_party)
    
    county_data_third_party_year <-subset(county_data,county_data$third_party==max_third_party)
    county_data_third_party_year_max <- county_data_third_party_year$year
    return(county_data_third_party_year_max)
    
  })

  
  output$vbox0 <- renderValueBox({
    valueBox(value = paste(input$county_select_hidden,'Stats'),
             subtitle = '',
             color = "light-blue"
    )
  })
  
  output$vbox1 <- renderValueBox({
    valueBox(value = tags$p(paste0(winner_votes(),"/16 Elections"),style = "font-size: 65%;"),
             subtitle = 'Voted for Winner',
             color = "light-blue"
    )
  })
  
  output$vbox2 <- renderValueBox({
    #tags$p("90k", style = "font-size: 150%;")
    valueBox(value =tags$p(paste0(dem_winner(),"/16 Elections"),style = "font-size: 65%;"),
             subtitle = 'Voted for Democrat',
             color = "light-blue"
    )
  })
  
  output$vbox3 <- renderValueBox({
    valueBox(value = tags$p(paste0(gop_winner(),"/16 Elections"),style = "font-size: 65%;"),
             subtitle = 'Voted for Republican',
             color = "light-blue"
    )
  })
  
  output$vbox4 <- renderValueBox({
    valueBox(value = tags$p(paste0(round((closest()*100),1),'% margin in ',closest_year()),style = "font-size: 65%;"),
             subtitle = 'Closest Election',
             color = "light-blue"
    )
  })
  
  output$vbox5 <- renderValueBox({
    valueBox(value = tags$p(paste0(round(max_third_party()*100,1),"% of votes in ",max_third_party_year()),style = "font-size: 65%;"),
             subtitle = 'Largest 3rd Party Vote',
             color = "light-blue"
    )
  })


#--------------------State Results with Click-County Stats-------------------#
  output$state_results <-renderLeaflet({
    # Create a color palette
    palette_rev <- rev(brewer.pal(11, "RdBu"))
    
    
    mypal <- colorNumeric(palette = palette_rev, 
                          domain = color_filter()$per_gop, 
                          na.color = "grey")
    
    
    leaflet() %>% 
      
      addProviderTiles(providers$CartoDB.Positron,
                       options = tileOptions(minZoom =0, maxZoom = 13),
                       group = "CartoDB.Positron") %>%

      addPolygons(data = just_the_map(), stroke = TRUE, weight = 0.1,
                  smoothFactor = 0.2, fillOpacity = 0.8,
                  #Essential for getting the click data to populate
                  layerId = ~CountyName, 
                  fillColor = ~mypal(state_filter()$per_gop),
                  popup = paste("County: ", state_filter()$CountyName, "<br>",
                                "Democratic Votes: ", formatC(state_filter()$dem_votes,format="d",big.mark=","), "<br>",
                                "Republican Votes: ", formatC(state_filter()$gop_votes,format="d",big.mark=","), "<br>",
                                "Margin: ", paste0(round(state_filter()$perc_margin*100,1),"%"), "<br>")) %>%

      addLegend(position = "bottomleft", 
                pal = mypal, 
                values = state_filter()$per_gop,
                title = "D-R Scale",
                opacity = 1)
  })
  
  
  
  
  
  

#---------- Update County Dropdown box from State Dropdown Box -----------#
# #this needs to be hidden
#   observeEvent(input$state_select1,{
#     updateSelectInput(session,'county_select_hidden',
#                       choices=unique(full_elections$county_name[full_elections$state_name==input$state_select1]))
#   })
  
#   # 
#   # update county options on state select
#   observeEvent(input$state_select1,{
#     choices <- subset(full_elections, full_elections$state_name == input$state_select1)$county_name
#     updateSelectInput(session,
#                       "county_select1",
#                       choices = county_select,
#                       selected = county_select[1])
#     rv$county <- input$county_select1
#   })
# 
# #update county on map click
#   observeEvent(input$state_results_shape_click,{
#     rv$county <- input$state_results_shape_click$id
#     choices <- subset(full_elections, full_elections$state_name == input$state_select1)$county_name
#     updateSelectInput(session,
#                       "county_select1",
#                       selected = input$state_results_shape_click$id)
#   })
#   
#   
  
  
  # # update county on map click
  # observe({ 
  #   rv$county <- input$state_results_shape_click$id
  # })

#-------------------% of Vote by Each Party by County-------------------#
  output$part_line_county_graph <-renderPlotly({
    p=ggplot(just_the_county(), 
             aes_string(x=just_the_county()$year, y=just_the_county()$per_dem))+
      geom_line(color="blue",size=1.1)+

      geom_line(aes(y = just_the_county()$per_gop, 
                    colour = "red"),
                size=1.1)+
      geom_point(size=1.5,
                 aes(text=paste("Year: ",just_the_county()$year, "<br>",
                                "% DEM Vote: ",paste(round(just_the_county()$per_dem*100,1),"%"))))+
      geom_point(size=1.5,
                 aes(y = just_the_county()$per_gop,
                     text=paste("Year: ",just_the_county()$year, "<br>",
                                "% GOP Vote: ", paste(round(just_the_county()$per_gop*100,1),"%"))))+
      ylab("% of Vote")+
      xlab("Year")+
      ggtitle(paste0("Results from ",unique(just_the_county()$county_name)))+
      theme(legend.position = "none",
            plot.title = element_text(color="black", size=14, face="bold",hjust=0.5))+
      #scale_y_continuous(labels = comma)
      scale_y_continuous(labels = percent)
    ggplotly(p, tooltip = c("text"))
    
    
    
  })
  
  
  
  
#----------Clustering Tab----------#
  
  observeEvent(input$state_select2,{
    updateSelectInput(session,'county_select1',
                      choices=unique(full_elections$county_name[full_elections$state_name==input$state_select2]))
  })
  
  #Cluster Data Filter - 2012 
  cluster_filter2012 <- reactive({
    
    state_selected_data <- subset(temp2012, temp2012$NAME_1==input$state_select2)
    county_selected_data <- subset(state_selected_data, state_selected_data$CountyName==input$county_select1)
    county_cluster <- county_selected_data$cluster
    cluster_data <-subset(temp2012,temp2012$cluster==county_cluster)
    return(cluster_data)
    
  })
  
  #Cluster Data Filter - 2016
  cluster_filter2016 <- reactive({
    
    state_selected_data <- subset(temp2016, temp2016$NAME_1==input$state_select2)
    county_selected_data <- subset(state_selected_data, state_selected_data$CountyName==input$county_select1)
    county_cluster <- county_selected_data$cluster
    cluster_data <-subset(temp2016,temp2016$cluster==county_cluster)
    return(cluster_data)
    
  })
  
  output$vbox0b <- renderValueBox({
    switch(
      input$rb2, 
      "2012 Election"=
    valueBox(value = paste(input$county_select1, ' belongs to Cluster #',unique(cluster_filter2012()$cluster),'. Below are the median cluster metrics:',style = "font-size: 65%;"),
             subtitle = '',
             color = "light-blue"
    ),
    "2016 Election"=
      valueBox(value = paste(input$county_select1, ' belongs to Cluster #',unique(cluster_filter2016()$cluster),'. Below are the median cluster metrics:',style = "font-size: 65%;"),
               subtitle = '',
               color = "light-blue"
      ))
  })
  
  output$vbox1b <- renderValueBox({
    switch(
      input$rb2, 
      "2012 Election"=
    valueBox(value = paste0(round(median(cluster_filter2012()$`% DEM`)*100,1),'%'),
             subtitle = '% DEM Vote',
             color = "light-blue"
    ),
    "2016 Election"=
      valueBox(value = paste0(round(median(cluster_filter2016()$`% DEM`)*100,1),'%'),
               subtitle = '% DEM Vote',
               color = "light-blue"
      ))
  })
  
  output$vbox2b <- renderValueBox({
    switch(
      input$rb2, 
      "2012 Election"=
    valueBox(value = paste0(round(median(cluster_filter2012()$`% GOP`)*100,1),'%'),
             subtitle = '% GOP Vote',
             color = "light-blue"
    ),
    "2016 Election"=
      valueBox(value = paste0(round(median(cluster_filter2016()$`% GOP`)*100,1),'%'),
               subtitle = '% GOP Vote',
               color = "light-blue"
      ))
  })
  
  output$vbox3b <- renderValueBox({
    switch(
      input$rb2, 
      "2012 Election"=
    valueBox(value = paste0('$',formatC(median(cluster_filter2012()$`Per Capita Income`),format="d",big.mark = ",")),
             subtitle = 'Per Capita Income',
             color = "light-blue"
    ),
    "2016 Election"=
      
      valueBox(value = paste0('$',formatC(median(cluster_filter2016()$`Per Capita Income`),format="d",big.mark = ",")),
               subtitle = 'Per Capita Income',
               color = "light-blue"
      ))
  })
  
  output$vbox4b <- renderValueBox({
    switch(
      input$rb2, 
      "2012 Election"=
    valueBox(value = paste0(round(median(cluster_filter2012()$`Unemployment Rate`),1),'%'),
             subtitle = '% Unemployed',
             color = "light-blue"
    ),
    "2016 Election"=
      valueBox(value = paste0(round(median(cluster_filter2016()$`Unemployment Rate`),1),'%'),
               subtitle = '% Unemployed',
               color = "light-blue"
      ))
  })
  
  
  output$vbox5b <- renderValueBox({
    switch(
      input$rb2, 
      "2012 Election"=
    valueBox(value = formatC(median(cluster_filter2012()$Population),format="d",big.mark = ","),
             subtitle = 'Population',
             color = "light-blue"
    ),
    "2016 Election"=
      valueBox(value = formatC(median(cluster_filter2016()$Population),format="d",big.mark = ","),
               subtitle = 'Population',
               color = "light-blue"
      ))
      
  })
  
#-------------------Cluster Map for 2012 vs. 2016 Election data-------------------#
  
  output$cluster_map <-renderLeaflet({
    
    switch(input$rb2, "2012 Election"=
  
    p<-leaflet(cluster_filter2012()) %>% 
      addProviderTiles(providers$CartoDB.Positron,
                       options = tileOptions(minZoom =0, maxZoom = 13),
                       group = "CartoDB.Positron") %>%
      addPolygons(data = cluster_filter2012(), stroke = TRUE, weight = 1.0,
                  smoothFactor = 0.2, fillOpacity = 0.3,
                  color='#8A2BE2',
                  popup = paste("Cluster: ", cluster_filter2012()$cluster, "<br>",
                                "County: ", cluster_filter2012()$CountyName, "<br>",
                                "Democratic Votes: ", formatC(cluster_filter2012()$`DEM Votes`,format="d",big.mark = ","), "<br>",
                                "Republican Votes: ", formatC(cluster_filter2012()$`GOP Votes`,format="d",big.mark = ","), "<br>",
                                "% Margin:", paste0(round((cluster_filter2012()$`% Margin`)*100,1),'%'))
                  
      ),
    "2016 Election"=
      p<-leaflet(cluster_filter2016()) %>% 
      addProviderTiles(providers$CartoDB.Positron,
                       options = tileOptions(minZoom =0, maxZoom = 13),
                       group = "CartoDB.Positron") %>%
      addPolygons(data = cluster_filter2016(), stroke = TRUE, weight = 1.0,
                  smoothFactor = 0.2, fillOpacity = 0.3,
                  color='#8A2BE2',
                  popup = paste("Cluster: ", cluster_filter2016()$cluster, "<br>",
                                "County: ", cluster_filter2016()$CountyName, "<br>",
                                "Democratic Votes: ", formatC(cluster_filter2016()$`DEM Votes`,format="d",big.mark = ","), "<br>",
                                "Republican Votes: ", formatC(cluster_filter2016()$`GOP Votes`,format="d",big.mark = ","), "<br>",
                                "% Margin:", paste0(round((cluster_filter2016()$`% Margin`)*100,1),'%'))
                  
      ))
    
  })
  
#-------------------Detailed Cluster Statistics Accessed by Modal Button under map-------------------#
  
  output$detailed_stats = renderText({
    switch(input$rb2,
           "2012 Election"=
    paste(
      p("Vote Share"), 
      p("1.) % of vote earned by Democrats:",paste(round(median(cluster_filter2012()$`% DEM`)*100,1),"%")), 
      p("2.) % of vote earned by Republicans:",paste(round(median(cluster_filter2012()$`% GOP`)*100,1),"%")), 
      tags$br(),
      p("Education"),
      p("1.) % of population with a High School Diploma:",paste(round(median(cluster_filter2012()$`% High School Diploma`),1),"%")),
      p("2.) % of population with a Bachelors Degree:",paste(round(median(cluster_filter2012()$`% Bachelors Degree`),1),"%")),
      p("3.) % of population with a Graduate Degree:",paste(round(median(cluster_filter2012()$`% Graduate Degree`),1),"%")),
      tags$br(),
      p("Demographics"),
      p("1.) % of population that are Women:",paste(round(median(cluster_filter2012()$`% Women`),1),"%")),
      p("2.) % of population that are White:",paste(round(median(cluster_filter2012()$`% White`),1),"%")),
      p("3.) % of population that are Black:",paste(round(median(cluster_filter2012()$`% Black`),1),"%")),
      p("4.) % of population that are American Indian:",paste(round(median(cluster_filter2012()$`% American Indian`),1),"%")),
      p("5.) % of population that are Asian:",paste(round(median(cluster_filter2012()$`% Asian`),1),"%")),
      p("6.) % of population that are Hispanic:",paste(round(median(cluster_filter2012()$`% Hispanic`),1),"%")),
      p("7.) % of population that are Veterans:",paste(round(median(cluster_filter2012()$`% Veteran`),1),"%")),
      p("8.) % of population that were not born in the US:",paste(round(median(cluster_filter2012()$`% Foreign Born`),1),"%")),
      p("9.) Median Age:",round(median(cluster_filter2012()$Age),1)),
      tags$br(),
      p("Economics"),
      p("1.) Per Capita Income:",paste("$",round(median(cluster_filter2016()$`Per Capita Income`),2))),
      p("2.) % Unemployed:" ,paste(round(median(cluster_filter2012()$`Unemployment Rate`),1),"%")),
      p("3.) Household Size:",round(median(cluster_filter2012()$`Household Size`),1)),
      p("4.) Gini Index of Income Inequality:",round(median(cluster_filter2012()$`Gini Index`),1)),
      p("5.) Violent Crime Reports per 100,000 people:",round(median(cluster_filter2012()$`Violent Crime`),1)),
      tags$br(),
      p("Population Density"),
      p("1.) Population:",formatC(round(median(cluster_filter2012()$Population),1),format="d",big.mark = ",")),
      p("2.) Land Area in Square Miles:",round(median(cluster_filter2012()$`Sq. Meters Area Land`),1))
      
      
      
    ),
    "2016 Election"=
      paste(
        p("Vote Share"), 
        p("1.) % of vote earned by Democrats:",paste(round(median(cluster_filter2016()$`% DEM`)*100,1),"%")), 
        p("2.) % of vote earned by Republicans:",paste(round(median(cluster_filter2016()$`% GOP`)*100,1),"%")), 
        tags$br(),
        p("Education"),
        p("1.) % of population with a High School Diploma:",paste(round(median(cluster_filter2016()$`% High School Diploma`),1),"%")),
        p("2.) % of population with a Bachelors Degree:",paste(round(median(cluster_filter2016()$`% Bachelors Degree`),1),"%")),
        p("3.) % of population with a Graduate Degree:",paste(round(median(cluster_filter2016()$`% Graduate Degree`),1),"%")),
        tags$br(),
        p("Demographics"),
        p("1.) % of population that are Women:",paste(round(median(cluster_filter2016()$`% Women`),1),"%")),
        p("2.) % of population that are White:",paste(round(median(cluster_filter2016()$`% White`),1),"%")),
        p("3.) % of population that are Black:",paste(round(median(cluster_filter2016()$`% Black`),1),"%")),
        p("4.) % of population that are American Indian:",paste(round(median(cluster_filter2016()$`% American Indian`),1),"%")),
        p("5.) % of population that are Asian:",paste(round(median(cluster_filter2016()$`% Asian`),1),"%")),
        p("6.) % of population that are Hispanic:",paste(round(median(cluster_filter2016()$`% Hispanic`),1),"%")),
        p("7.) % of population that are Veterans:",paste(round(median(cluster_filter2016()$`% Veteran`),1),"%")),
        p("8.) % of population that were not born in the US:",paste(round(median(cluster_filter2016()$`% Foreign Born`),1),"%")),
        p("9.) Median Age:",round(median(cluster_filter2016()$Age),1)),
        tags$br(),
        p("Economics"),
        p("1.) Per Capita Income:",paste("$",round(median(cluster_filter2016()$`Per Capita Income`),2))),
        p("2.) % Unemployed:" ,paste(round(median(cluster_filter2016()$`Unemployment Rate`),1),"%")),
        p("3.) Household Size:",round(median(cluster_filter2016()$`Household Size`),1)),
        p("4.) Gini Index of Income Inequality:",round(median(cluster_filter2016()$`Gini Index`),1)),
        p("5.) Violent Crime Reports per 100,000 people:",round(median(cluster_filter2016()$`Violent Crime`),1)),
        tags$br(),
        p("Population Density"),
        p("1.) Population:",formatC(round(median(cluster_filter2016()$Population),1),format="d",big.mark = ",")),
        p("2.) Land Area in Square Miles:",round(median(cluster_filter2016()$`Sq. Meters Area Land`),1))
        

        
      ))
  })
    
#----------Prediction Tab----------#
  
  #1.) Filter arma down to one row per state
  one_row = ARMA_preds[!duplicated(ARMA_preds$State), ]
  #2.) Filter to only states won by dem
  dem_states = subset(one_row,one_row$Win=="Democratic")
  gop_states = subset(one_row,one_row$Win=="Republican")
  #3.) sum columns
  dem_ev2024 = sum(dem_states$EV)
  gop_ev2024 = sum(gop_states$EV)
  
  dem_votes = sum(ARMA_preds$dem_votes)
  gop_votes = sum(ARMA_preds$gop_votes)
  
  
  winning_candidate <- reactive({
    winner_df = subset(one_row,one_row$State==input$state_select3)
    party = winner_df$Win
    return(party)
    
  })
  
  
  electoral_college_votes <- reactive({
    EV_df = subset(one_row,one_row$State==input$state_select3)
    num = EV_df$EV
    return(num)
    
  })
  
  
  state_dem_votes <- reactive({
    dem_state = subset(ARMA_preds, ARMA_preds$State == input$state_select3)
    total_dem_votes = sum(dem_state$dem_votes)
    return(total_dem_votes)
    
  })
  
  state_gop_votes <- reactive({
    gop_state = subset(ARMA_preds, ARMA_preds$State == input$state_select3)
    total_gop_votes = sum(gop_state$gop_votes)
    return(total_gop_votes)
    
  })
  
  
  state_dem_perc <- reactive({
    dem_state = subset(ARMA_preds, ARMA_preds$State == input$state_select3)
    gop_state = subset(ARMA_preds, ARMA_preds$State == input$state_select3)
    total_dem_votes = sum(dem_state$dem_votes)
    total_gop_votes = sum(gop_state$gop_votes)
    
    perc = round((total_dem_votes/sum(total_dem_votes,total_gop_votes))*100,1)
    
    return(perc)
    
  })
  
  state_gop_perc <- reactive({
    dem_state = subset(ARMA_preds, ARMA_preds$State == input$state_select3)
    gop_state = subset(ARMA_preds, ARMA_preds$State == input$state_select3)
    total_dem_votes = sum(dem_state$dem_votes)
    total_gop_votes = sum(gop_state$gop_votes)
    
    perc = round((total_gop_votes/sum(total_dem_votes,total_gop_votes))*100,1)
    
    return(perc)
    
  })
  

           
  output$vbox0c <- renderValueBox({
    
    switch(input$rb3,
           "Country View"=
              valueBox(value = "The Democratic candidate wins the election",
                       subtitle = "",
                       color = "light-blue"
              ),
            "State View"=
              valueBox(value = paste0("The ",winning_candidate()," candidate wins ",electoral_college_votes()," electoral votes."),
                       subtitle = "",
                       color = "light-blue"
                       )
    )
  })
  
  output$vbox1c <- renderValueBox({
    switch(input$rb3,
           "Country View"=
              valueBox(value = formatC(sum(dem_states$EV),format="d",big.mark = ","),
                       subtitle = paste0("DEM Electoral College Votes"),
                       color = "light-blue"
              ),
           "State View"=
             valueBox(value = formatC(state_dem_votes(),format="d",big.mark = ","),
                      subtitle = "Total State DEM Votes",
                      color = "light-blue"
             )
    )
  })
  
  output$vbox2c <- renderValueBox({
    switch(input$rb3,
           "Country View"=
              valueBox(value = formatC(sum(gop_states$EV),format="d",big.mark = ","),
                       subtitle = paste0("GOP Electoral College Votes"),
                       color = "light-blue"
              ),
           "State View"=
             valueBox(value = formatC(state_gop_votes(),format="d",big.mark = ","),
                      subtitle = "Total State GOP Votes",
                      color = "light-blue"
             )
    )
  })
  
  output$vbox3c <- renderValueBox({
    switch(input$rb3,
           "Country View"=
              valueBox(value = formatC(dem_votes,format="d",big.mark = ","),
                       subtitle = paste0("DEM Popular Vote"),
                       color = "light-blue"
              ),
           "State View"=
             valueBox(value = paste0(state_dem_perc(),"%"),
                      subtitle = paste0("% DEM Vote"),
                      color = "light-blue"
             )
    )
             
  })
  
  output$vbox4c <- renderValueBox({
    switch(input$rb3,
           "Country View"=
              valueBox(value = formatC(gop_votes,format="d",big.mark = ","),
                       subtitle = paste0("GOP Popular Vote"),
                       color = "light-blue"
              ),
           "State View"=
             valueBox(value = paste0(state_gop_perc(),"%"),
                      subtitle = paste0("% GOP Vote"),
                      color = "light-blue"
             )
    )
  })
  
  
  
#-------------------Time Series Prediction Map: Country vs. State View-------------------#
  
  output$prediction_map <-renderLeaflet({
    
    
    #Step 1: Merge predictions dataset on mapping data to use for overall color
    
    color_filter <- reactive({
      temp <- merge(USA, ARMA_preds,
                    by.x = c("NAME_1", "CountyName"),
                    by.y = c("State", "County"),
                    all.x = TRUE)
    })
    
    #Step 2: Filter down to just state level data
    state_filter=reactive({
      filter=subset(color_filter(),NAME_1==input$state_select3)
      return(filter)
    })
    
    
    
    #Step 4: Filter the United States map down to one state
    just_the_map=reactive({
      filter=subset(USA,NAME_1==input$state_select3)
      return(filter)
    })
    
    
    #County Dot Map -->Create a color palette
    mypal=colorNumeric("RdBu",ARMA_preds$per_dem)
    
    
    #State Choropleth
    palette_rev <- rev(brewer.pal(11, "RdBu"))
    mypal <- colorNumeric(palette = palette_rev, 
                          domain = color_filter()$per_gop, 
                          na.color = "grey")
    
    switch(input$rb3,
           "Country View"=
    leaflet(data=ARMA_preds) %>% 
      
      addProviderTiles(providers$CartoDB.Positron,
                       options = tileOptions(minZoom =0, maxZoom = 13),
                       group = "CartoDB.Positron") %>%
      setView(lat = 39.8283, lng = -98.5795, zoom = 3) %>%
      
      addCircles(radius = ~dem_gop_total/20, 
                 weight = 1, 
                 color = "black", 
                 fillColor = ~mypal(ARMA_preds$per_gop),
                 lat = ARMA_preds$Lon,
                 lng = ARMA_preds$Lat,
                 popup = paste("County: ", ARMA_preds$County, "<br>",
                               "Democratic Votes: ", formatC(ARMA_preds$dem_votes,format="d", big.mark=","), "<br>",
                               "Republican Votes: ", formatC(ARMA_preds$gop_votes,format="d", big.mark=","), "<br>",
                               "Margin: ", paste0(round(ARMA_preds$perc_margin*100,1),'%'), "<br>"),
                 fillOpacity = 0.7,
                 group = "Points")%>%
      addLegend(position = "bottomleft", 
                pal = mypal, 
                values = merge_filter()$per_gop,
                title = "D-R Scale",
                opacity = 1),
    "State View"=
      
    leaflet() %>% 
      addProviderTiles(providers$CartoDB.Positron,
                       options = tileOptions(minZoom =0, maxZoom = 13),
                       group = "CartoDB.Positron") %>%
      setView(lat = first(state_filter()$AvgLon),
              lng = first(state_filter()$AvgLat),
              zoom = 5) %>%
      addPolygons(data = just_the_map(), stroke = TRUE, weight = 0.1,
                  smoothFactor = 0.2, fillOpacity = 0.8,
   
                  fillColor = ~mypal(state_filter()$per_gop),
                  popup = paste("County: ", state_filter()$CountyName, "<br>",
                                "Democratic Votes: ", formatC(state_filter()$dem_votes,format="d", big.mark=","), "<br>",
                                "Republican Votes: ", formatC(state_filter()$gop_votes,format="d", big.mark=","), "<br>",
                                "Margin: ", paste0(round(state_filter()$perc_margin*100,1),'%'), "<br>")) %>%
      addLegend(position = "bottomleft", 
                pal = mypal, 
                values = state_filter()$per_gop, 
                title = "D-R Scale", 
                opacity = 1)
    )
  })
}

# Run the application 
shinyApp(ui = ui, server = server)