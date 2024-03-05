import ctypes
import inspect
import json
import sys
import threading
import time
import frida, os
import subprocess
import shutil
import pandas as pd
from copy import copy
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import XT_config
config = XT_config.config()
sys.setrecursionlimit(5000)
hook_mode = 'mult'
featurePath = config.data['baseConf']['feature_savepath']
featureAPIPath = featurePath + r'\api'
apkPath_0 = r'E:\benign'
apkPath_1 = r'E:\malice'
chooseApkPath = config.data['baseConf']['under_detection_filepath']
APP = None
scripts = []
device = None
loadingAPK = ''
packageName = ''
application_label = ''
hookComplete = 'false'
hookSuccess = False
successHook = 0
def getHookAPI():
    path = 'API-Set.csv'
    file = pd.read_csv(path, header=0)
    list = []
    for header in file:
        if not 'Union' in header:
            for item in file[header]:
                if not 'nan' in str(item):
                    item = item.replace(' ', '/')
                    list.append(item)
    return list
hookApi = []
class TraceItem(QStandardItem):
    def __init__(self, clazz, method, args, parent_item, retval=None, *__args):
        self.method = method
        self.args = args
        self.retval = retval
        self.clazz = clazz
        self.parent_item = parent_item
        super(TraceItem, self).__init__(str(self), *__args)
        self.parent_item.appendRow(self)
    def __str__(self):
        s = '{}.{}'.format(self.clazz, self.method)
        return s
    def set_retval(self, retval):
        self.retval = retval
class XtracerWindow(QMainWindow):
    app = None
    def __init__(self, app):
        super(XtracerWindow, self).__init__()
        self.app = app
    def stop(self):
        global scripts
        for s in copy(scripts):
            try:
                s.unload()
            except frida.InvalidOperationError as e:
                print(e)
                scripts.remove(s)
            else:
                scripts.remove(s)
        printNor('[G] success unload script')
    def clean(self):
        self.app.thread_map = {}
    def export(self):
        global loadingAPK, hookSuccess
        print(loadingAPK)
        api = loadingAPK.split('/')[-1].split('.apk')[0]
        featureFilePath = featureAPIPath + loadingAPK.split('/')[-1].split('\\')[0]
        if not os.path.exists(featureFilePath):
            os.makedirs(featureFilePath)
        jobfile = featureAPIPath + api + '.txt'
        tree = {}
        for tid in list(self.app.thread_map):
            tree[self.app.thread_map[tid]['list'][0].text()] = gen_tree(self.app.thread_map[tid]['list'][0])
        apiList = []
        for thread in tree:
            for clazz in tree[thread]:
                api = clazz['clazz'] + '/' + clazz['method']
                apiList.append(api.split('(')[0])
        count_dist = dict()
        for i in apiList:
            if i in count_dist:
                count_dist[i] += 1
            else:
                count_dist[i] = 1
        temp = str(count_dist)
        if temp != '{}':
            f = open(jobfile, 'w')
            f.write(temp)
            hookSuccess = True
        printNor('[G] success get jsonLog')
class Xtracer:
    def __init__(self, ):
        global APP
        APP = self
        self.app = QApplication(sys.argv)
        self.window = XtracerWindow(self)
        self.thread_map = {}
        if 'single' in hook_mode:
            singleTrace(chooseApkPath, self)
        elif 'mult' in hook_mode:
            multTrace(chooseApkPath, self)
        sys.exit()
    def method_entry(self, tid, tname, clazz, method, args):
        if tid not in self.thread_map:
            tItem = QStandardItem('{} - {}'.format(tid, tname))
            self.thread_map[tid] = {
                'current': tItem,
                'list': [tItem]
            }
        item = TraceItem(clazz, method, args, parent_item=self.thread_map[tid]['current'])
        self.thread_map[tid]['current'] = item
        self.thread_map[tid]['list'].append(item)
    def method_exit(self, tid, retval):
        self.thread_map[tid]['current'].set_retval(retval)
        self.thread_map[tid]['current'] = self.thread_map[tid]['current'].parent()
    def log(self, text):
        text = time.strftime('%Y-%m-%d %H:%M:%S:  [*] ', time.localtime(time.time())) + text
        printNor(text)
def start_trace():
    global scripts, device, hookComplete, successHook
    global application_label, packageName
    successHook = 0
    def _attach(pid):
        failcount = 0
        if not device:
            return
        try:
            session = device.attach(pid)
            session.enable_child_gating()
            source = open('Xtracer.js', 'r', encoding='utf-8').read().replace('{hookList}', str(hookApi))
            script = session.create_script(source)
            script.on("message", FridaReceive)
            script.load()
            scripts.append(script)
            return True
        except frida.ProcessNotFoundError:
            printNor('[E] fail find process: ' + str(pid))
            return
        except frida.NotSupportedError as e:
            printNor('[E] NotSupportedError:' + str(e))
            return
        except frida.TransportError as e:
            printNor('[E] TransportError:' + str(e))
            if 'timeout was reached' in str(e):
                return
            failcount += 1
            if failcount > 5:
                printRed('[E] fail connect')
                return
    def _on_child_added(child):
        print('[E] hook process_child:', child)
        _attach(child.pid)
    device = frida.get_usb_device()
    device.on("child-added", _on_child_added)
    for process in device.enumerate_processes():
        if packageName in process.name or application_label in process.name:
            print('[E] hook process:', process)
            if _attach(process.pid):
                successHook += 1
    time.sleep(10)
    if successHook == 0:
        printNor('hook process failed')
        hookComplete = 'fail'
        return
def put_tree(app, tid, tname, item):
    app.method_entry(tid, tname, item['clazz'], item['method'], item['args'])
    for child in item['child']:
        put_tree(app, tid, tname, child)
    app.method_exit(tid, item['retval'])
def gen_tree(item):
    if isinstance(item, TraceItem):
        res = {}
        res['clazz'] = item.clazz
        res['method'] = item.method
        res['args'] = item.args
        res['child'] = []
        for i in range(item.rowCount()):
            res['child'].append(gen_tree(item.child(i)))
        res['retval'] = item.retval
    elif isinstance(item, QStandardItem):
        res = []
        for i in range(item.rowCount()):
            res.append(gen_tree(item.child(i)))
    else:
        res = []
    return res
def FridaReceive(message, data):
    global hookComplete
    if message['type'] == 'send':
        if message['payload'][:11] == 'CxTracer:::':
            packet = json.loads(message['payload'][11:])
            cmd = packet['cmd']
            data = packet['data']
            if cmd == 'log':
                if 'Complete.' in data:
                    hookComplete = 'true'
            elif cmd == 'enter':
                tid, tName, cls, method, args = data
                APP.method_entry(tid, tName, cls, method, args)
            elif cmd == 'exit':
                tid, retval = data
                APP.method_exit(tid, retval)
    else:
        printNor(message['stack'])
def getApkPath(path):
    apkPaths = []
    for root, dirs, files in os.walk(path):
        for file in files:
            if '.apk' in file:
                apkPath = path + '\\' + file
                apkPaths.append(apkPath)
    return apkPaths
def getPackageLabel():
    command = 'aapt dump badging ' + loadingAPK + '| findstr application-label:'
    adbReturn = subprocess.run(command, shell=True, stdout=subprocess.PIPE, encoding="utf-8").stdout
    if 'application-label' in adbReturn:
        labelName = adbReturn.split("application-label:'")[1].split("'")[0]
        printNor('[B] labelName: ' + labelName)
        return labelName
def getPackageName():
    command = 'aapt dump badging ' + loadingAPK + '| findstr package'
    adbReturn = subprocess.run(command, shell=True, stdout=subprocess.PIPE, encoding="utf-8").stdout
    if 'package: name' in adbReturn:
        packageName = adbReturn.split("package: name='")[1].split("' versionCode")[0]
        printNor('[B] packageName: ' + packageName)
        return packageName
    else:
        print('[B] fail get packageName--adbReturn:', adbReturn)
        printRed('[B] fail get packageName--apkPath:' + loadingAPK)
        return None
def getPackageActivity():
    command = 'aapt dump badging ' + loadingAPK + '| findstr activity'
    adbReturn = subprocess.run(command, shell=True, stdout=subprocess.PIPE, encoding="utf-8").stdout
    if 'activity: name' in adbReturn:
        activityName = adbReturn.split("activity: name='")[1].split("'  label")[0]
        printNor('[B] mainActivityName: ' + activityName)
        return activityName
    else:
        print('[B] fail get activityName-w:', adbReturn)
        printRed('[B] fail get activityName--apkPath:' + loadingAPK)
        return None
def apkInstall():
    printNor('[C] ------------------ APK installing -----------------')
    command = 'adb install -r ' + loadingAPK
    proc = subprocess.Popen(command, shell=False, stdout=subprocess.PIPE)
    try:
        adbReturn = proc.communicate(180)
        for readLine in adbReturn:
            if 'Success' in str(readLine):
                printNor('[C] APK install success')
                return True
        return False
    except:
        printRed('[C] APK install fail--apkPath:' + loadingAPK)
        return False
def runApk(packageName, packageActivity):
    printNor('[D] ------------------ APK running --------------------')
    command = 'adb shell am start -W -n ' + packageName + '/' + packageActivity
    proc = subprocess.Popen(command, shell=False, stdout=subprocess.PIPE)
    try:
        adbReturn = proc.communicate(timeout=60)
        if 'Complete' in str(adbReturn):
            printNor('[D] start running')
            proc.kill()
            time.sleep(2)
            return True
    except subprocess.TimeoutExpired:
        proc.kill()
        printRed('[D] fail run--TimeoutExpired')
        printRed('[D] fail run--apkPath:' + loadingAPK)
        return False
def runTrace():
    printNor('[E] ------------------ hooking ------------------------')
    global hookComplete
    threading.Thread(target=start_trace).start()
    while True:
        if 'true' in hookComplete:
            printNor('[E] success hook')
            hookComplete = 'false'
            return True
        if 'fail' in hookComplete:
            printNor('[E] fail hook')
            hookComplete = 'false'
            return False
        time.sleep(1)
def runMonkey(packageName):
    printNor('[F] ------------------ monkey running -----------------')
    command = 'adb shell CLASSPATH=/sdcard/monkey.jar:/sdcard/framework.jar exec app_process /system/bin tv.panda.test.monkey.Monkey -p ' + packageName + ' --uiautomatormix --pct-reset 0 --pct-rotation 0 --running-minutes 2 -v'
    proc = subprocess.Popen(command, shell=False, stdout=subprocess.PIPE)
    try:
        adbReturn = proc.communicate(timeout=300)
        for readline in adbReturn:
            if ' Monkey finished' in str(readline):
                printNor('[F] success monkey')
                return
    except subprocess.TimeoutExpired:
        printRed('[F] fail run monkey--apkPath:' + loadingAPK)
def getJsonLog(self):
    printNor('[G] ------------------ get jsonLog --------------------')
    self.window.export()
def stopApk(packageName):
    printNor('[H] ------------------ app stopping -------------------')
    command = 'adb shell pm clear ' + packageName
    proc = subprocess.Popen(command, shell=False, stdout=subprocess.PIPE)
    try:
        adbReturn = proc.communicate(timeout=120)
        if 'Success' in str(adbReturn):
            printNor('[H] success stopping')
            return
    except:
        printRed('[H] fail stop--apkPath:' + loadingAPK)
def apkUninstall(packageName):
    printNor('[I] ------------------ uninstalling -------------------')
    command = 'adb uninstall ' + packageName
    proc = subprocess.Popen(command, shell=False, stdout=subprocess.PIPE)
    try:
        adbReturn = proc.communicate(timeout=120)
        for readLine in adbReturn:
            if 'Success' in str(readLine):
                printNor('[I] uninstalled')
                return
    except subprocess.TimeoutExpired:
        print('[I] fail uninstall')
        printRed('[I] fail uninstall--apkPath:' + loadingAPK)
def printRed(message):
    print("\033[1;31;48m" + message + "\033[0m")
def printNor(message):
    print(message)
def get_path():
    p = os.path.split(os.path.realpath(__file__))
    p = p[0] + r'\tmp\Tracer.pid'
    print(p)
    return p
def onsignal_term():
    print('STOPPED')
def appTrace(apkPath, self):
    printNor('[A] apkPath:' + str(apkPath))
    global packageName, hookSuccess, application_label
    application_label = getPackageLabel()
    packageName = getPackageName()
    packageActivity = getPackageActivity()
    fpath, fname = os.path.split(apkPath)
    if not os.path.exists(chooseApkPath + '_fail'):
        os.makedirs(chooseApkPath + '_fail')
    if not os.path.exists(chooseApkPath + '_success'):
        os.makedirs(chooseApkPath + '_success')
    if packageName == None or packageActivity == None:
        url = chooseApkPath + '_fail\\'
        shutil.move(apkPath, url + fname)
        printNor("[J] move %s -> %s" % (fname, str(url)))
        return
    if apkInstall():
        self.window.clean()
        if runApk(packageName, packageActivity):
            if runTrace():
                runMonkey(packageName)
                getJsonLog(self)
                self.window.stop()
            stopApk(packageName)
        apkUninstall(packageName)
        if hookSuccess:
            url = chooseApkPath + '_success\\'
            shutil.move(apkPath, url + fname)
            printNor("[J] move %s -> %s" % (fname, url))
            hookSuccess = False
        else:
            url = chooseApkPath + '_fail\\'
            shutil.move(apkPath, url + fname)
            printNor("[J] move %s -> %s" % (fname, url))
    else:
        url = chooseApkPath + '_fail\\'
        shutil.move(apkPath, url + fname)
        printNor("[J] move %s -> %s" % (fname, url))
def multTrace(path, self):
    global loadingAPK
    apkPaths = getApkPath(path)
    if apkPaths == []:
        print('there is no apk in this folder')
        return
    count = 0
    for apkPath in apkPaths:
        loadingAPK = apkPath
        if count == 0:
            printNor('[A] ------------------ start---------------------------')
        else:
            printNor('    ------------------ end %d' % (count) + ' APK ----------------------')
        count += 1
        appTrace(apkPath, self)
    printNor('    ------------------ end %d' % (count) + ' APK ----------------------')
def singleTrace(path, self):
    global loadingAPK
    apkPaths = getApkPath(path)
    if apkPaths == []:
        print('there is no apk in this folder')
        return
    loadingAPK = apkPaths[0]
    printNor('[A] ------------------ start ---------------------------')
    appTrace(loadingAPK, self)
    printNor('    ------------------ end -----------------------------')
def _async_raise(tid, exctype):
    """raises the exception, performs cleanup if needed"""
    tid = ctypes.c_long(tid)
    if not inspect.isclass(exctype):
        exctype = type(exctype)
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, ctypes.py_object(exctype))
    if res == 0:
        raise ValueError("invalid thread id")
    elif res != 1:
        ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, None)
        raise SystemError("PyThreadState_SetAsyncExc failed")
def stop_thread(thread):
    _async_raise(thread.ident, SystemExit)
def checkConnect():
    hookThread = threading.Thread(target=Xtracer)
    while True:
        time.sleep(1)
        adbReturn = subprocess.run('frida-ps -U', shell=True, stdout=subprocess.PIPE, encoding="utf-8").stdout
        if "Failed" in adbReturn:
            print('frida disconnect,trace thread alive:', hookThread.is_alive())
            continue
        if "PID" in adbReturn and not hookThread.is_alive():
            print('frida connect,trace thread alive:', hookThread.is_alive())
            hookThread = threading.Thread(target=Xtracer)
            hookThread.start()
            break
if __name__ == '__main__':
    with open('tmp/Tracer.pid', 'w') as f:
        f.write(str(os.getpid()))
    checkConnect()