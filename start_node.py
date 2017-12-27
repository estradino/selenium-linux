__author__ = 'TahaYassine'

import subprocess
import os
import platform
import requests
import sched
import time
import sys
import argparse

parser = argparse.ArgumentParser(
    description="the node side script to run selenium-node & heartbeat & subscribe to hub & check hub",
    epilog="created by the Asayer team")
parser.add_argument("-s", "--seleniumVersion", help="the selenium version of the hub (default 3.6.0)", default="3.6.0")
parser.add_argument("-c", "--config", help="the node json config file", default="configNode.json")
parser.add_argument("-p", "--proxyVersion", help="the proxy version to use (default 3.6)", default="3.6")
parser.add_argument("--Xmx", help="the Xmx size in Mb (default 512)", default="512")
parser.add_argument("--noVideoJar", help="don't import selenium-node-video.jar (default false)",
                    action='store_true')

args = parser.parse_args()

# monkey-patch for the print() function
old_f = sys.stdout


class F:
    def write(self, x):
        old_f.write(x.replace("\n", " [at %s]\n" % str(time.strftime("%c"))))

    def flush(self):
        pass


sys.stdout = F()

s = sched.scheduler(time.time, time.sleep)
authorization_token = '301f2b9da3e976f40c1bafe68ca0c703cc58221c7098da654099a40a9885dfcb'
delay = 30

node_heartbeat_url = "https://api.asayer.io/dev/selenium/node/linux/heartbeat"

id_env_var_name = "ID"

node_config_file_name = args.config
hub_version_3 = int(args.seleniumVersion.partition(".")[0]) > 2
separator = ";" if platform.system().lower() == "windows" else ":"
script_directory = os.getcwd()

proxy = "proxy" + args.proxyVersion + ".jar"
classpath = [
    '%s/%s' % (script_directory, proxy),
    '%s/selenium-server-standalone-%s.jar' % (script_directory, args.seleniumVersion)
]

if args.noVideoJar is False:
    classpath.append('%s/selenium-video-node-2.5.jar' % script_directory)

execute_jar_args = ['java',
                    '-Xmx' + args.Xmx + 'M',
                    '-cp',
                    separator.join(classpath),
                    'org.openqa.grid.selenium.GridLauncherV3' if hub_version_3 else 'org.openqa.grid.selenium.GridLauncher',
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
