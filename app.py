from dash import callback_context as ctx
from dash.exceptions import PreventUpdate
from dash_extensions.enrich import DashProxy, Output, Input, State, html, dcc, dash_table, ServersideOutput, ServersideOutputTransform
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import os, pathlib
import time

app = DashProxy(__name__, transforms=[ServersideOutputTransform()], external_stylesheets=[dbc.themes.FLATLY], assets_folder='assets')
server = app.server

app.title = "UC Employee Wages Dashboard"

# define paths
APP_PATH = str(pathlib.Path(__file__).parent.resolve())

# create schemas so that you don't need to remember the labels when coding
class DataSchema:
    NAME = "Employee Name"
    JOB = "Job Title"
    JOB_ABBREVIATED = "Abbreviated Job Title"
    TOTAL_PAY = 'Total Pay'
    TOTAL_PAY_AND_BENEFITS = 'Total Pay & Benefits'
    PAY = 'Total Pay & Benefits'
    YEAR = "Year"
    PRIORPAY = "Prior Year Pay"
    ADJUSTMENT = "Adjustment"
    CUMADJUSTMENT = "Cumulative Adjustment"
    PROJECTEDPAY = "Projected Pay"

class ids:
    PROJECTED_WAGES_LINE_PLOT = "projected-wages-line-plot"
    REAL_WAGES_LINE_PLOT = "real-wages-line-plot"
    RATE_JOB_DROPDOWN = "rate-job-dropdown"
    RATE_NAME_DROPDOWN = "rate-name-dropdown"
    RATE_COLA_DROPDOWN = "rate-cola-dropdown"
    INITIAL_WAGE_DROPDOWN = "initial-wage-dropdown"
    INITIAL_WAGE_INPUT = "initial-wage-input"
    LOLLIPOP_CHART = "lollipop-chart"
    NAME_SEARCH_CONTAINER = "name-search-container"
    NAME_SEARCH_INPUT = "name-search-input"
    NAME_SEARCH_BUTTON = "name-search-button"
    NAME_SEARCH_RESULTS_CONTAINER = "name-search-results-container"
    NAME_SEARCH_RESULTS_TABLE = "name-search-results-table"
    NAME_ADD_CONTAINER = "name-add-container"
    NAME_ADDED_DROPDOWN = "name-added-dropdown"
    NAME_ADD_BUTTON = "name-add-button"
    NAME_CONTAINER = "name-container"
    YEAR_RANGE_CONTAINER = "year-range-container"
    YEAR_RANGE_SLIDER = "year-range-slider"
    INITIAL_WAGE_CONTAINER = 'initial-wage-container'

class colors:
    PLOT_BACKGROUND_COLOR = "#eaf1f5"
    END_MARKER_COLOR = "#355218"
    START_MARKER_COLOR = "#759356"
    LOLLIPOP_LINE_COLOR = "#7B7B7B"
    GRID_LINES_COLOR = "#C5CCCA"

JOB_DATA_PATH =  os.path.join(APP_PATH, "assets", "salaries_by_job.csv")
NAME_DATA_PATH =  os.path.join(APP_PATH, "assets", "salaries_by_name.parquet")

t0 = time.time()
print('reading csv 1:')

# load data
#df_jobs = pd.read_parquet(JOB_DATA_PATH, engine='fastparquet')     # need to create parquet file first
cat_type = pd.api.types.CategoricalDtype(categories=[2011,2012,2013,2014,2015,2016,2017,2018,2019,2020,2021], ordered=True)
df_jobs = pd.read_csv(JOB_DATA_PATH, 
    usecols=[
        DataSchema.NAME,
        DataSchema.TOTAL_PAY,
        DataSchema.TOTAL_PAY_AND_BENEFITS,
        DataSchema.YEAR],
    dtype={
        DataSchema.NAME: "category",
        DataSchema.TOTAL_PAY: float,
        DataSchema.TOTAL_PAY_AND_BENEFITS: float,
        DataSchema.YEAR: cat_type
    }
)
# rename the compensation column (either Total Pay or Total Pay and Benefits) to compensation
#df_jobs = df_jobs.rename(columns={compensation_type: DataSchema.PAY})
print(time.time() - t0)

t0 = time.time()
print('reading csv 2:')
df_names = pd.read_parquet(NAME_DATA_PATH, engine='fastparquet')
print(time.time() - t0)

print('size of df_names_filtered:')
print(df_names.info(memory_usage = 'deep'))

t0 = time.time()




# df_names = pd.read_csv(NAME_DATA_PATH,
#     usecols=[
#         DataSchema.NAME,
#         DataSchema.TOTAL_PAY,
#         DataSchema.TOTAL_PAY_AND_BENEFITS,
#         DataSchema.YEAR],
#     dtype={
#         DataSchema.NAME: "category",
#         DataSchema.TOTAL_PAY: "int32",
#         DataSchema.TOTAL_PAY_AND_BENEFITS: "int32",
#         DataSchema.YEAR: "category"
#     }
# )
# df_names[DataSchema.YEAR] = df_names[DataSchema.YEAR].astype(cat_type)
#df_names = df_names.rename(columns={compensation_type: DataSchema.PAY})


# t0 = time.time()
print('creating html components:')
# ------------- create html components --------------------
# better way to do this? this is faster than reading a df
unique_jobs = ['GSR (Step 1)', 'GSR (Step 2)', 'GSR (Step 3)', 'GSR (Step 4)', 'GSR (Step 5)', 'GSR (Step 6)', 'GSR (Step 7)', 'GSR (Step 8)', 'GSR (Step 9)', 'GSR (Step 10)', 'UC President']        
initial_wage_container = html.Div(
        id = ids.INITIAL_WAGE_CONTAINER,
        className = 'dropdown-container',
        children = [
            html.P('Set a starting compensation by selecting a job or entering a custom amount:'),
            dcc.Dropdown(
                id=ids.INITIAL_WAGE_DROPDOWN,
                options=unique_jobs,
                value = "GSR (Step 1)",
                placeholder="Set an starting compensation based on job or enter custom value on the right",
                multi=False,
                clearable=False
            ),
            dcc.Input(
                id=ids.INITIAL_WAGE_INPUT, 
                value = 16698, #old code: value = df_jobs.loc[(df_jobs[DataSchema.NAME]=="GSR (Step 1)") & (df_jobs[DataSchema.YEAR]==2011), DataSchema.PAY].iloc[0],
                type="number", 
                placeholder="",
                debounce=True
            ),
        ]
)

job_container = html.Div(
    className="dropdown-container",
    children = [
        html.P("Select a job to add to the plots:", id="job-label"),
        dcc.Dropdown(
            id=ids.RATE_JOB_DROPDOWN,
            options=unique_jobs,
            value=['GSR (Step 1)', 'GSR (Step 4)', 'GSR (Step 7)', 'GSR (Step 10)'],
            multi=True
        )
    ]
)

# TODO: implement cola
# cola_container = html.Div(
#     className='dropdown-container',
#     children = [
#         html.Label("Select COLA", id="cola-label"),
#         dcc.Dropdown(
#             id=ids.RATE_COLA_DROPDOWN,
#             options=["Santa Barbara", "Los Angeles", "San Francisco"],
#             value="Santa Barbara",
#             multi=False
#         )
#     ]
# )


# ------------- create year range slider components ----------------
year_range_container = html.Div(
    id = ids.YEAR_RANGE_CONTAINER,
    className='dropdown-container',
    children = [
        dcc.RangeSlider(
            min = 2011, 
            max = 2021, 
            step = 1,
            value = [2011, 2021],
            marks = {
                2011: '2011',
                2012: '2012',
                2013: '2013',
                2014: '2014',
                2015: '2015',
                2016: '2016',
                2017: '2017',
                2018: '2018',
                2019: '2019',
                2020: '2020',
                2021: '2021'
            },
            id = ids.YEAR_RANGE_SLIDER
        )
    ]
)


# ------------- create name search components ----------------
name_search_container = html.Div(
        id = ids.NAME_SEARCH_CONTAINER,
        children = [
            html.Label('Enter name:'),
            dcc.Input(id = ids.NAME_SEARCH_INPUT),
            html.Button('Search', id = ids.NAME_SEARCH_BUTTON, className='button'),
        ]
)

name_search_results_container = html.Div(
    id = ids.NAME_SEARCH_RESULTS_CONTAINER,
    children = [
        dash_table.DataTable(id = ids.NAME_SEARCH_RESULTS_TABLE),
    ]
)

name_add_container = html.Div(
    id = ids.NAME_ADD_CONTAINER,
    children = [
        html.Button('Add Selected Name', id = ids.NAME_ADD_BUTTON, className = 'button'),
        dcc.Dropdown(id = ids.NAME_ADDED_DROPDOWN,
            value = [],
            options = [],
            multi=True)
    ]
)


t0 = time.time()
print('creating layout:')

# create layout
app.layout = html.Div(
    className="app-div",
    children=[
        # data stores
        dcc.Store(id='filtered-names-data'),
        dcc.Store(id='filtered-jobs-data'),
        dcc.Store(id='filtered-combined-data'),
        dcc.Store(id='jobs-data'),
        dcc.Store(id='names-data'),
        dcc.Store(id='table-data-records-list'),
        dcc.Store(id='traces-in-real-wages'),
        dcc.Store(id='traces-in-projected-wages'),
        dcc.Store(id='schema-class'),
       
        html.Header(
            className = "title-container",
            children=[
                html.H1(app.title)
            ]
        ),

        dbc.Accordion(
            children = [
                dbc.AccordionItem(
                    children = [
                        html.P('Select one of the following options:'),
                        dcc.Dropdown(
                            options = ['Total Pay', 'Total Pay & Benefits'],
                            value = 'Total Pay & Benefits',
                            multi=False,
                            clearable = False,
                            id = 'select-compensation-dropdown'
                        ),
                        dbc.Button('Refresh Figures', id = 'refresh-figures-button', className='button'),
                    ],
                    title = 'Selected Compensation: Total Pay & Benefits',
                    id = 'compensation-accordion-item'
                ),
                dbc.AccordionItem(
                    children = [
                        initial_wage_container,
                    ],
                    title = 'Starting Compensation',
                    id = 'starting-compensation-accordion-item'
                ),
                dbc.AccordionItem(
                    children = [
                        year_range_container,
                    ],
                    title = 'Years Range',
                    id = 'years-range-accordion-item'
                ),
                dbc.AccordionItem(
                    children = [
                        job_container,
                    ],
                    title = 'Compare Jobs',
                    id = 'compare-jobs-accordion-item'
                ),
                dbc.AccordionItem(
                    children = [
                        dcc.Loading(
                                id = 'name-container',
                                children = [
                                    name_search_container,
                                    name_search_results_container,
                                    name_add_container
                                ]
                              
                        ),
                    ],
                    title = 'Compare Employees'
                )
            ],
            id = 'accordion',
            always_open = True,
            active_item = ['item-1', 'item-2', 'item-3', 'item-4']    # this needs to be string id (not assigned id)
        ),
        html.Hr(),
        html.H4('How does your compensation stack up against other UC employees?'),
        html.H6('Hover around a data point to compare the compensation of all plotted employees for that year.'),
        dcc.Graph(id=ids.REAL_WAGES_LINE_PLOT, config={'displayModeBar': False}),
        html.Hr(),
        html.H4('Ever wonder what your compensation might be if it grew at the same rate as your peers or bosses?'), 
        html.H6('This plot displays how your specified initial wage would change if you received the same year-to-year percentage-based raises as other employees.'),
        dcc.Markdown("**If you're not seeing an employee that you added, try narrowing the year range. Only employees with data that spans those years will be plotted.**"),
        dcc.Graph(id=ids.PROJECTED_WAGES_LINE_PLOT, config={'displayModeBar': False}),
        html.Hr(),
        html.H4('How do your raises compare in terms of absolute dollar amounts?'), 
        html.H6('The following plot displays the absolute change in compensation over the selected time range. By comparing the length of the line connecting the dots, you can get a sense of the absolute change in compensation between the employees.'),
        dcc.Graph(id=ids.LOLLIPOP_CHART, config={'displayModeBar': False}),
        html.Hr(),
        html.H6('Even among graduate student researchers, applying the same percentage-based raises across all payscales breeds inequity. From 2011 to 2021, the lowest-paid graduate student researchers saw a $5k increase while the highest-paid saw a $10k increase (shown in the default plots).'),
        html.H6('However, this is nothing compared to the massive raises (in absolute dollar terms) of employees with vastly greater earnings (add UC President to the plots, for example).'),
        html.H6("For whatever reason, we tend to talk about raises as a percentage of our previous year's income. By making this our point of reference, we benefit individuals who are already making more by giving them disproportionately larger raises in terms of absolute dollars. Compounded year after year, this inequity becomes exorbitant."),
        dcc.Markdown("**Percentage-based raises are inherently regressive**. This really is all common sense, but percentages can misdirect our sense of outrage by obscuring absolute dollar amounts. To put this into context, graduate student workers making $27K asking for a 100% raise seems unreasonable. Meanwhile, chancellors getting up to a 28% raise on $450k was approved earlier this year. At the end of the day, one of these people gets an extra $27k that goes towards cost of living while the other gets $120k that goes towards idk a yacht."),
        dcc.Markdown("If we want to see raises that are truly equitable, we need to **tie our wages to our cost of living**, not our prior year's salary."),
        dbc.Modal(
            children = [
                dbc.ModalHeader(dbc.ModalTitle("UC My Wages")),
                dbc.ModalBody("Welcome! This dashboard visualizes publicly available data on UC employee compensation."),
                dbc.ModalBody("As this project is under active development, please bear with us if you encounter any bugs."),
                dbc.ModalFooter(
                    dbc.Button("Close", id="close-modal-button")
                ),
            ],
            is_open=True,
            id='landing-modal',
            centered=True

        )
    ]
)

print(time.time() - t0)
#--------------- callback - dropdown -------
# also - dsiable/enable refresh plot
@app.callback(
    Output('compensation-accordion-item','title'),
    Input('select-compensation-dropdown','value'),
    prevent_initial_call = True,       # want to load in background
)
def save_datastore(compensation_type):
    compensation_type = ''.join(compensation_type)        # coerce a list to string
    
    if compensation_type is None:
        raise PreventUpdate

    DataSchema.PAY = compensation_type      # bad: changing global variable - another way?
        
    title = 'Type of Compensation: ' + compensation_type

    return title

#--------------- callback - close modal -------
# triggered by pressing the close button
@app.callback(
    Output("landing-modal", "is_open"),
    Input("close-modal-button", "n_clicks"),
    prevent_initial_call = True
)
def close_modal(n_clicks): 
    return False

# ------------- callback - save_datastore ----------------------
# triggered by landing modal changing
@app.callback(
    ServersideOutput("jobs-data", "data"), 
    ServersideOutput("names-data",'data'),
    Input('landing-modal', 'is_open'),
    State('jobs-data', 'data'),
    State('names-data', 'data'),
    blocking = True, 
    prevent_initial_call = True)
def save_datastore(ts, jobs_data, names_data):
    # names_data can be filtered by year? and earnings?
    if (jobs_data is None) and (names_data is None):
        return df_jobs, df_names
    else:
        raise PreventUpdate
    
# ------------- callback - search names in data frame ----------------
@app.callback(
    Output(ids.NAME_SEARCH_RESULTS_CONTAINER, 'children'),
    Input(ids.NAME_SEARCH_BUTTON, 'n_clicks'),
    State(ids.NAME_SEARCH_INPUT, "value"),
    State('names-data','data'),
    prevent_initial_call=True,
    memoize = True,
    blocking = True,
)
def search_names(n_clicks, search_name, dff_names):
    print('entered search_names:')
    print(search_name)
    t0=time.time()
    # handle if names is empty
    if (search_name is None) or (dff_names is None):
        raise PreventUpdate
    # handle if no matches (maybe no need)

    # display unique matches
    df_names_match = dff_names[dff_names.loc[:,DataSchema.NAME].str.contains(search_name.casefold().strip(), regex=False)]
    print('pandas str contains:')
    print(time.time() - t0)

    t0=time.time()
    unique_names_match = list(set(df_names_match[DataSchema.NAME]))

    # handle if too many matches (todo: leave message)
    if len(unique_names_match) > 200:
        too_many_matches = html.Div(
            children = [
                html.Label('Found too many matching results. Please enter a more specific name.'),
            ]
        )
        return too_many_matches

    # build df where each row is a unique employee w/ an employee name col and a years available col
    table_data_records_list = []
    for name in unique_names_match:
        years_available = df_names_match[DataSchema.YEAR].loc[df_names_match[DataSchema.NAME]==name].to_list()
        years_available_str = ', '.join([str(x) for x in years_available])
        table_data_records_list.append({
            DataSchema.NAME: name, 
            'Years Available': years_available_str
        })
    print('rest of the script:')
    print(time.time() - t0)   

    name_search_results_container_updated = html.Div(
        children = [
            html.Label('Select a name to add to the plots'),
            dash_table.DataTable(
                data = table_data_records_list, 
                columns = [{"name": DataSchema.NAME, "id": DataSchema.NAME}, {"name": 'Years Available', "id": 'Years Available'}],
                id = ids.NAME_SEARCH_RESULTS_TABLE
            )
        ]
    )
    return name_search_results_container_updated

# ------------- callback - add selected name from table to the dropdown ----------------
@app.callback(
    Output(ids.NAME_ADDED_DROPDOWN, "value"),
    Output(ids.NAME_ADDED_DROPDOWN, "options"),
    Input(ids.NAME_ADD_BUTTON, "n_clicks"),
    State(ids.NAME_SEARCH_RESULTS_TABLE, "active_cell"),
    State(ids.NAME_SEARCH_RESULTS_TABLE, "data"),
    State(ids.NAME_ADDED_DROPDOWN, "value"),
    State(ids.NAME_ADDED_DROPDOWN, "options"),
    prevent_initial_call=True,
    blocking = True,
)
def add_name_to_dropdown(n_clicks, active_cell, data, value, options):
    if active_cell is None:
        return value, options

    selected_name = data[active_cell['row']][DataSchema.NAME]
    value.append(selected_name)
    options.append(selected_name)
    return value, options

# ------------- callback - update initial wages ----------------
@app.callback(
    Output(ids.INITIAL_WAGE_DROPDOWN, "value"),
    Output(ids.INITIAL_WAGE_INPUT, "value"),
    Input(ids.INITIAL_WAGE_DROPDOWN, "value"),
    Input(ids.INITIAL_WAGE_INPUT, "value"),
    Input(ids.YEAR_RANGE_SLIDER, 'value'),
    State('jobs-data','data'),
    prevent_initial_call=True
)
def update_initial_wage_input(dropdown_value, input_value, years, df_jobs):
    min_year = years[0]

    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if (trigger_id == ids.INITIAL_WAGE_DROPDOWN) or (trigger_id == ids.YEAR_RANGE_SLIDER):
        # if callback was triggered by user selecting from the dropdown menu, find the selected initial wage to display in the input field
        logical_array = (df_jobs[DataSchema.YEAR] == min_year) & (df_jobs[DataSchema.NAME] == dropdown_value)  # need to handle if more than 1 match
        if sum(logical_array) == 1: 
            input_value = df_jobs.loc[logical_array,DataSchema.PAY].iloc[0]  
        else:
            input_value = "" # default value if no string matches

    elif trigger_id == ids.INITIAL_WAGE_INPUT:
        # if callback was triggered by user editing the input field, set dropdown value to empty
        dropdown_value = ""
        input_value = input_value

    return dropdown_value, input_value

#------------- callback - filtered-names-data -----------------
# triggered (1) when name is added/dropped or (2) year range slider is moved (3) initial creation of data store
# filters by names detected in dropdown menu and year range
@app.callback(
    ServersideOutput('filtered-names-data', 'data'),
    Input(ids.NAME_ADDED_DROPDOWN, "value"),
    Input('names-data','data'),
    Input('compensation-accordion-item','title'),
    prevent_initial_call = True
)
def filter_names_data(names, df_names, title):
    if (names is None) or (names == []):
        raise PreventUpdate

    # IMPORTANT when dealing with categories (cat.remove_unused_categories)
    print('in filter_names_data:')
    t0 = time.time()
    logical_array = (df_names[DataSchema.NAME].isin(names))
    df_names_filtered = df_names.loc[logical_array, [DataSchema.PAY, DataSchema.YEAR]]
    df_names_filtered = df_names_filtered.merge(df_names.loc[(df_names[DataSchema.NAME].isin(names)),DataSchema.NAME].cat.remove_unused_categories(),left_index=True, right_index=True)
    print(time.time() - t0)


    return df_names_filtered

#------------- callback - filtered-jobs-data -----------------
# triggered (1) when name is added/dropped or (2) year range slider is moved
# filters by jobs detected in dropdown menu and year range
# prevent_initial_call is false because we want this to be updated ast startup
@app.callback(
    ServersideOutput('filtered-jobs-data', 'data'),
    Input(ids.RATE_JOB_DROPDOWN, "value"),
    Input('jobs-data','data'),
    Input('compensation-accordion-item','title'),
    prevent_initial_call = True
)
def filter_jobs_data(jobs, df_jobs, title):
    if jobs is None:
        raise PreventUpdate

    # IMPORTANT for mem usage when dealing with categories (cat.remove_unused_categories)
    print('in filter_jobs_data:')
    t0 = time.time()
    logical_array = (df_jobs[DataSchema.NAME].isin(jobs)) 
    df_jobs_filtered = df_jobs.loc[logical_array, [DataSchema.PAY, DataSchema.YEAR]]
    df_jobs_filtered = df_jobs_filtered.merge(df_jobs.loc[logical_array, DataSchema.NAME].cat.remove_unused_categories(),left_index=True, right_index=True)
    print(time.time() - t0)
    print('size of df_jobs_filtered:')
    print(df_jobs_filtered.info(memory_usage = 'deep'))
    
    return df_jobs_filtered

#------------- callback - filtered-combined-data -----------------
#
# combines filtered-jobs-data and filtered-names-data
# further processing by handling duplicates, 
@app.callback(
    ServersideOutput('filtered-combined-data', 'data'),
    Input('filtered-jobs-data','data'),
    Input('filtered-names-data','data'),
    Input(ids.YEAR_RANGE_SLIDER, 'value'),
    prevent_initial_call = True
)
def filter_combined_data(df_jobs_filtered, df_names_filtered, years):
    min_year = years[0]
    max_year = years[1]

    # combine
    df_combined = pd.concat([df_jobs_filtered, df_names_filtered]).astype({DataSchema.NAME: "category"})

    # filter out unused years
    logical_array = (df_combined[DataSchema.YEAR] >= min_year) & (df_combined[DataSchema.YEAR] <= max_year)
    df_combined_filtered = df_combined.loc[logical_array, [DataSchema.PAY, DataSchema.YEAR]]
    df_combined_filtered = df_combined_filtered.merge(df_combined.loc[logical_array, DataSchema.NAME].cat.remove_unused_categories(),left_index=True, right_index=True)
    
    # handle duplicates (same year and name)
    # TODO: handle "duplicates" with common names
    df_duplicates = df_combined_filtered[df_combined_filtered[[DataSchema.YEAR, DataSchema.NAME]].duplicated(keep=False)]                 # grab all duplicates (names and year)
    if len(df_duplicates) > 0:
        df_duplicates = df_duplicates.groupby([DataSchema.YEAR, DataSchema.NAME])[DataSchema.PAY].sum().reset_index()       # add duplicates together
    df_combined_filtered = df_combined_filtered[~df_combined_filtered[[DataSchema.YEAR, DataSchema.NAME]].duplicated(keep=False)]                  # delete duplciates from dff_combined
    df_combined_filtered = pd.concat([df_combined_filtered, df_duplicates])                                                               # concatenate together

    return df_combined_filtered

# ----------------- function for resetting figures -----
def reset_fig_lollipop():
    fig_lollipop = go.Figure()

    # templates
    lollipop_template = go.layout.Template()
    lollipop_template.layout = go.Layout(
            paper_bgcolor=colors.PLOT_BACKGROUND_COLOR,
            plot_bgcolor=colors.PLOT_BACKGROUND_COLOR,
            showlegend=False,
            title_font=dict(family="Arial", size=24),
            yaxis=dict(linewidth=1, linecolor = "black", 
                showgrid=True,  gridcolor = colors.GRID_LINES_COLOR, gridwidth=1,
                automargin = True,
                showline = False,
                fixedrange = True
            ),
            xaxis=dict(zeroline = False, rangemode = "tozero", 
                title = dict(text = "Compensation (USD)"),
                showgrid=True,  gridcolor = colors.GRID_LINES_COLOR, gridwidth=1,
                showline = True, linewidth=1, linecolor = "black",
                fixedrange = True
                )
        )
    fig_lollipop.update_layout(template=lollipop_template)
    return fig_lollipop

def reset_figures():
    print('inside reset_figures:')
    fig_real_wages = go.Figure()
    fig_projected_wages = go.Figure()

    line_template = go.layout.Template()
    line_template.layout = go.Layout(
            paper_bgcolor=colors.PLOT_BACKGROUND_COLOR,
            plot_bgcolor=colors.PLOT_BACKGROUND_COLOR,
            showlegend=False,
            title_font=dict(family="Arial", size=18),
            yaxis=dict(linewidth=1, linecolor = "black", 
                showgrid=True,  gridcolor = colors.GRID_LINES_COLOR, gridwidth=1,
                title = dict(text = "Compensation (USD)"),
                automargin = True,
                showline = True,
                fixedrange = True),
            xaxis=dict(zeroline = False,
                showgrid=True,  gridcolor = colors.GRID_LINES_COLOR, gridwidth=1,
                showline = True, linewidth=1, linecolor = "black",
                dtick = 1,
                fixedrange = True
                ),
            hovermode="x"
        )
    fig_real_wages.update_layout(template=line_template)
    fig_projected_wages.update_layout(template=line_template)

    # create empty dataframes to track names of traces
    df_traces_in_real_wages = pd.DataFrame({DataSchema.NAME: [], "Index": []}).astype({DataSchema.NAME: "category", "Index": int})
    df_traces_in_projected_wages = pd.DataFrame({DataSchema.NAME: [], "Index": []}).astype({DataSchema.NAME: "category", "Index": int})

    return fig_projected_wages, fig_real_wages, df_traces_in_projected_wages, df_traces_in_real_wages

# --------------- function for updating figures --------
# triggered when (1) filtered-jobs-data/filtered-names-data stores are updated 
#
# this callback updates figs only by adding/"removing" traces ("not technically removing, just deleting variables")
# also maintains a data frame ledger that tracks what names/jobs currently have traces in the figs
@app.callback(
        ServersideOutput('traces-in-real-wages', 'data'),
        ServersideOutput('traces-in-projected-wages', 'data'),
        Output(ids.PROJECTED_WAGES_LINE_PLOT, "figure"),
        Output(ids.REAL_WAGES_LINE_PLOT, "figure"),
        Output(ids.LOLLIPOP_CHART, "figure"),
        Input(ids.INITIAL_WAGE_INPUT, "value"),
        Input('filtered-combined-data', 'data'),
        Input('refresh-figures-button','n_clicks'),
        State(ids.YEAR_RANGE_SLIDER, 'value'),
        State('traces-in-real-wages','data'),
        State('traces-in-projected-wages','data'),
        State(ids.PROJECTED_WAGES_LINE_PLOT, "figure"),
        State(ids.REAL_WAGES_LINE_PLOT, "figure"),
        prevent_initial_call = True,
        blocking = True
)
def update_figures(initial_wage, df_combined_filtered, n_clicks, years, df_traces_in_real_wages, df_traces_in_projected_wages, fig_projected_wages, fig_real_wages):
    min_year = years[0]
    max_year = years[1]
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]

    # the innermost if statement should evaluate as true when user moves the year slider or modify input function; if so, resets plots and "ledgers"
    if fig_real_wages is not None:
        if fig_real_wages['layout']['xaxis']['range'] is not None:
            current_fig_min_year = -int(-fig_real_wages['layout']['xaxis']['range'][0]//1)       # this rounds up b/c axes min is less than the smallest year
            current_fig_max_year = int(fig_real_wages['layout']['xaxis']['range'][1]//1)          # this rounds down

            if (current_fig_min_year != min_year) or (current_fig_max_year != max_year) or (trigger_id == ids.INITIAL_WAGE_INPUT):
                fig_projected_wages, fig_real_wages, df_traces_in_projected_wages, df_traces_in_real_wages = reset_figures()
                fig_lollipop = reset_fig_lollipop()
            else:
                # do not reset real/projected wages figs - build it from dictionaries from their existing state
                fig_real_wages = go.Figure(fig_real_wages)
                fig_projected_wages = go.Figure(fig_projected_wages)
                fig_lollipop = reset_fig_lollipop()


    # the very first invocation of this callback is from updating 'filtered-jobs-data', triggered by the modal closing
    if (df_traces_in_real_wages is None) or (df_traces_in_projected_wages is None) or (trigger_id == 'refresh-figures-button'):
        reset_flag = False
        fig_projected_wages, fig_real_wages, df_traces_in_projected_wages, df_traces_in_real_wages = reset_figures()
        fig_lollipop = reset_fig_lollipop()

    # for real wages:
    # get names for real_wages figure
    names_wanted_in_real_wages = set(df_combined_filtered.loc[:,DataSchema.NAME])
    names_already_in_real_wages = set(df_traces_in_real_wages.loc[:, DataSchema.NAME])

    # names already in real wages but not in wanted: delete traces
    names_2delete_real_wages = list(names_already_in_real_wages.difference(names_wanted_in_real_wages))
    logical_array = df_traces_in_real_wages[DataSchema.NAME].isin(names_2delete_real_wages)
    indexes_2delete_real_wages = df_traces_in_real_wages.loc[logical_array, 'Index']
    for i in indexes_2delete_real_wages:
        fig_real_wages.data[int(i)]['x'] = []                        # awkward, but can't delete from tuple; can hide/modify inside objects
        fig_real_wages.data[int(i)]['y'] = []  
    
    df_traces_in_real_wages = df_traces_in_real_wages.loc[~logical_array, :]                        # remove deleted traces from the df "ledger"

    # names in wanted but not yet in real wages: add traces
    names_2add_real_wages = list(names_wanted_in_real_wages.difference(names_already_in_real_wages))
    fig_real_wage_indices = list()
    for name in names_2add_real_wages:
        logical_array = df_combined_filtered.loc[:,DataSchema.NAME] == name
        x_var = df_combined_filtered.loc[logical_array,DataSchema.YEAR]
        y_var = df_combined_filtered.loc[logical_array,DataSchema.PAY]

        fig_real_wages.add_trace(go.Scatter(x = x_var, y = y_var, name = name, hovertemplate = '$%{y}'))
        fig_real_wage_indices.append(len(fig_real_wages.data) - 1)     

    df_traces_in_real_wages = pd.concat([df_traces_in_real_wages, pd.DataFrame({DataSchema.NAME: names_2add_real_wages, 'Index': fig_real_wage_indices})]).astype({DataSchema.NAME: "category", "Index": int})     # update ledger

    # for projected wages/lollipop:
    # additional filter for names/jobs that do not span the years
    names_with_min = df_combined_filtered.loc[df_combined_filtered[DataSchema.YEAR] == min_year, DataSchema.NAME]
    names_with_max = df_combined_filtered.loc[df_combined_filtered[DataSchema.YEAR] == max_year, DataSchema.NAME]
    names_wanted_in_projected_wages = set(names_with_max) & set(names_with_min)
    names_already_in_projected_wages = set(df_traces_in_projected_wages.loc[:, DataSchema.NAME])

    # names already in real wages but not in wanted: delete traces
    names_2delete_projected_wages = list(names_already_in_projected_wages.difference(names_wanted_in_projected_wages))
    logical_array = df_traces_in_projected_wages[DataSchema.NAME].isin(names_2delete_projected_wages)
    indexes_2delete_projected_wages = df_traces_in_projected_wages.loc[logical_array, 'Index']
    for i in indexes_2delete_projected_wages:
        fig_projected_wages.data[int(i)]['x'] = []                        # awkward, but can't delete from tuple; can hide/modify inside objects
        fig_projected_wages.data[int(i)]['y'] = []  
    df_traces_in_projected_wages = df_traces_in_projected_wages.loc[~logical_array, :]                        # remove deleted traces from the df "ledger"

    # names in wanted but not yet in real wages: add traces
    names_2add_projected_wages = list(names_wanted_in_projected_wages.difference(names_already_in_projected_wages))
    fig_projected_wage_indices = list()
    for name in names_2add_projected_wages:
        logical_array = df_combined_filtered.loc[:,DataSchema.NAME] == name
        
        pay = df_combined_filtered.loc[logical_array,DataSchema.PAY].to_numpy()
        priorpay = df_combined_filtered.loc[logical_array,DataSchema.PAY].shift(1).to_numpy()
        priorpay[0] = pay[0]
        adjustment = (pay - priorpay)/priorpay + 1
        cumadjustment = pd.Series(adjustment).cumprod() 

        y_var = cumadjustment*initial_wage
        x_var = df_combined_filtered.loc[logical_array,DataSchema.YEAR]
        
        fig_projected_wages.add_trace(go.Scatter(x = x_var, y = y_var, hovertemplate = '$%{y}', name=name))
        fig_projected_wage_indices.append(len(fig_projected_wages.data) - 1)     

    df_traces_in_projected_wages = pd.concat([df_traces_in_projected_wages, pd.DataFrame({DataSchema.NAME: names_2add_projected_wages, 'Index': fig_projected_wage_indices})]).astype({DataSchema.NAME: "category", "Index": int})     # update ledger
    
    # create df_lollipop (pivot_wider the first and last years)
    # df lollipop needs to be reset every time because of sorting by largest to smallest
    df_lollipop = df_combined_filtered[df_combined_filtered[DataSchema.NAME].isin(names_wanted_in_projected_wages)]         # df lollipop uses the same wanted names as projected wages   
    if len(df_lollipop) > 0:
        df_lollipop = df_lollipop.pivot(index=DataSchema.NAME, columns=DataSchema.YEAR, values=DataSchema.PAY).reset_index()
        # sort by ascending wages
        df_lollipop = df_lollipop.sort_values(by=[max_year, min_year], ascending=True)

        lollipop_x_start = df_lollipop[min_year].tolist()
        lollipop_x_end = df_lollipop[max_year].tolist()
        lollipop_y = df_lollipop[DataSchema.NAME].tolist()

        for i in range(0, len(lollipop_x_start)):
            fig_lollipop.add_trace(go.Scatter(
                        x = [lollipop_x_start[i], lollipop_x_end[i]],
                        y = [lollipop_y[i],lollipop_y[i]],
                        line=dict(color=colors.LOLLIPOP_LINE_COLOR, width=3)))


        fig_lollipop.add_trace(go.Scatter(
                        name=str(min_year) + " Compensation",
                        x=lollipop_x_start,
                        y=lollipop_y,
                        mode = "markers",
                        marker_symbol = "circle",
                        marker_size = 15,
                        marker_color=colors.START_MARKER_COLOR,
                    )
        )

        fig_lollipop.add_trace(go.Scatter(
                        name=str(max_year) + " Compensation",
                        x=lollipop_x_end,
                        y=lollipop_y,
                        mode = "markers",
                        marker_size = 15,
                        marker_color=colors.END_MARKER_COLOR)
        )

    return df_traces_in_real_wages, df_traces_in_projected_wages, fig_projected_wages, fig_real_wages, fig_lollipop






# # # ------------- callback - update initial wage only plots ----------------
# # # triggers only if (1) initial wage is updated or (2) years range slider moved
# # # only need to update the projected wages line plot
# # # todo

# # # ------------- callback - update plots ----------------
# # # triggered (1) filtered-jobs-data/filtered-names-data stores are updated 
# # # 
# # #


# @app.callback(
#         Output(ids.PROJECTED_WAGES_LINE_PLOT, "figure"),
#         Output(ids.REAL_WAGES_LINE_PLOT, "figure"),
#         Output(ids.LOLLIPOP_CHART, "figure"),
#         Input(ids.INITIAL_WAGE_INPUT, "value"),
#         Input('filtered-combined-data', 'data'),
#         State(ids.YEAR_RANGE_SLIDER, 'value'),
#         prevent_initial_call = True,
# )
# def update_plots(initial_wage, df_combined_filtered, years):
#     min_year = years[0]
#     max_year = years[1]
#     if (df_combined_filtered is None):
#         raise PreventUpdate
    
#     t0= time.time()
#     print('update plots - processing dataframes:')




#     dff_real_wages = df_combined_filtered[[DataSchema.NAME, DataSchema.YEAR, DataSchema.PAY]]
#     dff_real_wages = dff_real_wages.sort_values(by=[DataSchema.NAME, DataSchema.YEAR])

#     # for projected wages and lollipop, only plot name if they have values that match the max and min years
#     dff_year_range = dff_real_wages

#     names_with_min = dff_year_range[DataSchema.NAME].loc[dff_year_range[DataSchema.YEAR] == min_year]
#     names_with_max = dff_year_range[DataSchema.NAME].loc[dff_year_range[DataSchema.YEAR] == max_year]
#     names_with_both = list(set(names_with_max) & set(names_with_min))

#     dff_year_range = dff_year_range[dff_year_range[DataSchema.NAME].isin(names_with_both)]
#     #dff_year_range = dff_year_range.sort_values(by=[DataSchema.NAME, DataSchema.YEAR])
#     dff_year_range[DataSchema.PRIORPAY] = dff_year_range[DataSchema.PAY]
#     dff_year_range[DataSchema.PRIORPAY] = dff_year_range[DataSchema.PRIORPAY].shift(1)      # this requires that df is sorted by name and by year
#     dff_year_range.loc[dff_year_range[DataSchema.YEAR] == min_year,DataSchema.PRIORPAY] = dff_year_range.loc[dff_year_range[DataSchema.YEAR] == min_year,DataSchema.PAY]
#     dff_year_range[DataSchema.ADJUSTMENT] = (dff_year_range[DataSchema.PAY] - dff_year_range[DataSchema.PRIORPAY])/dff_year_range[DataSchema.PRIORPAY] + 1

#     # cumulative product to get the compounded factor
#     unique_job_abbr = list(set(dff_year_range[DataSchema.NAME]))
#     for job_abbr in unique_job_abbr:
#         dff_year_range.loc[dff_year_range.loc[:,DataSchema.NAME]==job_abbr,DataSchema.CUMADJUSTMENT] = dff_year_range.loc[dff_year_range[DataSchema.NAME]==job_abbr,DataSchema.ADJUSTMENT].cumprod()

#     dff_year_range[DataSchema.PROJECTEDPAY] = dff_year_range[DataSchema.CUMADJUSTMENT]*initial_wage

#     # create df_lollipop (pivot_wider the first and last years)
#     df_lollipop = dff_year_range[dff_year_range[DataSchema.YEAR].isin([min_year, max_year])]       
#     df_lollipop = df_lollipop.pivot(index=DataSchema.NAME, columns=DataSchema.YEAR, values=DataSchema.PAY).reset_index()
#     # sort by ascending wages
#     df_lollipop = df_lollipop.sort_values(by=[max_year, min_year], ascending=True)


    
#     print('update plots - creating figs:')
    
#     # create line plot
#     fig_real_wages = px.line(
#         dff_real_wages,
#         x=DataSchema.YEAR,
#         y=DataSchema.PAY,
#         color=DataSchema.NAME,
#         markers=True
#     )

#     dff_year_range = dff_year_range[DataSchema.NAME].cat.remove_unused_categories()
#     fig_projected_wages = px.line(
#         dff_year_range,
#         x=DataSchema.YEAR,
#         y=DataSchema.PROJECTEDPAY,
#         color=DataSchema.NAME,
#         markers=True
#     )

#     t2 = time.time()

#     lollipop_x_start = df_lollipop[min_year].tolist()
#     lollipop_x_end = df_lollipop[max_year].tolist()
#     lollipop_y = df_lollipop[DataSchema.NAME].tolist()

#     t3 = time.time()

#     t4 = time.time()
#     fig_lollipop = go.Figure()

#     for i in range(0, len(lollipop_x_start)):
#         fig_lollipop.add_trace(go.Scatter(
#                     x = [lollipop_x_start[i], lollipop_x_end[i]],
#                     y = [lollipop_y[i],lollipop_y[i]],
#                     line=dict(color=colors.LOLLIPOP_LINE_COLOR, width=3)))


#     fig_lollipop.add_trace(go.Scatter(
#                     name=str(min_year) + " Compensation",
#                     x=lollipop_x_start,
#                     y=lollipop_y,
#                     mode = "markers",
#                     marker_symbol = "circle",
#                     marker_size = 15,
#                     marker_color=colors.START_MARKER_COLOR)
#     )

#     fig_lollipop.add_trace(go.Scatter(
#                     name=str(max_year) + " Salary",
#                     x=lollipop_x_end,
#                     y=lollipop_y,
#                     mode = "markers",
#                     marker_size = 15,
#                     marker_color=colors.END_MARKER_COLOR)
#     )

#     t5= time.time()

#     # templates
#     lollipop_template = go.layout.Template()
#     lollipop_template.layout = go.Layout(
#             paper_bgcolor=colors.PLOT_BACKGROUND_COLOR,
#             plot_bgcolor=colors.PLOT_BACKGROUND_COLOR,
#             showlegend=False,
#             title_font=dict(family="Arial", size=24),
#             yaxis=dict(linewidth=1, linecolor = "black", 
#                 showgrid=True,  gridcolor = colors.GRID_LINES_COLOR, gridwidth=1,
#                 automargin = True,
#                 showline = False),
#             xaxis=dict(zeroline = False, rangemode = "tozero", 
#                 title = dict(text = "Compensation (USD)"),
#                 showgrid=True,  gridcolor = colors.GRID_LINES_COLOR, gridwidth=1,
#                 showline = True, linewidth=1, linecolor = "black",
#                 )
#         )

#     t6 = time.time()

#     fig_lollipop.update_layout(title="change in compensation from " + str(min_year) + "-" + str(max_year),
#                   template=lollipop_template)

#     t7 = time.time()

#     line_template = go.layout.Template()
#     line_template.layout = go.Layout(
#             paper_bgcolor=colors.PLOT_BACKGROUND_COLOR,
#             plot_bgcolor=colors.PLOT_BACKGROUND_COLOR,
#             showlegend=False,
#             title_font=dict(family="Arial", size=18),
#             yaxis=dict(linewidth=1, linecolor = "black", 
#                 showgrid=True,  gridcolor = colors.GRID_LINES_COLOR, gridwidth=1,
#                 automargin = True,
#                 showline = True),
#             xaxis=dict(zeroline = False,
#                 title = dict(text = "Compensation (USD)"),
#                 showgrid=True,  gridcolor = colors.GRID_LINES_COLOR, gridwidth=1,
#                 showline = True, linewidth=1, linecolor = "black",
#                 dtick = 1
#                 )
#         )
    
    

#     fig_real_wages.update_layout(title="employee compensation from " + str(min_year) + "-" + str(max_year),
#                   template=line_template)
#     fig_projected_wages.update_layout(title="projected compensation from " + str(min_year) + "-" + str(max_year),
#                   template=line_template)
    

#     t8 = time.time()
#     print('t8 - t0: ' + str(t8 - t0))

#     return fig_projected_wages, fig_real_wages, fig_lollipop

# run script
if __name__ == '__main__':
     app.run_server(debug=True)