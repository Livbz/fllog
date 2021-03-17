import os
import argparse


def countfiles(folder):
    folderlist = list()
    folderlist.append((folder, 0))
    filelist = set()
    filecount = 0
    maxn = 1
    deep = 0
    while(1):
        for folder in folderlist:
            goon = False
            if folder[1] == maxn - 1:
                pathlist = os.listdir(folder[0])
                for path in pathlist:
                    fullpath = folder[0]+'/'+path
                    if os.path.isfile(fullpath):
                        # filelist.add(fullpath)
                        filecount += 1
                    if os.path.isdir(fullpath):
                        goon = True
                        folderlist.append((fullpath, deep))
        if goon:
            maxn += 1
        else:
            break
    # print(len(filelist))
    print(filecount)
    return 'total'


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("folder", help="input the folder you want to count")
    args = parser.parse_args()
    countfiles(args.folder)
