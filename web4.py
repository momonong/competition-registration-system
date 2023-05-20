#!/usr/bin/env python
from sqlalchemy import create_engine
from flask import Flask, render_template, request, url_for, redirect, flash, send_file,Response
import pandas as pd
from io import BytesIO
from urllib.parse import quote

# Note: 
# 1. 新增： ready
# 2. 修改： ready
# 3. 刪除： ready
# 4. 附件： ready

# 連接資料庫
engine = create_engine('postgresql://admin:123456@127.0.0.1:5432/sport')
app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = 'fi13dE9fafkd9a0afklm81WEEd'

app.config['ALLOWED_EXTENSIONS'] = {'PDF', 'JPG', 'JPEG', 'PNG', 'HEIC'}

# 連接到首頁
@app.route('/')
def index():
    sql = f'''SELECT pid,school_name,team_id,student_name,email,phone,jersey_number,
        CASE WHEN pid_data IS NOT NULL THEN 'Y' ELSE '' end as 身 from registration
        order by update_time desc'''
    data = engine.execute(sql)
    column_names = data.keys()
    return render_template('output4.html', outdata=data, outheaders=column_names)

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
        file = request.files['in_file']
        if file:
            file_extension = file.filename.rsplit('.', 1)[1].upper()
        conn = engine.connect()
        trans = conn.begin()
        try:
            #若HTML表單有選擇檔案, 但副檔名不在許可格式清單中, 則禁止新增, 並拋送Exception訊息
            if file and not(file_extension in app.config['ALLOWED_EXTENSIONS']):
                raise Exception(f"{file_extension}檔案格式不能上傳")
            sql1 = f'''insert into registration(pid, school_name, team_id, student_name, email, phone, jersey_number) 
                values ('{pid}', '{school}','{team_id}','{name}','{email}','{phone}','{jersey_number}')'''
            conn.execute(sql1)
            # 若HTML表單有選擇檔案, 並且副檔名在許可格式清單中, 則新增檔案
            if file and file_extension in app.config['ALLOWED_EXTENSIONS']:
                sql2 ="UPDATE registration SET pid_filename=%s, pid_data=%s WHERE pid=%s"
                conn.execute(sql2, file.filename, file.read(), pid) 
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
        file = request.files['in_file']
        if file:
            file_extension = file.filename.rsplit('.', 1)[1].upper()
        ifrmfile = request.form.get('in_rmexistfile')
        conn = engine.connect()
        trans = conn.begin()
        try:
            #若HTML表單有選擇檔案, 但副檔名不在許可格式清單中, 則禁止更新, 並拋送Exception訊息
            if file and not(file_extension in app.config['ALLOWED_EXTENSIONS']):
                raise Exception(f"{file_extension}檔案格式不能上傳")
            sql1 = f'''UPDATE registration SET school_name='{school}',team_id='{team_id}',student_name='{name}',
                email='{email}',phone='{phone}',jersey_number='{jersey_number}',update_time='now()' 
                WHERE pid='{pid}' '''
            conn.execute(sql1)
            # 若HTML表單有選擇檔案, 並且副檔名在許可格式清單中, 則更新檔案
            if file and file_extension in app.config['ALLOWED_EXTENSIONS']:
                sql2 ="UPDATE registration SET pid_filename=%s, pid_data=%s WHERE pid=%s"
                conn.execute(sql2, file.filename, file.read(), pid) 
            # 若HTML表單未選擇檔案, 並且勾選移除已上傳檔案, 則清除資料庫檔案
            elif not(file) and ifrmfile=='rm':
                sql3 ="UPDATE registration SET pid_filename=null, pid_data=null WHERE pid=%s"
                conn.execute(sql3, pid)
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

# create showfile function 
@app.route('/showfile/<pid>', methods=['GET','POST'])
def showfile(pid):
    try:
        sql = f"select pid_filename,pid_data from registration where pid='{pid}'"
        file_data = engine.execute(sql).fetchone()
        file_stream = BytesIO(file_data['pid_data'])
        file_name = file_data['pid_filename']
        file_extension = file_name.split(".")[-1].upper()
        headers = {}
        match file_extension:
            case 'JPG' | 'JPEG':
                filetype = 'image/jpeg'
            case 'PNG':
                filetype = 'image/png'
            case 'PDF':
                filetype = 'application/pdf'
            case _:
                filetype = 'na'
        #flash("Show檔案成功","primary")
        headers = {	'Content-Type': filetype,
                	'Content-Disposition': f'''inline; filename="{quote(file_data['pid_filename'])}"'''}
    
    except Exception as e:
        flash(f"Show檔案失敗,{str(e)}","danger")
    # 以下 send_file->download_name 需搭配python v3.11
    #return send_file(file_stream, mimetype=filetype, download_name=(quote(file_data['pid_filename'])), as_attachment=False)
    return Response(file_stream, headers=headers)


if __name__ == '__main__':
   app.run(host='0.0.0.0',port=8000,debug=True)
