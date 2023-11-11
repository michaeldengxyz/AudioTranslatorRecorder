#Pyhton 3.x
# -*- coding: UTF-8 -*-

#
#
#pip install SpeechRecognition   #not be used now
'''
pip install requests
pip install chardet
pip install baidu-aip
pip install cryptography
pip install pyOpenSSL
pip install certifi
pip install uuid
pip install azure-cognitiveservices-speech

'''

import time
import traceback
import re
import os,sys

#------------------------------
#!!! have to use this to find the right root path in its .exe file!!!
print("\n#AC#", sys._getframe().f_lineno,"run from file:", __file__, "\nsys.argv=", sys.argv, "\ngetcwd:", os.getcwd())  
self_folder = ""
def find_real_file(ofile):
    self_folder = ""
    dirname = os.path.abspath(os.path.dirname(ofile))
    if dirname and os.path.exists(dirname):
        self_folder = re.sub(r'\\','/', dirname)
    else:
        fname = os.path.basename(ofile)        
        for root, dirs, files in os.walk(os.getcwd(), topdown=True):
            for name in files:
                if re.match(r'.*{}$'.format(fname), str(name), re.I):
                    print(sys._getframe().f_lineno,"find file:", name)
                    self_folder = re.sub(r'\\','/',os.path.abspath(os.path.dirname(name)))
                    break
            if self_folder:
                break
    return self_folder

if os.path.exists(sys.argv[0]):
    self_folder = re.sub(r'\\','/',os.path.abspath(os.path.dirname(sys.argv[0])))

if not (self_folder and os.path.exists(self_folder + '/AudioTranslator_audio_options.json')):
    self_folder = find_real_file(sys.argv[0])

print("\n#AC#", sys._getframe().f_lineno,"root:", self_folder, "\n")
if not (self_folder and os.path.exists(self_folder + '/AudioTranslator_audio_options.json')):
    print("\n#AC#",sys._getframe().f_lineno, "File missing:", self_folder + '/AudioTranslator_audio_options.json')
    print(sys._getframe().f_lineno,"\n=========================== Failed to find root path!! ===========================\n")
    os._exit(0)
sys.path.append(self_folder)
#------------------------------

from tkinter import Tk, mainloop
import glob
from aip import AipSpeech
from AudioTranslatorUtils import UT_FileSave, UT_JsonFileSave, UT_JsonFileRead, UT_CryptMe, UT_GetMD5, UT_MD5_VerifyCode,UT_Str2Int, UI_AT_Close
import wave
import numpy as np
import threading

import requests
import random
from hashlib import md5

#import speech_recognition as sr     #not be used now
import azure.cognitiveservices.speech as speechsdk
import requests, uuid, json
import socket

print("\n\n#AC#",  sys._getframe().f_lineno,'\nAudio Translator - Convertor\n\tsys.argv=', sys.argv)

WindX  = {}
WindXX = {}
WindX['self_folder'] = self_folder
WindX['self_root_folder'] = ""
WindX['audio_options.json_last_update'] = 0
WindX['main'] = None

def init():
    AudioRecordFoleder()

    WindX['baidu_api_client'] = None
    WindX['AudioToText_Done'] = []

    WindX['convert_engine'] = 1
    if  len(sys.argv) > 3 and sys.argv[3]:
        WindX['convert_engine'] = UT_Str2Int(sys.argv[3])
    print("#AC#",  sys._getframe().f_lineno,"\tConvert Engine:", WindX['convert_engine'])

    WindX['AudioToText_to_language'] = ""
    if WindX['convert_engine'] == 1:
        WindX['AudioToText_to_language'] = 1537 #1537 普通话(纯中文识别), 1737 英语
        if len(sys.argv) >1 and sys.argv[1] and sys.argv[1] in ['1737', '1537']:
            WindX['AudioToText_to_language'] = UT_Str2Int(sys.argv[1])
        print("#AC#",  sys._getframe().f_lineno,"\tAudio language:", WindX['AudioToText_to_language'], "(1537 普通话(纯中文识别), 1737 英语)")
    elif len(sys.argv) >1 and sys.argv[1]:
        WindX['AudioToText_to_language'] = re.sub(r'___', ' ', str(sys.argv[1]))
        print("#AC#",  sys._getframe().f_lineno,"\tAudio language:", WindX['AudioToText_to_language'])

    WindX['audio_file_format'] = 'wav'
    if  len(sys.argv) >2 and sys.argv[2] and sys.argv[2] in ['wav', 'mp3']:
        WindX['audio_file_format'] = sys.argv[2]
    print("#AC#",  sys._getframe().f_lineno,"\tAudio file format:", WindX['audio_file_format'])

    WindX['EncryptCode_current'] = ""
    if  len(sys.argv) > 4 and sys.argv[4]:
        WindX['EncryptCode_current'] = str(sys.argv[4])
    print("#AC#",  sys._getframe().f_lineno,"\tEncryptCode_current:", re.sub(r'\w', '*', WindX['EncryptCode_current']))

    WindX['options_files_vals'] = {}

    WindXX['WatchingOptions_opts'] = {
        'translate_baidu_app_id' :  ['entry', 'encrypt'],
        'translate_baidu_app_key' : ['entry', 'encrypt'],

        'audio2text_baidu_app_id' :  ['entry', 'encrypt'],
        'audio2text_baidu_api_key' : ['entry', 'encrypt'],
        'audio2text_baidu_api_secret_key' : ['entry', 'encrypt'],

        'translate_azure_app_key' :  ['entry', 'encrypt'],
        'translate_azure_app_region':['entry', 'encrypt'],

        'audio2text_azure_api_speech_key' : ['entry', 'encrypt'],
        'audio2text_azure_api_speech_region' : ['entry', 'encrypt']    
    }

def AudioRecordFoleder():
    opts_file = WindX['self_folder'] + '/AudioTranslator_audio_options.json'
    if not WindX['self_root_folder']:
        WindX['self_root_folder'] = WindX['self_folder']
    
    try:
        last_update = 123456
        if os.path.exists(WindX['self_folder'] + '/AudioTranslator_audio_options.json'):
                os.chdir(WindX['self_folder'])
                try:
                    #fsize = os.path.getsize(f)  #when the file path is deep and every long, will get error and fail to get file size 
                    last_update = os.path.getmtime('AudioTranslator_audio_options.json')
                except:
                    print("#AC#",  sys._getframe().f_lineno,"\n",sys._getframe().f_lineno, traceback.format_exc())

        if WindX['audio_options.json_last_update'] == last_update:
            return        
        WindX['audio_options.json_last_update'] = last_update

        vals = UT_JsonFileRead(filepath=opts_file)
        if vals and vals.__contains__('custom') and vals['custom'].__contains__('self_root_folder') and vals['custom']['self_root_folder'] and os.path.exists(vals['custom']['self_root_folder']):
            WindX['self_root_folder'] = re.sub(r'\/+Records$|\/+\s*$', '', vals['custom']['self_root_folder'], flags=re.I)
            sys.path.append(WindX['self_root_folder'])
            print("\n#AC", sys._getframe().f_lineno,"Records saved in:", WindX['self_root_folder'], "\n")

        WindX['app_outfolder_recorders'] = WindX['self_root_folder'] + "/Records"
    except:
        print("#AC#",  sys._getframe().f_lineno,"\n",sys._getframe().f_lineno, traceback.format_exc())

def AudioToText(filepath="", audio_language='', convert_engine=0, translate_to="", optVals={}):
    if filepath in WindX['AudioToText_Done']:
        return
    
    if convert_engine == 4:
        return

    convert_engines = ['0 - NULL', '1 - Baidu', '2 - Google', '3 - Microsoft Azure AI', '4 - Not Convert']
    print("#AC#",  sys._getframe().f_lineno,"\nAudioToText:", filepath, ', audio_language=', audio_language, ', convert_engine=',convert_engines[convert_engine], ', translate_to=',translate_to)
    WindX['AudioToText_Done'].append(filepath)

    if convert_engine == 1:
        AudioToText_Baidu(filepath, audio_language=audio_language, translate_to=translate_to, optVals=optVals)
    elif convert_engine == 3:
        AudioToText_AzureAI(filepath, audio_language= audio_language, translate_to=translate_to, optVals=optVals)
    else:
        AudioToText_Else(filepath, audio_language= audio_language, convert_engine=convert_engine, translate_to=translate_to, optVals=optVals)

def AudioToText_Else(filepath, audio_language='zh-CN', convert_engine=0, translate_to="", optVals={}):
    return

    try:
        to_language = 'zh-CN'
        try:
            if UT_Str2Int(audio_language) == 1537:
                to_language = 'zh-CN'
            elif UT_Str2Int(audio_language) == 1737:
                to_language = 'en'
        except:
            pass

        api_service = ""
        r = sr.Recognizer()
        audio_data = b''
        with sr.AudioFile(filepath) as f:
            audio_data = r.record(f)
        try:
            if convert_engine == 2:
                api_service = "Google"
                result = r.recognize_google(audio_data, language= to_language)
                print("#AC#",  sys._getframe().f_lineno,result)            

        except sr.UnknownValueError:
            print("#AC#",  sys._getframe().f_lineno,"\n",sys._getframe().f_lineno, traceback.format_exc(), "\n", sr.UnknownValueError)
        except sr.RequestError:
            print("#AC#",  sys._getframe().f_lineno,"\n",sys._getframe().f_lineno, traceback.format_exc(), "\n", sr.RequestError, "\nCould not request results from "+ api_service +" Speech Recognition Service!")
    except:
        print("#AC#",  sys._getframe().f_lineno,"\n", traceback.format_exc())

def AudioToText_AzureAI(filepath, audio_language='zh-CN', translate_to="", optVals={}, action=1):
    try:
        print("\n#AC#",  sys._getframe().f_lineno, 
            "action#" + str( action),  
            "subscription=", optVals["audio2text_azure_api_speech_key"], 
            ", region=", optVals["audio2text_azure_api_speech_region"], 
            ", audio_language=", audio_language,
            ", translate_to=", translate_to
        )

        audio_languages = re.split(r'\s+', str(audio_language))
        audio_language  = audio_languages[0]
        translate_tos = re.split(r'\s+', translate_to)
        translate_to  = translate_tos[0]
        print("#AC#",  sys._getframe().f_lineno, 
            ", audio_language=", audio_language,
            ", translate_to=", translate_to
        )

        audio_config  = speechsdk.audio.AudioConfig(filename=filepath)

        speech_config = speechsdk.SpeechConfig(
            subscription= optVals["audio2text_azure_api_speech_key"], 
            region=optVals["audio2text_azure_api_speech_region"])
        speech_config.speech_recognition_language = audio_language

        auto_detect_source_language_config = None #speechsdk.languageconfig.AutoDetectSourceLanguageConfig(languages=[audio_language, translate_to])

        speech_recognizer = speechsdk.SpeechRecognizer(
            speech_config=speech_config, 
            audio_config=audio_config,
            auto_detect_source_language_config=auto_detect_source_language_config
        )

        """
        res_text = ""
        done = False
        def stop_cb(evt):
            '''callback that signals to stop continuous recognition upon receiving an event `evt`'''
            print("#AC#",  sys._getframe().f_lineno,'CLOSING on {}'.format(evt))
            nonlocal done
            done = True

        def status_cb(lineno, s, evt):
            nonlocal res_text
            if s == 'RECOGNIZED':  #or s == 'RECOGNIZING'                
                res_text = str(evt)
                print("#AC#", lineno, s + ":", res_text)
                # RECOGNIZED: SpeechRecognitionEventArgs(session_id=9df759e72c9148d6a9fa033ee1019a07, result=SpeechRecognitionResult(result_id=7a1e5c40f23645acb71e2f462a300e4a, text="菜鸟工具。", reason=ResultReason.RecognizedSpeech))
                #RECOGNIZING: SpeechRecognitionEventArgs(session_id=09adbd4f57984b9b973c3349cbeba21d, result=SpeechRecognitionResult(result_id=e8e98970e73b4c43a1dacff5da5e262d, text="菜鸟工具", reason=ResultReason.RecognizingSpeech))               

        # Connect callbacks to the events fired by the speech recognizer
        speech_recognizer.recognizing.connect(lambda evt: status_cb(sys._getframe().f_lineno,'RECOGNIZING', evt))
        speech_recognizer.recognized.connect (lambda evt: status_cb(sys._getframe().f_lineno,'RECOGNIZED', evt))  

        speech_recognizer.session_started.connect(lambda evt: status_cb(sys._getframe().f_lineno,'SESSION STARTED', evt))
        speech_recognizer.session_stopped.connect(lambda evt: status_cb(sys._getframe().f_lineno,'SESSION STOPPED', evt))
        speech_recognizer.canceled.connect       (lambda evt: status_cb(sys._getframe().f_lineno,'CANCELED', evt))

        # stop continuous recognition on either session stopped or canceled events
        speech_recognizer.session_stopped.connect(stop_cb)
        speech_recognizer.canceled.connect(stop_cb)

        # Start continuous speech recognition
        speech_recognizer.start_continuous_recognition()
        while not done:
            time.sleep(0.5)

        speech_recognizer.stop_continuous_recognition()
        print("#AC#",  sys._getframe().f_lineno, "res_text=", res_text)
        """

        try:
            #Note: Since recognize_once() returns only a single utterance, it is suitable only for single
            # shot recognition like command or query.
            # For long-running multi-utterance recognition, use start_continuous_recognition() instead.
            result = speech_recognizer.recognize_once_async().get()
            res_text = ""
            res_warn  = ""
            res_err  = ""
            print("\n#AC#",  sys._getframe().f_lineno,"speech_recognizer.recognize_once_async().get(): {}".format(result))

            auto_detect_source_language_result = speechsdk.AutoDetectSourceLanguageResult(result)
            detected_language = auto_detect_source_language_result.language
            print("#AC#",  sys._getframe().f_lineno,"auto_detect_source_language_result: {}".format(detected_language))

            ResultReason_NoMatch = False
            if result.reason == speechsdk.ResultReason.RecognizedSpeech:
                print("\n#AC#",  sys._getframe().f_lineno,"Recognized: {}".format(result.text))
                res_text = result.text
            elif result.reason == speechsdk.ResultReason.NoMatch:
                print("\n#AC#",  sys._getframe().f_lineno,"No speech could be recognized: {}".format(result.no_match_details))
                res_warn  = "No speech could be recognized: {}".format(result.no_match_details)
                ResultReason_NoMatch = True
            elif result.reason == speechsdk.ResultReason.Canceled:
                cancellation_details = result.cancellation_details
                print("\n#AC#",  sys._getframe().f_lineno,"Speech Recognition canceled: {}".format(cancellation_details.reason))
                res_err = "Speech Recognition canceled: {}".format(cancellation_details.reason)
                if cancellation_details.reason == speechsdk.CancellationReason.Error:
                    print("\n#AC#",  sys._getframe().f_lineno,"Error details: {}".format(cancellation_details.error_details))
                    res_err = "Error details: {}".format(cancellation_details.error_details)
                    print("\n#AC#",  sys._getframe().f_lineno,"Did you set the speech resource key and region values?")


            if res_err:
                if action == 1:
                    UT_FileSave(res_err, filepath + '.err', format="strings")
                    #if ResultReason_NoMatch: #not really good to get a right return!
                    #    AudioToText_AzureAI(filepath, audio_language= translate_to, translate_to=translate_to, optVals=optVals, action=2)
            elif res_warn:
                UT_FileSave(res_warn, filepath + '.warn', format="strings")

            else:
                UT_FileSave("[3." + str(audio_language).upper() + "] " + res_text, filepath + '.txt', format="strings")
                if res_text:
                    res_trans = Translate_AzureAI(res_text, audio_language, translate_to, optVals)
                    if len(res_trans):
                        UT_FileSave("[3." + str(translate_to).upper() + "] " + " ".join(res_trans), filepath + '.translated', format="strings")                
                
        except:
            print("\n#AC#",  sys._getframe().f_lineno,"\n",traceback.format_exc())

    except:
        print("#AC#",  sys._getframe().f_lineno,"\n",sys._getframe().f_lineno, traceback.format_exc())

def Translate_AzureAI(instring, from_lang, to_lang, optVals={}):
    print("\n#AC#",  sys._getframe().f_lineno, "from_lang=", from_lang, ", to_lang=", to_lang, ", key =", optVals["translate_azure_app_key"], ", location=", optVals["translate_azure_app_region"])
    try:
        from_langs = re.split(r'\s+', from_lang)
        from_lang  = from_langs[0]
        to_langs = re.split(r'\s+', to_lang)
        to_lang  = to_langs[0]

        if from_lang == to_lang:
            print("#AC#",  sys._getframe().f_lineno,"\t",sys._getframe().f_lineno, "No need to translate!")
            return
    
        # Add your key and endpoint
        key = optVals["translate_azure_app_key"]
        endpoint = "https://api.cognitive.microsofttranslator.com"

        # location, also known as region.
        # required if you're using a multi-service or regional (not global) resource. It can be found in the Azure portal on the Keys and Endpoint page.
        location = optVals["translate_azure_app_region"]

        path = '/translate'
        constructed_url = endpoint + path

        params = {
            'api-version': '3.0',
            'from': from_lang,
            'to': to_lang   #single string or list as [fr, zu]
        }

        headers = {
            'Ocp-Apim-Subscription-Key': key,
            # location required if you're using a multi-service or regional (not global) resource.
            'Ocp-Apim-Subscription-Region': location,
            'Content-type': 'application/json',
            'X-ClientTraceId': str(uuid.uuid4())
        }

        # You can pass more than one object in body.
        body = [{
            'text': instring
        }]

        request = requests.post(constructed_url, params=params, headers=headers, json=body, verify=False)
        response = request.json()
        print("\n#AC#", sys._getframe().f_lineno, "\n", json.dumps(response, sort_keys=True, ensure_ascii=False, indent=4, separators=(',', ': ')))  

        tt = []
        if type(response) == list and response[0].__contains__("translations"):            
            for t in response[0]["translations"]:
                #print("#AC#", sys._getframe().f_lineno, " Translated to ["+ t["to"] + "]", ":", t["text"])
                tt.append(t["text"])
            
        elif response.__contains__("error"):
            print("\n#AC#", sys._getframe().f_lineno, "Error code", response["error"]["code"], ":", response["error"]["message"])

        return tt
    except:
        print("#AC#",  sys._getframe().f_lineno,"\n", traceback.format_exc())
        return []

def api_connect_BaiDu(optVals={}):
    #https://ai.baidu.com/ai-doc/SPEECH/pk4o0bkx8
    hasValidKey = 0

    #print("#AC#",  sys._getframe().f_lineno,"api_connect_BaiDu optVals=", optVals)
    for s in ['audio2text_baidu_app_id', 'audio2text_baidu_api_key','audio2text_baidu_api_secret_key']:
        if (optVals.__contains__(s) and optVals[s]):
            hasValidKey += 1
    if hasValidKey < 3:
        print("\n",sys._getframe().f_lineno, "audio2text_baidu_app or key or secret_key is not valid!!")
        return
    try:
        baidu_app_id = optVals['audio2text_baidu_app_id'] 
        baidu_api_key= optVals['audio2text_baidu_api_key']
        baidu_api_secret_key = optVals['audio2text_baidu_api_secret_key']
        WindX['baidu_api_client'] = AipSpeech(baidu_app_id, baidu_api_key, baidu_api_secret_key)
    except:
        print("#AC#",  sys._getframe().f_lineno,"\n", traceback.format_exc())

def AudioToText_Baidu(filepath, audio_language='1537',translate_to="", optVals={}):
    try:
        print("\n#AC#",  sys._getframe().f_lineno, 
            "baidu_app_id=", optVals['audio2text_baidu_app_id'], 
            ", baidu_api_key=", optVals['audio2text_baidu_api_key'], 
            ", api_secret_key=", optVals['audio2text_baidu_api_secret_key'], 
            ", audio_language=", audio_language,
            ", translate_to=", translate_to
        )

        #1537 普通话(纯中文识别), 1737 英语)
        audio_languageX = str(audio_language)
        if str(audio_language) == '1737':
            audio_languageX = "1737-EN"
        elif str(audio_language) == '1537':
            audio_languageX = "1537-ZH"

        if not WindX['baidu_api_client']:
            api_connect_BaiDu(optVals)
    
        fsize = os.path.getsize(filepath)
               
        audio_rate = 16000
        wf = wave.open(filepath, 'rb')
        audio_rate = wf.getframerate()
        audio_frames_data = wf.readframes(wf.getnframes())
        print("#AC#",  sys._getframe().f_lineno,wf.getparams())
        wf.close()  

        audio_data = b''
        if not os.path.exists(filepath + '.pcm'):
            f = open(filepath, 'rb')
            f.seek(0)
            f.seek(44)
            audio_data = np.fromfile(f, dtype=np.int16)
            f.close()
            audio_data.tofile(filepath + '.pcm')

        f = open(filepath + '.pcm', 'rb')
        audio_data = f.read()
        f.close() 
        #'''

        if audio_frames_data == audio_data:
            print("#AC#",  sys._getframe().f_lineno,"\twav frames data is pcm coding format!")
        print("#AC#",  sys._getframe().f_lineno,"\tfile size=", fsize, ', frames data=', len(audio_frames_data), ', pcm data length=', len(audio_data), ", dev_pid=", audio_language)

        if len(audio_data):            
            result = WindX['baidu_api_client'].asr(
                speech=audio_data, 
                format = 'pcm',
                rate= audio_rate,
                options={'dev_pid': audio_language}
            )

            print("#AC#",  sys._getframe().f_lineno,"\tconvert engine Baidu, result=", result)
            if result and result.__contains__('result') and len(result['result']) and re.match(r'.*success', result['err_msg'], re.I):
                t = "".join(result['result'])
                if len(t):
                    UT_FileSave("[1." + audio_languageX + "] " + "\n".join(result['result']), filepath + '.txt', format="strings")
                    if translate_to:
                        Translate_Baidu(",\n".join(result['result']), audio_language, translate_to, filepath, optVals=optVals)
                else:
                    UT_JsonFileSave(filepath + '.err', fdata= result)
            else:
                print("#AC#",  sys._getframe().f_lineno,"\tFailed to convert!")
                result['get_help_from'] = "https://ai.baidu.com/ai-doc/SPEECH/Zlbxew2qk"
                UT_JsonFileSave(filepath + '.warn', fdata= result)
    except:
        print("#AC#",  sys._getframe().f_lineno,"\n", traceback.format_exc())

def Translate_Baidu(query, audio_language, translate_to, filepath, optVals={}):
    # This code runs on Python 2.7.x and Python 3.x.
    # You may install `requests` to run this code: pip install requests
    # Please refer to `https://api.fanyi.baidu.com/doc/21` for complete api document

    if not translate_to:
        print("#AC#",  sys._getframe().f_lineno,"\t",sys._getframe().f_lineno, "Not translate!!")
        return
        
    hasValidKey = 0
    for s in ['translate_baidu_app_id', 'translate_baidu_app_key']:
        if (optVals.__contains__(s) and optVals[s]):
            hasValidKey += 1
    if hasValidKey < 2:
        print("#AC#",  sys._getframe().f_lineno,"\n",sys._getframe().f_lineno, "translate_baidu_app or key is not valid!!")
        return

    # Set your own appid/appkey.
    baidu_app_id= optVals['translate_baidu_app_id'] 
    baidu_api_key=optVals['translate_baidu_app_key']

    # For list of language codes, please refer to `https://api.fanyi.baidu.com/doc/21`
    from_lang = 'en'    
    if audio_language == 1537: #1537 普通话(纯中文识别), 1737 英语)
        from_lang = 'zh'

    to_lang =  'zh'
    if re.match(r'.*English', translate_to, re.I):
        to_lang =  'en'

    if from_lang == to_lang:
        print("#AC#",  sys._getframe().f_lineno,"\t",sys._getframe().f_lineno, "No need to translate!")
        return

    endpoint = 'http://api.fanyi.baidu.com'
    path = '/api/trans/vip/translate'
    url = endpoint + path

    salt = random.randint(32768, 65536)
    sign = make_md5(baidu_app_id + query + str(salt) + baidu_api_key)

    # Build request
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    payload = {'appid': baidu_app_id, 'q': query, 'from': from_lang, 'to': to_lang, 'salt': salt, 'sign': sign}

    # Send request
    r = requests.post(url, params=payload, headers=headers)
    result = r.json()

    # Show response
    #print("#AC#",  sys._getframe().f_lineno,json.dumps(result, indent=4, ensure_ascii=False))
    '''
    {
        "from": "en",
        "to": "zh",
        "trans_result": [
            {
                "src": "For list of language codes, please refer to `https://api.fanyi.baidu.com/doc/21`",
                "dst": "有关语言代码的列表，请参阅`https://api.fanyi.baidu.com/doc/21`"
            }
        ]
    }
    '''

    if filepath and result and result.__contains__("trans_result") and  len(result["trans_result"]) and result["trans_result"][0]["dst"]:
        #print("#AC#",  sys._getframe().f_lineno,result["trans_result"][0]["dst"])
        UT_FileSave("[1." + str(to_lang).upper() + "] " + result["trans_result"][0]["dst"], filepath + '.translated', format="strings")
    elif result.__contains__("trans_result") and  len(result["trans_result"]) and result["trans_result"][0]["dst"]:
        return result["trans_result"][0]["dst"]
    else:
        return ""

def SocketInputGet():
    print("\n#AC#", sys._getframe().f_lineno, "Listening socket ... ...")
    try:
        print("#AC# host name=" + str(socket.gethostname()))
        proc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        proc.bind(('127.0.0.1', 8181))
        proc.listen(5)      
        while True:
            conn, addr = proc.accept()
            data = conn.recv(1024).decode()
            #print("#AC# received data:", data)   #[to_language, audio_file_format, convert_engine, EncryptCode_current]
            conn.sendall("THANK YOU!".encode(encoding='UTF-8',errors='ignore'))
            if re.match(r'.*88', data, re.I):
                conn.close()
                break
            elif data:
                conn.close()

                print("\n")
                to_language, audio_file_format, convert_engine, EncryptCode_current = re.split(r'\s*\,\s*', data)                
                if len(convert_engine):
                    WindX['convert_engine'] = UT_Str2Int(convert_engine)
                elif not WindX['convert_engine']:
                    WindX['convert_engine'] = 1
                print("#AC#",  sys._getframe().f_lineno,"\tConvert Engine:", WindX['convert_engine'])

                WindX['AudioToText_to_language'] = ""
                if WindX['convert_engine'] == 1:
                    WindX['AudioToText_to_language'] = 1537 #1537 普通话(纯中文识别), 1737 英语
                    if len(to_language) and to_language in ['1737', '1537']:
                        WindX['AudioToText_to_language'] = UT_Str2Int(to_language)
                    print("#AC#",  sys._getframe().f_lineno,"\tAudio language:", WindX['AudioToText_to_language'], "(1537 普通话(纯中文识别), 1737 英语)")
                elif len(to_language):
                    WindX['AudioToText_to_language'] = re.sub(r'___', ' ', to_language)
                    print("#AC#",  sys._getframe().f_lineno,"\tAudio language:", WindX['AudioToText_to_language'])

                WindX['audio_file_format'] = 'wav'
                if len(audio_file_format) and audio_file_format in ['wav', 'mp3']:
                    WindX['audio_file_format'] = audio_file_format
                print("#AC#",  sys._getframe().f_lineno,"\tAudio file format:", WindX['audio_file_format'])

                WindX['EncryptCode_current'] = ""
                if  len(EncryptCode_current):
                    WindX['EncryptCode_current'] = EncryptCode_current
                print("#AC#",  sys._getframe().f_lineno,"\tEncryptCode_current:", re.sub(r'\w', '*', WindX['EncryptCode_current']))   
                print("\n")            

        print("#AC# SocketInputGet --- end")
        proc.close()
    except:
        print("#AC#",  sys._getframe().f_lineno, traceback.format_exc())    

def AudioCheckFiles():
    print("\n#AC#", sys._getframe().f_lineno, "start checking files inside the folder:", WindX['app_outfolder_recorders'], "... ...\n")
    app_outfolder = WindX['app_outfolder_recorders']
    n = 0

    while True:
        if not WindX['EncryptCode_current']:
            #print("#AC#",  sys._getframe().f_lineno,"\n=========================== Encrypt code is not valid!! ===========================\n")
            #sys.exit(0)
            print("\n#AC#",  sys._getframe().f_lineno, "waiting for socket message ... ...\n")
            time.sleep(1)
            k = 0
            while not WindX['EncryptCode_current']:    
                k +=1
                WindX['main'].title(WindX['main_title'] + " | Waiting for socket message ... ("+ str(k)+")")    
                time.sleep(1)

            WindX['main'].title(WindX['main_title'])

        if not WindX['main']:
            print("\n#AC#", sys._getframe().f_lineno, "stop to close !!!\n")
            break

        n +=1
        #print("#AC#", sys._getframe().f_lineno, n)
        try:
            AudioRecordFoleder()
            if not (app_outfolder == WindX['app_outfolder_recorders']):
                print("\n#AC#", sys._getframe().f_lineno, "start checking files inside the folder:", WindX['app_outfolder_recorders'], "... ...\n")
                app_outfolder = WindX['app_outfolder_recorders']

            if os.path.exists(WindX['app_outfolder_recorders']):
                os.chdir(WindX['app_outfolder_recorders'])
                
                files = glob.glob("*")                
                for f in sorted(files): 
                    if re.match(r'^Audio\.\d+', f, re.I) and os.path.isdir(WindX['app_outfolder_recorders'] + "/" + f):
                        #print("#AC#",  sys._getframe().f_lineno,"\n#" + str(n), f)
                        os.chdir(WindX['app_outfolder_recorders'] + "/" + f)

                        audio_file_format = WindX['audio_file_format']
                        audio_language = WindX['AudioToText_to_language']
                        convert_engine = WindX['convert_engine']
                        translate_to   = ""
                        vals = {}
                        
                        opts_file = WindX['app_outfolder_recorders'] + "/" + f + '/audio_options.json'
                        if os.path.exists(opts_file):                            
                            if WindX['options_files_vals'].__contains__(f):
                                vals = WindX['options_files_vals'][f]
                            else:
                                vals = UT_JsonFileRead(filepath=opts_file)
                                WindX['options_files_vals'][f] = vals
                            #print("#AC#",  sys._getframe().f_lineno,vals)
                            
                            if vals and vals.__contains__('custom'):
                                if vals['custom'].__contains__('convert_engine') and vals['custom']['convert_engine']: 
                                    convert_engine = UT_Str2Int(vals['custom']['convert_engine']) 

                                if vals['custom'].__contains__('audio_file_format') and vals['custom']['audio_file_format']: 
                                    audio_file_format = vals['custom']['audio_file_format']   

                                if vals['custom'].__contains__('convert_to_language') and vals['custom']['convert_to_language']: 
                                    if convert_engine == 1:
                                        audio_language = UT_Str2Int(vals['custom']['convert_to_language'])
                                    else:
                                        audio_language = vals['custom']['convert_to_language']                                     

                                if vals['custom'].__contains__('translate_to') and vals['custom']['translate_to']: 
                                    translate_to = vals['custom']['translate_to']
                            else:
                                vals['custom'] = {}

                        if vals and vals.__contains__('custom') and WindX['EncryptCode_current']:
                            if vals['custom'].__contains__('EncryptCode_MD5_VerifyCode') and vals['custom']['EncryptCode_MD5_VerifyCode']:
                                tmp_str = UT_CryptMe(vals['custom']['EncryptCode_MD5_VerifyCode'].encode(),key=UT_GetMD5(WindX['EncryptCode_current']), isEncript=False)
                                #print("#AC#",  sys._getframe().f_lineno, "VerifyCode:", tmp_str)
                                if tmp_str:
                                    for s in vals['custom'].keys():
                                        val_e = str(vals['custom'][s])
                                        if WindX['EncryptCode_current'] and val_e and re.match(r"^\$\$", val_e) and WindXX['WatchingOptions_opts'].__contains__(s) and WindXX['WatchingOptions_opts'][s][-1] == 'encrypt':   
                                            val_e = re.sub(r"^\$\$", '', val_e)               
                                            val_e = UT_CryptMe(val_e.encode(),key=UT_GetMD5(WindX['EncryptCode_current']), isEncript=False)
                                            vals['custom'][s] = val_e
                                else:
                                    print("#AC#",  sys._getframe().f_lineno, "!!! EncryptCode is incorrect !!!")
                                    continue
                        
                        if not convert_engine == 1:
                            audio_language = re.split(r'\s+', str(audio_language))[0]
                            #print("#AC#",  sys._getframe().f_lineno, "audio_language=", audio_language)

                        #print(vals)
                        os.chdir(WindX['app_outfolder_recorders'] + "/" + f)
                        for fmpx in sorted(glob.glob("*." + audio_file_format)):  
                            #print("\t", fmpx)                          
                            if not (os.path.exists(fmpx + '.txt.done') or os.path.exists(fmpx + '.txt') or os.path.exists(fmpx + '.err') or os.path.exists(fmpx + '.warn')):                                
                                #print("#AC#",  sys._getframe().f_lineno,"\t", fmpx)
                                if convert_engine == 4:                                    
                                    #print("#AC#",  sys._getframe().f_lineno, "convert_engine=", convert_engine, " - not convert!")
                                    UT_FileSave('This audio is not required to be converted to text!', fmpx + '.warn', format="strings")
                                else:
                                    n = 0
                                    AudioToText(filepath=fmpx, audio_language=audio_language, convert_engine=convert_engine, translate_to=translate_to, optVals=vals['custom'])    
        except:
            print("#AC#",  sys._getframe().f_lineno, traceback.format_exc())

        if n== 1 or n % 50 == 0:            
            print('.', end='')
            sys.stdout.flush()
        
        WindX['main'].title(WindX['main_title'] + " ("+ str(n)+")")
        time.sleep(0.5)

# Generate salt and sign
def make_md5(s, encoding='utf-8'):
    return md5(s.encode(encoding)).hexdigest()

def tmp():
    ui_lang = UT_JsonFileRead(filepath= WindX['self_folder'] + "/AudioTranslator/ui_languages.json")    #{1:{'CN':""  , 'EN':""}, 2:{'CN':""  , 'EN':""}, ...}
    print("#AC#",  sys._getframe().f_lineno,ui_lang)
    optVals = {
        "translate_baidu_app_id": "",
        "translate_baidu_app_key": ""        
    }
    k = 1
    data = ["{"]
    for num in ui_lang.keys():
        if ui_lang[num]['EN'] and not ui_lang[num]['CN']:
            k +=1
            ui_lang[num]['CN'] = Translate_Baidu(ui_lang[num]['EN'], 1737, 'Chinese', "", optVals=optVals)
        print("#AC#",  sys._getframe().f_lineno,ui_lang[num]['EN'], "===>", ui_lang[num]['CN'])
        data.append("\t\"" + num + "\":{\"CN\":\"" + ui_lang[num]['CN'] + "\", \"EN\":\"" + re.sub(r'\n', '\\n', ui_lang[num]['EN'] + "\"}"))
    data.append("}")
    print("#AC#",  sys._getframe().f_lineno,ui_lang)
    if k:
        UT_FileSave(",\n".join(data), WindX['self_folder'] + "/AudioTranslator/ui_languages.json", format="strings")
        #UT_JsonFileSave(WindX['self_folder'] + "/AudioTranslator/ui_languages.json", fdata=ui_lang)

def main():
    UI_AT_Close("AC")
    init()

    WindX['main_title'] = "AT-Convertor " + str(time.time())
    WindX['main'] = Tk()
    WindX['main'].title(WindX['main_title'])
    WindX['main'].geometry('500x30+0+0')
    WindX['main'].protocol("WM_DELETE_WINDOW", WindExit)
    WindX['main'].iconify()

    t1 = threading.Timer(0.1, AudioCheckFiles)
    t1.start()
    t2 = threading.Timer(0.1, SocketInputGet)
    t2.start()
    
    mainloop()

def WindExit(): 
    if WindX['main']:                     
        WindX['main'].destroy()
    WindX['main'] = None
    os._exit(0)
    #sys.exit(0)  # This will cause the window error: Python has stopped working ...

if __name__ == "__main__":      
    main()