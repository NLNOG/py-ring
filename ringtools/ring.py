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

import Queue
from dns.resolver import query
from dns.exception import DNSException
from paramiko import Agent

from exception import RingException
from node import RingNode, NodeCommandThread
from result import NodeResult, NodeResultSet

from paramiko import Agent
# ===========================================================================

DFLT_MAX_THREADS = 25           # number of concurrent threads

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


def get_ring_nodes(country=None):
    '''Get a list of all ring hosts using a TCP DNS query.
       Optionally, specify the country for which the lookup has to be done.
    '''
    hosts = []
    try:
        # TCP query required due to the large TXT record
        qres = query("%sring.nlnog.net" % ("%s." % country if country != None else ''), "TXT", tcp=True)
        for rr in qres:
            for s in rr.strings:
                for srv in s.split(' '):
                    hosts.append(srv)
    except DNSException, e:
        return []

    hosts.sort()
    return hosts


def get_ring_countries():
    '''Get a list of all ring countries.
    '''

    countries = []
    try:
        # TCP query required due to the large TXT record
        qres = query("countries.ring.nlnog.net", "TXT", tcp=True)
        for rr in qres:
            for s in rr.strings:
                for srv in s.split(' '):
                    countries.append(srv)
    except DNSException, e:
        return []

    countries.sort()
    return countries


def get_ring_networks():
    '''Get a list of all ring networks.
    '''

    networks = {}
    hosts = get_ring_nodes()
    for h in hosts:
        networks[h[:-2]] = 1
    return networks.keys()
    

def pick_nodes(count, include=[], exclude=[]):
    '''Pick a set of ring hosts. 
    '''
    nodes = get_ring_nodes()

    if isinstance(include, str):
        include = [include]
    if isinstance(exclude, str):
        exclude = [exclude]
    
    if count >= len(nodes):
        return nodes
    if len(include) >= count:
        return include
    else:
        newlist = include
        for x in range(count - len(include)):
            i = random.randint(0, len(nodes) - 1)
            newlist.append(nodes[i])
            nodes.remove(nodes[i])
        for x in exclude:
            newlist.remove(x)
        return newlist


def is_ring_node(host):
    '''determine if a name is a name of an existing ringnode
    '''
    return host in get_ring_nodes()


def is_ring_country(country):
    '''determine if a country has any ringnodes.
    '''

    return country in get_ring_countries()


def get_countries_by_node():
    '''Get a map of node->country entries
    '''
    result = {}
    countries = get_ring_countries()
    for country in countries:
        nodes = get_ring_nodes(country) 
        for node in nodes:
            result[node] = country

    return result


def get_nodes_by_country():
    '''Get a list of all nodes per country
    '''
    result = {}
    countries = get_ring_countries()
    for country in countries:
        result[country] = []
        nodes = get_ring_nodes(country) 
        for node in nodes:
            result[country].append(node)

    return result


def get_node_country(node):
    '''Look up in which country a node is
    '''

    return get_countries_by_node()[node]
