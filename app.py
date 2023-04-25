from flask import Flask,jsonify
import logging
from core.tencent import speech_recognition
from core.helper import *
from core.english import read_write_words,random_words,random_speak_title
from core.scenes import scene,school_scenes
from core.responses import *
import random


app = Flask(__name__)



@event_manager.register("url_verification")
def request_url_verify_handler(req_data: UrlVerificationEvent):
    # url verification, just need return challenge
    if req_data.event.token != VERIFICATION_TOKEN:
        raise Exception("VERIFICATION_TOKEN is invalid")
    return jsonify({"challenge": req_data.event.challenge})



#https://open.feishu.cn/document/uAjLw4CM/ukTMukTMukTM/reference/im-v1/message-reaction/events/created
@event_manager.register("im.message.reaction.created_v1")
def reaction_receive_event_handler(req_data: MessageReactionCreateEvent):

    message_id = req_data.event.message_id
    reaction_type = req_data.event.reaction_type
    emoji_type = reaction_type.emoji_type
    root_id = message_api_client.get_message(message_id)

    # 防止重放消息
    record_file = os.path.join(cwd, "file/resp.txt")
    if not os.path.isfile(record_file):
        with open(record_file, "w") as file:
            pass
    f = open(record_file, "r", encoding='utf-8')
    record = f.read()
    f.close()
    characteristic = message_id+","+emoji_type
    if characteristic not in record:
        fr = open(record_file, "a+", encoding='utf-8')
        fr.write(characteristic + "\n")
        fr.close()
    else:
        return jsonify()

    #print(emoji_type)

    #原文
    if emoji_type=='THUMBSUP':
        try:
            resp_text = dialogues[root_id][-1]['content']
        except:
            resp_text = '确定以上内容是否有原文'
        message_api_client.reply_send(message_id, resp_text, 'text')
    #单词分析
    elif emoji_type == 'HEART':
        try:
            text = dialogues[root_id][-2]['content']
        except:
            text = '确定以上内容是否有原文'
        content = scene['单词分析'].format(text)
        msg = [{'role': 'user', 'content': content}]
        resp_text = send_ai(msg,AiKey)
        message_api_client.reply_send(message_id, resp_text, 'text')

    elif emoji_type == 'SMILE':
        content = scene['阅读题目']
        resp_text = deal_dialogues(dialogues, root_id, root_id, message_id, content, AiKey)
        message_api_client.reply_send(message_id, resp_text, 'text')


    elif emoji_type == 'Delighted':
        content = scene['阅读答案']
        resp_text = deal_dialogues(dialogues, root_id, root_id, message_id, content, AiKey)
        message_api_client.reply_send(message_id, resp_text, 'text')


    return jsonify()


@event_manager.register("im.message.receive_v1")
def message_receive_event_handler(req_data: MessageReceiveEvent):
    message = req_data.event.message
    message_id = message.message_id
    # 防止重放消息
    record_file = os.path.join(cwd,"file/record.txt")
    if not os.path.isfile(record_file):
        with open(record_file, "w") as file:
            pass
    f = open(record_file, "r", encoding='utf-8')
    record = f.read()
    f.close()
    if message_id not in record:
        fr = open(record_file, "a+", encoding='utf-8')
        fr.write(message_id+"\n")
        fr.close()
    else:
        return jsonify()

    try:
        root_id = message.root_id
    except:
        root_id = ''
    try:
        parent_id = message.parent_id
    except:
        parent_id = ''

    message_type=message.message_type

    now = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')

    filepath = os.path.join(chatfile_path,f"{now}.opus")

    if message_type == "text":
        text_content = json.loads(message.content)['text']

        if text_content=="帮助列表":
            message_api_client.reply_send(message_id,help_text,'post')


        elif text_content == "余额":
            hard_limit_usd,total_usage = check_price(AiKey)
            resp_text = "授权金额:{}\n\n总共使用:{}".format(hard_limit_usd,total_usage)
            message_api_client.reply_send(message_id,resp_text,'text')

        elif text_content == "清除会话":
            global dialogues
            dialogues = {}
            resp_text = "清除会话成功，请重新创建新的会话"
            message_api_client.reply_send(message_id, resp_text, 'text')

        elif "查询" in text_content:
            text_content = text_content.replace("查询","").strip()
            resp_text = deal_dialogues(dialogues, parent_id, root_id, message_id, text_content, AiKey)
            message_api_client.reply_send(message_id, resp_text, 'text')

        elif "英文播放" in text_content:
            text_content = text_content.replace("英文播放","").strip()
            duration_ms = generate_audio(text_content,filepath,dialogue=0)
            filekey = message_api_client.upload_audio_file(filepath,duration_ms)
            message_api_client.reply_send(message_id, filekey,'audio')

        elif "录入单词" in text_content:
            contents  = text_content.replace("录入单词", "").strip().split("\n")
            new_words,total_words = read_write_words(contents)
            message_api_client.reply_send(message_id, f'录入单词完成,更新{new_words}个单词,总共{total_words}个单词', 'text')
        elif "词汇阅读" == text_content:

            words = random_words(random_word_num)
            if words!=None:
                text_content = scene['词汇阅读'].format(",".join(words))
                resp_text = deal_dialogues(dialogues, parent_id, root_id, message_id, text_content, AiKey)
                message_api_client.reply_send(message_id, resp_text, 'text')
            else:
                resp_text = '触发错误，确定是否录入单词'
                message_api_client.reply_send(message_id, resp_text, 'text')
        elif "英语对话" in text_content:
            content  = text_content.replace("英语对话", "").strip()
            content = scene['英语对话'].format(content)
            deal_response(parent_id, root_id, message_id, content,filepath,ingore_grammar=1)
        #听力场景
        elif text_content in topics_list:
            content = scene[text_content]
            deal_response(parent_id, root_id, message_id, content,filepath,ingore_grammar=1)

        elif "独立口语" == text_content:
            title = random_speak_title()
            duration_ms = generate_audio(title, filepath, dialogue=0)
            filekey = message_api_client.upload_audio_file(filepath, duration_ms)
            message_api_client.reply_send(message_id, filekey, 'audio')


        elif text_content =="原文":
            try:
                resp_text = dialogues[root_id][-1]['content']
            except:
                resp_text = '确定以上内容是否有原文'
            message_api_client.reply_send(message_id, resp_text, 'text')

        elif "扮演" in text_content:
            content  = text_content.replace("扮演", "").strip()
            text_content = scene['扮演角色'].format(content)
            deal_response(parent_id, root_id, message_id, text_content, filepath)

        elif "学校" == text_content:
            sc_scene = random.choice(list(school_scenes.keys()))
            value = school_scenes[sc_scene]
            sc_selected = random.choice(value)
            sc_content = f"根据新托福听力模板，生成{sc_scene}的英语对话，内容包括{sc_selected}等话题，两人讨论话题会延申到其他{sc_scene}话题上面。两人对话分别用P1:和P2:表示。对话内容不少于30段。"
            deal_response(parent_id, root_id, message_id, sc_content, filepath,dialogue=1)




        elif "词汇题" == text_content:
            words = random_words(random_word_num)
            if words != None:
                word = words[0]
                text_content = scene['词汇题'].format(word,word)
                resp_text = deal_dialogues(dialogues, parent_id, root_id, message_id, text_content, AiKey)
                message_api_client.reply_send(message_id, resp_text, 'text')
            else:
                resp_text = '触发错误，确定是否录入单词'
                message_api_client.reply_send(message_id, resp_text, 'text')

        else:
            deal_response(parent_id, root_id, message_id, text_content, filepath)


    elif message_type == 'audio':
        audio_content = json.loads(message.content)
        file_key = audio_content['file_key']
        message_api_client.download_audio(message_id,file_key,filepath)
        speech_text = speech_recognition(filepath,TencentSecretId,TencentSecretKey)

        deal_response(parent_id, root_id, message_id, speech_text, filepath)

    #print(dialogues)
    return jsonify()


@app.errorhandler
def msg_error_handler(ex):
    logging.error(ex)
    response = jsonify(message=str(ex))
    response.status_code = (
        ex.response.status_code if isinstance(ex, requests.HTTPError) else 500
    )
    return response


@event_manager.register("im.message.message_read_v1")
def message_read_event_handler(req_data: MessageReceiveEvent):
    return jsonify()


@app.route("/feishu/callback", methods=["POST"])
def callback_event_handler():
    # init callback instance and handle
    # try:
    event_handler, event = event_manager.get_handler_with_event(VERIFICATION_TOKEN, ENCRYPT_KEY)

    return event_handler(event)
    # except:
    #     return jsonify()


if __name__ == "__main__":
    app.run(host='0.0.0.0',port=5000)