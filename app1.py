#!/usr/bin/env python
from flask import Flask, render_template, redirect, url_for, request, flash, Response
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_security import UserMixin, RoleMixin, roles_accepted, Security, SQLAlchemySessionUserDatastore 
from sqlalchemy import create_engine
from io import BytesIO
from urllib.parse import quote
import pandas as pd


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://admin:123456@127.0.0.1:5432/sport'
app.config['SECRET_KEY'] = 'fi13dE9fafkd9a0afklm81WEEd'
app.config['SECURITY_PASSWORD_SALT'] = "uY939qAAZiqi939dfGQR2sDG9333SIkjWu"
app.config['SECURITY_REGISTERABLE'] = True
app.config['SECURITY_SEND_REGISTER_EMAIL'] = False
app.config['ALLOWED_EXTENSIONS'] = {'PDF', 'JPG', 'JPEG', 'PNG', 'HEIC'}
app.config['MAX_FILE_SIZE'] =  16 * 1024 * 1024  # 16MB 的位元組
app.config['GAME'] = {'賽事名稱':'2023興傳盃公益籃球邀請賽', '主辦':'國立中興大學EMBA校友會',
                      '協辦':'國立中興大學EMBA學生會、國立中興大學EMBA辦公室',
                      '執行':'國立中興大學EMBA籃球社',
                      '比賽地點':'國立中興大學體育館B1及2F籃球場（台中市南區興大路145號）',
                      '比賽開始日期':'2023/8/19','比賽結束日期':'2023/8/20',
                      '參賽組別':{'挑戰組(不限齡)':'最多16隊','菁英組(43歲以上)':'最多8隊'},
                      '開始報名日期':'即日起','截止報名日期':'2023/5/31 晚上24:00',
                      '選手之夜報名截止時間':'2023/6/9 晚上24:00',
                      '賽事狀態':'報名截止','賽事管理員':'vicfenny@gmail.com'}

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
    game_content = app.config['GAME']
    return render_template('home.html',game_content=game_content)

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

@app.route('/gamerule')
def gamerule():
    return render_template('rule.html')

# query all teams 
@app.route('/get_teams/<game_id>', methods=['GET', 'POST'])
@login_required
@roles_accepted('admin', 'gamemanager', 'user')
def get_teams(game_id):
    if current_user.has_role('admin') or current_user.has_role('gamemanager'):
        condition = ''
    else:    
        condition = f" AND contact_pid='{current_user.id}'"
    sql = f'''SELECT team_id, team_name 報名單位, group_id 參賽組別, status 狀態, qualified 是否合格 FROM team 
        WHERE game_id='{game_id}' {condition} '''
    df = pd.DataFrame(engine.execute(sql))
    df.index += 1 
    # 加'報名單位' hyperlink 至 editteam_member 頁面
    df['報名單位'] = df.apply(lambda x: f"<a href={url_for('editteam_member',team_id=(x.team_id))}>{x.報名單位}</a>", axis=1)
    df = df.drop('team_id', axis=1)
    # 將dataframe 的 是否合格 column 內容為false 置換成“否”, true 置換成“是”,
    df['是否合格'] = df['是否合格'].apply(lambda x: '是' if x else '否')
    # 將html table head 文字靠左對齊
    data_html = df.to_html(classes=['table table-border table-striped'], escape=False).replace('<th', '<th style="text-align: left;"')
        
    return render_template('show_teams.html', outgame_id=game_id, outdata=data_html)

# member data database CRUD
def get_teamid_fm_pid(pid):
    sql = f'''SELECT team_id FROM team WHERE {current_user.id}=team.contact_pid'''
    data = engine.execute(sql).fetchone()
    return data['team_id']

@app.route('/editteam_member/', methods=['GET', 'POST'])
@app.route('/editteam_member/<int:team_id>', methods=['GET', 'POST'])
@login_required
@roles_accepted('admin', 'gamemanager', 'user')
def editteam_member(team_id=''):
    if current_user.has_role('admin') or current_user.has_role('gamemanager'):
        condition = ''
    else:
        team_id = get_teamid_fm_pid(current_user.id) 
        condition =  f"WHERE team_num={team_id}"
    sql = f'''SELECT pid,school_name,team_id,student_name,email,phone,jersey_number,
        CASE WHEN pid_data IS NOT NULL THEN '_Y' ELSE '' end as 身,
        CASE WHEN st_data IS NOT NULL THEN '_S' ELSE '' end as 學, 
        CASE WHEN er_data IS NOT NULL THEN '_E' ELSE '' end as 在
        FROM registration {condition} ORDER BY team_num, update_time desc'''
    data = engine.execute(sql)
    column_names = data.keys()
    sql_team = f'''SELECT A.team_id,B.id,team_name 報名單位,name 聯絡人,email 電子郵件,group_id 參賽組別,coach 教練,head_coach 領隊,team_captain 隊長,
            status 狀態,CASE WHEN qualified IS true THEN '是' ELSE '否' END as 是否合格
            FROM team A INNER JOIN "user" B ON B.id=A.contact_pid WHERE A.team_id={team_id} '''
    team_data = engine.execute(sql_team).fetchone()
    team_column_names = team_data.keys()
    return render_template('output6.html', outdata=data, outheaders=column_names,outteam=team_data,outteamheader=team_column_names)


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
        FROM registration {condition} ORDER BY team_id, update_time desc'''
    data = engine.execute(sql)
    column_names = data.keys()
    return render_template('output5.html', outdata=data, outheaders=column_names)

# 新增人員
@app.route('/add_person', methods=['GET','POST'])
def add_person():
    if request.method == "POST":
        pid = request.values['in_pid'].upper().strip()  #去除頭尾空白字元
        school = request.values['in_school'].strip()
        team_id = request.values['in_teamid'].strip()
        name = request.values['in_name'].strip()
        email = request.values['in_email'].lower().strip()
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
            team_num = get_teamid_fm_pid(current_user.id)
            sql1 = f'''insert into registration(pid, school_name, team_id, student_name, email, phone, team_num, jersey_number) 
                values ('{pid}', '{school}','{team_id}','{name}','{email}','{phone}',{team_num},'{jersey_number}')'''
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
    return redirect(url_for("editteam_member"))

#修改人員資料
@app.route('/edit_person/<pid>', methods=['GET','POST'])
def edit_person(pid):
    if request.method == "POST":
        school = request.values['in_school'].strip()
        team_id = request.values['in_teamid'].strip()
        name = request.values['in_name'].strip()
        email = request.values['in_email'].lower().strip()
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
                email='{email}',phone='{phone}',jersey_number='{jersey_number}' update_time='now()' 
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
    
    return redirect(url_for("editteam_member"))

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

    return redirect(url_for("editteam_member"))

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
    app.run(host='0.0.0.0', port=8000, debug=True)

