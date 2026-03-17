#!/usr/bin/env python3
"""
RGDS Bottom-Screen Virtual Keyboard v4
=======================================
Phone-style touch keyboard for Anbernic RG DS / ROCKNIX.
Renders on DSI-1 (bottom screen), injects keystrokes via uinput.

v4: Phone layout, key repeat, auto-survive app launches, visual polish.
"""

import ctypes, struct, fcntl, os, sys, threading, time, select, signal, subprocess, atexit

TOUCH_DEVICE = "/dev/input/event2"
JOYPAD_DEVICE = "/dev/input/event6"
W, H = 640, 480
BTN_THUMBR = 318
TITLE = "RGDS Keyboard [Bottom]"
REASSERT_INTERVAL = 1.5
REPEAT_DELAY = 0.4
REPEAT_RATE = 0.05
REPEATABLE = {'bksp','space','up','down','left','right','del','bksp2','bksp3'}

C_BG=(15,15,25,255);C_KEY_LET=(48,52,82,255);C_KEY_LET_H=(58,63,98,255)
C_KEY=(38,40,62,255);C_KEY_SP=(30,32,50,255);C_KEY_ACT=(65,50,90,255)
C_PRESS=(220,65,85,255);C_TEXT=(215,220,235,255);C_TEXT_SP=(130,170,245,255)
C_TEXT_NUM=(180,185,200,255);C_BORDER=(55,58,88,255);C_BLACK=(0,0,0,255)
C_DIVIDER=(25,25,40,255)
GAP=3

F={
'A':(0x0E,0x11,0x11,0x1F,0x11,0x11,0x11),'B':(0x1E,0x11,0x11,0x1E,0x11,0x11,0x1E),
'C':(0x0E,0x11,0x10,0x10,0x10,0x11,0x0E),'D':(0x1E,0x11,0x11,0x11,0x11,0x11,0x1E),
'E':(0x1F,0x10,0x10,0x1E,0x10,0x10,0x1F),'F':(0x1F,0x10,0x10,0x1E,0x10,0x10,0x10),
'G':(0x0E,0x11,0x10,0x17,0x11,0x11,0x0E),'H':(0x11,0x11,0x11,0x1F,0x11,0x11,0x11),
'I':(0x0E,0x04,0x04,0x04,0x04,0x04,0x0E),'J':(0x07,0x02,0x02,0x02,0x02,0x12,0x0C),
'K':(0x11,0x12,0x14,0x18,0x14,0x12,0x11),'L':(0x10,0x10,0x10,0x10,0x10,0x10,0x1F),
'M':(0x11,0x1B,0x15,0x15,0x11,0x11,0x11),'N':(0x11,0x19,0x15,0x13,0x11,0x11,0x11),
'O':(0x0E,0x11,0x11,0x11,0x11,0x11,0x0E),'P':(0x1E,0x11,0x11,0x1E,0x10,0x10,0x10),
'Q':(0x0E,0x11,0x11,0x11,0x15,0x12,0x0D),'R':(0x1E,0x11,0x11,0x1E,0x14,0x12,0x11),
'S':(0x0E,0x11,0x10,0x0E,0x01,0x11,0x0E),'T':(0x1F,0x04,0x04,0x04,0x04,0x04,0x04),
'U':(0x11,0x11,0x11,0x11,0x11,0x11,0x0E),'V':(0x11,0x11,0x11,0x11,0x0A,0x0A,0x04),
'W':(0x11,0x11,0x11,0x15,0x15,0x1B,0x11),'X':(0x11,0x11,0x0A,0x04,0x0A,0x11,0x11),
'Y':(0x11,0x11,0x0A,0x04,0x04,0x04,0x04),'Z':(0x1F,0x01,0x02,0x04,0x08,0x10,0x1F),
'0':(0x0E,0x11,0x13,0x15,0x19,0x11,0x0E),'1':(0x04,0x0C,0x04,0x04,0x04,0x04,0x0E),
'2':(0x0E,0x11,0x01,0x06,0x08,0x10,0x1F),'3':(0x0E,0x11,0x01,0x06,0x01,0x11,0x0E),
'4':(0x02,0x06,0x0A,0x12,0x1F,0x02,0x02),'5':(0x1F,0x10,0x1E,0x01,0x01,0x11,0x0E),
'6':(0x06,0x08,0x10,0x1E,0x11,0x11,0x0E),'7':(0x1F,0x01,0x02,0x04,0x08,0x08,0x08),
'8':(0x0E,0x11,0x11,0x0E,0x11,0x11,0x0E),'9':(0x0E,0x11,0x11,0x0F,0x01,0x02,0x0C),
' ':(0,0,0,0,0,0,0),'.':(0,0,0,0,0,0x0C,0x0C),',':(0,0,0,0,4,4,8),
'!':(4,4,4,4,4,0,4),'?':(0x0E,0x11,1,2,4,0,4),
'-':(0,0,0,0x1F,0,0,0),'_':(0,0,0,0,0,0,0x1F),
'+':(0,4,4,0x1F,4,4,0),'=':(0,0,0x1F,0,0x1F,0,0),
'@':(0x0E,0x11,0x17,0x15,0x17,0x10,0x0E),'#':(0x0A,0x0A,0x1F,0x0A,0x1F,0x0A,0x0A),
'$':(4,0x0F,0x14,0x0E,5,0x1E,4),'%':(0x18,0x19,2,4,8,0x13,3),
'&':(8,0x14,0x14,8,0x15,0x12,0x0D),'*':(0,4,0x15,0x0E,0x15,4,0),
'(':(2,4,8,8,8,4,2),')':(8,4,2,2,2,4,8),
'[':(0x0E,8,8,8,8,8,0x0E),']':(0x0E,2,2,2,2,2,0x0E),
'{':(6,8,8,0x10,8,8,6),'}':(0x0C,2,2,1,2,2,0x0C),
'/':(1,1,2,4,8,0x10,0x10),'\\':(0x10,0x10,8,4,2,1,1),
'|':(4,4,4,4,4,4,4),':':(0,0x0C,0x0C,0,0x0C,0x0C,0),
';':(0,0x0C,0x0C,0,4,4,8),"'":(4,4,8,0,0,0,0),
'"':(0x0A,0x0A,0x14,0,0,0,0),'`':(8,4,2,0,0,0,0),
'~':(0,0,8,0x15,2,0,0),'<':(2,4,8,0x10,8,4,2),
'>':(8,4,2,1,2,4,8),'^':(4,0x0A,0x11,0,0,0,0),
'\u2190':(0,4,8,0x1F,8,4,0),'\u2192':(0,4,2,0x1F,2,4,0),
'\u2191':(4,0x0E,0x15,4,4,4,0),'\u2193':(0,4,4,4,0x15,0x0E,4),
'\u232B':(0,0x11,0x0A,0x04,0x0A,0x11,0),
}

EVF='llHHi';EVS=struct.calcsize(EVF)
EV_SYN=0;EV_KEY=1;EV_ABS=3
ABS_MT_X=0x35;ABS_MT_Y=0x36;ABS_MT_ID=0x39;BTN_TOUCH=330
EVIOCGRAB=0x40044590;UI_SEVBIT=0x40045564;UI_SKEYBIT=0x40045565
UI_CREATE=0x5501;UI_DESTROY=0x5502

KEY_ESC=1;KEY_1=2;KEY_2=3;KEY_3=4;KEY_4=5;KEY_5=6;KEY_6=7;KEY_7=8;KEY_8=9
KEY_9=10;KEY_0=11;KEY_MINUS=12;KEY_EQUAL=13;KEY_BACKSPACE=14;KEY_TAB=15
KEY_Q=16;KEY_W=17;KEY_E=18;KEY_R=19;KEY_T=20;KEY_Y=21;KEY_U=22;KEY_I=23
KEY_O=24;KEY_P=25;KEY_LEFTBRACE=26;KEY_RIGHTBRACE=27;KEY_ENTER=28
KEY_LEFTCTRL=29;KEY_A=30;KEY_S=31;KEY_D=32;KEY_F=33;KEY_G=34;KEY_H=35
KEY_J=36;KEY_K=37;KEY_L=38;KEY_SEMICOLON=39;KEY_APOSTROPHE=40;KEY_GRAVE=41
KEY_LEFTSHIFT=42;KEY_BACKSLASH=43;KEY_Z=44;KEY_X=45;KEY_C=46;KEY_V=47
KEY_B=48;KEY_N=49;KEY_M=50;KEY_COMMA=51;KEY_DOT=52;KEY_SLASH=53
KEY_LEFTALT=56;KEY_SPACE=57;KEY_LEFT=105;KEY_RIGHT=106;KEY_UP=103
KEY_DOWN=108;KEY_HOME=102;KEY_END=107;KEY_DELETE=111;KEY_INSERT=110

ALL_KC=[KEY_ESC,KEY_1,KEY_2,KEY_3,KEY_4,KEY_5,KEY_6,KEY_7,KEY_8,KEY_9,KEY_0,
KEY_MINUS,KEY_EQUAL,KEY_BACKSPACE,KEY_TAB,KEY_Q,KEY_W,KEY_E,KEY_R,KEY_T,
KEY_Y,KEY_U,KEY_I,KEY_O,KEY_P,KEY_LEFTBRACE,KEY_RIGHTBRACE,KEY_ENTER,
KEY_LEFTCTRL,KEY_A,KEY_S,KEY_D,KEY_F,KEY_G,KEY_H,KEY_J,KEY_K,KEY_L,
KEY_SEMICOLON,KEY_APOSTROPHE,KEY_GRAVE,KEY_LEFTSHIFT,KEY_BACKSLASH,
KEY_Z,KEY_X,KEY_C,KEY_V,KEY_B,KEY_N,KEY_M,KEY_COMMA,KEY_DOT,KEY_SLASH,
KEY_LEFTALT,KEY_SPACE,KEY_LEFT,KEY_RIGHT,KEY_UP,KEY_DOWN,KEY_HOME,KEY_END,
KEY_DELETE,KEY_INSERT]

_grabbed=[]
def _cleanup():
    for fd in _grabbed:
        try:fcntl.ioctl(fd,EVIOCGRAB,0)
        except:pass
atexit.register(_cleanup)

class SDL:
    def __init__(self):
        self.lib=ctypes.CDLL('libSDL2-2.0.so.0')
        class R(ctypes.Structure):
            _fields_=[("x",ctypes.c_int),("y",ctypes.c_int),("w",ctypes.c_int),("h",ctypes.c_int)]
        self.Rect=R
        class E(ctypes.Union):
            _fields_=[("type",ctypes.c_uint32),("pad",ctypes.c_uint8*56)]
        self.Ev=E
        self.lib.SDL_Init.restype=ctypes.c_int
        self.lib.SDL_CreateWindow.restype=ctypes.c_void_p
        self.lib.SDL_CreateRenderer.restype=ctypes.c_void_p
        self.lib.SDL_PollEvent.restype=ctypes.c_int
        self.lib.SDL_GetError.restype=ctypes.c_char_p
        self.lib.SDL_SetHint.argtypes=[ctypes.c_char_p,ctypes.c_char_p]
        self.lib.SDL_GetCurrentVideoDriver.restype=ctypes.c_char_p
    def init(self):return self.lib.SDL_Init(0x20|0x4000)
    def mkwin(self,t,x,y,w,h,f):return self.lib.SDL_CreateWindow(t.encode(),x,y,w,h,f)
    def mkren(self,w,i,f):return self.lib.SDL_CreateRenderer(w,i,f)
    def color(self,r,cr,cg,cb,ca):self.lib.SDL_SetRenderDrawColor(r,cr,cg,cb,ca)
    def clr(self,r):self.lib.SDL_RenderClear(r)
    def frect(self,r,x,y,w,h):
        rc=self.Rect(int(x),int(y),int(w),int(h));self.lib.SDL_RenderFillRect(r,ctypes.byref(rc))
    def drect(self,r,x,y,w,h):
        rc=self.Rect(int(x),int(y),int(w),int(h));self.lib.SDL_RenderDrawRect(r,ctypes.byref(rc))
    def flip(self,r):self.lib.SDL_RenderPresent(r)
    def poll(self):
        e=self.Ev();return e if self.lib.SDL_PollEvent(ctypes.byref(e)) else None
    def dren(self,r):self.lib.SDL_DestroyRenderer(r)
    def dwin(self,w):self.lib.SDL_DestroyWindow(w)
    def quit(self):self.lib.SDL_Quit()
    def wait(self,ms):self.lib.SDL_Delay(ms)

class VKB:
    def __init__(self):self.fd=None
    def setup(self):
        self.fd=os.open("/dev/uinput",os.O_WRONLY|os.O_NONBLOCK)
        fcntl.ioctl(self.fd,UI_SEVBIT,EV_KEY)
        for c in ALL_KC:fcntl.ioctl(self.fd,UI_SKEYBIT,c)
        name=b"RGDS Virtual Keyboard\0"+b"\0"*58
        dev=name+struct.pack('HHHHi',3,0x1234,0x5678,1,0)+b"\0"*(64*4*4)
        os.write(self.fd,dev);fcntl.ioctl(self.fd,UI_CREATE);time.sleep(0.3)
        print("[uinput] OK")
    def emit(self,et,code,val):
        t=int(time.time());us=int((time.time()%1)*1e6)
        os.write(self.fd,struct.pack(EVF,t,us,et,code,val))
    def press(self,code,shift=False):
        if shift:self.emit(EV_KEY,KEY_LEFTSHIFT,1);self.emit(EV_SYN,0,0)
        self.emit(EV_KEY,code,1);self.emit(EV_SYN,0,0)
        self.emit(EV_KEY,code,0);self.emit(EV_SYN,0,0)
        if shift:self.emit(EV_KEY,KEY_LEFTSHIFT,0);self.emit(EV_SYN,0,0)
    def close(self):
        if self.fd:
            try:fcntl.ioctl(self.fd,UI_DESTROY)
            except:pass
            os.close(self.fd);self.fd=None

class Touch:
    def __init__(self,path):
        self.path=path;self.fd=None;self.grabbed=False
        self.tx=-1;self.ty=-1;self.evts=[];self.lock=threading.Lock()
    def open(self):
        self.fd=os.open(self.path,os.O_RDONLY|os.O_NONBLOCK);print("[touch] Opened")
    def grab(self):
        if self.fd and not self.grabbed:
            try:fcntl.ioctl(self.fd,EVIOCGRAB,1);self.grabbed=True;_grabbed.append(self.fd);print("[touch] Grabbed")
            except OSError as e:print(f"[touch] Grab fail: {e}")
    def ungrab(self):
        if self.fd and self.grabbed:
            try:fcntl.ioctl(self.fd,EVIOCGRAB,0)
            except:pass
            self.grabbed=False
            if self.fd in _grabbed:_grabbed.remove(self.fd)
            print("[touch] Released")
    def read(self):
        if not self.fd:return
        try:data=os.read(self.fd,EVS*32)
        except OSError:return
        off=0;nd=False;nu=False
        while off+EVS<=len(data):
            _,_,et,code,val=struct.unpack_from(EVF,data,off);off+=EVS
            if et==EV_ABS:
                if code==ABS_MT_X:self.tx=val
                elif code==ABS_MT_Y:self.ty=val
                elif code==ABS_MT_ID:
                    if val>=0:nd=True
                    else:nu=True
            elif et==EV_KEY and code==BTN_TOUCH:nd=val==1;nu=val==0
            elif et==EV_SYN:
                with self.lock:
                    if nd and self.tx>=0:self.evts.append(('d',self.tx,self.ty));nd=False
                    if nu:self.evts.append(('u',self.tx,self.ty));nu=False
    def get(self):
        with self.lock:e=self.evts[:];self.evts.clear()
        return e
    def close(self):
        self.ungrab()
        if self.fd:os.close(self.fd);self.fd=None

class Joy(threading.Thread):
    def __init__(self,path,btn,cb):
        super().__init__(daemon=True);self.path=path;self.btn=btn;self.cb=cb;self.on=True
    def run(self):
        try:fd=os.open(self.path,os.O_RDONLY|os.O_NONBLOCK)
        except:print("[joy] Can't open");return
        print("[joy] R3 monitor active")
        while self.on:
            try:
                r,_,_=select.select([fd],[],[],0.5)
                if not r:continue
                data=os.read(fd,EVS*16);off=0
                while off+EVS<=len(data):
                    _,_,et,code,val=struct.unpack_from(EVF,data,off);off+=EVS
                    if et==EV_KEY and code==self.btn and val==1:self.cb()
            except OSError:time.sleep(0.1)
        os.close(fd)

def sway(cmd):
    try:subprocess.run(['swaymsg',cmd],capture_output=True,timeout=2)
    except:pass

def place():
    sway('output DSI-1 power on')
    sway(f'[title="{TITLE}"] move to output DSI-1')
    sway(f'[title="{TITLE}"] fullscreen enable')

# =============================================================================
# Layouts
# =============================================================================

def build():
    L={}

    # MAIN: phone-style
    main={'name':'main','rows':[
        {'y':0,'h':95,'keys':[
            {'l':'q','d':'Q','c':KEY_Q,'s':False,'w':1},{'l':'w','d':'W','c':KEY_W,'s':False,'w':1},
            {'l':'e','d':'E','c':KEY_E,'s':False,'w':1},{'l':'r','d':'R','c':KEY_R,'s':False,'w':1},
            {'l':'t','d':'T','c':KEY_T,'s':False,'w':1},{'l':'y','d':'Y','c':KEY_Y,'s':False,'w':1},
            {'l':'u','d':'U','c':KEY_U,'s':False,'w':1},{'l':'i','d':'I','c':KEY_I,'s':False,'w':1},
            {'l':'o','d':'O','c':KEY_O,'s':False,'w':1},{'l':'p','d':'P','c':KEY_P,'s':False,'w':1},
        ]},
        {'y':98,'h':95,'keys':[
            {'l':'a','d':'A','c':KEY_A,'s':False,'w':1},{'l':'s2','d':'S','c':KEY_S,'s':False,'w':1},
            {'l':'d2','d':'D','c':KEY_D,'s':False,'w':1},{'l':'f','d':'F','c':KEY_F,'s':False,'w':1},
            {'l':'g','d':'G','c':KEY_G,'s':False,'w':1},{'l':'h','d':'H','c':KEY_H,'s':False,'w':1},
            {'l':'j','d':'J','c':KEY_J,'s':False,'w':1},{'l':'k','d':'K','c':KEY_K,'s':False,'w':1},
            {'l':'l2','d':'L','c':KEY_L,'s':False,'w':1},
        ]},
        # SHIFT Z X C V B N M BKSP
        {'y':196,'h':95,'keys':[
            {'l':'shift','d':'SHIFT','c':None,'s':False,'w':1.4,'a':'shift'},
            {'l':'z','d':'Z','c':KEY_Z,'s':False,'w':1},{'l':'x','d':'X','c':KEY_X,'s':False,'w':1},
            {'l':'c2','d':'C','c':KEY_C,'s':False,'w':1},{'l':'v','d':'V','c':KEY_V,'s':False,'w':1},
            {'l':'b','d':'B','c':KEY_B,'s':False,'w':1},{'l':'n','d':'N','c':KEY_N,'s':False,'w':1},
            {'l':'m','d':'M','c':KEY_M,'s':False,'w':1},
            {'l':'bksp','d':'\u232B','c':KEY_BACKSPACE,'s':False,'w':1.4},
        ]},
        # Utility row with centered space
        {'y':294,'h':75,'keys':[
            {'l':'sym','d':'#+','c':None,'s':False,'w':1.2,'a':'symbols'},
            {'l':'comma','d':',','c':KEY_COMMA,'s':False,'w':0.8},
            {'l':'space','d':'SPACE','c':KEY_SPACE,'s':False,'w':4.5},
            {'l':'dot','d':'.','c':KEY_DOT,'s':False,'w':0.8},
            {'l':'enter','d':'RET','c':KEY_ENTER,'s':False,'w':1.2},
        ]},
        # Numbers
        {'y':372,'h':50,'keys':[
            {'l':'1','d':'1','c':KEY_1,'s':False,'w':1},{'l':'2','d':'2','c':KEY_2,'s':False,'w':1},
            {'l':'3','d':'3','c':KEY_3,'s':False,'w':1},{'l':'4','d':'4','c':KEY_4,'s':False,'w':1},
            {'l':'5','d':'5','c':KEY_5,'s':False,'w':1},{'l':'6','d':'6','c':KEY_6,'s':False,'w':1},
            {'l':'7','d':'7','c':KEY_7,'s':False,'w':1},{'l':'8','d':'8','c':KEY_8,'s':False,'w':1},
            {'l':'9','d':'9','c':KEY_9,'s':False,'w':1},{'l':'0','d':'0','c':KEY_0,'s':False,'w':1},
        ]},
        # Small utility
        {'y':425,'h':52,'keys':[
            {'l':'tab','d':'TAB','c':KEY_TAB,'s':False,'w':1},
            {'l':'esc','d':'ESC','c':KEY_ESC,'s':False,'w':1},
            {'l':'nav','d':'NAV','c':None,'s':False,'w':1,'a':'nav'},
            {'l':'dash','d':'-','c':KEY_MINUS,'s':False,'w':0.8},
            {'l':'qmark','d':'?','c':KEY_SLASH,'s':True,'w':0.8},
            {'l':'excl','d':'!','c':KEY_1,'s':True,'w':0.8},
            {'l':'at','d':'@','c':KEY_2,'s':True,'w':0.8},
        ]},
    ]}
    L['main']=main

    # SHIFT
    shift={'name':'shift','rows':[]}
    for row in main['rows'][:2]:
        shift['rows'].append({'y':row['y'],'h':row['h'],'keys':[{**k,'s':True} for k in row['keys']]})
    sr2={'y':196,'h':95,'keys':[]}
    for k in main['rows'][2]['keys']:
        nk=dict(k)
        if nk['l']=='shift':nk['a']='unshift'
        elif nk['c'] and nk['l']!='bksp':nk['s']=True
        sr2['keys'].append(nk)
    shift['rows'].append(sr2)
    # Shifted utility row
    shift['rows'].append({'y':294,'h':75,'keys':[
        {'l':'sym','d':'#+','c':None,'s':False,'w':1.2,'a':'symbols'},
        {'l':'semi','d':';','c':KEY_SEMICOLON,'s':False,'w':0.8},
        {'l':'space','d':'SPACE','c':KEY_SPACE,'s':False,'w':4.5},
        {'l':'colon','d':':','c':KEY_SEMICOLON,'s':True,'w':0.8},
        {'l':'enter','d':'RET','c':KEY_ENTER,'s':False,'w':1.2},
    ]})
    sd=['!','@','#','$','%','^','&','*','(',')']
    shift['rows'].append({'y':372,'h':50,'keys':[
        {**dict(k),'d':sd[i],'s':True} for i,k in enumerate(main['rows'][4]['keys'])
    ]})
    shift['rows'].append({'y':425,'h':52,'keys':[
        {'l':'tab','d':'TAB','c':KEY_TAB,'s':False,'w':1},
        {'l':'esc','d':'ESC','c':KEY_ESC,'s':False,'w':1},
        {'l':'nav','d':'NAV','c':None,'s':False,'w':1,'a':'nav'},
        {'l':'under','d':'_','c':KEY_MINUS,'s':True,'w':0.8},
        {'l':'apos','d':"'",'c':KEY_APOSTROPHE,'s':False,'w':0.8},
        {'l':'quot','d':'"','c':KEY_APOSTROPHE,'s':True,'w':0.8},
        {'l':'hash','d':'#','c':KEY_3,'s':True,'w':0.8},
    ]})
    L['shift']=shift

    # SYMBOLS
    sd2=[[('!',KEY_1,True),('@',KEY_2,True),('#',KEY_3,True),('$',KEY_4,True),('%',KEY_5,True),('^',KEY_6,True),('&',KEY_7,True),('*',KEY_8,True),('(',KEY_9,True),(')',KEY_0,True)],
         [('-',KEY_MINUS,False),('_',KEY_MINUS,True),('+',KEY_EQUAL,True),('=',KEY_EQUAL,False),('[',KEY_LEFTBRACE,False),(']',KEY_RIGHTBRACE,False),('{',KEY_LEFTBRACE,True),('}',KEY_RIGHTBRACE,True),('|',KEY_BACKSLASH,True),('\\',KEY_BACKSLASH,False)],
         [(':',KEY_SEMICOLON,True),(';',KEY_SEMICOLON,False),("'",KEY_APOSTROPHE,False),('"',KEY_APOSTROPHE,True),('`',KEY_GRAVE,False),('~',KEY_GRAVE,True),('<',KEY_COMMA,True),('>',KEY_DOT,True),('/',KEY_SLASH,False),('?',KEY_SLASH,True)]]
    sym={'name':'symbols','rows':[]}
    for ri,keys in enumerate(sd2):
        sym['rows'].append({'y':[0,98,196][ri],'h':95,'keys':[{'l':d,'d':d,'c':c,'s':s,'w':1} for d,c,s in keys]})
    sym['rows'].append({'y':294,'h':75,'keys':[
        {'l':'abc','d':'ABC','c':None,'s':False,'w':1.5,'a':'main'},
        {'l':'space','d':'SPACE','c':KEY_SPACE,'s':False,'w':4.0},
        {'l':'bksp2','d':'\u232B','c':KEY_BACKSPACE,'s':False,'w':1.5},
        {'l':'enter2','d':'RET','c':KEY_ENTER,'s':False,'w':1.5},
    ]})
    sym['rows'].append(dict(main['rows'][4]))
    sym['rows'].append({'y':425,'h':52,'keys':[
        {'l':'tab','d':'TAB','c':KEY_TAB,'s':False,'w':1},
        {'l':'esc','d':'ESC','c':KEY_ESC,'s':False,'w':1},
        {'l':'nav','d':'NAV','c':None,'s':False,'w':1,'a':'nav'},
    ]})
    L['symbols']=sym

    # NAV
    L['nav']={'name':'nav','rows':[
        {'y':0,'h':120,'keys':[
            {'l':'home','d':'HOME','c':KEY_HOME,'s':False,'w':1},{'l':'up','d':'\u2191','c':KEY_UP,'s':False,'w':1},
            {'l':'end','d':'END','c':KEY_END,'s':False,'w':1},{'l':'del','d':'DEL','c':KEY_DELETE,'s':False,'w':1}]},
        {'y':123,'h':120,'keys':[
            {'l':'left','d':'\u2190','c':KEY_LEFT,'s':False,'w':1},{'l':'down','d':'\u2193','c':KEY_DOWN,'s':False,'w':1},
            {'l':'right','d':'\u2192','c':KEY_RIGHT,'s':False,'w':1},{'l':'ins','d':'INS','c':KEY_INSERT,'s':False,'w':1}]},
        {'y':246,'h':100,'keys':[
            {'l':'tab2','d':'TAB','c':KEY_TAB,'s':False,'w':1},{'l':'esc2','d':'ESC','c':KEY_ESC,'s':False,'w':1},
            {'l':'bksp3','d':'BKSP','c':KEY_BACKSPACE,'s':False,'w':1},{'l':'enter3','d':'RET','c':KEY_ENTER,'s':False,'w':1}]},
        {'y':349,'h':68,'keys':[
            {'l':'space','d':'SPACE','c':KEY_SPACE,'s':False,'w':3},
            {'l':'abc2','d':'ABC','c':None,'s':False,'w':1,'a':'main'},
            {'l':'sym2','d':'#+','c':None,'s':False,'w':1,'a':'symbols'}]},
        {'y':420,'h':57,'keys':[
            {'l':'1','d':'1','c':KEY_1,'s':False,'w':1},{'l':'2','d':'2','c':KEY_2,'s':False,'w':1},
            {'l':'3','d':'3','c':KEY_3,'s':False,'w':1},{'l':'4','d':'4','c':KEY_4,'s':False,'w':1},
            {'l':'5','d':'5','c':KEY_5,'s':False,'w':1},{'l':'6','d':'6','c':KEY_6,'s':False,'w':1},
            {'l':'7','d':'7','c':KEY_7,'s':False,'w':1},{'l':'8','d':'8','c':KEY_8,'s':False,'w':1},
            {'l':'9','d':'9','c':KEY_9,'s':False,'w':1},{'l':'0','d':'0','c':KEY_0,'s':False,'w':1}]},
    ]}
    return L

def crects(layout):
    rows=[]
    for row in layout['rows']:
        y=row['y'];h=row['h'];keys=row['keys']
        total=sum(k['w'] for k in keys);avail=W-2*GAP-GAP*(len(keys)-1);unit=avail/total
        comp=[];cx=GAP
        for k in keys:kw=int(k['w']*unit);comp.append({**k,'rect':(int(cx),y+1,kw,h-2)});cx+=kw+GAP
        if comp:l=comp[-1];rx,ry,rw,rh=l['rect'];l['rect']=(rx,ry,W-GAP-rx,rh)
        rows.append(comp)
    return rows

def dc(s,r,ch,cx,cy,sc,col):
    g=F.get(ch.upper(),F.get(ch))
    if not g:return
    s.color(r,*col)
    for ri,bits in enumerate(g):
        for ci in range(5):
            if bits&(1<<(4-ci)):s.frect(r,cx+ci*sc,cy+ri*sc,sc,sc)

def dt(s,r,text,cx,cy,sc,col):
    for i,ch in enumerate(text):dc(s,r,ch,cx+i*(5*sc+sc),cy,sc,col)

def ms(text,sc):return len(text)*(5*sc+sc)-sc if text else 0

def dk(s,r,key,pressed=False,sa=False):
    x,y,w,h=key['rect']
    il=(key['c'] is not None and not key.get('a') and len(key['d'])==1 and key['d'].isalpha())
    isp=bool(key.get('a'));isn=(key['c'] is not None and not key.get('a') and len(key['d'])==1 and key['d'].isdigit())
    ish=key.get('a') in('shift','unshift')

    bg=C_PRESS if pressed else(C_KEY_ACT if ish and sa else(C_KEY_LET if il else(C_KEY_SP if isp else C_KEY)))
    s.color(r,*bg);s.frect(r,x,y,w,h)
    if il and not pressed:s.color(r,*C_KEY_LET_H);s.frect(r,x+1,y+1,w-2,2)
    s.color(r,*C_BORDER);s.drect(r,x,y,w,h)

    d=key['d'];tc=C_TEXT_SP if(isp or ish)else(C_TEXT_NUM if isn else C_TEXT)
    sc=5 if(il and len(d)==1)else(4 if len(d)==1 else(3 if len(d)<=3 else 2))
    tw=ms(d,sc);th=7*sc
    dt(s,r,d,x+(w-tw)//2,y+(h-th)//2,sc,tc)

def dkb(s,r,rows,pressed=None,sa=False):
    s.color(r,*C_BG);s.clr(r)
    for row in rows:
        if row:s.color(r,*C_DIVIDER);s.frect(r,0,row[0]['rect'][1]-1,W,1)
    for row in rows:
        for k in row:dk(s,r,k,pressed=(pressed and k['l']==pressed),sa=sa)
    s.flip(r)

def dblk(s,r):s.color(r,*C_BLACK);s.clr(r);s.flip(r)

def main():
    os.environ['SDL_VIDEODRIVER']='wayland'
    s=SDL()
    if s.init()!=0:print("[sdl] fail");sys.exit(1)
    sway('output DSI-1 power on');time.sleep(0.2)
    win=s.mkwin(TITLE,0x1FFF0000,0x1FFF0000,W,H,0x04)
    ren=s.mkren(win,-1,0x06)
    s.color(ren,30,30,50,255);s.clr(ren);s.flip(ren)
    time.sleep(0.5);place();time.sleep(0.3);dblk(s,ren)

    layouts=build();rects={n:crects(l) for n,l in layouts.items()}
    vkb=VKB();vkb.setup()
    touch=Touch(TOUCH_DEVICE);touch.open()

    vis=False;run=True;layer='main'
    pr=None;prk=None;pt=0;sa=False;ss=False
    tf=False;dirty=True;lr=0;la=time.time()

    def on_t():nonlocal tf;tf=True
    def stop(sig,f):nonlocal run;run=False
    signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)

    joy=Joy(JOYPAD_DEVICE,BTN_THUMBR,on_t);joy.start()
    print("[app] Running — R3 to toggle")

    try:
        while run:
            now=time.time()
            while True:
                ev=s.poll()
                if not ev:break

            if tf:
                tf=False;vis=not vis
                if vis:touch.grab();dirty=True;print("[app] Shown")
                else:
                    touch.ungrab();layer='main';sa=False;ss=False;pr=None;prk=None
                    dblk(s,ren);print("[app] Hidden")

            if vis and now-la>REASSERT_INTERVAL:place();la=now

            if not vis:s.wait(50);continue

            touch.read()
            for et,tx,ty in touch.get():
                if et=='d':
                    for row in rects[layer]:
                        for k in row:
                            x,y,w,h=k['rect']
                            if x<=tx<=x+w and y<=ty<=y+h:pr=k['l'];prk=k;pt=now;lr=0;dirty=True
                elif et=='u':
                    if pr and prk:
                        hit=None
                        for row in rects[layer]:
                            for k in row:
                                x,y,w,h=k['rect']
                                if x<=tx<=x+w and y<=ty<=y+h:hit=k
                        if hit and hit['l']==pr:
                            a=hit.get('a')
                            if a=='shift':layer='shift';ss=True;sa=True
                            elif a=='unshift':layer='main';ss=False;sa=False
                            elif a in('symbols','main','nav'):layer=a;ss=False;sa=False
                            elif hit['c']:
                                if hit['l'] not in REPEATABLE or lr==0:
                                    vkb.press(hit['c'],shift=hit.get('s',False))
                                if layer=='shift' and ss and len(hit['d'])==1 and hit['d'].isalpha():
                                    layer='main';ss=False;sa=False
                    pr=None;prk=None;dirty=True

            if pr and prk and prk['l'] in REPEATABLE and prk['c']:
                if now-pt>REPEAT_DELAY:
                    if lr==0 or now-lr>REPEAT_RATE:
                        vkb.press(prk['c'],shift=prk.get('s',False));lr=now

            if dirty:dkb(s,ren,rects[layer],pr,sa=sa);dirty=False
            s.wait(16)
    except KeyboardInterrupt:print("\n[app] Interrupted")
    finally:joy.on=False;touch.close();vkb.close();s.dren(ren);s.dwin(win);s.quit();print("[app] Done")

if __name__=='__main__':main()
