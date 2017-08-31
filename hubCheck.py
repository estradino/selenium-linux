__author__ = 'TahaYassine'

import subprocess
import getpass
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

hub_status_url = "https://api.asayer.io/dev/selenium/hub/%s/status"
hub_selector_url = "https://api.asayer.io/dev/selenium/hub_selector"
get_public_ip_url = "https://api.ipify.org?format=text"

hub_env_var_name = "hub"
hub_env_var_ip = "hubIp"
host_name = socket.gethostname()

node_config_file_name = "configNode.json" if len(sys.argv) < 2 else sys.argv[1]
separator = ";" if platform.system().lower() == "windows" else ":"
script_directory = os.getcwd()

execute_jar_args = ['java',
                    '-Xmx1024M',
                    '-cp',
                    '%s/selenium-video-node-2.3.jar%s%s/proxy.jar%s%s/selenium-server-standalone-3.4.0.jar' % (
                        script_directory, separator, script_directory, separator, script_directory),
                    'org.openqa.grid.selenium.GridLauncherV3',
                    '-role',
                    'node',
                    '-nodeConfig',
                    node_config_file_name
                    ]

java_output_log = open("selenium_node_log.txt", "ab")

public_ip = None

process_username = host_name.upper() + ("\\" if host_name is not None else "") + getpass.getuser()

java_process = None


def check():
    if hub_env_var_name in os.environ and hub_env_var_ip in os.environ and java_process is not None:
        print("used hub: %s : %s" % (os.environ[hub_env_var_name], os.environ[hub_env_var_ip]))
        r = requests.get(url=hub_status_url % os.environ[hub_env_var_name],
                         auth=('Authorization', authorization_token))

        if r.status_code is not 200:
            print("hub_status_url > status code not 200:%s" % r.status_code)
            return

        hub_status = r.json()
        print("hub_status: %s" % json.dumps(hub_status))

        if hub_status["status"] == "DOWN":
            subscribe_to_hub()
        elif hub_status["ip"] != os.environ[hub_env_var_ip]:
            change_hub_ip(hub_status["ip"])

    else:
        subscribe_to_hub()


hub_select_retries = 0


def subscribe_to_hub():
    kill_java()
    r = requests.post(url=hub_selector_url, json={"caps": get_caps(), "node": "http://" + get_public_ip()},
                      auth=('Authorization', authorization_token))
    global hub_select_retries
    if r.status_code is not 200:
        if r.status_code == 404:
            resj = json.loads(r.text)
            if hub_select_retries < 3:
                print("try %s : %s" % (hub_select_retries, resj["Message"]))
                time.sleep(3)
                hub_select_retries += 1
                subscribe_to_hub()
            else:
                hub_select_retries = 0
                print("%s : 3 retries failed, waiting for next iteration" % resj["Message"])
        else:
            print("hub_selector_url > status code not 200:%s" % r.status_code)
        return
    hub_select_retries = 0

    hub = r.json()
    print("hub selector result: %s" % json.dumps(hub))
    os.environ[hub_env_var_name] = hub["hostname"]
    os.environ[hub_env_var_ip] = hub["hub"]
    print("created env var: %s : %s" % (os.environ[hub_env_var_name], hub["hub"]))
    edit_node_config(hub)
    execute_jar()


def kill_java():
    global java_process
    if java_process is not None:
        print("Flushing the rest of the log before killing java process")
        java_output_log.write(
            "-----------------End of log for PID %s at %s-----------------" % (java_process.pid, time.strftime("%c")))
        java_output_log.write(os.linesep)
        java_output_log.write(os.linesep)
        java_output_log.write(os.linesep)
        java_output_log.flush()
        print("Killing java process with the PID=%s" % java_process.pid)
        java_process.terminate()
        java_process = None


def edit_node_config(hub):
    print("hub: %s" % json.dumps(hub))
    with open(node_config_file_name, 'r') as f:
        data = json.load(f)
        data['port'] = hub["port"]
        data['register'] = True
        data['hub'] = "http://%s:4444" % hub["hub"]
        data['host'] = get_public_ip()

    os.remove(node_config_file_name)
    with open(node_config_file_name, 'w') as f:
        json.dump(data, f, indent=4)


def change_hub_ip(ip):
    kill_java()
    with open(node_config_file_name, 'r') as f:
        data = json.load(f)
        print("hub IP changed from %s to %s" % (data['hub'], "http://%s:4444" % ip))
        data['hub'] = "http://%s:4444" % ip

    os.remove(node_config_file_name)
    with open(node_config_file_name, 'w') as f:
        json.dump(data, f, indent=4)

    execute_jar()


def get_caps():
    with open(node_config_file_name, 'r') as f:
        data = json.load(f)
        caps = "".join(
            ["-%s-%s" % (cap["browserName"], cap["browserVersion"] if "browserVersion" in cap else "null") for cap in
             data['capabilities']]) + "-%s" % platform.system().lower()
        print("caps: %s" % str(caps))
        return str(caps)


def get_public_ip():
    global public_ip
    if public_ip is not None:
        return public_ip
    r = requests.get(url=get_public_ip_url)
    if r.status_code is not 200:
        print("get_public_ip_url status code not 200:%s" % r.status_code)
        return
    public_ip = r.text
    print("public_ip: %s" % public_ip)
    return public_ip


def add_log_header():
    line = "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
    java_output_log.write(line)
    java_output_log.write(os.linesep)
    java_output_log.write("Scrip started at: %s" % time.strftime("%c"))
    java_output_log.write(os.linesep)
    java_output_log.write(line)
    java_output_log.write(os.linesep)
    java_output_log.flush()


def execute_jar():
    print("Starting the  .jar")
    global java_process
    java_process = subprocess.Popen(args=execute_jar_args,
                                    shell=False,
                                    stdout=java_output_log, stderr=java_output_log
                                    )
    java_output_log.write(os.linesep)
    java_output_log.write(
        "-----------------Start of log for PID %s at %s-----------------" % (java_process.pid, time.strftime("%c")))
    java_output_log.write(os.linesep)
    java_output_log.flush()
    print("Started Java process PID= %s at %s" % (java_process.pid, time.strftime("%c")))


def start(sc):
    check()
    s.enter(delay, 1, start, (sc,))


add_log_header()

s.enter(0, 1, start, (s,))
s.run()
