from flask import Flask, request, redirect, url_for, send_file, render_template
import pandas as pd
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['PROCESSED_FOLDER'] = 'processed'
app.config['ALLOWED_EXTENSIONS'] = {'csv', 'xls', 'xlsx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def process_file(file_path, file_extension):
    # Depending on the file extension, read the file into a DataFrame
    if file_extension == '.csv':
        df = pd.read_csv(file_path)
    elif file_extension in ['.xls', '.xlsx']:
        df = pd.read_excel(file_path, engine='openpyxl' if file_extension == '.xlsx' else 'xlrd')
    else:
        raise ValueError("Unsupported file format")

    # Insert your processing logic here
    d=df['QTRNO'][:]
    final=list(map(lambda x: x[1:-1],d))
    for i in range(len(final)):
        if(int(final[i])<696):
            df.drop(i,inplace=True)
    df.sort_values(by='QTRNO',inplace=True)
    df.drop(['METERID','METERNO', 'METER_TYPE', 'METER_STATUS', 'HOUSE_LOCK','METER_READ_DATE','AVG_UNITS', 'AVG_AMT','BILLMONTH', 'MONTH_PERIOD', 'ELE_SUPPLIER','ELE_PHASE_TYPE', 'ELE_LOAD', 'RECV_PERIOD', 'BILL_STATUS'],axis=1,inplace=True)
    df['SerialNo']=list(range(2475,2475+len(df)))
    def convertt(x):
        if(type(x)==type(1.0)):
            return 0
        else:
            t,z=x.split("/")[1],x.split("/")[2]
            t1,t2=t.split(" ")[0][0],t.split(" ")[1][0]
            z1=z[4:]
            return str(t1+t2+z1)
    qtr=list(df['QTR_DETAILS'])
    qtr_f=list(map(lambda x: convertt(x),qtr))
    df['QTR_DETAILS']=qtr_f

    

    copy_final=df[['SerialNo','QTRNO','QTR_DETAILS','PARTYCODE','PARTYNAME','BILL_AMT','METER_READING','TOTAL_UNITS']]
    df=copy_final

    # Save the processed file with 'converted' appended to the original name
    processed_file_name = secure_filename(file_path) + '_converted' + file_extension
    processed_file_path = os.path.join(app.config['PROCESSED_FOLDER'], processed_file_name)

    if file_extension == '.csv':
        df.to_csv(processed_file_path, index=False)
    elif file_extension in ['.xls', '.xlsx']:
        df.to_excel(processed_file_path, index=False, engine='openpyxl')

    return processed_file_path

@app.route('/')
def upload_form():
    return render_template('upload.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(request.url)

    file = request.files['file']
    if file.filename == '':
        return redirect(request.url)

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        # Process the file
        processed_file_path = process_file(file_path, os.path.splitext(filename)[1])

        # Send the processed file back to the user
        return send_file(
            processed_file_path,
            as_attachment=True,
            download_name=os.path.basename(processed_file_path)
        )

if __name__ == '__main__':
    # Create directories if they don't exist
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    if not os.path.exists(app.config['PROCESSED_FOLDER']):
        os.makedirs(app.config['PROCESSED_FOLDER'])
    
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)
