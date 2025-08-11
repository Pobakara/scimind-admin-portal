import sqlite3

DB_PATH = 'data/SciMindMain.db'

con = sqlite3.connect(DB_PATH)
with open('dump.sql', 'w', encoding='utf-8') as f:
    for line in con.iterdump():
        f.write('%s\n' % line)
con.close()

def print_schema():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]
    print('Database tables:')
    for table in tables:
        print(f'\nTable: {table}')
        cursor.execute(f'PRAGMA table_info({table});')
        columns = cursor.fetchall()
        for col in columns:
            print(f'  {col[1]} ({col[2]})')
    conn.close()

if __name__ == '__main__':
    print_schema()
