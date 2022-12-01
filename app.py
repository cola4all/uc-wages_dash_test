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
JOB_DATA_PATH =  os.path.join(APP_PATH, "assets", "salaries.csv")
NAME_DATA_PATH =  os.path.join(APP_PATH, "assets", "salaries_by_name.csv")

# create schemas so that you don't need to remember the labels
class DataSchema:
    NAME = "Employee Name"
    JOB = "Job Title"
    JOB_ABBREVIATED = "Abbreviated Job Title"
    PAY = "Total Pay & Benefits"
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
    PLOT_BACKGROUND_COLOR = "#c2e2f3"
    END_MARKER_COLOR = "#355218"
    START_MARKER_COLOR = "#759356"
    LOLLIPOP_LINE_COLOR = "#7B7B7B"
    GRID_LINES_COLOR = "#C5CCCA"
    
# load data
df_jobs = pd.read_csv(
    JOB_DATA_PATH,
    usecols=[
        DataSchema.NAME,
        DataSchema.JOB,
        DataSchema.JOB_ABBREVIATED,
        DataSchema.PAY,
        DataSchema.YEAR],
    dtype={
        DataSchema.NAME: str,
        DataSchema.JOB: str,
        DataSchema.JOB_ABBREVIATED: str,
        DataSchema.PAY: float,
        DataSchema.YEAR: str
    }
)
all_jobs = df_jobs[DataSchema.JOB].tolist()
unique_jobs = list(set(all_jobs))

df_names = pd.read_csv(
    NAME_DATA_PATH,
    usecols=[
        DataSchema.NAME,
        DataSchema.PAY,
        DataSchema.YEAR],
    dtype={
        DataSchema.NAME: "category",
        DataSchema.PAY: float,
        DataSchema.YEAR: int
    }
)

all_names = df_names[DataSchema.NAME].tolist()
unique_names = list(set(all_names))
print(len(df_names))

# ------------- create html components --------------------
initial_wage_container = html.Div(
        id = ids.INITIAL_WAGE_CONTAINER,
        className = 'dropdown-container',
        children = [
            html.Label('Set an initial wage:', id="initial-wage-label"),
            dcc.Dropdown(
                id=ids.INITIAL_WAGE_DROPDOWN,
                options=unique_jobs,
                value = "Graduate Student Researcher (Step 1)",
                placeholder="select initial wage by job or enter custom value on the right",
                multi=False,
                clearable=False
            ),
            dbc.Input(
                id=ids.INITIAL_WAGE_INPUT, 
                value = df_jobs.loc[df_jobs[DataSchema.JOB]=="Graduate Student Researcher (Step 1)", DataSchema.PAY].iloc[0],
                type="number", 
                placeholder="",
                debounce=True)
        ]
)

job_container = html.Div(
    className="dropdown-container",
    children = [
        html.Label("Select Job", id="job-label"),
        dcc.Dropdown(
            id=ids.RATE_JOB_DROPDOWN,
            options=unique_jobs,
            value=["Graduate Student Researcher (Step 1)",
                "Graduate Student Researcher (Step 4)",
                "Graduate Student Researcher (Step 7)",
                "Graduate Student Researcher (Step 10)",
                ],
            multi=True
        )
    ]
)

cola_container = html.Div(
    className='dropdown-container',
    children = [
        html.Label("Select COLA", id="cola-label"),
        dcc.Dropdown(
            id=ids.RATE_COLA_DROPDOWN,
            options=["Santa Barbara", "Los Angeles", "San Francisco"],
            value="Santa Barbara",
            multi=False
        )
    ]
)

# ------------- create year range slider components ----------------
year_range_container = html.Div(
    id = ids.YEAR_RANGE_CONTAINER,
    className='dropdown-container',
    children = [
        html.Label('Years Range:', id='year-range-label'),
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
            html.Label('Search for a name:'),
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

# create layout
app.layout = html.Div(
    className="app-div",
    children=[
        html.Div(
            className = "title-container",
            children=[
                html.H1(app.title),
                html.H3('How does your compensation stack up?'),
                html.Hr(),
                html.H4("by POISE"),
            ]
        ),
        html.Div(
            className="inputs-container",
            children = [
                initial_wage_container,
                job_container,
                cola_container,
                year_range_container
            ]
        ),
        dcc.Loading(
            html.Div(
                id = 'name-container',
                children = [
                    name_search_container,
                    name_search_results_container,
                    name_add_container
                ]
            ),  
        ),
        html.Hr(),
        html.H6('This first plot displays the raw compensation data from the data sources.'),
        dcc.Graph(id=ids.REAL_WAGES_LINE_PLOT, config={'displayModeBar': False}),
        html.Hr(),
        html.H4('Ever wonder what your compensation might be if it grew at the same rate as other UC employees?'), 
        html.H6('This plot displays how your specified initial wage would change if you received the same year-to-year percentage-based raises as other employees.'),
        html.H6('(Note that only people with data that spans the selected years are displayed here.)'),   
        dcc.Graph(id=ids.PROJECTED_WAGES_LINE_PLOT, config={'displayModeBar': False}),
        html.Hr(),
        html.H4('Percentage-based raises are inherently regressive.'),
        html.H6('Given the same percentage raise, higher-earners receive a larger raise in absolute dollar amount compared to lower-earners. This discrepancy is drastic when comparing two employees with vastly different earnings. Compounded year after year, this discrepancy can grow at an exorbitant rate.'),
        html.H6('The following plot displays the absolute change in compensation over the selected time range. By comparing the length of the line connecting the dots, you can get a sense of the absolute change in compensation between the employees.'),
        dcc.Graph(id=ids.LOLLIPOP_CHART, config={'displayModeBar': False}),
        html.Hr(),
        html.H6('Placeholder for comparing wrt COL'),
        html.H6('Placeholder for something about data sources'),

        # data stores
        dcc.Store(id='jobs-data'),
        dcc.Store(id='names-data'),
        dcc.Store(id='unique-names'),
        dcc.Store(id='table-data-records-list')
    ]
)

# ------------- callback - filter_datastore ----------------------
@app.callback(
    ServersideOutput("jobs-data", "data"), 
    ServersideOutput("names-data",'data'),
    ServersideOutput('unique-names','data'),
    Input('jobs-data', 'modified_timestamp'),
    State('jobs-data', 'data'),
    State('names-data', 'data'),
    State('unique-names', 'data'),
    blocking = True)
def filter_datastore(ts, jobs_data, names_data, unique_names_data):

    # names_data can be filtered by year? and earnings?
    if (jobs_data is None) and (names_data is None) and (unique_names_data is None):
        return df_jobs, df_names, unique_names
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
        raise PreventUpdate

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
    prevent_initial_call=True
)
def update_initial_wage_input(dropdown_value, input_value):
    initial_year = '2011'     # for now, initial year is 2011

    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if trigger_id == ids.INITIAL_WAGE_DROPDOWN:
        # if callback was triggered by user selecting from the dropdown menu, find the selected initial wage to display in the input field
        logical_array = (df_jobs[DataSchema.YEAR] == initial_year) & (df_jobs[DataSchema.JOB] == dropdown_value)  # need to handle if more than 1 match
        if sum(logical_array) == 1: 
            input_value = df_jobs.loc[logical_array,DataSchema.PAY].iloc[0]  
        else:
            input_value = "" # default value if no string matches
        dropdown_value = dropdown_value
    elif trigger_id == ids.INITIAL_WAGE_INPUT:
        # if callback was triggered by user editing the input field, set dropdown value to empty
        dropdown_value = ""
        input_value = input_value

    return dropdown_value, input_value

# ------------- callback - update plots ----------------
@app.callback(
        Output(ids.PROJECTED_WAGES_LINE_PLOT, "figure"),
        Output(ids.REAL_WAGES_LINE_PLOT, "figure"),
        Output(ids.LOLLIPOP_CHART, "figure"),
        Input(ids.INITIAL_WAGE_INPUT, "value"),
        Input(ids.RATE_JOB_DROPDOWN, "value"),
        Input(ids.NAME_ADDED_DROPDOWN, "value"),
        Input(ids.YEAR_RANGE_SLIDER,"value")
)
def update_plots(initial_wage, jobs, names, years):
    min_year = str(years[0])
    max_year = str(years[1])
    ## plot using jobs data first
    # filter data frame by job title
    logical_array_jobs = (df_jobs[DataSchema.JOB].isin(jobs)) & (df_jobs[DataSchema.YEAR].astype(int) >= int(min_year)) & (df_jobs[DataSchema.YEAR].astype(int) <= int(max_year))
    dff_jobs = df_jobs[logical_array_jobs]

    # if names list is empty, don't bother transferring the names_df
    if names:
        logical_array_names = (df_names[DataSchema.NAME].isin(names)) & (df_names[DataSchema.YEAR].astype(int) >= int(min_year)) & (df_names[DataSchema.YEAR].astype(int) <= int(max_year))
        dff_names = df_names[logical_array_names]
        dff_names[DataSchema.JOB_ABBREVIATED] = dff_names[DataSchema.NAME]      # keep consistent with dff_jobs
    else:
        dff_names = pd.DataFrame()
    
    dff_combined = pd.concat([dff_jobs, dff_names])

    # handle duplicates (same year and abbreviated job)
    dff_duplicates = dff_combined[dff_combined[[DataSchema.YEAR, DataSchema.JOB_ABBREVIATED]].duplicated(keep=False)]
    dff_duplicates = dff_duplicates.groupby([DataSchema.YEAR, DataSchema.JOB_ABBREVIATED])[DataSchema.PAY].sum().reset_index()     # add duplicates together
    dff_combined = dff_combined[~dff_combined[[DataSchema.YEAR, DataSchema.JOB_ABBREVIATED]].duplicated(keep=False)]
    dff_combined = pd.concat([dff_combined, dff_duplicates])
    # todo- handle "duplicates" with common names

    dff_real_wages = dff_combined[[DataSchema.JOB_ABBREVIATED, DataSchema.YEAR, DataSchema.PAY]]
    dff_real_wages = dff_real_wages.sort_values(by=[DataSchema.JOB_ABBREVIATED, DataSchema.YEAR])

    # for projected wages and lollipop, only plot name if they have values that match the max and min years
    dff_year_range = dff_real_wages

    names_with_min = dff_year_range[DataSchema.JOB_ABBREVIATED].loc[dff_year_range[DataSchema.YEAR] == min_year]
    names_with_max = dff_year_range[DataSchema.JOB_ABBREVIATED].loc[dff_year_range[DataSchema.YEAR] == max_year]
    names_with_both = list(set(names_with_max) & set(names_with_min))

    dff_year_range = dff_year_range[dff_year_range[DataSchema.JOB_ABBREVIATED].isin(names_with_both)]
    #dff_year_range = dff_year_range.sort_values(by=[DataSchema.JOB_ABBREVIATED, DataSchema.YEAR])
    dff_year_range[DataSchema.PRIORPAY] = dff_year_range[DataSchema.PAY]
    dff_year_range[DataSchema.PRIORPAY] = dff_year_range[DataSchema.PRIORPAY].shift(1)      # this requires that df is sorted by name and by year
    dff_year_range.loc[dff_year_range[DataSchema.YEAR] == min_year,DataSchema.PRIORPAY] = dff_year_range.loc[dff_year_range[DataSchema.YEAR] == min_year,DataSchema.PAY]
    dff_year_range[DataSchema.ADJUSTMENT] = (dff_year_range[DataSchema.PAY] - dff_year_range[DataSchema.PRIORPAY])/dff_year_range[DataSchema.PRIORPAY] + 1

    # cumulative product to get the compounded factor
    unique_job_abbr = list(set(dff_year_range[DataSchema.JOB_ABBREVIATED]))
    for job_abbr in unique_job_abbr:
        dff_year_range.loc[dff_year_range.loc[:,DataSchema.JOB_ABBREVIATED]==job_abbr,DataSchema.CUMADJUSTMENT] = dff_year_range.loc[dff_year_range[DataSchema.JOB_ABBREVIATED]==job_abbr,DataSchema.ADJUSTMENT].cumprod()

    dff_year_range[DataSchema.PROJECTEDPAY] = dff_year_range[DataSchema.CUMADJUSTMENT]*initial_wage

    # create df_lollipop (pivot_wider the first and last years)
    df_lollipop = dff_year_range[dff_year_range[DataSchema.YEAR].isin([min_year, max_year])]       
    df_lollipop = df_lollipop.pivot(index=DataSchema.JOB_ABBREVIATED, columns=DataSchema.YEAR, values=DataSchema.PAY).reset_index()
    # sort by ascending wages
    df_lollipop = df_lollipop.sort_values(by=[max_year, min_year], ascending=True)

    # create line plot
    fig_real_wages = px.line(
        dff_real_wages,
        x=DataSchema.YEAR,
        y=DataSchema.PAY,
        color=DataSchema.JOB_ABBREVIATED,
        markers=True
    )

    fig_projected_wages = px.line(
        dff_year_range,
        x=DataSchema.YEAR,
        y=DataSchema.PROJECTEDPAY,
        color=DataSchema.JOB_ABBREVIATED,
        markers=True
    )


    lollipop_x_start = df_lollipop[min_year].tolist()
    lollipop_x_end = df_lollipop[max_year].tolist()
    lollipop_y = df_lollipop[DataSchema.JOB_ABBREVIATED].tolist()

    fig_lollipop = go.Figure()

    for i in range(0, len(lollipop_x_start)):
        fig_lollipop.add_trace(go.Scatter(
                    x = [lollipop_x_start[i], lollipop_x_end[i]],
                    y = [lollipop_y[i],lollipop_y[i]],
                    line=dict(color=colors.LOLLIPOP_LINE_COLOR, width=3)))


    fig_lollipop.add_trace(go.Scatter(
                    name=min_year + " Compensation",
                    x=lollipop_x_start,
                    y=lollipop_y,
                    mode = "markers",
                    marker_symbol = "circle",
                    marker_size = 15,
                    marker_color=colors.START_MARKER_COLOR)
    )

    fig_lollipop.add_trace(go.Scatter(
                    name=max_year + " Salary",
                    x=lollipop_x_end,
                    y=lollipop_y,
                    mode = "markers",
                    marker_size = 15,
                    marker_color=colors.END_MARKER_COLOR)
    )

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
                showline = False),
            xaxis=dict(zeroline = False, rangemode = "tozero", 
                title = dict(text = "Compensation (USD)"),
                showgrid=True,  gridcolor = colors.GRID_LINES_COLOR, gridwidth=1,
                showline = True, linewidth=1, linecolor = "black",
                )
        )
    fig_lollipop.update_layout(title="change in compensation from " + min_year + "-" + max_year,
                  template=lollipop_template)

    line_template = go.layout.Template()
    line_template.layout = go.Layout(
            paper_bgcolor=colors.PLOT_BACKGROUND_COLOR,
            plot_bgcolor=colors.PLOT_BACKGROUND_COLOR,
            showlegend=False,
            title_font=dict(family="Arial", size=18),
            yaxis=dict(linewidth=1, linecolor = "black", 
                showgrid=True,  gridcolor = colors.GRID_LINES_COLOR, gridwidth=1,
                automargin = True,
                showline = True),
            xaxis=dict(zeroline = False,
                title = dict(text = "Compensation (USD)"),
                showgrid=True,  gridcolor = colors.GRID_LINES_COLOR, gridwidth=1,
                showline = True, linewidth=1, linecolor = "black",
                dtick = 1
                )
        )
    fig_real_wages.update_layout(title="employee compensation from " + min_year + "-" + max_year,
                  template=line_template)
    fig_projected_wages.update_layout(title="projected compensation from " + min_year + "-" + max_year,
                  template=line_template)

    return fig_projected_wages, fig_real_wages, fig_lollipop

# run script
if __name__ == '__main__':
    app.run_server(debug=True)