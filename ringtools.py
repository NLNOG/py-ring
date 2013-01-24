#! /usr/bin/env python
#
# ABOUT
# =====
# py-ring - A generic module for running commands on nodes of the NLNOG 
# ring. More information about the ring: https://ring.nlnog.net
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

import threading, sys, Queue, os, time, random, socket, operator
from dns.resolver import query
from dns import name, reversename
from dns.exception import DNSException
from paramiko import *

# ===========================================================================

DFLT_SSH_TIMEOUT = 20           # seconds
DFLT_FQDN = "ring.nlnog.net"    # fqdn for hosts
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


class RingException(Exception):
    def __init__(self, message):
        self.message = message


    def __str__(self):
        return repr(self.message)


# ===========================================================================


class NodeResult:
    ''' a class containing results of a specific node
    '''
    SSH_OK      = 0
    SSH_TIMEOUT = 1
    SSH_ERROR   = 2


    def __init__(self, hostname=None, ssh_result=None, exitcode=None, 
                 stdout=None, stderr=None):
        self.hostname = hostname
        self.ssh_result = ssh_result
        self.ssh_errmsg = None
        self.exitcode = exitcode
        self.stdout = stdout
        self.stderr = stderr
        self.values = {}


    def get_hostname(self):
        return self.hostname


    def set_hostname(self, hostname):
        self.hostname = hostname


    def get_ssh_result(self):
        return self.ssh_result


    def set_ssh_result(self, ssh_result):
        self.ssh_result = ssh_result


    def get_ssh_errormsg(self):
        return self.ssh_errormsg


    def set_ssh_errormsg(self, ssh_errormsg):
        self.ssh_errormsg = ssh_errormsg


    def get_exitcode(self):
        return self.exitcode


    def set_exitcode(self, exitcode):
        self.exitcode = exitcode


    def get_stdout(self):
        return self.stdout


    def set_stdout(self, stdout):
        self.stdout = stdout


    def get_stderr(self):
        return self.stderr


    def set_stderr(self, stderr):
        self.stderr = stderr


    def add_value(self, name, value):
        self.values[name] = value


    def get_value(self, name):
        return self.values.get(name, None)


    def get_values(self):
        return self.values


    def __repr__(self):
        if self.hostname:
            return "<results for node %s. ssh_result: %d, ssh_errmsg: '%s', exitcode: %s, values: %s>" % (
                self.hostname, self.ssh_result, self.ssh_errmsg, self.exitcode, 
                ', '.join(["'%s': '%s'" % (x, self.get_value(x)) for x in self.get_values().keys()]))
        else:
            return "results for unknown node"


# ===========================================================================


class NodeResultSet:
    '''Set of node results
    '''

    def __init__(self, results=None):
        self.results = []
        self.append(results)


    def append(self, results):
        if isinstance(results, NodeResult):
            self.results.append(results)
        elif isinstance(results, list):
            for r in results:
                if isinstance(r, NodeResult):
                    self.results.append(r)
        elif isinstance(results, NodeResultSet):
            for r in results.get_results():
                self.results.append(r)


    def get_hostnames(self):
        return [r.get_hostname() for r in self.results]


    def get_results(self):
        return self.results


    def get_successful_results(self):
        '''List only all nodes which have run the command with return code 0.
        '''
        results = []
        for result in self.results:
            if result.get_ssh_result() == NodeResult.SSH_OK and result.get_exitcode() == 0:
                results.append(result)
        return NodeResultSet(results)
    

    def get_failed_results(self, include_ssh_problems = True, only_ssh_problems = False):
        '''List only the nodes which failed to run correctly.
        '''
        results = []
        for result in self.results:
            e = result.get_exitcode()
            s = result.get_ssh_result()
            if not e == 0:
                if not only_ssh_problems and s == NodeResult.SSH_OK:
                    results.append(result)
                elif only_ssh_problems and include_ssh_problems and s != NodeResult.SSH_OK:
                    results.append(result)
        return NodeResultSet(results)

    
    def count_results(self):
        return len(self.results)


    def get_value(self, name):
        result = {}
        for r in self.results:
            result[r.get_hostname()] = r.get_value(name)
        return result


    def get_value_sorted(self, name):
        return sorted(self.get_value(name).iteritems(), key=operator.itemgetter(1))


    def __repr__(self):
        return "<result set for: %s>" % ", ".join(self.get_hostnames())

# ===========================================================================

class RingNode:
    STATE_DISCONNECTED = 0
    STATE_CONNECTED = 1
    STATE_AUTHENTICATED = 2

    def __init__(self, hostname=None, username=None, ssh_client=None, ssh_agent=None, ssh_config=None, timeout=DFLT_SSH_TIMEOUT):
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

        return NodeResult(
            hostname = self.hostname,
            ssh_result= NodeResult.SSH_OK,
            exitcode = channel.recv_exit_status(),
            stdout = [line.strip() for line in self.stdout], 
            stderr = [line.strip() for line in self.stderr])


    def get_state(self):
        return self.state

# ===========================================================================


class NodeCommandThread(threading.Thread):
    ''' a thread for processing commands to a node via SSH
    '''

    def __init__(self, queue, command, agent, timeout=DFLT_SSH_TIMEOUT, loglevel=LOG_DEBUG):
        self.queue = queue
        self.command = command
        self.agent = agent
        self.timeout = timeout
        self.result = NodeResultSet()
        self.loglevel = loglevel
        threading.Thread.__init__(self)


    def log(self, msg, loglevel=LOG_INFO):
        if self.loglevel >= loglevel:
            print "[%s] %5s: %s" % (time.strftime('%H:%M:%S'), LOG_STR[loglevel], msg)
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
                node = RingNode(host)
                try:
                    # some template replacements
                    cmd = self.command.replace("%%HOST%%", host)
                    result = node.run_command(cmd)
                    node.close()
                except RingException, e:
                    result.set_ssh_errormsg(e.__str__())

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


# ===========================================================================

def run_command(command, hosts, max_threads=DFLT_MAX_THREADS):
    ''' Run a command over a set of hosts using threading.
        A working SSH agent is for authentication.
    '''

    agent = Agent()
    queue = Queue.Queue()
    threads = {}

    # fork enough (but not too many) threads
    for i in range(min(max_threads, len(hosts))):
        threads[i] = NodeCommandThread(queue, command, agent)
        threads[i].setDaemon(True)
        threads[i].start()

    # add all hosts to the work queue
    for host in hosts:
        queue.put(host)

    # wait for threads to be done
    queue.join()

    # gather results
    result = NodeResultSet()
    for i in range(min(max_threads, len(hosts))):
        result.append(threads[i].get_result())

    return result


def get_hostlist():
    '''Get a list of all ring hosts using a TCP DNS query.
    '''
    hosts = []
    try:
        # TCP query required due to the large TXT record
        qres = query("ring.nlnog.net", "TXT", tcp=True)
        for rr in qres:
            for s in rr.strings:
                for srv in s.split(' '):
                    hosts.append(srv)
    except DNSException, e:
        return []

    return hosts


def pick_hosts(count, include=[], exclude=[]):
    '''Pick a set of ring hosts. 
    '''
    hosts = get_hostlist()

    if isinstance(include, str):
        include = [include]
    if isinstance(exclude, str):
        exclude = [exclude]
    
    if count >= len(hosts):
        return hosts
    if len(include) >= count:
        return include
    else:
        newlist = include
        for x in range(count - len(include)):
            i = random.randint(0, len(hosts) - 1)
            newlist.append(hosts[i])
            hosts.remove(hosts[i])
        for x in exclude:
            Gnewlist.remove(x)
        return newlist


def is_ringnode(host):
    '''determine if a name is a name of an existing ringnode
    '''
    return host in get_hostlist()
