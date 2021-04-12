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
# Set the secret key to some random bytes. Keep this really secret!
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'
AUTHORITY = 'visiter'
PASSWD = '!,2a'
IP_dict = dict()
redis_link = redis.StrictRedis(host='127.0.0.1', port=6379, db=0)


def get_bloglist(format):
    filepathList = glob.glob(f'{CURENT_PATH}/blogs/*.md')
    blogDict = dict()
    tagDict = dict()
    blogList = list()
    UTC_Title_List = list()
    Tag_title = dict()
    # UTC_title = dict()
    for filepath in filepathList:
        ifPublic = filepath.split('--')[0].split('/')[-1] # 访问权限
        title = filepath.split('--')[1]
        tags = filepath.split('--')[2].split('&')
        createdAt = filepath.split('--')[3]
        editedAt = filepath.split('--')[4].split('.')[0]
        blogDict[title] = {
            'filepath':filepath,
            'ifPublic':ifPublic,
            'tags':tags,
            'createdAt':createdAt,
            'editedAt':editedAt,
        }
    for key in blogDict:
        blogInfo = blogDict.get(key)
        UTC_Title_List.append([blogInfo['createdAt'],[key, blogInfo['ifPublic']]])
        tags = blogInfo['tags']
        for tag in tags:
            titleList = Tag_title.get(tag, list())
            titleList.append([blogInfo['editedAt'],key])
            titleList.sort(key= lambda y : y[0], reverse = True)
            Tag_title[tag] = titleList
    UTC_Title_List.sort(key=lambda x: x[0],reverse = True)                                                                                                
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
    print('get_bloglist title_info', get_bloglist('title_info'))
    print('get_bloglist time_series', get_bloglist('time_series'))
    print('get_bloglist tag_series', get_bloglist('tag_series'))
    ip = request.remote_addr
    print('ip------> ', ip)
    return redirect(url_for('index'))


@app.route('/index')
def index():
    secret_key = request.cookies.get('secretKey')
    if session.get('secretKey') == secret_key:
        print('correspond!')
    get_Args = request.args
    userID = get_Args.get('userID')
    if session.get(userID) == True:
        user = 'admin'
    else:
        user = 'visitor'
# if get_Args.get('Mode') == None:
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
        if year not in year_set:  # 说明是新的一年了
            year_set.add(year)
            year_list.append(year)
            segment_year = f"<div class='yearOrTag'><h3 class='yearOrTagH3'>{year}<h3><hr align='left' width='85%'></div>"
            blogs_index += segment_year
        segment_date = '<div class="dateAndTitle"><div class="date">'+ date+'</div><div class="title"><a class="titlelink" href="javascript:getBlog(\''+ title + '\')">'+  title + '</a></div></div>'
        blogs_index += segment_date
    blogs_index = blogs_index + '</div>'
    # blogs_index = blogs_index
    # blogs_index = '<h1>xx</h1>'
    # print(blogs_index)
# elif get_Args.get('Mode') == 'groupbytag':
    blogs_index_tag = "<div id='indexList'>"
    tag_title_list = get_bloglist('tag_series')
    print('tag_title_list\n', tag_title_list)
    for tag in tag_title_list:
        blogs_index_tag += f"<div class='yearOrTag'><h3  class='yearOrTagH3'>{tag} ➜ <h3></div>"
        for item in tag_title_list[tag]:
            title = item[1]
            date = item[0]
            date = datetime.datetime.fromtimestamp(int(date))
            date = str(date).split(' ')[0]
            segment_date = '<div class="title tagTitle"><a class="titlelink" href="javascript:getBlog(\''+ title + '\')">' + title  +  '</a></div>'
            blogs_index_tag += segment_date
    blogs_index_tag += '</div>'
    return render_template('index.html', user = user, userID=userID, blogs_index=blogs_index, blogs_index_tag=blogs_index_tag)



@app.route('/hello')
def hello():
    secretKey = request.cookies.get('secretKey')
    if request.cookies.get('secretKey') == session['secretKey']:
        user = 'admin'
    else:
        user = 'visitozzzr'
    print(user)
    return render_template('hello.html',cookie=secretKey)

@app.route('/admin')
def admin():
    secretKey = request.cookies.get('secretKey')
    if request.cookies.get('secretKey'):
        if request.cookies.get('secretKey') == session['secretKey']:
            user = 'admin'
            return render_template('admin.html',user=user, cookie=secretKey)
        return redirect(url_for('login'))
    else:
        return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        secret_key =  str(uuid.uuid4())
        print(secret_key)
        if PASSWD == request.form['passwd']:
            session['secretKey'] = secret_key
            print('x',secret_key)
            return render_template('hello.html',cookie=secret_key)
        else:
            return '''
                <form method="post">
                    <p><input type=text name=passwd>
                    <p><input type=submit value=Login>
                </form>
            '''         
    else:
        return '''
            <form method="post">
                <p><input type=text name=passwd>
                <p><input type=submit value=Login>
            </form>
        '''

@app.route('/logout')
def logout():
    # remove the username from the session if it's there
    session.pop('username', None)
    return redirect(url_for('index'))

@app.route('/bloglist')
def bloglist(user='visitor'):
    # 获取参数 
    get_Args = request.args
    # args_title = get_Args.get('title')
    if get_Args.get('tag') == 'tag':
        args_tag = 1
    else:
        args_tag = 0
    if get_Args.get('timeseries') == 'timeseries':
        args_time = 1
    else:
        args_time = 0
    # 获取博客列表
    filepathList = glob.glob(f'{CURENT_PATH}/blogs/*.md')
    bloglist = get_bloglist('title_info')
    if args_time ==1 and args_tag == 0:
        bloglist_time = dict()  # { 'date'：['title',]}
        for key in bloglist:
            createdAt = bloglist.get(key).get('createdAt')
            bloglist_time[createdAt] = bloglist_time.get(createdAt, list())
            bloglist_time[createdAt].append(key)
        print(bloglist_time)
        return jsonify(bloglist_time)
    elif args_time ==0 and args_tag == 1:
        # { 'tag': ['title,']}
        bloglist_tag = dict()
        for key in bloglist:
            tags = bloglist.get(key).get('tags')
            for tag in tags:
                bloglist_tag[tag] = bloglist_tag.get(tag, list())
                bloglist_tag[tag].append(key)
        print(bloglist_tag)
        return jsonify(bloglist_tag)
    else:
        return 'Either timeseries or tags'

# 返回整个博客页面 or 单个博客文本
@app.route('/blogpage', methods=['GET','POST'])
def blogpage():
    # print(CURENT_PATH)
    filepathList = glob.glob(f'{CURENT_PATH}/blogs/*.md')
    print(filepathList)
    bloglist = dict()
    for filepath in filepathList:
        ifPublic = filepath.split('--')[0][-1] # 访问权限
        title = filepath.split('--')[1]
        tags = filepath.split('--')[2].split('&')
        createdAt = filepath.split('--')[3].split('.')[0]
        createdAt = datetime.datetime.fromtimestamp(int(createdAt))
        createdAt = str(createdAt).split(' ')[0]
        editedAt = filepath.split('--')[4].split('.')[0]
        editedAt = datetime.datetime.fromtimestamp(int(editedAt))
        editedAt = str(editedAt).split(' ')[0]
        bloglist[title] = {
            'filepath':filepath,
            'ifPublic':ifPublic,
            'tags':tags,
            'createdAt':createdAt,
            'editedAt':editedAt,
        }
    print(type(bloglist))
        # bloglist[title] = [filename, ifPublic, tags, createdAt, editedAt]
    # 默认为游客登录
    # md_string = r"## MaHua有哪些功能？\n* 方便的`导入导出`功能\n*  直接把一个markdown的文本文件拖放到当前这个页面就可以了\n*  导出为一个html格式的文件，样式一点也不会丢失\n* 编辑和预览`同步滚动`，所见即所得（右上角设置）\n* `VIM快捷键`支持，方便vim党们快速的操作 （右上角设置）\n* 强大的`自定义CSS`功能，方便定制自己的展示\n* 有数量也有质量的`主题`,编辑器和预览区域\n* 完美兼容`Github`的markdown语法\n* 预览区域`代码高亮`\n* 所有选项自动记忆"
    secretKey = request.cookies.get('secretKey')
    user = 'visitor'
    if request.cookies.get('secretKey') == session.get('secretKey'):
        user = 'admin'
    get_Args = request.args
    args_title = get_Args.get('title')
    if args_title in bloglist:
        ip = request.remote_addr
        redis_link.sadd(args_title, ip)
        print('sum ip',redis_link.scard(args_title))  # 集合的长度是4
        print('members of set',redis_link.smembers(args_title))   # 获取集合中所有的成员
        # ip_set = IP_dict.get(args_title,set())
        # ip_set.add(ip)
        # IP_dict[args_title] = ip_set
        print(IP_dict)
        if get_Args.get('search') == 'search':
            args_search = get_Args.get('search')
        else:
            args_search = 0
        blogArgs_Dict = bloglist.get(args_title)
        print(type(blogArgs_Dict))
        blogContent = 'blank'
        if isinstance(blogArgs_Dict, dict):
            blogPath = blogArgs_Dict.get('filepath')
            with open(blogPath, 'r') as fp:
                allRaw = fp.readlines()
                a = ''
                blogContent = a.join(allRaw)
            createdAt = blogArgs_Dict.get('createdAt')
            editedAt = blogArgs_Dict.get('editedAt')
            tags = blogArgs_Dict.get('tags')
            # print('blogContent json', json.dumps(blogContent, ensure_ascii=False))
            blogContent = {
                '1': blogContent,
            }
        print(blogArgs_Dict.get('ifPublic'))
        if blogArgs_Dict.get('ifPublic') == '1':
            if args_search != 'search' :
                return render_template('blogpage.html', 
                user = user,
                blogTitle= args_title, 
                blogCreatedAt = createdAt,
                blogEditedAt = editedAt,
                tags = tags,
                blogViewCount = redis_link.scard(args_title), 
                blogContent=json.dumps(blogContent, ensure_ascii=False))
            else :
                searched_blog = {
                    'args_title': args_title,
                    'createdAt': createdAt,
                    'blogContent': blogContent,
                    }
                return jsonify(searched_blog)
    else:
        return '404 U CAN NOT SEE'


@app.route('/writeblog')
def writeblog(user='visitor'):
    # blog page
    # 默认为游客登录
    if request.cookies.get('secretKey'):
        if request.cookies.get('secretKey') == session['secretKey']:
            user = 'admin'
            return render_template('blog-write.html', user=user)
        return redirect(url_for('login'))
    else:
        return redirect(url_for('login'))


@app.route('/input-blog', methods=['GET', 'POST'])
def getinput(user='visitor'):
    # request_data = request.get_data()
    getjson = request.get_json()
    print(getjson)
    # b_ for blog_s
    b_title = getjson.get('title')
    b_tags = getjson.get('tags').replace('\'' , '')
    b_created_at = str(int(time.time()))
    b_edited_at = str(int(time.time()))
    # b_edited_at = getjson.get('edited_at')
    b_content = getjson.get('blogContent')
    if getjson.get('ifPublic')=='Private':
        b_ifPublic = '0'
    else:
        b_ifPublic = '1'
    blogname_list  = '--'.join([b_ifPublic, b_title, b_tags, b_created_at, b_edited_at])
    print(getjson)
    with open(f'{CURENT_PATH}/blogs/{blogname_list}.md', 'w') as fp:
        fp.write(getjson.get('blogContent'))
    return 'ok'

@app.route('/edit-blog',methods=['POST'])
def editBlog():
    getjson = request.get_json()
    b_title = getjson.get('title')
    blog_list = get_bloglist('title_info')
    if blog_list.get(b_title):
        src_path = blog_list.get(b_title).get('filepath')
        created_at = blog_list.get(b_title).get('createdAt')
    else:
        src_path = ''
    
    print(getjson)
    # b_ for blog_s

    b_tags = getjson.get('tags').replace('\'' , '')
    b_created_at = created_at
    b_edited_at = str(int(time.time()))
    # b_edited_at = getjson.get('edited_at')
    b_content = getjson.get('blogContent')
    if getjson.get('ifPublic')=='Private':
        b_ifPublic = '0'
    else:
        b_ifPublic = '1'
    blogname_list  = '--'.join([b_ifPublic, b_title, b_tags, b_created_at, b_edited_at])
    print(getjson)
    with open(f'{CURENT_PATH}/blogs/{blogname_list}.md', 'w') as fp:
        fp.write(getjson.get('blogContent'))
    print('src_path=====',src_path)
    dst_path = f"{CURENT_PATH}/blogsTrash/"
    shutil.move(src_path,dst_path)
    return 'ok'

# @app.route('/edit-blog',method=['POST'])
# def edit_blog()
#     getjson = request.get_json()
#     print(getjson)
#     # b_ for blog_s
#     b_title = getjson.get('title')
#     b_tags = getjson.get('tags').replace('\'' , '')
#     b_created_at = getjson.get('created_at')
#     UTC = str(int(time.time()))
#     # b_edited_at = getjson.get('edited_at')
#     b_content = getjson.get('blogContent')
#     if getjson.get('ifPublic')=='Private':
#         b_ifPublic = '0'
#     else:
#         b_ifPublic = '1'
#     blogname_list  = '--'.join([b_ifPublic, b_title, b_tags, b_created_at, UTC])
#     print(getjson)
#     with open(f'{CURENT_PATH}/blogs/{blogname_list}.md', 'w') as fp:
#         fp.write(getjson.get('blogContent'))
#     return 'ok'


@app.route('/search', methods=['GET'])
def search(user='visitor'):
    blogList = get_bloglist('title_info')
    request_args = request.args
    request_title = request_args.get('title')
    if request_title in blogList:
        blog_info = blogList.get(request_title)
        print(blog_info)
        if blog_info.get('ifPublic') == '1':
            return '<a href="javascript:getBlog(\''+ request_title + '\')">' + request_title + '</a>'
        else:
            return 'Permission denied'
    else:
        return f'No blog is named {request_title}'
    pattern = f'{CURENT_PATH}/blogs/*.md'
    filepath_list =  glob.glob(pattern)
    bloglist = dict()
    for filepath in filepath_list:
            ifPublic = filepath.split('--')[0] # 访问权限
            title = filepath.split('--')[1]
            tags = filepath.split('--')[2].split('tag')
            createdAt = filepath.split('--')[3]
            editedAt = filepath.split('--')[4]
            bloglist[title] = {
                'filepath':filepath,
                'ifPublic':ifPublic,
                'tags':tags,
                'createdAt':createdAt,
                'editedAt':editedAt,
            }
    return 'ok'

@app.route('/newcomment',methods=['POST'])
def uew_comment():
    getjson = request.get_json()
    print(getjson)
    blogtitle = getjson.get('title')
    username = getjson.get('username')
    usertext = getjson.get('usertext')
    userid = str(uuid.uuid4())
    time = str(datetime.datetime.now()).split('.')[0]
    conn = sql.connect("dbname=yang user=yang")
    cur = conn.cursor()
    cur.execute(f"INSERT INTO usercomments(blogtitle,username,time,usertext) VALUES('{blogtitle}','{username}','{time}','{usertext}');")
    conn.commit()
    cur.close()
    conn.close()
    return 'ok'

@app.route('/getcomments',methods=['GET'])
def get_comments():
    get_Args = request.args
    blogtitle = get_Args.get('blogtitle')
    conn = sql.connect("dbname=yang user=yang")
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM usercomments WHERE blogtitle='{blogtitle}';")
    response = cur.fetchall()
    print(response)
    cur.close()
    conn.close()
    return jsonify(response)
