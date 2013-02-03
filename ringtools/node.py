#! /usr/bin/env python
#
# ABOUT
# =====
# py-ring - A generic module for running commands on nodes of the NLNOG 
# ring. More information about the ring: https://ring.nlnog.net
#
# source code: https://github.com/NLNOG/py-ring 
#
# AUTHOR
# ======
# Teun Vink - teun@teun.tv
#
# CHANGELOG
# =========
# v0.1  start coding
# 
#
# ===========================================================================

import threading, sys, Queue, os, time, socket
from paramiko import *

from exception import RingException
from result import NodeResult, NodeResultSet

# ===========================================================================

DFLT_SSH_TIMEOUT = 20           # seconds
DFLT_FQDN = "ring.nlnog.net"    # fqdn for nodes
DFLT_MAX_THREADS = 25           # number of concurrent threads

LOG_NONE  = 0
LOG_FATAL = 1
LOG_ERROR = 2
LOG_WARN  = 3
LOG_INFO  = 4
LOG_DEBUG = 5 

LOG_STR = [ "", "FATAL", "ERROR", "WARN", "INFO", "DEBUG" ]

VERSION = "0.1"


# ===========================================================================

class RingNode:
    STATE_DISCONNECTED = 0
    STATE_CONNECTED = 1
    STATE_AUTHENTICATED = 2

    def __init__(self, hostname=None, username=None, ssh_client=None, ssh_agent=None, ssh_config=None, timeout=DFLT_SSH_TIMEOUT, analyse=None):
        self.hostname = hostname
        self.username = username
        self.ssh_client = ssh_client
        self.ssh_config = ssh_config
        self.timeout = timeout
        self.state = RingNode.STATE_DISCONNECTED
        self.stdin = None
        self.stdout = None
        self.stderr = None
        self.analyse = analyse
        
        if ssh_agent != None:
            self.ssh_agent = ssh_agent
        else:
            self.ssh_agent = Agent()


    def close(self):
        if self.ssh_client != None:
            self.ssh_client.close()

    
    def connect(self, hostname=None, timeout=DFLT_SSH_TIMEOUT):
        if hostname == None and self.hostname == None:
            # no idea what host to connect to
            self.state = RingNode.STATE_DISCONNECTED
            raise RingException('No host specified.')
        elif hostname != None:
            self.hostname = hostname
    
        if self.ssh_client == None:
            self.ssh_client = SSHClient()

        if self.ssh_config == None:
            self.ssh_config = SSHConfig()
            self.ssh_config.parse(open(os.path.join(os.environ['HOME'], '.ssh', 'config'), 'r'))

        if self.username == None:
            self.username = self.ssh_config.lookup('%s.%s' % (hostname, DFLT_FQDN)).get('user', '')

        self.ssh_client.set_missing_host_key_policy(AutoAddPolicy())
        self.ssh_client.load_system_host_keys()
                
        try:
            self.ssh_client.connect(
                hostname='%s.%s' % (self.hostname, DFLT_FQDN),
                username=self.username,
                allow_agent=True, 
                look_for_keys=True, 
                timeout=self.timeout) 
            self.state = RingNode.STATE_CONNECTED
            return RingNode.STATE_CONNECTED
        except BadHostKeyException, e:
            self.state = RingNode.STATE_DISCONNECTED
            raise RingException('Bad host key for %s.%s' % (self.hostname, DFLT_FQDN))
        except SSHException, e:
            self.state = RingNode.STATE_DISCONNECTED
            raise RingException(e)
        except socket.error, e:
            self.state = RingNode.STATE_DISCONNECTED
            raise RingException(e)
        except socket.timeout, e:
            self.state = RingNode.STATE_DISCONNECTED
            raise RingException('Socket timeout.')
    

    def authenticate(self):
        if self.state == RingNode.STATE_DISCONNECTED or self.ssh_client == None or self.ssh_agent == None:
            connect()
                
        transport = self.ssh_client.get_transport()
        channel = transport.open_session()
        for key in self.ssh_agent.get_keys():
            try:
                channel.auth_publickey(key)
                break
            except:
                # wrong key, nothing to worry about since people can have 
                # multiple keys available in their agent
                continue
        try:
            if transport.is_authenticated:
                self.state = RingNode.STATE_AUTHENTICATED
                return RingNode.STATE_AUTHENTICATED
            else:
                self.state = RingNode.STATE_CONNECTED
                raise RingException('Failed to authenticate.')
        except Exception, e: 
            self.state = RingNode.STATE_DISCONNECTED
            raise RingException(e)


    def run_command(self, command):
        if self.state == RingNode.STATE_DISCONNECTED:
            self.connect()
        if self.state == RingNode.STATE_CONNECTED:
            self.authenticate() 

        transport = self.ssh_client.get_transport()
        channel = transport.open_session()
        if transport.is_authenticated:
            self.stdin = channel.makefile('wb')
            self.stdout = channel.makefile('rb')
            self.stderr = channel.makefile_stderr('rb') 
            self.state = RingNode.STATE_AUTHENTICATED
            channel.exec_command(command)

        result = NodeResult(
            hostname = self.hostname,
            ssh_result= NodeResult.SSH_OK,
            exitcode = channel.recv_exit_status(),
            stdout = [line.strip() for line in self.stdout], 
            stderr = [line.strip() for line in self.stderr])
    
        if self.analyse:
            self.analyse(result)
        return result

    def get_state(self):
        return self.state

# ===========================================================================


class NodeCommandThread(threading.Thread):
    ''' a thread for processing commands to a node via SSH
    '''

    def __init__(self, queue, command, agent, timeout=DFLT_SSH_TIMEOUT, loglevel=LOG_NONE, analyse=None):
        self.queue = queue
        self.command = command
        self.agent = agent
        self.timeout = timeout
        self.result = NodeResultSet()
        self.loglevel = loglevel
        self.analyse = analyse
        threading.Thread.__init__(self)


    def log(self, msg, loglevel=LOG_INFO):
        if self.loglevel >= loglevel:
            print "[%s] %5s: %s" % (time.strftime('%H:%M:%S', time.localtime()), LOG_STR[loglevel], msg)
            sys.stdout.flush()


    def run(self):
        # read default SSH config
        ssh = SSHClient()
        conf = SSHConfig()
        conf.parse(open(os.path.join(os.environ['HOME'], '.ssh', 'config'), 'r'))
        ssh.set_missing_host_key_policy(AutoAddPolicy())
        ssh.load_system_host_keys()

        # continue to process hosts until the queue is empty
        while True:
            try:
                starttime = time.time()
                # pick the next available host
                host = self.queue.get()
                self.log("%s picked %s" % (self.name, host), LOG_DEBUG)
                result = NodeResult(host)
                node = RingNode(host, analyse=self.analyse)
                try:
                    # some template replacements
                    cmd = self.command.replace("%%HOST%%", host)
                    result = node.run_command(cmd)
                except RingException, e:
                    result.set_ssh_errormsg(e.__str__())
                finally:
                    node.close()

                result.add_value('runtime', time.time() - starttime)
                self.result.append(result)

            except Queue.Empty:
                # we're done!
                pass
            finally:
                self.log("%s is finished" % self.name, LOG_DEBUG)
                self.queue.task_done() 


    def get_result(self):
        return self.result
