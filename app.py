from flask import Flask, request, escape
from os import getenv
import pyodbc
import logging

app = Flask(__name__)

odbc_dsn = getenv('SQL_ODBC')
odbc_user = getenv('SQL_USER')
odbc_pass = getenv('SQL_PASS')
odbc_appname = getenv('SQL_APPNAME')

log_directory = getenv('LOGDIR')
if log_directory == None:
    log_directory = ''

def sql_connect():
    #
    # Driver={SQL Server Native Client 11.0};Server=myServerAddress;
    # Database=myDataBase;Uid=myUsername;Pwd=myPassword;
    #
    # https://www.connectionstrings.com/sql-server-native-client-11-0-odbc-driver/
    #
    constr = 'DSN=' + odbc_dsn + ';'
    constr = constr + 'Uid=' + odbc_user + ';'
    constr = constr + 'Pwd=' + odbc_pass + ';'
    if odbc_appname > '':
        constr = constr + 'ApplicationName=' + odbc_appname + ';'
    print(constr)
    conn = pyodbc.connect(constr)
    return conn


def setup_logging(log_dir):
    if log_dir <= '':
        log_dir = 'c:\\temp\\app.log'
    log_handler = logging.FileHandler(log_dir)
    log_handler.setLevel(logging.INFO)
    app.logger.addHandler(log_handler)
    app.logger.setLevel(logging.INFO)


setup_logging(log_directory)


@app.before_request
def log_request_info():
    s = request.method + '\t' + request.host_url + '\t' + str(request.query_string)
    app.logger.info(s)


@app.route('/')
def home():
    return f'Hello'


@app.route('/api/v1/auth', methods=['POST'])
def app_v1_auth():
    param_username = request.form['username']
    param_password = request.form['password']
    param_app = request.form['app']
    o_auth_result = ''
    o_token = ''
    o_key = ''

    conn = sql_connect()
    cursor = conn.cursor()
    qt = '\''
    cmd = 'sp_app_authorize '
    cmd = cmd + '@UserName=' + qt + param_username + qt + ', '
    cmd = cmd + '@UserPass=' + qt + param_password + qt + ', '
    cmd = cmd + '@App=' + qt + param_app + qt

    cursor.execute(cmd)
    row = cursor.fetchone()
    if row:
        o_auth_result = row.result
        o_token = row.token
        o_key = row.encryptkey

    conn.commit()
    conn.close()

    result = {
        'result': '',
        'token': o_auth_result,
        'key': ''
    }
    # If successful, send back the token and key
    if o_auth_result == 'authorized':
        result = {
            'result': o_auth_result,
            'token': o_token,
            'key': o_key
        }

    return result


@app.route('/api/v1/expire', methods=['POST'])
def app_v1_expire():
    param_id = request.form['id']

    conn = sql_connect()
    cursor = conn.cursor()
    qt = '\''
    cmd = 'sp_app_token_expire ' + qt + param_id + qt
    cursor.execute(cmd)
    conn.commit()
    conn.close()

    result = {
        'result': 'OK',
    }
    return result


@app.route('/api/v1/check', methods=['POST'])
def app_v1_check():
    param_token = request.form['token']
    param_app = request.form['app']

    o_token = ''

    conn = sql_connect()
    cursor = conn.cursor()
    qt = '\''
    cmd = 'sp_app_token_check @token=' + qt + param_token + qt + ', @app=' + qt + param_app + qt
    cursor.execute(cmd)
    row = cursor.fetchone()
    if row:
        o_token = row.token

    conn.close()

    result = {'result': 'failed'}

    if param_token == o_token:
        result = {'result': 'valid'}

    return result


@app.route('/api/v1/userinfo', methods=['POST'])
def app_v1_get_user_info():
    param_token = request.form['token']
    param_app = request.form['app']

    o_loginid = ''
    o_username = ''
    o_email = ''
    o_login_name = ''

    conn = sql_connect()
    cursor = conn.cursor()
    qt = '\''
    cmd = 'sp_app_get_user_info '
    cmd = cmd + '@token=' + qt + param_token + qt + ', '
    cmd = cmd + '@app=' + qt + param_app + qt

    cursor.execute(cmd)
    row = cursor.fetchone()
    if row:
        o_loginid = row.loginid
        o_username = row.username
        o_email = row.email
        o_login_name = row.loginname

    conn.commit()
    conn.close()

    result = {
        'loginid': o_loginid,
        'username': o_username,
        'email': o_email,
        'login_name': o_login_name
    }

    return result


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=1080)
