import os
import math
import shutil
import string
import sys
import json
import random
from PIL import Image
import re
import time
from psycopg2.extras import Json 
from datetime import datetime

currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)

from tbclibs.langdetect_class import LangDetect
from tbclibs.book_utils import extract_meta_from_book, TextLayerExtractorClass, extract_images_class, \
    TextLayerExtractorClass, TextlayerMetaExtractor
from tbclibs.websearch_class import websearch_class


from tbclibs.pgdb_class import pgdb

def  get_tbc_id():
    pg = pgdb()
    id=pg.fetchone("SELECT nextval('tbc.books_id_seq')")[0]
    pg.close()
    return id



class TBC:
    storage_base = '/data'

    def __init__(self, db):
        self.db = db

    def  get_new_tbc_id(self):
        pg = self.db
        id=pg.fetchone("SELECT nextval('tbc.books_id_seq')")[0]
        return id

    def get_id_by_hash(self, md5):
        sql = "select * from books where md5=%s and reload=0"
        return self.db.fetchone(sql, [md5])

    def get_book_by_hash_dict(self, md5):
        sql = "select * from books where md5=%s and reload=0"
        return self.db.fetchone_dict(sql, [md5])

    def isReload(self, md5):
        sql = "select id,reload from books where md5=%s"
        return self.db.fetchone(sql, [md5])

    def get_locator(self, id):
        th = math.floor(id / 1000) * 1000
        print(f"th={th}")
        sql = "select location from book_locator where th=%s"
        row = self.db.fetchone(sql, [th])
        if len(row) == 0:
            print(f"th={th}")
            raise NameError(f"Не определена локация для id = {id}")
        return row[0]


    def import_file(self, params):

        def shorten_string(input_string, max_length=500):
            names = input_string.split(',')  # Разделяем строку по запятой
            shortened_string = ""
            
            for name in names:
                name = name.strip()  # Убираем пробелы вокруг имени
                # Проверяем, добавление очередного имени не превысит 500 символов
                if len(shortened_string) + len(name) + (1 if shortened_string else 0) < max_length:
                    if shortened_string:  # Если не пустая строка, добавляем запятую
                        shortened_string += ', '
                    shortened_string += name
                else:
                    break  # Если превышает 500 символов, прекращаем добавление

            return shortened_string
        if not 'import_file' in params:
            raise NameError(f"Опущен обязательный парамет:  import_file")
        if not os.path.isfile(params['import_file']):
            raise NameError(f"при импорте нет файла {params['import_file']}")
        if 'md5' not in params:
            raise NameError(f"нужно передать md5")
        pars = []
        vals = []
        p = []
        data = {}



        file = os.path.basename(params['import_file'])
        (file_name, file_ext) = os.path.splitext(file)
        if 'filename' not in params:
            params['filename'] = file_name

        if 'extension' not in params:
            params['extension'] = file_ext.strip('.').strip().lower()

        file_size = os.path.getsize(params['import_file'])
        pars.append('filesize')
        vals.append(file_size)
        p.append('%s')
        
        # Смотрим не восстановление ли это потерянной книги
        sql = "select * from books where md5=%s"
        reload_row = self.db.fetchone_dict(sql, [params['md5']])
        if reload_row and reload_row["reload"] == 1:
            reload=True
        else:
            reload=False

        if reload:
            #book = self.get_id_by_hash(params['md5'])
            new_id = reload_row["id"]
            pars.append('reload')
            vals.append(0)       

            # select nextval('tbc.books_id_seq')
            # sql = "select max(id) from books"

            # плохо работает в многопотоке
            # sql = "select nextval('books_id_seq')"
            # id = self.db.fetchone(sql)[0]

            # print("start get ID", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            # sql = f"""
            #     with next_task as (                                                                                                                                                                                                                                                   
            #     select id from books_ids_pool where status = 0 order by id limit 1 
            #     for update skip locked )                                                                                                                                            
            #     update books_ids_pool  set status = 1 from next_task  
            #     where books_ids_pool.id = next_task.id                                                                                                                      
            #     returning next_task.id
            #     """
            # row = self.db.fetchone(sql)
            # self.db.commit()
            # print("End get ID", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            # if row:
            #     new_id=row[0]
            #     print(f"NEW ID = ", new_id)
                
        else:
            #new_id = self.get_new_tbc_id()
            new_id = self.db.fetchone("SELECT nextval('tbc.books_id_seq')")[0]
            #new_id = int(id) + 1
            pars.append('id')
            vals.append(new_id)
            p.append('%s')

        
        ths = math.floor(new_id / 1000) * 1000
        pars.append('ths')
        vals.append(ths)
        p.append('%s')
        #locator = self.get_locator(new_id)

        
        

        if reload:
            locator_id=reload_row["locator_id"]
        else:
            locator_id = self.db.fetchone_dict("select name from storage_pools where is_active=True")["name"]
            #book_locator_row = self.db.fetchone_dict("select * from book_locator where th=%s", [ths])
            #locator_id=book_locator_row["pool"]
            pars.append('locator_id')
            vals.append(locator_id)
            p.append('%s')


        if reload:
            location = os.path.join(self.storage_base, reload_row["locator_id"], str(ths), str(new_id))
        else:
            location = os.path.join(self.storage_base, locator_id, str(ths) , str(new_id))


        if 'title' in params and len(params['title']) > 1000:
            params['title'] = params['title'][0:1000]
        for par in ['filename', 'extension', 'src_type', 'src_id', 'library', 'src_add_algorithm', 'year', 'num',
                    'book_type', 'pages', 'title', 'author', 'reload', 'md5', 'isbn', 'descr', 'params_json',
                    'textlayer_enable', 'textlayer_size', 'cover_small', 'flags', 'publisher', 'parent_id']:
            if par in params:
                # print(f"+++par: {par}")
                if par == 'isbn' and len(params[par]) > 300:
                    params[par] = params[par][0:300]
                if par == 'pages' and len(params[par]) >100:
                    params[par]=params[par][:100]
                # if par == "params_json":
                #     params[par] = json.dumps(params[par], indent=4, sort_keys=True, default=str)
                # if par == "flags" and params[par]:
                #     #params[par] = json.dumps(params[par], sort_keys=True, default=str)
                #     params[par] = json.dumps(params[par])
                #     #params[par] = Json(params[par])
                if par == "publisher" and params[par]:
                    if len(params[par])>500:
                        if "," in params[par]:
                            params[par]=shorten_string(params[par],500)
                        else:
                            params[par]=params[par][:500]

                pars.append(par)
                vals.append(params[par])
                p.append('%s')



        ld = LangDetect()
        try:
            str4detect = ''
            for par in ['title', 'author', 'filename']:
                if par in params:
                    str4detect += " " + params[par]
            lang = ld.detect(f"{str4detect}")
        except Exception as e:
            print("error detect : " + str(e))
            lang = None
        print(f"detectied lang: {lang}")

        pars.append('download_hash')
        vals.append(''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(15)))
        p.append('%s')

        if lang:
            pars.append('detected_lang')
            vals.append(lang)
            p.append('%s')
            if lang in ['russian', 'english', 'bulgarian']:
                if lang == 'bulgarian':
                    lang = 'russian'
                pars.append("search_lang_regconfig")
                vals.append(lang)
                p.append('%s')
                if lang == 'russian':
                    pars.append("search_updated")
                    vals.append(1)
                    p.append('%s')

        print(f"pars: ", pars)
        print(f"vals: ", vals)
        print(f"p: ", p)

        #sys.exit()
        if reload:
            update_pars = []
            for par in pars:
                update_pars.append(f"{par}=%s")

            sql = "update books set {} where id={}".format(",".join(update_pars), new_id)
            self.db.execute(sql, vals)
        else:
            sql = "insert into books ({}) values ({})".format(",".join(pars), ",".join(p))
            print(sql)
            print(vals)
            self.db.execute(sql, vals)
            # if 'flags' in params:
            #     self.db.execute("update books set flags=%s where id=%s", [params['flags'], new_id])

        print(f"new_id: {new_id}")

        print(f"move file to {location}")



        os.makedirs(location, exist_ok=True)

        if 'filename' in params and 'extension' in params:
            short_filename = f"{params['filename']}.{params['extension']}"
        else:
            short_filename = f"{file}"
        target = f"{location}/{short_filename}"

        MAX_LEN = 100
        if len(target) > MAX_LEN:
            max_len = MAX_LEN - len(location) - 1
            (file_name, file_ext) = os.path.splitext(short_filename)
            file_ext = file_ext.replace(".", "")
            file_name = file_name[0:max_len]
            short_filename = file_name + "." + file_ext
            target = f"{location}/{short_filename}"
            print(f"Shorted name: {target}")
            params['filename'] = file_name
            params['extension'] = file_ext
            self.db.execute("update books set filename=%s where id=%s", [file_name, new_id])
            self.db.commit()
            # sys.exit()
            # time.sleep(3)

        print(f"target: {target}")



        # sys.exit()
        # flags = {}
        # if 'flags' in params:
        #     flags = json.loads(params['flags'])
        # print(f"--->>>> {flags}")
        import_type = 'move'
        if 'import_type' in params:
            import_type = params['import_type']
        if import_type == 'move':
            shutil.move(params['import_file'], target)
        elif import_type == 'copy':
            shutil.copy(params['import_file'], target)
        else:
            print(f"!!! import_type ont recognised : {import_type}")
            sys.exit()
        # if 'textlayer_file' in params:
        #     shutil.copy(params['textlayer_file'], f"{location}/textlayer.txt")
        #     flags['textlayer_file'] = 'textlayer.txt'
        #     if 'textlayer_enable' in params:
        #         flags['textlayer_enable'] = params['textlayer_enable']
        #     if 'textlayer_size' in params:
        #         flags['textlayer_size'] = params['textlayer_size']

        if 'cover_file' in params:
            shutil.copy(params['cover_file'], f"{location}/cover_small.jpg")

        # shutil.copyfile(pars['import_file'], )
        # self.db.commit()
        # new_book = self.get_book_by_hash_dict(params['md5'])
        # f = new_book['flags']
        # if not f:
        #     f = {}
        # f = f.update(flags)
        # self.db.execute("update books set flags=%s where id=%s", [json.dumps(flags), new_id])
        self.db.commit()

        new_book = self.get_book_by_hash_dict(params['md5'])

        if not os.path.isfile(f"{location}/{new_book['filename']}.{new_book['extension']}"):
            raise NameError(f"Файл не найден в новом месте {location}/{new_book['filename']}.{new_book['extension']}")
        print(params)
        if reload:
            print("reload")
            self.db.execute("delete from books_images where tbc_id=%s", [new_id])
            self.db.execute("delete from books_images_cache where tbc_id=%s", [new_id])
            self.db.execute("delete from books_textlayers where tbc_id=%s", [new_id])
            self.db.execute("delete from books_textlayers_cache where tbc_id=%s", [new_id])
            self.db.execute("delete from finereader_queue where tbc_id=%s", [new_id])

            # sys.exit()
        sql = "delete from books_ids_pool where id=%s"
        self.db.execute(sql, [new_id])
        self.db.commit()
        return self.db.fetchone_dict("select * from books where id=%s", [new_id])
