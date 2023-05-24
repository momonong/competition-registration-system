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
app.config['MAX_FILE_SIZE'] =  16 * 1024 * 1024  # 16MB 的位元組

# 連接到首頁
@app.route('/')
def index():
    sql = f'''SELECT pid,school_name,team_id,student_name,email,phone,jersey_number,
        CASE WHEN pid_data IS NOT NULL THEN '_Y' ELSE '' end as 身,
        CASE WHEN st_data IS NOT NULL THEN '_S' ELSE '' end as 學, 
        CASE WHEN er_data IS NOT NULL THEN '_E' ELSE '' end as 在 
        FROM registration ORDER BY update_time desc'''
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

        conn = engine.connect()
        trans = conn.begin()
        try:
            #找出所有 input box 為file type, iboxname存放所有input box name, file 存放檔案資料 
            for iboxname,file in request.files.items():
                if file.filename:
                    file_extension = file.filename.rsplit('.', 1)[1].upper()
                    file_size = len(file.read())
                    file.seek(0)  # 將檔案指標重新移回檔案開頭
                #若HTML表單有選擇檔案, 但副檔名不在許可格式清單中, 則禁止新增, 並拋送Exception訊息
                if file and not(file_extension in app.config['ALLOWED_EXTENSIONS']):
                    raise Exception(f"{file_extension}檔案格式不能上傳")
                #若HTML表單有選擇檔案, 但檔案大小超過規定, 則禁止新增, 並拋送Exception訊息
                if file and file_size > app.config['MAX_FILE_SIZE']:
                    raise Exception(f"檔案太大,無法上傳,不能>{app.config['MAX_FILE_SIZE']}Bytes")
            
            sql1 = f'''insert into registration(pid, school_name, team_id, student_name, email, phone, jersey_number) 
                values ('{pid}', '{school}','{team_id}','{name}','{email}','{phone}','{jersey_number}')'''
            conn.execute(sql1)
            
            for iboxname, file in request.files.items():
                # 若HTML表單有選擇檔案, 根據input box name而決定更新資料庫對應檔案欄位, 則新增檔案
                if file.filename:
                    match iboxname.upper():
                        case 'IN_FILE_PID':
                            sql2 ="UPDATE registration SET pid_filename=%s, pid_data=%s WHERE pid=%s"
                        case 'IN_FILE_STUID':
                            sql2 ="UPDATE registration SET st_filename=%s, st_data=%s WHERE pid=%s"
                        case 'IN_FILE_ENROLL':
                            sql2 ="UPDATE registration SET er_filename=%s, er_data=%s WHERE pid=%s"
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

        conn = engine.connect()
        trans = conn.begin()
        try:
            #找出所有 input box 為file type, iboxname存放所有input box name, file 存放檔案資料 
            for iboxname,file in request.files.items():
                if file.filename:
                    file_extension = file.filename.rsplit('.', 1)[1].upper()
                    file_size = len(file.read())
                    file.seek(0)  # 將檔案指標重新移回檔案開頭
            #若HTML表單有選擇檔案, 但副檔名不在許可格式清單中, 則禁止更新, 並拋送Exception訊息
            if file and not(file_extension in app.config['ALLOWED_EXTENSIONS']):
                raise Exception(f"{file_extension}檔案格式不能上傳")
            #若HTML表單有選擇檔案, 但檔案大小超過規定, 則禁止新增, 並拋送Exception訊息
            if file and file_size > app.config['MAX_FILE_SIZE']:
                raise Exception(f"檔案太大,無法上傳,不能>{app.config['MAX_FILE_SIZE']}Bytes")
            sql1 = f'''UPDATE registration SET school_name='{school}',team_id='{team_id}',student_name='{name}',
                email='{email}',phone='{phone}',jersey_number='{jersey_number}',update_time='now()' 
                WHERE pid='{pid}' '''
            conn.execute(sql1)

            for iboxname, file in request.files.items():
                # 若HTML表單有選擇檔案, 根據input box name而決定更新資料庫對應檔案欄位, 則更新檔案
                if file.filename:
                    match iboxname.upper():
                        case 'IN_FILE_PID':
                            sql2 ="UPDATE registration SET pid_filename=%s, pid_data=%s WHERE pid=%s"
                            conn.execute(sql2, file.filename, file.read(), pid)  
                        case 'IN_FILE_STUID':
                            sql2 ="UPDATE registration SET st_filename=%s, st_data=%s WHERE pid=%s"
                            conn.execute(sql2, file.filename, file.read(), pid)
                        case 'IN_FILE_ENROLL':
                            sql2 ="UPDATE registration SET er_filename=%s, er_data=%s WHERE pid=%s"
                            conn.execute(sql2, file.filename, file.read(), pid)    
                # 若HTML表單未選擇檔案, 並且勾選移除已上傳檔案, 則清除資料庫檔案
                elif not(file.filename):
                    if iboxname.upper()=='IN_FILE_PID' and request.form.get('in_rmpidexistfile')=='PID':
                        sql3 ="UPDATE registration SET pid_filename=null, pid_data=null WHERE pid=%s"
                        conn.execute(sql3, pid)
                    elif iboxname.upper()=='IN_FILE_STUID' and request.form.get('in_rmstuexistfile')=='STUID':
                        sql3 ="UPDATE registration SET st_filename=null, st_data=null WHERE pid=%s"
                        conn.execute(sql3, pid)
                    elif iboxname.upper()=='IN_FILE_ENROLL' and request.form.get('in_rmenrollexistfile')=='ENROLL':
                        sql3 ="UPDATE registration SET er_filename=null, er_data=null WHERE pid=%s"
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
@app.route('/showfile/<ftype>/<pid>', methods=['GET','POST'])
def showfile(ftype,pid):
    try:
        match ftype:
            case 'PID':
                fname = 'pid_filename'
                fdata = 'pid_data'
            case 'STUID':
                fname = 'st_filename'
                fdata = 'st_data'
            case 'ENROLL':
                fname = 'er_filename'
                fdata = 'er_data'
        sql = f"select {fname},{fdata} from registration where pid='{pid}'"
        file_data = engine.execute(sql).fetchone()
        file_stream = BytesIO(file_data[fdata])
        file_name = file_data[fname]
        file_extension = file_name.split(".")[-1].upper()
        headers = {}
        match file_extension:
            case 'JPG' | 'JPEG':
                filetype = 'image/jpeg'
            case 'PNG':
                filetype = 'image/png'
            case 'PDF':
                filetype = 'application/pdf'
            case 'HEIC':
                filetype = 'image/heic'
            case _:
                filetype = 'na'
        #flash("Show檔案成功","primary")
        headers = {	'Content-Type': filetype,
                	'Content-Disposition': f'''inline; filename="{quote(file_data[fname])}"'''}
    
    except Exception as e:
        flash(f"Show檔案失敗,{str(e)}","danger")
    # 以下 send_file->download_name 需搭配python v3.11
    #return send_file(file_stream, mimetype=filetype, download_name=(quote(file_data['pid_filename'])), as_attachment=False)
    return Response(file_stream, headers=headers)


if __name__ == '__main__':
   app.run(host='0.0.0.0',port=8000,debug=True)
