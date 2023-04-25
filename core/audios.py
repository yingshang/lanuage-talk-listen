import requests
import urllib
import io
from pydub import AudioSegment
from .config import *
import azure.cognitiveservices.speech as speechsdk


def generate_audio(sentence, filepath, dialogue):
    duration_ms = 0
    if audio_mode == "youdao":
        duration_ms = youdao_generate_audio(sentence, filepath, dialogue)
    elif audio_mode == "sougou":
        duration_ms = sougou_generate_audio(sentence, filepath, dialogue)
    elif audio_mode == "azure":
        duration_ms = azure_generate_audio(sentence, filepath, dialogue)
    else:
        raise Exception("没有这个类型")
    return duration_ms


# 有道和搜狗的播放引擎有单词数限制，需要进行分割
def split_long_text(text, chunk_size=500):
    """
    Split a long text into chunks of size chunk_size, while ensuring that the last word in each chunk is complete.
    """
    chunks = []
    words = text.split()
    current_chunk = ''
    for word in words:
        if len(current_chunk + ' ' + word) <= chunk_size:
            current_chunk += ' ' + word
        else:
            chunks.append(current_chunk.strip())
            current_chunk = word
    if current_chunk:
        chunks.append(current_chunk.strip())
    return chunks


def youdao_generate_audio(sentence, filepath, dialogue):
    if dialogue == 1:
        sentence = sentence.replace("P1:", "").replace("P2:", "")
    combined_audio = AudioSegment.empty()
    rs = split_long_text(sentence)

    for i in rs:
        url = "https://tts.youdao.com/fanyivoice?word={}".format(urllib.parse.quote(i))
        response = requests.get(url)
        audio_data = io.BytesIO(response.content)
        audio = AudioSegment.from_file(audio_data, format="mp3")
        combined_audio += audio

    combined_audio.export(filepath, format="opus")
    duration_ms = len(combined_audio)

    AudioSegment.empty()
    return duration_ms


def sougou_generate_audio(sentence, filepath, dialogue):
    if dialogue == 1:
        sentence = sentence.replace("P1:", "").replace("P2:", "")

    combined_audio = AudioSegment.empty()
    rs = split_long_text(sentence)
    for i in rs:
        url = "https://fanyi.sogou.com/reventondc/synthesis?text={}&speaker={}".format(
            urllib.parse.quote(sentence), sougou_speaker)
        response = requests.get(url)
        audio_data = io.BytesIO(response.content)
        audio = AudioSegment.from_file(audio_data, format="mp3")
        combined_audio += audio

    combined_audio.export(filepath, format="opus")
    duration_ms = len(combined_audio)
    AudioSegment.empty()
    return duration_ms


def azure_generate_audio(sentence, filepath, dialogue):
    speech_config = speechsdk.SpeechConfig(subscription=azure_speech_key, region=azure_service_region)
    synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=None)
    if dialogue == 0:
        ssml = f"""
                <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">
            <voice name="{azure_speaker}">
                {sentence} <break />
            </voice>
            </speak>
        """
    elif dialogue == 1:
        ssml = """
        <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">
        {}
        </speak>
        """
        sl = ""
        for i in sentence.split("\n"):
            if "P1:" in i:
                s = f"""
                        <voice name="en-US-JennyNeural">
                            {i.replace("P1:", "")} 
                        </voice>
                    """
                sl = sl + s
            elif "P2:" in i:
                s = f"""
                        <voice name="en-US-GuyNeural">
                            {i.replace("P2:", "")} 
                        </voice>
                """
                sl = sl + s
        ssml = ssml.format(sl)

    wav_path = filepath.replace(".opus", ".wav")
    result = synthesizer.speak_ssml_async(ssml).get()
    stream = speechsdk.AudioDataStream(result)
    stream.save_to_wav_file(wav_path)
    audio = AudioSegment.from_file(wav_path)
    audio.export(filepath, format="opus")
    duration_ms = len(audio)
    return duration_ms
