
import json
import glob
from flask import g
import sqlite3 as sql
from flask import Flask, render_template, request, session, redirect, url_for, escape
app = Flask(__name__)
# Set the secret key to some random bytes. Keep this really secret!
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'
@app.route('/')
def index():
    # if 'username' in session:
    #     return 'Logged in as %s' % escape(session['username'])
    # return 'You are not logged in'
    return render_template('index.html')


@app.route('/hello/<name>')
def hello(name=None):
    return render_template('hello.html', name=name)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        session['username'] = request.form['username']
        return redirect(url_for('index'))
    return '''
        <form method="post">
            <p><input type=text name=username>
            <p><input type=submit value=Login>
        </form>
    '''


@app.route('/logout')
def logout():
    # remove the username from the session if it's there
    session.pop('username', None)
    return redirect(url_for('index'))


@app.route('/blogpage', methods=['GET','POST'])
def blogpage(user='visitor'):
    filepathList = glob.glob('/home/admin/fllog/blogs/*.md')
    bloglist = dict()
    for filepath in filepathList:
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
    print(type(bloglist))
        # bloglist[title] = [filename, ifPublic, tags, createdAt, editedAt]
    # 默认为游客登录
    # md_string = r"## MaHua有哪些功能？\n* 方便的`导入导出`功能\n*  直接把一个markdown的文本文件拖放到当前这个页面就可以了\n*  导出为一个html格式的文件，样式一点也不会丢失\n* 编辑和预览`同步滚动`，所见即所得（右上角设置）\n* `VIM快捷键`支持，方便vim党们快速的操作 （右上角设置）\n* 强大的`自定义CSS`功能，方便定制自己的展示\n* 有数量也有质量的`主题`,编辑器和预览区域\n* 完美兼容`Github`的markdown语法\n* 预览区域`代码高亮`\n* 所有选项自动记忆"
    get_Args = request.args
    args_title = get_Args.get('title')
    blogArgs_Dict = bloglist.get(args_title)
    print(type(blogArgs_Dict))
    blogContent = 'blank'
    if isinstance(blogArgs_Dict, dict):
        blogPath = blogArgs_Dict.get('filepath')
        with open(blogPath, 'r') as fp:
            allRaw = fp.readlines()
            a = ''
            blogContent = a.join(allRaw)
    print(blogContent)
    return render_template('blogpage.html', blogTitle='博客标题', blogCreatedAt='', blogEditedAt='', blogContent=blogContent)


@app.route('/writeblog')
def writeblog(user='visitor'):
    # blog page
    # 默认为游客登录
    # md_string = r"## MaHua有哪些功能？\n* 方便的`导入导出`功能\n*  直接把一个markdown的文本文件拖放到当前这个页面就可以了\n*  导出为一个html格式的文件，样式一点也不会丢失\n* 编辑和预览`同步滚动`，所见即所得（右上角设置）\n* `VIM快捷键`支持，方便vim党们快速的操作 （右上角设置）\n* 强大的`自定义CSS`功能，方便定制自己的展示\n* 有数量也有质量的`主题`,编辑器和预览区域\n* 完美兼容`Github`的markdown语法\n* 预览区域`代码高亮`\n* 所有选项自动记忆"
    return render_template('blog-write.html')


@app.route('/input-blog', methods=['GET', 'POST'])
def getinput(user='visitor'):
    # request_data = request.get_data()
    getjson = request.get_json()
    # b_ for blog_
    b_title = getjson.get('title')
    b_tags = getjson.get('tags')
    b_created_at = getjson.get('created_at')
    b_edited_at = getjson.get('edited_at')
    b_content = getjson.get('blogContent')
    b_ifPublic = '1'
    blogname_list  = '--'.join([b_ifPublic, b_title, b_tags, b_created_at, b_edited_at])

    print(getjson)
    with open(f'/home/admin/fllog/blogs/{blogname_list}.md', 'w') as fp:
        fp.write(getjson.get('blogContent'))
        # con = sql.connect("DB2.db")
        # con.row_factory = sql.Row
        # cur = con.cursor()
        # # INSERT INTO "new_table" VALUES('hello',10);
        # blog_Content = getjson.get('blogContent')
        # cur.execute(
        #     f"INSERT INTO `blogs` VALUES('test_two','{blog_Content}');")
        # con.close()
    return 'ok'

@app.route('/search', methods=['GET'])
def search(user='visitor'):
    pattern = '/home/admin/fllog/blogs/*.md'
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