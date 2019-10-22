from flask import Flask, Response, request
from datetime import datetime
import json
import src.data_service.data_table_adaptor as dta
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# The convention is that a compound primary key in a path has the elements separated by "_"
# For example, /batting/willite01_BOS_1960_1 maps to the primary key for batting
_key_delimiter = "_"
_host = "127.0.0.1"
_port = 5002
_api_base = "/api"

application = Flask(__name__)


def handle_args(args):
    """
    :param args: The dictionary form of request.args.
    :return: The values removed from lists if they are in a list. This is flask weirdness.
        Sometimes x=y gets represented as {'x': ['y']} and this converts to {'x': 'y'}
    """
    result = {}
    if args is not None:
        for k, v in args.items():
            if type(v) == list:
                v = v[0]
            result[k] = v
    return result


# 1. Extract the input information from the requests object.
# 2. Log the information
# 3. Return extracted information.
def log_and_extract_input(method, path_params=None):
    path = request.path
    args = dict(request.args)
    data = None
    headers = dict(request.headers)
    method = request.method
    url = request.url
    base_url = request.base_url
    try:
        if request.data is not None:
            data = request.json  # dict
    except Exception as e:
        # This would fail the request in a more real solution.
        data = "You sent something but I could not get JSON out of it."
    log_message = str(datetime.now()) + ": Method " + method
    # Get rid of the weird way that Flask sometimes handles query parameters.
    args = handle_args(args)
    inputs = {
        "path": path,
        "method": method,
        "path_params": path_params,
        "query_params": args,
        "headers": headers,
        "body": data,
        "url": url,
        "base_url": base_url
    }

    def pull_args(element, list):  # pulls element from args adds to input as list
        if element in args.keys():
            if args.get(element, None) is not "":
                a = args.get(element)
                if list:
                    a = a.split(",")
            else:
                a = None
            del args[element]
            inputs[element] = a

    pull_args('fields', list=True)
    pull_args('limit', list=False)
    pull_args('offset', list=False)
    log_message += " received: \n" + json.dumps(inputs, indent=2)
    logger.debug(log_message)
    return inputs


def log_response(path, rsp):
    """
    :param path: The path parameter received.
    :param rsp: Response object
    :return:
    """
    msg = rsp
    logger.debug(str(datetime.now()) + ": \n" + str(rsp))


def get_field_list(inputs):
    return inputs.get('fields', None)


def generate_error(status_code, ex=None, msg=None):
    """
    This used to be more complicated in previous semesters, but we simplified for fall 2019.
    Does not do much now.
    :param status_code:
    :param ex:
    :param msg:
    :return:
    """
    rsp = Response("Oops", status=500, content_type="text/plain")
    if status_code == 500:
        if msg is None:
            msg = "INTERNAL SERVER ERROR. Please take COMSE6156 -- Cloud Native Applications."
        rsp = Response(msg, status=status_code, content_type="text/plain")
    return rsp


@application.route("/health/", methods=["GET"])
def health_check():
    rsp_data = {"status": "healthy", "time": str(datetime.now())}
    rsp_str = json.dumps(rsp_data)
    rsp = Response(rsp_str, status=200, content_type="application/json")
    return rsp


@application.route("/demo/<parameter>/", methods=["GET", "PUT", "DELETE", "POST"])
def demo(parameter):
    """
    This simple echoes the various elements that you get for handling a REST request.
    Look at https://flask.palletsprojects.com/en/1.1.x/api/#incoming-request-data
    :param parameter: A list of the path parameters.
    :return: None
    """
    inputs = log_and_extract_input(demo, {"parameter": parameter})
    msg = {"/demo received the following inputs": inputs}
    rsp = Response(json.dumps(msg), status=200, content_type="application/json")
    return rsp


####################################################################################################
#
# YOU HAVE TO COMPLETE THE IMPLEMENTATION OF THE FUNCTIONS BELOW.
#
#
@application.route("/api/databases", methods=["GET"])
def dbs():
    """
    :return: A JSON object/list containing the databases at this endpoint.
    """
    return Response(json.dumps(dta.get_databases()), status=200, content_type="application/json")


@application.route("/api/databases/<dbname>", methods=["GET"])
def tbls(dbname):
    """
    :param dbname: The name of a database/schema
    :return: List of tables in the database.
    """
    return Response(json.dumps(dta.get_tables(dbname)), status=200, content_type="application/json")


@application.route('/api/<dbname>/<resource>/<primary_key>', methods=['GET', 'PUT', 'DELETE'])
def resource_by_id(dbname, resource, primary_key):
    """
    :param dbname: Schema/database name.
    :param resource: Table name.
    :param primary_key: Primary key in the form "col1_col2_..._coln" with the values of key columns.
    :return: Result of operations.
    """
    result = None
    try:
        # Parse the incoming request into an application specific format.
        context = log_and_extract_input(resource_by_id, (dbname, resource, primary_key))
        fields = context.get('fields', None)
        tbl = dta.get_rdb_table(resource, dbname)
        pks = primary_key.split(_key_delimiter)
        if request.method == 'GET':
            res = tbl.find_by_primary_key(pks, field_list=fields)
            rsp = Response(json.dumps(res, default=str), status=200, content_type="application/json")
            return rsp
        elif request.method == 'DELETE':
            res = {"Entries Deleted": tbl.delete_by_key(pks)}
            rsp = Response(json.dumps(res, default=str), status=200, content_type="application/json")
            return rsp
        elif request.method == 'PUT':
            entry = context.get('body')
            res = {"Entries Updated": tbl.update_by_key(pks, entry)}
            rsp = Response(json.dumps(res, default=str), status=200, content_type="application/json")
            return rsp
        else:
            result = "Invalid request."
            return result, 400, {'Content-Type': 'text/plain; charset=utf-8'}
    except Exception as e:
        print(e)
        return handle_error(e, result)


@application.route('/api/<dbname>/<resource_name>', methods=['GET', 'POST'])
def get_resource(dbname, resource_name):
    result = None
    try:
        context = log_and_extract_input(get_resource, (dbname, resource_name))
        tbl = dta.get_rdb_table(resource_name, dbname)
        if request.method == 'GET':
            queries = context.get('query_params', None)
            fields = context.get('fields', None)
            limit = context.get('limit', '10')
            offset = context.get('offset', '0')
            base_url = context.get('base_url', None)
            s = "?"
            for k, v in queries.items():
                s += k + "=" + v + "&"
            if fields is not None:
                s += "fields="
                for i in range(len(fields)):
                    s += fields[i]
                    if i < len(fields) - 1:
                        s += ","
            s += "&limit=" + limit + "&offset="
            prev_url = base_url + s + str(max(0, int(offset) - int(limit)))
            next_url = base_url + s + str(int(offset) + int(limit))
            res = tbl.find_by_template(template=queries, field_list=fields, limit=limit, offset=offset)
            res.insert(0, {"prev_page": prev_url, "current_page": context.get("url"), "next_page": next_url})
            rsp = Response(json.dumps(res, default=str), status=200, content_type="application/json")
            return rsp
        elif request.method == 'POST':
            entry = context.get('body')
            res = {"Entries Inserted": tbl.insert(new_record=entry)}
            return Response(json.dumps(res, default=str), status=200, content_type="application/json")
        else:
            result = "Invalid request."
            return result, 400, {'Content-Type': 'text/plain; charset=utf-8'}
    except Exception as e:
        print("Exception e = ", e)
        return handle_error(e, result)


@application.route('/api/<dbname>/<parent_name>/<primary_key>/<target_name>', methods=['GET'])
def get_by_path(dbname, parent_name, primary_key, target_name):
    # Do not implement
    result = " -- THANK ALY AND ARA -- "
    return result, 501, {'Content-Type': 'application/json; charset=utf-8'}


@application.route('/api/<dbname>/<parent_name>/<primary_key>/<target_name>/<target_key>',
                   methods=['GET'])
def get_by_path_key(dbname, parent_name, primary_key, target_name, target_key):
    # Do not implement
    result = " -- THANK ALY AND ARA -- "

    return result, 501, {'Content-Type': 'application/json; charset=utf-8'}


# You can ignore this method.
def handle_error(e, result):
    return "Internal error.", 504, {'Content-Type': 'text/plain; charset=utf-8'}


if __name__ == "__main__":
    # Setting debug to True enables debug output. This line should be
    # removed before deploying a production app.
    logger.debug("Starting HW2 time: " + str(datetime.now()))
    application.debug = True
    application.run(host=_host, port=_port)
