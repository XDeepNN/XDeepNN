import signal
import time
from tkinter import *
from tkinter.filedialog import (askopenfilename,askdirectory)
from tkinter import scrolledtext
import subprocess, os, threading
import pandas as pd
import psutil
import XT_config
class XtracerWindow(Frame):
    def __init__(self, master=None):
        Frame.__init__(self, master)
        self.master.title('Xtracer')
        self.config = XT_config.config()
        self.configdata = self.config.data
        self.selectFile = StringVar()
        self.selectFile.set(self.configdata['baseConf']['under_detection_filepath'])
        self.featureFile = StringVar()
        self.featureFile.set(self.configdata['baseConf']['feature_savepath'])
        self.selectSimulator = StringVar()
        self.selectSimulator.set(self.configdata['baseConf']['simulator_filepath'])
        self.width = 900
        self.height = 600
        self.master.geometry('%dx%d+%d+%d' % (self.width, self.height, (self.winfo_screenwidth() - self.width) / 2,
                                              (self.winfo_screenheight() - self.height) / 2))
        self.master.resizable(width=False, height=False)
        self.pack()
        self.title, self.list = getStableAPI()
        self.traceLog = scrolledtext.ScrolledText(self, width=120, height=24, state='disabled')
        self.monitor = scrolledtext.ScrolledText(self, width=66, height=14, state='disabled')
        self.traceLogThread = threading.Thread(target=listenMSG, args=(logwriter(self.traceLog), 'python Xtracer.py',))
        self.traceLogThread.setDaemon(True)
        self.monitorThread = threading.Thread(target=listenMSG, args=(logwriter(self.monitor), 'python XT_checker.py',))
        self.apiHookNum = IntVar()
        self.hookAPIList = []
        self.initHookAPI()
        self.chooseAPIText = StringVar()
        self.customAPIselectText = StringVar()
        self.customAPIselectText.set('')
        self.customBlackAPIselectText = StringVar()
        self.customBlackAPIselectText.set('')
        self.apibuttonCheckList = []
        self.customAPICheck = BooleanVar()
        self.blackAPICheck = BooleanVar()
        self.createItem()
    def createItem(self):
        selectFileRow = 0
        Label(self, text="Detection folder:").grid(row=selectFileRow, column=0)
        Entry(self, textvariable=self.selectFile, width=34, state='readonly').grid(
            row=selectFileRow,
            column=1, columnspan=2)
        Button(self, text='Choose folder', command=self.select_apkfile).grid(row=selectFileRow, column=3)
        featrueFileRow = 1
        Label(self, text="Feature storage path:").grid(row=featrueFileRow, column=0)
        Entry(self, textvariable=self.featureFile, width=34, state='readonly').grid(
            row=featrueFileRow,
            column=1, columnspan=2)
        Button(self, text='Choose folder', command=self.select_featurefile).grid(row=featrueFileRow,
                                                                        column=3)
        selectSimulatorRow = 2
        Label(self, text="Simulator Path:").grid(row=selectSimulatorRow, column=0)
        Entry(self, textvariable=self.selectSimulator, width=34, state='readonly').grid(
            row=selectSimulatorRow,
            column=1, columnspan=2)
        Button(self, text='Choose folder', command=self.select_simulator).grid(
            row=selectSimulatorRow, column=3)
        hookAPInumFrame = Frame(self)
        Label(hookAPInumFrame, text="Number of APIs for hook：").grid(row=0, column=0)
        Label(hookAPInumFrame, textvariable=self.apiHookNum).grid(row=0, column=1)
        hookAPInumFrame.grid(row=3, column=0, columnspan=2)
        Button(self, text="Start detection", command=self.startTrace).grid(row=4, column=0)
        Button(self, text="Select the APIs that require Hook", command=self.select_Hook_API).grid(row=4, column=1)
        Button(self, text="Stop detection", command=self.stopTrace).grid(row=4, column=3)
        Label(self, text="Simulator status:").grid(row=0, column=4, sticky=W, padx=10, pady=4)
        self.monitor.grid(row=1, column=4, rowspan=4, padx=14)
        Label(self, text="Test log:").grid(row=5, column=0, sticky=W, padx=10, pady=4)
        self.traceLog.grid(row=6, column=0, columnspan=5)
    def select_apkfile(self):
        path = askdirectory(title='Select the APK storage folder')
        if path:
            self.selectFile.set(path)
            self.configdata['baseConf']['under_detection_filepath'] = path
            self.config.saveData()
    def select_featurefile(self):
        path = askdirectory(title='Select feature storage folder')
        if path:
            self.featureFile.set(path)
            self.configdata['baseConf']['feature_savepath'] = path
            self.config.saveData()
    def select_simulator(self):
        path = askopenfilename(title='Select Simulator Path', filetypes=[('exe', '*.exe')])
        if path:
            self.selectSimulator.set(path)
            self.configdata['baseConf']['simulator_filepath'] = path
            self.config.saveData()
    def checkTrace(self):
        timecount = 0
        while True:
            timecount += 1
            if timecount % 300 == 0:
                timecount = 0
                TracerControl()
            print('traceLogThread:', self.traceLogThread.is_alive())
            if not self.traceLogThread.is_alive():
                self.traceLogThread = threading.Thread(target=listenMSG,
                                                       args=(logwriter(self.traceLog), 'python Xtracer.py',))
                self.traceLogThread.setDaemon(True)
                self.traceLogThread.start()
            print("----------------- timecount:" + str(timecount) + " -------------------")
            time.sleep(5)

    def startTrace(self):
        if not self.traceLogThread.is_alive():
            logwriter(self.traceLog).write('waiting for device...')
            self.traceLogThread = threading.Thread(target=listenMSG,
                                                   args=(logwriter(self.traceLog), 'python Xtracer.py',))
            self.traceLogThread.setDaemon(True)
            self.traceLogThread.start()

        if not self.monitorThread.is_alive():
            logwriter(self.monitor).write('device starting')
            self.monitorThread = threading.Thread(target=listenMSG,
                                                  args=(logwriter(self.monitor), 'python XT_checker.py',))
            self.monitorThread.start()
        threading.Thread(target=self.checkTrace).start()
    def stopTrace(self):
        print('stop')
    def initHookAPI(self):
        selectList = self.configdata['hookconf_api']['selectAPI_list']
        self.apiHookNum.set(2)
        mainlist = pd.read_csv('source/API-HookList.csv', header=0)
        lists = []
        blackList = []
        indexlist = {}
        for select in selectList:
            if selectList[select]:
                if select == 'restricted_API':
                    indexlist['Restricted API'] = 1
                if select == 'highCorrelation_API':
                    indexlist['Highly-Correlation API'] = 1
                if select == 'sensitiveOperation_API':
                    indexlist['Sensitive Operation API'] = 1
                if select == 'union_API':
                    indexlist['Union'] = 1
                customList = self.configdata['hookconf_api']['customAPI_list']
                if select == 'custom_list' and customList:
                    for item in customList:
                        lists.append(item)
                if select == 'black_list' and self.configdata['hookconf_api']['blackAPI_list']:
                    blackList = self.configdata['hookconf_api']['blackAPI_list']
        for head in indexlist:
            for item in mainlist[head]:
                if not 'nan' in str(item):
                    lists.append(item.replace(' ', '/'))
        lists = list(set(lists))
        if blackList:
            for item in blackList:
                lists.remove(item)
        self.apiHookNum.set(len(lists))
        self.hookAPIList = lists
    def select_Hook_API(self):
        self.master.wm_attributes('-topmost', 0)
        self.APIwindow = Toplevel(self.master)
        self.APIwindow.title('Select the APIs that require hook')
        APIwindow_width = 1000
        APIwindow_height = 600
        self.APIwindow.geometry('%dx%d+%d+%d' % (
            APIwindow_width, APIwindow_height, (self.winfo_screenwidth() - APIwindow_width) / 2,
            (self.winfo_screenheight() - APIwindow_height) / 2))
        self.APIwindow.resizable(width=False, height=False)
        self.APIwindow.focus_set()
        self.searchAPIFrame = Frame(self.APIwindow)
        self.searchAPI = Entry(self.searchAPIFrame, width=46).grid(row=0, column=0)
        Button(self.searchAPIFrame, text="Query API").grid(row=0, column=1)
        self.searchAPIFrame.grid(row=2, column=0, columnspan=2)
        self.loadedAPI = None
        self.changeAPIList(0)
        for index, item in enumerate(self.title):
            self.apibuttonCheckList.append(BooleanVar())
            buttonFrame = Frame(self.APIwindow)
            # Button(buttonFrame, text=item, command=lambda i=index: self.changeAPIList(i), width=30).grid(row=0,
            #                                                                                              column=0)
            # Checkbutton(buttonFrame, variable=self.apibuttonCheckList[index], command=self.updateCheck).grid(row=0,
            #                                                                                                  column=1)
            buttonFrame.grid(row=int(index / 2) + 1, column=int(index % 2))
        self.initChooseCheck()
        chooseAPIFrame = Frame(self.APIwindow)
        # Label(chooseAPIFrame, text='目前已选择的api组：', justify=LEFT, anchor=W).grid(row=0, column=0)
        # Label(chooseAPIFrame, textvariable=self.chooseAPIText, width=40, height=2, justify='left', wraplength=300).grid(
        #     row=0, column=1)
        chooseAPIFrame.grid(row=3, column=0, columnspan=2)
        self.customAPIchooseFrame = Frame(self.APIwindow)
        Label(self.customAPIchooseFrame, text='Additional API-list').grid(row=0, column=0)
        # Checkbutton(self.customAPIchooseFrame, variable=self.customAPICheck, command=self.updateCheck).grid(row=0,
        #                                                                                                     column=1)
        self.customAPIchooseFrame.grid(row=5, column=0)
        self.customAPI = Listbox(self.APIwindow, height=20, width=36, selectmode=SINGLE, exportselection=False)
        self.customAPI.bind('<<ListboxSelect>>', self.whiteListClickEvent)
        customAPIlist = self.configdata['hookconf_api']['customAPI_list']
        if customAPIlist:
            for index, api in enumerate(customAPIlist):
                self.customAPI.insert(index, ' ' + api)
        self.customAPI.grid(row=6, column=0, padx=2)
        self.customAPIFrame = Frame(self.APIwindow)
        self.customAPIAddEntry = Entry(self.customAPIFrame, textvariable=self.customAPIselectText, width=26)
        self.customAPIAddEntry.grid(row=0, column=0)
        Button(self.customAPIFrame, text="add",
               command=lambda text=self.customAPIselectText, conf_name='customAPI_list',
                              list=self.customAPI: self.addAPI(text, conf_name, list)).grid(row=0, column=1)
        Button(self.customAPIFrame, text="del",
               command=lambda text=self.customAPIselectText, conf_name='customAPI_list',
                              list=self.customAPI: self.delAPI(text, conf_name, list)).grid(row=0, column=2)
        self.customAPIFrame.grid(row=7, column=0)
        self.customBlackAPIchooseFrame = Frame(self.APIwindow)
        Label(self.customBlackAPIchooseFrame, text='Black API-list').grid(row=0, column=0)
        # Checkbutton(self.customBlackAPIchooseFrame, variable=self.blackAPICheck, command=self.updateCheck).grid(row=0,
        #                                                                                                         column=1)
        self.customBlackAPIchooseFrame.grid(row=5, column=1)
        self.customBlackAPI = Listbox(self.APIwindow, height=20, width=36, selectmode=SINGLE, exportselection=False)
        self.customBlackAPI.bind('<<ListboxSelect>>', self.blackListClickEvent)
        customBlackAPIlist = self.configdata['hookconf_api']['blackAPI_list']
        if customBlackAPIlist:
            for index, api in enumerate(customBlackAPIlist):
                self.customBlackAPI.insert(index, ' ' + api)
        self.customBlackAPI.grid(row=6, column=1, padx=2)
        self.customBlackAPIFrame = Frame(self.APIwindow)
        self.customBlackAPIAddEntry = Entry(self.customBlackAPIFrame, textvariable=self.customBlackAPIselectText,
                                            width=26)
        self.customBlackAPIAddEntry.grid(row=0, column=0)
        Button(self.customBlackAPIFrame, text="add",
               command=lambda text=self.customBlackAPIselectText, conf_name='blackAPI_list',
                              list=self.customBlackAPI: self.addAPI(text, conf_name, list)).grid(row=0, column=1)
        Button(self.customBlackAPIFrame, text="del",
               command=lambda text=self.customBlackAPIselectText, conf_name='blackAPI_list',
                              list=self.customBlackAPI: self.delAPI(text, conf_name, list)).grid(row=0, column=2)
        self.customBlackAPIFrame.grid(row=7, column=1)
        self.master.attributes('-disabled', True)
        self.master.wait_window(self.APIwindow)
        self.master.protocol("WM_DELETE_WINDOW", self.master.attributes('-disabled', False))
        self.master.wm_attributes('-topmost', 1)
        self.initHookAPI()
        self.master.focus_set()
    def changeAPIList(self, index):
        if self.loadedAPI != None:
            self.loadedAPI.grid_forget()
            self.loadedAPILabel.grid_forget()
        for index1, item in enumerate(self.title):
            if index == index1:
                self.loadedAPI = Listbox(self.APIwindow, height=30, width=60, selectmode=SINGLE, exportselection=False)
                self.loadedAPI.bind('<<ListboxSelect>>', self.blackListClickEvent)
                self.loadedAPILabel = Label(self.APIwindow, text=item)
                self.loadedAPILabel.grid(row=0, column=2)
                for index2, api in enumerate(self.list[item]):
                    self.loadedAPI.insert(index2, ' ' + api)
                self.loadedAPI.grid(row=1, column=2, padx=2, rowspan=10)
    def addAPI(self, insertText, confName, targetList):
        insertAPI = str(insertText.get()).strip()
        if str(insertText.get()) == '':
            return
        APIlist = self.configdata['hookconf_api'][confName]
        for api in APIlist:
            if api.strip() == insertAPI:
                return
        targetList.insert("end", ' ' + insertAPI)
        APIlist.append(insertAPI)
        self.configdata['hookconf_api'][confName] = APIlist
        self.config.saveData()
    def delAPI(self, insertText, confName, targetList):
        insertAPI = str(insertText.get()).strip()
        APIlist = self.configdata['hookconf_api'][confName]
        for index, api in enumerate(APIlist):
            if api.strip() == insertAPI:
                targetList.delete(index)
                APIlist.remove(insertAPI)
                self.configdata['hookconf_api'][confName] = APIlist
                self.config.saveData()
    def blackListClickEvent(self, event):
        widget = event.widget
        if widget.curselection():
            selection_value = widget.get(widget.curselection()[0])
            self.customBlackAPIselectText.set(selection_value)
        else:
            self.customBlackAPIselectText.set('')
    def whiteListClickEvent(self, event):
        widget = event.widget
        if widget.curselection():
            selection_value = widget.get(widget.curselection()[0])
            self.customAPIselectText.set(selection_value)
        else:
            self.customAPIselectText.set('')
    def initChooseCheck(self):
        list = self.configdata['hookconf_api']['selectAPI_list']
        for item in list:
            if list[item]:
                if item == 'black_list':
                    self.blackAPICheck.set(True)
                if item == 'custom_list':
                    self.customAPICheck.set(True)
                if item == 'restricted_API':
                    self.apibuttonCheckList[0].set(True)
                if item == 'highCorrelation_API':
                    self.apibuttonCheckList[1].set(True)
                if item == 'sensitiveOperation_API':
                    self.apibuttonCheckList[2].set(True)
                if item == 'union_API':
                    self.apibuttonCheckList[3].set(True)
        self.updateCheck()
    def updateCheck(self):
        str = ''
        list = self.configdata['hookconf_api']['selectAPI_list']
        if self.blackAPICheck.get():
            list['black_list'] = True
        else:
            list['black_list'] = False
        if self.customAPICheck.get():
            list['custom_list'] = True
        else:
            list['custom_list'] = False
        for index, item in enumerate(self.apibuttonCheckList):
            if index == 0 and item.get():
                list['restricted_API'] = True
            elif index == 0 and not item.get():
                list['restricted_API'] = False
            if index == 1 and item.get():
                list['highCorrelation_API'] = True
            elif index == 1 and not item.get():
                list['highCorrelation_API'] = False
            if index == 2 and item.get():
                list['sensitiveOperation_API'] = True
            elif index == 2 and not item.get():
                list['sensitiveOperation_API'] = False
            if index == 3 and item.get():
                list['union_API'] = True
            elif index == 3 and not item.get():
                list['union_API'] = False
        for item in list:
            if list[item]:
                str += ' ' + item + ','
        self.chooseAPIText.set(str)
        self.configdata['hookconf_api']['selectAPI_list'] = list
        self.config.saveData()
class logwriter(object):
    def __init__(self, widget):
        self.widget = widget

    def write(self, string):
        self.widget.configure(state='normal')
        self.widget.insert('end', string + '\n')
        self.widget.see('end')
        self.widget.configure(state='disabled')
def sleeptime(hour, min, sec):
    return hour * 3600 + min * 60 + sec
def TracerControl():
    with open('tmp\Tracer.pid', 'r') as f:
        data = int(f.read())
        for pid in psutil.pids():
            if pid == data:
                os.kill(pid, signal.SIGTERM)
def listenMSG(room, shell_cmd):
    p = subprocess.Popen(shell_cmd, shell=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding='utf-8')
    while p.poll() is None:
        line = p.stdout.readline()
        line = line.strip()
        room.write(line)
def getStableAPI():
    file = pd.read_csv('source/API-HookList.csv', header=0)
    title = []
    list = {}
    for header in file:
        title.append(header)
        list[header] = []
    return title, list
if __name__ == '__main__':
    ct = XtracerWindow()
    ct.mainloop()