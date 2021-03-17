'''
python 3.6
v 0.12.0
校验标注文件夹及其中的文件
1.文件目录完整性校验
2.关联完整性校验
3.逻辑完整性校验

校验逻辑：
1.文件目录完整性
    获取根目录下，存在的所有文件夹名和文件名，以此为依据，判断文件目录是否符合要求
2.关联完整性同理
'''
import json
import sys
import glob
import os

'''
os.path.isdir( ), os.path.isfile（），os.listdir( ), os.walk( )
os.path.isdir( ) 函数：判断某一路径是否为目录
os.path.isdir(path)
os.path.isfile( ) 函数：判断某一路径是否为文件
os.path.isfile(path)
path：要进行判断的路径
'''
def folder_integrity_check(root_path):
    error_list = []
    out_folder_set = set()
    folders_out_list = glob.glob(root_path + "*")
    folders_in_list = glob.glob(root_path + "*/*")
    folders_out_split_set = set()
    folders_in_split_set = set()
    for item in folders_out_list:
        folders_out_split_set.add(item.split('/')[-1])
    # >>文件目录校验<<
    # 1.压缩包根目录内一定是多个文件夹：
    if not (len(folders_out_list) > 1):
        error_list.append('压缩包根目录内不是多个文件夹')
    # 2. 压缩包根目录内必定包含文件夹：-1000、promptAudios。
    if not('-1000' in folders_out_split_set):
        error_list.append('压缩包根目录内未包含文件夹：-1000')
    if not('promptAudios' in folders_out_split_set):
        error_list.append('压缩包根目录内未包含文件夹：promptAudios')
    # 3. 压缩包根目录内必定包含文件：bookInfo.json
    if not(os.path.isfile(root_path + 'bookInfo.json')):
        error_list.append('压缩包根目录内未包含文件：bookInfo.json')
    # 4.-1000一定表示目录
    if not(os.path.isdir(root_path+'-1000')):
        error_list.append('-1000不是一个目录')
    # 5. 压缩包根目录内除了promptAudios文件夹外，其它文件夹内一定包含文件：label.json
    for path_out in folders_out_list:
        if os.path.isdir(path_out):
            out_folder_set.add(path_out.split('/')[-1])
            if not(os.path.isfile(path_out+'/label.json')) and path_out != root_path + 'promptAudios':
                error_list.append(path_out+' 中缺少label.json')

    # >>bookInfo.json内容校验<<
    # 1.文件内容必须是合法的JSON格式
    try:
        with open(root_path +'bookInfo.json', 'r') as fp:
            bookinfo_json = json.load(fp)
        # 2.1 JSON根结点一定包含pagesList字段，pagesList字段必须表示数组，且数组长度必须大于1。
        page_list = bookinfo_json.get('pagesList')
        if not page_list:
            error_list.append('JSON根结点未包含pagesList字段')
        elif not type(page_list) == list:
            error_list.append('pagesList字段对应的不是数组!')
        elif not len(page_list) > 1:
            error_list.append('pagesList字段对应的数组长度小于1!')
        # 2.2 其中第一个元素必须是-1000，表示封面。（与文件夹进行相互校验）
        elif not page_list[0] == '-1000':
            error_list.append('pagesList字段对应的数组第一个元素不是-1000!')
        else:
            page_set =set(page_list)
            page_set.add(bookinfo_json.get('promptAudio').get('directoryName'))
        # 2.3 pagesList中元素必须包含资源压缩包根目录下的所有文件夹名称（除了下面directoryName指定名称的文件夹）。
            if not (page_set == page_set | out_folder_set):
                error_list.append('pagesList中未包含资源压缩包根目录下的所有文件夹名称，或directoryName指定名称与实际文件夹不符')
        # 3.0 JSON根结点一定包含promptAudio字段，
        prompt_audio = bookinfo_json.get('promptAudio')
        if not prompt_audio:
            error_list.append('JSON根结点没有包含promptAudio字段!')
        # 3.1 其中directoryName的值必须是资源压缩包根目录下的一个文件夹名称。
        elif not (prompt_audio.get('directoryName') in out_folder_set):
            error_list.append('bookInfo.json的directoryName的值`不是`资源压缩包根目录下的一个文件夹名称!')
        # 3.2 directoryName、turnPageStartAudio、turnPageMiddleAudio都是必不可少的字段
        include_set = set(['directoryName','turnPageStartAudio','turnPageMiddleAudio'])
        for key in bookinfo_json.get('promptAudio'):
            if not key in include_set:
                err = f'promptAudio的字段中缺少 {key} !'
                error_list.append(err)
        # 3.3 turnPageStartAudio和turnPageMiddleAudio的值也必须是directoryName指定的文件夹下的文件，且值一定是.ogg或者.mp3后缀
        dir_directoryName = bookinfo_json.get('promptAudio').get('directoryName')
        turn_page_start_audio =  bookinfo_json.get('promptAudio').get('turnPageStartAudio')
        turn_page_middle_audio = bookinfo_json.get('promptAudio').get('turnPageMiddleAudio')
        turn_page_start_audio_path = root_path + dir_directoryName + '/' + turn_page_start_audio
        turn_page_middle_audio_path = root_path + dir_directoryName + '/' + turn_page_middle_audio
        if not os.path.isfile(turn_page_start_audio_path):
            error_list.append(f'{turn_page_start_audio} 不存在！')
        if not os.path.isfile(turn_page_middle_audio_path):
            error_list.append(f'{turn_page_middle_audio} 不存在！')
        if not (turn_page_start_audio[-4:] in set(['.ogg', '.mp3'])):
            error_list.append(f'{turn_page_start_audio} 后缀名不等于`.ogg`或`.mp3`！')
        if not (turn_page_middle_audio[-4:] in set(['.ogg', '.mp3'])):
            error_list.append(f'{turn_page_middle_audio} 后缀名不等于`.ogg`或`.mp3`！')
        # 3.4 JSON根结点一定包含tutorialNum字段，且值必须是pagesList的某个元素
        tutorial_num = bookinfo_json.get('tutorialNum')
        if not tutorial_num:
            error_list.append('JSON根结点没有包含`tutorialNum`字段!')
        else:
            if not tutorial_num in set(page_list):
                error_list.append('`tutorialNum`字段的值不存在于pagesList中!')
    except Exception as e:
        error_list.append('bookInfo.json的格式不是合法的JSON格式')
        raise e

    # >>label.json内容校验<<
    '''
    1. 文件内容必须是合法的JSON格式。
    2. JSON根结点一定包含pageAudio字段，且值一定是.ogg或者.mp3后缀，且一定能在label.json同目录下找到相应命名的文件。
    3. JSON根结点一定包含pageImage字段，且值一定是.png或.jpg后缀，且一定能在label.json同目录下找到相应命名的文件。
    4. JSON根结点一定包含pageNum字段，且值一定和文件夹名字相同。
    5. JSON根结点一定包含pageTitleText字段，且值不为空。
    6. JSON根结点一定包含supportImage字段，且值一定是.jpg后缀，且一定能在label.json同目录下找到相应命名的文件。
    7. JSON根结点一定包含pageType字段，且值必须是限定以下几种：
      1. findSystem
      2. findSystem_MFHP
      3. colorTheShape
      4. connectTheDots
      5. findPair
      6. pointAndRead
      7. drawAndPaint
    '''
    for path in folders_out_list:  # 对每一个文件夹中有的label文件进行校验
        if os.path.isdir(path):
            label_json_path = path + '/label.json'
            if os.path.exists(label_json_path):
                with open(label_json_path, 'r') as fp:
                    try:
                        label_json = json.load(fp)
                        page_audio = label_json.get('pageAudio')
                        page_image = label_json.get('pageImage')
                        page_num = label_json.get('pageNum')
                        page_title_text = label_json.get('pageTitleText')
                        support_image = label_json.get('supportImage')
                        page_type = label_json.get('pageType')
                        question = label_json.get('question')
                        answer = label_json.get('answer')
                        valid_area = label_json.get('validArea')
                        # 2. JSON根结点一定包含pageAudio字段，且值一定是.ogg或者.mp3后缀，且一定能在label.json同目录下找到相应命名的文件
                        if not page_audio:
                            error_list.append(f'{label_json_path} 的根结点没有包含`pageAudio`字段!')
                        elif not page_audio[-4:] in set(['.ogg','.mp3']):
                            error_list.append(f'{label_json_path} 的`pageAudio`字段`不是`.ogg或者.mp3后缀!')
                        elif not os.path.isfile(path + '/' +page_audio):
                            error_list.append(f'{path} 中不存在文件`{page_audio}`!')
                        # 3. JSON根结点一定包含pageImage字段，且值一定是.png或.jpg后缀，且一定能在label.json同目录下找到相应命名的文件。
                        if not page_image:
                            error_list.append(f'{label_json_path} 的根结点没有包含`pageImage`字段!')
                        elif not page_image[-4:] in set(['.png','.jpg']):
                            error_list.append(f'{label_json_path} 的`pageImage`字段`不是`.png后缀!')
                        elif not os.path.isfile(path + '/' +page_image):
                            error_list.append(f'{path} 中不存在文件`{page_image}`!')
                        # 4. JSON根结点一定包含pageNum字段，且值一定和文件夹名字相同。
                        if not page_num:
                            error_list.append(f'{label_json_path} 的根结点没有包含`pageNum`字段!')
                        elif not label_json_path.split('/')[-2] == page_num:
                            error_list.append(f'{label_json_path} 的`pageNum`字段值与当前文件夹名称不符!')
                        # 5. JSON根结点一定包含pageTitleText字段，且值不为空。
                        if not page_title_text:
                            error_list.append(f'{label_json_path} 的根结点没有包含`pageTitleText`字段或字段为空!')
                        elif page_title_text.replace(' ','') == '':
                            error_list.append(f'{label_json_path} 的`pageTitleText`字段为空白!')
                        # 6. JSON根结点一定包含supportImage字段，且值一定是.jpg或.png后缀，且一定能在label.json同目录下找到相应命名的文件
                        if not support_image:
                            error_list.append(f'{label_json_path} 的根结点没有包含`supportImage`字段!')
                        elif not support_image[-4:] in set(['.jpg','.png']):
                            error_list.append(f'{label_json_path} 的`supportImage`字段`不是`.jpg或者.png后缀!')
                        elif not os.path.isfile(path + '/' +support_image):
                            error_list.append(f'{path} 中不存在文件`{support_image}`!')
                        # 7. JSON根结点一定包含pageType字段，且值必须是限定以下几种：
                        #   1. findSystem
                        #   2. findSystem_MFHP
                        #   3. colorTheShape
                        #   4. connectTheDots
                        #   5. findPair
                        #   6. pointAndRead
                        #   7. drawAndPaint
                        #   8. pageReading
                        if not page_type:
                            error_list.append(f'{label_json_path} 的根结点未包含`pageType`字段`!')
                        elif not page_type in set(['pageReading', 'findSystem', 'findSystem_MFHP', 'colorTheShape', 'connectTheDots', 'findPair', 'pointAndRead', 'drawAndPaint']):
                            error_list.append(f'{label_json_path} 的`pageType`字段`未在限定集合中：`pageReading, findSystem, findSystem_MFHP, colorTheShape, connectTheDots, findPair, pointAndRead, drawAndPaint!')
                        # 8. 除非是-1000目录，否则JSON根结点一定包含question字段。

                        if not 'question' in label_json and path.split('/')[-1] != '-1000':
                            error_list.append(f'{label_json_path} 的根结点未包含`question`字段`!')
                        # 9. 除非pageType为pointAndRead，除非是-1000目录，否则JSON根结点一定包含answer字段
                        if not answer and path.split('/')[-1] != '-1000' and page_type != 'pointAndRead':
                            error_list.append(f'{label_json_path} 的根结点未包含`answer`字段`!')
                        # 10. 当pageType为colorTheShape/connectTheDots/findPair/drawAndPaint时，JSON根结点一定包含validArea字段
                        if page_type in set(['findPair', 'drawAndPaint']) and not valid_area:
                            error_list.append(f'{label_json_path} 的根结点未包含`validArea`字段`!')

                        # 12. answer字段必须表示数组，且数组长度必须大于等于1。
                        if 'answer' in label_json:
                            if not type(answer) == list:
                                error_list.append(f'{label_json_path} 的`answer`字段`必须表示数组!')
                            else:
                                if not len(answer) >= 1:
                                    error_list.append(f'{label_json_path} 的`answer`字段`数组长度必须大于等于1!')
                                else:
                                    n_answer_item = 0
                                    answer_item_id_set = set()  # 验证answer数组元素中的id字段唯一
                                    # 22. answer数组元素一定包含id字段，且每个元素的id一定是唯一的。
                                    for item in label_json.get('answer'):
                                        if not 'id' in item:
                                            error_list.append(f'{label_json_path} 的`answer`数组的第{n_answer_item}个字典元素缺少`id`字段!')
                                        else:
                                            if item.get('id') in answer_item_id_set:
                                                error_list.append(f'{label_json_path} 的`answer`数组的第{n_answer_item}个字典元素的`id`字段重复!')
                                            answer_item_id_set.add(item.get('id'))
                                    n_answer_id_ok = 0  # 记录answer中有效的answerID
                                    id_answerid = {}  # 记录answer中有效的answerID和对应的元素id
                                    for item in label_json.get('answer'):  # 校验answer数组中的每一个元素
                                        n_answer_item += 1
                                        # 23. 除非pageType为findPair，否则answer数组元素一定包含answerAudio字段，且值一定是.ogg或者.mp3后缀，且一定能在label.json同目录下找到相应命名的文件。
                                        if page_type not in set(['findPair', 'colorTheShape', 'connectTheDots']):
                                            if not 'answerAudio' in item:
                                                error_list.append(f'{label_json_path} 的`answer`数组的第{n_answer_item}个字典元素缺少‘answerAudio’字段!')
                                            else:
                                                if not item.get('answerAudio')[-4:] in set(['.mp3', '.ogg']):
                                                    error_list.append(f'{label_json_path} 的`answer`数组的第{n_answer_item}个字典元素的‘answerAudio’字段值不符合规定的`.mp3, .ogg!`')
                                                else:
                                                    if not os.path.isfile(path + '/' + item.get('answerAudio')):
                                                        error_list.append(f'{label_json_path} 的`answer`数组的第{n_answer_item}个字典元素的‘answerAudio’字段值对应的文件不存在于当前文件夹下')
                                        # 24. 当pageType为colorTheShape/connectTheDots/drawAndPaint时，answer数组元素一定包含answerText字段，且值不为空。
                                        if page_type in set(['drawAndPaint']):
                                            if not 'answerText' in item:
                                                error_list.append(f'{label_json_path} 的`answer`数组的第{n_answer_item}个字典元素缺少‘answerText’字段!')
                                            else:
                                                if not item.get('answerText'):
                                                    error_list.append(f'{label_json_path} 的`answer`数组的第{n_answer_item}个字典元素的‘answerText’字段的值为空!')
                                        # 25. 当pageType为findPair时，answer数组元素一定包含answersID字段，且answersID的值为整型数组.
                                        if page_type == 'findPair':
                                            if not 'answersID' in item:
                                                error_list.append(f'{label_json_path} 的`answer`数组的第{n_answer_item}个字典元素缺少‘answersID’字段!')
                                            else:
                                                if not type(item.get('answersID')) == list:
                                                    error_list.append(f'{label_json_path} 的`answer`数组的第{n_answer_item}个字典元素的‘answersID’字段不是数组!')
                                                else:
                                                    if len(item.get('answersID')) == 1:  # 有且只有两个不为空的answerID
                                                        n_answer_id_ok += 1
                                                        if 'id' in item:
                                                            id_answerid[item.get('id')] = item.get('answersID')[0]
                                        # 26. answer数组元素一定包含geometry字段，且geometry字段必须表示数组，且数组长度必须大于等于1。
                                        #     当pageType为findSystem/findSystem_MFHP/pointAndRead/findPair时，数组长度必须等于4。geometry字段中点的坐标值一定是0-1范围内的浮点数。
                                        if not 'geometry' in item:
                                            error_list.append(f'{label_json_path} 的`answer`数组的第{n_answer_item}个字典元素缺少`geometry`字段!')
                                        else:
                                            if not type(item.get('geometry')) == list:
                                                error_list.append(f'{label_json_path} 的`answer`数组的第{n_answer_item}个字典元素的`geometry`字段值不是数组!')
                                            else:
                                                if not len(item.get('geometry')) >= 1:
                                                    error_list.append(f'{label_json_path} 的`answer`数组的第{n_answer_item}个字典元素的`geometry`数组长度小于1!')
                                                if page_type in set(['findSystem', 'findSystem_MFHP', 'pointAndRead', 'findPair']) and not len(item.get('geometry')) == 4:
                                                    error_list.append(f'{label_json_path} 的`answer`数组的第{n_answer_item}个字典元素的`geometry`数组长度不等于4!')
                                            # geometry字段中点的坐标值一定是0-1范围内的浮点数。
                                            n_xy_in_geometry = 0  # 记录错误的xy的位置
                                            for xy in item.get('geometry'):
                                                x = xy.get('x')
                                                y = xy.get('y')
                                                if not (x >= 0 and x <= 1):
                                                    error_list.append(f'{label_json_path} 的`answer`数组的第{n_answer_item}个字典元素的`geometry`数组中的第{n_xy_in_geometry}组 x 坐标不在0~1范围内!')
                                                if not (y >= 0 and y <= 1):
                                                    error_list.append(f'{label_json_path} 的`answer`数组的第{n_answer_item}个字典元素的`geometry`数组中的第{n_xy_in_geometry}组 y 坐标不在0~1范围内!')
                                    # 配对题: 校验完四个answer的item，4个中只有两个配对,必须有且只有两个item的answerID的值不为空
                                    if page_type == 'findPair':
                                        if not n_answer_id_ok >= 2:
                                            error_list.append(f'{label_json_path} 的`answer`数组中‘answersID’值不为空的元素的数量不为2，要求有且只有2个元素的answerID值不为空!')
                                        else:  # 且不为空的两个answerID指向对方的answer的ID
                                            for key in id_answerid:
                                                if not id_answerid.get(id_answerid.get(key)) == key:
                                                    error_list.append(f'{label_json_path} 的`answer`数组的第{n_answer_item}个字典元素的‘answersID’的值`{id_answerid.get(key)}`没有对应的答案id值!')
                        # 11. question字段必须表示数组，且数组长度必须大于等于1
                        if 'question' in label_json and not type(question) == list:
                            error_list.append(f'{label_json_path} 的`question`字段`必须表示数组!')
                        elif 'question' in label_json and  not len(question) >= 1:
                            error_list.append(f'{label_json_path} 的`question`字段`数组长度必须大于等于1!')
                        elif 'question' in label_json:
                        # 14. question数组元素一定包含id字段，且每个元素的id一定是唯一的。
                            n = 0  # 记录第几个字典缺少"id"键
                            id_set = set()
                            for dic_ques_item in question:  # 校验数组中的每一个字典
                                n += 1
                                # 26. 如果类别为connectTheDots，question字段的元素一定包含questionAudio，questionImage和questionText，
                                # 其中questionText不为空，questionAudio值一定是.ogg或者.mp3后缀，且一定能在label.json同目录下找到相应命名的文件。
                                # questionImage一定是.png后缀，且一定能在label.json同目录下找到相应命名的文件。
                                if page_type == 'connectTheDots':
                                    for item in ['questionAudio', 'questionImage', 'questionText']:
                                        if not item in dic_ques_item:
                                            error_list.append(f'{label_json_path} 的`question`对应的数组中第{n}个字典缺少了’{item}’字段!')
                                        if 'questionText' in dic_ques_item and not dic_ques_item.get('questionText'):
                                            error_list.append(f'{label_json_path} 的`question`对应的数组中第{n}个字典的`questionText`字段为空!')
                                        if 'questionAudio' in dic_ques_item and not dic_ques_item.get('questionAudio')[-4:] in ['.ogg', '.mp3']:
                                            error_list.append(f'{label_json_path} 的`question`对应的数组中第{n}个字典`questionAudio`值不是.ogg或者.mp3后缀!')
                                        if 'questionAudio' in dic_ques_item and dic_ques_item.get('questionAudio')[-4:] in ['.ogg', '.mp3']:
                                            if not os.path.exists(path + '/' + dic_ques_item.get('questionAudio')):
                                                error_list.append(f'{label_json_path} 的`question`对应的数组中第{n}个字典的`questionAudio`对应文件不存在!')
                                        # questionImage一定是.png后缀，且一定能在label.json同目录下找到相应命名的文件
                                        if 'questionImage' in dic_ques_item and not dic_ques_item.get('questionImage')[-4:] == '.png':
                                            error_list.append(f'{label_json_path} 的`question`对应的数组中第{n}个字典`questionImage`值不是.png后缀!')
                                        if 'questionImage' in dic_ques_item and dic_ques_item.get('questionImage')[-4:] == '.png':
                                            if not os.path.exists(path + '/' + dic_ques_item.get('questionImage')):
                                                error_list.append(f'{label_json_path} 的`question`对应的数组中第{n}个字典的`questionImage`对应文件不存在!')
                                if not "id" in dic_ques_item:
                                    error_list.append(f'{label_json_path} 的`question`对应的数组中第{n}个字典缺少了’id’字段!')
                                else:
                                    if dic_ques_item.get("id") in id_set:
                                        error_list.append(f'{label_json_path} 的`question`对应的数组中第{n}个字典中的’id’值重复!')
                                    else:
                                        id_set.add(dic_ques_item.get("id"))
                        # 15. question数组元素一定包含questionAudio字段，且值一定是.ogg或者.mp3后缀，且一定能在label.json同目录下找到相应命名的文件。
                                if not "questionAudio" in dic_ques_item:
                                    error_list.append(f'{label_json_path} 的`question`对应的数组中第{n}个字典缺少了’questionAudio’字段!')
                                else:
                                    if not dic_ques_item.get("questionAudio")[-4:] in set([".ogg", ".mp3"]):
                                        error_list.append(f'{label_json_path} 的`question`对应的数组中第{n}个字典中的`questionAudio`字段值不是.ogg或者.mp3后缀!')
                                    else:
                                        if not os.path.isfile(path + '/' + dic_ques_item.get("questionAudio")):
                                            error_list.append(f'{label_json_path} 的`question`对应的数组中第{n}个字典中的`questionAudio`字段值对应文件`{dic_ques_item.get("questionAudio")}`不存在于当前文件夹!')
                                # 16. 除非pageType为pointAndRead,colorTheShape，否则question数组元素一定包含questionImage字段，且值一定是.png后缀，且一定能在label.json同目录下找到相应命名的文件。
                                if not page_type in set(["pointAndRead", "colorTheShape"]) and not "questionImage" in dic_ques_item:
                                    error_list.append(f'{label_json_path} 的`question`对应的数组中第{n}个字典缺少了`questionImage`字段!')
                                elif not page_type == "pointAndRead":
                                    if dic_ques_item.get("questionImage"):
                                        if not dic_ques_item.get("questionImage")[-4:] in set([".png",]):
                                            error_list.append(f'{label_json_path} 的`question`对应的数组中第{n}个字典中的`questionImage`字段值不是.png后缀!')
                                        else:
                                            if not os.path.isfile(path + '/' + dic_ques_item.get("questionImage")):
                                                error_list.append(f'{label_json_path} 的`question`对应的数组中第{n}个字典中的`questionImage`字段值对应文件不存在于当前文件夹!')
                                # 17. 当pageType为findSystem/findSystem_MFHP/pointAndRead/findPair时，question数组元素一定包含questionText字段，且值不为空。
                                if page_type in set(['findSystem', 'findSystem_MFHP', 'pointAndRead', 'findPair']):
                                    if not 'questionText' in dic_ques_item:
                                        error_list.append(f'{label_json_path} 的`question`对应的数组中第{n}个字典中缺少`questionText`字段!')
                                    else:
                                        if not dic_ques_item.get("questionText"):
                                            error_list.append(f'{label_json_path} 的`question`对应的数组中第{n}个字典中的`questionText`字段为空!')
                                # 18. 当pageType为findSystem/findSystem_MFHP时，question数组元素一定包含questionType字段，且值必须限定为point/bookMoving/question之一。
                                # 21. 当pageType为findSystem/findSystem_MFHP时，question数组元素一定包含answersID字段。且answersID的值为整型数组，且数组长度必须大于等于1。
                                #     数组中的值必须是answer数组元素的id字段的值，且值不能出现重复。根据ID，判断是否存在对应的answer标注信息。
                                if page_type in set(['findSystem', 'findSystem_MFHP']):
                                    if not 'questionType' in dic_ques_item:
                                        error_list.append(f'{label_json_path} 的`question`对应的数组中第{n}个字典中缺少`questionType`字段!')
                                    else:
                                        if not dic_ques_item.get('questionType') in set(['point', 'bookMoving', 'question']):
                                            error_list.append(f"{label_json_path} 的`question`对应的数组中第{n}个字典中`questionType`字段值不在设定值中：'point', 'bookMoving', 'question'!")
                                    if not 'answersID' in dic_ques_item:
                                        error_list.append(f'{label_json_path} 的`question`对应的数组中第{n}个字典中缺少`answersID`字段!')
                                    else:  # answersID的值为整型数组，且数组长度必须大于等于1
                                        if not type(dic_ques_item.get('answersID')) == list:
                                            error_list.append(f'{label_json_path} 的`question`对应的数组中第{n}个字典中`answersID`字段不是数组!')
                                        else:
                                            n_num = 0  # 校验answersID数组中的元素
                                            for item in dic_ques_item.get('answersID'):
                                                n_num += 1
                                                if not type(item) == int:
                                                    error_list.append(f'{label_json_path} 的`question`对应的数组中第{n}个字典中`answersID`数组的第{n_num}个元素不是整数!')
                                                else:
                                                    if not item in answer_item_id_set:
                                                        error_list.append(f'{label_json_path} 的`question`对应的数组中第{n}个字典中`question`字段中的`answersID`数组的元素`{item}`，在JSON根目录下的`answer`字段中没有元素有对应的id字段!')
                                            if not len(dic_ques_item.get('answersID')) >= 1:
                                                error_list.append(f'{label_json_path} 的`question`对应的数组中第{n}个字典中`answersID`数组的长度不应该小于1!')
                                            else:
                                                if not len(set(dic_ques_item.get('answersID'))) == len(dic_ques_item.get('answersID')):
                                                    error_list.append(f'{label_json_path} 的`question`对应的数组中第{n}个字典中`answersID`数组的元素有重复!')

                                # 19. question数组元素一定包含geometry字段，且geometry字段必须表示数组，且数组长度必须大于等于1。geometry字段中点的坐标值一定是0-1范围内的浮点数。
                                if not 'geometry' in dic_ques_item:
                                    error_list.append(f'{label_json_path} 的`question`对应的数组中第{n}个字典中缺少`geometry`字段!')
                                else:
                                    if not type(dic_ques_item.get('geometry')) == list:
                                        error_list.append(f'{label_json_path} 的`question`对应的数组中第{n}个字典中的`geometry`字段不是数组!')
                                    else:
                                        if len(dic_ques_item.get('geometry')) < 1:
                                            error_list.append(f'{label_json_path} 的`question`对应的数组中第{n}个字典中的`geometry`数组长度小于1!')
                                        else:
                                            n_xy = 0  # 记录第几个坐标有问题
                                            for xy in dic_ques_item.get('geometry'):  # 校验坐标
                                                n_xy += 1
                                                if  not (xy.get('x') >= 0 and xy.get('x') <= 1 and xy.get('y') >= 0 and xy.get('y') <= 1):
                                                    error_list.append(f'{label_json_path} 的`question`对应的数组中第{n}个字典中的`geometry`中的第{n_xy}组坐标不是0-1范围内的浮点数!')

                        # 20. question数组元素不一定包含checkMark字段，如果包含，值必须限定为yes/no。
                                if 'checkMark' in dic_ques_item and not dic_ques_item.get('checkMark') in set(['yes', 'no']):
                                    error_list.append(f'{label_json_path} 的`question`对应的数组中第{n}个字典中有checkMark字段，但值不为yes/no!')
                        # 30. 如果类别为connectTheDots和colorTheShape，-
                        # 一定存在questionLevel1,uestionLevel2和questionLevel3三个字段，-
                        # 这三个字段下，必然包含answersID-，且ID对应到answer字段下的id，-
                        # 同时，三个字段下均包含questionAudio和questionImage，-
                        # questionAudio值一定是.ogg或者.mp3后缀，且一定能在label.json同目录下找到相应命名的文件-
                        # questionImage一定是.png后缀，且一定能在label.json同目录下找到相应命名的文件-
                        if page_type in set(['connectTheDots', 'colorTheShape']):
                            if not "questionLevel1" in label_json:
                                error_list.append(f'{label_json_path} 的根节点下缺少`questionLevel1`字段!')
                            elif not 'questionLevel2' in label_json:
                                error_list.append(f'{label_json_path} 的根节点下缺少`questionLevel2`字段!')
                            elif not 'questionLevel3' in label_json:
                                error_list.append(f'{label_json_path} 的根节点下缺少`questionLevel3`字段!')
                            else:
                                for question_level in ['questionLevel1', 'questionLevel2', 'questionLevel3']:
                                    count_question_level_item = 0
                                    for question_level_item in label_json.get(question_level):
                                        count_question_level_item += 1
                                        if not 'answersID' in question_level_item:
                                            error_list.append(f'{label_json_path} 的`{question_level}`节点的第{count_question_level_item}个元素中缺少`answersID`字段!')
                                        elif not  answer_item_id_set == set(question_level_item.get('answersID')) | answer_item_id_set:
                                            error_list.append(f'{label_json_path} 的`{question_level}`节点的第{count_question_level_item}个元素的`answersID`字段值，不是一一对应于根节点answer的元素的id!')
                                        # 三个字段下均包含questionAudio和questionImage
                                        if not 'questionAudio' in question_level_item:
                                            error_list.append(f'{label_json_path} 的`{question_level}`节点缺少`questionAudio`字段!')
                                        else:
                                            # questionAudio值一定是.ogg或者.mp3后缀，且一定能在label.json同目录下找到相应命名的文件
                                            if not question_level_item.get('questionAudio')[-4:] in set(['.ogg', '.mp3']):
                                                error_list.append(f'{label_json_path} 的`{question_level}`节点的第{count_question_level_item}个元素的`questionAudio`字段不是.ogg或者.mp3后缀!')
                                            elif not os.path.isfile(path + '/' + question_level_item.get('questionAudio')):
                                                error_list.append(f'{label_json_path} 的`{question_level}`节点的第{count_question_level_item}个元素的`questionAudio`字段对应文件{question_level_item.get("questionAudio")}不存在!')

                                        if not 'questionImage' in question_level_item:
                                            error_list.append(f'{label_json_path} 的`{question_level}`节点缺少`questionImage`字段!')
                                        else:
                                            # questionAudio值一定是.ogg或者.mp3后缀，且一定能在label.json同目录下找到相应命名的文件
                                            if not question_level_item.get('questionImage')[-4:] == '.png':
                                                error_list.append(f'{label_json_path} 的`{question_level}`节点的第{count_question_level_item}个元素的`questionImage`字段不是.png后缀!')
                                            elif not os.path.isfile(path + '/' + question_level_item.get('questionImage')):
                                                error_list.append(f'{label_json_path} 的`{question_level}`节点的第{count_question_level_item}个元素的`questionImage`字段对应文件{question_level_item.get("questionImage")}不存在!')
                        # 13. validArea字段必须表示数组，且数组长度必须大于等于1
                        if 'validArea' in label_json:
                            if not type(valid_area) == list:
                                error_list.append(f'{label_json_path} 的`validArea`字段`必须表示数组!')
                            else:
                                if not len(valid_area) >= 1:
                                    error_list.append(f'{label_json_path} 的`validArea`字段`数组长度必须大于等于1!')
                                else:
                                    # 27. validArea数组元素一定包含id字段，且每个元素的id一定是唯一的。
                                    valid_area_id_set = set()
                                    n_valid_item = 0  # 判断是数组中的哪一个元素出问题
                                    for item in valid_area:
                                        n_valid_item += 1
                                        if not 'id' in item:
                                            error_list.append(f'{label_json_path} 的`validArea`字段`的数组中第{n_valid_item}个元素没有包含`id`字段!')
                                        else:
                                            if item.get('id') in valid_area_id_set:
                                                error_list.append(f'{label_json_path} 的`validArea`字段`数组中`id`字段重复!')
                                            else:
                                                valid_area_id_set.add(item.get('id'))
                                        # 28. validArea数组元素一定包含geometry字段，且geometry字段必须表示数组，且数组长度必须等于4。geometry字段中点的坐标值一定是0-1范围内的浮点数。
                                        if not 'geometry' in item:
                                            error_list.append(f'{label_json_path} 的`validArea`字段`的数组中第{n_valid_item}个元素没有包含`geometry`字段!')
                                        else:
                                            if not isinstance(item.get('geometry'), list):
                                                error_list.append(f'{label_json_path} 的`validArea`字段`的数组中第{n_valid_item}个元素中的`geometry`字段值不是数组!')
                                            else:
                                                if not len(item.get('geometry')) >= 4:
                                                    error_list.append(f'{label_json_path} 的`validArea`字段`的数组中第{n_valid_item}个元素中的`geometry`数组中的元素个数不等于4!')
                                                else:
                                                    count_item_in_geometry = 0  # 记录是第几个xy错了
                                                    for g_xy in item.get('geometry'):
                                                        count_item_in_geometry += 1
                                                        g_x = g_xy.get('x')
                                                        g_y = g_xy.get('y')
                                                        if not (g_x >= 0 and g_x <=1):
                                                            error_list.append(f'{label_json_path} 的`geometry`数组的第{count_item_in_geometry}组xy的 x 坐标不在 0~1 范围内!')
                                                        if not (g_y >= 0 and g_y <=1):
                                                            error_list.append(f'{label_json_path} 的`geometry`数组的第{count_item_in_geometry}组xy的 y 坐标不在 0~1 范围内!')
                    except Exception as e:
                        raise e
                        error_list.append(f'`{path}/label.json`格式不合法!')

            elif not label_json_path[-23:-11] == 'promptAudios':
                error_list.append(f'`{path}/label.json`文件不存在!')
    if len(error_list):
        print("ERROR!!")
        for err in error_list:
            print(err)
    else:
        print("NO ERROR!!")

if __name__ == "__main__":
    # str1 = input("请输入测试文件根目录\n")
    # root_path = str1
    root_path = '/mnt/docker-store/01_yangboya_workspace/scripts/check/HL_MyFirstHiddenPicture_Volume2/'
    folder_integrity_check(root_path)


