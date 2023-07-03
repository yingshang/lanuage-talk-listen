APP_ID = "" #飞书应用的App ID
APP_SECRET = "" # 飞书应用的App Secret
ENCRYPT_KEY = "" #飞书应用事件订阅的Encrypt Key
VERIFICATION_TOKEN = "" #飞书应用事件订阅的Verification Token
LARK_HOST = "https://open.feishu.cn"
TencentSecretId = "" #腾讯SecretId，用来语音转文字
TencentSecretKey = "" #腾讯SecretId，用来语音转文字
AiKeyList = ["sk-","sk-"] #openai的key
robotCode = '' #钉钉机器人AppKey
AppKey = '' ##钉钉应用key，等于robotCode
AppSecret = '-' #钉钉应用Secret

azure_speech_key_list = ["",""]  #微软的key

azure_service_region = "eastus" #微软资源的地区
azure_speaker = "en-US-JennyNeural" #点击语音库，选择自己喜欢的声音。https://speech.microsoft.com/portal

google_api_key = ''


text_and_audio = 0 #默认只回复英文语音，设置为1同时回复英语语音和英语文本。当配置为0的时候，可以采用官方的语音翻译功能对回复录音进行翻译，用于练听力。
random_word_num = 10 #随机生成单词的个数
audio_mode = "azure"  #有四种模式，youdao(已经失效)、sougou、azure、google
sougou_speaker = 6 #搜狗语音有6种语音，可以选择自己喜欢的，参考https://fanyi.sogou.com/reventondc/synthesis?text=hello%20i%20am%20xiaoming&speaker=6
