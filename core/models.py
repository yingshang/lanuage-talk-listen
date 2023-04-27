from sqlalchemy import create_engine, Column, Integer, String,Text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound
from core.config import random_word_num
import random

# 创建一个数据库引擎
engine = create_engine('sqlite:///file/feishu.db', echo=False)

# 创建一个映射类
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

class Word(Base):
    __tablename__ = 'words'

    id = Column(Integer, primary_key=True)
    content = Column(String, unique=True)


class Msg(Base):
    __tablename__ = 'msg_table'

    id = Column(Integer, primary_key=True)
    message_id = Column(String,default='')
    root_id = Column(String,default='')
    parent_id = Column(String,default='')
    message_type = Column(String)
    operation = Column(String)
    dia_type = Column(String)
    content = Column(Text)
    file_key = Column(Text,default='')
    filepath = Column(Text,default='')
    characteristic = Column(String)


# 创建表
Base.metadata.create_all(engine)

def get_filepath_by_message_id(parent_id):
    # 创建session
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        msg = session.query(Msg).filter(Msg.message_id == parent_id).one_or_none()

        if msg:
            return msg.filepath
        else:
            return None
    finally:
        session.close()

def get_first_conversation_dia_type(message_id,root_id):
    Session = sessionmaker(bind=engine)
    session = Session()

    first_msg = None

    if root_id and root_id != '':
        # 查找具有给定root_id的第一次会话消息
        first_msg = session.query(Msg).filter(Msg.message_id == root_id).one_or_none()

    if first_msg is None:
        # 如果找不到与root_id匹配的消息，尝试使用message_id查找第一次会话
        first_msg = session.query(Msg).filter(Msg.message_id == message_id, Msg.root_id == '', Msg.parent_id == '').one_or_none()

    # 如果找到了第一次会话消息，返回dia_type字段的值
    if first_msg is not None:
        return first_msg.dia_type

    return None

def insert_msg(message_id, root_id, parent_id, content,message_type, characteristic,operation,dia_type,file_key='',filepath=''):
    Session = sessionmaker(bind=engine)

    # 创建一个 Session 实例
    session = Session()
    # 创建一个新消息
    new_msg = Msg(
        message_id=message_id,
        root_id=root_id,
        parent_id=parent_id,
        content=content,
        message_type=message_type,
        operation=operation,
        characteristic=characteristic,
        dia_type=dia_type,
        file_key=file_key,
        filepath=filepath,
    )
    # 添加到会话
    session.add(new_msg)

    # 提交更改
    session.commit()

    # 关闭会话
    session.close()


def get_root_and_parent_id_by_message_id(message_id):
    Session = sessionmaker(bind=engine)

    # 创建一个 Session 实例
    session = Session()

    # 查询具有给定 message_id 的记录，并选择 root_id 和 parent_id 字段
    matching_msg = session.query(Msg.root_id, Msg.parent_id).filter_by(message_id=message_id).first()

    # 关闭会话
    session.close()

    # 返回匹配记录的 root_id 和 parent_id 字段，或 None（如果没有匹配记录）
    return matching_msg if matching_msg else None

def get_content_by_message_id(message_id):
    Session = sessionmaker(bind=engine)

    # 创建一个 Session 实例
    session = Session()

    # 查询具有给定 message_id 的记录，并选择 content 字段
    matching_msg = session.query(Msg.content).filter_by(message_id=message_id).first()

    # 关闭会话
    session.close()

    # 返回匹配记录的 content 字段，或 None（如果没有匹配记录）
    return matching_msg[0] if matching_msg else None


def is_characteristic_exist(characteristic):
    Session = sessionmaker(bind=engine)

    # 创建一个 Session 实例
    session = Session()

    # 查询是否存在具有给定 message_id 的记录
    existing_msg = session.query(Msg).filter_by(characteristic=characteristic).first()

    # 关闭会话
    session.close()

    # 如果存在，则返回 True，否则返回 False
    return existing_msg is not None


def get_conversation(msg_id):
    Session = sessionmaker(bind=engine)
    session = Session()
    conversation = []
    if msg_id is not None:
        msg = session.query(Msg).filter(Msg.message_id == msg_id).one()

        # 处理当前消息的祖先消息
        def process_ancestors(ancestor_msg):
            if ancestor_msg.parent_id and ancestor_msg.parent_id != '':
                parent_msg = session.query(Msg).filter(Msg.message_id == ancestor_msg.parent_id).one()
                process_ancestors(parent_msg)
                if parent_msg.operation in ["receive", "ai"]:
                    conversation.append({"role": "user" if parent_msg.operation == "receive" else "assistant",
                                         "content": parent_msg.content})

        process_ancestors(msg)

        # 添加当前消息
        if msg.operation in ["receive", "ai"]:
            conversation.append({"role": "user" if msg.operation == "receive" else "assistant", "content": msg.content})

        # 处理当前消息的子消息
        def process_children(child_msg):
            child_msgs = session.query(Msg).filter(Msg.parent_id == child_msg.message_id).order_by(Msg.id).all()
            for message in child_msgs:
                if message.operation in ["receive", "ai"]:
                    conversation.append(
                        {"role": "user" if message.operation == "receive" else "assistant", "content": message.content})
                process_children(message)

        process_children(msg)

    return conversation

def read_write_words(word_list):

    Session = sessionmaker(bind=engine)
    session = Session()

    # 将word_list中的单词添加到数据库中，跳过已存在的单词
    new_words_count = 0
    for word in word_list:
        try:
            # 如果单词已存在，跳过
            session.query(Word).filter(Word.content == word).one()
        except NoResultFound:
            # 否则，插入新单词
            new_word = Word(content=word)
            session.add(new_word)
            new_words_count += 1

    # 提交更改并关闭会话
    session.commit()
    session.close()

    # 查询总单词数
    session = Session()
    total_words = session.query(Word).count()
    session.close()

    return new_words_count, total_words

def get_random_words(num_words=random_word_num):
    Session = sessionmaker(bind=engine)
    session = Session()

    # 从数据库中获取所有单词
    words = session.query(Word).all()
    session.close()

    # 随机抽取num_words个单词，如果数量不够则返回None
    if len(words) >= num_words:
        selected_words = random.sample(words, num_words)
        return [word.content for word in selected_words]
    else:
        return None

def update_dia_type(message_id, new_dia_type):
    # 创建数据库连接和会话
    Session = sessionmaker(bind=engine)
    session = Session()

    # 根据message_id查找相应的记录，并更新dia_type字段
    session.query(Msg).filter(Msg.message_id == message_id).update({Msg.dia_type: new_dia_type})

    # 提交更改并关闭会话
    session.commit()
    session.close()