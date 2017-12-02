import sqlite3
import json
from datetime import datetime
import pandas as pd

timeframe = "2015-04"
sql_transaction = []

conn = sqlite3.connect("{}.db".format('2015-05'))
c = conn.cursor()

def create_table():
    c.execute("CREATE TABLE IF NOT EXISTS parent_reply(parent_id TEXT PRIMARY KEY, comment_id TEXT UNIQUE, parent TEXT, comment TEXT, subreddit TEXT, unix INT, score INT)")

def format_data(data):
    data = data.replace("\n"," ").replace("\r", " ").replace('"',"'")
    return data

def find_parent(pid):
     try:
        sql = "SELECT comment from parent_reply WHERE comment_id = '{}' LIMIT 1".format(pid) 
        c.execute(sql)
        result = c.fetchone()
        if result != None:
            return result[0]
        else:
            return False
     except Exception as e:
        #print("find_parent :" , e)
        return False
    
def find_existing_score(pid):
    try:
        sql = "SELECT score from parent_reply WHERE parent_id = '{}' LIMIT 1".format(pid) 
        c.execute(sql)
        result = c.fetchone()
        if result != None:
            return result[0]
        else:
            return False
    except Exception as e:
        print("find_parent :" , str(e))
        return False
    
def acceptable(data):
    if len(data.split(' ')) > 50 or len(data) < 1:
        return False
    elif len(data) > 1000:
        return False
    elif data == '[deleted]' or data == '[removed]':
        return False
    else:
        return True

def sql_insert_replace_comment(commentid,parentid,parent,comment,subreddit,time,score):
    try:
        sql = """UPDATE parent_reply SET parent_id = ?,comment_id = ?,parent = ?,comment = ?, subreddit = ?,unix = ?,score = ? WHERE parent_id =?;""".format(parentid,commentid,parent,comment,subreddit,time,score,parentid)
        transaction_bldr(sql)
    except Exception as e:
        print("replace_comment",str(e))

def sql_insert_has_parent(commentid,parentid,parent,comment,subreddit,time,score):
    try:
        sql = """INSERT INTO parent_reply VALUES("{}","{}","{}","{}","{}","{}","{}");""".format(parentid,commentid,parent,comment,subreddit,time,score)
        transaction_bldr(sql)
    except Exception as e:
        print("sql-has-parent",str(e))

def sql_insert_no_parent(commentid,parentid,comment,subreddit,time,score):
    try:
        sql = """INSERT INTO parent_reply(parent_id,comment_id,comment,subreddit,unix,score) VALUES("{}","{}","{}","{}","{}","{}");""".format(parentid,commentid,comment,subreddit,time,score)
        transaction_bldr(sql)
    except Exception as e:
        print("sql-has-no-parent",str(e))
        
def transaction_bldr(sql):
    global sql_transaction
    sql_transaction.append(sql)
    if len(sql_transaction) >1000:
        c.execute('BEGIN TRANSACTION')
        for s in sql_transaction:
            try:
                c.execute(s)
            except:
                pass
            conn.commit()
            sql_transaction = []
    
if __name__ == "__main__":
    create_table()
    
    row_counter = 0
    paired_rows = 0
    
    with open("reddit_data/{}/RC_{}/RC_{}".format(timeframe.split('-')[0], timeframe,timeframe), buffering = 1000) as f:
        for row in f:
            row_counter += 1
            row = json.loads(row)
            parent_id = row['parent_id']
            body = format_data(row['body'])
            created_utc = row['created_utc']
            score = row['score']
            subreddit = row['subreddit']
            comment_id = row['name']
            parent_data = find_parent(parent_id)
            
            if score >= 2:
                if acceptable(body):
                    existing_comment_score = find_existing_score(parent_id)
                    if existing_comment_score:    
                        if score > existing_comment_score:
                            sql_insert_replace_comment(comment_id, parent_id, parent_data, body, subreddit, created_utc, score)
                    else:
                        if parent_data:
                            sql_insert_has_parent(comment_id, parent_id, parent_data, body, subreddit, created_utc, score)
                            paired_rows +=1
                        else:
                            sql_insert_no_parent(comment_id, parent_id, body, subreddit, created_utc, score)
                            
                        
            if row_counter % 1000 == 0:
                print("Total rows read:{},Paired_rows:{},Time:{}".format(row_counter,paired_rows,str(datetime.now())))
                    
        

    
timeframes = ['2015-05']

for timeframe in timeframes:
    connection = sqlite3.connect('{}.db'.format(timeframe))
    c = connection.cursor
    limit = 5000
    last_unix = 0
    cur_length = limit
    counter = 0
    test_done = False
    while cur_length == limit:
        df = pd.read_sql("SELECT * FROM parent_reply WHERE unix > {} AND parent NOT NULL AND score > 0 ORDER BY unix ASC LIMIT {}".format(last_unix,limit),connection)
        last_unix = df.tail(1)['unix'].values[0]
        cur_length = len(df)
        if not test_done:
            with open("test.from",'a',encoding = ' utf8') as f:
                for content in df['parent'].values:
                    f.write(content+'\n')
            with open("test.to",'a',encoding = ' utf8') as f:
                for content in df['comment'].values:
                    f.write(content+'\n') 
            
            test_done = True
        else:
            with open("train.from",'a',encoding = ' utf8') as f:
                for content in df['parent'].values:
                    f.write(content+'\n')
            with open("train.to",'a',encoding = ' utf8') as f:
                for content in df['comment'].values:
                    f.write(content+'\n') 
            
        counter += 1
        print(counter * 5000)
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
