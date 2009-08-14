#!/usr/bin/env python

import socket
from socket import AF_INET, SOCK_DGRAM, socket
import os
import os.path
import sys
import time
from optparse import OptionParser

VERSION=0.1

def sendMessage(message, addr):
    s = socket(AF_INET,SOCK_DGRAM)
    try:
        s.sendto(message.payload(), addr)
    finally:
        s.close()

def prowlnotify(options):
    try:
        import prowlpy
    except Error as e:
        sys.stderr.write("Unable to load 'prowlpy' module\n")
        sys.stderr.write(e)
        sys.exit(1)

    if options.prowl_key == "" and options.password != "":
        options.prowl_key = options.password

    if options.prowl_key == "":
        if options.prowl_keyfile == "":
            try:
                options.prowl_keyfile = os.path.join(os.path.expanduser("~"),
                                                     ".prowlkey")
            except:
                pass
        if options.prowl_keyfile != "":
            keyfile = None
            try:
                keyfile = open(options.prowl_keyfile,'r')
            except:
                pass
            if keyfile:
                options.prowl_key = keyfile.readline().rstrip()

    if options.prowl_key == "":
        sys.stderr.write("please provide Prowl API key using --prowl-key or --prowl-keyfile\n")
        sys.exit(3)

    application = ""
    if options.name != os.path.basename(sys.argv[0]):
        application = options.name
        if options.identifier != "":
            application = application + ": "

    if options.identifier != "":
        application = application + options.identifier

    if application == "":
        application=options.name
        
    p = prowlpy.Prowl(options.prowl_key)
    p.post(application=application,
           event=options.title,
           description=options.message,
           priority=options.priority)

def netgrowlnotify(options):
    try:
        import netgrowl
    except Error as e:
        sys.stderr.write("Unable to load 'netgrowl' module\n")
        sys.stderr.write(e)
        sys.exit(1)

    if options.port == None:
        options.port=netgrowl.GROWL_UDP_PORT
        
    addr = (options.host, options.port)

    r = netgrowl.GrowlRegistrationPacket(application=options.name,
                                         password=options.password)
    r.addNotification(options.identifier)

    sendMessage(r,addr)
    
    p = netgrowl.GrowlNotificationPacket(application=options.name,
                                         notification=options.identifier,
                                         title=options.title,
                                         description=options.message,
                                         priority=options.priority,
                                         sticky=options.sticky,
                                         password=options.password)

    sendMessage(p,addr)

def parse_time(stime):
    ftime = time.strftime('%Y %j ',time.localtime()) + stime.replace(' ','')
    ret = None
    try:
        ret = time.strptime(ftime,'%Y %j %I:%M%p')
    except:
        ret = None
        pass

    if ret == None:
        try:
            ret = time.strptime(ftime, '%Y %j %H:%M')

        except:
            ret = None
            pass

    if ret == None:
        raise Exception("unable to parse time: " + stime)

    return ret


if __name__ == "__main__":
    usage = "Usage: %prog [options] [title]"

    parser = OptionParser(usage=usage, version='%s %s' % ('%prog', VERSION))
    parser.add_option("-n", "--name", dest="name",
                      help="Set the name of the application that sends the notification",
                      type="string", default=os.path.basename(sys.argv[0]))
    parser.add_option("-s", "--sticky", dest="sticky",
                      help="Make the notification sticky",action="store_true",
                      default=False)
    parser.add_option("-m", "--message", dest="message",
                      help="Sets the message to be used instead of using stdin",
                      type="string", default="")
    parser.add_option("-p", "--priority", dest="priority",
                      help="Specify an int or named key (default is 0)",
                      type="int", default=0)
    parser.add_option("-d", "--identifier", dest="identifier",
                      help="Specify a notification identifier (used for coalescing)",
                      type="string", default="")
    parser.add_option("-H", "--host", dest="host",
                      help="Specify a hostname to which to send a remote notification.",
                      type="string", default="localhost")
    parser.add_option("-P", "--password", dest="password",
                      help="Password used for remote notifications.",
                      type="string", default="")
    parser.add_option("", "--port", dest="port",
                      help="Port number for UDP notifications.",
                      type="int", default=None)
    parser.add_option("-t", "--title", dest="title",
                      help="Does nothing. Any text following will be treated as the",
                      type="string", default="")
    # prowl support
    parser.add_option("","--prowl",action="store_true", default=False,
                      help="Send notification to Prowl instead of Growl")
    parser.add_option("","--prowl-key",type="string",dest="prowl_key",
                      default="",
                      help="API key used for Prowl notifications")
    parser.add_option("","--prowl-keyfile", type="string", dest="prowl_keyfile",
                      help="Path to file containing Prowl API key",
                      default="")

    # time window support
    parser.add_option("","--time-start", default=None, type="string",
                      dest="time_start")
    parser.add_option("","--time-end", default=None, type="string",
                      dest="time_end")

    (options,args) = parser.parse_args()
    options.title = options.title + " " + " ".join(args)
    options.message = options.message.replace("\\n","\n")

    if options.time_start != None or options.time_end != None:
        now = time.localtime()
        if options.time_start != None:
            mintime = parse_time(options.time_start)
            if now < mintime:
                sys.exit(0)

        if options.time_end != None:
            maxtime = parse_time(options.time_end)
            if now > maxtime:
                print "too late"
                sys.exit(0)


    if options.prowl:
        prowlnotify(options)
    else:
        netgrowlnotify(options)

