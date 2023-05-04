from sqlalchemy import create_engine
from flask import Flask, render_template, request, url_for
import pandas as pd

# 連接資料庫
engine = create_engine('postgresql://admin:123456@127.0.0.1:5432/postgres')
app = Flask(__name__, template_folder='templates', static_folder='static')

# 連接到首頁
@app.route('/')
def index():
    sql = f'''SELECT * from registration_test'''
    data = engine.execute(sql)
    column_names = data.keys()
    #print(column_names)
    return render_template('output1-1.html', outdata=data, outheaders=column_names)

if __name__ == '__main__':
   app.run(port=5000,debug=True)
