#! /usr/bin/env python
"""
A node in the NLNOG ring.
"""

# ABOUT
# =====
# This file is part of:
# 
# ringtools - A generic module for running commands on nodes of the NLNOG 
# ring. More information about the ring: U{https://ring.nlnog.net}
# 
# source code: U{https://github.com/NLNOG/py-ring}
# 
# AUTHOR
# ======
# Teun Vink - teun@teun.tv

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
    """ 
    A node of the NLNOG ring.
    """

    STATE_DISCONNECTED = 0
    STATE_CONNECTED = 1
    STATE_AUTHENTICATED = 2

    def __init__(self, hostname=None, username=None, ssh_client=None, ssh_agent=None, ssh_config=None, timeout=DFLT_SSH_TIMEOUT):
        """ Create a new RingNode object.

            @param hostname: the host in the ring to connect to
            @type hostname: string

            @param username: the username used when authenticating using SSH. 
            If no I{username} is specified the SSH configuration is checked.
            @type username: string

            @param ssh_client: a I{paramiko.SSHClient} object. If none is
            specified a new one is created. Passing this as an argument is
            useful when a lot of L{RingNode} objects are created: only one
            SSHClient object is used then. 
            
            I{Not providing this parameter is no problem.}

            @type ssh_client: paramiko.SSHClient

            @param ssh_agent: a I{paramiko.Agent} object. If none is specified
            a new agent object is created. Passing this as asn argument is useful
            when a lot of L{RingNode} objects are created: only one SSHAgent object
            is used.

            I{Not providing this parameter is no problem.}

            @type ssh_agent: paramiko.Agent

            @param ssh_config: a I{paramiko.SSHConfig} object. If none is specified
            a new object is created. Passing this as asn argument is useful
            when a lot of L{RingNode} objects are created: only one SSHConfig object
            is used.

            I{Not providing this parameter is no problem.}

            @type ssh_config: paramiko.SSHConfig

            @param timeout: SSH timeout in seconds
            @type timeout: integer
        """
        self.hostname = hostname
        self.username = username
        self.ssh_client = ssh_client
        self.ssh_config = ssh_config
        self.timeout = timeout
        self.state = RingNode.STATE_DISCONNECTED
        self.stdin = None
        self.stdout = None
        self.stderr = None
        
        if ssh_agent != None:
            self.ssh_agent = ssh_agent
        else:
            self.ssh_agent = Agent()


    def close(self):
        """ Close the SSH connection to the node.
        """
        if self.ssh_client != None:
            self.ssh_client.close()

    
    def connect(self, hostname=None, timeout=DFLT_SSH_TIMEOUT):
        """ Open a SSH connection to the host. If ssh_client and ssh_config were not
            specified when constructing the object they are created.

            @param hostname: the name of the host to connect to (needed if not specified when making the object)
            @type hostname: string

            @param timeout: SSH timeout in seconds
            @type timeout: integer

            @raise RingException: when the connection failed
        """
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
            raise RingException(e.__str__())
        except socket.timeout, e:
            self.state = RingNode.STATE_DISCONNECTED
            raise RingException('Socket timeout.')
    

    def authenticate(self):
        """ Authenticate on the SSH session.
            If the SSH agent provides more than on SSH-key all of the
            keys are tried.

            @raise RingException: if the authentication failed
        """
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
        """ Execute a command using the SSH connection.
            Create a connection and authenticate if not done yet.

            @param command: the command to be executed
            @type command: string

            @return: object containing the exitcode, 
            output of stdout and stderr and additional data
            @rtype NodeResult
        """
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
    
        return result


    def get_state(self):
        """ Return the state of the SSH connection.

            return: state (STATE_DISCONNECTED = 0, 
            STATE_CONNECTED = 1, STATE_AUTHENTICATED = 2)
            rtype integer
        """
        return self.state

# ===========================================================================


class NodeCommandThread(threading.Thread):
    ''' a thread for processing commands to a node via SSH
    '''

    def __init__(self, queue, command, agent, timeout=DFLT_SSH_TIMEOUT, loglevel=LOG_NONE, analyse=None):
        """ Create a new NodeCommandThread object.

            @param queue: a list of nodes on which the commands is to be executed
            @type queue: list of strings
            
            @param command: the command to be executed
            @type command: string
        
            @param agent: a I{paramiko.Agent} SSH-agent object.
            @type agent: I{paramiko.Agent} object

            @param timeout: the SSH timeout in seconds
            @type timeout: integer

            @param loglevel: the level of logdetail
            @type loglevel: integer

            @param analyse: callback analyse function. This function is called after
            the command has been executed. Argument for the function is a L{NodeResult} object.
            @type analyse: function
        """
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
        """ Execution of the thread.
        """
        # read default SSH config
        ssh = SSHClient()
        conf = SSHConfig()
        
        # use the local SSH configuration for keys, known hosts, etc
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
                node = RingNode(host)
                try:
                    # some template replacements
                    cmd = self.command.replace("%%HOST%%", host)
                    result = node.run_command(cmd)
                except RingException, e:
                    result.set_ssh_result(NodeResult.SSH_ERROR)
                    result.set_ssh_errormsg(e.__str__())
                finally:
                    node.close()
                    if self.analyse:
                        self.analyse(result)

                result.add_value('runtime', time.time() - starttime)
                self.result.append(result)

            except Queue.Empty:
                # we're done!
                pass
            finally:
                self.log("%s is finished" % self.name, LOG_DEBUG)
                self.queue.task_done() 


    def get_result(self):
        """ Get the result of the execution of the command.

            @return: L{NodeResult} object with all information
            @rtype: NodeResult
        """
        return self.result
