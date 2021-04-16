import os
import json
import glob
import uuid
import datetime
import time
import os
import shutil

import redis
import psycopg2 as sql
from flask import g
from flask import Flask, render_template, request, session, redirect, url_for, escape, jsonify


CURENT_PATH = os.getcwd()
app = Flask(__name__, template_folder='./static/templates')
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'
AUTHORITY = 'visiter'
PASSWD = '!,2a'
IP_dict = dict()
redis_link = redis.StrictRedis(host='127.0.0.1', port=6379, db=0)


# 从文件夹中按需求获取博客列表
def get_bloglist(format):
    filepathList = glob.glob(f'{CURENT_PATH}/blogs/*.md')
    blogDict = dict()
    tagDict = dict()
    blogList = list()
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
            titleList.append([blogInfo['editedAt'], key])
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
        date = datetime.datetime.fromtimestamp(int(item[0]))
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
    tag_title_list = get_bloglist('tag_series')
    for tag in tag_title_list:
        blogs_index_tag += f"<div class='yearOrTag'><h3  class='yearOrTagH3'>{tag} ➜ <h3></div>"
        for item in tag_title_list[tag]:
            title = item[1]
            date = item[0]
            date = datetime.datetime.fromtimestamp(int(date))
            date = str(date).split(' ')[0]
            segment_date = '<div class="title tagTitle"><a class="titlelink" href="javascript:getBlog(\'' + \
                title + '\')">' + title + '</a></div>'
            blogs_index_tag += segment_date
    blogs_index_tag += '</div>'
    return render_template('index.html', user=user, userID=userID, blogs_index=blogs_index, blogs_index_tag=blogs_index_tag)


@app.route('/hello')
def hello():
    secretKey = request.cookies.get('secretKey')
    if request.cookies.get('secretKey') == session['secretKey']:
        user = 'admin'
    else:
        user = 'visitozzzr'
    return render_template('hello.html', cookie=secretKey)


@app.route('/admin')
def admin():
    secretKey = request.cookies.get('secretKey')
    if request.cookies.get('secretKey'):
        if request.cookies.get('secretKey') == session['secretKey']:
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
    if request.cookies.get('secretKey') == session.get('secretKey'):
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
            createdAt = datetime.datetime.fromtimestamp(int(createdAt))
            createdAt = str(createdAt).split(' ')[0]
            editedAt = datetime.datetime.fromtimestamp(int(editedAt))
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
        if blogArgs_Dict.get('ifPublic') == '1':
                return render_template('blogpage.html',
                                       user=user,
                                       blogTitle=args_title,
                                       blogCreatedAt=createdAt,
                                       blogEditedAt=editedAt,
                                       tags=tags,
                                       blogViewCount=redis_link.scard(
                                           args_title),
                                       blogContent=json.dumps(blogContent, ensure_ascii=False))
    else:
        return 'NO RESULT.'


@app.route('/writeblog')
def writeblog(user='visitor'):
    if request.cookies.get('secretKey'):
        if request.cookies.get('secretKey') == session['secretKey']:
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
    time = str(datetime.datetime.now()).split('.')[0]
    conn = sql.connect("dbname=yang user=yang")
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
    conn = sql.connect("dbname=yang user=yang")
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
    conn = sql.connect("dbname=yang user=yang")
    cur = conn.cursor()
    sqltext = f"UPDATE newusercomments SET show='false' WHERE id='{commentID}';"
    cur.execute(sqltext)
    conn.commit()
    cur.close()
    conn.close()
    return 'ok'
