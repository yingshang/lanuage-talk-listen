from flask import Flask,jsonify

from core.models import *
from core.core import text_choice,emoji_choice
from core.config import *
import os


app = Flask(__name__)

# 记录对话上下文
cwd = os.getcwd()
chatfile_path = os.path.join(cwd,'chatfile')
file_path = os.path.join(cwd,'file')
if not os.path.exists(chatfile_path):
    os.makedirs(chatfile_path)
    #print("文件夹创建成功！")
if not os.path.exists(file_path):
    os.makedirs(file_path)



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
    #root_id, parent_id = get_root_and_parent_id_by_message_id(message_id)
    root_id,parent_id = message_api_client.get_message(message_id)

    if root_id==None:
        root_id=''
    if parent_id ==None:
        parent_id =''


    characteristic = message_id+"_"+emoji_type

    #用来判断message_id，防止重放数据
    message_status = is_characteristic_exist(characteristic)
    if message_status:
        return jsonify()


    emoji_choice(root_id, parent_id,message_id,emoji_type,characteristic)

    return jsonify()


@event_manager.register("im.message.receive_v1")
def message_receive_event_handler(req_data: MessageReceiveEvent):
    message = req_data.event.message
    message_id = message.message_id
    msgcontent = message.content

    try:
        root_id = message.root_id
    except:
        root_id = ''
    try:
        parent_id = message.parent_id
    except:
        parent_id = ''

    message_type=message.message_type

    #用来判断message_id，防止重放数据
    message_status = is_characteristic_exist(message_id)


    if message_status:
        return jsonify()

    text_choice(message_id, root_id, parent_id, message_type, msgcontent)

    return jsonify()




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