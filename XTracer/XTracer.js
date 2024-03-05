function log(text) {
    var packet = {
        'cmd': 'log',
        'data': text
    };
    send("CxTracer:::" + JSON.stringify(packet))
}

function enter(tid, tname, cls, method, args) {
    var packet = {
        'cmd': 'enter',
        'data': [tid, tname, cls, method, args]
    };
    send("CxTracer:::" + JSON.stringify(packet))
}
function exit(tid, retval) {
    var packet = {
        'cmd': 'exit',
        'data': [tid, retval]
    };
    send("CxTracer:::" + JSON.stringify(packet))
}

function getTid() {
    var Thread = Java.use("java.lang.Thread")
    return Thread.currentThread().getId();
}

function getTName() {
    var Thread = Java.use("java.lang.Thread")
    return Thread.currentThread().getName();
}
function overloads(target,methodName,clsname){
    var overloads = target[methodName].overloads;
    overloads.forEach(function (overload) {
        var proto = "(";
        overload.argumentTypes.forEach(function (type) {
            proto += type.className + ", ";
        });
        if (proto.length > 1) {
            proto = proto.substr(0, proto.length - 2);
        }
        proto += ")";
        log("hooking: " + clsname + "." + methodName + proto);
        overload.implementation = function () {
            var args = [];
            var tid = getTid();
            var tName = getTName();
            for (var j = 0; j < arguments.length; j++) {
                args[j] = arguments[j] + ""
            }
            enter(tid, tName, clsname, methodName + proto, args);
            var retval = this[methodName].apply(this, arguments);
            exit(tid, "" + retval);
            return retval;
        }
    });
}
function traceClass(clsname,method) {
    try {
        var target = Java.use(clsname);
       if(method==''){
        var methods = target.class.getDeclaredMethods();
        methods.forEach(function (mtd) {
            var methodName = mtd.getName();
            overloads(target,methodName,clsname);
        });
       }else{
            overloads(target,method,clsname);
       }
    } catch (e) {
        log("'" + clsname + "' hook fail: " + e)
    }
}

function match(ex, text) {
    if(ex.indexOf('/')!=-1){
        var method=ex.split('/')[1]
        ex=ex.split('/')[0]
        return [ex == text,method];
    }
    else
        return [text.match(ex),'']
}
traceClass("android.telephony.SmsManager","createFromPdu")
if (Java.available) {
    Java.perform(function () {
        log('Start...');
        var hookList = {hookList};
        Java.enumerateLoadedClasses({
            onMatch: function (aClass) {
                for (var index in hookList) {
                    var method=match(hookList[index], aClass)
                    if (method[0]) {
                        log(aClass + "' match by '" + hookList[index] + "'");
                        traceClass(aClass,method[1]);
                    }
                }
            },
            onComplete: function () {
                log("Complete.");
            }
        });
    });
}