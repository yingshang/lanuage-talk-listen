from core.tencent import speech_recognition
from feishu.helper import *
import os
from core.scenes import scene,school_scenes,academic_scenes,toefl_scenes
from core.responses import *
from datetime import datetime
import json
from core.config import *
from core.models import *
from core.english import toefl_load_independent_file
import string
from feishu.api import MessageApiClient
from core.english import get_listen_school_scene,get_listen_academic_scene

# init service
message_api_client = MessageApiClient(APP_ID, APP_SECRET, LARK_HOST)

topics_list = ['随机话题','讲座','学校','xx','jz']
values_list = ['独立口语1','t1']
cwd = os.getcwd()
chatfile_path = os.path.join(cwd,'chatfile')


def feishu_type_choice(message_id,root_id,parent_id,message_type,msgcontent):
    random_string = ''.join(random.sample(string.ascii_lowercase + string.digits, 32))
    msg_id = "om_{}".format(random_string)
    now = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    filepath = os.path.join(chatfile_path, f"{now}.opus")

    characteristic = message_id
    if message_type == "text":
        text_content = json.loads(msgcontent)['text']
        insert_msg(message_id, root_id, parent_id, text_content, message_type, characteristic, 'receive', 'text')

        if text_content == "帮助列表" or text_content== "bz":
            message_api_client.reply_send(message_id, feishu_help_text, 'post')

        elif text_content == "余额" or text_content=="ye":
            hard_limit_usd, total_usage = check_price()
            resp_text = "授权金额:{}\n\n总共使用:{}".format(hard_limit_usd, total_usage)
            message_api_client.reply_send(message_id, resp_text, 'text')

        elif "查询" in text_content:
            text_content = text_content.replace("查询", "").strip()
            dia_choice(parent_id, root_id, message_id, text_content,characteristic)

        elif "英文播放" in text_content:
            text_content = text_content.replace("英文播放", "").strip()
            duration_ms = generate_audio(text_content, filepath, dialogue=0)
            filekey = message_api_client.upload_audio_file(filepath, duration_ms)
            message_api_client.reply_send(message_id, filekey, 'audio')

        elif "录入单词" in text_content:
            contents = text_content.replace("录入单词", "").strip().split("\n")
            new_words, total_words = read_write_words(contents)
            message_api_client.reply_send(message_id, f'录入单词完成,更新{new_words}个单词,总共{total_words}个单词', 'text')

        elif "词汇阅读" == text_content or "chyd"==text_content:
            words = get_random_words()
            if words != None:
                text_content = scene['词汇阅读'].format(",".join(words))
                dia_choice(parent_id, root_id, message_id, text_content,characteristic)
            else:
                resp_text = '触发错误，确定是否录入单词。'
                message_api_client.reply_send(message_id, resp_text, 'text')

        elif "英语对话" in text_content:
            content = text_content.replace("英语对话", "").strip()
            text_content = scene['英语对话'].format(content)
            update_dia_type(message_id,'audio')
            dia_choice(parent_id, root_id, message_id, text_content,characteristic,filepath)

        elif text_content=="学校听力场景总览" or text_content=='xxtlcjzl':
            resp_text = get_listen_school_scene()
            message_api_client.reply_send(message_id, resp_text, 'post')

        elif text_content=="讲座听力场景总览" or text_content=='jztlcjzl':
            resp_text = get_listen_academic_scene()
            message_api_client.reply_send(message_id, resp_text, 'post')

        elif text_content in topics_list:
            update_dia_type(message_id,'audio')

            if text_content =='学校' or text_content=='xx':
                sc_scene = random.choice(list(school_scenes.keys()))
                value = school_scenes[sc_scene]
                sc_selected = random.choice(value)
                content = scene['学校'].format(sc_scene,sc_selected,sc_scene)
                dia_choice(parent_id, root_id, message_id, content, characteristic, filepath,dialogue=1)


            elif text_content=="讲座" or text_content=='jz':
                content = scene['讲座'].format(random.choice(academic_scenes))
                dia_choice(parent_id, root_id, message_id, content, characteristic, filepath)

            else:
                content = scene[text_content]
                dia_choice(parent_id, root_id, message_id, content, characteristic, filepath)


        #指定一个学校的听力场景
        elif text_content in list(school_scenes.keys()):
            update_dia_type(message_id,'audio')
            value = school_scenes[text_content]
            sc_selected = random.choice(value)
            content = scene['学校'].format(text_content, sc_selected, text_content)
            dia_choice(parent_id, root_id, message_id, content, characteristic, filepath, dialogue=1)

        # 指定一个讲座的听力场景 
        elif text_content in academic_scenes:
            update_dia_type(message_id,'audio')
            content = scene['讲座'].format(text_content)
            dia_choice(parent_id, root_id, message_id, content, characteristic, filepath)


        elif "独立口语1" == text_content or 't1' == text_content:
            title = get_random_toefl_independent_title()

            duration_ms = generate_audio(title, filepath, dialogue=0)
            file_key = message_api_client.upload_audio_file(filepath, duration_ms)
            message_id, parent_id, root_id, content = message_api_client.reply_send(message_id, file_key, 'audio')
            insert_msg(message_id, root_id, parent_id, title, message_type, characteristic, 'send', 'audio',file_key, filepath)
        elif "独立口语2" == text_content  or 't2' == text_content:
            content = random.choice(toefl_scenes['oral_task2'])
            resp_text,message_id, parent_id, root_id = dia_choice(parent_id, root_id, message_id, content, characteristic, ingore_type=1)
            #发送对话音频
            now = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
            filepath = os.path.join(chatfile_path, f"{now}.opus")
            content = scene['托福独立口语task2意见生成']
            insert_msg(msg_id, root_id, message_id, content, 'text', msg_id, 'receive', '')

            dia_choice(parent_id, root_id, message_id, content, message_id,filepath,ingore_type=2,dialogue=1)






        elif "口语评分" in text_content:
            content = text_content.replace("口语评分", "").strip()
            filepath = get_filepath_by_parent_id(parent_id)

            wav_filepath = to_wavfile(filepath)
            msgs = pronunciation_assessment_continuous_from_file(content,wav_filepath)
            message_api_client.reply_send(message_id, msgs, 'text')


        elif "扮演" in text_content:
            content = text_content.replace("扮演", "").strip()
            text_content = scene['扮演角色'].format(content)
            update_dia_type(message_id,'audio')
            dia_choice(parent_id, root_id, message_id, text_content,characteristic, filepath)

        elif "词汇题" == text_content or "cht" ==text_content:
            words = get_random_words(1)
            if words != None:
                word = words[0]
                text_content = scene['词汇题'].format(word, word)
                dia_choice(parent_id, root_id, message_id, text_content,characteristic)

            else:
                resp_text = '触发错误，确定是否录入单词'
                message_api_client.reply_send(message_id, resp_text, 'text')
        elif "托福独立口语模板" ==text_content:
            filepath = "origin/托福独立口语模板.xlsx"
            filekey = message_api_client.upload_stream_file(filepath)
            message_api_client.reply_send(message_id, filekey, 'file')


        else:
            content = get_content_by_root_id(root_id)
            if content in values_list:
                title = get_content_by_parent_id(root_id)
                if content=="独立口语1" or content == 't1':
                    text_content = scene['托福独立口语task1批改'].format(title,text_content)

                    update_content_by_message_id(message_id,text_content)

                    dia_choice(parent_id, root_id, message_id, text_content, characteristic)

            else:
                update_dia_type(message_id,'audio')
                dia_choice(parent_id, root_id, message_id, text_content,characteristic,filepath)


    elif message_type == 'audio':
        audio_content = json.loads(msgcontent)
        file_key = audio_content['file_key']
        message_api_client.download_file(message_id, file_key, filepath)
        #获取音频文本
        speech_text = speech_recognition(filepath, TencentSecretId, TencentSecretKey)
        insert_msg(message_id, root_id, parent_id, speech_text, message_type, characteristic,'receive','audio',file_key,filepath)

        content = get_content_by_root_id(root_id)
        if content in values_list:
            title = get_content_by_parent_id(root_id)
            if content == "独立口语1" or content=='t1':
                text_content = scene['托福独立口语task1批改'].format(title, speech_text)
                update_content_by_message_id(message_id, text_content)

                dia_choice(parent_id, root_id, message_id, text_content, characteristic)
        else:

            dia_choice(parent_id, root_id, message_id, speech_text,characteristic,filepath)

    elif message_type == 'file':
        file_content = json.loads(msgcontent)
        file_name = file_content['file_name']
        file_key = file_content['file_key']
        file = "file/托福独立口语题目.xlsx"
        if file_name == '托福独立口语题目.xlsx':
            message_api_client.download_file(message_id, file_key, file)
            total,num = toefl_load_independent_file(file)
            resp_text = '录入总数为：{}条记录，新增{}条记录，重复{}条记录'.format(total,num,total-num)
            message_api_client.reply_send(message_id, resp_text, 'text')


def feishu_emoji_choice(root_id, parent_id,message_id,emoji_type,characteristic):
    random_string = ''.join(random.sample(string.ascii_lowercase + string.digits, 32))
    msg_id = "om_{}".format(random_string)
    now = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    filepath = os.path.join(chatfile_path, f"{now}.opus")
    #print(emoji_type)
    # 原文
    if emoji_type == 'THUMBSUP':
        resp_text = get_content_by_message_id(message_id)
        message_id,parent_id,root_id,content = message_api_client.reply_send(message_id, resp_text, 'text')
        insert_msg(message_id, root_id, parent_id, resp_text,'text', characteristic,'send','')

    # 单词分析
    elif emoji_type == 'HEART':
        resp_text = get_content_by_message_id(message_id)
        content = scene['单词分析'].format(resp_text)
        dia_choice(parent_id, root_id, message_id, content,characteristic,ingore_type=1)


    elif emoji_type == 'SMILE':
        content = scene['阅读题目']
        insert_msg(msg_id, root_id, message_id, content, 'text', characteristic, 'receive', '')
        dia_choice(parent_id, root_id, message_id, content,characteristic,ingore_type=1)


    elif emoji_type == 'Delighted':
        content = scene['阅读答案']
        insert_msg(msg_id, root_id, message_id, content, 'text', characteristic, 'receive', '')

        dia_choice(parent_id, root_id, message_id, content,characteristic,ingore_type=1)


    elif emoji_type == 'MUSCLE':
        resp_text = get_content_by_message_id(message_id)
        duration_ms = generate_audio(resp_text, filepath, dialogue=0)
        filekey = message_api_client.upload_audio_file(filepath, duration_ms)
        message_id,parent_id,root_id,content = message_api_client.reply_send(message_id, filekey, 'audio')
        insert_msg(message_id, root_id, parent_id, resp_text,'text', characteristic,'send','')


    elif emoji_type =='THANKS':
        resp_text = get_content_by_message_id(message_id)

        content = scene['语法批改'].format(resp_text)
        insert_msg(msg_id, root_id, message_id, content, 'text', characteristic, 'receive', '')

        dia_choice(parent_id, root_id, message_id, content, characteristic, ingore_type=1)

    elif emoji_type =='OK':
        filepath = get_filepath_by_message_id(message_id)
        # 将音频文件以文件方式发送出来，用于上传到空间，后台听音频。
        filekey = message_api_client.upload_stream_file(filepath)
        message_id,parent_id,root_id,content = message_api_client.reply_send(message_id, filekey, 'file')
        insert_msg(message_id, root_id, parent_id, '', 'audio', characteristic,'send','',filekey,filepath)

    #托福独立口语task1答案生成
    elif emoji_type =='LAUGH':
        resp_text = get_content_by_message_id(message_id)
        content = scene['托福独立口语task1答案生成'].format(resp_text)
        insert_msg(msg_id, root_id, message_id, content, 'text', characteristic, 'receive', '')

        dia_choice(parent_id, root_id, message_id, content, characteristic)


