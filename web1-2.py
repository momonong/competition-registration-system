from sqlalchemy import create_engine
from flask import Flask, render_template, request, url_for, redirect
import pandas as pd

# Note: 
# 1. 新增： ready
# 2. 修改： not ready
# 3. 刪除： not ready
# 4. 附件： not ready

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
    return render_template('output1-2.html', outdata=data, outheaders=column_names)

# 新增人員
@app.route('/add_person', methods=['GET','POST'])
def add_person():
    if request.method == "POST":
        school = request.values['in_school']
        name = request.values['in_name']
        email = request.values['in_email']
        phone = request.values['in_phone']
        jersey_number = request.values['in_jersey']
        sql = f'''insert into registration_test(school_name, student_name, email, phone, jersey_number) 
            values ('{school}','{name}','{email}','{phone}','{jersey_number}')'''
        engine.execute(sql)
        #print(school+name+email)
    return redirect(url_for("index"))

if __name__ == '__main__':
   app.run(port=5000,debug=True)
