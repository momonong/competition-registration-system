#!/usr/bin/env python
from flask import Flask, render_template, redirect, url_for, request, flash, Response
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_security import UserMixin, RoleMixin, roles_accepted, Security, SQLAlchemySessionUserDatastore 
from sqlalchemy import create_engine
from io import BytesIO
from urllib.parse import quote
from web5 import app as web5_app

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://admin:123456@127.0.0.1:5432/sport'
app.config['SECRET_KEY'] = 'fi13dE9fafkd9a0afklm81WEEd'
app.config['SECURITY_PASSWORD_SALT'] = "uY939qAAZiqi939dfGQR2sDG9333SIkjWu"
app.config['SECURITY_REGISTERABLE'] = True
app.config['SECURITY_SEND_REGISTER_EMAIL'] = False
app.config['ALLOWED_EXTENSIONS'] = {'PDF', 'JPG', 'JPEG', 'PNG', 'HEIC'}
app.config['MAX_FILE_SIZE'] =  16 * 1024 * 1024  # 16MB 的位元組

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'mylogin'

engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])

# 自定義未授權處理程序
@login_manager.unauthorized_handler
def unauthorized():
    return redirect(url_for('mylogin'))

# Setup User Model and link with database
roles_users = db.Table('roles_users',
        db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
        db.Column('role_id', db.Integer(), db.ForeignKey('role.id'))) 

class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    email = db.Column(db.String, unique=True)
    password = db.Column(db.String(255), nullable=False, server_default='')
    active = db.Column(db.Boolean())
    name = db.Column(db.String)
    team_id = db.Column(db.String)
    # backreferences the user_id from roles_users table
    roles = db.relationship('Role', secondary=roles_users, backref='roled')
 
class Role(db.Model, RoleMixin):
    __tablename__ = 'role'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String)
 
# load users, roles for a session
user_datastore = SQLAlchemySessionUserDatastore(db.session, User, Role)
security = Security(app, user_datastore)


# Load User
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Routes
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/admin')
@login_required
@roles_accepted('admin')
def admin_dashboard():
        return '系統管理者 Dashboard (Requires admin role)'
    
@app.route('/gamemanager')
@login_required
@roles_accepted('admin', 'gamemanager')
def gamemanager_dashboard():
    return '比賽主辦管理者 Dashboard (Requires gamemanager role)'

@app.route('/user')
@login_required
@roles_accepted('admin', 'gamemanager', 'user')
def user_dashboard():
        return '參賽隊伍 Dashboard (Requires user role)'

@app.route('/mylogin', methods=['GET', 'POST'])
def mylogin():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()
        if user and user.password == password:
            login_user(user)
            flash('登入成功！', 'success')
            return redirect(url_for('home'))
        else:
            flash('email 或 password 錯誤！請重試！', 'danger')

    return render_template('mylogin.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('登出成功！', 'success')
    return redirect(url_for('home'))

# member data database CRUD
@app.route('/editmember/', methods=['GET', 'POST'])
@app.route('/editmember/<team_id>', methods=['GET', 'POST'])
@login_required
@roles_accepted('admin', 'gamemanager', 'user')
def editmember(team_id=''):
    if current_user.has_role('admin') or current_user.has_role('gamemanager'):
        condition = ''
    else:    
        condition = f"WHERE team_id='{current_user.team_id}'"
    sql = f'''SELECT pid,school_name,team_id,student_name,email,phone,jersey_number,
        CASE WHEN pid_data IS NOT NULL THEN '_Y' ELSE '' end as 身,
        CASE WHEN st_data IS NOT NULL THEN '_S' ELSE '' end as 學, 
        CASE WHEN er_data IS NOT NULL THEN '_E' ELSE '' end as 在 
        FROM registration {condition} ORDER BY update_time desc'''
    data = engine.execute(sql)
    column_names = data.keys()
    return render_template('output5.html', outdata=data, outheaders=column_names)

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
    return redirect(url_for("editmember"))

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
    
    return redirect(url_for("editmember"))

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

    return redirect(url_for("editmember"))

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
    app.run(debug=True)

