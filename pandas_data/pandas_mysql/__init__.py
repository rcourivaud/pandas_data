import pandas as pd
import sqlalchemy
from pandas.io import sql


class PandasMySQL:
    def __init__(self, host="localhost", port=3306, usr="root", pwd=""):
        """
        :param host: MySQL Host
        :param port:
        :param usr:
        :param pwd:
        """
        self.host = host
        self.port = port
        self.user = usr
        self.pwd = pwd
        print("MySQL url : mysql://{0}:{1}@{2}:{3}".format(self.user, self.pwd, self.host, self.port))

    def execute_stored_procedure(self, proc_name, params, base):
        """
        Excecute stored procedure on table selected with some parameters

        :param proc_name:
        :param params:
        :param base:
        :return:
        """
        conn = self.connect_to_database(db=base)
        connection = conn.connect()
        result = connection.execute(proc_name, params)
        connection.close()
        return result

    def connect_to_database(self, db):
        """
        Connect to MySQL Database and return engine to use it in pandas librairy

        :param db:
        :return:
        """
        try:
            engine = sqlalchemy.create_engine(
            'mysql://{0}:{1}@{2}:{3}/{4}?charset=utf8'.format(self.user, self.pwd, self.host,
                                                              str(self.port), db), echo=False)
        except:
            try:
                engine = sqlalchemy.create_engine(
                    'mysql+mysqldb://{0}:{1}@{2}:{3}/{4}?charset=utf8'.format(self.user, self.pwd, self.host,
                                                                              str(self.port), db), echo=False)
            except:
                engine = sqlalchemy.create_engine(
                    'mysql+mysqlconnector://{0}:{1}@{2}:{3}/{4}?charset=utf8'.format(self.user, self.pwd, self.host,
                                                                                     str(self.port), db), echo=False)
        return engine

    def open_csv_file(self, path, **args):
        """
        :param path:
        :param args:
        :return:
        """
        return pd.read_csv(path, args)

    def read_table(self, db, table_name):
        """
        Read table from database
        :param db:
        :param table_name:
        :return: Pandas dataframe
        """
        engine = self.connect_to_database(db=db)
        df = pd.read_sql_table(table_name=table_name, con=engine)
        engine.connect().connection.close()
        return df

    def read_table_from_query(self, db, query):
        """
        :param db:
        :param query:
        :return:
        """
        engine = self.connect_to_database(db=db)
        df = pd.read_sql_query(query, engine)
        engine.connect().connection.close()
        return df

    def execute_query(self, db, query):
        assert isinstance(query, str)
        #assert not query.lower().startswith("select")
        conn = self.connect_to_database(db=db).connect()
        result = conn.execute(query)
        conn.connection.close()
        return result

        
    def to_csv(self, dataframe, file_path, encoding="utf-8", index=False):
        """
        :param encoding:
        :param index:
        :param dataframe:
        :param file_path:
        :return:
        """
        dataframe.to_csv("./" + file_path, encoding=encoding, index=index)

    def to_database(self, dataframe, name, db, if_exists, chunksize=50000, dtypes=None, index=False, save_if_error=False):
        """
        Upload dataframe to table in selected SQL database
        """

        if dtypes is None:
            dtypes = {}
        conn = self.connect_to_database(db=db)
        if dataframe.shape[0] != 0:
            print(
                "Writing to table : " + name + " and database : " + db + " if exists : " + if_exists + " shape : " + str(
                    dataframe.shape))
            try:
                dataframe.to_sql(name=name,
                                 con=conn,
                                 if_exists=if_exists,
                                 chunksize=chunksize,
                                 dtype=dtypes,
                                 index=index)
                conn.connect().connection.close()
            except Exception as e:
                print(e)
                print("Bug in uploading dataframe, it has been writen in error_uploading{}_{}.csv".format(db, name))
                if save_if_error:
                    self.to_csv(dataframe=dataframe, file_path="error_uploading{}_{}.csv".format(db, name), index=index)

        else:
            print("Dataframe is empty")

    @staticmethod
    def create_dtypes_str(df, max_size_string=None):
        """
        Basic sqlalchemy connection upload string with text type.
        Calculate optimum size for SQL columns

        :param df:
        :param max_size_string:
        :return:
        """
        df_types = {n: str(t) for n, t in zip(df.columns, df.dtypes.values)}

        dstr = {n: str(t) for n, t in zip(df.columns, df.dtypes.values) if t == "object"}
        if max_size_string:
            d_size_str = {n: (df[n].str.len().max() if df[n].str.len().max() < max_size_string else max_size_string) for
                          n, t in dstr.items()}
        else:
            d_size_str = {n: df[n].str.len().max() for n, t in dstr.items()}

        return {n: sqlalchemy.types.VARCHAR(v) for n, v in d_size_str.items()}

    def drop_table(self, name, db):
        """
        Drop selected Table

        :param name:
        :param db:
        :return:
        """
        conn = self.connect_to_database(db=db)
        print("Drop table : " + name + " and database : " + db)
        connec = sql.execute('DROP TABLE IF EXISTS %s' % name, conn)
        connec.close()
