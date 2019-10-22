import pymysql
import logging

logger = logging.getLogger()


def get_connection(connect_info):
    """
    :param connect_info: A dictionary containing the information necessary to make a PyMySQL connection.
    :return: The connection. May raise an Exception/Error.
    """
    cnx = pymysql.connect(**connect_info)
    return cnx


def run_q(sql, args=None, fetch=True, cur=None, conn=None, commit=True):
    """
    Helper function to run an SQL statement.
    This is a modification that better supports HW1. An RDBDataTable MUST have a connection specified by
    the connection information. This means that this implementation of run_q MUST NOT try to obtain
    a default connection.
    :param sql: SQL template with placeholders for parameters. Cannot be NULL.
    :param args: Values to pass with statement. May be null.
    :param fetch: Execute a fetch and return data if TRUE.
    :param conn: The database connection to use. This cannot be NULL, unless a cursor is passed.
        DO NOT PASS CURSORS for HW1.
    :param cur: The cursor to use. This is wizard stuff. Do not worry about it for now.
        DO NOT PASS CURSORS for HW1.
    :param commit: This is wizard stuff. Do not worry about it.
    :return: A pair of the form (execute response, fetched data). There will only be fetched data if
        the fetch parameter is True. 'execute response' is the return from the connection.execute, which
        is typically the number of rows effected.
    """
    cursor_created = False
    connection_created = False
    try:
        if conn is None:
            raise ValueError("In this implementation, conn cannot be None.")
        if cur is None:
            cursor_created = True
            cur = conn.cursor()
        if args is not None:
            log_message = cur.mogrify(sql, args)
        else:
            log_message = sql
        logger.debug("Executing SQL = " + log_message)
        res = cur.execute(sql, args)
        if fetch:
            data = cur.fetchall()
        else:
            data = None
        if commit:  # Do not ask.
            conn.commit()
    except Exception as e:
        raise e

    return res, data


def template_to_where_clause(template):
    """
    :param template: One of those weird templates
    :return: WHERE clause corresponding to the template.
    """
    if template is None or template == {}:
        result = ("", None)
    else:
        args = []
        terms = []
        for k, v in template.items():
            terms.append(" " + k + "=%s ")
            args.append(v)
        w_clause = "AND".join(terms)
        w_clause = " WHERE " + w_clause
        result = (w_clause, args)
    return result


def create_select(table_name, template, fields=None, order_by=None, limit=None, offset=None, is_select=True):
    """
    Produce a select statement: sql string and args.
    :param table_name: Table name: May be fully qualified dbname.tablename or just tablename.
    :param fields: Columns to select (an array of column name)
    :param template: One of Don Ferguson's weird JSON/python dictionary templates.
    :param order_by: Ignore for now.
    :param limit: Ignore for now.
    :param offset: Ignore for now.
    :return: A tuple of the form (sql string, args), where the sql string is a template.
    """
    if is_select:
        if fields is None:
            field_list = " * "
        else:
            field_list = " " + ",".join(fields) + " "
    else:
        field_list = None
    w_clause, args = template_to_where_clause(template)
    l_clause, o_clause = "", ""
    if limit is not None:
        l_clause = "limit " + limit + " "
    if offset is not None:
        o_clause = "offset " + offset + " "
    if is_select:
        sql = "select " + field_list + " from " + table_name + " " + w_clause + l_clause + o_clause
    else:
        sql = "delete from " + table_name + " " + w_clause + l_clause + o_clause
    return sql, args


def create_insert(table_name, new_row):
    sql = "insert into " + table_name + " "
    cols = list(new_row.keys())
    cols = ",".join(cols)
    col_clause = "(" + cols + ") "
    args = list(new_row.values())
    s_stuff = ["%s"] * len(args)
    s_clause = ",".join(s_stuff)
    v_clause = " values(" + s_clause + ")"
    sql += " " + col_clause + " " + v_clause
    return sql, args


def create_update(table_name, template, changed_cols):
    sql = "update " + table_name + " "
    set_terms = []
    args = []
    for k, v in changed_cols.items():
        args.append(v)
        set_terms.append(k + "=%s")
    set_terms = ",".join(set_terms)
    set_clause = " set " + set_terms
    w_clause, args2 = template_to_where_clause(template)
    sql += set_clause + " " + w_clause
    args.extend(args2)
    return sql, args
