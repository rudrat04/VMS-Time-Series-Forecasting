import streamlit as st
import pandas as pd
import numpy as np
from warnings import filterwarnings
from PIL import Image
from io import BytesIO
filterwarnings("ignore")



from prophet import Prophet
from prophet.plot import add_changepoints_to_plot
from prophet.diagnostics import cross_validation
from prophet.diagnostics import performance_metrics
from prophet.plot import plot_cross_validation_metric
from prophet.diagnostics import performance_metrics
import json
from prophet.serialize import model_to_json, model_from_json
import holidays
import plotly.express as px
import altair as alt
import plotly as plt
import plotly.offline as pyoff
import plotly.graph_objs as go
import plotly.figure_factory as ff
import plotly.io as pio
import base64
import itertools
from datetime import datetime
from dateutil import parser
import json

st.set_page_config(page_title =" VMS Time Series Forecasting",
                    initial_sidebar_state="collapsed",
                    page_icon="🔮")


tabs = ["Application","About"]
page = st.sidebar.radio("Tabs",tabs)


@st.cache(persist=False,
          allow_output_mutation=True,
          suppress_st_warning=True,
          show_spinner= True)
def load_csv():
    
    df_input = pd.DataFrame()  
    df_input=pd.read_csv(input,sep=None ,engine='python', encoding='utf-8',
                            parse_dates=True,
                            infer_datetime_format=True)
    return df_input

def prep_data(df):

    df_input = df.rename({date_col:"ds",metric_col:"y"},errors='raise',axis=1)
    st.markdown("The selected date column is now labeled as **ds** and the values columns as **y**")
    df_input = df_input[['ds','y']]
    df_input =  df_input.sort_values(by='ds',ascending=True)
    return df_input

code1 = """                       
st.dataframe(df)
                       
st.write(df.describe())

try:
    line_chart = alt.Chart(df).mark_line().encode(
    x = 'ds:T',
    y = "y:Q").properties(title="Time series preview").interactive()
        st.altair_chart(line_chart,use_container_width=True)
except:
    st.line_chart(df['y'],use_container_width =True,height = 300) """ 
code2="""
 m = Prophet(
    seasonality_mode=seasonality,
    daily_seasonality=daily,
    weekly_seasonality=weekly,
    yearly_seasonality=yearly,
    growth=growth,
    changepoint_prior_scale=changepoint_scale,
    seasonality_prior_scale= seasonality_scale)
if holidays:
    m.add_country_holidays(country_name=selected_country)
                        
if monthly:
    m.add_seasonality(name='monthly', period=30.4375, fourier_order=5)

m = m.fit(df)
future = m.make_future_dataframe(periods=periods_input,freq='D')
future['cap']=cap
future['floor']=floor
                """

code3 = """
try:     
    df_cv = cross_validation(m, initial=initial,
        period=period, 
        horizon = horizon,
        parallel="processes")
except:
    df_cv = cross_validation(m, initial=initial,
        period=period, 
        horizon = horizon,
        parallel="threads")
except:
    st.write("Invalid configuration")    
    df_p = performance_metrics(df_cv)
    st.dataframe(df_p)

metrics = ['mse','rmse','mae','mape','mdape','coverage']

selected_metric = st.radio(label='Plot metric',options=metrics)
st.write(selected_metric)
fig4 = plot_cross_validation_metric(df_cv, metric=selected_metric)
st.write(fig4)
"""
code4 = """
param_grid = {  
            'changepoint_prior_scale': [0.01, 0.1, 0.5],
            'seasonality_prior_scale': [0.1, 1.0, 10.0],
             }

# Generate all combinations of parameters
all_params = [dict(zip(param_grid.keys(), v)) for v in itertools.product(*param_grid.values())]
rmses = []  # Store the RMSEs for each params here

# Use cross validation to evaluate all parameters
for params in all_params:
m = Prophet(**params).fit(df)  # Fit model with given params
df_cv = cross_validation(m, initial=initial,
                                period=period,
                                horizon=horizon,
                                parallel="processes")
df_p = performance_metrics(df_cv, rolling_window=1)
rmses.append(df_p['rmse'].values[0])

# Find the best parameters
tuning_results = pd.DataFrame(all_params)
tuning_results['rmse'] = rmses
st.write(tuning_results)

best_params = all_params[np.argmin(rmses)]
st.write('The best parameter combination is:')
st.write(f"Changepoint prior scale: ** {best_params[0]} ** ")
st.write(f"Seasonality prior scale: ** {best_params[1]} ** ")
                        """

code_options = ["Dataframe information","Model fitting","Cross validation","Hyperparam tuning"]

if page == "Application":
    
    with st.sidebar:
        if st.button(label='Clear cache'):
            st.cache_data.clear()
            # caching.clear_cache()
            

        with st.expander("Code snippets"):
            snippet = st.radio('Code snippets',options=code_options)    
            if snippet == code_options[0]:
                st.code(code1)
            if snippet == code_options[1]:
                st.code(code2)
            if snippet == code_options[2]:
                st.code(code3)
            if snippet == code_options[3]:
                st.code(code4)

    st.title('VMS Time Series Forecasting')
    st.write('This app enables you to generate time series forecast withouth any dependencies.')
    st.markdown("""The forecasting library used is **[Prophet](https://facebook.github.io/prophet/)**.""")
    st.cache_data.clear()
    df =  pd.DataFrame()   

    st.subheader('1. Data loading 🏋️')
    st.write("Import a time series csv file.")
    with st.expander("Data format"): 
        st.write("The dataset can contain multiple columns but you will need to select a column to be used as dates and a second column containing the metric you wish to forecast. The columns will be renamed as **ds** and **y** to be compliant with Prophet. Even though we are using the default Pandas date parser, the ds (datestamp) column should be of a format expected by Pandas, ideally YYYY-MM-DD for a date or YYYY-MM-DD HH:MM:SS for a timestamp. The y column must be numeric.")

    input = st.file_uploader('')
    
    if input is None:
        st.write("Or use sample dataset to try the application")
        sample = st.checkbox("Download sample data from GitHub")

    try:
        if sample:
            st.markdown("""[download_link](https://gist.github.com/giandata/e0b5c2d2e71d4fd4388295eb5b71aeeb)""")    
            
    except:

        if input:
            with st.spinner('Loading data..'):
                df = load_csv()
        
                st.write("Columns:")
                st.write(list(df.columns))
                columns = list(df.columns)
        
                col1,col2 = st.columns(2)
                with col1:
                    date_col = st.selectbox("Select date column",index= 0,options=columns,key="date")
                with col2:
                    metric_col = st.selectbox("Select values column",index=1,options=columns,key="values")

                df = prep_data(df)
                output = 0
    

        if st.checkbox('Chart data',key='show'):
            with st.spinner('Plotting data..'):
                col1,col2 = st.columns(2)
                with col1:
                    st.dataframe(df)
                    
                with col2:    
                    st.write("Dataframe description:")
                    st.write(df.describe())

            try:
                line_chart = alt.Chart(df).mark_line().encode(
                    x = 'ds:T',
                    y = "y:Q",tooltip=['ds:T', 'y']).properties(title="Time series preview").interactive()
                st.altair_chart(line_chart,use_container_width=True)
                
            except:
                st.line_chart(df['y'],use_container_width =True,height = 300)
                
            

    st.subheader("2. Parameters configuration 🛠️")

    with st.container():
        st.write('In this section you can modify the algorithm settings.')
            
        with st.expander("Horizon"):
            periods_input = st.number_input('Select how many future peris (days) to forecast.',
            min_value = 1, max_value = 366,value=90)

        with st.expander("Seasonality"):
            st.markdown("""The default seasonality used is additive, but the best choice depends on the specific case, therefore specific domain knowledge is required. For more informations visit the [documentation](https://facebook.github.io/prophet/docs/multiplicative_seasonality.html)""")
            seasonality = st.radio(label='Seasonality',options=['additive','multiplicative'])

        with st.expander("Trend components"):
            st.write("Add or remove components:")
            daily = st.checkbox("Daily")
            weekly= st.checkbox("Weekly")
            monthly = st.checkbox("Monthly")
            yearly = st.checkbox("Yearly")

        with st.expander("Growth model"):
            st.write('Prophet uses by default a linear growth model.')
            st.markdown("""For more information check the [documentation](https://facebook.github.io/prophet/docs/saturating_forecasts.html#forecasting-growth)""")

            growth = st.radio(label='Growth model',options=['linear',"logistic"]) 

            if growth == 'linear':
                growth_settings= {
                            'cap':1,
                            'floor':0
                        }
                cap=1
                floor=1
                df['cap']=1
                df['floor']=0

            if growth == 'logistic':
                st.info('Configure saturation')

                cap = st.slider('Cap',min_value=0.0,max_value=1.0,step=0.05)
                floor = st.slider('Floor',min_value=0.0,max_value=1.0,step=0.05)
                if floor > cap:
                    st.error('Invalid settings. Cap must be higher then floor.')
                    growth_settings={}

                if floor == cap:
                    st.warning('Cap must be higher than floor')
                else:
                    growth_settings = {
                        'cap':cap,
                        'floor':floor
                        }
                    df['cap']=cap
                    df['floor']=floor
            
            
        with st.expander('Holidays'):
            def extract_year_from_datetime_column(datetime_column):
                """
                Extracts the year from each date in a datetime column.

                Args:
                - datetime_column: A list or array-like object containing datetime strings.

                Returns:
                - A list containing the extracted years.
                """
                years = set()
                for date_str in datetime_column:
                    parsed_date = parser.parse(date_str)
                    years.add(parsed_date.year)
                return list(years)
            
            countries = ['Country name','India','France','Germany','Ukraine']
            
            with st.container():
                years = extract_year_from_datetime_column(df.iloc[:, 0])
                selected_country = st.selectbox(label="Select country",options=countries)

                if selected_country == 'India':
                    for date, name in sorted(holidays.IN(years=years).items()):
                        st.write(date,name)                           
                            
                if selected_country == 'France':
                    
                    for date, name in sorted(holidays.FR(years=years).items()):
                            st.write(date,name)
                            
                if selected_country == 'Germany':
                    
                    for date, name in sorted(holidays.DE(years=years).items()):
                            st.write(date,name)
                            
                if selected_country == 'Ukraine':
                    
                    for date, name in sorted(holidays.UKR(years=years).items()):
                            st.write(date,name)

                else:
                    holidays = False
                            
                holidays = st.checkbox('Add country holidays to the model')

        with st.expander('Hyperparameters'):
            st.write('In this section it is possible to tune the scaling coefficients.')
            
            seasonality_scale_values= [0.1, 1.0,5.0,10.0]    
            changepoint_scale_values= [0.01, 0.1, 0.5,1.0]

            st.write("The changepoint prior scale determines the flexibility of the trend, and in particular how much the trend changes at the trend changepoints.")
            changepoint_scale= st.select_slider(label= 'Changepoint prior scale',options=changepoint_scale_values)
            
            st.write("The seasonality change point controls the flexibility of the seasonality.")
            seasonality_scale= st.select_slider(label= 'Seasonality prior scale',options=seasonality_scale_values)    

            st.markdown("""For more information read the [documentation](https://facebook.github.io/prophet/docs/diagnostics.html#parallelizing-cross-validation)""")

    with st.container():
        st.subheader("3. Forecast 🔮")
        st.write("Fit the model on the data and generate future prediction.")
        st.write("Load a time series to activate.")
        
        if input:
            
            if st.checkbox("Initialize model (Fit)",key="fit"):
                if len(growth_settings)==2:
                    m = Prophet(seasonality_mode=seasonality,
                                daily_seasonality=daily,
                                weekly_seasonality=weekly,
                                yearly_seasonality=yearly,
                                growth=growth,
                                changepoint_prior_scale=changepoint_scale,
                                seasonality_prior_scale= seasonality_scale)
                    if holidays:
                        m.add_country_holidays(country_name=selected_country)
                        
                    if monthly:
                        m.add_seasonality(name='monthly', period=30.4375, fourier_order=5)

                    with st.spinner('Fitting the model..'):

                        m = m.fit(df)
                        future = m.make_future_dataframe(periods=periods_input,freq='D')
                        future['cap']=cap
                        future['floor']=floor
                        st.write("The model will produce forecast up to ", future['ds'].max())
                        st.success('Model fitted successfully')

                else:
                    st.warning('Invalid configuration')

            if st.checkbox("Generate forecast (Predict)",key="predict"):
                try:
                    with st.spinner("Forecasting.."):

                        forecast = m.predict(future).tail(periods_input)
                        st.success('Prediction generated successfully')
                        st.dataframe(forecast)
                        fig1 = m.plot(forecast)
                        st.write(fig1)
                        def save_plot_to_bytes(fig):
                            img_bytes = BytesIO()
                            fig.savefig(img_bytes, format='png')
                            img_bytes.seek(0)
                            return img_bytes

                        img_bytes = save_plot_to_bytes(fig1)

                        def get_download_link(img_bytes, filename, text):
                            encoded = base64.b64encode(img_bytes.read()).decode()
                            href = f'<a href="data:image/png;base64,{encoded}" download="{filename}">{text}</a>'
                            return href
                        
                
                        
                        if st.button('Download Plot'):
                            st.markdown(get_download_link(img_bytes, 'forecast_plot.png', 'Click here to download'), unsafe_allow_html=True)
                        output = 1 

                        if growth == 'linear':
                            fig2 = m.plot(forecast)
                            a = add_changepoints_to_plot(fig2.gca(), m, forecast)
                            st.write(fig2)
                            def save_plot_to_bytes(fig):
                                img_bytes = BytesIO()
                                fig.savefig(img_bytes, format='png')
                                img_bytes.seek(0)
                                return img_bytes

                        img_bytes_2 = save_plot_to_bytes(fig2)
                        
                        def get_download_link(img_bytes, filename, text):
                            encoded = base64.b64encode(img_bytes.read()).decode()
                            href = f'<a href="data:image/png;base64,{encoded}" download="{filename}">{text}</a>'
                            return href
                        if st.button('Download Linear Graph'):
                            
                            st.markdown(get_download_link(img_bytes_2, 'lineargraph.png', 'Click here to download'), unsafe_allow_html=True)
                            output = 1
                except:
                    st.warning("You need to train the model first.. ")
                        
            
            if st.checkbox('Show components'):
                try:
                    with st.spinner("Loading.."):
                        fig3 = m.plot_components(forecast)
                        st.write(fig3)
                        def save_plot_to_bytes(fig):
                            img_bytes = BytesIO()
                            fig.savefig(img_bytes, format='png')
                            img_bytes.seek(0)
                            return img_bytes

                        img_bytes_1 = save_plot_to_bytes(fig3)
                        
                        def get_download_link(img_bytes, filename, text):
                            encoded = base64.b64encode(img_bytes.read()).decode()
                            href = f'<a href="data:image/png;base64,{encoded}" download="{filename}">{text}</a>'
                            return href
                        if st.button('Download Component Plot'):
                            
                            st.markdown(get_download_link(img_bytes_1, 'components.png', 'Click here to download'), unsafe_allow_html=True)
                except: 
                    st.warning("Requires forecast generation..") 
        
        st.subheader('4. Model validation 🧪')
        st.write("In this section it is possible to do cross-validation of the model.")
        with st.expander("Explanation"):
            st.markdown("""The Prophet library makes it possible to divide our historical data into training data and testing data for cross validation. The main concepts for cross validation with Prophet are:""")
            st.write("Training data (initial): The amount of data set aside for training. The parameter is in the API called initial.")
            st.write("Horizon: The data set aside for validation.")
            st.write("Cutoff (period): a forecast is made for every observed point between cutoff and cutoff + horizon.""")

            
        with st.expander("Cross validation"):    
            initial = st.number_input(value= 365,label="initial",min_value=30,max_value=1096)
            initial = str(initial) + " days"

            period = st.number_input(value= 90,label="period",min_value=1,max_value=365)
            period = str(period) + " days"

            horizon = st.number_input(value= 90, label="horizon",min_value=30,max_value=366)
            horizon = str(horizon) + " days"

            st.write(f"Here we do cross-validation to assess prediction performance on a horizon of **{horizon}** days, starting with **{initial}** days of training data in the first cutoff and then making predictions every **{period}**.")
            st.markdown("""For more information read the [documentation](https://facebook.github.io/prophet/docs/diagnostics.html#parallelizing-cross-validation)""")
        
     
        with st.expander("Metrics"):
            
            if input:
                if output == 1:
                    metrics = 0
                    if st.checkbox('Calculate metrics'):
                        with st.spinner("Cross validating.."):
                            try:
                                df_cv = cross_validation(m, initial=initial,
                                                        period=period, 
                                                        horizon = horizon,
                                                        parallel="processes")                                        
                            
                            
                            
                                df_p = df_cv.describe(percentiles=[0.1, 0.25, 0.5, 0.75, 0.9])
                                for col in df_p.columns:
                                    if df_p[col].dtype == 'timedelta64[ns]':
                                        df_p[col] = df_p[col].dt.total_seconds().astype(str)
                                metrics=1
                            except:
                                st.write("Invalid configuration. Try other parameters.")
                                metrics = 0


                            st.markdown('**Metrics definition**')
                            st.write("Mse: mean absolute error")
                            st.write("Rmse: Root mean absolute error")
                            st.write("Mae: Mean average error")
                            

                            if metrics == 1:

                                metrics = ['Choose a metric','mse','rmse','mae']
                                selected_metric = st.selectbox("Select metric to plot",options=metrics)
                                if selected_metric != metrics[0]:
                                    fig4 = plot_cross_validation_metric(df_cv, metric=selected_metric)
                                    st.write(fig4)
                                    def save_plot_to_bytes(fig):
                                        img_bytes = BytesIO()
                                        fig.savefig(img_bytes, format='png')
                                        img_bytes.seek(0)
                                        return img_bytes

                                    img_bytes_4 = save_plot_to_bytes(fig4)
                        
                                    def get_download_link(img_bytes, filename, text):
                                        encoded = base64.b64encode(img_bytes.read()).decode()
                                        href = f'<a href="data:image/png;base64,{encoded}" download="{filename}">{text}</a>'
                                        return href
                                    if st.button('Download Metric Graph'):
                                        st.markdown(get_download_link(img_bytes_4, 'metricgraph.png', 'Click here to download'), unsafe_allow_html=True)
                                        output = 1
                                    
                        
            else:
                st.write("Create a forecast to see metrics")
                            

        st.subheader('5. Hyperparameter Tuning 🧲')
        st.write("In this section it is possible to find the best combination of hyperparamenters.")
        st.markdown("""For more informations visit the [documentation](https://facebook.github.io/prophet/docs/diagnostics.html#hyperparameter-tuning)""")

        param_grid = {  
                            'changepoint_prior_scale': [0.01, 0.1, 0.5, 1.0],
                            'seasonality_prior_scale': [0.1, 1.0, 5.0, 10.0],
                        }

        # Generate all combinations of parameters
        all_params = [dict(zip(param_grid.keys(), v)) for v in itertools.product(*param_grid.values())]
        rmses = []  # Store the RMSEs for each params here

        if input:
            if output == 1:

                if st.button("Optimize hyperparameters"):
                    
                    with st.spinner("Finding best combination. Please wait.."):

                        
                        try:
                        # Use cross validation to evaluate all parameters
                            for params in all_params:
                                m = Prophet(**params).fit(df)  # Fit model with given params
                                df_cv = cross_validation(m, initial=initial,
                                                                period=period,
                                                                horizon=horizon,
                                                                parallel="processes")
                                df_p = performance_metrics(df_cv, rolling_window=1)
                                rmses.append(df_p['rmse'].values[0])
                        except:
                            for params in all_params:
                                m = Prophet(**params).fit(df)  # Fit model with given params
                                df_cv = cross_validation(m, initial=initial,
                                                                period=period,
                                                                horizon=horizon,
                                                                parallel="threads")
                                df_p = performance_metrics(df_cv, rolling_window=1)
                                rmses.append(df_p['rmse'].values[0])

                    # Find the best parameters
                    tuning_results = pd.DataFrame(all_params)
                    tuning_results['rmse'] = rmses
                    st.write(tuning_results)
                            
                    best_params = all_params[np.argmin(rmses)]
                    
                    st.write('The best parameter combination is:')
                    st.write(best_params)
                    #st.write(f"Changepoint prior scale:  {best_params[0]} ")
                    #st.write(f"Seasonality prior scale: {best_params[1]}  ")
                    st.write(" You may repeat the process using these parameters in the configuration section 2")
                    

            else:
                st.write("Create a model to optimize")    

        st.subheader('6. Export results ✨')
        
        st.write("Finally you can export your result forecast, model configuration and evaluation metrics.")
        
        if input:
            if output == 1:
                col1, col2, col3 = st.columns(3)

                with col1:
                    
                    if st.button('Export forecast (.csv)'):
                        with st.spinner("Exporting.."):

                            #export_forecast = pd.DataFrame(forecast[['ds','yhat_lower','yhat','yhat_upper']]).to_csv()
                            export_forecast = pd.DataFrame(forecast[['ds','yhat_lower','yhat','yhat_upper']])
                            st.write(export_forecast.head())
                            export_forecast= export_forecast.to_csv(decimal=',')
                            b64 = base64.b64encode(export_forecast.encode()).decode()
                            href = f'<a href="data:file/csv;base64,{b64}" download="export_forecast.csv">Download CSV file</a>'
                            
                        
                            st.markdown(href, unsafe_allow_html=True)
            

                with col2:
                    if st.button('Save model configuration (.json) in memory'):
                        with open('serialized_model.json', 'w') as fout:
                            json.dump(model_to_json(m), fout)
                            
                    

                with col3:
                    if st.button('Clear cache memory please'):
                        st.cache_data.clear()

            else:
                st.write("Generate a forecast to download.")
            

if page == "About":
    st.image("prophet.png")
    st.header("About")
    st.markdown("Official documentation of **[Facebook Prophet](https://facebook.github.io/prophet/)**")
    st.markdown("Official documentation of **[Streamlit](https://docs.streamlit.io/en/stable/getting_started.html)**")
    st.write("")
    st.write("Author:")
    st.markdown(""" **[Giancarlo Di Donato](https://www.linkedin.com/in/giancarlodidonato/)**""")
    st.markdown("""**[Source code](https://github.com/giandata/forecast-app)**""")

    st.write("Created on 27/02/2021")
    st.write("Last updated: **29/04/2021**")
