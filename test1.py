import pandas as pd

df = pd.read_excel('template.xlsx',converters={'tel': str})
print(df)
df = df.drop('id', axis=1).drop('學生證', axis=1).drop('身份證', axis=1).drop('在學證明', axis=1)
#print(df)
df = df.rename(columns={'校名': 'school_name', '姓名': 'student_name','tel': 'phone', '背號': 'jersey_number'})
print(df)
#df.reset_index()
#row = df.iloc[0:]
#for data in row:
#    print(df.loc[data])
from sqlalchemy import create_engine

engine = create_engine('postgresql://admin:123456@127.0.0.1:5432/postgres')

#從資料庫抓資料
sql = "select * from registration_test" 
sql_data = pd.DataFrame(engine.execute(sql))
print("Before save to DB")
print(sql_data)
#sql_data = engine.execute(sql)
#for data in sql_data:
#    print(data[0],data[1],data[2],data[3])

#送資料到資料庫
i = 0
#sql = f'''insert into registration_test (
#    school_name, student_name, email, phone, jersey_number)
#    VALUES ('{df.loc[i, '校名']}', '{df.loc[i, '姓名']}', '{df.loc[i, 'email']}', 
#    '{df.loc[i, 'tel']}', '{df.loc[i, '背號']}')'''
#engine.execute(sql)

#送資料到資料庫
df.to_sql('registration_test', engine, index=False,if_exists='append')

#從資料庫抓資料
sql = "select * from registration_test" 
sql_data = pd.DataFrame(engine.execute(sql))
print("After save to DB")
print(sql_data)
