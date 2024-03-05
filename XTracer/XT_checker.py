import subprocess
import os
import time
import XT_config
config = XT_config.config()
def deviceStart():
    devicePath = config.data['baseConf']['simulator_filepath']
    print('devicePath:', devicePath)
    os.popen(devicePath)
def checkDeviceConnect():
    adbReturn = os.popen('adb devices').readlines()
    if len(adbReturn) != 3:
        os.popen('adb disconnect')
        return False
    else:
        readline = adbReturn[1]
        if 'device' in readline:
            os.popen('adb forward tcp:27043 tcp:27043')
            printM('adb forward tcp:27043 tcp:27043')
            return True
        else:
            os.popen('adb disconnect')
            printM('adb disconnect')
            return False
    return False
def AdbConnect():
    tryNum = 0
    while tryNum < 5:
        adbReturn = subprocess.run('adb connect 127.0.0.1:5555', shell=True, stdout=subprocess.PIPE,
                                   encoding="utf-8").stdout
        if 'connected' in adbReturn:
            printM('success connect device')
            return True
        tryNum += 1
        printM('fail connect ,try:' + str(tryNum))
        time.sleep(1)
    return False
def checkFrada():
    adbReturn = subprocess.run('frida-ps -U', shell=True, stdout=subprocess.PIPE, encoding="utf-8").stdout
    if "Failed" in adbReturn:
        return False
    if "PID" in adbReturn:
        return True
    return False
def FridaConnect():
    cmd = 'adb shell < source/frida-server_start.bat'
    os.popen(cmd)
def printM(msg):
    print(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())), ':', msg)
def TracerStart():
    os.system('python Xtracer.py')
def restartDevice():
    command = """wmic process where 'name="HD-Player.exe"' get processid"""
    proc = subprocess.Popen(command, shell=False, stdout=subprocess.PIPE)
    commandReturn = proc.communicate(timeout=120)
    deviceStart()
def mainCheckProcess():
    deviceStart()
    timecount = 0
    print("---------------------------------------------")
    while True:
        if checkDeviceConnect():
            adbReturn = os.popen('adb shell getprop sys.boot_completed').readlines()
            if '1\n' not in adbReturn:
                printM('device loading')
                time.sleep(10)
                continue
            printM('device connect')
            if checkFrada():
                printM('frida connect')
            else:
                printM('frida disonnected | trying connect')
                FridaConnect()
        else:
            printM('device disconnected | trying connect')
            if not AdbConnect():
                printM('device restart')
                restartDevice()
        time.sleep(5)
        timecount += 1
        print("----------------- timecount:" + str(timecount) + " -------------------")
        if timecount % 300 == 0:
            timecount = 0
            restartDevice()
            print('restart device')
if __name__ == '__main__':
    mainCheckProcess()