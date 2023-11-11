#Pyhton 3.x
# -*- coding: UTF-8 -*-

import time
import traceback
import re
import os,sys

#------------------------------
#!!! have to use this to find the right root path in its .exe file!!!
print("\n#AR", sys._getframe().f_lineno,"run from file:", __file__, "\nsys.argv=", sys.argv, "\ngetcwd:", os.getcwd())  

#sys.argv= ['T:\\OneDrive\\Program\\AT\\dist\\AudioTranslatorRecorder.exe', '--multiprocessing-fork', 'parent_pid=10980', 'pipe_handle=2496']
#check and stop Process(): multiprocessing module starts a new Python process, for Windows!
for s in sys.argv:
    if re.match(r'.*multiprocessing\-fork', s, re.I):
        print(sys._getframe().f_lineno,"\n=========================== This runs from a Process(), stop!! ===========================\n")
        os._exit(0)

self_sys_argv0  = os.path.basename(sys.argv[0])
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

print("\n#AR", sys._getframe().f_lineno,"root:", self_folder, "\n")
if not (self_folder and os.path.exists(self_folder + '/AudioTranslator_audio_options.json')):
    print(sys._getframe().f_lineno, "File missing:", self_folder + '/AudioTranslator_audio_options.json')
    print(sys._getframe().f_lineno,"\n=========================== Failed to find root path!! ===========================\n")
    os._exit(0)
sys.path.append(self_folder)
#------------------------------

import random, string
from tkinter import *
from tkinter import filedialog,ttk,messagebox

from AudioTranslatorUtils import *
import audioop
import pyaudio
import wave
import socket

import pygetwindow
import win32gui
import threading
import numpy as np 
from multiprocessing import Process

"""
注意: 在windows中Process()必须放到# if __name__ == '__main__':下
由于Windows没有fork, 多处理模块启动一个新的Python进程并导入调用模块。 
如果在导入时调用Process(), 那么这将启动无限继承的新进程（或直到机器耗尽资源）.
这是隐藏对Process()内部调用的原, 使用if __name__ == '__main __, 这个if语句中的语句将不会在导入时被调

Note: in Windows Process () must be in the # if __name__ = = "__main__ ':
Since Windows has no fork, the multiprocessing module starts a new Python process and imports the calling module.
If Process() is called at import time, this will start a new process that inherits indefinitely (or until the machine runs out of resources).
This hides the origin of internal calls to Process(), using if __name__ == '__main __, the statements in this if statement will not be called at import time
"""

WindX  = {}
WindXX = {}
WindX['self_folder'] = self_folder
WindX['self_sys_argv0'] = self_sys_argv0

WindX['main_rev'] = '1.5'
def Revisons():
    WindX['main_rev_list'] ={
        '1.3': "initiation",
        '1.4': "add new functions",
        '1.5': "change encrypt code verification method"
    }

def init():
    #The folder self_folder contains: 
    #---- AudioTranslator_audio_options.json
    #---- AudioTranslator_ui_languages.json
    #---- AudioTranslatorConvertor.py (AudioTranslatorConvertor.exe)
    #---- AudioTranslatorRecorder.py (AudioTranslatorRecorder.exe)
    #---- AudioTranslatorUtils.py
    WindX['app_watching_options_file'] = WindX['self_folder'] + '/AudioTranslator_audio_options.json'
    WindX['app_ui_languages']          = WindX['self_folder'] + '/AudioTranslator_ui_languages.json'
    WindX['ms_languages_selected_default'] = ['de', 'fr', 'en', 'ja', 'ko', 'pt', 'ru', 'zh']
    #The folder self_root_folder contains:
    #---- Records (folder to save all audio records)
     
    WindX['self_root_folder'] = WindX['self_folder']
    vals = UT_JsonFileRead(filepath= WindX['app_watching_options_file'])
    if vals and vals.__contains__('custom'):
        if vals['custom'].__contains__('self_root_folder') and vals['custom']['self_root_folder'] and os.path.exists(vals['custom']['self_root_folder']):
            WindX['self_root_folder'] = re.sub(r'\/+Records$|\/+\s*$', '', vals['custom']['self_root_folder'], flags=re.I)
            sys.path.append(WindX['self_root_folder'])
            print("\n#AR", sys._getframe().f_lineno,"Records saved in:", WindX['self_root_folder'], "\n")
        
        if vals['custom'].__contains__('ms_languages_selected') and vals['custom']['ms_languages_selected']:
            WindX['ms_languages_selected_default'] = re.split(r'\s*\,\s*', vals['custom']['ms_languages_selected'])

    WindX['app_outfolder_recorders'] = WindX['self_root_folder'] + "/Records"
    if not os.path.exists(WindX['app_outfolder_recorders']):
        print(sys._getframe().f_lineno,"create dir:", WindX['app_outfolder_recorders'])
        os.makedirs(WindX['app_outfolder_recorders'])

        if not os.path.exists(WindX['app_outfolder_recorders']):
            user_home = re.sub(r'\\','/', os.path.expanduser('~'))
            if user_home and re.match(r'[a-z]+', user_home, re.I):
                tmp_folder = re.sub(r'\\','/', os.path.join(user_home, 'Downloads/AT-Records'))
                os.makedirs(tmp_folder)
                if os.path.exists(tmp_folder):
                    WindX['app_outfolder_recorders'] = tmp_folder

    #print(sys._getframe().f_lineno,"\n", os.path.dirname(WindX['app_ui_languages']))
    #print(sys._getframe().f_lineno,os.path.basename(WindX['app_ui_languages']), "\n")

    WindX['main'] = None
    WindX['mainPX'] = 20
    WindX['mainPY'] = 20
    
    WindX['b_AudioRecord_action'] = False
    WindX['SystemAudioDevice_data'] = {}
    WindX['yscrollbar_oWidth'] = 0
    WindX['start_time'] = time.time()

    WindX['ClassScrollableFrame_frame_rows'] = 0
    WindX['frame_visualize_cur_page'] = {}
    WindX['frame_visualize_all_pages'] = {}
    WindX['frame_visualize_cur_page_done'] = {}
    WindX['frame_visualize_all_pages_ui_index'] = 0
    WindX['win_last_geo'] = ""
    WindX['add_ui_data'] = []
    WindX['audio_play_Go_working'] = []
    WindX['audio_play_Go_working_by_row'] = {}

    WindX['AudioRecordOptions_show'] = True
    WindXX['AudioDevicesSelected'] = {}
    WindXX['AudioDevicesInfo'] = {}
    WindX['b_AudioDevicesSelected_labels'] = {}
    WindX['b_AudioDevicesSelected_checkboxes'] = {}
    WindX['AudioWatchingOptions_show'] = False
    WindXX['WatchingOptions_Vars'] = {}
    WindXX['WatchingOptions_Vars_ms_languages'] = {}
    WindX['amplitude_to_db_vals'] = {}
    WindX['audio_visualizationGo_PointData'] = {}
    WindX['audio_visualizationGo_x0'] = 0
    WindX['audio_visualizationGo_canvas_items'] = {}
    WindX['audio_file_format'] = 'wav'
    WindX['AudioRecordPause_Yes'] = False
    WindX['b_AudioDeviceTests'] = {}
    WindX['AudioAccountOptions_show'] = False
    WindX['MoreLanguages_show'] = False

    WindXX['WatchingOptions_opts'] = {}
    WindXX['UI_LANG'] = None
    WindXX['UI_LANG_SEL'] = "CN"
    WindX['EncryptCode_current'] = ""
    WindX['last_ss_values'] = {}
    WindX['win_main_background'] = "#303030"
    WindX['self_scrollable_frame2'] = 0

def GUI_Init():
    WindX['win_main_background'] = "#303030"
        
    WindXX['WatchingOptions_opts'] = {
        'ui_language' : ['selectbox', 'CN - 简体中文', GUI_LANG(1), GUI_LANG(1), ['EN - English', 'CN - 简体中文']], 
        'convert_to_language' : ['selectbox', '1537 - ' + GUI_LANG(2), GUI_LANG(3),GUI_LANG(3), ['1737 - '+ GUI_LANG(109), '1537 - '  + GUI_LANG(2)]], 
        'convert_engine' : ['selectbox', '1 - ' + GUI_LANG(103), GUI_LANG(4), GUI_LANG(4), ['1 - ' + GUI_LANG(103), '2 - ' + GUI_LANG(104), '3 - ' + GUI_LANG(105),'4 - ' + GUI_LANG(5)]],
        'translate_to'   : ['selectbox', GUI_LANG(108), GUI_LANG(6), GUI_LANG(6), [GUI_LANG(108), GUI_LANG(109), '']], 
        'ms_languages_selected': ['entry', '', '', WindX['ms_languages_selected_default'], ''],
        'self_root_folder':['entry', '', GUI_LANG(114), GUI_LANG(115), ''],
        
        'frames_per_buffer' : ['selectbox', 1024, GUI_LANG(7),GUI_LANG(8), [256, 512, 1024, 2048, 4896]], 
        'channels' : ['selectbox','1 - '+ GUI_LANG(106), GUI_LANG(9), GUI_LANG(10), ['1 - '+ GUI_LANG(106), '2 - '+ GUI_LANG(107)]], 
        'format' : ['selectbox', 16, GUI_LANG(11), GUI_LANG(12), [8, 16, 24, 32]],   #pyaudio.paInt16, .paInt8, .paInt16, .paInt24, .paInt32
        'rate' : ['selectbox', 16000, GUI_LANG(13), GUI_LANG(14), [8000, 16000, 32000, 48000, 96000]],

        'audio_threshold' : ['entry', 50, GUI_LANG(15), GUI_LANG(16)], 
        'audioop_rms_threshold': ['entry', 100, GUI_LANG(17), GUI_LANG(18)], 
        'break_points' : ['entry', 5, GUI_LANG(19), GUI_LANG(20)],  
        'audio_frame_rate' : ['entry', 200, GUI_LANG(21), GUI_LANG(22)], 
        'audio_section_max_length': ['entry', 25, GUI_LANG(110), GUI_LANG(111)], 

        'audio_visualization_interval' : ['entry', 5, GUI_LANG(23), GUI_LANG(24)],
        'audio_visualization_signal_enhance' : ['entry', 1.5, GUI_LANG(25), GUI_LANG(26)],
        'audio_visualization_num_per_page' : ['entry', 10, GUI_LANG(82), GUI_LANG(83)],
        'audio_visualization_line_color' : ['entry', 'red', GUI_LANG(112), GUI_LANG(113)],

        'translate_baidu_app_id' :  ['entry', '', GUI_LANG(27), GUI_LANG(28), 'encrypt'],
        'translate_baidu_app_key' : ['entry', '', GUI_LANG(29), GUI_LANG(30), 'encrypt'],

        'translate_azure_app_key' :  ['entry', '', GUI_LANG(95), GUI_LANG(96), 'encrypt'],
        'translate_azure_app_region':['entry', '', GUI_LANG(97), GUI_LANG(98), 'encrypt'],

        'audio2text_baidu_app_id' :  ['entry', '', GUI_LANG(31), GUI_LANG(32), 'encrypt'],
        'audio2text_baidu_api_key' : ['entry', '', GUI_LANG(33), GUI_LANG(34), 'encrypt'],
        'audio2text_baidu_api_secret_key' : ['entry', '', GUI_LANG(35), GUI_LANG(36), 'encrypt'],

        'audio2text_azure_api_speech_key' : ['entry', '', GUI_LANG(91), GUI_LANG(92), 'encrypt'],
        'audio2text_azure_api_speech_region' : ['entry', '', GUI_LANG(93), GUI_LANG(94), 'encrypt']
    }

def GUI_LANG_STD():
    lang_std = {
        '1': "UI Language",
        '2': "Simplified Chinese",
        '3': "Audio Language",
        '4': "Audio Engine",
        '5': "Not Convert - record only",
        '6': "Translate To",
        '7': "Audio samples per buffer",
        '8': "Specifies the number of samples per buffer",
        '9': "Audio number of channels",
        '10': "Number of audio channels (1 for mono, 2 for stereo)",
        '11': "Audio sample size",
        '12': "Sampling size and format: x bits per sample",
        '13': "Audio sampling rate",
        '14': "Audio sampling rate in Hz",
        '15': "Audio threshold",
        '16': "Audio threshold: audio value not less than this threshold will be consider valid voice",
        '17': "Audioop.rms threshold",
        '18': "Audioop.rms: Return the root-mean-square of the fragment, i.e. sqrt(sum(S_i^2)/n).\nThis is a measure of the power in an audio signal.",
        '19': "Audio Break points",
        '20': "break point after consecutive X samples are below the Watch threshold",
        '21': "Audio Watch interval",
        '22': "Check X times per second, if no signal input",
        '23': "Visualizing interval",
        '24': "Refresh audio visualization in X times of Audio frames per buffer",
        '25': "Visualizing signal enhance",
        '26': "visualizing signal enhance, \nto make better looking of the sinal diagram, should be greater than 1",
        '27': "Translatror - Baidu ID",
        '28': "Translatror - Baidu App ID, register with https://api.fanyi.baidu.com/",
        '29': "Translatror - Baidu Key",
        '30': "Translatror - Baidu App key",
        '31': "Audio to Text - Baidu App-ID",
        '32': "Audio to Text - Baidu ID, register with https://ai.baidu.com/ai-doc/SPEECH/pk4o0bkx8/",
        '33': "Audio to Text - Baidu Key",
        '34': "Audio to Text - Baidu App-Key",
        '35': "Audio to Text - Baidu Secret Key",
        '36': "Audio to Text - Baidu App-Secret-Key",
        '37': "Show / Hide options",
        '38': "Load History",
        '39': "Pause / Continue",
        '40': "◉ Click to start recording",
        '41': "Basic Information",
        '42': "Audio Language",
        '43': "Audio Engine",
        '44': "Translate To",
        '45': "Audio Devices (select for recording)",
        '46': "Click to refresh Audio Devices",
        '47': "Audio - Other Options ⋁",
        '48': "Click to show / hide options",
        '49': "UI language change to",
        '50': "Change UI language to",
        '51': "this app needs to restart, go?",
        '52': "Change UI language, restart ...",
        '53': "Check to end convertor ...",
        '54': "---- Kill this process! ----",
        '55': "Initiating convertor ...",
        '56': "Open File",
        '57': "AudioRecordLoadHistory: selected a wrong file name, it should be audio_info.json!!",
        '58': "Load History: you selected a wrong file name, its name should be 'audio_info.json' !!",
        '59': "◉ Click to start recording",
        '60': "■ Click to stop recording",
        '61': "\nrecord default device\n\tdevice info:",
        '62': "\nAudio deviceCount=",
        '63': "\n.... Audio device #",
        '64': "selectable",
        '65': "Test device #",
        '66': "\noutput folder:",
        '67': "\nAudio - Other Options:",
        '68': "Please select max 5 devices!!",
        '69': "Please select at least one device!!",
        '70': "Warning",
        '71': "\nrecording device #",
        '72': "\n\tdevice info:",
        '73': "saved to:",
        '74': "\ntesting selected device: #",
        '75': "Audio - Other Options",
        '76': "KT Recorder",
        '77': "\ncustom settings:",
        '78': "First Page",
        '79': "Previous Page",
        '80': "Next Page",
        '81': "Last Page",
        '82': "Visualizing points per page",
        '83': "display how many audio points per page on the screen.",
        '84': "Code to encrypt or decrypt your data",
        '85': "Please input the code to encrypt or decrypt your data",
        '86': "encrypt code",
        '87': "Encrypt code is changed!\nDo you want to continue?",
        '88': "Can not decrypt",
        '89': "please input new values for them!!",
        '90': "Please select an Audio Language!",
        "91": "Audio to Text - MS Azure Speech-Key",
        "92": "Audio to Text - MS Azure Speech-Key, register with https://portal.azure.com/#view/Microsoft_Azure_ProjectOxford/CognitiveServicesHub/~/SpeechServices",
	    "93": "Audio to Text - MS Azure Region-Key",
	    "94": "Audio to Text - MS Azure Region-Key",
        "95": "Translatror - MS Azure Key",
        "96": "Translatror - MS Azure Key, register with https://portal.azure.com/#home",
        "97": "Translatror - MS Azure Region",
        "98": "Translatror - MS Azure Region",
        "99": "My Accounts",
        "100":"Click to show / hide options",
        "101":"Click to open the link",
        "102":"pause ... ...",
        "103":"Baidu",
	    "104":"Google",
	    "105":"Microsoft Azure AI",
        "106":"mono",
	    "107":"stereo",
        "108":"Simplified Chinese",
	    "109":"English",
        "110":"Audio section max length",
	    "111":"Seconds, not allow one audio section too long, normally <= 30 seconds, \nbecause of audio length limit for converting audio to text!",
        "112":"Visualizing line color",
	    "113":"Visualizing line color: color name or hex format as #FFFFFF, \nbut will use its device's assigned color in priority.",
        "114":"Records saved in",
        "115":"Records saved in, where you keep the audio records",
        "116":"Select Folder",
        "117":"Please run the file: AudioTranslatorConvertor.(exe|py)\n in the folder",
        "118":"Have you run it now?",
        "119":"More languages",
        "120":"Languages available for MS speech engine"
    }
    
    return lang_std

def GUI_LANG(n):
    if not re.match(r'^\d+$', str(n)):
        return "N/A"
    
    if not WindXX['UI_LANG']:
        if os.path.exists(WindX['app_ui_languages']):
            WindXX['UI_LANG'] = UT_JsonFileRead(filepath= WindX['app_ui_languages'])    #{1:{'CN':""  , 'EN':""}, 2:{'CN':""  , 'EN':""}, ...}
            vals = UT_JsonFileRead(filepath= WindX['app_watching_options_file'])
            if vals and vals.__contains__('custom') and vals["custom"].__contains__('ui_language') and re.match(r'.*English', vals["custom"]['ui_language'], re.I):
                WindXX['UI_LANG_SEL'] = "EN"
        else:
            lang_std = GUI_LANG_STD()
            langs = {}
            for num in lang_std.keys():
                langs[num] = {
                    'CN':"",
                    'EN': lang_std[num]
                }
            
            print("\n#AR", sys._getframe().f_lineno,"Saved to:", WindX['app_ui_languages'])
            UT_JsonFileSave(filepath= WindX['app_ui_languages'], fdata= langs)

    n = str(n)
    if WindXX['UI_LANG'] and WindXX['UI_LANG'].__contains__(n) and WindXX['UI_LANG'][n].__contains__(WindXX['UI_LANG_SEL']) and len(WindXX['UI_LANG'][n][WindXX['UI_LANG_SEL']]):
        return WindXX['UI_LANG'][n][WindXX['UI_LANG_SEL']]
    else:
        lang_std = GUI_LANG_STD()
        if lang_std.__contains__(n):
            return lang_std[n]
        else:
            return "??"
        
def GUI():
    GUI_Init()

    WindX['main'] = Tk()
    WindX['main'].title(GUI_LANG(76) + " Rev " + WindX['main_rev'])
    WindX['main'].geometry('+' + str(WindX['mainPX']) + '+' + str(WindX['mainPY']))
    WindX['main'].wm_attributes('-topmost',1) 
    WindX['main'].protocol("WM_DELETE_WINDOW", WindExit)

    bgcolor = WindX['win_main_background']
    fgcolor = '#FFFFFF'
    WindX['Frame1'] = Frame(WindX['main'], bg=bgcolor)
    WindX['Frame1'].grid(row=0,column=0,sticky=E+W+S+N,pady=0,padx=0)

    WindX['Frame2'] = Frame(WindX['main'], bg= WindX['win_main_background'])
    WindX['Frame2'].grid(row=1,column=0,sticky=E+W+S+N,pady=0,padx=0)

    WindX['Frame3'] = Frame(WindX['main'], bg='#B0B0B0')
    WindX['Frame3'].grid(row=2,column=0,sticky=E+W+S+N,pady=0,padx=0)

    WindX['main'].grid_columnconfigure(0, weight=1)
    WindX['main'].grid_rowconfigure(1, weight=1)
   
    #s = ttk.Style()
    #s.configure('My.TCombobox', foreground=fgcolor, background=bgcolor, selectbackground=bgcolor)
    key_button_pady = 8
    if WindX['Frame1']:        
        row = 0 
        col = 0
        b=iButton(WindX['Frame1'],row,col, AudioRecordOptions,'⋀',fg=fgcolor,bg=bgcolor,p=[LEFT,FLAT,3,key_button_pady,'#A0A0A0','#A0A0A0',10,E+W+N+S,1,1]) 
        WindX['b_AudioRecordOptions'] = b.b
        UI_WidgetBalloon(WindX['b_AudioRecordOptions'], GUI_LANG(37))

        col +=1
        b=iButton(WindX['Frame1'],row,col, AudioRecordLoadHistory,'↺',fg=fgcolor,bg=bgcolor,p=[LEFT,FLAT,3,key_button_pady,'#A0A0A0','#A0A0A0',10,E+W+N+S,1,1]) 
        WindX['b_AudioRecordLoad'] = b.b
        UI_WidgetBalloon(WindX['b_AudioRecordLoad'], GUI_LANG(38))

        col +=1
        b=iButton(WindX['Frame1'],row,col, AudioRecordPause,'||',fg=fgcolor,bg=bgcolor,p=[LEFT,FLAT,3,key_button_pady,'#A0A0A0','#A0A0A0',10,E+W+N+S,1,1]) 
        WindX['b_AudioRecordPause'] = b.b
        UI_WidgetBalloon(WindX['b_AudioRecordPause'], GUI_LANG(39))

        col +=1
        b=iButton(WindX['Frame1'],row,col, AudioRecord, GUI_LANG(40) ,fg=fgcolor,bg=bgcolor,p=[LEFT,FLAT,3,key_button_pady,'#A0A0A0','#A0A0A0',10,E+W+N+S,1,1]) 
        WindX['b_AudioRecord'] = b.b
        #UI_WidgetBalloon(WindX['b_AudioRecord'], GUI_LANG(40))
    
        row +=1
        WindX['Frame11'] = Frame(WindX['Frame1'])
        WindX['Frame11'].grid(row=row,column=0,sticky=E+W+S+N,pady=1,padx=0, columnspan=10)
        if WindX['Frame11']:
            row11 = 0
            col11 = 0
            WindX['Frame110A'] = Frame(WindX['Frame11'])
            WindX['Frame110A'].grid(row=row11,column=col11,sticky=E+W+S+N,pady=5,padx=0,columnspan=10)
            if WindX['Frame110A']:
                row110A = 0
                Label(WindX['Frame110A'], text= "1. " + GUI_LANG(41), justify=LEFT, relief=FLAT,pady=3,padx=3, fg='blue').grid(row=row110A,column=0,sticky=W, columnspan=10)

                row110A += 1
                #Encrypt code
                Label(WindX['Frame110A'], text=' ', justify=LEFT, relief=FLAT,pady=3,padx=3, width=3 ).grid(row=row110A,column=0,sticky=W, pady=3)
                Label(WindX['Frame110A'], text= GUI_LANG(86), justify=LEFT, relief=FLAT,pady=3,padx=3).grid(row=row110A,column=1,sticky=W)          
                WindXX['EncryptCode'] = StringVar()
                e=Entry(WindX['Frame110A'], justify=CENTER, relief=FLAT, textvariable=WindXX['EncryptCode'], show="*", width=10)
                e.grid(row=row110A,column=2,sticky=E+W+N+S,pady=3,padx=0)
                e.bind('<Button>',    func=UT_HandlerAdaptor(UI_WidgetEntryShow,e=e,ishow=''))
                e.bind('<Leave>',     func=UT_HandlerAdaptor(UI_WidgetEntryShow,e=e,ishow='*'))
                e.bind('<KeyRelease>',func=UT_HandlerAdaptor(UI_KeyInputCheck,e=e))
                e.focus()
                WindX['e_EncryptCode'] = e
                UI_WidgetBalloon(e,  GUI_LANG(84))        

                psw_lbl = Label(WindX['Frame110A'], text=GUI_LANG(86), justify=CENTER, relief=FLAT, pady=3, fg='red', bg='white')
                psw_lbl.grid(row=row110A,column=2,sticky=E+W+N+S,pady=3,padx=0)
                psw_lbl.bind('<Button>',   func=UT_HandlerAdaptor(UI_WidgetEntryShow,e=psw_lbl,ishow='close'))
                UI_WidgetBalloon(psw_lbl,  GUI_LANG(84)) 

                #UI Language
                Label(WindX['Frame110A'], text=' ', justify=LEFT, relief=FLAT,pady=3,padx=3, width=3 ).grid(row=row110A,column=3,sticky=W)
                Label(WindX['Frame110A'], text= GUI_LANG(1),  justify=LEFT, relief=FLAT,pady=3,padx=3).grid(row=row110A,column=4,sticky=W)
                WindXX['WatchingOptions_Vars']['ui_language'] = StringVar()
                e = ttk.Combobox(WindX['Frame110A'], textvariable= WindXX['WatchingOptions_Vars']['ui_language'], justify=CENTER,state="readonly") #, style='My.TCombobox'
                e.grid(row=row110A,column=5,sticky=E+W+S+N,pady=3,padx=1)
                e['values'] = WindXX['WatchingOptions_opts']['ui_language'][4]
                WindXX['WatchingOptions_Vars']['ui_language'].set(WindXX['WatchingOptions_opts']['ui_language'][1])
                WindX['b_ui_language'] = e
                e.bind("<<ComboboxSelected>>", UI_LanguageChange)
                UI_WidgetBalloon(e, GUI_LANG(1))
                print(sys._getframe().f_lineno,"WindXX['WatchingOptions_Vars']['ui_language'].get()=", WindXX['WatchingOptions_Vars']['ui_language'].get())
                #print(sys._getframe().f_lineno,e.configure())

                row110A += 1
                #convert engine
                Label(WindX['Frame110A'], text=' ', justify=LEFT, relief=FLAT,pady=3,padx=3, width=3).grid(row=row110A,column=0,sticky=W, pady=3)

                Label(WindX['Frame110A'], text= GUI_LANG(43), justify=LEFT, relief=FLAT,pady=3,padx=3).grid(row=row110A,column=1,sticky=W)
                WindXX['WatchingOptions_Vars']['convert_engine'] = StringVar()
                e = ttk.Combobox(WindX['Frame110A'], textvariable= WindXX['WatchingOptions_Vars']['convert_engine'], justify=LEFT,state="readonly", width=30)
                e.grid(row=row110A,column=2,sticky=E+W+S+N,pady=3,padx=1)
                e['values'] = WindXX['WatchingOptions_opts']['convert_engine'][4]
                WindXX['WatchingOptions_Vars']['convert_engine'].set(WindXX['WatchingOptions_opts']['convert_engine'][1])
                e.bind("<<ComboboxSelected>>", UI_ConvertEngineChange)
                
                row110A += 1
                Label(WindX['Frame110A'], text=' ', justify=LEFT, relief=FLAT,pady=3,padx=3, width=3 ).grid(row=row110A,column=0,sticky=W, pady=3)
                Label(WindX['Frame110A'], text= GUI_LANG(42), justify=LEFT, relief=FLAT,pady=3,padx=3).grid(row=row110A,column=1,sticky=W)
                WindXX['WatchingOptions_Vars']['convert_to_language'] = StringVar()
                e = ttk.Combobox(WindX['Frame110A'], textvariable= WindXX['WatchingOptions_Vars']['convert_to_language'], justify=LEFT,state="readonly", width=30)
                e.grid(row=row110A,column=2,sticky=E+W+S+N,pady=3,padx=1)
                e['values'] = WindXX['WatchingOptions_opts']['convert_to_language'][4]
                WindX['b_ui_convert_to_language'] = e
                WindXX['WatchingOptions_Vars']['convert_to_language'].set(WindXX['WatchingOptions_opts']['convert_to_language'][1])

                Label(WindX['Frame110A'], text=' ', justify=LEFT, relief=FLAT,pady=3,padx=3, width=3 ).grid(row=row110A,column=3,sticky=W)
                Label(WindX['Frame110A'], text= GUI_LANG(44), justify=LEFT, relief=FLAT,pady=3,padx=3).grid(row=row110A,column=4,sticky=W)
                WindXX['WatchingOptions_Vars']['translate_to'] = StringVar()
                e = ttk.Combobox(WindX['Frame110A'], textvariable= WindXX['WatchingOptions_Vars']['translate_to'], justify=LEFT,state="readonly", width=30)
                e.grid(row=row110A,column=5,sticky=E+W+S+N,pady=3,padx=1)
                e['values'] = WindXX['WatchingOptions_opts']['translate_to'][4]
                WindX['b_ui_translate_to'] = e
                WindXX['WatchingOptions_Vars']['translate_to'].set(WindXX['WatchingOptions_opts']['translate_to'][1])
                #print(sys._getframe().f_lineno,"WindXX['WatchingOptions_Vars']['translate_to'].get()=",WindXX['WatchingOptions_Vars']['translate_to'].get())

                b=iButton(WindX['Frame110A'],row110A,6, UI_MoreLanguages, '...' ,fg='blue',bg='#EFEFEF', p=[LEFT,FLAT,3,1,'#FFFF66','#FFFF99',10,E+W+N+S,1,1]) 
                WindX['b_ui_more_languages'] = b.b
                UI_WidgetBalloon(b.b, GUI_LANG(119))

                row110A += 1                
                WindX['Frame110A1'] = Frame(WindX['Frame110A'], bg="gray")
                WindX['Frame110A1'].grid(row=row110A,column=1,sticky=E+W+S+N,pady=1,padx=0, columnspan=5)
                if WindX['Frame110A1']:
                    #WindX['Frame110A11'] = Frame(WindX['Frame110A1'])
                    #WindX['Frame110A11'].grid(row=0,column=0,sticky=E+W+S+N,pady=1,padx=1, columnspan=10)

                    Frame110A11 = ClassScrollableFrame2(WindX['Frame110A1'])                 
                    Frame110A11.grid(row=0,column=0,sticky=E+W+S+N,pady=1,padx=1, columnspan=10)
                    #WindX['main'].bind("<MouseWheel>",  Frame110A11.canvasMouseWheel)
                    Frame110A11.scrollable_frame.grid_columnconfigure(2, weight=1)
                    WindX['Frame110A11'] = Frame110A11.scrollable_frame

                    lang_list = UI_ConvertEngineChange(get3list=True)
                    Label(WindX['Frame110A11'], text= GUI_LANG(120) + ' ('+ str(len(lang_list)) +')', justify=LEFT, relief=FLAT,pady=3,padx=3, anchor="w", bg="#D0D0D0").grid(row=0,column=1,sticky=E+W+S+N, columnspan=10)
                    row110A11 = 1
                    col110A11 = 0                    
                    for lang in lang_list:
                        col110A11 += 1  
                        langs = re.split(r'\s+', lang)
                        fname = langs[0]
                        WindXX['WatchingOptions_Vars_ms_languages'][fname] = BooleanVar()
                        cb = Checkbutton(WindX['Frame110A11'], text= lang, variable=WindXX['WatchingOptions_Vars_ms_languages'][fname], justify=LEFT, anchor="w", relief=FLAT,pady=3,padx=3)
                        cb.grid(row= row110A11,column=col110A11,sticky=E+W+S+N)
                        #cb.bind('<ButtonRelease-1>', UI_MoreLanguagesChange)
                        cb.bind("<MouseWheel>",  Frame110A11.canvasMouseWheel)
                        ischecked = False
                        for lx in WindXX['WatchingOptions_opts']['ms_languages_selected'][3]:
                            if re.match(r'^{}(\-|\s+)'.format(lx), lang, re.I):
                                ischecked = True                                
                                break
                        WindXX['WatchingOptions_Vars_ms_languages'][fname].set(ischecked)

                        if col110A11 > 2:
                            col110A11 = 0
                            row110A11 +=1

                    WindX['Frame110A1'].grid_columnconfigure(0, weight=1)
                    WindX['Frame110A11'].bind('<Leave>', UI_MoreLanguagesChange)

                    row110A11 += 1
                    WindXX['WatchingOptions_Vars']['ms_languages_selected'] = StringVar()
                    e=Entry(WindX['Frame110A11'], justify=LEFT, relief=FLAT, textvariable= WindXX['WatchingOptions_Vars']['ms_languages_selected'], state='readonly', fg='green')
                    e.grid(row=row110A11,column=0,sticky=E+W+N+S,pady=0,padx=0, columnspan=4)
                    WindXX['WatchingOptions_Vars']['ms_languages_selected'].set(", ".join(WindXX['WatchingOptions_opts']['ms_languages_selected'][3]))

                row110A += 1
                Label(WindX['Frame110A'], text=' ', justify=LEFT, relief=FLAT,pady=3,padx=3, width=3 ).grid(row=row110A,column=0,sticky=W, pady=3)
                Label(WindX['Frame110A'], text= GUI_LANG(114), justify=LEFT, relief=FLAT,pady=3,padx=3).grid(row=row110A,column=1,sticky=W)
                WindXX['WatchingOptions_Vars']['self_root_folder'] = StringVar()
                e=Entry(WindX['Frame110A'], justify=LEFT, relief=FLAT, textvariable= WindXX['WatchingOptions_Vars']['self_root_folder'], width=10)
                e.grid(row=row110A,column=2,sticky=E+W+N+S,pady=3,padx=0, columnspan=4)
                UI_WidgetBalloon(e,  GUI_LANG(115))   

                b=iButton(WindX['Frame110A'],row110A,6, UI_SetFolder, '...' ,fg='blue',bg='#EFEFEF', p=[LEFT,FLAT,3,1,'#FFFF66','#FFFF99',10,E+W+N+S,1,1]) 
                UI_WidgetBalloon(b.b, GUI_LANG(116))

            row11 +=1
            #Label(WindX['Frame11'], text='Audio Devices (select for watching):', justify=LEFT, relief=FLAT,pady=3,padx=3).grid(row=row11,column=0,sticky=W,columnspan=10, pady=1)
            b=iButton(WindX['Frame11'],row11,0, AudioDeviceRefresh, "2. " + GUI_LANG(45),fg='blue',bg='#EFEFEF',colspan=10, p=[LEFT,FLAT,3,1,'#FFFF66','#FFFF99',10,E+W+N+S,1,1]) 
            b.b.configure(anchor='nw')
            UI_WidgetBalloon(b.b, GUI_LANG(46))

            row11 +=1
            WindX['Frame111'] = Frame(WindX['Frame11'])
            WindX['Frame111'].grid(row=row11,column=0,sticky=E+W+S+N,pady=0,padx=0,columnspan=10)

            row11 +=1
            b=iButton(WindX['Frame11'],row11,0, AudioWatchingOptions, "3. " + GUI_LANG(47),fg='blue',bg='#EFEFEF',colspan=10, p=[LEFT,FLAT,3,1,'#FFFF66','#FFFF99',10,E+W+N+S,1,1]) 
            WindX['b_AudioWatchingOptions'] = b.b
            b.b.configure(anchor='nw')
            UI_WidgetBalloon(b.b, GUI_LANG(48))

            row11 +=1
            WindX['Frame112'] = Frame(WindX['Frame11'])
            WindX['Frame112'].grid(row=row11,column=0,sticky=E+W+S+N,pady=5,padx=0,columnspan=10)
            if WindX['Frame112']:
                except_ss = [
                    'convert_to_language', 
                    'convert_engine', 
                    'translate_to', 
                    'ui_language', 
                    'ms_languages_selected',
                    'self_root_folder',

                    'translate_baidu_app_id',
                    'translate_baidu_app_key',

                    'translate_azure_app_key',
                    'translate_azure_app_region',

                    'audio2text_baidu_app_id',
                    'audio2text_baidu_api_key',
                    'audio2text_baidu_api_secret_key',

                    'audio2text_azure_api_speech_key',
                    'audio2text_azure_api_speech_region'
                ]

                opts = WindXX['WatchingOptions_opts']
                row112 = 0
                for s in opts.keys():  
                    if s in except_ss:
                        continue

                    iipady = 0
                    if row112 % 2:
                        iipady = 0
                    else:
                        iipady = 1

                    Label(WindX['Frame112'], text=" ", justify=LEFT, relief=FLAT,pady=3,padx=3, width=3).grid(row=row112,column=0,sticky=W,pady=iipady)
                    Label(WindX['Frame112'], text= "3." + UT_number_0_format(row112 + 1) + " " + opts[s][2], justify=LEFT, relief=FLAT,pady=3,padx=3).grid(row=row112,column=1,sticky=W,pady=iipady)
                    
                    e = None
                    WindXX['WatchingOptions_Vars'][s] = StringVar()
                    if opts[s][0] == 'entry':
                        e=Entry(WindX['Frame112'], justify=LEFT, relief=FLAT, textvariable= WindXX['WatchingOptions_Vars'][s])
                        e.grid(row=row112,column=2, sticky=E+W+N+S,padx=1,pady=iipady)
                        e.insert(0, opts[s][1])
                    else:
                        e = ttk.Combobox(WindX['Frame112'], textvariable= WindXX['WatchingOptions_Vars'][s], justify=LEFT,state="readonly")
                        e.grid(row=row112,column=2, sticky=E+W+N+S,padx=1,pady=iipady)
                        e['values'] = opts[s][4]

                    WindXX['WatchingOptions_Vars'][s].set(opts[s][1])
                    #UI_WidgetBalloon(e, opts[s][3])

                    #Label(WindX['Frame112'], text=opts[s][3], justify=LEFT, relief=FLAT,pady=3,padx=3, fg='#A0A0A0').grid(row=row112,column=3,sticky=W,pady=1)                    
                    lbl = Label(WindX['Frame112'], text=opts[s][3], justify=LEFT, relief=FLAT,pady=3,padx=3, fg='#606060')
                    lbl.grid(row=row112,column=3,sticky=W,pady=iipady)
                    s3 = re.sub(r"\n+", "\t", opts[s][3])
                    if re.match(r'.*http(s*)\:\/\/\w+', s3, re.I):
                        link = 'http' + re.sub(r'^.*http','', s3, re.I|re.M)
                        lbl.config(fg='#505050')
                        lbl.bind('<Button-1>',func=UT_HandlerAdaptor(UT_OpenLink, link=link))
                        lbl.bind('<Motion>', func=UT_HandlerAdaptor(UI_ChangeBackgroud, e=lbl, color='#FFFF66'))
                        lbl.bind('<Leave>',  func=UT_HandlerAdaptor(UI_ChangeBackgroud, e=lbl, color='#EFEFEF'))
                        UI_WidgetBalloon(lbl, GUI_LANG(101) + ": " + link)

                    row112 +=1
                
                WindX['Frame112'].grid_columnconfigure(2, weight=1)
                #WindX['Frame112'].grid_columnconfigure(3, weight=1)

            row11 +=1
            b=iButton(WindX['Frame11'],row11,0, AudioAccountOptions, "4. " + GUI_LANG(99) + ' ⋁',fg='blue',bg='#EFEFEF',colspan=10, p=[LEFT,FLAT,3,1,'#FFFF66','#FFFF99',10,E+W+N+S,1,1]) 
            WindX['b_AudioAccountOptions'] = b.b
            b.b.configure(anchor='nw')
            UI_WidgetBalloon(b.b, GUI_LANG(100)) 

            row11 +=1
            WindX['Frame113'] = Frame(WindX['Frame11'])
            WindX['Frame113'].grid(row=row11,column=0,sticky=E+W+S+N,pady=5,padx=0,columnspan=10)     
            if WindX['Frame113']:
                accept_ss = [
                    'translate_baidu_app_id',
                    'translate_baidu_app_key',

                    'translate_azure_app_key',
                    'translate_azure_app_region',

                    'audio2text_baidu_app_id',
                    'audio2text_baidu_api_key',
                    'audio2text_baidu_api_secret_key',

                    'audio2text_azure_api_speech_key',
                    'audio2text_azure_api_speech_region'
                ]
                opts = WindXX['WatchingOptions_opts']
                row112 = 0                
                for s in opts.keys():
                    if not (s in accept_ss):
                        continue
                    
                    iipady = 0
                    if row112 % 2:
                        iipady = 0
                    else:
                        iipady = 1

                    Label(WindX['Frame113'], text=" ", justify=LEFT, relief=FLAT,pady=3,padx=3, width=3).grid(row=row112,column=0,sticky=W,pady=iipady)
                    Label(WindX['Frame113'], text= "4." + UT_number_0_format(row112 + 1) + " " + opts[s][2], justify=LEFT, relief=FLAT,pady=3,padx=3).grid(row=row112,column=1,sticky=W,pady=iipady)
                    
                    e = None
                    WindXX['WatchingOptions_Vars'][s] = StringVar()
                    if opts[s][0] == 'entry':
                        e=Entry(WindX['Frame113'], justify=LEFT, relief=FLAT, textvariable= WindXX['WatchingOptions_Vars'][s])
                        e.grid(row=row112,column=2, sticky=E+W+N+S,padx=1,pady=iipady)
                        e.insert(0, opts[s][1])
                        e.bind('<Button>',   func=UT_HandlerAdaptor(UI_WidgetEntryShowX,e=e))
                    else:
                        e = ttk.Combobox(WindX['Frame113'], textvariable= WindXX['WatchingOptions_Vars'][s], justify=LEFT,state="readonly")
                        e.grid(row=row112,column=2, sticky=E+W+N+S,padx=1,pady=iipady)
                        e['values'] = opts[s][4]

                    WindXX['WatchingOptions_Vars'][s].set(opts[s][1])
                    #UI_WidgetBalloon(e, opts[s][3])
  
                    lbl = Label(WindX['Frame113'], text=opts[s][3], justify=LEFT, relief=FLAT,pady=3,padx=3, fg='#606060')
                    lbl.grid(row=row112,column=3,sticky=W,pady=iipady)
                    s3 = re.sub(r"\n+", "\t", opts[s][3])
                    if re.match(r'.*http(s*)\:\/\/\w+', s3, re.I|re.M):
                        link = 'http' + re.sub(r'^.*http','', s3, re.I)
                        lbl.config(fg='#505050')
                        lbl.bind('<Button-1>', func=UT_HandlerAdaptor(UT_OpenLink, link=link))
                        lbl.bind('<Motion>', func=UT_HandlerAdaptor(UI_ChangeBackgroud, e=lbl, color='#FFFF66'))
                        lbl.bind('<Leave>',  func=UT_HandlerAdaptor(UI_ChangeBackgroud, e=lbl, color='#EFEFEF'))
                        UI_WidgetBalloon(lbl, GUI_LANG(101) + ": " + link)

                    row112 +=1
                
                WindX['Frame113'].grid_columnconfigure(2, weight=1)
                #WindX['Frame113'].grid_columnconfigure(3, weight=1)

            WindX['Frame11'].grid_columnconfigure(0, weight=1)

        row +=1
        canvas = Canvas(WindX['Frame1'], 
            width=590, 
            height=50,
            bg="#EFEFEF",
            relief=FLAT,
            bd = 0,
        )
        canvas.grid(row=row,column=0,sticky=E+W+S+N,pady=0,padx=0,columnspan=10)
        WindX['b_frame1_canvas'] = canvas
        #WindX['b_frame1_canvas'].grid_remove()

        #WindX['Frame1'].grid_columnconfigure(0, weight=1)
        WindX['Frame1'].grid_columnconfigure(3, weight=1)
        
    if WindX['Frame2']:
        row = 0
        col =0

        WindX['ClassScrollableFrame'] = ClassScrollableFrame(WindX['Frame2'])                 
        WindX['ClassScrollableFrame'].grid(row=1,column=0,sticky=E+W+S+N,pady=0,padx=0)
        WindX['main'].bind("<MouseWheel>",  WindX['ClassScrollableFrame'].canvasMouseWheel)

        WindX['ClassScrollableFrame'].scrollable_frame.grid_columnconfigure(2, weight=1)

    if WindX['Frame3']:
        row = 0 
        col = 0
        b=iButton(WindX['Frame3'],row,col, lambda:AudioPageChange(-1000),'<<',p=[LEFT,FLAT,3,key_button_pady,'#A0A0A0','#A0A0A0',10,E+W+N+S,1,0]) 
        WindX['b_AudioFirstPage'] = b.b
        UI_WidgetBalloon(WindX['b_AudioFirstPage'], GUI_LANG(78)) #"First Page"

        col +=1
        b=iButton(WindX['Frame3'],row,col, lambda:AudioPageChange(-1),'<',p=[LEFT,FLAT,3,key_button_pady,'#A0A0A0','#A0A0A0',10,E+W+N+S,1,1]) 
        WindX['b_AudioPreviousPage'] = b.b
        UI_WidgetBalloon(WindX['b_AudioPreviousPage'], GUI_LANG(79)) #"Previous Page"

        col +=1
        #lbl = Label(WindX['Frame3'], text= "  Page 1/1 (0) ", justify=CENTER, bg="#E5E5E5",relief=FLAT,pady=2,padx=0)
        #lbl.grid(row=row,column=col,sticky=E+W+S+N)
        lbl = iButton(WindX['Frame3'],row,col, None,'  Page 1/1 (0) ',fg='#A0A0A0', p=[LEFT,FLAT,3,key_button_pady,'#A0A0A0','#A0A0A0',30,E+W+N+S,1,0])        
        WindX['b_AudioPageStatus'] = lbl.b

        col +=1
        b=iButton(WindX['Frame3'],row,col, lambda:AudioPageChange(1),'>',p=[LEFT,FLAT,3,key_button_pady,'#A0A0A0','#A0A0A0',10,E+W+N+S,1,1]) 
        WindX['b_AudioNextPage'] = b.b
        UI_WidgetBalloon(WindX['b_AudioNextPage'], GUI_LANG(80)) #"Next Page"               

        col +=1
        b=iButton(WindX['Frame3'],row,col, lambda:AudioPageChange(1000),'>>',p=[LEFT,FLAT,3,key_button_pady,'#A0A0A0','#A0A0A0',10,E+W+N+S,1,0]) 
        WindX['b_AudioLastPage'] = b.b
        UI_WidgetBalloon(WindX['b_AudioLastPage'], GUI_LANG(81)) #"Last Page"

        WindX['Frame3'].grid_columnconfigure(0, weight=1)
        WindX['Frame3'].grid_columnconfigure(1, weight=1)
        WindX['Frame3'].grid_columnconfigure(3, weight=1)
        WindX['Frame3'].grid_columnconfigure(4, weight=1)

    WindX['main'].update()
    if not WindX['yscrollbar_oWidth']:
        try:
            rect = win32gui.GetWindowRect(WindX['ClassScrollableFrame'].scrollbar_y.winfo_id())  #Frame2.scrollbar_y left top right bottom (522, 78, 539, 382)
            WindX['yscrollbar_oWidth'] = abs(rect[2] - rect[0])
        except:
            print(sys._getframe().f_lineno, traceback.format_exc())

    WindX['b_ui_more_languages'].grid_remove()
    AudioDeviceRefresh()    
    WindX['ClassScrollableFrame'].canvasLeave(force=True)

    WindX['WindowRect_Frame112'] = win32gui.GetWindowRect(WindX['Frame112'].winfo_id())
    #print(sys._getframe().f_lineno,'\nFrame112', WindX['WindowRect_Frame112'])
    WindX['Frame112'].grid_remove()
    WindX['Frame113'].grid_remove()
    WindX['Frame110A1'].grid_remove()

    WindX['main'].update()
    wgeo = WindX['main'].geometry()
    #print(sys._getframe().f_lineno,'\ngeometry=', wgeo)
    WindX['main'].geometry(re.sub(r'^\d+x\d+', str(int(WindX['main'].winfo_screenwidth()/2)) + 'x' + str(int(WindX['main'].winfo_screenheight()*0.85)), wgeo))

    mainloop()

def UI_SetFolder():
    fpath = filedialog.askdirectory(initialdir = WindX['self_folder'])
    if fpath:
        if re.match(r'.*\/+Records$', fpath, re.I):
            fpath = re.sub(r'\/+Records$', '', fpath, flags=re.I)

        WindX['self_root_folder'] = re.sub(r'\/+$', '',fpath)
        WindX['app_outfolder_recorders'] = WindX['self_root_folder'] + "/Records"
        print(sys._getframe().f_lineno, "new " + GUI_LANG(115), WindX['app_outfolder_recorders'], "\nself_root_folder=", WindX['self_root_folder'])
        WindXX['WatchingOptions_Vars']['self_root_folder'].set(WindX['self_root_folder'])

def UI_KeyInputCheck(event,e=None):
    #if event.keycode == 13:
    WindX['EncryptCode_current'] = re.sub(r'\s+', '', WindXX['EncryptCode'].get())
    if not len(WindX['EncryptCode_current']):
        WindX['e_EncryptCode'].config(bg='yellow')    
    
    #print(sys._getframe().f_lineno,"EncryptCode_current:", WindX['EncryptCode_current'])

def UI_WidgetEntryShowX(event=None, e=None):
    UI_WidgetEntryShow(e=e, ishow='decrypt', code=WindX['EncryptCode_current'])

def UI_MoreLanguages(ev=None):
    #print("MoreLanguages ...")    
    if WindX['MoreLanguages_show']:
        WindX['MoreLanguages_show'] = False
        WindX['Frame110A1'].grid_remove()
    else:
        WindX['MoreLanguages_show'] = True
        WindX['Frame110A1'].grid()

def UI_MoreLanguagesChange(ev=None):
    sels = {}
    for fname in WindXX['WatchingOptions_Vars_ms_languages'].keys():        
        #print(fname, WindXX['WatchingOptions_Vars_ms_languages'][fname].get())
        if WindXX['WatchingOptions_Vars_ms_languages'][fname].get():
            fns = re.split(r'\-+', fname)
            sels[fns[0]] = 1

    selsx = sorted(sels.keys())
    selected_langs = re.split(r'\s*\,\s*', WindXX['WatchingOptions_Vars']['ms_languages_selected'].get())
    if selsx == selected_langs:
        return

    WindXX['WatchingOptions_Vars']['ms_languages_selected'].set(", ".join(selsx))
    UI_ConvertEngineChange()

    #save the change
    vals = UT_JsonFileRead(filepath= WindX['app_watching_options_file'])
    if not vals.__contains__('custom'): 
        vals['custom'] = {}
    vals['custom']['ms_languages_selected'] = ", ".join(selsx)
    UT_JsonFileSave(WindX['app_watching_options_file'], fdata=vals)

def UI_ConvertEngineChange(ev=None, get3list=False):
    ce = re.split(r'\s+', WindXX['WatchingOptions_Vars']['convert_engine'].get())
    print(sys._getframe().f_lineno,"Audio Engine:", ce)  #'1 - Baidu', '2 - Google', '3 - Bing AI','4 - '

    selected_langs = []
    if ce[0] == '3':
        WindX['b_ui_more_languages'].grid()
        selected_langs = re.split(r'\s*\,\s*', WindXX['WatchingOptions_Vars']['ms_languages_selected'].get())
        print('selected_langs=', selected_langs)
    else:
        WindX['b_ui_more_languages'].grid_remove()
        WindX['MoreLanguages_show'] = False
        WindX['Frame110A1'].grid_remove()
    
    avl = {
        '1':{
            'convert_to':  ['1737 - ' + GUI_LANG(109), '1537 - '  + GUI_LANG(2)],
            'translate_to':[GUI_LANG(108), GUI_LANG(109), '']
        },

        '4':{
            'convert_to':  ['1737 - ' + GUI_LANG(109), '1537 - '  + GUI_LANG(2)],
            'translate_to':[GUI_LANG(108), GUI_LANG(109), '']
        },

        '3':{
            'convert_to':  [
                'af-ZA 南非荷兰语（南非）', 'am-ET 阿姆哈拉语(埃塞俄比亚)', 'ar-AE 阿拉伯语（阿拉伯联合酋长国）', 'ar-BH 阿拉伯语（巴林）', 'ar-DZ 阿拉伯语（阿尔及利亚）', 'ar-EG 阿拉伯语（埃及）', 'ar-IL 阿拉伯语（以色列）',
                'ar-IQ 阿拉伯语（伊拉克）', 'ar-JO 阿拉伯语（约旦）', 'ar-KW 阿拉伯语（科威特）', 'ar-LB 阿拉伯语（黎巴嫩）', 'ar-LY 阿拉伯语（利比亚）', 'ar-MA 阿拉伯语（摩洛哥）', 'ar-OM 阿拉伯语（阿曼）', 
                'ar-PS 阿拉伯语（巴勒斯坦民族权利机构）', 'ar-QA 阿拉伯语（卡塔尔）', 'ar-SA 阿拉伯语(沙特阿拉伯)', 'ar-SY 阿拉伯语（叙利亚）', 'ar-TN 阿拉伯语（突尼斯）', 'ar-YE 阿拉伯语（也门）', 'az-AZ 阿塞拜疆语(拉丁语，阿塞拜疆)', 
                'bg-BG 保加利亚语(保加利亚)', 'bn-IN 孟加拉语（印度）', 'bs-BA 波斯尼亚语（波斯尼亚和黑塞哥维那）', 'ca-ES 加泰罗尼亚语', 'cs-CZ 捷克语(捷克)', 'cy-GB 威尔士语（英国）', 'da-DK 丹麦语（丹麦）', 'de-AT 德语（奥地利）', 
                'de-CH 德语（瑞士）', 'de-DE 德语（德国）', 'el-GR 希腊语(希腊)', 'en-AU 英语（澳大利亚）', 'en-CA 英语（加拿大）', 'en-GB 英语（英国）', 'en-GH 英语（加纳）', 'en-HK 英语（香港特別行政区）', 
                'en-IE 英语（爱尔兰）', 'en-IN 英语（印度）', 'en-KE 英语（肯尼亚）', 'en-NG 英语（尼日利亚）', 'en-NZ 英语（新西兰）', 'en-PH 英语（菲律宾）', 'en-SG 英语（新加坡）', 'en-TZ 英语（坦桑尼亚）', 
                'en-US 英语（美国）', 'en-ZA 英语（南非）', 'es-AR 西班牙语（阿根廷）', 'es-BO 西班牙语（玻利维亚）', 'es-CL 西班牙语（智利）', 'es-CO 西班牙语（哥伦比亚）', 'es-CR 西班牙语（哥斯达黎加）', 'es-CU 西班牙语（古巴）', 
                'es-DO 西班牙语（多米尼加共和国）', 'es-EC 西班牙语（厄瓜多尔）', 'es-ES 西班牙语(西班牙)', 'es-GQ 西班牙语（赤道几内亚）', 'es-GT 西班牙语（危地马拉）', 'es-HN 西班牙语（洪都拉斯）', 'es-MX 西班牙语(墨西哥)', 
                'es-NI 西班牙（尼加拉瓜）', 'es-PA 西班牙语（巴拿马）', 'es-PE 西班牙语（秘鲁）', 'es-PR 西班牙语（波多黎各）', 'es-PY 西班牙语（巴拉圭）', 'es-SV 西班牙语（萨尔瓦多）', 'es-US 西班牙语（美国）', 
                'es-UY 西班牙语（乌拉圭）', 'es-VE 西班牙语（委内瑞拉）', 'et-EE 爱沙尼亚语(爱沙尼亚)', 'eu-ES 巴斯克语', 'fa-IR 波斯语（伊朗）', 'fi-FI 芬兰语（芬兰）', 'fil-PH 菲律宾语（菲律宾）', 'fr-BE 法语（比利时）', 
                'fr-CA 法语（加拿大）', 'fr-CH 法语（瑞士）', 'fr-FR 法语（法国）', 'ga-IE 爱尔兰语（爱尔兰）', 'gl-ES 加利西亚语', 'gu-IN 古吉拉特语（印度）', 'he-IL 希伯来语（以色列）', 'hi-IN 印地语（印度）', 
                'hr-HR 克罗地亚语（克罗地亚）', 'hu-HU 匈牙利语(匈牙利)', 'hy-AM 亚美尼亚语（亚美尼亚）', 'id-ID 印度尼西亚语(印度尼西亚)', 'is-IS 冰岛语(冰岛)', 'it-CH 意大利语（瑞士）', 'it-IT 意大利语（意大利）', 
                'ja-JP 日语（日本）', 'jv-ID 爪哇语(拉丁语、印度尼西亚)', 'ka-GE 格鲁吉亚语（格鲁吉亚）', 'kk-KZ 哈萨克语（哈萨克斯坦）', 'km-KH 高棉语(柬埔寨)', 'kn-IN 卡纳达语（印度）', 'ko-KR 韩语(韩国)', 'lo-LA 老挝语(老挝)', 
                'lt-LT 立陶宛语(立陶宛)', 'lv-LV 拉脱维亚语(拉脱维亚)', 'mk-MK 马其顿语（北马其顿）', 'ml-IN 马拉雅拉姆语（印度）', 'mn-MN 蒙古语（蒙古）', 'mr-IN 马拉地语（印度）', 'ms-MY 马来语（马来西亚）', 
                'mt-MT 马耳他语（马耳他）', 'my-MM 缅甸语(缅甸)', 'nb-NO 书面挪威语（挪威）', 'ne-NP 尼泊尔语（尼泊尔）', 'nl-BE 荷兰语（比利时）', 'nl-NL 荷兰语（荷兰）', 'pa-IN 旁遮普语(印度)', 'pl-PL 波兰语（波兰）', 
                'ps-AF 普什图语（阿富汗）', 'pt-BR 葡萄牙语（巴西）', 'pt-PT 葡萄牙语(葡萄牙)', 'ro-RO 罗马尼亚语（罗马尼亚）', 'ru-RU 俄语（俄罗斯）', 'si-LK 僧伽罗语(斯里兰卡)', 'sk-SK 斯洛伐克语（斯洛伐克）', 
                'sl-SI 斯洛文尼亚语(斯洛文尼亚)', 'so-SO 索马里语（索马里）', 'sq-AL 阿尔巴尼亚语（阿尔巴尼亚）', 'sr-RS 塞尔维亚语(西里尔文，塞尔维亚)', 'sv-SE 瑞典语（瑞典）', 'sw-KE 斯瓦希里语（肯尼亚）', 
                'sw-TZ 斯瓦希里语（坦桑尼亚）', 'ta-IN 泰米尔语（印度）', 'te-IN 泰卢固语（印度）', 'th-TH 泰语（泰国）', 'tr-TR 土耳其语 (Türkiye)', 'uk-UA 乌克兰语(乌克兰)', 'ur-IN 乌尔都语（印度）', 
                'uz-UZ 乌兹别克语(拉丁语，乌兹别克斯坦)', 'vi-VN 越南语(越南)', 'wuu-CN 中文（吴语，简体）', 'yue-CN 中文（粤语，简体）', 'zh-CN 中文（普通话，简体）', 'zh-CN-shandong 中文（冀鲁官话，简体）', 
                'zh-CN-sichuan 中文（西南普通话，简体）', 'zh-HK 中文（粤语，繁体）', 'zh-TW 中文（台湾普通话，繁体）', 'zu-ZA 祖鲁语（南非）'
            ],

            'convert_to_EN':  [
                'af-ZA Afrikaans (South Africa)', 'am-ET Amharic (Ethiopia)', 'ar-AE Arabic (United Arab Emirates)', 'ar-BH Arabic (Bahrain)', 'ar-DZ Arabic (Algeria)', 'ar-EG Arabic (Egypt)', 'ar-IL Arabic (Israel)', 
                'ar-IQ Arabic (Iraq)', 'ar-JO Arabic (Jordan)', 'ar-KW Arabic (Kuwait)', 'ar-LB Arabic (Lebanon)', 'ar-LY Arabic (Libya)', 'ar-MA Arabic (Morocco)', 'ar-OM Arabic (Oman)', 
                'ar-PS Arabic (Palestinian National Authority)', 'ar-QA Arabic (Qatar)', 'ar-SA Arabic (Saudi Arabia)', 'ar-SY Arabic (Syria)', 'ar-TN Arabic (Tunisia)', 'ar-YE Arabic (Yemen)', 
                'az-AZ Azerbaijani (Latin, Azerbaijan)', 'bg-BG Bulgarian (Bulgaria)', 'bn-IN Bengali (India)', 'bs-BA Bosnian (Bosnia and Herzegovina)', 'ca-ES Catalan', 'cs-CZ Czech (Czech)', 
                'cy-GB Welsh (United Kingdom)', 'da-DK Danish (Denmark)', 'de-AT German (Austria)', 'de-CH German (Switzerland)', 'de-DE German (Germany)', 'el-GR Greek (Greece)', 'en-AU English (Australia)', 
                'en-CA English (Canada)', 'en-GB English (UK)', 'en-GH English (Ghana)', 'en-HK English (Hong Kong SAR)', 'en-IE English (Ireland)', 'en-IN English (India)', 'en-KE English (Kenya)', 
                'en-NG English (Nigeria)', 'en-NZ English (New Zealand)', 'en-PH English (Philippines)', 'en-SG English (Singapore)', 'en-TZ English (Tanzania)', 'en-US English (United States)', 
                'en-ZA English (South Africa)', 'es-AR Spanish (Argentina)', 'es-BO Spanish (Bolivia)', 'es-CL Spanish (Chile)', 'es-CO Spanish (Colombia)', 'es-CR Spanish (Costa Rica)', 'es-CU Spanish (Cuba)', 
                'es-DO Spanish (Dominican Republic)', 'es-EC Spanish (Ecuador)', 'es-ES Spanish (Spain)', 'es-GQ Spanish (Equatorial Guinea)', 'es-GT Spanish (Guatemala)', 'es-HN Spanish (Honduras)', 
                'es-MX Spanish (Mexico)', 'es-NI Spain (Nicaragua)', 'es-PA Spanish (Panama)', 'es-PE Spanish (Peru)', 'es-PR Spanish (Puerto Rico)', 'es-PY Spanish (Paraguay)', 'es-SV Spanish (El Salvador)', 
                'es-US Spanish (United States)', 'es-UY Spanish (Uruguay)', 'es-VE Spanish (Venezuela)', 'et-EE Estonian (Estonia)', 'eu-ES Basque', 'fa-IR Persian (Iran)', 'fi-FI Finnish (Finland)', 
                'fil-PH Filipino (Philippines)', 'fr-BE French (Belgium)', 'fr-CA French (Canada)', 'fr-CH French (Switzerland)', 'fr-FR French (France)', 'ga-IE Irish (Ireland)', 'gl-ES Galician', 
                'gu-IN Gujarati (India)', 'he-IL Hebrew (Israel)', 'hi-IN Hindi (India)', 'hr-HR Croatian (Croatia)', 'hu-HU Hungarian (Hungary)', 'hy-AM Armenian (Armenia)', 'id-ID Indonesian (Indonesia)', 
                'is-IS Icelandic (Iceland)', 'it-CH Italian (Switzerland)', 'it-IT Italian (Italy)', 'ja-JP Japanese (Japan)', 'jv-ID Javanese (Latin, Indonesia)', 'ka-GE Georgian (Georgia)', 
                'kk-KZ Kazakh (Kazakhstan)', 'km-KH Khmer (Cambodia)', 'kn-IN Kannada (India)', 'ko-KR Korean (Korea)', 'lo-LA Lao (Laos)', 'lt-LT Lithuanian (Lithuania)', 'lv-LV Latvian (Latvia)', 
                'mk-MK Macedonian (North Macedonia)', 'ml-IN Malayalam (India)', 'mn-MN Mongolian (Mongolia)', 'mr-IN Marathi (India)', 'ms-MY Malay (Malaysia)', 'mt-MT Maltese (Malta)', 'my-MM Burmese (Myanmar)', 
                'nb-NO Written Norwegian (Norway)', 'ne-NP Nepali (Nepal)', 'nl-BE Dutch (Belgium)', 'nl-NL Dutch (Netherlands)', 'pa-IN Punjabi (India)', 'pl-PL Polish (Poland)', 'ps-AF Pashto (Afghanistan)', 
                'pt-BR Portuguese (Brazil)', 'pt-PT Portuguese (Portugal)', 'ro-RO Romanian (Romania)', 'ru-RU Russian (Russia)', 'si-LK Sinhala (Sri Lanka)', 'sk-SK Slovak (Slovakia)', 'sl-SI Slovenian (Slovenia)', 
                'so-SO Somali (Somalia)', 'sq-AL Albanian (Albania)', 'sr-RS Serbian (Cyrillic, Serbia)', 'sv-SE Swedish (Sweden)', 'sw-KE Kiswahili (Kenya)', 'sw-TZ Kiswahili (Tanzania)', 
                'ta-IN Tamil (India)', 'te-IN Telugu (India)', 'th-TH Thai (Thailand)', 'tr-TR Turkish (Türkiye)', 'uk-UA Ukrainian (Ukraine)', 'ur-IN Urdu (India)', 'uz-UZ Uzbek (Latin, Uzbekistan)', 
                'vi-VN Vietnamese (Vietnam)', 'wuu-CN Chinese (Wu, Simplified)', 'yue-CN Chinese (Cantonese, Simplified)', 'zh-CN Chinese (Mandarin, Simplified)', 
                'zh-CN-shandong Chinese (Jilu official dialect, Simplified)', 'zh-CN-sichuan Chinese (Southwest Mandarin, Simplified)', 'zh-HK Chinese (Cantonese, Traditional)', 
                'zh-TW Chinese (Taiwanese Mandarin, Traditional)', 'zu-ZA Zulu (South Africa)'          
            ],

            'translate_to':[
                'af 南非荷兰语', 'am 阿姆哈拉语', 'ar 阿拉伯语', 'as 阿萨姆语', 'az 阿塞拜疆语(拉丁语)', 'ba 巴什基尔语', 'bg 保加利亚语', 'bn Bangla', 'bo 藏语', 'bs 波斯尼亚语(拉丁语系)', 'ca 加泰罗尼亚语', 'cs 捷克语', 
                'cy 威尔士语', 'da 丹麦语', 'de 德语', 'dsb 下索布语', 'dv 马尔代夫语', 'el 希腊语', 'en 英语', 'es 西班牙语', 'et 爱沙尼亚语', 'eu 巴斯克语', 'fa 波斯语', 'fi 芬兰语', 'fil 菲律宾语', 'fj 斐济语', 
                'fo 法罗语', 'fr 法语', 'fr-ca 法语（加拿大）', 'ga 爱尔兰语', 'gl 加利西亚语', 'gom 孔卡尼语', 'gu 古吉拉特语', 'ha 豪萨语', 'he 希伯来语', 'hi Hindi', 'hr 克罗地亚语', 'hsb 上索布语', 'ht 海地克里奥尔语', 
                'hu 匈牙利语', 'hy 亚美尼亚语', 'id 印度尼西亚语', 'ig 伊博语', 'ikt 因纽纳敦语', 'is 冰岛语', 'it 意大利语', 'iu 因纽特语', 'iu-Latn 因纽特语(拉丁语)', 'ja 日语', 'ka 格鲁吉亚语', 'kk 哈萨克语', 'km 高棉语', 
                'kmr 库尔德语(北部)', 'kn 卡纳达语', 'ko 朝鲜语', 'ku 库尔德语(中部)', 'ky 吉尔吉斯语(西里尔语)', 'ln 林加拉语', 'lo 老挝语', 'lt 立陶宛语', 'lug 卢干达语', 'lv 拉脱维亚语', 'lzh 中文（文学）', 'mai 迈蒂利语', 
                'mg 马达加斯加语', 'mi 毛利语', 'mk 马其顿语', 'ml 马拉雅拉姆语', 'mn-Cyrl 蒙古语(西里尔文)', 'mn-Mong 蒙古语(传统)', 'mr 马拉地语', 'ms 马来语(拉丁语系)', 'mt 马耳他语', 'mww 白苗语（拉丁语）', 'my 缅甸', 
                'nb 挪威语', 'ne 尼泊尔语', 'nl 荷兰语', 'nso 北索托语', 'nya 尼昂加语', 'or 奥里亚语', 'otq 克雷塔罗奥托米语', 'pa 旁遮普语', 'pl 波兰语', 'prs 达里语', 'ps 普什图语', 'pt 葡萄牙语（巴西）', 
                'pt-pt 葡萄牙语(葡萄牙)', 'ro 罗马尼亚语', 'ru 俄语', 'run 隆迪语', 'rw 卢旺达语', 'sd 信德语', 'si 僧伽罗语', 'sk 斯洛伐克语', 'sl 斯洛文尼亚语', 'sm 萨摩亚语(拉丁语)', 'sn 绍纳语', 'so 索马里语（阿拉伯语）', 
                'sq 阿尔巴尼亚语', 'sr-Cyrl 塞尔维亚语（西里尔）', 'sr-Latn 塞尔维亚语（拉丁）', 'st 南索托语', 'sv 瑞典语', 'sw 斯瓦希里语（拉丁语）', 'ta 泰米尔语', 'te 泰卢固语', 'th 泰语', 'ti 提格里尼亚语', 
                'tk 土库曼语(拉丁语)', 'tlh-Latn 克林贡语', 'tlh-Piqd 克林贡语(plqaD)', 'tn 茨瓦纳语', 'to 汤加语', 'tr 土耳其语', 'tt 鞑靼语（拉丁语）', 'ty 塔希提语', 'ug 维吾尔语（阿拉伯语）', 'uk 乌克兰语', 
                'ur 乌尔都语', 'uz 乌兹别克语(拉丁文)', 'vi 越南语', 'xh 班图语', 'yo 约鲁巴语', 'yua 尤卡坦玛雅语', 'yue 粤语(繁体)', 'zh-Hans 简体中文', 'zh-Hant 中文(繁体)', 'zu 祖鲁语'
            ],

            'translate_to_EN': [
                'af Afrikaans', 'am Amharic', 'ar Arabic', 'as Assamese', 'az Azerbaijani (Latin)', 'ba Bashkir', 'bg Bulgarian', 'bn Bangla', 'bo Tibetan', 'bs Bosnian (Latin)', 'ca Catalan', 'cs Czech', 
                'cy Welsh', 'da Danish', 'de German', 'dsb Lower Sorbian language', 'dv Maldivian', 'el Greek', 'en English', 'es Spanish', 'et Estonian', 'eu Basque', 'fa Persian', 'fi Finnish', 'fil Filipino', 
                'fj Fijian', 'fo Faroese', 'fr French', 'fr-ca French (Canada)', 'ga Irish', 'gl Galician', 'gom Konkani', 'gu Gujarati', 'ha Hausa', 'he Hebrew', 'hi Hindi', 'hr Croatian', 'hsb Upper Sorbian', 
                'ht Haitian Creole', 'hu Hungarian', 'hy Armenian', 'id Indonesian', 'ig Igbo', 'ikt Inunaten', 'is Icelandic', 'it Italian', 'iu Inuktitut', 'iu-Latn Inuktitut (Latin)', 'ja Japanese', 'ka Georgian', 
                'kk Kazakh', 'km Khmer', 'kmr Kurdish (North)', 'kn Kannada', 'ko Korean', 'ku Kurdish (Central)', 'ky Kyrgyz (Cyrillic)', 'ln Lingala', 'lo Lao', 'lt Lithuanian', 'lug Luganda language', 
                'lv Latvian', 'lzh Chinese (Literature)', 'mai Maithili', 'mg Malagasy', 'mi Māori', 'mk FYRO Macedonian', 'ml Malayalam', 'mn-Cyrl Mongolian (Cyrillic)', 'mn-Mong Mongolian (Traditional)', 
                'mr Marathi', 'ms Malay (Latin)', 'mt Maltese', 'mww Bai Hmong (Latin)', 'my Myanmar', 'nb Norwegian', 'ne Nepali', 'nl Dutch', 'nso Northern Sotho', 'nya Nyanja', 'or Oriya', 'otq Querétaro Otomi', 
                'pa Punjabi', 'pl Polish', 'prs Dari language', 'ps Pashto', 'pt Portuguese (Brazil)', 'pt-pt Portuguese (Portugal)', 'ro Romanian', 'ru Russian', 'run Lund language', 'rw Kinyarwanda', 
                'sd Sindhi', 'si Sinhalese', 'sk Slovak', 'sl Slovenian', 'sm Samoan (Latin)', 'sn Shona', 'so Somali (Arabic)', 'sq Albanian', 'sr-Cyrl Serbian (Cyrillic)', 'sr-Latn Serbian (Latin)', 
                'st Southern Sotho', 'sv Swedish', 'sw Swahili (Latin)', 'ta Tamil', 'te Telugu', 'th Thai', 'ti Tigrinian', 'tk Turkmen (Latin)', 'tlh-Latn Klingon', 'tlh-Piqd Klingon (plqaD)', 'tn Tswana', 
                'to Tongan', 'tr Turkish', 'tt Tatar (Latin)', 'ty Tahitian', 'ug Uyghur (Arabic)', 'uk Ukrainian', 'ur Urdu', 'uz Uzbek (Latin)', 'vi Vietnamese', 'xh Xhosa', 'yo Yoruba', 'yua Yucatan Mayan', 
                'yue Cantonese (Traditional)', 'zh-Hans Chinese Simplified', 'zh-Hant Chinese (Traditional)', 'zu Zulu'
            ]
        },

        '2-':{
            'convert_to':  [],
            'translate_to':[]
        },         
    }

    if get3list:
        if WindXX['UI_LANG_SEL'] == "EN" and avl['3'].__contains__('convert_to_EN'):
            return avl['3']['translate_to_EN']
        else:
            return avl['3']['translate_to']
    
    if ce[0] and avl.__contains__(ce[0]):
        if WindXX['UI_LANG_SEL'] == "EN" and avl[ce[0]].__contains__('convert_to_EN'):
            avl[ce[0]]['convert_to']   = avl[ce[0]]['convert_to_EN']
            avl[ce[0]]['translate_to'] = avl[ce[0]]['translate_to_EN']

        listx={
            'convert_to': [],
            'translate_to': []
        }
        if len(selected_langs):
            for tp in ['convert_to', 'translate_to']:
                for ct in avl[ce[0]][tp]:
                    ischecked = False
                    for lx in selected_langs:
                        if re.match(r'^{}(\-|\s+)'.format(lx), ct, re.I):
                            ischecked = True                                
                            break
                    if ischecked:
                        listx[tp].append(ct)            
        else:
            listx['convert_to']   = avl[ce[0]]['convert_to']
            listx['translate_to'] = avl[ce[0]]['translate_to']            

        WindX['b_ui_convert_to_language']["values"] = listx['convert_to']
        WindXX['WatchingOptions_Vars']['convert_to_language'].set(listx['convert_to'][0])
        WindX['b_ui_translate_to']["values"] = listx['translate_to']
        WindXX['WatchingOptions_Vars']['translate_to'].set(listx['translate_to'][0])

        UI_Last_ConvertTranslateLang(WindX['last_ss_values'], ce[0])
    else:
        WindX['b_ui_convert_to_language']["values"] = []
        WindXX['WatchingOptions_Vars']['convert_to_language'].set("")
        WindX['b_ui_translate_to']["values"] = []
        WindXX['WatchingOptions_Vars']['translate_to'].set("") 

def UI_Last_ConvertTranslateLang(ss_values, CE0):
    print(WindX['last_ss_values'], CE0)
    if not ss_values.__contains__(CE0):
        return

    if ss_values[CE0]['convert_to_language']:
        WindXX['WatchingOptions_Vars']['convert_to_language'].set(ss_values[CE0]['convert_to_language'])
    if ss_values[CE0]['translate_to']:
        WindXX['WatchingOptions_Vars']['translate_to'].set(ss_values[CE0]['translate_to'])
    
    WindX['last_ss_values'] = ss_values

def UI_LanguageChange(ev=None):
    tolange = WindXX['WatchingOptions_Vars']['ui_language'].get()
    #print(sys._getframe().f_lineno,ev, tolange, __file__)
    vals = UT_JsonFileRead(filepath= WindX['app_watching_options_file'])
    go = True
    if vals and vals.__contains__('custom') and vals["custom"].__contains__('ui_language'):
        if vals["custom"]['ui_language'] == tolange:
            go = False
    if not go:
        return
    
    go = messagebox.askyesno(GUI_LANG(49) +" [" + tolange + "]", GUI_LANG(50) + " [" + tolange + "], " +  GUI_LANG(51))
    if not go:
        WindXX['WatchingOptions_Vars']['ui_language'].set(vals["custom"]['ui_language'])
        return
    
    vals["custom"]['ui_language'] = tolange
    print("\n#AR", sys._getframe().f_lineno,"Saved to:", WindX['app_watching_options_file'])
    UT_JsonFileSave(WindX['app_watching_options_file'], fdata=vals)
    
    print(sys._getframe().f_lineno,"\n" +  GUI_LANG(52))
    p = Process(target=OpenNew,args=(__file__, []))
    p.start()
    WindExit()

def UI_EncryptCode_Check():
    WindX['EncryptCode_current'] = re.sub(r'\s+', '', WindXX['EncryptCode'].get())
    if not len(WindX['EncryptCode_current']):
        WindX['e_EncryptCode'].config(bg='yellow')
        messagebox.showwarning(title=GUI_LANG(70), message= GUI_LANG(85))
        return False
    
    #verify input code
    vals = UT_JsonFileRead(filepath= WindX['app_watching_options_file'])
    if vals and vals.__contains__('custom') and WindX['EncryptCode_current']:
        if vals['custom'].__contains__('EncryptCode_MD5_VerifyCode') and vals['custom']['EncryptCode_MD5_VerifyCode']:
            tmp_str = UT_CryptMe(vals['custom']['EncryptCode_MD5_VerifyCode'].encode(),key=UT_GetMD5(WindX['EncryptCode_current']), isEncript=False)
            print(sys._getframe().f_lineno, "VerifyCode:", tmp_str)
            if not tmp_str:
                go = messagebox.askyesno(title=GUI_LANG(70), message= GUI_LANG(87))
                if go:
                    #check encrypted field values
                    errors = []
                    if vals and vals.__contains__('custom'):
                        for s in WindXX['WatchingOptions_Vars'].keys():            
                            if vals['custom'].__contains__(s) and len(str(vals['custom'][s])):
                                val_e = str(vals['custom'][s])
                                if WindX['EncryptCode_current'] and val_e and re.match(r"^\$\$", val_e) and WindXX['WatchingOptions_opts'].__contains__(s) and WindXX['WatchingOptions_opts'][s][-1] == 'encrypt': 
                                    val_e = re.sub(r"^\$\$", '', val_e)                    
                                    val_e = UT_CryptMe(val_e.encode(),key=UT_GetMD5(WindX['EncryptCode_current']), isEncript=False)
                                    print(sys._getframe().f_lineno,s, val_e)
                                    if not val_e:
                                        errors.append(str(len(errors)+1) + ". " + GUI_LANG(88) + " [" + str(WindXX['WatchingOptions_opts'][s][2]) + "]: " + str(vals['custom'][s]))

                    if len(errors):
                        messagebox.showwarning(title=GUI_LANG(70), message= "\n\n".join(errors) + "\n\n" + GUI_LANG(89))
                        return False
                    
                    print(sys._getframe().f_lineno,GUI_LANG(87), ": Yes, go!")
                else:         
                    WindX['EncryptCode_current'] = ""
                    return False

    WindX['e_EncryptCode'].config(bg='white')
    
    return True

def UI_Socket_Message(msg):
    print(sys._getframe().f_lineno,"sending via socket ... ...")
    try:
        proc = socket.socket()
        proc.connect(('127.0.0.1', 8181))
        proc.send(msg.encode(encoding='UTF-8',errors='ignore')) 
        rdata = proc.recv(1024).decode()
        print(sys._getframe().f_lineno, "received reply:", rdata)
        proc.close()
    except:
        print(sys._getframe().f_lineno, traceback.format_exc())

def AudioPageChange(step=0):
    t = WindX['b_AudioPageStatus'].config('text')
    tt = re.split(r'[^\d]+', re.sub(r'^.*Page\s+', '', str(t), re.I))
    if len(tt) < 2:
        return
    cur_page = int(tt[0])
    total_pages = int(tt[1])

    to_page = cur_page
    if step == -1000:
        to_page = 1
    elif step == 1000:
        to_page = total_pages
    else:
        to_page = cur_page + step
    if to_page < 1:
        to_page = 1
    elif to_page > total_pages:
        to_page = total_pages

    if to_page == cur_page:
        return
    
    print(sys._getframe().f_lineno,"AudioPageChange step=", step, "; go to page=", to_page, ", cur_page=",cur_page, ", total_pages=",total_pages)

    WindX['b_AudioPageStatus'].config(text=" Page "+ str(to_page) +"/"+ str(total_pages) +" ("+ tt[2] +")")
    WindX['main'].update()

    r = recordAudio(go_to_page=True)
    r.audio_go_to_page(to_page)

def AudioConvertorEnd(force=False):
    if (not force) and (not re.match(r'.*\.py$', WindX['self_sys_argv0'], re.I)):
        return
        #do only when run in python

    print("\n", sys._getframe().f_lineno, GUI_LANG(53))
    UI_AT_Close("AR")

def AudioConvertorStart(to_language, convert_engine):
    AudioConvertorEnd()
    print("\n--------------------------------\n",sys._getframe().f_lineno, GUI_LANG(55))    
    
    xfile = "AudioTranslatorConvertor.py"
    if os.path.exists(WindX['self_folder'] + "/AudioTranslatorConvertor.exe") and re.match(r'.*\.exe$', WindX['self_sys_argv0'], re.I):
        xfile = "AudioTranslatorConvertor.exe"

    print(sys._getframe().f_lineno,
          "\nAudioConvertorStart:",  
          WindX['self_folder'] + '/' + xfile, 
          re.sub(r'\s+', '___', str(to_language)), 
          WindX['audio_file_format'], 
          str(convert_engine),
          re.sub(r'\w', '*', WindX['EncryptCode_current']),
          "\n--------------------------------\n"
        )
    os.chdir(WindX['self_folder'])
    
    if re.match(r'.*\.py$', WindX['self_sys_argv0'], re.I):
        #!!! this function Process(...) can not work with .exe format in Windows !!!
        try:
            p = Process(
                target=OpenNew,
                args=(xfile, 
                    re.sub(r'\s+', '___', str(to_language)),
                    WindX['audio_file_format'], 
                    str(convert_engine), 
                    WindX['EncryptCode_current']
                    )
                )
            p.start()
        except:
            print(sys._getframe().f_lineno,traceback.format_exc())
    else:
        #use socket
        #check if AudioTranslatorConvertor is running
        IsACon = False  
        reply_ok = True    
        while not IsACon:            
            for winx in pygetwindow.getAllWindows():
                #<Win32Window left="-7", top="-7", width="2575", height="1407", title="tmp6.py - Visual Studio Code [Administrator]">
                if winx.title and re.match(r'.*AT\-Convertor\s+\d+\.*\d*', str(winx.title), re.I):
                    IsACon = True
                    break

            if not IsACon:
                reply_ok = messagebox.askokcancel(title = GUI_LANG(70), message= GUI_LANG(117) + " " + WindX['self_folder'] + "\n\n" + GUI_LANG(118))
                if not reply_ok:
                    break
        
        if reply_ok:
            UI_Socket_Message(", ".join([re.sub(r'\s+', '___', str(to_language)), WindX['audio_file_format'], str(convert_engine), WindX['EncryptCode_current']]))

        print("")
    
def AudioAccountOptions(event=None):
    if WindX['AudioAccountOptions_show']:
        WindX['AudioAccountOptions_show'] = False
        WindX['b_AudioAccountOptions'].config(text= "4. " + GUI_LANG(99) + ' ⋁')
        WindX['Frame113'].grid_remove()
    else:
        WindX['AudioAccountOptions_show'] = True
        WindX['b_AudioAccountOptions'].config(text= "4. " + GUI_LANG(99) + ' ⋀')
        WindX['Frame113'].grid()

def AudioWatchingOptions(event=None):
    if WindX['AudioWatchingOptions_show']:
        WindX['AudioWatchingOptions_show'] = False
        WindX['b_AudioWatchingOptions'].config(text= "3. " + GUI_LANG(75) + ' ⋁')
        WindX['Frame112'].grid_remove()
    else:
        WindX['AudioWatchingOptions_show'] = True
        WindX['b_AudioWatchingOptions'].config(text= "3. " + GUI_LANG(75) + ' ⋀')
        WindX['Frame112'].grid()

def AudioRecordOptions(event=None):
    if WindX['AudioRecordOptions_show']:
        WindX['AudioRecordOptions_show'] = False
        WindX['b_AudioRecordOptions'].config(text='⋁')
        WindX['Frame11'].grid_remove()
    else:
        WindX['AudioRecordOptions_show'] = True
        WindX['b_AudioRecordOptions'].config(text='⋀')
        WindX['Frame11'].grid()

def AudioRecordLoadHistory(event=None):
    #fpath = filedialog.askdirectory(initialdir = WindX['app_outfolder_recorders'])
    #if fpath:
    #    print(sys._getframe().f_lineno,"\nAudioRecordLoadHistory:", re.sub(r'\\','/',fpath))
    if not UI_EncryptCode_Check():
        return
    
    filepath = filedialog.askopenfilename(
                filetypes= [('audio_info', '.jsonx')], 
                defaultextension='.jsonx',
                initialdir= WindX['app_outfolder_recorders'],
                title= GUI_LANG(56) + " - audio_info.jsonx"
                )
    if filepath:
        print(sys._getframe().f_lineno,"\nAudioRecordLoadHistory:", re.sub(r'\\','/',filepath))
        filename = str(os.path.basename(filepath)).lower()
        if not filename == 'audio_info.jsonx':
            print(sys._getframe().f_lineno,"\n" + GUI_LANG(57))
            messagebox.showwarning(title=GUI_LANG(70), message= GUI_LANG(58))
            return
        
        r = recordAudio(load_history=True, history_file= filepath)
        r.audio_load_history()


def AudioRecordPause(event=None):
    if WindX['AudioRecordPause_Yes']:
        WindX['AudioRecordPause_Yes'] = False
        WindX['b_AudioRecordPause'].config(text='||')
        WindX['audio_play_Go_working'].pop(0)
    else:
        WindX['AudioRecordPause_Yes'] = True
        WindX['b_AudioRecordPause'].config(text='▶')
        WindX['audio_play_Go_working'].append(1) 

        t = threading.Timer(0.1, AudioButton_Highlight, args=['AudioRecordPause_Yes', WindX['b_AudioRecordPause'], 360, WindX['win_main_background']])
        t.start()

def AudioButton_Highlight(ikeyTrue, bttn, nc, obg):
    colors = UT_GetColors(n=nc)
    i = 0
    while WindX[ikeyTrue]:
        if ikeyTrue == 'b_AudioRecord_action' and WindX['AudioRecordPause_Yes']:
            bttn.config(fg="#FFFFFF", bg=obg)
        else:
            try:
                bttn.config(fg=colors[i], bg='#000000')
            except:
                pass
            i +=1
            if i >= nc:
                i = 0

        time.sleep(0.5)
    
    bttn.config(fg="#FFFFFF", bg=obg)

def AudioRecord(event=None):
    if WindX['b_AudioRecord_action']:
        for r in WindX['b_AudioDeviceTests'].keys():
            WindX['b_AudioDeviceTests'][r].config(state='normal')

        WindX['b_AudioRecordLoad'].config(state='normal')
        WindX['b_AudioFirstPage'].config(state='normal')
        WindX['b_AudioPreviousPage'].config(state='normal')
        WindX['b_AudioNextPage'].config(state='normal')
        WindX['b_AudioLastPage'].config(state='normal')
        WindX['b_ui_language'].config(state='readonly')

        WindX['b_AudioRecord_action'] = False        
        WindX['b_AudioRecord'].config(text= GUI_LANG(40), fg="#FFFFFF", bg=WindX['win_main_background'])
        #UI_WidgetBalloon(WindX['b_AudioRecord'], GUI_LANG(59))

        WindX['AudioRecordPause_Yes'] = False
        WindX['b_AudioRecordPause'].config(text='||', fg="#FFFFFF", bg=WindX['win_main_background'])
        
        for s in WindXX['AudioDevicesSelected'].keys():
            WindX['b_AudioDevicesSelected_labels'][s].configure(bg='#EFEFEF')
            WindX['b_AudioDevicesSelected_checkboxes'][s].configure(state='normal')

        os.chdir(WindX['self_folder'])
    else:
        if not UI_EncryptCode_Check():
            return
        
        audio_lang = WindXX['WatchingOptions_Vars']['convert_to_language'].get()
        print(sys._getframe().f_lineno,"\nconvert_engine=", WindXX['WatchingOptions_Vars']['convert_engine'].get(), ", audio_lang=", audio_lang)
        if not audio_lang:
            messagebox.showwarning(title=GUI_LANG(70), message= GUI_LANG(90))
            return

        if WindX['AudioRecordOptions_show']:
            AudioRecordOptions()

        WindX['b_AudioRecordLoad'].config(state='disabled')        
        WindX['b_AudioFirstPage'].config(state='disabled')
        WindX['b_AudioPreviousPage'].config(state='disabled')
        WindX['b_AudioNextPage'].config(state='disabled')
        WindX['b_AudioLastPage'].config(state='disabled')
        WindX['b_ui_language'].config(state='disabled')

        for r in WindX['b_AudioDeviceTests'].keys():
            WindX['b_AudioDeviceTests'][r].config(state='disabled')

        for s in WindXX['AudioDevicesSelected'].keys():
            WindX['b_AudioDevicesSelected_checkboxes'][s].configure(state='disabled')
        
        WindX['b_AudioRecord_action'] = True
        WindX['b_AudioRecord'].config(text= GUI_LANG(60))
        #UI_WidgetBalloon(WindX['b_AudioRecord'], GUI_LANG(60))

        t = threading.Timer(0.1, AudioRecord_timing)
        t.start()

        t = threading.Timer(0.1, AudioButton_Highlight, args=['b_AudioRecord_action', WindX['b_AudioRecord'], 360, WindX['win_main_background']])
        t.start()

        r = recordAudio()
        r.run()

def AudioRecord_timing():
    stime = time.time()
    pstime = 0
    while WindX['b_AudioRecord_action']:
        if WindX['AudioRecordPause_Yes']:
            if not pstime:
                pstime = time.time()
                WindX['b_AudioRecord'].config(text= GUI_LANG(102) + "   " + usedTime(stime))
        else:
            if pstime:
                print("\n", sys._getframe().f_lineno, "pause time=", usedTime(0, time.time() - pstime))
                stime = stime + (time.time() - pstime)
                pstime = 0

            WindX['b_AudioRecord'].config(text= GUI_LANG(60) + "   " + usedTime(stime))
            WindX['main'].update()
        time.sleep(0.5)

    WindX['b_AudioRecord'].config(text= GUI_LANG(40))

def AudioDeviceRefresh(event=None):
    """
    refresh audio devices, and watching option
    """
    
    UI_WinWidgetRemove(wid=WindX['Frame111'])
    WindXX['AudioDevicesSelected'] = {}
    WindX['b_AudioDevicesSelected_labels'] = {}
    WindX['b_AudioDevicesSelected_checkboxes'] = {}
    WindXX['AudioDevicesInfo'] = {}
    WindX['b_AudioDeviceTests'] = {}

    sadevices = ["-1. Refresh Devices"]
    p = pyaudio.PyAudio()    

    default_info = p.get_default_input_device_info()
    print(sys._getframe().f_lineno,GUI_LANG(61), default_info,"\n")

    info = p.get_host_api_info_by_index(0)
    numdevices = info.get('deviceCount')
    print(sys._getframe().f_lineno,GUI_LANG(62), numdevices)

    indexs = []
    row = 1
    for i in range(0, numdevices):
        try:
            print(sys._getframe().f_lineno,GUI_LANG(63) + str(i), p.get_device_info_by_index(i))
            sel_info = p.get_device_info_by_index(i)

            test_ok = False
            try:    
                #test the device                 
                stream = p.open(
                    format  = pyaudio.paInt16,  # 音频流wav格式
                    channels= 2,  # 声道
                    rate    = 16000,  # 采样率
                    input   =True,
                    frames_per_buffer= 1024,
                    input_device_index= sel_info['index'])

                stream.stop_stream()  # 停止数据流
                stream.close() 
                test_ok = True              
            except:
                print(sys._getframe().f_lineno,traceback.format_exc())

            if test_ok:
                name = str(sel_info['index']) + ". " + p.get_device_info_by_host_api_device_index(0, i).get('name')
                sadevices.append(name)
                print(sys._getframe().f_lineno,'\t#' + str(sel_info['index']), GUI_LANG(64))

                data_index = 'data' + str(sel_info['index'])
                lbl = Label(WindX['Frame111'], text=' ', justify=LEFT, relief=FLAT,pady=3,padx=3, width=3)
                lbl.grid(row=row,column=0,sticky=W)
                WindX['b_AudioDevicesSelected_labels'][data_index] = lbl

                WindXX['AudioDevicesSelected'][data_index] = BooleanVar()
                cb = Checkbutton(WindX['Frame111'], text= name, variable= WindXX['AudioDevicesSelected'][data_index], justify=LEFT, relief=FLAT,pady=3,padx=3)
                cb.grid(row=row,column=1,sticky=W)
                if (sel_info['index'] == default_info['index']) or re.match(r'.*Realtek', name, re.I):
                    cb.select() 
                WindX['b_AudioDevicesSelected_checkboxes'][data_index] = cb
                indexs.append(data_index)

                device_index = sel_info['index']
                Add_Button(row, device_index)

                WindXX['AudioDevicesInfo'][data_index] = sel_info 
                # {'index': 1, 'structVersion': 2, 'name': '麦克风 (Realtek High Definition Au', 'hostApi': 0, 'maxInputChannels': 2, 'maxOutputChannels': 0, 
                # 'defaultLowInputLatency': 0.09, 'defaultLowOutputLatency': 0.09, 'defaultHighInputLatency': 0.18, 'defaultHighOutputLatency': 0.18, 'defaultSampleRate': 44100.0}
                row +=1
        except:
            print(sys._getframe().f_lineno,traceback.format_exc())

    #p.terminate()  # do not close PyAudio here, or cause this app crashing!!!

    if len(indexs) <= 2:
        #print(sys._getframe().f_lineno,'indexs=',indexs)
        for data_index in indexs:
            if not (sel_info['index'] == default_info['index']):
                WindX['b_AudioDevicesSelected_checkboxes'][data_index].select()

    #set custom values
    vals = UT_JsonFileRead(filepath= WindX['app_watching_options_file'])
    #print(sys._getframe().f_lineno,vals)
    print(sys._getframe().f_lineno,GUI_LANG(77))

    ss_values = {
        'convert_to_language': '',
        'translate_to': ''
    }
    if vals and vals.__contains__('custom'):
        for s in WindXX['WatchingOptions_Vars'].keys():            
            if vals['custom'].__contains__(s) and len(str(vals['custom'][s])): # and (vals['custom'][s] != WindXX['WatchingOptions_opts'][s][1]):
                print(sys._getframe().f_lineno,"....", WindXX['WatchingOptions_opts'][s][2] + ":", str(vals['custom'][s]))
                val_e = str(vals['custom'][s])

                if WindX['EncryptCode_current'] and val_e and re.match(r"^\$\$", val_e) and WindXX['WatchingOptions_opts'].__contains__(s) and WindXX['WatchingOptions_opts'][s][-1] == 'encrypt': 
                    val_e = re.sub(r"^\$\$", '', val_e)                    
                    val_e = UT_CryptMe(val_e.encode(),key=UT_GetMD5(WindX['EncryptCode_current']), isEncript=False)
                
                WindXX['WatchingOptions_Vars'][s].set(val_e)
                if s == 'convert_to_language' or s == 'translate_to':
                    ss_values[s] = val_e
    
    UI_ConvertEngineChange()

    ce = re.split(r'\s+', WindXX['WatchingOptions_Vars']['convert_engine'].get())
    CE0 = ce[0]
    if not CE0:
        CE0 = 'NA'
    ss_valuesX = {}
    ss_valuesX[CE0] = ss_values
    UI_Last_ConvertTranslateLang(ss_valuesX, CE0)

def Add_Button(row, device_index):
        b=iButton(WindX['Frame111'], row, 2, lambda:AudioDeviceTest(None, row, device_index),'⫗',fg='blue',bg='#EFEFEF',p=[LEFT,FLAT,3,1,'#FFFF66','#FFFF99',15,E+W+N+S,1,1]) 
        WindX['b_AudioDeviceTests'][row] = b.b
        UI_WidgetBalloon(b.b, GUI_LANG(65) + str(device_index))

def AudioDeviceTest(event=None, row=0, device_index=0):
    print(sys._getframe().f_lineno,"\n" + GUI_LANG(65) + str(device_index))
    #return

    if WindX['b_AudioRecord_action']:
        return
    for r in WindX['b_AudioDeviceTests'].keys():
        WindX['b_AudioDeviceTests'][r].config(state='disabled')

    WindX['b_AudioRecordPause'].config(state='disabled')
    WindX['b_AudioRecord'].config(state='disabled')
    r = recordAudio()
    r.audio_device_test(row, device_index)
    for r in WindX['b_AudioDeviceTests'].keys():
        WindX['b_AudioDeviceTests'][r].config(state='normal', text='⫗')

    WindX['b_AudioRecordPause'].config(state='normal')
    WindX['b_AudioRecord'].config(state='normal')   

def AudioInfoSave_Pre(filepath=""):
    filepathx = filepath
    if not filepathx:
        return
    t1 = threading.Timer(0.1, AudioInfoSave, args=[filepathx])
    t1.start() 

def AudioInfoSave(filepath):
    n = 0
    fdata = {}
    for row in WindX['frame_visualize_all_pages'].keys():
        fdata[row] = {}
        n +=1
        for s in WindX['frame_visualize_all_pages'][row].keys():
            fdata[row][s] = WindX['frame_visualize_all_pages'][row][s]
    
    if n:
        print("\n#AR", sys._getframe().f_lineno, "Saved to:", filepath)
        UT_JsonFileSave(filepath=filepath, fdata=fdata)
    '''
    WindX['frame_visualize_all_pages'][row] = {
        'filepath': "",
        'device': "",
        'record_time': "",
        'total_frames': "",
        'title': "",
        'audio2text': "",
        'translation': ""
    }
    '''

def WindExit():      
    if WindX['b_AudioRecord_action']:
        print("\n", sys._getframe().f_lineno, "ending record ...\n")
        AudioRecord()        
        time.sleep(3)

    #close the convertor
    AudioConvertorEnd(True)

    WindX['main'].destroy()  
    os._exit(0)
    #sys.exit(0)  # This will cause the window error: Python has stopped working ...

def main():
    init()
    GUI()

class recordAudio:
    def __init__(self, load_history=False, history_file='', go_to_page=False):
        timestf = time.strftime("%Y%m%d-%H%M%S",time.localtime(time.time()))
        self.frames_per_buffer = 1024
        self.channels = 1
        self.format = pyaudio.paInt16
        self.rate = 16000
        self.sampwidth = 2
        self.load_history = load_history
        self.go_to_page = go_to_page

        self.audio_threshold = 50
        self.audioop_rms_threshold = 100
        self.audio_frame_rate= 200
        self.break_points = 5
        self.audio_visualization_interval = 5
        self.audio_visualization_signal_enhance = 1.5
        self.convert_to_language = 1537 #1537 普通话(纯中文识别), 1737 英语
        self.convert_engine = int(re.sub(r'[^\d\.]+', '', str(WindXX['WatchingOptions_Vars']['convert_engine'].get())))

        val =  WindXX['WatchingOptions_Vars']['audio_section_max_length'].get()
        val = re.sub(r'[^\d\.]+', '', val)
        if not val:
            val = 25
        self.audio_section_max_length =  int(val)  #seconds - do not allow one audio section too long, because there is a limit for converting audio to text!!!
        if self.convert_engine == '4':
            self.audio_section_max_length = 7200 #2 hours = 2 * 3600

        self.audio_visualization_line_color = re.sub(r'^\s+|\s+$|[^a-z0-9]+', '', WindXX['WatchingOptions_Vars']['audio_visualization_line_color'].get(), re.I)
        if not self.audio_visualization_line_color:
            self.audio_visualization_line_color = 'red'
        
        val = WindXX['WatchingOptions_Vars']['audio_visualization_num_per_page'].get()
        val = re.sub(r'[^\d\.]+', '', val)
        if not val:
            val = 20
        self.audio_visualization_num_per_page = int(val)
        if self.audio_visualization_num_per_page < 5:
            self.audio_visualization_num_per_page = 5
        self.audio_visualization_cur_page_num = 1

        self.device_colors = {}
        self.audio_info_outfile = ""
        self.audio_watching_options_file = ""
        self.audio_watching_options_file_this_record = ""
        self.history_file = ""
        self.outfoldertmp = "" 

        self.PyAudio = None
        if self.load_history or self.go_to_page:
            self.history_file = history_file
            self.outfoldertmp = os.path.dirname(history_file)
        else:
            self.outfoldertmp       = WindX['app_outfolder_recorders'] + "/Audio." + timestf
            self.outfile_audio      = self.outfoldertmp  + "/device"
            self.audio_info_outfile = self.outfoldertmp  + "/audio_info.jsonx"
            self.audio_watching_options_file = WindX['app_watching_options_file']
            self.audio_watching_options_file_this_record = self.outfoldertmp + '/audio_options.json'

            self.PyAudio = pyaudio.PyAudio()  #DO call here for multiple threads!!! 
    
            if not os.path.exists(self.outfoldertmp):  
                os.makedirs(self.outfoldertmp)
            UT_Print2Log('', GUI_LANG(66), self.outfoldertmp)

    def init(self):
        WindX['b_frame1_canvas'].delete('all')
        WindX['audio_play_Go_working_by_row'] = {}
        WindX['frame_visualize_cur_page'] = {}        
        WindX['frame_visualize_cur_page_done'] = {}
        WindX['ClassScrollableFrame_frame_rows'] = -3            
        WindX['SystemAudioDevice_data'] = {}
        WindX['amplitude_to_db_vals'] = {}
        WindX['audio_visualizationGo_PointData'] = {}
        WindX['audio_visualizationGo_x0'] = 0
        WindX['audio_play_Go_working'] = []
        WindX['audio_visualizationGo_canvas_items'] = {}

        UI_WinWidgetRemove(wid=WindX['ClassScrollableFrame'].scrollable_frame)
        #"""
        WindX['main'].update()
        print(sys._getframe().f_lineno,'canvas.bbox("all")=', WindX['ClassScrollableFrame'].canvas.bbox("all"))
        WindX['ClassScrollableFrame'].canvas.configure(scrollregion= WindX['ClassScrollableFrame'].canvas.bbox("all"))
        WindX['ClassScrollableFrame'].canvas.yview_moveto(0.0)
        #"""

        if not self.go_to_page:
            WindX['b_AudioPageStatus'].config(text=" Page 1/1 (0) ")
            WindX['main'].title(GUI_LANG(76)+ " Rev " + WindX['main_rev'])
            WindX['frame_visualize_all_pages'] = {}
            WindX['frame_visualize_all_pages_ui_index'] = 0    

        if WindX['AudioRecordPause_Yes']:
            AudioRecordPause()

        if self.load_history or self.go_to_page:
            self.devices_set_color(ifilter='all')
            return

        vals = {}
        except_ss = [
            'convert_to_language', 
            'channels', 
            'convert_engine', 
            'translate_to', 
            'ui_language',
            'ms_languages_selected',
            'self_root_folder',    
            'audio_visualization_line_color',

            'translate_baidu_app_id',
            'translate_baidu_app_key',

            'translate_azure_app_key',
            'translate_azure_app_region',

            'audio2text_baidu_app_id',
            'audio2text_baidu_api_key',
            'audio2text_baidu_api_secret_key',

            'audio2text_azure_api_speech_key',
            'audio2text_azure_api_speech_region'
        ]
        for s in WindXX['WatchingOptions_Vars'].keys():
            val = WindXX['WatchingOptions_Vars'][s].get()

            if not (s in except_ss):
                val = re.sub(r'[^\d\.]+', '', val)
                if not val:
                    vals[s] = 0
            vals[s] = val

            if WindX['EncryptCode_current'] and val and (not re.match(r"^\$\$", val)) and WindXX['WatchingOptions_opts'].__contains__(s) and WindXX['WatchingOptions_opts'][s][-1] == 'encrypt':
                val_e = re.sub(r'^b(\'|\")|(\'|\")$', '', str(UT_CryptMe(val,key=UT_GetMD5(WindX['EncryptCode_current']), isEncript=True)))
                print(sys._getframe().f_lineno,"\t...", s, ":", val, "-->", val_e, "-->", val_e.encode(),"-->",  UT_CryptMe(val_e.encode(),key=UT_GetMD5(WindX['EncryptCode_current']), isEncript=False))
                vals[s] = "$$" + val_e

        tmp_str = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(60))
        vals['EncryptCode_MD5_VerifyCode'] = re.sub(r'^b(\'|\")|(\'|\")$', '', str(UT_CryptMe(tmp_str, key=UT_GetMD5(WindX['EncryptCode_current']), isEncript=True)))
        print(sys._getframe().f_lineno,"\t... VerifyCode", vals['EncryptCode_MD5_VerifyCode'])

        #selectbox
        self.convert_engine =  int(re.sub(r'[^\d\.]+', '', vals['convert_engine']))
        
        if self.convert_engine == 1:
            self.convert_to_language = int(re.sub(r'[^\d\.]+', '', vals['convert_to_language']))
            #1537 普通话(纯中文识别), 1737 英语
            if not self.convert_to_language in [1537, 1737]:
                self.convert_to_language = 1537
                vals['convert_to_language'] = '1537 - ' + GUI_LANG(2)
        else:
            self.convert_to_language = vals['convert_to_language']

        #selectbox
        self.frames_per_buffer = int(vals['frames_per_buffer'])
        if self.frames_per_buffer < 256:
            self.frames_per_buffer = 256

        #selectbox
        self.channels = int(re.sub(r'[^\d\.]+', '', vals['channels']))  

        #selectbox
        if vals['format'] == 8:
            self.format = pyaudio.paInt8
        elif vals['format'] == 24:
            self.format = pyaudio.paInt24
        elif vals['format'] == 32:
            self.format = pyaudio.paInt32
        else:
            self.format = pyaudio.paInt16
            vals['format'] = 16
        
        #selectbox
        self.rate = int(vals['rate'])
        if not self.rate in [8000, 16000, 32000, 48000, 96000]:
            self.rate = 16000
            vals['rate'] = 16000

        self.audio_threshold = int(vals['audio_threshold'])
        if not self.audio_threshold:
            self.audio_threshold = 50
            vals['audio_threshold'] = 50

        self.audio_frame_rate= int(vals['audio_frame_rate'])
        if not self.audio_frame_rate:
            self.audio_frame_rate = 200
            vals['audio_frame_rate'] = 200

        self.break_points = int(vals['break_points'])
        if not self.break_points:
            self.break_points = 5
            vals['break_points'] = 5

        self.audio_visualization_interval = int(vals['audio_visualization_interval'])
        if not self.audio_visualization_interval:
            self.audio_visualization_interval = 5
            vals['audio_visualization_interval'] = 5

        self.audioop_rms_threshold = int(vals['audioop_rms_threshold'])
        if not self.audioop_rms_threshold:
            self.audioop_rms_threshold = 100
            vals['audioop_rms_threshold'] = 100

        self.audio_visualization_signal_enhance = float(vals['audio_visualization_signal_enhance'])
        if self.audio_visualization_signal_enhance < 1:
            self.audio_visualization_signal_enhance = 1
            vals['audio_visualization_signal_enhance'] = 1

        print(sys._getframe().f_lineno,GUI_LANG(67))
        for s in WindXX['WatchingOptions_opts'].keys():
            print(sys._getframe().f_lineno,"\t--",WindXX['WatchingOptions_opts'][s][2], "=", vals[s])
        
        vals['audio_file_format'] = WindX['audio_file_format']

        fdata = {
            'default': WindXX['WatchingOptions_opts'],
            'custom' : vals
        }
        print("\n#AR", sys._getframe().f_lineno,"Saved to:", self.audio_watching_options_file)
        UT_JsonFileSave(self.audio_watching_options_file, fdata=fdata)

        print("\n#AR", sys._getframe().f_lineno,"Saved to:", self.audio_watching_options_file_this_record)
        UT_JsonFileSave(self.audio_watching_options_file_this_record, fdata=fdata)
    
        ce = re.split(r'\s+', WindXX['WatchingOptions_Vars']['convert_engine'].get())
        CE0 = ce[0]
        if not CE0:
            CE0 = 'NA'
        WindX['last_ss_values'][CE0] = {
            'convert_to_language': WindXX['WatchingOptions_Vars']['convert_to_language'].get(),
            'translate_to': WindXX['WatchingOptions_Vars']['translate_to'].get()
        }

    def run(self):
        self.init()

        try:
            delaySeconds = 0.1
            deviceIndexs = self.devices_set_color()

            if len(deviceIndexs):
                if len(deviceIndexs) <=5:
                    threads = [] 
                    for i in range(len(deviceIndexs)):
                        if i > 4:
                            break

                        t = None
                        if i ==0:
                            t = threading.Timer(delaySeconds,self.record_audio, args=[deviceIndexs[i], True])
                        else:
                            t = threading.Timer(delaySeconds,self.record_audio, args=[deviceIndexs[i], False])
                        threads.append(t)
                    
                    if len(threads):
                        t = threading.Timer(delaySeconds,self.audio_conversion_check)
                        threads.append(t)

                        t = threading.Timer(delaySeconds, AudioConvertorStart, args=[self.convert_to_language , self.convert_engine])
                        threads.append(t)
                    
                    for i in range(len(threads)):
                        threads[i].start()

                    #can not lock the threads!!!!!!
                    #for t in range(len(threads)):
                    #    threads[i].join()
                    #self.PyAudio.terminate() 
                else:
                    messagebox.showwarning(title= GUI_LANG(70), message= GUI_LANG(68))
                    AudioRecord()
            else:
                messagebox.showwarning(title= GUI_LANG(70), message= GUI_LANG(69))
                AudioRecord()
        except:
            print(sys._getframe().f_lineno,traceback.format_exc())
            AudioRecord()

    def devices_set_color(self, ifilter='selected'):
        try:
            deviceIndexs = []
            for s in WindXX['AudioDevicesSelected'].keys():
                if ifilter== 'selected':
                    if WindXX['AudioDevicesSelected'][s].get():
                        deviceIndexs.append(int(re.sub(r'data', '', s)))
                        WindX['b_AudioDevicesSelected_labels'][s].configure(bg='#EFEFEF')
                else:
                    deviceIndexs.append(int(re.sub(r'data', '', s)))
                    WindX['b_AudioDevicesSelected_labels'][s].configure(bg='#EFEFEF')                

            self.device_colors = {}
            if len(deviceIndexs) <=5:
                colors = ['#FF0000', '#33CCFF', '#0000FF', '#00FF00', '#009900'] #GetColorsHex(len(deviceIndexs))
                for i in range(len(deviceIndexs)):
                    if i > 4:
                        break
                    self.device_colors['data' + str(deviceIndexs[i])] = colors[i]
                    WindX['b_AudioDevicesSelected_labels']['data' + str(deviceIndexs[i])].configure(bg= colors[i])

            return deviceIndexs
        except:
            print(sys._getframe().f_lineno,traceback.format_exc())

    def is_valid_audio_fragment(self, data, device_index):
        try:
            rms = audioop.rms(data, 2)
            audio_data = np.frombuffer(data, dtype=np.short) #通过frombuffer函数将二进制转换为整型数组，通过其参数dtype指定转换后的数据格式。
            xmax = np.max(np.absolute(audio_data))

            #if device_index == 2:
            #    dbs = amplitude_to_db(audio_data, ref=np.max)
            #    WindX['amplitude_to_db_vals']['data' + str(device_index)].append(int(np.average(dbs)))
            #    print(sys._getframe().f_lineno,str(device_index) + ", audioop.rms=", rms, ', np.max=', xmax, ', db=', int(np.max(dbs)), int(np.min(dbs)), int(np.average(dbs)))

            if  xmax >= self.audio_threshold and rms >= self.audioop_rms_threshold:
                return True
            else:
                return False
        except:
            print(sys._getframe().f_lineno,traceback.format_exc())
            return False
        
    def record_audio(self, device_index = 0, main_thread=False):
        try:
            stime = time.time()
             
            #p = pyaudio.PyAudio()    #DO NOT call here for multiple threads!!! 
            p = self.PyAudio      
            print(sys._getframe().f_lineno,GUI_LANG(71) + str(device_index) + GUI_LANG(72), p.get_device_info_by_index(device_index),"\n")
            
            stream = p.open(
                format  = self.format,  # 音频流wav格式
                channels= self.channels,  # 声道
                rate    = self.rate,  # 采样率
                input   = True,
                frames_per_buffer= self.frames_per_buffer,
                input_device_index= device_index
            )

            data_index = 'data' + str(device_index)
            device_name= 'device-' + str(device_index)
            if WindXX['AudioDevicesInfo'].__contains__(data_index) and WindXX['AudioDevicesInfo'][data_index].__contains__('name') and WindXX['AudioDevicesInfo'][data_index]['name']:
                x = re.sub(r'\s+\(.*$', '', WindXX['AudioDevicesInfo'][data_index]['name'])
                if len(x) >= 2: 
                    device_name = x + '('+str(device_index)+')'
            WindX['amplitude_to_db_vals'][data_index] = []
            WindX['audio_visualizationGo_PointData'][data_index] = []

            self.sampwidth = p.get_sample_size(self.format)
            print("\nformat {}, channels {}, rate {}, frames_per_buffer {}, sampwidth {}".format(self.format, self.channels, self.rate, self.frames_per_buffer, self.sampwidth))

            all_frames = []
            half_second_cycles = int(0.5*(self.rate/self.frames_per_buffer))

            has_signal_k = 0
            while WindX['b_AudioRecord_action']: 
                if len(WindX['audio_play_Go_working']):
                    time.sleep(1/self.audio_frame_rate)
                else:                    
                    if not main_thread:   
                        WindX['SystemAudioDevice_data'][data_index] = [b'', False]
        
                    data = None
                    frames = []  # 录制的音频流                    
                    k = 0
                    thk = 0    #count for valid voice per buffer
                    less = []
                    data_avg  = []

                    audio_last_time = time.time()
                    audio_section_time_break = False
                    while WindX['b_AudioRecord_action']:
                        if len(WindX['audio_play_Go_working']):
                            break
                                
                        data = stream.read(self.frames_per_buffer)              
                        frames.append(data)          
                        #all_frames.append(data)                        
                        data_avg.append(np.average(np.absolute(np.frombuffer(data, dtype=np.short))))
                        voice_valid = self.is_valid_audio_fragment(data, device_index)
                        if voice_valid:
                            less = []
                            thk += 1                               
                        else:
                            less.append(-1)

                        if not main_thread:
                            WindX['SystemAudioDevice_data'][data_index] = [data, voice_valid]

                        #如果有连续x个循环的点，都不是声音信号，就认为音频结束了
                        #If there are x consecutive loops of points, none of which are sound signals, the audio section is considered to be end
                        if len(less) >= self.break_points:  #                         
                            break
                        elif (time.time() - audio_last_time > self.audio_section_max_length): #seconds - do not allow one audio section too long, because there is a limit for converting audio to text!!!
                            audio_section_time_break = True
                            break

                        if (k == self.audio_visualization_interval or k == 0) and main_thread:      
                            k = 0
                            vstime = time.time()

                            #visualize the waveform on the screen
                            t1 = threading.Timer(0.1, self.audio_visualization, args=[data, data_index, voice_valid])
                            t1.start()
                            #print(sys._getframe().f_lineno,'visualization, used time:', int((time.time() - vstime)*10000)/10, 'ms')
                        k +=1
                    
                    #print(sys._getframe().f_lineno,'thk=', thk)
                    #if thk > half_second_cycles: #not use this condition, or will lose some audio sections!!!!!
                    if thk > self.break_points or audio_section_time_break:
                        davg = int(np.average(data_avg))
                        if davg >= self.audio_threshold:
                            #xstime = time.time()
                            has_signal_k += 1
                            #print(sys._getframe().f_lineno,'default data_avg=', np.average(data_avg))
                            outf = self.outfile_audio + '-' + str(device_index) + '_' + str(time.time()) + '.' + WindX['audio_file_format']
                            self.audio_save_to_file(outf, frames)
                            self.audio_add_ui(device_name, outf, frames, davg)

                            AudioInfoSave_Pre(self.audio_info_outfile)                                               
                            #print(sys._getframe().f_lineno,'save section, used time:', int((time.time() - xstime)*10000)/10 + 'ms')

            # 录制完成
            stream.stop_stream()
            stream.close()
            #p.terminate()   #DO NOT call here for multiple threads!!! 

            if has_signal_k and len(all_frames):
                self.audio_save_to_file(self.outfile_audio + '-' + str(device_index) + '_00all.' + WindX['audio_file_format'], all_frames, toprint=True)

                if main_thread:
                    AudioInfoSave_Pre(self.audio_info_outfile)
        except:
            print(sys._getframe().f_lineno,GUI_LANG(71) + str(device_index) + GUI_LANG(72), p.get_device_info_by_index(device_index),"\n")
            print(sys._getframe().f_lineno,traceback.format_exc())

    def audio_save_to_file(self, outf, frames, toprint=False):
        if len(frames):
            try:
                wf = wave.open(outf, 'wb')
                wf.setnchannels(self.channels)
                wf.setsampwidth(self.sampwidth)
                wf.setframerate(self.rate)
                wf.writeframes(b''.join(frames))
                wf.close()

                if toprint:
                    print(sys._getframe().f_lineno,GUI_LANG(73), outf)
            except:
                print(sys._getframe().f_lineno,traceback.format_exc())

    def audio_visualization(self, data, data_index, isValid=True, isTest=False):              
        rectFram = UI_WidgetRectGET(WindX['b_frame1_canvas'])
        w = rectFram[2] - rectFram[0]
        h = rectFram[3] - rectFram[1]
        
        increasing=True
        r1 = 0
        r2 = 0
        if w:
            WindX['audio_visualizationGo_canvas_items'][WindX['audio_visualizationGo_x0']] = []

            #block = 20  #block number
            wblock = 10 #w / block

            icolor = 'red'           
            if self.device_colors.__contains__(data_index):
                icolor = self.device_colors[data_index]
            r1 = self.audio_visualizationGo(data, w, h, icolor, WindX['b_frame1_canvas'], isValid, increasing=increasing, data_index=data_index, data_x0= WindX['audio_visualizationGo_x0'], wblock=wblock)

            if (not isTest) and len(WindX['SystemAudioDevice_data'].keys()):                
                for s in WindX['SystemAudioDevice_data'].keys():
                    if WindX['SystemAudioDevice_data'][s]:
                        r2 += self.audio_visualizationGo(
                            WindX['SystemAudioDevice_data'][s][0],
                            w, h, self.device_colors[s], WindX['b_frame1_canvas'],
                            WindX['SystemAudioDevice_data'][s][1], 
                            increasing=increasing,
                            data_index = s, 
                            data_x0= WindX['audio_visualizationGo_x0'],
                            wblock=wblock
                        )
            
            WindX['audio_visualizationGo_x0'] += wblock   #x0
        #print(sys._getframe().f_lineno,'audio_visualization: r1, r2=', r1, r2)

        return r1+r2

    def audio_visualizationGo(self, data, w, h, color, icanvas, isValid, dy=2, dx=10, x0=0, kk=16, increasing=False, data_index=None, data_x0=0, wblock=10):
        """
        draw audio wave in canvas
        """
        #return 0
    
        linetype = 'line'
        result = True
        points_y = []
        
        if isValid:
            linetype = 'polygon'
            audio_data = np.frombuffer(data, dtype=np.short) 
            len_audio_data = len(audio_data)
            if len_audio_data:
                try:
                    xmax = np.max(audio_data)
                    xmin = np.min(audio_data)
                    #print(sys._getframe().f_lineno,len_audio_data, xmax, xmin)
                    
                    if increasing and data_index:
                        while wblock * kk / len_audio_data < 1:
                            kk = kk + 1
                    else:
                        while w * kk / len_audio_data < 1:
                            kk = kk + 1                        
                    #print(sys._getframe().f_lineno,'kk=', kk, wblock)

                    k = 0
                    ss = []
                    sss= []
                    for i in range(len_audio_data):
                        k +=1
                        ss.append(audio_data[i])
                        if k == kk and len(ss):
                            sss.append(ss)
                            ss = []
                            k = 0
                    if len(ss):
                        sss.append(ss)
                    
                    for ss in sss:
                        '''
                        xmax1 = np.max(ss)                             
                        xmin1 = np.min(ss) 
                        val = 0
                        if xmax1 > abs(xmin1):
                            val = xmax1
                        else:
                            val = xmin1
                        '''
                        val = int(np.average(ss))
                        y  = 0

                        if increasing and data_index:
                            val = int(val * self.audio_visualization_signal_enhance)
                            if val < 0:
                                y = int(h/2 + val/xmin*(h/2-dy))                        
                            else:
                                y = int(h/2 - val/xmax*(h/2-dy))
                        else:
                            y = val
                        
                        #if y < 0 or y > h:
                        #    print(sys._getframe().f_lineno,y)
                        points_y.append(y)    

                    if not (increasing and data_index):
                        xmax = np.max(points_y)
                        xmin = np.min(points_y)
                        #print(sys._getframe().f_lineno,"not (increasing and data_index): ", xmax, xmin)
                        for ii in range(len(points_y)):
                            if points_y[ii] < 0:
                                points_y[ii] = int(h/2 + points_y[ii]/xmin*(h/2-dy))  
                            else:
                                points_y[ii] = int(h/2 - points_y[ii]/xmax*(h/2-dy))
                except:
                    print(sys._getframe().f_lineno,traceback.format_exc())
                    result = False
            else:
                result = False  

        if result:
            points = []
            if increasing and data_index:
                x = data_x0
                if linetype == 'line':
                    points=[                        
                        x,
                        int(h/2), 
                        x + wblock,
                        int(h/2)
                    ]
                else:
                    points.append(x)
                    points.append(int(h/2))
                    lw = wblock/ len(points_y)
                    for i in range(len(points_y)):
                        points.append(x)
                        points.append(points_y[i])
                        x+= lw 
                    points.append(x - lw)
                    points.append(int(h/2)) 
            else:
                if linetype == 'line':
                    points = [0, int(h/2), w, int(h/2)]
                else:
                    x = x0
                    lw = w / len(points_y)
                    for i in range(len(points_y)):
                        points.append(x)
                        points.append(points_y[i])
                        x+= lw

                    for x in [int(h/2), -2, h*2, -10]:
                        points.insert(0, x)
                    points.append(int(w + dx))
                    points.append(int(h/2)) 
                    points.append(int(w + dx*2))
                    points.append(int(h*2))

            item = 0

            try:
                if linetype == 'line':
                    item = icanvas.create_line(
                        points,
                        fill = color,
                        width= 1
                    )               
                else:
                    item = icanvas.create_polygon(points, width=1,outline=color,fill="")
            except:
                print(sys._getframe().f_lineno, traceback.format_exc())
            
            if increasing and data_index:                
                if not WindX['audio_visualizationGo_canvas_items'].__contains__(data_x0):
                    WindX['audio_visualizationGo_canvas_items'][data_x0] = []
                WindX['audio_visualizationGo_canvas_items'][data_x0].append(item)

                if data_x0 > 0:
                    keep_n = int(w / wblock + 10)
                    items_len = len(WindX['audio_visualizationGo_canvas_items'].keys())
                    if items_len > keep_n:
                        i = 0
                        for dx in sorted(WindX['audio_visualizationGo_canvas_items'].keys()):
                            i+=1
                            if i > items_len - keep_n:
                                break
                            go = True
                            for x in WindX['audio_visualizationGo_canvas_items'][dx]:
                                try:
                                    icanvas.delete(x)
                                except:
                                    go = False
                                    pass
                            if go:
                                try:
                                    del WindX['audio_visualizationGo_canvas_items'][dx]   
                                except:
                                    pass    

                    #print(sys._getframe().f_lineno,'keep_n=', keep_n, ', [canvas_items by x0-key]=', list(WindX['audio_visualizationGo_canvas_items'].keys())[0:10])

                icanvas.configure(scrollregion=icanvas.bbox("all"))
                #scrollregion = icanvas.configure('scrollregion')
                #rect = UI_WidgetRectGET(icanvas)
                #print(sys._getframe().f_lineno,'visual canvas:', rect, ', width=', rect[2] - rect[0], ', scrollregion=', scrollregion[4])
                icanvas.xview_moveto(1.0)

            return 1
        else:
            return 0                     

    def audio_add_ui(self, device, filepath, frames, data_avg, history_row_data=None):
        if not self.go_to_page:
            WindX['frame_visualize_all_pages_ui_index'] += 1

        #ct = time.time()
        #st = int((ct - int(ct))*1000)
        #t = time.strftime("%H:%M:%S",time.localtime(ct)) + "." + str(st) + "\n#" + str(WindX['frame_visualize_all_pages_ui_index']) + " " + device + "\n(" + str(data_avg) + ")"
        #print(sys._getframe().f_lineno,"\naudio_add_ui:", t, len(WindX['add_ui_data']))
        y_moveto = 1.0
        WindX['ClassScrollableFrame_frame_rows'] +=3
        ct = time.time()

        #isnewpage=False
        if not self.go_to_page:
            if (WindX['frame_visualize_all_pages_ui_index'] > self.audio_visualization_num_per_page) and (WindX['frame_visualize_all_pages_ui_index'] % self.audio_visualization_num_per_page) == 1: #new page
                self.audio_visualization_cur_page_num += 1
                #isnewpage= True
                WindX['ClassScrollableFrame_frame_rows'] = 0
                y_moveto = 0.0

                if not self.load_history:
                    UI_WinWidgetRemove(wid=WindX['ClassScrollableFrame'].scrollable_frame) 

                print(sys._getframe().f_lineno,"\nui_index=", WindX['frame_visualize_all_pages_ui_index'], ", page#", self.audio_visualization_cur_page_num, ", num_per_page=", self.audio_visualization_num_per_page)

        if self.load_history and self.audio_visualization_cur_page_num > 1:
            WindX['frame_visualize_all_pages'][WindX['frame_visualize_all_pages_ui_index']] = {}
            for x in history_row_data.keys():
                WindX['frame_visualize_all_pages'][WindX['frame_visualize_all_pages_ui_index']][x] =  history_row_data[x]

            k = len(WindX['frame_visualize_all_pages'].keys())
            pages = int(k / self.audio_visualization_num_per_page) + 1
            WindX['b_AudioPageStatus'].config(text=" Page 1/"+ str(pages) +" ("+ str(k) +")")
            WindX['main'].update()
        
            WindX['ClassScrollableFrame_frame_rows'] = -3
            return

        t1 = threading.Timer(
            0.01,
            self.audio_add_ui_go,
            args=[
                WindX['ClassScrollableFrame_frame_rows'],
                device, filepath, frames, history_row_data, 
                WindX['frame_visualize_all_pages_ui_index'],
                ct,
                y_moveto
            ] 
        )
        t1.start()

        #if isnewpage:
        #    WindX['ClassScrollableFrame_frame_rows'] = -3

    def audio_add_ui_go(self, start_row, device, filepath, frames, history_row_data, all_pages_rows, ct, y_moveto):
        try:  
            xrow = start_row
            data = b''.join(frames)
            record_time = int(len(frames)*self.frames_per_buffer / self.rate * 1000)/1000

            pady = 0
            ibg = WindX['win_main_background']
            ifg = "#FFFFFF"

            lbl0 = Label(WindX['ClassScrollableFrame'].scrollable_frame, text="", justify=CENTER, relief=FLAT,pady=3,padx=3, bg=ibg)
            lbl0.grid(row=xrow,column=0,sticky=E+W+N+S, pady=0, padx=0, columnspan=10)

            xrow +=1
            icanvas = Canvas(WindX['ClassScrollableFrame'].scrollable_frame, 
                height=30,
                bg= ibg,
                relief=FLAT,
                bd = 0
            )
            icanvas.grid(row=xrow,column=0,sticky=E+W+S+N,pady=0,padx=0,columnspan=10)
            icanvas.configure(highlightthickness = 0)

            xrow +=1
            pady = 1 
            irow = xrow
            b = iButton(
                WindX['ClassScrollableFrame'].scrollable_frame,
                xrow,
                0, 
                lambda:self.audio_play(filepath, irow),
                '▶',
                fg=ifg,bg=ibg,p=[LEFT,FLAT,3,1,'#A0A0A0','#A0A0A0',5,E+W+N+S,pady, 0])

            st = int((ct - int(ct))*1000)
            ttitle = "#" + str(all_pages_rows) + " " + time.strftime("%H:%M:%S",time.localtime(ct)) + "." + str(st) + "\n" + device + "\n" + re.sub(r'^(00\:)+', '',usedTime(0,record_time)) #+ "\n(" + str(data_avg) + ")"
            
            if self.load_history or self.go_to_page:
                ttitle = history_row_data["title"]
                                                                            #+ "\nrow." + str(xrow)
            lbl1 = Label(WindX['ClassScrollableFrame'].scrollable_frame, text= ttitle, justify=CENTER, relief=FLAT,pady=3,padx=3,fg='#E0E0E0', bg = ibg)
            lbl1.grid(row=xrow,column=1,sticky=E+W+N+S, pady=pady, padx=1)

            text = Text(WindX['ClassScrollableFrame'].scrollable_frame,
                        fg= ifg, bg = ibg, wrap = 'word',
                        font=("Arial", 10),
                        relief=FLAT,pady=3,padx=3, height=5)
            text.grid(row=xrow,column=2,sticky=E+W+N+S, pady=pady, padx=0)

            audio2text = ""
            translation= ""
            if self.load_history or self.go_to_page:
                all_pages_rows = history_row_data['all_pages_rows']

                tstr = history_row_data["audio2text"]
                audio2text = history_row_data["audio2text"]
                if len(tstr) and len(history_row_data["translation"]):
                    tstr = tstr + "\n" + history_row_data["translation"]
                    translation = history_row_data["translation"]
                text.insert('0.0', tstr)

                if re.match(r'^\[Error\!\]\s+', history_row_data["audio2text"], re.I):
                    text.config(fg="red")
                elif re.match(r'^\[Warning\!\]\s+', history_row_data["audio2text"], re.I):
                    text.config(fg="yellow")

            if not self.go_to_page:
                WindX['frame_visualize_all_pages'][all_pages_rows] = {
                    'filepath': filepath,
                    'device': device,
                    'record_time': record_time,
                    'total_frames': len(frames)*self.frames_per_buffer,
                    'title': ttitle,
                    'audio2text': audio2text,
                    'translation': translation,
                    'record_time': ct,
                    'all_pages_rows': all_pages_rows
                }

            WindX['frame_visualize_cur_page'][xrow] =[lbl1, b.b, text, icanvas, filepath, device, None, record_time, len(frames)*self.frames_per_buffer, ttitle, WindX['main'].winfo_width(), "", "", all_pages_rows] 

            xx = re.split(r'\s+', re.sub(r'^\s+|\s+$','', re.sub(r'[^\d]+',' ', str(device), re.I)))
            data_index = 'data' + xx[-1]
            t1 = threading.Timer(0.1, self.audio_add_ui_refresh, args=[icanvas, data, y_moveto, data_index])
            t1.start()
        except:
            print(sys._getframe().f_lineno,traceback.format_exc())

    def audio_add_ui_refresh(self, icanvas, data, y_moveto, data_index):
        if not self.go_to_page:
            k = len(WindX['frame_visualize_all_pages'].keys())
            pages = int(k / self.audio_visualization_num_per_page) + 1
            WindX['b_AudioPageStatus'].config(text=" Page "+str(self.audio_visualization_cur_page_num)+"/"+ str(pages) +" ("+ str(k) +")")

        WindX['main'].update()
        rectFram = UI_WidgetRectGET(icanvas)
        w = rectFram[2] - rectFram[0]
        h = rectFram[3] - rectFram[1]

        icolor = self.audio_visualization_line_color
        if data_index and self.device_colors.__contains__(data_index):
            icolor = self.device_colors[data_index]
        self.audio_visualizationGo(data, w, h, icolor, icanvas, True, dy=1, dx=1, x0=0)               
        WindX['ClassScrollableFrame'].canvasLeave(force=True, y_moveto=y_moveto)

    def audio_conversion_check(self,):
        while True:
            try:
                if WindX['frame_visualize_cur_page'] and len(WindX['frame_visualize_cur_page'].keys()):
                    n = 0
                    filepath = ""
                    for row in sorted(WindX['frame_visualize_cur_page'].keys()):
                        try:
                            filepath = WindX['frame_visualize_cur_page'][row][4]
                            fileID   = UT_GetMD5(filepath)
                            if WindX['frame_visualize_cur_page_done'].__contains__(fileID) and WindX['frame_visualize_cur_page_done'][fileID]:
                                continue
                            
                            row_13 = WindX['frame_visualize_cur_page'][row][13]
                            if len(str(row_13)) and WindX['frame_visualize_all_pages'].__contains__(row_13):
                                if len(WindX['frame_visualize_all_pages'][row_13]['audio2text']) and len(WindX['frame_visualize_all_pages'][row_13]['translation']):
                                    WindX['frame_visualize_cur_page_done'][fileID] = True
                                    continue

                                #print(sys._getframe().f_lineno,row, fileID, filepath)
                                #print(sys._getframe().f_lineno,row_13, "audio2text=", WindX['frame_visualize_all_pages'][row_13]['audio2text'], "|||| translation=", WindX['frame_visualize_all_pages'][row_13]['translation'])

                                k = 0
                                if not len(WindX['frame_visualize_all_pages'][row_13]['audio2text']):
                                    if os.path.exists(filepath) and os.path.exists(filepath + '.txt'):
                                        t = UT_FileOpen(filepath + '.txt', format='string')
                                        if len(t):
                                            k += 1
                                            WindX['frame_visualize_all_pages'][row_13]['audio2text'] = t
                                        else:
                                            WindX['frame_visualize_all_pages'][row_13]['audio2text'] = " "
                                        os.rename(filepath + '.txt', filepath + '.txt' + '.done')
                                    elif os.path.exists(filepath) and os.path.exists(filepath + '.txt.done'):
                                        t = UT_FileOpen(filepath + '.txt.done', format='string')
                                        if len(t):
                                            k += 1                                        
                                            WindX['frame_visualize_all_pages'][row_13]['audio2text'] = t      
                                        else:
                                            WindX['frame_visualize_all_pages'][row_13]['audio2text'] = " "
                                    elif os.path.exists(filepath) and os.path.exists(filepath + '.err'):
                                        t = UT_FileOpen(filepath + '.err', format='string')                            
                                        if len(t):
                                            k += 1                                        
                                            WindX['frame_visualize_all_pages'][row_13]['audio2text'] = "[Error!] " + t                                        
                                        else:
                                            WindX['frame_visualize_all_pages'][row_13]['audio2text'] = " "

                                    elif os.path.exists(filepath) and os.path.exists(filepath + '.warn'):
                                        t = UT_FileOpen(filepath + '.warn', format='string')                            
                                        if len(t):
                                            k += 1                                        
                                            WindX['frame_visualize_all_pages'][row_13]['audio2text'] = "[Warning!] " + t                                        
                                        else:
                                            WindX['frame_visualize_all_pages'][row_13]['audio2text'] = " "

                                if not len(WindX['frame_visualize_all_pages'][row_13]['translation']):
                                    if os.path.exists(filepath) and os.path.exists(filepath + '.translated'):
                                        tt = UT_FileOpen(filepath + '.translated', format='string')
                                        if len(tt):
                                            k += 1
                                            WindX['frame_visualize_all_pages'][row_13]['translation'] = tt
                                        else:
                                            WindX['frame_visualize_all_pages'][row_13]['translation'] = " "
                                        os.rename(filepath + '.translated', filepath + '.translated' + '.done')
                                    elif os.path.exists(filepath) and os.path.exists(filepath + '.translated.done'):
                                        tt = UT_FileOpen(filepath + '.translated.done', format='string')
                                        if len(tt):
                                            k += 1
                                            WindX['frame_visualize_all_pages'][row_13]['translation'] = tt
                                        else:
                                            WindX['frame_visualize_all_pages'][row_13]['translation'] = " "

                                if k and len(WindX['frame_visualize_all_pages'][row_13]['audio2text']):
                                    t = WindX['frame_visualize_all_pages'][row_13]['audio2text']
                                    if re.match(r'^\[Error\!\]\s+', t, re.I):
                                        WindX['frame_visualize_cur_page'][row][2].config(fg="red")
                                    elif re.match(r'^\[Warning\!\]\s+', t, re.I):
                                        WindX['frame_visualize_cur_page'][row][2].config(fg="yellow")

                                    if len(t) and len(WindX['frame_visualize_all_pages'][row_13]['translation']):
                                        t = t + "\n" + WindX['frame_visualize_all_pages'][row_13]['translation']    
                                        WindX['frame_visualize_cur_page_done'][fileID] = True                  
                                    n+=1
                                    try:
                                        WindX['frame_visualize_cur_page'][row][2].delete('0.0',"end")
                                        WindX['frame_visualize_cur_page'][row][2].insert('0.0', t)
                                    except:
                                        pass  
                        except:
                            print(sys._getframe().f_lineno,traceback.format_exc())
                    
                    if filepath and self.audio_info_outfile:
                        #set a condition to break the while loop
                        file_dir = re.sub(r'\\','/',os.path.dirname(filepath)).upper()
                        self_dir = re.sub(r'\\','/',os.path.dirname(self.audio_info_outfile)).upper()
                        if file_dir == self_dir:
                            if n and not (self.load_history or self.go_to_page):
                                AudioInfoSave(self.audio_info_outfile)
                        else:
                            print(sys._getframe().f_lineno, "\nfile_dir: {}\nself_dir: {}\n------------**** audio_conversion_check break ****------------\n".format(file_dir, self_dir))
                            break
            except:
                print(sys._getframe().f_lineno,traceback.format_exc())
            
            time.sleep(1)

    def audio_play(self, filepath, row):
        #if WindX['b_AudioRecord_action']:
        #    return        
        WindX['audio_play_Go_working'].append(1)
        t1 = threading.Timer(0.5, self.audio_play_Go, args=[filepath, row])
        t1.start()

    def audio_play_Go(self, filepath, row):
        #print(sys._getframe().f_lineno,"\naudio_play_Go:", filepath, ', row=',row)   
        if not (WindX['audio_play_Go_working_by_row'].__contains__(row) and WindX['audio_play_Go_working_by_row'][row]):
            WindX['audio_play_Go_working_by_row'][row] = True
            icanvas = WindX['frame_visualize_cur_page'][row][3]
            total_chunk = WindX['frame_visualize_cur_page'][row][8]
            record_time = WindX['frame_visualize_cur_page'][row][7] 
            all_data = [] #WindX['frame_visualize_cur_page'][row][6]
            last_WinWidth =  WindX['frame_visualize_cur_page'][row][10]      
            WindX['frame_visualize_cur_page'][row][1].config(text='■')
        
            self.audio_play_Go2(filepath, icanvas, total_chunk, record_time, all_data, last_WinWidth, row, WindX['frame_visualize_cur_page'][row][1])

        WindX['audio_play_Go_working_by_row'][row] = False
        WindX['audio_play_Go_working'].pop(0)
        WindX['frame_visualize_cur_page'][row][1].config(text='▶', fg='#FFFFFF')

    def audio_play_Go2(self, filepath, icanvas, total_chunk, record_time, all_data, last_WinWidth, row, bplaybutton): 
        try:
            rectFram = UI_WidgetRectGET(icanvas)
            w = rectFram[2] - rectFram[0]
            h = rectFram[3] - rectFram[1]

            #icanvas.delete('all')
            if not last_WinWidth == WindX['main'].winfo_width(): 
                if not len(all_data):
                    wf = wave.open(filepath, 'rb')
                    all_data = wf.readframes(wf.getnframes())
                    wf.close()
                self.audio_visualizationGo(all_data, w, h, 'red', icanvas, True, dy=1, dx=1, x0=0)

            indicator = icanvas.create_line(
                            0, int(h/3),
                            0, h-3,
                            fill = '#FFFFFF',
                            width= 1,
                        )
            r_time = icanvas.create_text(
                    2,
                    8,
                    font = ('Arial', 8, 'normal'),
                    text = '00:00:00',
                    fill = '#FFFFFF',
                    anchor = W,
                    justify = LEFT)

            chunk = self.frames_per_buffer
            wf = wave.open(filepath, 'rb')
            p = pyaudio.PyAudio()
            stream = p.open(
                format=p.get_format_from_width(wf.getsampwidth()), 
                channels=wf.getnchannels(),
                rate=wf.getframerate(), 
                output=True
            )

            data = wf.readframes(chunk)  # 读取数据
            #print(sys._getframe().f_lineno,data)
            now_chunk = 0
            while data != b'':  # 播放
                if not WindX['audio_play_Go_working_by_row'][row]:
                    break

                stream.write(data)
                data = wf.readframes(chunk)
                #print(sys._getframe().f_lineno,'while循环中！')
                #print(sys._getframe().f_lineno,data)
                now_chunk += chunk
                x = int(w*now_chunk/total_chunk)
                icanvas.coords(indicator, x, int(h/3), x, h-3)

                t = usedTime(0, record_time*now_chunk/total_chunk)
                icanvas.itemconfig(r_time, text= re.sub(r'^(00\:)+', '', t))
                #icanvas.coords(r_time, x+2, 8)

                colors = GetColorsHex(2)
                bplaybutton.config(fg=colors[1])
                WindX['main'].update()

            wf.close()
            stream.stop_stream()  # 停止数据流
            stream.close()
            p.terminate()  # 关闭 PyAudio

            icanvas.delete(indicator)
            icanvas.delete(r_time)
        except:
            print(sys._getframe().f_lineno,traceback.format_exc())

    def audio_device_test(self, row=0, device_index=0):
        try:                     
            self.init()
            p = pyaudio.PyAudio()   

            test_time = 15
            data_index = 'data' + str(device_index)
            WindX['audio_visualizationGo_PointData'][data_index] = []
            print(sys._getframe().f_lineno,GUI_LANG(74) + str(device_index), ", for "+str(test_time)+" seconds ...")

            stream = p.open(
                format  = self.format,  # 音频流wav格式
                channels= self.channels,  # 声道
                rate    = self.rate,  # 采样率
                input   =True,
                frames_per_buffer= self.frames_per_buffer,
                input_device_index= device_index)
            self.sampwidth = p.get_sample_size(self.format)

            st = time.time() + test_time
            for i in range(int(test_time*self.rate/self.frames_per_buffer)):     
                data = stream.read(self.frames_per_buffer)
                self.audio_visualization(data, data_index, isTest=True)
                WindX['b_AudioDeviceTests'][row].config(text= re.sub(r'^(00\:)+', '',usedTime(0, st - time.time())))
                WindX['main'].update()

            stream.stop_stream()  # 停止数据流
            stream.close()
            p.terminate()  # 关闭 PyAudio
        except:
            print(sys._getframe().f_lineno,traceback.format_exc())

    def audio_load_history(self):
        print(sys._getframe().f_lineno,'\naudio_load_history: self.outfoldertmp=', self.outfoldertmp)
        vals = UT_JsonFileRead(filepath= self.history_file)
        #print(sys._getframe().f_lineno,json.dumps(vals, indent=4, ensure_ascii=False))
        '''
        "2": {
            "filepath": "c:/Users/dengm/OneDrive/Program/AudioTranslator/Recorders/Audio.20230811-235115/device-1_1691769121.7444327.wav",
            "device": "Stereo Mix(1)",
            "record_time": 4.8,
            "total_frames": 76800,
            "title": "#1 23:52:01.789\nStereo Mix(1)\n04.800",
            "audio2text": "\u864e\u62518\u670810\u65e5\u8baf\u54c8\u767b\u6628\u65e5\u62b5\u8fbe\u4e0a\u6d77\uff0c\u5f00\u542f\u4e2d\u56fd\u884c\u3002",
            "translation": "Huden arrived in Shanghai yesterday and started his trip to China."
        },
        '''
        
        vals_rows = []
        for x in vals.keys():
            vals_rows.append([int(x), vals[x]['record_time']])
        vals_rows = sorted(vals_rows, key=lambda x:x[1], reverse=False)
        #for x in vals_rows:
        #    print(sys._getframe().f_lineno,x)

        self.audio_load_sections(vals_rows, vals)
        t1 = threading.Timer(0.1, AudioConvertorStart, args=[self.convert_to_language , self.convert_engine])
        t1.start()
        t2 = threading.Timer(0.1,self.audio_conversion_check)
        t2.start()

    def audio_load_sections(self, vals_rows, vals):
        if not len(vals_rows):
            return
        
        self.init()

        stime = time.time()
        n = len(vals_rows)
        i = 0
        for r in vals_rows:
            row = r[0]
            if not vals.__contains__(row):
                row = str(r[0])
            try:
                i +=1
                Progress(i, n, stime, x="Loading ...")

                history_row_data = vals[row]
                if not self.outfoldertmp:
                    self.outfoldertmp = os.path.dirname(history_row_data["filepath"])
                         
                filepath = self.outfoldertmp + '/' + os.path.basename(history_row_data["filepath"])
                if os.path.exists(filepath):                    
                    frames= []
                    if not (self.load_history and self.audio_visualization_cur_page_num > 1):  #read the first page audio file only
                        chunk = self.frames_per_buffer
                        wf = wave.open(filepath, 'rb')
                        data = wf.readframes(chunk)  # 读取数据
                        while data != b'': 
                            frames.append(data)
                            data = wf.readframes(chunk)
                        wf.close()
                        #print(sys._getframe().f_lineno,row, 'frames=', len(frames), type(frames[0]))

                    history_row_data["filepath"] = filepath
                    self.audio_add_ui(
                        history_row_data["device"], 
                        filepath, 
                        frames,
                        0,
                        history_row_data
                    )
                else:
                    print("\n", sys._getframe().f_lineno,"\t... audio file missing:", filepath)
            except:
                print(sys._getframe().f_lineno,traceback.format_exc())
        Progress(i, n, stime, x="Loaded ")
        WindX['main'].title(GUI_LANG(76) + " Rev " + WindX['main_rev'] + "  " + self.outfoldertmp)

    def audio_go_to_page(self, to_page):
        print(sys._getframe().f_lineno,'self.go_to_page=', self.go_to_page, to_page)

        row_max = len(WindX['frame_visualize_all_pages'].keys())
        vals_rows = []
        start_row = self.audio_visualization_num_per_page * (to_page - 1) + 1
        for i in range(self.audio_visualization_num_per_page):
            row = start_row + i
            if WindX['frame_visualize_all_pages'].__contains__(row):
                vals_rows.append([row, WindX['frame_visualize_all_pages'][row]['record_time']])
            elif row <= row_max:
                print(sys._getframe().f_lineno,"!!! page#" + str(to_page), "row#" + str(row), ", is missing!")

        self.audio_load_sections(vals_rows, WindX['frame_visualize_all_pages'])
        
class iButton:
    def __init__(self,frm,row=0,col=0,cmd=None,txt='?',fg='blue',bg='#E0E0E0',
                    colspan=1,msg=None, 
                    p=[LEFT,FLAT,3,1,'#FFFF66','#FFFF99',5,E+W+N+S,0,0]):
        
        self.motion_color = p[5]
        self.b = Button( frm, 
                    text=txt, 
                    fg=fg,
                    bg=bg,
                    justify=p[0], 
                    relief=p[1],
                    padx=p[2],
                    pady=p[3],                    
                    activebackground=p[4],
                    highlightbackground=p[5],
                    width=p[6],
                    command=cmd
                    )
        self.b.grid( row=row,
                column=col,
                sticky=p[7],
                pady=p[8],
                padx=p[9],
                columnspan=colspan
                )
        self.b.bind('<Motion>',self.iMotion)
        self.b.bind('<Leave>',self.iLeave)
        self.bg = bg

        if msg:                
            self.message = msg
        else:
            self.message = ""

    def iMotion(self,event):
        self.b.config(bg = self.motion_color)

    def iLeave(self,event):
        self.b.config(bg = self.bg)

class ClassScrollableFrame2(ttk.Frame):
    def __init__(self, container, show_scrollbar_x=True, *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        self.canvas = Canvas(self, 
            width=500, 
            height=300,
            #bg= WindX['win_main_background'],
            relief=FLAT,
            bd = 0,
        )
        self.canvas.configure(highlightthickness = 0)
        self.canvas.grid(row=0,column=0,sticky=E+W+N+S,padx=0,pady=0)
        
        self.scrollbar_y = ttk.Scrollbar(self, orient="vertical",   command=self.canvas.yview)
        if show_scrollbar_x:
            self.scrollbar_x = ttk.Scrollbar(self, orient="horizontal", command=self.canvas.xview)

        self.gui_style = ttk.Style()
        self.gui_style.configure('My.TFrame', background='#404040', padx=0, pady=0, relief=FLAT, bd=0)
        self.scrollable_frame = ttk.Frame(self.canvas, style='My.TFrame')
        
        #"""
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )
        #"""

        self.container = container        
        container.bind("<Motion>", self.canvasMotion)
        container.bind("<MouseWheel>",  self.canvasMouseWheel)
        container.bind("<Leave>",  self.canvasLeave)
                
        self.win_scrollable_frame_canvas_index = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar_y.set)
        if show_scrollbar_x:
            self.canvas.configure(xscrollcommand=self.scrollbar_x.set)

        self.scrollbar_y_show = True

        self.scrollbar_y.grid(row=0,column=1,sticky=N+S)
        if show_scrollbar_x:
            self.scrollbar_x.grid(row=1,column=0,sticky=E+W) 

        #self.scrollable_frame.grid(row=0,column=0,sticky=E+W,padx=0,pady=0)  #can not grid, because need scrollbar_y function!!!!
        self.canvas.grid_columnconfigure(0, weight=1)
        #self.canvas.grid_rowconfigure(0, weight=1)

        #- ttkFrame
        #---- canvas (0, 0)
        #-------- scrollable_frame
        #---- scrollbar_y (0,1), scrollbar_y (1,1)

    def canvasMouseWheel(self,e):
        if self.scrollbar_y_show:
            #print(sys._getframe().f_lineno,"canvasMouseWheel")
            self.canvas.yview_scroll(int(-1*(e.delta/120)), "unit")

    def canvasMotion(self,e):
        return
        self.scrollbar_y.grid()
        self.scrollbar_y_show = True

    def canvasLeave(self,e=None,force=False, y_moveto=1.0):
        rectMain = UI_WidgetRectGET(self.container)
        MainW = rectMain[2] - rectMain[0] - 2

        if not WindX['self_scrollable_frame2']:
            rectFram = UI_WidgetRectGET(self.scrollable_frame)
            WindX['self_scrollable_frame2'] = rectFram[2] - rectFram[0]

        #1. check width
        CanvW = MainW - WindX['yscrollbar_oWidth']
        if CanvW > 0 and WindX['self_scrollable_frame2'] < MainW:
            #print(sys._getframe().f_lineno,"set width=", CanvW)
            self.canvas.configure(width = CanvW)
            self.canvas.itemconfig(self.win_scrollable_frame_canvas_index, width=CanvW) #change the windows inside canvas

class ClassScrollableFrame(ttk.Frame):
    def __init__(self, container, *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        self.canvas = Canvas(self, 
            width=500, 
            height=300,
            bg= WindX['win_main_background'],
            relief=FLAT,
            bd = 0,
        )
        self.canvas.configure(highlightthickness = 0)
        self.canvas.grid(row=0,column=0,sticky=E+W+N+S,padx=0,pady=0)
        
        self.scrollbar_y = ttk.Scrollbar(self, orient="vertical",   command=self.canvas.yview)
        #self.scrollbar_x = ttk.Scrollbar(self, orient="horizontal", command=self.canvas.xview)

        self.gui_style = ttk.Style()
        self.gui_style.configure('My.TFrame', background='#404040', padx=0, pady=0, relief=FLAT, bd=0)
        self.scrollable_frame = ttk.Frame(self.canvas, style='My.TFrame')
        
        #"""
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )
        #"""

        self.container = container        
        container.bind("<Motion>", self.canvasMotion)
        container.bind("<Leave>",  self.canvasLeave)
        #container.bind("<MouseWheel>",  self.canvasMouseWheel)
        
        self.win_scrollable_frame_canvas_index = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar_y.set)
        #self.canvas.configure(xscrollcommand=self.scrollbar_x.set)

        self.scrollbar_y_show = True

        self.scrollbar_y.grid(row=0,column=1,sticky=N+S)
        #self.scrollbar_x.grid(row=1,column=0,sticky=E+W) 

        #self.scrollable_frame.grid(row=0,column=0,sticky=E+W,padx=0,pady=0)  #can not grid, because need scrollbar_y function!!!!
        #self.canvas.grid_columnconfigure(0, weight=1)
        #self.canvas.grid_rowconfigure(0, weight=1)

        #- ttkFrame
        #---- canvas (0, 0)
        #-------- scrollable_frame
        #---- scrollbar_y (0,1), scrollbar_y (1,1)

    def canvasMouseWheel(self,e):
        if self.scrollbar_y_show:
            #print(sys._getframe().f_lineno,"canvasMouseWheel")
            self.canvas.yview_scroll(int(-1*(e.delta/120)), "unit")

    def canvasMotion(self,e):
        return
        self.scrollbar_y.grid()
        self.scrollbar_y_show = True

    def canvasLeave(self,e=None,force=False, y_moveto=1.0):

        if not force:
            if WindX['win_last_geo'] == WindX['main'].geometry():
                return
        #fit frame22 to window size

        #- root
        #-- frame1
        #-- frame2
        #- ttkFrame (class)
        #---- canvas (0, 0)
        #-------- scrollable_frame ==> as frame221
        #---- scrollbar_y (0,1), scrollbar_y (1,1)
        #-- frame3
        
        #print(sys._getframe().f_lineno,'container=', self.container)
        try:
            rectMain = UI_WidgetRectGET(WindX['main'])
            rectFram = UI_WidgetRectGET(self.scrollable_frame)
            MainH = rectMain[3] - rectMain[1]
            MainW = rectMain[2] - rectMain[0]
            FramH = rectFram[3] - rectFram[1]
            rectFram1 = UI_WidgetRectGET(WindX['Frame1'])
            rectFram3 = UI_WidgetRectGET(WindX['Frame3'])
            Fram1H = rectFram1[3] - rectFram1[1]
            Fram3H = rectFram3[3] - rectFram3[1]

            WindX['b_frame1_canvas'].configure(width = MainW - 10)
            #1. check width
            CanvW = MainW - WindX['yscrollbar_oWidth']
            if CanvW > 0:
                #print(sys._getframe().f_lineno,"set width=", CanvW)
                self.canvas.configure(width = CanvW)
                self.canvas.itemconfig(self.win_scrollable_frame_canvas_index, width=CanvW) #change the windows inside canvas

            #2. check height   
            to_height = MainH - Fram1H - Fram3H #- WindX['yscrollbar_oWidth']            
            self.canvas.configure(height= to_height)                

            rectCanv = UI_WidgetRectGET(self.canvas)
            #print(sys._getframe().f_lineno,"canvas inside: width=", rectCanv[2] - rectCanv[0], ", height=", rectCanv[3] - rectCanv[1])  
            #CanvH = rectCanv[3] - rectCanv[1]
            rectMain = UI_WidgetRectGET(WindX['main'])
            MainH = rectMain[3] - rectMain[1]
            CanvCurA_H = MainH - Fram1H - Fram3H
            
            refresh_scroll = True
            
            if FramH < CanvCurA_H:
                self.scrollbar_y.grid_remove()
                self.scrollbar_y_show = False
                refresh_scroll = False
                self.canvas.configure(width = MainW)
                self.canvas.itemconfig(self.win_scrollable_frame_canvas_index, width=MainW) #change the windows inside canvas
            else:
                self.scrollbar_y.grid()
                self.scrollbar_y_show = True

            if refresh_scroll:
                CanvW = rectCanv[2] - rectCanv[0]
                CanvH = rectCanv[3] - rectCanv[1]
                #print(sys._getframe().f_lineno,"\nrefresh scroll:", refresh_scroll, ", canvas inside", rectCanv, (CanvW, CanvH), ", scrollregion=",(0, 0, CanvW, FramH), ", WindX['main'].geometry()=",WindX['main'].geometry())          
                self.canvas.configure(scrollregion=(0, 0, CanvW, FramH))
                self.canvas.yview_moveto(y_moveto)
            
            #print(sys._getframe().f_lineno,"self.scrollable_frame.configure()=", self.scrollable_frame.configure())
            #self.scrollbar_y_show = False
            #self.scrollbar_y.grid_remove()
            #self.scrollbar_x.grid_remove()

            #WindX['main'].update()
            #print(sys._getframe().f_lineno,"WindX['main'].winfo_width=", WindX['main'].winfo_width())
            #print(sys._getframe().f_lineno,"self.canvas.winfo_width=", self.canvas.winfo_width())
            #print(sys._getframe().f_lineno,"self.scrollable_frame.winfo_width=", self.scrollable_frame.winfo_width())
            #print(sys._getframe().f_lineno,"scrollable_frame width=", self.canvas.itemconfig(self.win_scrollable_frame_canvas_index, 'width'))

            WindX['win_last_geo'] = WindX['main'].geometry()
        except:
            print('red', sys._getframe().f_lineno, traceback.format_exc())


if __name__ == "__main__":      
    main()
