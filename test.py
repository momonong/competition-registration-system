import pandas as pd

#test 2
df = pd.read_excel('template.xlsx')
df.reset_index()
row = df.iloc[0:]
for data in row:
    print(df.loc[data])
from sqlalchemy import create_engine

engine = create_engine('postgresql://admin:123456@127.0.0.1:5432/postgres')

#從資料庫抓資料
'''sql = "select * from registration_test"
sql_data = pd.DataFrame(engine.execute(sql))
print(sql_data)'''

#送資料到資料庫
i = 0
sql = f'''insert into registration_test (
    school_name, student_name, email, phone, jersey_number)
    VALUES ('{df.loc[i, '校名']}', '{df.loc[i, '姓名']}', '{df.loc[i, 'email']}', 
    '{df.loc[i, 'tel']}', '{df.loc[i, '背號']}')'''
#engine.execute(sql)
