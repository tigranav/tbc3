class pgq_class:
    def __init__(self, db, table_name, id_column_name='id', status_column_name='pgq_status', filter=" 1=1 "):
        self.db = db
        self.table_name = table_name
        self.id_column_name = id_column_name
        self.status_column_name = status_column_name
        self.statuses = {"inqueue": 0, "processing": 1, 'completed': 2}
        self.filter = filter

    def get_task(self):
        sql = f"""with next_task as (                                                                                                                                                                                                                                                   
        select id from {self.table_name} where {self.status_column_name} = {self.statuses['inqueue']} 
        and {self.filter}
        order by {self.id_column_name} limit 1 
        for update skip locked )                                                                                                                                            
        update {self.table_name} set {self.status_column_name} = {self.statuses['processing']} from next_task  
        where {self.table_name}.{self.id_column_name} = next_task.{self.id_column_name}                                                                                                                      
        returning {self.table_name}.{self.id_column_name}"""

        row = self.db.fetchone(sql)
        self.db.commit()
        if row:
            return row[0]
        return False

    def complete_task(self, id):
        sql = f"update {self.table_name} set {self.status_column_name}={self.statuses['completed']} " \
              f"where {self.id_column_name}=%s"
        self.db.execute(sql, [id])
        self.db.commit()
