import streamlit as st
import pandas as pd
import plotly.express as px 
import plotly.graph_objects as go
import numpy as np
from datetime import datetime

### Config
st.set_page_config(
    page_title="Getaround Analysis",
    page_icon="🚗",
    layout="wide"
)

DATA_URL_DELAY = ('https://full-stack-assets.s3.eu-west-3.amazonaws.com/Deployment/get_around_delay_analysis.xlsx')
DATA_URL_PRICING = ('https://full-stack-assets.s3.eu-west-3.amazonaws.com/Deployment/get_around_pricing_project.csv')

### App
st.title("Streamlit dashboard to analyse a minimum delay to be implemented between two Getaround rentals")

st.markdown("""
    Welcome to this awesome `Streamlit` dashboard. Il will allow you to decide which minimum delay to implement
    between two rentals, with figures to help you make an educated decision.
""")

today = datetime.now().strftime("%d/%m/%Y")
st.caption(f"App last run on **{today}**")

st.markdown("---")


@st.cache_data
def load_data():
    try:
        delay = pd.read_excel(DATA_URL_DELAY)
        pricing = pd.read_csv(DATA_URL_PRICING)
        return delay, pricing
    except Exception as e:
        st.error(f"{e}")
        return None

st.subheader("Load and showcase data")

data_load_state = st.text('Loading data...')
delay, pricing = load_data()

# Creating the temporary dataframes for the figures
delay_prevRent = delay[pd.notna(delay["previous_ended_rental_id"])].copy().reset_index(drop=True)
delay_prevRent['previous_ended_rental_id'] = [int(x) for x in delay_prevRent['previous_ended_rental_id']]
delay_prevRent['previous_delay_at_checkout'] = [
    delay[delay['rental_id'] == prev_car].delay_at_checkout_in_minutes.values[0]
    for prev_car in delay_prevRent['previous_ended_rental_id']]

delay_prevRent_woNaN = delay_prevRent[pd.notna(delay_prevRent["previous_delay_at_checkout"])].copy().reset_index(drop=True)
delay_prevRent_woNaN['timedelta_minus_delay'] = delay_prevRent_woNaN['time_delta_with_previous_rental_in_minutes'] \
                                                - delay_prevRent_woNaN['previous_delay_at_checkout']

delay_prevRent_woNaN_previousdelay = delay_prevRent[pd.notna(delay_prevRent["previous_delay_at_checkout"])].copy().reset_index(drop=True)
delay_prevRent_woNaN_previousdelay['type_of_delay'] = delay_prevRent_woNaN_previousdelay['previous_delay_at_checkout'].apply(lambda x: 'in_advance' if x<=0 else 
    'late'
)

data_load_state.text("") 

## Run the below code if the check is checked ✅
if st.checkbox('Show raw data'):
    st.markdown('Raw data: delay')
    st.write(delay)    

st.markdown("---")

## charts to choose the threshold and type of checkin
st.subheader("Choose your threshold and type of checkin")
st.markdown("""
    Here are 5 figures to let you choose:
    
    - the threshold you may fix as a minimum between two rentals, to limit the cases where the next driver 
            cancels its rental because the previous person is late with the car
            
    - the type of checkin on which to apply this threshold: either connect, mobile or both
""")

## Question 1
st.markdown("Question 1: How often are drivers late for the next check-in? How does it impact the next driver?")
col1, col2 = st.columns(2)
with col1:
    df_pie = pd.DataFrame(delay_prevRent_woNaN_previousdelay['type_of_delay'].value_counts())
    fig = px.pie(df_pie, values=df_pie['count'], names=df_pie.index, color=df_pie.index, 
             color_discrete_map={'late': 'red', 'in_advance': 'green'}, 
             title="Percentage of drivers late versus in advance")
    st.plotly_chart(fig, use_container_width=True)
with col2:
    fig = px.histogram(delay_prevRent_woNaN_previousdelay, 'state', pattern_shape='checkin_type', 
             color='type_of_delay', text_auto=True,
             title='Impact of all types of arrival and checkin on the next driver')
    st.plotly_chart(fig, use_container_width=True)

## Choice of threshold and type of checkin
st.markdown("Empirical Cumulative Distribution Functions to choose a threshold and type of checkin:")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("type of checkin: both")
    fig = px.ecdf(delay_prevRent_woNaN, color='state', x='timedelta_minus_delay', 
              title="ECDF for both checkin types")
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.markdown("type of checkin: mobile")
    fig = px.ecdf(delay_prevRent_woNaN.loc[delay_prevRent_woNaN['checkin_type']=='mobile',:], 
              color='state', x='timedelta_minus_delay', title='ECDF for checkin_type mobile')
    st.plotly_chart(fig, use_container_width=True)

with col3:
    st.markdown("type of checkin: connect")
    fig = px.ecdf(delay_prevRent_woNaN.loc[delay_prevRent_woNaN['checkin_type']=='connect',:], 
              color='state', x='timedelta_minus_delay', title='ECDF for checkin_type connect')
    st.plotly_chart(fig, use_container_width=True)

threshold = st.selectbox("Select the threshold (in minutes) you want to try out", range(0,720))
checkin_type = st.selectbox("Select the type of checkin you want to apply this threshold to", ['connect', 'mobile', 'both'])
delay_prevRent_woNaN_previousdelay['threshold'] = delay_prevRent_woNaN_previousdelay['time_delta_with_previous_rental_in_minutes']\
                .apply(lambda x: 'below_threshold' if x<=threshold else 'above_threshold')

st.markdown("---")

## charts to see the effects of both parameters (threshold & checkin) on the rentals 
st.subheader("Effects of both chosen parameters on the rentals") 
st.markdown("""
    You can see here the answers to your questions, according to the threshold & checkin type you chose:              
""")

## Question 2
st.markdown("Question 2: How many rentals would be affected by the feature depending on the threshold and scope we choose?")
if checkin_type == 'both':
    delay_question2 = delay.copy()
else:
    delay_question2 = delay.loc[delay['checkin_type']==checkin_type, :].copy()
delay_question2['threshold'] = delay_question2['time_delta_with_previous_rental_in_minutes']\
    .apply(lambda x: 'below_threshold' if x<=threshold else 
            'above_threshold')
fig = px.pie(delay_question2['threshold'].value_counts(), values='count', 
             names=delay_question2['threshold'].value_counts().index, 
             color=delay_question2['threshold'].value_counts().index, 
             color_discrete_map={'below_threshold': 'red', 'above_threshold': 'green'}, 
             title="Percentage of checkin_type rentals below or above the chosen threshold")
st.plotly_chart(fig, use_container_width=True)

value_metric_question2 = round(delay_question2['threshold'].value_counts()['below_threshold']/delay.shape[0]*100, ndigits=2)
st.metric(label="Percentage of all rentals potentially lost with your selected parameters", value=value_metric_question2)

## Question 3
st.markdown("Question 3: How many problematic cases will it solve depending on the chosen threshold and scope?")
if checkin_type == 'both':
    delay_question3 = delay_prevRent_woNaN_previousdelay.loc[delay_prevRent_woNaN_previousdelay['type_of_delay']=='late', :]
else:
    delay_question3 = delay_prevRent_woNaN_previousdelay.loc[delay_prevRent_woNaN_previousdelay['type_of_delay']=='late', :]\
    .loc[delay_prevRent_woNaN_previousdelay['checkin_type']==checkin_type, :]

fig = px.histogram(delay_question3, 
             'state', pattern_shape='checkin_type', color='threshold', text_auto=True,  
             title='Impact of late arrivals on the next driver')
st.plotly_chart(fig, use_container_width=True)

df_groupby = delay_question3.groupby(['state', 'threshold'], as_index=False).size()
df = df_groupby.loc[df_groupby['state']=='canceled',:]
number_solved = df.loc[df['threshold']=='below_threshold', 'size'].values[0]
total_number = delay_question3.groupby('state').count().loc['canceled', 'threshold']
value_metric_question3 = round(number_solved/total_number*100, ndigits=2)
st.metric(label="Percentage of problematic cases potentially solved with your selected parameters", value=value_metric_question3)

## Question 4
st.markdown("Question 4: Which share of our owner’s revenue would potentially be affected by the feature?")
fig = px.histogram(pricing, 'rental_price_per_day', color='has_getaround_connect', 
                   title="Current rental prices (dashed lines: mean per category)")
fig.add_vline(x=np.mean(pricing.loc[pricing['has_getaround_connect']==False, 
                                    'rental_price_per_day']), line_dash = 'dash', line_color = 'blue')
fig.add_vline(x=np.mean(pricing.loc[pricing['has_getaround_connect']==True, 
                                    'rental_price_per_day']), line_dash = 'dash', line_color = 'lightblue')
st.plotly_chart(fig, use_container_width=True)

current_prices = sum(pricing['rental_price_per_day'])
if checkin_type == 'both':
    percentage_affected = 1 - delay_question2['threshold'].value_counts()['below_threshold']/delay.shape[0]
    shape = pricing.shape[0]
    to_be_sampled = int(round(percentage_affected*shape, 0))
    pricing_affected = pricing.sample(to_be_sampled, random_state=10)
    mean_price_woFeature = np.mean(pricing['rental_price_per_day'])
    mean_price_withFeature = np.mean(pricing_affected['rental_price_per_day'])
    price_affected = mean_price_woFeature - mean_price_withFeature
    total_rentals = delay_prevRent_woNaN_previousdelay.shape[0]
    total_late = delay_prevRent_woNaN_previousdelay.loc[delay_prevRent_woNaN_previousdelay['threshold']=='below_threshold', :].shape[0]
    rentals_affected = total_late / total_rentals
    affected_prices = sum(pricing['rental_price_per_day'])* (1-rentals_affected)*(1-price_affected) + \
                  sum(pricing['rental_price_per_day'])*rentals_affected 
elif checkin_type == 'connect':
    percentage_affected = 1 - delay_question2['threshold'].value_counts()['below_threshold']/delay_question2.shape[0]
    shape = pricing.loc[pricing['has_getaround_connect']==True, :].shape[0]
    to_be_sampled = int(round(percentage_affected*shape, 0))
    pricing_affected = pricing.loc[pricing['has_getaround_connect']==True, :].sample(to_be_sampled, random_state=10)
    mean_price_woFeature = np.mean(pricing.loc[pricing['has_getaround_connect']==True, 'rental_price_per_day'])
    mean_price_withFeature = np.mean(pricing_affected['rental_price_per_day'])
    price_affected = mean_price_woFeature - mean_price_withFeature
    total_rentals = delay_prevRent_woNaN_previousdelay.loc[delay_prevRent_woNaN_previousdelay['checkin_type']=='connect', :].shape[0]
    total_late = delay_prevRent_woNaN_previousdelay.loc[delay_prevRent_woNaN_previousdelay['threshold']=='below_threshold', :]\
        .loc[delay_prevRent_woNaN_previousdelay['checkin_type']=='connect', :].shape[0]
    rentals_affected = total_late / total_rentals
    affected_prices = sum(pricing.loc[pricing['has_getaround_connect']==True, 'rental_price_per_day'])* \
                  (1-rentals_affected)*(1-price_affected) + \
                  sum(pricing.loc[pricing['has_getaround_connect']==True, 'rental_price_per_day'])*rentals_affected + \
                  sum(pricing.loc[pricing['has_getaround_connect']==False, 'rental_price_per_day'])
else:
    percentage_affected = 1 - delay_question2['threshold'].value_counts()['below_threshold']/delay_question2.shape[0]
    shape = pricing.loc[pricing['has_getaround_connect']==False, :].shape[0]
    to_be_sampled = int(round(percentage_affected*shape, 0))
    pricing_affected = pricing.loc[pricing['has_getaround_connect']==False, :].sample(to_be_sampled, random_state=10)
    mean_price_woFeature = np.mean(pricing.loc[pricing['has_getaround_connect']==False, 'rental_price_per_day'])
    mean_price_withFeature = np.mean(pricing_affected['rental_price_per_day'])
    price_affected = mean_price_woFeature - mean_price_withFeature
    total_rentals = delay_prevRent_woNaN_previousdelay.loc[delay_prevRent_woNaN_previousdelay['checkin_type']=='mobile', :].shape[0]
    total_late = delay_prevRent_woNaN_previousdelay.loc[delay_prevRent_woNaN_previousdelay['threshold']=='below_threshold', :]\
        .loc[delay_prevRent_woNaN_previousdelay['checkin_type']=='mobile', :].shape[0]
    rentals_affected = total_late / total_rentals
    affected_prices = sum(pricing.loc[pricing['has_getaround_connect']==False, 'rental_price_per_day'])* \
                  (1-rentals_affected)*(1-price_affected) + \
                  sum(pricing.loc[pricing['has_getaround_connect']==False, 'rental_price_per_day'])*rentals_affected + \
                  sum(pricing.loc[pricing['has_getaround_connect']==True, 'rental_price_per_day'])

total_loss = current_prices - affected_prices
percent_loss = (current_prices - affected_prices)/current_prices*100
a, b = st.columns(2)
c, d = st.columns(2)
a.metric(label="perte de prix moyenne par jour (€)", value=round(price_affected, ndigits=2))
b.metric(label="pourcentage de locations affectées par cette perte de prix", value=round(rentals_affected*100, ndigits=2))
c.metric(label="La perte totale serait de (€)", value=round(total_loss, ndigits=2))
d.metric(label="Ce qui représente un pourcentage de", value=round(percent_loss, ndigits=2))


### Side bar 
st.sidebar.header("Dashboard for Getaround Analysis")
st.sidebar.markdown("""
    * [Load and showcase data](#load-and-showcase-data)
    * [Choose your threshold and type of checkin](#choose-your-threshold-and-type-of-checkin)
    * [Effects of both chosen parameters on the rentals](#effects-of-both-chosen-parameters-on-the-rentals)
""")
e = st.sidebar.empty()
e.write("")
st.sidebar.write("Made with 💖 by Eugénie")
