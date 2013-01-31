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

import Queue, random
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
    

def _get_node_add_pref(node, i_h, e_h, i_c, e_c, i_n, e_n, v4, v6, cbn, v4nodes):
    # determine the preference of a node to be added
    # higher = better


    # mentioned in host include
    if node in i_h:
        return 4

    # mentioned in host_exclude
    if node in e_h:
        return 0

    # v4 required, no v4 support
    if v4 and not v4nodes[node]:
        return 0

    # v6 only required and v4 supported
    if v6 and v4nodes[node]:
        return 0

    # mentioned in network exclude
    if node[:-2] in e_n:
        return 0

    # mentioned in country exclude
    if cbn.get(node, 'unknown') in e_c:
        return 0
    
    # mentioned in network include
    if node[:-2] in i_n:
        return 3

    # mentioned in country include
    if cbn.get(node, 'unknown') in i_c:
        return 2

    # finally
    return 1


def pick_nodes(count, 
               inc_hosts=[], ex_hosts=[], 
               inc_countries=[], ex_countries=[], 
               inc_networks=[], ex_networks=[],
               support_ipv4=False, support_ipv6_only=False,
               unique_countries=False, unique_networks=False):
    '''Pick a set of ring hosts, specific filters can be given optionally
    '''
    nodes = get_ring_nodes()
    nbc = get_nodes_by_country()
    cbn = get_countries_by_node()
    nbn = get_nodes_by_network()
    networks = get_ring_networks()
    v4 = {}
    for node in nodes:
        v4[node] = node_has_ipv4(node)

    if isinstance(inc_hosts, str):
        inc_hosts = [inc_hosts]
    if isinstance(ex_hosts, str):
        ex_hosts = [ex_hosts]
    if isinstance(inc_countries, str):
        inc_countries = [inc_countries]
    if isinstance(ex_countries, str):
        ex_countries = [ex_countries]
    if isinstance(inc_networks, str):
        inc_networks = [inc_networks]
    if isinstance(ex_networks, str):
        ex_networks = [ex_networks]
   
    newlist = []

    prefs = {}
    for node in nodes:
        # TODO: dit enigszins herschrijven zodat er in preflevels blokjes van hosts toegevoegd worden op basis van country/net
        # dus bijv als inc_countr='fr' dan moet ['fr1','fr2','fr3'] als array van 'kies er hier een uit' toegevoegd worden aan de set met mogelijk geschikte nodes
        # je zou dan dus iets krijgen als [ node1, node2, [node1 | node 2], [node 3|node 4] node 5]
        # waarbij iedere sub-array geregeld wordt door een inc_*
        pref = _get_node_add_pref(node, inc_hosts, ex_hosts, inc_countries, ex_countries, inc_networks, ex_networks, support_ipv4, support_ipv6_only, cbn, v4)
        if not prefs.has_key(pref):
            prefs[pref] = []
        prefs[pref].append(node)

    # only examine prefs 4 downto 1, pref 0 is used for nodes which need to be excluded
    for pref in range(4, 0, -1):
        # TODO: properly handle subsets
        todo = count - len(newlist)
        if len(prefs[pref])> 0:
            # add all nodes in this pref lvl
            if len(prefs[pref]) <= todo:
                newlist.append(prefs[pref])
            else:
                # TODO: pick #todo items from prefs[pref]
                pass

            
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
