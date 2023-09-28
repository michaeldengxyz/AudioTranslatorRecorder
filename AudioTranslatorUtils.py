#Pyhton 3.x
# -*- coding: UTF-8 -*-

import time
import traceback
import re
import os,sys
import win32gui
from ttkwidgets.frames import Tooltip

import hashlib
import numpy as np
import random
import json
from numpyencoder import NumpyEncoder

import zlib
import base64
from Crypto.Cipher import AES
import pygetwindow

from colorama import init
init(autoreset=True) #set this True to print color fonts in the console

def UI_AT_Close(mark=""):
    for winx in pygetwindow.getAllWindows():
        #<Win32Window left="-7", top="-7", width="2575", height="1407", title="tmp6.py - Visual Studio Code [Administrator]">
        if winx.title and re.match(r'.*AT\-Convertor\s+\d+\.*\d*', str(winx.title), re.I):
            try:       
                print("\n#AU from {}#".format(mark),  sys._getframe().f_lineno, "close window:", winx, "\n")
                winx.close()
            except:
                print("#AU from {}#".format(mark),  sys._getframe().f_lineno, traceback.format_exc())
            break

def UI_ChangeBackgroud(event=None, e=None, color=""):
    if e and color:
        e.config(bg=color)

def UI_WidgetBalloon(wid, msg, title=""):
    if title:
        return Tooltip(wid, title, msg)
    else:
        return Tooltip(wid, "Tip", msg, showheader=False)

def UI_WidgetRectGET(widget=None):
    rect = []
    if widget:        
        try:
            rect = win32gui.GetWindowRect(widget.winfo_id())
            #left top right bottom (18, 78, 522, 382)
        except:
            print(traceback.format_exc())

    return rect

def UI_WinGeometry(mainWin=None, p='+0+0',fromx=''):
    #relocate main window
    try:
        #UT_Print2Log('', sys._getframe().f_lineno, 'WmainWin geometry:', p, fromx)
        mainWin.geometry(p)
    except:
        print('red', sys._getframe().f_lineno, traceback.format_exc())

def UI_WinWidgetRemove(wid=None, act=1):
    try:
        for item in wid.winfo_children():
            #print('', "-"*act,item)
            if item.winfo_children():
                UI_WinWidgetRemove(wid=item,act=act+1)
            try:
                item.destroy()
            except:
                pass
    except:
        pass

def UT_number_0_format(num, xlen=2):
    if len(str(num)) >= xlen:
        return str(num)
    else:
        return '0'*(xlen - len(str(num))) + str(num)

def UT_MD5_VerifyCode(instring):
    my_md5 = UT_GetMD5(instring)
    return my_md5[0] + my_md5[-1] + my_md5[int(len(my_md5)/2)] + my_md5[int(len(my_md5)/4)]

def UT_GetMD5(instring):
    #GetMD5
    return str(hashlib.md5(instring.encode(encoding='UTF-8',errors='strict')).hexdigest()).upper()

def UT_HandlerAdaptor(fun,**kwds):
    """
    #let button click event carry parameters
    #sample: 
    canvas.bind('<Button-1>',func=UN_HandlerAdaptor(MeetingUIClosed,tl=tl))
    def MeetingUIClosed(event=None, tl=None):
        try:
            tl.destroy()
        except:
            pass
    """
    return lambda event,fun=fun,kwds=kwds:fun(event,**kwds) 
import webbrowser
def UT_OpenLink(event=None, link=None):
    UT_Print2Log('blue', "\n#AU#", sys._getframe().f_lineno,'... open link: ' + link)
    webbrowser.open_new_tab(link)

def UT_CryptMe(instring,key=None,isEncript=True):    
    #CryptMe    
    #fdata['string'] = 'ILOVEU'
    #fdata['key']    = 'DF11-FB15-B7B2-15AB-47B7-7AC4-C6F9-5EFE'
    if not len(str(instring)):
        if isEncript:
            return b''
        else:
            return ''

    fdata = {}
    unit = "characters"
    fdata['string'] = instring
    fdata['size'] = len(fdata['string'])
    fdata['sizeZ']= 0
    fdata['rateC']= 'NA'
    fdata['key'] = key
    fdata['data'] = ''
    try:
        if isEncript:
            #UT_Print2Log('', "#AU#", "\n\t.. Encrypt ..."); 
            data_tmp = zlib.compress(fdata['string'].encode(encoding='UTF-8',errors='ignore'))       
            if(data_tmp):         
                ckey = re.sub(r'-','',fdata['key']); 
                #UT_Print2Log('',  "#AU#","\t\tEncrypted:\n\t\t-- KEY: "+ fdata['key']) 

                cryptor = AES.new(ckey.encode('utf-8'),AES.MODE_CBC,str(ckey[0:16]).encode('utf-8'))                       
                fdata['data'] = base64.b64encode(cryptor.encrypt(UT_PadText(data_tmp))); 
                
                #UT_Print2Log('',  "#AU#","\t\t-- KEYSIZE: "+str(len(ckey))+"\n\t\t-- BLOCKSIZE: "+str(AES.block_size)+"\n\t\t-- IV: "+ckey[0:16])
            
                fdata['sizeZ']= len(fdata['data'])
                if(fdata['sizeZ']):
                    fdata['rateC'] = "{:0.2f}".format(fdata['size']/fdata['sizeZ'])
            else:
                UT_Print2Log('red',  "#AU#", sys._getframe().f_lineno, "\t.. Failed to compress!\n")        
            
            #UT_Print2Log('',  "#AU#", "\t.. Compressed: before size="+str(fdata['size'])+" "+unit+", after size="+str(fdata['sizeZ'])+", compressed rate "+str(fdata['rateC'])+"\n") dhkaads
        else:
            #UT_Print2Log('',  "#AU#", "\n\t.. Decrypt ..."); 
            ckey = re.sub(r'-','',fdata['key']); 
            cryptor = AES.new(ckey.encode('utf-8'),AES.MODE_CBC,str(ckey[0:16]).encode('utf-8'))  
            data_tmp = cryptor.decrypt(base64.b64decode(fdata['string'])); 
            fdata['data'] = zlib.decompress(data_tmp).decode(encoding='UTF-8',errors='ignore') 
    except:
        UT_Print2Log('red', "#AU#", sys._getframe().f_lineno, traceback.format_exc())

    #UT_Print2Log('', 'In: ',instring,'\nout: ',fdata['data'],'\n')
    return fdata['data']

def UT_PadText(s):
    '''Pad an input string according to PKCS#7''' #
    BS = AES.block_size
    return s + (BS - len(s) % BS) * chr(BS - len(s) % BS).encode("utf-8")

def UI_WidgetEntryShow(event=None,e=None, ishow='', code=''):
    try:
        #UT_Print2Log('yellow', "#AU#",  sys._getframe().f_lineno, e, ishow, code)
        if ishow =='close':
            e.grid_remove()
        elif ishow == 'decrypt':
            if code:
                val_e = e.get()
                if re.match(r'^\$\$', val_e):
                    val_e = re.sub(r"^\$\$", '', val_e)               
                    val_e = UT_CryptMe(val_e.encode(),key=UT_GetMD5(code), isEncript=False)
                    if val_e:
                        e.delete(0,"end")
                        e.insert(0, val_e)
        else:
            e.config(show=ishow)
    except:
        UT_Print2Log('red', "#AU#",  sys._getframe().f_lineno, traceback.format_exc())
    
def UT_JsonFileRead(filepath= ""):
    try:
        if filepath:
            return json.loads(UT_FileOpen(filepath, format='string'))
        else:
            UT_Print2Log('red',  "#AU#", sys._getframe().f_lineno, "File path is invalid!!")
    except:
        UT_Print2Log('red', "#AU#",  sys._getframe().f_lineno, traceback.format_exc())
    
    return None

def UT_JsonFileSave(filepath= "", fdata=None):
    try:       
        UT_FileSave(json.dumps(fdata, cls=NumpyEncoder),filepath, format='string')
    except:
        UT_Print2Log('red', "#AU#",  sys._getframe().f_lineno, traceback.format_exc())

def UT_FileOpen(filepath, format='bytes'):    
    UT_Print2Log('', "#AU#",  "\t.... Open file:",filepath)
    try:
        if os.path.exists(filepath):  
            if format == 'bytes': 
                buffer = b''   
                with open(filepath,'rb') as f:   
                    buffer = f.read()   
                    f.close()
                return buffer
            else:
                buffer = ''   
                with open(filepath,'r',encoding="utf-8") as f:   
                    buffer = f.read()   
                    f.close()
                return buffer
        else:
            UT_Print2Log('red', "#AU#",  sys._getframe().f_lineno, "File path is not existing!!")
    except:
        UT_Print2Log('red', "#AU#",  sys._getframe().f_lineno, traceback.format_exc())   

def UT_FileSave(data,filepath, format='bytes'):    
    #UT_Print2Log('', "#AU#",  "\t.... Save to file:",filepath)
    try:
        if os.path.exists(filepath):       
            os.unlink(filepath) 

        if format == 'bytes':    
            with open(filepath,'wb+') as f:   
                f.write(data)
        else:
            with open(filepath,'w+',encoding="utf-8") as f:  
            #important to have encoding="utf-8", to prevent Window opens the file as encoding="gbk" or else encoding then cause error.
                f.write(str(data))            
    except:
        UT_Print2Log('red', "#AU#",  sys._getframe().f_lineno, traceback.format_exc())    

def UT_FolderCreate(folder):
    if not folder:
        return False

    if not os.path.exists(folder):
        os.makedirs(folder)
        if not os.path.exists(folder):
            UT_Print2Log('red', "#AU#",  sys._getframe().f_lineno, "Can not create the folder:\n\t" + folder)
            return False
    return True

def UT_Print2Log(*args):
    ss = []
    for i in range(1,len(args)):
        obj = args[i]
        if(type(obj) == np.ndarray) or type(obj) == tuple or type(obj) == list or type(obj) == dict:
            ss.append(json.dumps(str(obj)))
        else:
            ss.append(str(obj))

    icolor = UT_PrintInColor(icolor=args[0], text= '\t'.join(ss))

def UT_PrintInColor(icolor="", text=""):
    pcolor = ''
    if icolor:
        if icolor=='black':
            pcolor = '\033[0;30;40m'
        elif icolor=='red':
            pcolor = '\033[0;31;40m'
        elif icolor=='green':
            pcolor = '\033[0;32;40m'
        elif icolor=='yellow':
            pcolor = '\033[0;33;40m'
        elif icolor=='blue':
            pcolor = '\033[0;34;40m'
        elif icolor=='carmine' or icolor=='#FF33CC':
            pcolor = '\033[0;35;40m'
        elif icolor=='#00CCFF':
            pcolor = '\033[0;36;40m'
        elif icolor=='white':
            pcolor = '\033[0;37;40m'
    else:
        icolor = "#606060"
        pcolor = '\033[0;37;40m'

    #显示方式: 0（默认\）、1（高亮）、22（非粗体）、4（下划线）、24（非下划线）、 5（闪烁）、25（非闪烁）、7（反显）、27（非反显）
    #前景色:   30（黑色）、31（红色）、32（绿色）、 33（黄色）、34（蓝色）、35（洋 红）、36（青色）、37（白色）
    #背景色:   40（黑色）、41（红色）、42（绿色）、 43（黄色）、44（蓝色）、45（洋 红）、46（青色）、47（白色）

    print(pcolor + text + '\033[0m')
    return icolor

def UT_Str2Int(s):
    x = re.sub(r'[^\d\.]+', '', str(s))
    if len(x):
        return int(x)
    else:
        return 0

def UT_GetColors(istart=16711680, n=10):
    colors = []
    a = np.linspace(istart,255,n)
    #UT_Print2Log('', sys._getframe().f_lineno, a)
    for i in a:
        c = int(i)
        colors.append('#%06x'%c)
    #UT_Print2Log('', sys._getframe().f_lineno, colors)
    return colors

def GetColorsHex(n):
    cs = GetColorsRGB(n)
    csx = []
    for c in cs:
        x = ColorRGB_to_Hex(re.sub(r'rgb\(|\)', '', c))
        csx.append(x)
    
    return csx

def GetColorsRGB(n):
    e = {}
    cs = []
    R = 255
    G = 0
    B = 0
    for i in range(n):            
        while (IsKeyExist(e,[str(R)+"_"+str(G)+"_"+str(B)]) or (R==255 and G==255 and B==255)):
            R = random.randint(0,255)
            G = random.randint(0,255)
            B = random.randint(0,255)  

        e[str(R)+"_"+str(G)+"_"+str(B)] = 1     
        cs.append("rgb("+str(R)+","+str(G)+","+str(B)+")")     
        R = random.randint(0,255)
        G = random.randint(0,255)
        B = random.randint(0,255)  
    return cs  

def ColorRGB_to_Hex(rgb):
    RGB = []
    if type(rgb) == list:
        RGB = rgb
    else:
        RGB = rgb.split(',')
    color = '#'
    for i in RGB:
       num = int(i)
       color += str(hex(num))[-2:].replace('x', '0').upper()
    #print(color)
    return color

def IsKeyExist(dictx,keys):
    t = 1
    while len(keys):
        key = keys.pop(0)                             
        if not dictx.__contains__(key): 
            t = 0
            break
        else:
            dictx = dictx[key]
            
    return t

def usedTime(stime,t=0):
    if not t:
        t = time.time() - stime

    tt={'h':'00','m':'00','s':'00'}
    
    if t > 3600:
        h = int(t/3600)
        tt['h'] = "{:0>2d}".format(h)
        t = t - h*3600
       
    if t > 60:
        m = int(t/60)
        tt['m'] = "{:0>2d}".format(m)
        t = t - m*60

    if t > 0:
        tt['s'] = "{:0>6.3f}".format(t)

    return tt['h'] + ':' + tt['m'] + ':' + tt['s'] 

def OpenNew(f, to_language, audio_file_format, convert_engine, EncryptCode):
    options=[to_language, audio_file_format, convert_engine, EncryptCode]
    cmd = ""
    xfile = str("".join(f))
    if re.match(r'.*\.py$', xfile, re.I):
        cmd = "python " + xfile + " "+ " ".join(options)
    else:
        cmd = xfile + " " + " ".join(options)
    
    #print("\n\n#AU#",  sys._getframe().f_lineno, "cmd=\"" + cmd + "\"", ", f=",f, ', options=', options)
    try:
        os.system(cmd)
    except:
        print("\n", traceback.format_exc())

def Progress(i, n, stime, x="",lastTime=0, to_print=False):                        
    if n > 0:
        leftt = ", est.left 00:00:00.000"  
        speed = ""      
        dt = 0
        if lastTime:
            dt = time.time() - lastTime
        else:
            dt = time.time() - stime

        speed = int(dt / i * 1000000) / 1000
        if speed > 1000:
            speed = str(int(speed / 10)/100) + " s/unit"
        else:
            speed = str(speed) + " ms/unit"

        if i > 0 and n - i > 0:                                  
            left = dt / i * (n - i)  
            leftt = ", est.left " + usedTime(0,left)

        total_dots = 20
        dots_num = int((i/n)*total_dots)
        if dots_num > total_dots:
            dots_num = total_dots
        
        pstr = "\r\t"+ x +"["+("."*dots_num)+(" "*(total_dots - dots_num))+"] " + str(i) + "/" + str(n) + ", {:0>2.1f}".format(i/n*100) + "%, speed "+ speed +", used " + usedTime(stime) + leftt + "    "
        if i==n or to_print:
            print(pstr, end='')
        else:
            print(pstr, end='')
            sys.stdout.flush()