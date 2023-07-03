import requests
import urllib
import io,time,string
from pydub import AudioSegment
from .config import *
import azure.cognitiveservices.speech as speechsdk
from google.cloud import texttospeech
import wave,os,random


def generate_audio(sentence, filepath, dialogue):
    duration_ms = 0
    #if audio_mode == "youdao":
    #    duration_ms = youdao_generate_audio(sentence, filepath, dialogue)
    if audio_mode == "sougou":
        duration_ms = sougou_generate_audio(sentence, filepath, dialogue)
    elif audio_mode == "azure":
        duration_ms = azure_generate_audio(sentence, filepath, dialogue)
    elif audio_mode == "google":
        duration_ms = google_generate_audio(sentence, filepath, dialogue)
    elif audio_mode =="baidu":
        duration_ms = baidu_generate_audio(sentence, filepath, dialogue)
    else:
        raise Exception("没有这个类型")
    return duration_ms


# 有道和搜狗的播放引擎有单词数限制，需要进行分割
def split_long_text(text, chunk_size=100):
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

def to_wavfile(filepath):
    audio = AudioSegment.from_file(filepath)
    audio.export(filepath+"1", format="wav")
    return filepath+"1"

def deal_sentence(article):
    sentences = article.split('. ')

    formatted_sentences = []
    for sentence in sentences:
        formatted_sentences.append('<s>' + sentence.strip() + '</s>')

    formatted_paragraph = '<p>' + ''.join(formatted_sentences) + '</p>'
    return formatted_paragraph


def baidu_generate_audio(sentence, filepath, dialogue):

    combined_audio = AudioSegment.empty()

    rs = split_long_text(sentence)
    for i in rs:
        url = "https://fanyi.baidu.com/gettts?lan=en&text={}&spd=5&source=web".format(
            urllib.parse.quote(i), sougou_speaker)
        response = requests.get(url)
        audio_data = io.BytesIO(response.content)
        audio = AudioSegment.from_file(audio_data, format="mp3")
        combined_audio += audio

    combined_audio.export(filepath, format="opus")
    duration_ms = len(combined_audio)
    AudioSegment.empty()
    return duration_ms



def merge_audio(input_files,output_file):
    # 打开第一个文件获取音频参数
    with wave.open(input_files[0], 'rb') as in_file:
        nchannels = in_file.getnchannels()
        sampwidth = in_file.getsampwidth()
        framerate = in_file.getframerate()
        nframes = in_file.getnframes()

    # 打开输出文件进行写操作
    with wave.open(output_file, 'wb') as out_file:
        out_file.setnchannels(nchannels)
        out_file.setsampwidth(sampwidth)
        out_file.setframerate(framerate)

        # 逐一读取输入文件并将其写入输出文件
        for file_name in input_files:
            with wave.open(file_name, 'rb') as in_file:
                # 确认所有文件参数都一致
                assert nchannels == in_file.getnchannels()
                assert sampwidth == in_file.getsampwidth()
                assert framerate == in_file.getframerate()
                data = in_file.readframes(nframes)
                out_file.writeframes(data)
            os.remove(file_name)


# 支持的语音：https://cloud.google.com/text-to-speech/docs/voices?hl=zh-cn
# 测试ssml：https://cloud.google.com/text-to-speech?hl=zh-cn
def google_generate_audio(sentence, filepath, dialogue):

    client_options = {"api_key": google_api_key}
    sens = []
    p1_name = 'en-US-Wavenet-A'

    if dialogue == 0:
        rs = split_long_text(sentence)

        ssml_text = "<speak>{}</speak>"
        tmp = ""
        for i in rs:
            s = f'<voice name="{p1_name}">{i}</voice>'
            if len(tmp)<4500:
                tmp = tmp+s
            else:
                sens.append(ssml_text.format(tmp))
                tmp = ""
        sens.append(ssml_text.format(tmp))

    elif dialogue == 1:
        ssml = """<speak>{}</speak>"""
        sl = ""
        p2_name = 'en-US-Wavenet-C'
        for i in sentence.split("\n"):
            if len(sl)<3000:

                if "P1:" in i:
                    s = f"""<voice name="{p1_name}">{i.replace("P1:", "")} </voice>"""
                    sl = sl + s
                elif "P2:" in i:
                    s = f"""<voice name="{p2_name}">{i.replace("P2:", "")}</voice>"""
                    sl = sl + s

            else:
                sens.append(ssml.format(sl))
                sl = ""
                if "P1:" in i:
                    s = f"""<voice name="en-US-News-K">{i.replace("P1:", "")} </voice>"""
                    sl = sl + s
                elif "P2:" in i:
                    s = f"""<voice name="en-US-News-N">{i.replace("P2:", "")}</voice>"""
                    sl = sl + s
        sens.append(ssml.format(sl))

    input_files = []
    for ssml_text in sens:
        # Instantiates a client
        client = texttospeech.TextToSpeechClient(client_options=client_options)

        # Sets the text input to be synthesized
        synthesis_input = texttospeech.SynthesisInput(ssml=ssml_text)

        # Builds the voice request, selects the language code ("en-US") and
        # the SSML voice gender ("MALE")
        voice = texttospeech.VoiceSelectionParams(
            language_code="en-US", ssml_gender=texttospeech.SsmlVoiceGender.MALE
        )

        # Selects the type of audio file to return
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )

        # Performs the text-to-speech request on the text input with the selected
        # voice parameters and audio file type
        response = client.synthesize_speech(
            input=synthesis_input, voice=voice, audio_config=audio_config
        )
        random_string = ''.join(random.sample(string.ascii_lowercase + string.digits, 32))
        path = f'temp-{random_string}.mp3'
        # Writes the synthetic audio to the output file.
        with open(path, "wb") as out:
            out.write(response.audio_content)
            #print("Audio content written to file ")
        input_files.append(path)


    combined_audio = AudioSegment.empty()

    # 逐个加载每个MP3文件并将其添加到combined_audio对象中
    for mp3_file in input_files:
        audio = AudioSegment.from_mp3(mp3_file)
        combined_audio += audio
        #os.remove(mp3_file)

    #audio = AudioSegment.from_file(mp3_path)
    combined_audio.export(filepath, format="opus")
    duration_ms = len(combined_audio)
    return duration_ms

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
    combined_audio = AudioSegment.empty()

    if dialogue == 1:
        for i in sentence.split("\n"):
            if "P1:" in i:
                content = i.replace("P1:", "").strip()
                url = "https://fanyi.sogou.com/reventondc/synthesis?text={}&speaker=6&speed=1".format(
                    urllib.parse.quote(content))
            elif "P2:" in i:
                content = i.replace("P2:", "").strip()
                url = "https://fanyi.sogou.com/reventondc/synthesis?text={}&speaker=3&speed=1".format(
                    urllib.parse.quote(content))
            else:
                content = ' '
                url = "https://fanyi.sogou.com/reventondc/synthesis?text={}&speaker=1&speed=1".format(
                    urllib.parse.quote(content))
            response = requests.get(url)
            audio_data = io.BytesIO(response.content)
            audio = AudioSegment.from_file(audio_data, format="mp3")
            combined_audio += audio
        combined_audio.export(filepath, format="opus")
        duration_ms = len(combined_audio)
        AudioSegment.empty()
        return duration_ms
    else:
        rs = split_long_text(sentence)
        for i in rs:
            url = "https://fanyi.sogou.com/reventondc/synthesis?text={}&speaker={}&speed=1".format(
                urllib.parse.quote(i), sougou_speaker)
            response = requests.get(url)
            audio_data = io.BytesIO(response.content)
            audio = AudioSegment.from_file(audio_data, format="mp3")
            combined_audio += audio

    combined_audio.export(filepath, format="opus")
    duration_ms = len(combined_audio)
    AudioSegment.empty()
    return duration_ms


def azure_generate_audio(sentence, filepath, dialogue):
    while len(azure_speech_key_list)>0:
        azure_speech_key = random.choice(azure_speech_key_list)
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
            sentence = add_missing_markers(sentence)
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
        # Check result
        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            stream = speechsdk.AudioDataStream(result)
            stream.save_to_wav_file(wav_path)
            audio = AudioSegment.from_file(wav_path)
            audio.export(filepath, format="opus")
            duration_ms = len(audio)
            return duration_ms
        elif result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = result.cancellation_details
            azure_speech_key_list.remove(azure_speech_key_list)

            # print("Speech synthesis canceled: {}".format(cancellation_details.reason))
            # if cancellation_details.reason == speechsdk.CancellationReason.Error:
            #     print("Error details: {}".format(cancellation_details.error_details))
    return None



def add_missing_markers(text):
    lines = text.split("\n")
    result = []

    previous_marker = None

    for line in lines:
        line = line.strip()  # 去除行两端的空格

        if line.startswith("P1:"):
            previous_marker = "P1:"
            result.append(line)
        elif line.startswith("P2:"):
            previous_marker = "P2:"
            result.append(line)
        elif line != "":
            if previous_marker is not None:
                result.append(previous_marker + " " + line)
            else:
                result.append(line)

    return "\n".join(result)



def pronunciation_assessment_continuous_from_file(reference_text,weatherfilename):
    """Performs continuous pronunciation assessment asynchronously with input from an audio file.
        See more information at https://aka.ms/csspeech/pa"""

    import difflib
    import json

    # Creates an instance of a speech config with specified subscription key and service region.
    # Replace with your own subscription key and service region (e.g., "westus").
    # Note: The sample is for en-US language.
    speech_config = speechsdk.SpeechConfig(subscription=azure_speech_key, region=azure_service_region)
    audio_config = speechsdk.audio.AudioConfig(filename=weatherfilename)

    # create pronunciation assessment config, set grading system, granularity and if enable miscue based on your requirement.
    enable_miscue = True
    pronunciation_config = speechsdk.PronunciationAssessmentConfig(
        reference_text=reference_text,
        grading_system=speechsdk.PronunciationAssessmentGradingSystem.HundredMark,
        granularity=speechsdk.PronunciationAssessmentGranularity.Phoneme,
        enable_miscue=enable_miscue)

    # Creates a speech recognizer using a file as audio input.
    language = 'en-US'
    speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, language=language, audio_config=audio_config)
    # apply pronunciation assessment config to speech recognizer
    pronunciation_config.apply_to(speech_recognizer)

    done = False
    recognized_words = []
    fluency_scores = []
    durations = []

    def stop_cb(evt: speechsdk.SessionEventArgs):
        """callback that signals to stop continuous recognition upon receiving an event `evt`"""
        print('CLOSING on {}'.format(evt))
        nonlocal done
        done = True

    def recognized(evt: speechsdk.SpeechRecognitionEventArgs):
        #print('pronunciation assessment for: {}'.format(evt.result.text))
        pronunciation_result = speechsdk.PronunciationAssessmentResult(evt.result)
        # print('    Accuracy score: {}, pronunciation score: {}, completeness score : {}, fluency score: {}'.format(
        #     pronunciation_result.accuracy_score, pronunciation_result.pronunciation_score,
        #     pronunciation_result.completeness_score, pronunciation_result.fluency_score
        # ))
        nonlocal recognized_words, fluency_scores, durations
        recognized_words += pronunciation_result.words
        fluency_scores.append(pronunciation_result.fluency_score)
        json_result = evt.result.properties.get(speechsdk.PropertyId.SpeechServiceResponse_JsonResult)
        jo = json.loads(json_result)
        nb = jo['NBest'][0]
        durations.append(sum([int(w['Duration']) for w in nb['Words']]))

    # Connect callbacks to the events fired by the speech recognizer
    speech_recognizer.recognized.connect(recognized)
    speech_recognizer.session_started.connect(lambda evt: print('SESSION STARTED: {}'.format(evt)))
    speech_recognizer.session_stopped.connect(lambda evt: print('SESSION STOPPED {}'.format(evt)))
    speech_recognizer.canceled.connect(lambda evt: print('CANCELED {}'.format(evt)))
    # stop continuous recognition on either session stopped or canceled events
    speech_recognizer.session_stopped.connect(stop_cb)
    speech_recognizer.canceled.connect(stop_cb)

    # Start continuous pronunciation assessment
    speech_recognizer.start_continuous_recognition()
    while not done:
        time.sleep(.5)

    speech_recognizer.stop_continuous_recognition()

    # we need to convert the reference text to lower case, and split to words, then remove the punctuations.
    if language == 'zh-CN':
        # Use jieba package to split words for Chinese
        import jieba
        import zhon.hanzi
        jieba.suggest_freq([x.word for x in recognized_words], True)
        reference_words = [w for w in jieba.cut(reference_text) if w not in zhon.hanzi.punctuation]
    else:
        reference_words = [w.strip(string.punctuation) for w in reference_text.lower().split()]

    # For continuous pronunciation assessment mode, the service won't return the words with `Insertion` or `Omission`
    # even if miscue is enabled.
    # We need to compare with the reference text after received all recognized words to get these error words.
    if enable_miscue:
        diff = difflib.SequenceMatcher(None, reference_words, [x.word.lower() for x in recognized_words])
        final_words = []
        for tag, i1, i2, j1, j2 in diff.get_opcodes():
            if tag in ['insert', 'replace']:
                for word in recognized_words[j1:j2]:
                    if word.error_type == 'None':
                        word._error_type = 'Insertion'
                    final_words.append(word)
            if tag in ['delete', 'replace']:
                for word_text in reference_words[i1:i2]:
                    word = speechsdk.PronunciationAssessmentWordResult({
                        'Word': word_text,
                        'PronunciationAssessment': {
                            'ErrorType': 'Omission',
                        }
                    })
                    final_words.append(word)
            if tag == 'equal':
                final_words += recognized_words[j1:j2]
    else:
        final_words = recognized_words

    # We can calculate whole accuracy by averaging
    final_accuracy_scores = []
    for word in final_words:
        if word.error_type == 'Insertion':
            continue
        else:
            final_accuracy_scores.append(word.accuracy_score)
    accuracy_score = sum(final_accuracy_scores) / len(final_accuracy_scores)
    # Re-calculate fluency score
    fluency_score = sum([x * y for (x, y) in zip(fluency_scores, durations)]) / sum(durations)
    # Calculate whole completeness score
    completeness_score = len([w for w in recognized_words if w.error_type == "None"]) / len(reference_words) * 100
    completeness_score = completeness_score if completeness_score <= 100 else 100

    msgs = '段落准确性评分: {}, 完成性评分: {}, 流畅性评分: {}\n'.format(accuracy_score, completeness_score, fluency_score)

    for idx, word in enumerate(final_words):
        msgs = msgs+'{}: 单词: {}\t准确性分数: {}\t错误类型: {};\n'.format(idx + 1, word.word, word.accuracy_score, word.error_type)

    return msgs
