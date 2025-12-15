import psycopg2
import psycopg2.extras

# with pgdb(user, database, password, host, port) as db:
class pgdb:
    PG_HOST = '192.168.0.50' 
    PG_PORT = 5433
    PG_USER = 'tbc'
    PG_PASSWORD = 'tbcpass'
    PG_DB = 'books'    

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.con.close()

    def __init__(self):
        self.con = psycopg2.connect(user=self.PG_USER, database=self.PG_DB,
                password=self.PG_PASSWORD, host=self.PG_HOST,  port=self.PG_PORT, application_name="")
        self.cur = self.con.cursor()

    def convert_to_dict(self, columns, results):
        allResults = []
        columns = [col.name for col in columns]
        if type(results) is list:
            for value in results:
                allResults.append(dict(zip(columns, value)))
            return allResults
        elif type(results) is tuple:
            allResults.append(dict(zip(columns, results)))
            return allResults

    def build_dict(self, cursor, row):
        x = {}
        for key, col in enumerate(cursor.description):
            x[col[0]] = row[key]
        return x 

    def cursor(self):
        self.cur = self.con.cursor() 
        return self.cur

    def fetchone(self, sql, pars=[]):
        self.cur.execute(sql, pars)
        return self.cur.fetchone()

    def fetchall(self, sql, pars=[]):
        self.cur.execute(sql, pars)
        return self.cur.fetchall()
    
    def fetchone_dict(self, sql, pars=[]):
        self.cur.execute(sql, pars)
        row = self.cur.fetchone()
        if row:
            row = self.build_dict(self.cur, row)
            return row
        else:
            return False

    def fetchall_dict(self, sql, pars=[]):                                                                                                              
        self.cur.execute(sql, pars)
        allrows = []
        for row in  self.cur.fetchall():
            row = self.build_dict(self.cur, row)
            allrows.append(row)
        return allrows

    def commit(self):
        self.con.commit()

    def execute(self, sql, pars=[]):
        self.cur.execute(sql, pars)

    def execute_and_return(self, sql, pars=[]):
        self.cur.execute(sql, pars)
        return self.cur.fetchone()[0]

    def close(self):
        self.con.close()
