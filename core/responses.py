from core.config import *
from core.openai import *
from core.audios import *


# 回复功能集合
def deal_response(parent_id, root_id, message_id, content, filepath, ingore_grammar=0, dialogue=0):
    grammar_modify(content, parent_id, root_id, message_id, ingore_grammar)

    resp_text = deal_dialogues(dialogues, parent_id, root_id, message_id, content, AiKey)

    duration_ms = generate_audio(resp_text, filepath,dialogue)
    filekey = message_api_client.upload_audio_file(filepath, duration_ms)
    message_api_client.reply_send(message_id, filekey, 'audio')
    if text_and_audio != 0:
        message_api_client.reply_send(message_id, resp_text, 'text')

def deal_dialogues(dialogues,parent_id,root_id,message_id,text_content,AiKey):

    if len(parent_id)==0 and len(root_id)==0:
        dialogues[message_id] = []
        dialogues[message_id].append(
            {
                "role": "user", "content": text_content
            }
        )
        resp_text =send_ai(dialogues[message_id],AiKey)

        dialogues[message_id].append(
            {
                "role": "assistant",
                "content": resp_text,
            }
        )
    else:
        dialogues[root_id].append(
            {
                "role": "user", "content": text_content
            }
        )
        resp_text =send_ai(dialogues[root_id],AiKey)
        dialogues[root_id].append(
            {
                "role": "assistant",
                "content": resp_text,
            }
        )

    return resp_text


def just_dialogues(dialogues,parent_id,root_id,message_id,text_content,AiKey):

    if len(parent_id)==0 and len(root_id)==0:
        dialogues[message_id] = []
        dialogues[message_id].append(
            {
                "role": "user", "content": text_content
            }
        )
        resp_text =send_ai(dialogues[message_id],AiKey)

    else:
        dialogues[root_id].append(
            {
                "role": "user", "content": text_content
            }
        )
        resp_text =send_ai(dialogues[root_id],AiKey)

    return resp_text


def grammar_modify(speech_text, parent_id, root_id, message_id, ingore_grammar):
    if syntactic_correction == 1 and ingore_grammar == 0:
        content = "Help me check if there are any English grammar errors in these contents: {}".format(speech_text)
        resp_text = just_dialogues(dialogues, parent_id, root_id, message_id, content, AiKey)
        message_api_client.reply_send(message_id, resp_text, 'text')
