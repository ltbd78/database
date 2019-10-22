import pymysql
import src.data_service.dbutils as dbutils
import src.data_service.RDBDataTable as RDBDataTable
import copy

# The REST application server app.py will be handling multiple requests over a long period of time.
# It is inefficient to create an instance of RDBDataTable for each request.  This is a cache of created
# instances.
_db_tables = {}

_default_connect_info = {"host": "localhost",
              "port": 3306,
              "user": "root",
              "password": "simplex78",
              "cursorclass": pymysql.cursors.DictCursor}


def get_rdb_table(table_name, db_name, key_columns=None, connect_info=None):
    """
    :param table_name: Name of the database table.
    :param db_name: Schema/database name.
    :param key_columns: This is a trap. Just use None.
    :param connect_info: You can specify if you have some special connection, but it is
        OK to just use the default connection.
    :return:
    """
    if connect_info is None:
        _connect_info = copy.deepcopy(_default_connect_info)
        _connect_info['db'] = db_name
    global _db_tables
    # We use the fully qualified table name as the key into the cache, e.g. lahman2019clean.people
    key = db_name + "." + table_name
    # Have we already created and cache the data table?
    result = _db_tables.get(key, None)
    # We have not yet accessed this table.
    if result is None:
        # Make an RDBDataTable for this database table.
        result = RDBDataTable.RDBDataTable(table_name, db_name, key_columns=key_columns, connect_info=_connect_info)
        # Add to the cache.
        _db_tables[key] = result
    return result


def get_tables(db_name):
    _connect_info = copy.deepcopy(_default_connect_info)
    _connect_info['db'] = db_name
    _conn = pymysql.connect(**_connect_info)
    sql = "show tables"
    res, d = dbutils.run_q(sql, conn=_conn)
    return d


def get_databases():
    """
    :return: A list of databases/schema at this endpoint.
    """
    _conn = pymysql.connect(**_default_connect_info)
    sql = "show databases"
    res, d = dbutils.run_q(sql, conn=_conn)
    return d
