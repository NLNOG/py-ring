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

import Queue, random, time
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
    

def pick_nodes(count, 
               inc_hosts=[], ex_hosts=[], 
               inc_countries=[], ex_countries=[], only_countries=[],  
               inc_networks=[], ex_networks=[], only_networks=[],
               support_ipv4=None, support_ipv6_only=None):
    '''Pick a set of ring hosts, specific filters can be given optionally
    '''
    random.seed(time.time())
    nodes = get_ring_nodes()
    nbc = get_nodes_by_country()
    cbn = get_countries_by_node()
    nbn = get_nodes_by_network()
    networks = get_ring_networks()
    v4 = {} 

    if support_ipv4 != None and support_ipv4 == False:
        support_ipv6_only = True

    for node in nodes:
        v4[node] = node_has_ipv4(node)
        
    if isinstance(inc_hosts, str):
        inc_hosts = [inc_hosts]
    if isinstance(ex_hosts, str):
        ex_hosts = [ex_hosts]
    if isinstance(inc_networks, str):
        inc_networks = [inc_networks]
    if isinstance(ex_networks, str):
        ex_networks = [ex_networks]
    if isinstance(only_networks, str):
        only_networks = [only_networks]
    if isinstance(inc_countries, str):
        inc_countries = [inc_countries]
    if isinstance(ex_countries, str):
        ex_countries = [ex_countries]
    if isinstance(only_countries, str):
        only_countries = [only_countries]
   
    newlist = []

    # start with all explicitly included hosts
    if inc_hosts:
        for h in inc_hosts:
            if h in nodes:
                newlist.append(h)
            nodes.remove(h)

    # for each network to be included pick a node
    for n in inc_networks:
        valid = []
        for h in nbn.get(n, ''):
            if ((not h in newlist) and (not h in ex_hosts) and
               ((support_ipv4 != None and ((support_ipv4 and v4.get(h, False)) or not support_ipv4)) or support_ipv4 == None) and
               ((support_ipv6_only != None and ((support_ipv6_only and not v4.get(h, True)) or not support_ipv6_only)) or support_ipv6_only == None) and
               (cbn.get(h, '') not in ex_countries) and 
               (cbn.get(h, '') in only_countries or len(only_countries) == 0)):
                    valid.append(h)
        if len(valid) > 0:
            r = random.randint(0, len(valid) - 1)
            newlist.append(valid[r])
            nodes.remove(valid[r])

    # for each country to be included pick a host
    for c in inc_countries:
        valid = []
        for h in nbc.get(c, ''):
            if ((not h in newlist) and (not h in ex_hosts) and
               ((support_ipv4 != None and ((support_ipv4 and v4.get(h, False)) or not support_ipv4)) or support_ipv4 == None) and
               ((support_ipv6_only != None and ((support_ipv6_only and not v4.get(h, True)) or not support_ipv6_only)) or support_ipv6_only == None) and
               (nbn.get(h, '') not in ex_networks) and
               (h[:-2] in only_networks or len(only_networks) == 0)):
                    valid.append(h)
        if len(valid) > 0:
            r = random.randint(0, len(valid) - 1)
            newlist.append(valid[r])
            nodes.remove(valid[r])

    # select all possibly valid hosts 
    valid = []
    for h in nodes:
        if ((not h in newlist) and (not h in ex_hosts) and
           ((support_ipv4 != None and ((support_ipv4 and v4.get(h, False)) or not support_ipv4)) or support_ipv4 == None) and
           ((support_ipv6_only != None and ((support_ipv6_only and not v4.get(h, True)) or not support_ipv6_only)) or support_ipv6_only == None) and
           (nbn.get(h, '') not in ex_networks) and (cbn.get(h, '') not in ex_countries) and
           (cbn.get(h, '') in only_countries or len(only_countries) == 0) and
           (h[:-2] in only_networks or len(only_networks) == 0)):
                valid.append(h)

    # add enough nodes upto the requested number
    if len(valid) + len(newlist) <= count:
        [newlist.append(v) for v in valid]
    elif len(valid) > 0:
        for i in range(count - len(newlist)):
            r = random.randint(0, len(valid) - 1)
            newlist.append(valid[r])
            valid.remove(valid[r])
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


def get_nodes_by_network():
    '''Get a list of all nodes for a network
    '''
    result = {}
    nodes = get_ring_nodes()
    for node in nodes:
        if not node[:-2] in result.keys():
            result[node[:-2]] = []
        result[node[:-2]].append(node)
    
    return result


def get_node_country(node):
    '''Look up in which country a node is
    '''

    return get_countries_by_node()[node]


def node_has_ipv4(node):
    '''determine if a node support ipv4
    '''

    if not node in get_ring_nodes():
        return False
    else:
        try:
            result = query("%s.ring.nlnog.net" % node, "A")
            return True
        except DNSException:
            return False
