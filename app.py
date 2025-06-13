from flask import Flask, render_template, request
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os
import uuid
from werkzeug.utils import secure_filename

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
STATIC_FOLDER = 'static'
ALLOWED_EXTENSIONS = {'csv'}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(STATIC_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'datafile' not in request.files:
        return "No file part"

    file = request.files['datafile']
    if file.filename == '':
        return "No selected file"

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        df = pd.read_csv(filepath)
        df_sorted = df.sort_values(by=df.columns[0])
        head_data = df_sorted.head(10).values.tolist()
        full_data = df_sorted.values.tolist()  # All rows
        column_names = df_sorted.columns.tolist()

        stats = df.describe(include='all').transpose()
        stats['null_count'] = df.isnull().sum()
        stats['data_type'] = df.dtypes
        stats_dict = stats.to_dict(orient='index')

        return render_template('select_columns.html',
                       filename=filename,
                       columns=column_names,
                       head_data=head_data,
                       column_names=column_names,
                       num_rows=df.shape[0],
                       num_columns=df.shape[1],
                       column_stats=stats_dict,
                       full_data=full_data)  # ✅ Add this line


    return "Invalid file type. Please upload a CSV file."

@app.route('/visualize', methods=['POST'])
def visualize():
    filename = request.form['filename']
    chart_type = request.form['chart_type']
    x_col = request.form['x_col']
    y_col = request.form.get('y_col')

    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    df = pd.read_csv(filepath)

    fig, ax = plt.subplots(figsize=(8, 5))

    try:
        if chart_type == 'bar':
            df.groupby(x_col)[y_col].mean().plot(kind='bar', ax=ax)
        elif chart_type == 'line':
            df.sort_values(by=x_col).plot(x=x_col, y=y_col, kind='line', ax=ax)
        elif chart_type == 'scatter':
            df.plot.scatter(x=x_col, y=y_col, ax=ax)
        elif chart_type == 'hist':
            df[x_col].plot(kind='hist', bins=20, ax=ax)
        else:
            return "Unsupported chart type."
    except Exception as e:
        return f"Error generating plot: {str(e)}"

    plot_filename = f"plot_{uuid.uuid4().hex}.png"
    plot_path = os.path.join(STATIC_FOLDER, plot_filename)
    fig.tight_layout()
    plt.savefig(plot_path)
    plt.close(fig)

    return render_template('visualize.html', plot_url=plot_filename)


@app.route('/stats', methods=['POST'])
def calculate_stat():
    filename = request.form['filename']
    column = request.form['column']
    stat_type = request.form['stat_type']

    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    df = pd.read_csv(filepath)

    try:
        if stat_type == 'mean':
            result = df[column].mean()
        elif stat_type == 'median':
            result = df[column].median()
        elif stat_type == 'mode':
            result = df[column].mode().values.tolist()
        elif stat_type == 'variance':
            result = df[column].var()
        else:
            result = "Invalid stat type."
    except Exception as e:
        result = f"Error: {str(e)}"

    return render_template('stat_result.html', column=column, stat_type=stat_type, result=result)

# ✅ app.run should be last
if __name__ == '__main__':
    app.run(debug=True)

