import getpass

import psutil

__author__ = 'TahaYassine'

import os
import platform
import requests
import sched
import socket
import time
import json
import sys

s = sched.scheduler(time.time, time.sleep)
authorization_token = '301f2b9da3e976f40c1bafe68ca0c703cc58221c7098da654099a40a9885dfcb'
delay = 30

hub_status_url = "https://avnzgtxgr4.execute-api.eu-central-1.amazonaws.com/dev/selenium/hub/%s/status"
hub_selector_url = "https://avnzgtxgr4.execute-api.eu-central-1.amazonaws.com/dev/selenium/hub_selector"

hub_env_var_name = "hub"
host_name = socket.gethostname()

node_config_file_name = "configNode.json" if len(sys.argv) < 2 else sys.argv[1]
separator = ";" if platform.system().lower() == "windows" else ":"
execute_jar_command = '''java -Xmx1024M -cp "/selenium/selenium-video-node-2.3.jar%s/selenium/proxy.jar%s/selenium/selenium-server-standalone-3.4.0.jar" org.openqa.grid.selenium.GridLauncherV3 -role node -nodeConfig %s''' % (
    separator, separator, node_config_file_name)

public_ip = None
java_process_name = "java"

process_username = host_name.upper() + ("\\" if host_name is not None else "") + getpass.getuser()


def check():
    if hub_env_var_name in os.environ and len(get_java_pids()) > 0:
        print(os.environ[hub_env_var_name])
        # r = requests.get(hub_status_url % "123", auth=('user', 'pass'))
        # r = requests.get(hub_status_url % os.environ[host_env_var_name],
        r = requests.get(url=hub_status_url % os.environ[hub_env_var_name],
                         auth=('Authorization', authorization_token))

        if r.status_code is not 200:
            print("status code not 200:%s" % r.status_code)
            return

        hub_status = r.json()
        print(hub_status)

        if hub_status["status"] == "DOWN":
            subscribe_to_hub()

    else:
        subscribe_to_hub()


def subscribe_to_hub():
    kill_java()
    r = requests.post(url=hub_selector_url, json={"caps": get_caps(), "node": "http://" + get_public_ip()},
                      auth=('Authorization', authorization_token))

    if r.status_code is not 200:
        print("status code not 200:%s" % r.status_code)
        return

    hub = r.json()
    os.environ[hub_env_var_name] = hub["hub"]
    print("created env var:%s" % os.environ[hub_env_var_name])
    edit_node_config(hub)
    execute_jar()


def kill_java():
    return
    java_pids = get_java_pids()
    if len(java_pids) is 0:
        return
    for pid in java_pids:
        psutil.Process(pid).terminate()
    kill_java()


def get_java_pids():
    processes = [p.as_dict(attrs=['pid', 'name', 'username']) for p in psutil.process_iter()]
    java_pid = []
    for proc in processes:
        if proc["name"].startswith(java_process_name) and proc["username"] == process_username:
            java_pid.append(proc["pid"])
    return java_pid


def edit_node_config(hub):
    print(hub)
    with open(node_config_file_name, 'r') as f:
        data = json.load(f)
        data['port'] = hub["port"]
        data['register'] = True
        data['hub'] = "http://%s:4444" % hub["hub"]
        data['host'] = get_public_ip()

    os.remove(node_config_file_name)
    with open(node_config_file_name, 'w') as f:
        json.dump(data, f, indent=4)


def get_caps():
    with open(node_config_file_name, 'r') as f:
        data = json.load(f)
        caps = "".join(
            ["-%s-%s" % (cap["browserName"], cap["browserVersion"] if "browserVersion" in cap else "null") for cap in
             data['capabilities']]) + "-%s" % platform.system().lower()
        print str(caps)
        return str(caps)


def get_public_ip():
    global public_ip
    if public_ip is not None:
        return public_ip
    print "call"
    r = requests.get(url="https://api.ipify.org?format=text")
    if r.status_code is not 200:
        print("status code not 200:%s" % r.status_code)
        return
    public_ip = r.text
    return public_ip


def execute_jar():
    os.system(execute_jar_command)


def start(sc):
    check()
    s.enter(delay, 1, start, (sc,))


s.enter(0, 1, start, (s,))
s.run()


# start()
