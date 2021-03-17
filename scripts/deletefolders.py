'''
提供一个包含所有要删除文件夹路径的txt，
或一个根目录和该目录下需要删除的文件夹名的txt
'''
import shutil


def delete(rootpath, filepath):
    with open(filepath, 'r') as fp:
        pathlist = fp.readlines()
        for path in pathlist:
            try:
                path = rootpath + path.split('.')[0]
                shutil.rmtree(path)
                print(path)
            except OSError as e:
                print("Error: %s:%s" % (path, e.strerror))


if __name__ == '__main__':
    rootpath = './'
    rathfile = 'delete.txt'
    delete(rootpath, rathfile)
