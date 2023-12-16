import pandas as pd
import io
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from IPython.display import clear_output
import numpy as np
from flask import Flask, render_template, request, Response

app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

# Loads data into data_src Data Frame from summer.csv
data_src = pd.read_csv('summer.csv')

# Groupingby data for Filter Criterion in Search Olympic Data page
groupby_data = {}
for column in data_src.columns.tolist():
    groupby_data[column] = data_src[column].unique()


# Loading the dataset into a variable and initialising variables
available_filter_options = data_src.columns
selected_filter_list = []
user_input_dict = {}

# Filtering data based on the criterion given in Search Olympic Data page
def get_filtered_data(filter_criterion):
    data_check_list = []
    for k,v in filter_criterion.items():
        data_inner_check_list = []
        if k != 'search' and k != 'number_of_records' and k!= 'plot_for':
            for val in v:
                if k == 'Year':
                    data_inner_check_list.append(data_src[k] == int(val))
                else:
                    data_inner_check_list.append(data_src[k] == val)

            inner_condition_check = True
            if len(data_inner_check_list) >= 1:
                inner_condition_check = data_inner_check_list[0]

            for index in range(1,len(data_inner_check_list)-1):
                inner_condition_check |= data_inner_check_list[index]

            if len(data_inner_check_list) >= 2:
                inner_condition_check |= data_inner_check_list[len(data_inner_check_list)-1]
            
            data_check_list.append(inner_condition_check)

    condition_check = True
    if len(data_check_list) >= 1:
        condition_check = data_check_list[0]

    for index in range(1,len(data_check_list)-1):
        condition_check &= data_check_list[index]

    if len(data_check_list) >= 2:
        condition_check &= data_check_list[len(data_check_list)-1]

    records_num = filter_criterion.get('number_of_records')
    records_limit = records_num and records_num[0]

    if records_limit == 'all':
        if type(condition_check) == bool:
            return data_src
        return data_src[condition_check]
    else:
        return data_src[condition_check].head(int(records_limit))

# Generating Plot
@app.route('/print-plot')
def plot_results(filtered_data, plot_for):
    labels = filtered_data[plot_for].unique()
    label_data = filtered_data[plot_for].value_counts().to_numpy()
    if plot_for == 'Country':
        fig, ax = plt.subplots()
        ax.set_title(f'{plot_for} Plot')
        label_data_sum = sum(label_data)
        label_data_proportion = [(x/label_data_sum)*100 for x in label_data]
        if (len(labels) > len(label_data_proportion)):
            labels = labels[0:len(labels)-1]
        ax.set_facecolor('aliceblue');
        fig.set_facecolor('aliceblue');
        ax.pie(label_data_proportion, labels=labels, autopct='%1.1f%%', shadow=True, startangle=90)
        fig.savefig('./static/plots/pie_plot.png')
        output = io.BytesIO()
    elif plot_for in ['Gender', 'Medal']:
        fig, ax = plt.subplots()
        ax.set_title(f'{plot_for} Plot')
        ax.bar(labels, label_data)
        ax.set_xlabel (plot_for)
        ax.set_ylabel('Count');
        ax.set_facecolor('aliceblue');
        fig.set_facecolor('aliceblue');
        fig.savefig('./static/plots/bar_plot.png')
        output = io.BytesIO()

# Page with Search Olympic functionality
@app.route('/', methods=['post', 'get'])
def index():
    filtered_data = data_src.head().to_numpy()
    return render_template('index.html', groupby_data=groupby_data, filtered_data=filtered_data)

# Page with Search Results upon filtering in Search Olympic functionality'
@app.route('/result',methods = ['POST', 'GET'])
def result():
    filtered_data = data_src.head().to_numpy()
    if request.method == 'POST':
        filter_criterion = request.form.to_dict(flat=False)
        filtered_data = get_filtered_data(filter_criterion)
        filtered_data_value_counts = filtered_data['Country'].value_counts().to_json()
        plot_for = filter_criterion['plot_for'][0]
        fig_url = ""
        if plot_for != 'Table':
            plot_results(filtered_data, filter_criterion['plot_for'][0])
            fig_urls = {
                "bar_plot": "http://127.0.0.1:5000/static/plots/bar_plot.png",
                "pie_plot": "http://127.0.0.1:5000/static/plots/pie_plot.png"
            }
            if plot_for == 'Country':
                fig_url = fig_urls['pie_plot']
            else:
                fig_url = fig_urls['bar_plot']
        return render_template('result.html', groupby_data=groupby_data, filtered_data=filtered_data.to_numpy(), filtered_data_value_counts=filtered_data_value_counts,  display_filter=plot_for, fig_url=fig_url)
 
if __name__ == "__main__":
    app.run(debug=True)