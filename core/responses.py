from core.openai import *
from core.audios import *
from core.models import insert_msg,get_conversation,get_first_conversation_dia_type
from feishu.api import MessageApiClient

# init service
message_api_client = MessageApiClient(APP_ID, APP_SECRET, LARK_HOST)

def dia_choice(parent_id, root_id, message_id, content,characteristic, filepath='', dialogue=0,ingore_type=0):
    dia_type = get_first_conversation_dia_type(message_id,root_id)
    if ingore_type == 1:
        resp_text,message_id, parent_id, root_id = deal_text_response(parent_id, root_id, message_id, content,characteristic)
        return resp_text,message_id, parent_id, root_id
    elif ingore_type == 2:
        deal_audio_response(parent_id, root_id, message_id, content,characteristic,filepath,dialogue)

    elif dia_type == 'audio':
        deal_audio_response(parent_id, root_id, message_id, content,characteristic,filepath,dialogue)
    elif dia_type == 'text':
        deal_text_response(parent_id, root_id, message_id, content,characteristic)


# 回复音频功能集合
def deal_audio_response(parent_id, root_id, message_id, content,characteristic, filepath, dialogue):

    resp_text = deal_dialogues(parent_id, root_id,message_id,content)
    duration_ms = generate_audio(resp_text, filepath,dialogue)
    if duration_ms==None:
        if audio_mode == 'azure':
            message_api_client.reply_send(message_id, 'azure语音服务的额度已经用完', 'text')
        return
    filekey = message_api_client.upload_audio_file(filepath, duration_ms)
    message_id,parent_id,root_id,file_key = message_api_client.reply_send(message_id, filekey, 'audio')
    #插入返回数据
    insert_msg(message_id, root_id, parent_id, resp_text, 'text', characteristic, 'ai','',file_key,filepath)


    if text_and_audio != 0:
        message_api_client.reply_send(message_id, resp_text, 'text')

# 回复文本功能集合
def deal_text_response(parent_id, root_id, message_id, content,characteristic):

    resp_text = deal_dialogues(parent_id, root_id, message_id, content)

    message_id, parent_id, root_id, content = message_api_client.reply_send(message_id, resp_text, 'text')
    # 插入返回数据
    insert_msg(message_id, root_id, parent_id, resp_text, 'text', characteristic, 'ai','')
    return resp_text,message_id, parent_id, root_id

def deal_dialogues(parent_id,root_id,message_id,text_content):
    if len(parent_id)==0 and len(root_id)==0:
        msgs = [
            {
                "role": "user", "content": text_content
            }
        ]
        resp_text =send_ai(msgs)

    else:
        msgs = get_conversation(message_id)
        resp_text =send_ai(msgs)


    return resp_text


