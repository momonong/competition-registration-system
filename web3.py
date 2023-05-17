from sqlalchemy import create_engine
from flask import Flask, render_template, request, url_for, redirect, flash
import pandas as pd

# Note: 
# 1. 新增： ready
# 2. 修改： ready
# 3. 刪除： ready
# 4. 附件： not ready

# 連接資料庫
engine = create_engine('postgresql://admin:123456@127.0.0.1:5432/sport')
app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = 'fi13dE9fafkd9a0afklm81WEEd'

# 連接到首頁
@app.route('/')
def index():
    sql = f'''SELECT pid,school_name,team_id,student_name,email,phone,jersey_number 背號 from registration'''
    data = engine.execute(sql)
    column_names = data.keys()
    #print(column_names)
    return render_template('output3.html', outdata=data, outheaders=column_names)

# 新增人員
@app.route('/add_person', methods=['GET','POST'])
def add_person():
    if request.method == "POST":
        pid = request.values['in_pid'].strip()  #去除頭尾空白字元
        school = request.values['in_school'].strip()
        team_id = request.values['in_teamid'].strip()
        name = request.values['in_name'].strip()
        email = request.values['in_email'].strip()
        phone = request.values['in_phone'].strip()
        jersey_number = request.values['in_jersey'].strip()
        conn = engine.connect()
        trans = conn.begin()
        try:
            sql = f'''insert into registration(pid, school_name, team_id, student_name, email, phone, jersey_number) 
                values ('{pid}', '{school}','{team_id}','{name}','{email}','{phone}','{jersey_number}')'''
            conn.execute(sql)
            trans.commit()
            flash("新增人員成功","primary")
        except Exception as e:
            trans.rollback()
            flash(f"新增人員失敗,{str(e)}","danger")
        finally:
            conn.close()
        #print(school+name+email)
    return redirect(url_for("index"))

#修改人員資料
@app.route('/edit_person/<pid>', methods=['GET','POST'])
def edit_person(pid):
    if request.method == "POST":
        school = request.values['in_school'].strip()
        team_id = request.values['in_teamid'].strip()
        name = request.values['in_name'].strip()
        email = request.values['in_email'].strip()
        phone = request.values['in_phone'].strip()
        jersey_number = request.values['in_jersey'].strip()
        conn = engine.connect()
        trans = conn.begin()
        try:
            sql = f'''UPDATE registration SET school_name='{school}',team_id='{team_id}',student_name='{name}',
                email='{email}',phone='{phone}',jersey_number='{jersey_number}',update_time='now()' 
                WHERE pid='{pid}' '''
            conn.execute(sql)
            trans.commit()
            flash("修改人員成功","primary")
        except Exception as e:
            trans.rollback()
            flash(f"修改人員失敗,{str(e)}","danger")
        finally:
            conn.close()
    
    return redirect(url_for("index"))

#刪除人員資料
@app.route('/del_person/<pid>', methods=['GET','POST'])
def del_person(pid):
    if request.method == "POST":
        conn = engine.connect()
        trans = conn.begin()
        try:
            sql = f'''DELETE FROM registration WHERE pid='{pid}' '''
            conn.execute(sql)
            trans.commit()
            flash("刪除人員成功","primary")
        except Exception as e:
            trans.rollback()
            flash(f"刪除人員失敗,{str(e)}","danger")
        finally:
            conn.close()

    return redirect(url_for("index"))

if __name__ == '__main__':
   app.run(host='0.0.0.0',port=8000,debug=True)
