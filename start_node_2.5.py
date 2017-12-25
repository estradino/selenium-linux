__author__ = 'TahaYassine'

import subprocess
import os
import platform
import requests
import sched
import time
import sys

s = sched.scheduler(time.time, time.sleep)
authorization_token = '301f2b9da3e976f40c1bafe68ca0c703cc58221c7098da654099a40a9885dfcb'
delay = 30

node_heartbeat_url = "https://api.asayer.io/dev/selenium/node/linux/heartbeat"

id_env_var_name = "ID"

node_config_file_name = "configNode.json" if len(sys.argv) < 2 else sys.argv[1]

separator = ";" if platform.system().lower() == "windows" else ":"
script_directory = os.getcwd()

execute_jar_args = ['java',
                    '-Xmx1024M',
                    '-cp',
                    '%s/selenium-video-node-2.5.jar%s%s/proxy25.jar%s%s/selenium-server-standalone-2.53.1.jar' % (
                        script_directory, separator, script_directory, separator, script_directory),
                    'org.openqa.grid.selenium.GridLauncher',
                    '-role',
                    'node',
                    '-nodeConfig',
                    node_config_file_name
                    ]

java_output_log = open("selenium_node_log.txt", "ab")

java_process = None


def check():
    if java_process is None:
        execute_jar()
    else:
        send_heartbeat()


def get_node_id():
    if id_env_var_name in os.environ:
        return os.environ[id_env_var_name]
    else:
        print("No ID found in env vars")
        return None


def send_heartbeat():
    id = get_node_id()
    if id is not None:
        print("sending heartbeat")
        r = requests.post(url=node_heartbeat_url, json={"id": id},
                          auth=('Authorization', authorization_token))
        print(r.text)


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
