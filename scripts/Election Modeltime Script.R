#Let's try the modeltime process for my elections data
#Date: April 25th, 2023
#----------------------------------------

#Load libraries ----
message('Loading packages...')
suppressPackageStartupMessages({
  library(readxl)
  library(tidyverse)
  library(tidymodels)
  library(modeltime)
  library(timetk)
  library(lubridate)
  library(timeDate)
  library(poissonreg)
  library(furrr)
  library(tictoc)
  library(tidyr)
  library(workflows)
})

#Load data ----
message('Loading data...')
df <- read_excel("~/Desktop/Data Projects/Elections Project/Data/FullElectionsData.xlsx")

#Make sure each time series is complete - impute 0 for missing ----
message('Prepping the data...')

df <- df %>%
  mutate(year = lubridate::ymd(df$year, truncated = 2L))

df <- df %>%
  group_by(fips_code_lz) %>%
  pad_by_time(
    .date_var = year,
    .by = 'auto',
    .pad_value = 0,
    .start_date = min(df$year),
    .end_date = max(df$year)
  )

#Create case weights - more recent day gets more weight ----
# df <- df %>%
#   group_by(fips_code_lz) %>%
#   mutate(dec_year = lubridate::decimal_date(year),
#          case_wts = exp(max(dec_year) - dec_year))


#Extend each time series into the future ----
df_ext <- df %>%
  group_by(fips_code_lz) %>%
  future_frame(
    .date_var = year,
    .length_out = '4 year',
    .bind_data = TRUE
  )

message('Make 2 partitions of data (DEM, GOP)...')
#Break into dem and gop dfs ----

df_ext_dem <- df_ext %>%
  select(fips_code_lz,year,dem_votes)#,case_wts)


df_ext_gop <- df_ext %>%
  select(fips_code_lz,year,gop_votes)#,case_wts)

#Split into full training data and future data that will be forecasted ----
message('Make 2 partitions of data (full, future)...')

#DEM dfs
df_dem_full_data <- df_ext_dem %>%
  drop_na() %>%
  tidyr::nest(data_full = c(-fips_code_lz))

df_dem_future_data <-df_ext_dem %>%
  filter(is.na(dem_votes)==TRUE) %>%
  tidyr::nest(data_future = c(-fips_code_lz))


#GOP dfs
df_gop_full_data <- df_ext_gop %>%
  drop_na() %>%
  tidyr::nest(data_full = c(-fips_code_lz))

df_gop_future_data <-df_ext_gop %>%
  filter(is.na(gop_votes)==TRUE) %>%
  tidyr::nest(data_future = c(-fips_code_lz))



#Join data all together ----
message('Join full and future data together in nested df...')

df_dem_nest <- inner_join(df_dem_full_data,
                          df_dem_future_data,
                          by = 'fips_code_lz')


df_gop_nest <- inner_join(df_gop_full_data,
                          df_gop_future_data,
                          by = 'fips_code_lz')

#Create training and calibration (test) data ----
message('Make 2 partitions of data (train, test)...')

df_dem_nest <- df_dem_nest %>%
  mutate(splits = map(data_full, .f = function(x) {
    time_series_split(x, assess = 4, cumulative = TRUE)
  }))

df_gop_nest <- df_gop_nest %>%
  mutate(splits = map(data_full, .f = function(x) {
    time_series_split(x, assess = 4, cumulative = TRUE)
  }))



df_dem_nest <- df_dem_nest %>%
  mutate(data_train = map(.x = data_full, .f = ~slice_head(.x, n = -4)),
         data_calib = map(.x = data_full, .f = ~slice_tail(.x, n = 4))) %>%
  relocate(data_train,.after=data_full) %>%
  relocate(data_calib,.after=data_train)


df_gop_nest <- df_gop_nest %>%
  mutate(data_train = map(.x = data_full, .f = ~slice_head(.x, n = -4)),
         data_calib = map(.x = data_full, .f = ~slice_tail(.x, n = 4))) %>%
  relocate(data_train,.after=data_full) %>%
  relocate(data_calib,.after=data_train)

#Recipes ----
message('Define recipes (ie: model params)...')

rec_dem_list <- list()
rec_gop_list <- list()

num_of_dem_counties <- dim(df_dem_nest)[1]
num_of_gop_counties <- dim(df_gop_nest)[1]

for (i in 1:num_of_dem_counties){
  rec_dem_list[[i]] <- recipe(dem_votes ~ ., data = df_dem_nest$data_train[[i]])
}


for (i in 1:num_of_gop_counties){
  rec_gop_list[[i]] <- recipe(gop_votes ~ ., data = df_gop_nest$data_train[[i]])
}

#Workflows ----
message('Assign recipes to workflow...')


#replace lists with dataframes
wfl_arima <- workflow() %>%
  add_model(
    arima_reg() %>%
      set_engine(engine='auto_arima')
  )

wfl_dem_list <-list()
wfl_gop_list <-list()

for (i in 1:num_of_dem_counties){
  wfl_dem_list[[i]] <- wfl_arima %>%
    add_recipe(rec_dem_list[[i]])# %>%
    #add_case_weights(case_wts)
}

for (i in 1:num_of_gop_counties){
    wfl_gop_list[[i]] <- wfl_arima %>%
      add_recipe(rec_gop_list[[i]])# %>%
      #add_case_weights(case_wts)
  
}

message('Assign workflows to groups in nested df...')

df_dem_nest$.wfl <- vector('list', nrow(df_dem_nest))
for(i in 1:num_of_dem_counties){
  df_dem_nest$.wfl[i] <- list(wfl_dem_list[[i]])
} 


df_gop_nest$.wfl <- vector('list', nrow(df_gop_nest))
for(i in 1:num_of_gop_counties){
  df_gop_nest$.wfl[i] <- list(wfl_gop_list[[i]])
} 

#Fit models
message('Fit workflows using training data...')

df_dem_nest <- df_dem_nest %>%
  mutate(.fit = map2(.x = .wfl,
                     .y = data_train,
                     .f = ~fit(.x, .y)))

df_gop_nest <- df_gop_nest %>%
  mutate(.fit = map2(.x = .wfl,
                     .y = data_train,
                     .f = ~fit(.x, .y)))


#Calibrate models
message('Calibrate models using test data...')

df_dem_nest <- df_dem_nest %>%
  mutate(.calib = future_map2(.x = .fit,
                              .y = data_calib,
                              .f = ~modeltime_calibrate(modeltime_table(.x),new_data=.y),
                              .options = furrr_options(packages = c("timetk","purrr"))))

df_gop_nest <- df_gop_nest %>%
  mutate(.calib = future_map2(.x = .fit,
                              .y = data_calib,
                              .f = ~modeltime_calibrate(modeltime_table(.x),new_data=.y),
                              .options = furrr_options(packages = c("timetk","purrr"))))



#Refit models
message('Refit models using all data...')

df_dem_nest <- df_dem_nest %>%
  mutate(.refit = future_map2(.x = .calib,
                              .y = data_full,
                              .f = ~modeltime_refit(.x,data=.y)))


df_gop_nest <- df_gop_nest %>%
  mutate(.refit = future_map2(.x = .calib,
                              .y = data_full,
                              .f = ~modeltime_refit(.x,data=.y)))



#Generate forecasts
message('Generate forecasts...')

df_dem_nest <- df_dem_nest %>%
  mutate(.fc = future_pmap(.l = list(.refit,data_future,data_full),
                           .f = ~modeltime_forecast(
                             object = ..1,
                             new_data = ..2,
                             actual_data = ..3,
                             keep_data = FALSE
                           ),.options = furrr_options(packages = c("timetk","purrr"))
                           )
         )

df_gop_nest <- df_gop_nest %>%
  mutate(.fc = future_pmap(.l = list(.refit,data_future,data_full),
                           .f = ~modeltime_forecast(
                             object = ..1,
                             new_data = ..2,
                             actual_data = ..3,
                             keep_data = FALSE
                           ),.options = furrr_options(packages = c("timetk","purrr"))
  )
  )


message('Make predictions dataset by pulling out forecasts...')
dem_preds_list <-list()
gop_preds_list <-list()

#Make a predictions dataset
for (i in 1:num_of_dem_counties){
  dem_preds_list[[i]] <- df_dem_nest[[11]][[i]] %>%
    filter(.key == "prediction") %>%
    mutate(year = .index,
           dem_votes = .value) %>%
    select(year,dem_votes)
}



for (i in 1:num_of_gop_counties){
  gop_preds_list[[i]] <- df_gop_nest[[11]][[i]] %>%
    filter(.key == "prediction") %>%
    mutate(year = .index,
           gop_votes = .value) %>%
    select(year,gop_votes)
}


#Pull out element pieces and put into dataframe
dem_preds_df <- cbind(df_dem_nest$fips_code_lz, 
                  do.call(rbind.data.frame,dem_preds_list)) %>%
  rename("fips_code_lz" = "df_dem_nest$fips_code_lz")

gop_preds_df <- cbind(df_gop_nest$fips_code_lz, 
                      do.call(rbind.data.frame,gop_preds_list)) %>%
  rename("fips_code_lz" = "df_gop_nest$fips_code_lz")

message('Put forecasts together in one df...')

preds_df <-inner_join(dem_preds_df,
                      gop_preds_df,
                      by = c('fips_code_lz','year'))


message('Match up original data and predictions dataset for stacking')

#Join predictions back on to original dataset
df <- df %>%
  select(c(-'Lat',-'Lon',-'AvgLat',-'AvgLon'))

df_labels <- df %>%
  select(fips_code_lz,state_name,county_name) %>%
  distinct()


preds_df <- inner_join(preds_df,
                       df_labels,
                       by = 'fips_code_lz')



preds_df <- preds_df %>%
  mutate(fips_code = NA,
         gop_dem_total = NA,
         margin = NA,
         per_gop = NA,
         per_dem = NA,
         perc_margin = NA,
         gop_demperc = NA,
         Dem_EV = NA,
         Rep_EV = NA) %>%
  relocate(gop_votes, .after = county_name) %>%
  relocate(dem_votes, .after = gop_votes) %>%
  relocate(year, .before = margin) %>%
  relocate(fips_code_lz, .before = Dem_EV)
  
#Stack datasets

df <- bind_rows(
  df,
  preds_df
)

#Rearrange by fips_code_lz and year
df <- df %>%
  arrange(fips_code_lz, year)

message('Fixing all the NAs...')
#Fix all the NAs 

df <- df %>%
  select(c(-fips_code)) %>%
  mutate(gop_dem_total = if_else(is.na(gop_dem_total)==TRUE,dem_votes + gop_votes,gop_dem_total)) %>%
  mutate(margin = if_else(is.na(margin)==TRUE, abs(dem_votes - gop_votes),margin)) %>%
  mutate(per_gop = if_else(is.na(per_gop)==TRUE, (gop_votes / (gop_votes+dem_votes)), per_gop)) %>%
  mutate(per_dem = if_else(is.na(per_dem)==TRUE, (dem_votes / (dem_votes+gop_votes)), per_dem)) %>%
  mutate(perc_margin = if_else(is.na(perc_margin)==TRUE,abs(per_dem - per_gop),perc_margin)) %>%
  mutate(gop_demperc = if_else(is.na(gop_demperc)==TRUE, 1, gop_demperc))


message('Sum up all the votes by state...')

sum_votes <- df %>%
  filter(year == '2024-01-01') %>%
  group_by(state_name) %>%
  summarise(sum_dem_votes = sum(dem_votes),
            sum_gop_votes = sum(gop_votes)) %>%
  mutate(dem_winner = if_else(sum_dem_votes > sum_gop_votes,1,0),
         gop_winner = if_else(sum_gop_votes > sum_dem_votes,1,0),
         margin = abs(sum_dem_votes - sum_gop_votes),
         EV = case_when(state_name=="Alabama"~9,
                        state_name=="Alaska"~3,
                        state_name=="Arizona"~11,
                        state_name=="Arkansas"~6,
                        state_name=="California"~54,
                        state_name=="Colorado"~10,
                        state_name=="Connecticut"~7,
                        state_name=="Delaware"~3,
                        state_name=="District of Columbia"~3,
                        state_name=="Florida"~30,
                        state_name=="Georgia"~16,
                        state_name=="Hawaii"~4,
                        state_name=="Idaho"~4,
                        state_name=="Illinois"~19,
                        state_name=="Indiana"~11,
                        state_name=="Iowa"~6,
                        state_name=="Kansas"~6,
                        state_name=="Kentucky"~8,
                        state_name=="Louisiana"~8,
                        state_name=="Maine"~4,
                        state_name=="Maryland"~10,
                        state_name=="Massachusetts"~11,
                        state_name=="Michigan"~15,
                        state_name=="Minnesota"~10,
                        state_name=="Mississippi"~6,
                        state_name=="Missouri"~10,
                        state_name=="Montana"~4,
                        state_name=="Nebraska"~5,
                        state_name=="Nevada"~6,
                        state_name=="New Hampshire"~4,
                        state_name=="New Jersey"~14,
                        state_name=="New Mexico"~5,
                        state_name=="New York"~28,
                        state_name=="North Carolina"~16,
                        state_name=="North Dakota"~3,
                        state_name=="Ohio"~17,
                        state_name=="Oklahoma"~7,
                        state_name=="Oregon"~8,
                        state_name=="Pennsylvania"~19,
                        state_name=="Rhode Island"~4,
                        state_name=="South Carolina"~9,
                        state_name=="South Dakota"~3,
                        state_name=="Tennessee"~11,
                        state_name=="Texas"~40,
                        state_name=="Utah"~6,
                        state_name=="Vermont"~3,
                        state_name=="Virginia"~13,
                        state_name=="Washington"~12,
                        state_name=="West Virginia"~4,
                        state_name=="Wisconsin"~10,
                        state_name=="Wyoming"~3)) %>%
  filter(is.na(state_name)==FALSE)
  


dem_states <- sum_votes %>%
  select(state_name,dem_winner,EV,margin) %>%
  filter(dem_winner == 1)

gop_states <- sum_votes %>%
  select(state_name,gop_winner,EV,margin) %>%
  filter(gop_winner == 1)
  

message('Determine the winner...')

dem_ev <- sum(dem_states$EV)
gop_ev <- sum(gop_states$EV)


if (dem_ev > gop_ev){
  message(sprintf('The Democratic candidate wins the 2024 US Presidential election with %s electoral votes.',dem_ev))
} else {
  message(sprintf('The Republican candidate wins the 2024 US Presidential election with %s electoral votes.',gop_ev))
}