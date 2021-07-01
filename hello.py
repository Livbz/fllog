#coding:utf-8
import os
import json
import glob
import uuid
from datetime import datetime
import time
import shutil

import redis
import psycopg2 as sql
from flask import g
from flask import Flask, render_template, Response, request, session, redirect, url_for, escape, jsonify,make_response
from flask_cors import CORS
from flask_talisman import Talisman


CURENT_PATH = os.getcwd()
app = Flask(__name__, template_folder='./static/templates')
CORS(app, supports_credentials=True)

app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'
AUTHORITY = 'visiter'
PASSWD = '1234'
IP_dict = dict()
redis_link = redis.StrictRedis(host='127.0.0.1', port=6379, db=0)
app.config['DEBUG'] = False
# 从文件夹中按需求获取博客列表
def get_bloglist(format):
    filepathList = glob.glob(f'{CURENT_PATH}/blogs/*.md')
    blogDict = dict()
    UTC_Title_List = list()
    Tag_title = dict()
    for filepath in filepathList:
        ifPublic = filepath.split('--')[0].split('/')[-1]  # 访问权限
        title = filepath.split('--')[1]
        tags = filepath.split('--')[2].split('&')
        createdAt = filepath.split('--')[3]
        editedAt = filepath.split('--')[4].split('.')[0]
        blogDict[title] = {
            'filepath': filepath,
            'ifPublic': ifPublic,
            'tags': tags,
            'createdAt': createdAt,
            'editedAt': editedAt,
        }
    for key in blogDict:
        blogInfo = blogDict.get(key)
        UTC_Title_List.append(
            [blogInfo['createdAt'], [key, blogInfo['ifPublic']]])
        tags = blogInfo['tags']
        for tag in tags:
            titleList = Tag_title.get(tag, list())
            titleList.append([blogInfo['editedAt'], key,blogInfo['ifPublic']])
            titleList.sort(key=lambda y: y[0], reverse=True)
            Tag_title[tag] = titleList
    UTC_Title_List.sort(key=lambda x: x[0], reverse=True)
    if format == 'title_info':
        return blogDict
    elif format == 'time_series':
        return UTC_Title_List
    elif format == 'tag_series':
        return Tag_title
    else:
        return 'Invalid param'


@app.route('/')
def url_redirect():
    return redirect(url_for('index'))


@app.route('/index')
def index():
    secret_key = request.cookies.get('secretKey')
    get_Args = request.args
    userID = get_Args.get('userID')
    if session.get(userID) == True:
        user = 'admin'
    else:
        user = 'visitor'
    UTC_Title_List = get_bloglist('time_series')
    blogs_index = '<div id="indexList">'
    year_set = set()
    year_list = list()
    for item in UTC_Title_List:
        if item[1][1] == '0':
            continue
        date = datetime.fromtimestamp(int(item[0]))
        date = str(date).split(' ')[0]
        year = date.split('-')[0]
        date = date[5:]
        title = item[1][0]
        if year not in year_set:
            year_set.add(year)
            year_list.append(year)
            segment_year = f"<div class='yearOrTag'><h3 class='yearOrTagH3'>{year}<h3><hr align='left' width='85%'></div>"
            blogs_index += segment_year
        segment_date = '<div class="dateAndTitle"><div class="date">' + date + \
            '</div><div class="title"><a class="titlelink" href="javascript:getBlog(\'' + \
            title + '\')">' + title + '</a></div></div>'
        blogs_index += segment_date
    blogs_index = blogs_index + '</div>'

    blogs_index_tag = "<div id='indexList'>"
    segment_date = ''
    tag_title_list = get_bloglist('tag_series')
    for tag in tag_title_list:
        blogs_index_tag += f"<div class='yearOrTag'><h3  class='yearOrTagH3'>{tag} ➜ <h3></div>"
        for item in tag_title_list[tag]:
            if item[2] == '0':
                continue
            title = item[1]
            date = item[0]
            date = datetime.fromtimestamp(int(date))
            date = str(date).split(' ')[0]
            segment_date = '<div class="title tagTitle"><a class="titlelink" href="javascript:getBlog(\'' + \
                title + '\')">' + title + '</a></div>'
            blogs_index_tag += segment_date
        segment_date
    blogs_index_tag += '</div>'
    return render_template('index.html', user=user, userID=userID, blogs_index=blogs_index, blogs_index_tag=blogs_index_tag)

@app.route('/document')
def document():
    fileNames=[]
    obj = os.walk("./static/document")
    for root,dirname,filename in obj:
        fileNames.append(filename)
    return render_template("document.html",fileNames=fileNames[0])

@app.route("/download/<filename>")
def download(filename):
    # 流式读取
    def send_file():
        store_path = "./static/document/"+filename
        with open(store_path, 'rb') as targetfile:
            while 1:
                data = targetfile.read(20 * 1024 * 1024)  # 每次读取20M
                if not data:
                    break
                yield data

    response = Response(send_file(), content_type='application/octet-stream')
    response.headers["Content-disposition"] = 'attachment; filename=%s' % filename  # 如果不加上这行代码，导致下图的问题
    return response




# ---map

@app.route('/map')
def map():
    cookie_role = request.cookies.get('role')
    print("cookie_role:",cookie_role)
    return render_template('map.html',role=cookie_role)

@app.route('/gps')
def gps():
    gps = {
        1: [117.140178,34.234979],
        2: [117.142624,34.236238],
        3: [117.14301,34.233196],
        4: [117.14139,34.232983],
        5: [117.14595,34.235538]
    }
    res = make_response( jsonify(gps)) # 设置响应体
    res.headers['Access-Control-Allow-origin'] = "*" # 设置响应头
    return res

@app.route('/polyline',methods=['GET', 'POST'])
def polyline():
    # 接收、更新折线点
    if request.method == 'GET':
        # 返回坐标点
        polyline_names = redis_link.lrange("polyline_names",0,-1) 
        print('polyline_names',polyline_names)
        polyline_list = []
        polyline_dict = dict()
        if polyline_names:
            for key in polyline_names:
                print(key)
                path_list = str(redis_link.get(key),encoding = "utf-8")
                path_list = path_list.split(';')
                print(path_list)
                for i in range(len(path_list)):
                    couple = path_list[i].split(',')
                    couple = [float(couple[0]),float(couple[1])]
                    path_list[i] = couple
                polyline_dict[str(key, encoding = "utf-8")] = path_list
                polyline_list.append(redis_link.get(key))
                print(redis_link.get(key))
                print('type : ',type(redis_link.get(key)))
            return jsonify(polyline_dict)
        else:
            return jsonify(polyline_dict)
    else:
        # 接收坐标点
        polyline_name = request.json.get('name')
        print('polyline_name',polyline_name)
        polyline_path = request.json.get('path')
        print('polyline_path',polyline_path)
        for i in range(len(polyline_path)):
            polyline_path[i] = str(polyline_path[i][0]) + ',' + str(polyline_path[i][1])
        str_path = (';').join(polyline_path)
        str_path = str_path[:-1]
        print(str_path)
        if redis_link.exists(polyline_name):
            key_exists = 0
        else:
            key_exists = 1
        if polyline_name != 'tempoErea' and key_exists:
                redis_link.lpush("polyline_names",polyline_name)
        redis_link.set(polyline_name,str_path)
        return 'ok'

@app.route('/tempoErea')
def tempoErea():
        polyline_dict = {}
        polyline_list = []
        path_list = str(redis_link.get('tempoErea'),encoding = "utf-8")
        path_list = path_list.split(';')
        print(path_list)
        for i in range(len(path_list)):
            couple = path_list[i].split(',')
            couple = [float(couple[0]),float(couple[1])]
            path_list[i] = couple
        polyline_dict['tempoErea'] = path_list
        polyline_list.append(redis_link.get('tempoErea'))
        print(redis_link.get('tempoErea'))
        print('type : ',type(redis_link.get('tempoErea')))
        return jsonify(polyline_dict)


@app.route('/mapindex')
def mapindex():
    return render_template('loginon.html')

@app.route('/maplogon',methods=['POST'])
def maplogon():
    res = {}
    password = request.form['password']
    username = request.form['username']
    phone = request.form['phone']
    role = request.form['role']
    if not(password and  username and phone and role):
        res['check'] = 0
        res['info'] = '信息不全'
        return jsonify(res)
    conn = sql.connect("dbname=flaskcomment user=yang")
    cur = conn.cursor()
    sqltext = f"INSERT INTO mapusers(username,password,phone,role) VALUES('{username}','{password}',{phone},'{role}');"
    cur.execute(sqltext)
    conn.commit()
    cur.close()
    conn.close()
    res['check'] = 1
    res['info'] = '注册成功'
    print(sqltext)
    return  jsonify(res)


@app.route('/maplogin',methods=['POST'])
def maplogin():
    print(request.form['password'])
    print(request.form['username'])
    # print(request.form['role'])
    res = {}
    password = request.form['password']
    username = request.form['username']
    # role = request.form['role']
    conn = sql.connect("dbname=flaskcomment user=yang")
    cur = conn.cursor()
    sqltext = f"SELECT * FROM mapusers WHERE username = '{username}'"
    cur.execute(sqltext)
    sqlres = cur.fetchone()
    print(sqlres)
    if not sqlres:
        res['check'] = 0
        return jsonify(res)
    db_password = sqlres[1]
    db_role = sqlres[3]
    conn.commit()
    cur.close()
    conn.close()
    uid = uuid.uuid4()
    uid = str(uid)
    redis_link.set(uid,username)
    if db_role == "visitor":
        if db_password == password:
            res['check'] = 1
            res['cookie'] = uid
            res['role'] = "visitor"
        else:
            res['check'] = 0
        return jsonify(res)
    else:
        if db_password == password:
            res['check'] = 1
            res['cookie'] = uid
            res['role'] = "guide"
        else:
            res['check'] = 0
        return jsonify(res)


@app.route('/maptalk',methods=['GET', 'POST'])
def maptalk():
    if request.method == 'POST':
        print(request.form)
        cookie = request.form['mapid']
        words =  request.form['words']
        redis_name = str(redis_link.get(cookie),encoding = "utf-8")
        print('redis_name',redis_name)
        if redis_name:
            time = datetime.now().strftime("%H:%M:%S")
            wordslist = redis_name + '@#' + time + '@#' + words
            print(wordslist)
            redis_link.lpush("maptalk",wordslist)
            return 'ok'
        return 'no name'
    else:
        res = {}
        talk_list = redis_link.lrange("maptalk",0,-1) 
        for i in range(len(talk_list)):
            talk_slice = str(talk_list[i],encoding = "utf-8")
            talk_list[i] = talk_slice.split('@#')
        talk_list.reverse()
        res['talkList'] = talk_list
        return jsonify(res)


@app.route('/gather',methods=['GET','POST'])
def gather():
        if request.method == 'GET':
            destination = redis_link.get('destination')
            gatherlng = float(str(redis_link.get('gatherlng'),encoding = "utf-8"))
            gatherlat = float(str(redis_link.get('gatherlat'),encoding = "utf-8"))
            res = {}
            res['destination'] = [gatherlng, gatherlat]
            return jsonify(res)
        else:
            print('destination', request.form)
            if request.form['lng']:
                gatherlng = request.form['lng']
                gatherlat = request.form['lat']
                redis_link.set('gatherlng', gatherlng)
                redis_link.set('gatherlat', gatherlat)
                return 'ok'
            return 'bad args'


@app.route('/mapgeofence',methods=['GET','POST'])
def mapgeofence():
    if request.method == 'GET':
        res = {}
        res
        # 使用polyline 代替 polygon
#---map end

@app.route('/hello')
def hello():
    secretKey = request.cookies.get('secretKey')
    if request.cookies.get('secretKey') == session.get('secretKey'):
        user = 'admin'
    else:
        user = 'visitozzzr'
    return render_template('hello.html', cookie=secretKey)


@app.route('/admin')
def admin():
    secretKey = request.cookies.get('secretKey')
    if request.cookies.get('secretKey'):
        if request.cookies.get('secretKey') == session.get('secretKey'):
            user = 'admin'
            return render_template('admin.html', user=user, cookie=secretKey)
        return redirect(url_for('login'))
    else:
        return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        secret_key = str(uuid.uuid4())
        if PASSWD == request.form['passwd']:
            session['secretKey'] = secret_key
            return render_template('hello.html',cookie=secret_key)
        else:
            return render_template('login.html')
    else:
        return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('secretKey', None)
    return redirect(url_for('index'))


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/blogpage', methods=['GET', 'POST'])
def blogpage():
    bloglist = get_bloglist('title_info')
    user = 'visitor'
    if request.cookies.get('secretKey') == session.get('secretKey') and session.get('secretKey') != None:
        user = 'admin'
    get_args = request.args
    args_title = get_args.get('title')
    if args_title in bloglist:
        ip = request.remote_addr
        redis_link.sadd(args_title, ip)
        if get_args.get('search') == 'search':
            args_search = get_args.get('search')
        else:
            args_search = 0
        blogArgs_Dict = bloglist.get(args_title)
        blogContent = 'blank'
        if isinstance(blogArgs_Dict, dict):
            blogPath = blogArgs_Dict.get('filepath')
            with open(blogPath, 'r') as fp:
                allRaw = fp.readlines()
                a = ''
                blogContent = a.join(allRaw)
            createdAt = blogArgs_Dict.get('createdAt')
            editedAt = blogArgs_Dict.get('editedAt')
            createdAt = datetime.fromtimestamp(int(createdAt))
            createdAt = str(createdAt).split(' ')[0]
            editedAt = datetime.fromtimestamp(int(editedAt))
            editedAt = str(editedAt).split(' ')[0]
            tags = blogArgs_Dict.get('tags')
            tags = str(tags)
            tags = tags.replace('\'','')
            tags = tags.replace(',',';')
            tags = tags.replace('[','')
            tags = tags.replace(']','')
            blogContent = {
                '1': blogContent,
            }
        if blogArgs_Dict.get('ifPublic') == '1' or request.cookies.get('secretKey') == session.get('secretKey'):
                return render_template('blogpage.html',
                                       user=user,
                                       blogTitle=args_title,
                                       blogCreatedAt=createdAt,
                                       blogEditedAt=editedAt,
                                       tags=tags,
                                       blogViewCount=redis_link.scard(
                                           args_title),
                                       blogContent=json.dumps(blogContent, ensure_ascii=False))
        return 'PERMISSION DENIE.'
    else:
        return 'NO RESULT.'


@app.route('/writeblog')
def writeblog(user='visitor'):
    if request.cookies.get('secretKey'):
        if request.cookies.get('secretKey') == session.get('secretKey'):
            user = 'admin'
            return render_template('blog-write.html', user=user)
        return redirect(url_for('login'))
    else:
        return redirect(url_for('login'))


@app.route('/input-blog', methods=['GET', 'POST'])
def getinput(user='visitor'):
    getjson = request.get_json()
    b_title = getjson.get('title')
    b_tags = getjson.get('tags').replace('\'', '')
    b_created_at = str(int(time.time()))
    b_edited_at = str(int(time.time()))
    b_content = getjson.get('blogContent')
    if getjson.get('ifPublic') == 'Private':
        b_ifPublic = '0'
    else:
        b_ifPublic = '1'
    blogname_list = '--'.join([b_ifPublic, b_title,b_tags, b_created_at, b_edited_at])
    with open(f'{CURENT_PATH}/blogs/{blogname_list}.md', 'w') as fp:
        fp.write(getjson.get('blogContent'))
    return 'ok'


@app.route('/edit-blog', methods=['POST'])
def editBlog():
    getjson = request.get_json()
    b_title = getjson.get('title')
    blog_list = get_bloglist('title_info')
    if blog_list.get(b_title):
        src_path = blog_list.get(b_title).get('filepath')
        created_at = blog_list.get(b_title).get('createdAt')
        b_tags = getjson.get('tags').replace('\'', '')
        b_created_at = created_at
        b_edited_at = str(int(time.time()))
        b_content = getjson.get('blogContent')
        if getjson.get('ifPublic') == 'Private':
            b_ifPublic = '0'
        else:
            b_ifPublic = '1'
        blogname_list = '--'.join([b_ifPublic, b_title,b_tags, b_created_at, b_edited_at])
        with open(f'{CURENT_PATH}/blogs/{blogname_list}.md', 'w') as fp:
            fp.write(getjson.get('blogContent'))
        dst_path = f"{CURENT_PATH}/blogsTrash/"
        shutil.move(src_path, dst_path)
        return 'ok'
    else:
        return 'Blog not exists.'


@app.route('/search', methods=['GET'])
def search(user='visitor'):
    blogList = get_bloglist('title_info')
    request_args = request.args
    request_title = request_args.get('title')
    if request_title in blogList:
        blog_info = blogList.get(request_title)
        if blog_info.get('ifPublic') == '1':
            return '<a href="javascript:getBlog(\'' + request_title + '\')">' + request_title + '</a>'
        else:
            return 'Permission denied'
    else:
        return f'No blog is named {request_title}'


@app.route('/newcomment', methods=['POST'])
def new_comment():
    request_json = request.get_json()
    blogtitle = request_json.get('title')
    username = request_json.get('username')
    if username == '用户名/邮箱/联系方式':
        username = '匿名'
    usertext = request_json.get('usertext')
    userid = str(uuid.uuid4())
    time = str(datetime.now()).split('.')[0]
    conn = sql.connect("dbname=flaskcomment user=yang")
    cur = conn.cursor()
    if usertext != '':
        cur.execute(
            f"INSERT INTO newusercomments(show,blogtitle,username,time,usertext) VALUES('true','{blogtitle}','{username}','{time}','{usertext}');")
        conn.commit()
    cur.close()
    conn.close()
    return 'ok'

@app.route('/getcomments', methods=['GET'])
def get_comments():
    get_args = request.args
    blogtitle = get_args.get('blogtitle')
    conn = sql.connect("dbname=flaskcomment user=yang")
    cur = conn.cursor()
    cur.execute(
        f"SELECT * FROM newusercomments WHERE blogtitle='{blogtitle}' AND show='true';")
    response = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(response)


@app.route('/managecomment')
def managecomment():
    get_args = request.args
    commentID = get_args.get('id')
    conn = sql.connect("dbname=flaskcomment user=yang")
    cur = conn.cursor()
    sqltext = f"UPDATE newusercomments SET show='false' WHERE id='{commentID}';"
    cur.execute(sqltext)
    conn.commit()
    cur.close()
    conn.close()
    return 'ok'


app.run(host='0.0.0.0', port=443, ssl_context=('./static/ssl/5607143_www.livebz.fun.pem', './static/ssl/5607143_www.livebz.fun.key')) 