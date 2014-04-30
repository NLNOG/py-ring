#! /usr/bin/env python
"""
A python module to interact with the NLNOG ring.
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

import Queue, random, time, sys, urllib, urllib2, simplejson
from paramiko import Agent

from exception import RingException
from node import RingNode, NodeCommandThread
from result import NodeResult, NodeResultSet

# ===========================================================================

# number of concurrent threads
DFLT_MAX_THREADS = 25

# pastebin address
PASTEBIN = "https://ring.nlnog.net/paste/"

# ring API
RING_API = "https://ring.nlnog.net/api/1.0/"

# ===========================================================================

# caches for data
_nodes = {}
_countries = {}


def run_command(command, hosts, max_threads=DFLT_MAX_THREADS, analyse=None):
    ''' Run a command over a set of hosts using threading.
        A working SSH agent is needed for authentication.
        
        @param command: the command to be executed on the specified hosts.
        @type command: string

        @param hosts: the hosts on which the command is to be executed
        @type hosts: list

        @param max_threads: the number of concurrent threads used to
        interact with nodes
        @type max_threads: int

        @param analyse: a function which can be called to analyse the
        results of the execution of the command for each host. Argument
        of the function should be a L{NodeResult} variable.
        @type analyse: function

        @return: a L{NodeResultSet} with results for all hosts
        @rtype: NodeResultSet
    '''

    agent = Agent()
    queue = Queue.Queue()
    threads = {}

    # fork enough (but not too many) threads
    for i in range(min(max_threads, len(hosts))):
        threads[i] = NodeCommandThread(queue, command, agent, analyse=analyse)
        threads[i].setDaemon(True)
        threads[i].start()

    # add all hosts to the work queue
    for host in hosts:
        queue.put(host)

    # wait for threads to be done
    queue.join()

    # fix for some threading problems
    time.sleep(1)

    # gather results
    result = NodeResultSet()
    for i in range(min(max_threads, len(hosts))):
        result.append(threads[i].get_result())

    return result


def get_ring_nodes(country=None, active_only=False):
    ''' Get a list of all ring hosts.
        
        @param country: list only nodes hosted in this country. If not specified
        nodes in all countries are returned.
        @type country: str

        @param active_only: list only active nodes
        @type active_only: boolean

        @return: a list of node names

        @rtype: list of strings
    '''
    global _nodes, _countries

    if _nodes and not country:
        return _nodes.keys()
    elif _nodes and _countries:
        return _countries[country.upper()].keys()

    try:
        req = urllib2.Request("%snodes%s%s" % (RING_API, "/active" if active_only else "", "/country/%s" % country.upper() if country != None else ''))
        opener = urllib2.build_opener()
        f = opener.open(req)
        result = simplejson.load(f)
        if result["info"]["success"] == 1:
            nodes = {}
            for host in result["results"]["nodes"]:
                nodes[host["hostname"].replace(".ring.nlnog.net", "")] = host
                if not _countries.has_key(host['countrycode']):
                    _countries[host['countrycode']] = {}
                _countries[host["countrycode"]][host["hostname"].replace(".ring.nlnog.net", "")] = host
        _nodes = nodes
        return nodes.keys()
    except Exception, e:
        return {}


def get_ring_countries():
    ''' Get a list of all ring countries.
        
        @return: a list of country codes
        @rtype: list of strings
    '''

    global _countries
    if _countries:
        return _countries.keys()
    
    # update node list
    nodes = get_ring_nodes()

    # _countries is now available
    return _countries.keys()


def get_ring_networks():
    ''' Get a list of all ring networks.
        
        @return: a list of all network names
        @rtype: list of strings
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
               support_ipv4=None, support_ipv6_only=None,
               active_only=True):
    ''' Pick a set of ring hosts based on given criteria. If more nodes match
        the given criteria random nodes are picked.

        @param count: the number of hosts to be picked (at most)
        @type count: integer

        @param inc_hosts: hosts which must be included
        @type inc_hosts: string or list of strings

        @param ex_hosts: hosts which must be excluded
        @type ex_hosts: string or list of strings

        @param inc_countries: countries from which at least one node must be included
        @type inc_countries: string or list of strings

        @param ex_countries: countries which must be excluded
        @type ex_countries: string or list of strings

        @param only_countries: all nodes picked must be in these countries
        @type only_countries: string or list of strings

        @param inc_networks: networks from which at least one node must be included
        @type inc_networks: string or list of strings

        @param ex_networks: networks which must be excluded
        @type ex_networks: string or list of strings

        @param only_networks: all nodes picked must be in these networks
        @type only_networks: string or list of strings

        @param support_ipv4: all nodes picked must support IPv4 (dual-stacked)
        @type support_ipv4: boolean

        @param support_ipv6_only: all nodes picked must be IPv6-only
        @type support_ipv6_only: boolean

        @param active_only: pick only from nodes which are active
        @type active_only: boolean

        @return: a list of nodes matching the given criteria
        @rtype: list of strings
    '''
    random.seed(time.time())
    nodes = get_ring_nodes(active_only=active_only)
    nbc = get_nodes_by_country()
    cbn = get_countries_by_node()
    nbn = get_nodes_by_network()
    networks = get_ring_networks()
    v4 = {} 

    if count == 0:
        count = sys.maxint

    if support_ipv4 != None and support_ipv4 == False:
        support_ipv6_only = True

    for node in nodes:
        v4[node] = get_node_details(node)["ipv4"] != None
        
    if isinstance(inc_hosts, str):
        inc_hosts = [inc_hosts]
    elif inc_hosts == None:
        inc_hosts = []

    if isinstance(ex_hosts, str):
        ex_hosts = [ex_hosts]
    elif ex_hosts == None:
        ex_hosts = []

    if isinstance(inc_networks, str):
        inc_networks = [inc_networks]
    elif inc_networks == None:
        inc_networks = []

    if isinstance(ex_networks, str):
        ex_networks = [ex_networks]
    elif ex_networks == None:
        ex_networks = []

    if isinstance(only_networks, str):
        only_networks = [only_networks]
    elif only_networks == None:
        only_networks = []

    if isinstance(inc_countries, str):
        inc_countries = [inc_countries.upper()]
    elif inc_countries == None:
        inc_countries = []
    else:
        inc_countries = [c.upper() for c in inc_countries]

    if isinstance(ex_countries, str):
        ex_countries = [ex_countries.upper()]
    elif ex_countries == None:
        ex_countries = []
    else:
        ex_countries = [c.upper() for c in ex_countries]

    if isinstance(only_countries, str):
        only_countries = [only_countries.upper()]
    elif only_countries == None:
        only_countries = []
    else:
        only_countries = [c.upper() for c in only_countries]


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
               (cbn.get(h, '').upper() not in ex_countries) and 
               (cbn.get(h, '').upper() in only_countries or len(only_countries) == 0)):
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
           (nbn.get(h, '').upper() not in ex_networks) and (cbn.get(h, '') not in ex_countries) and
           (cbn.get(h, '').upper() in only_countries or len(only_countries) == 0) and
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


def is_ring_node(name):
    ''' Determine if a name is a name of an existing ringnode.

        @param name: the name to be checked
        @type name: string

        @return: I{True} if the name is a valid node name, else I{False}
        @rtype: boolean
    '''
    return name in get_ring_nodes()


def is_ring_country(country):
    ''' Determine if a country has any ring nodes.

        @param country: the country to be checked
        @type country: string

        @return: I{True} if the country has any nodes, else I{False}
        @rtype: boolean
    '''
    return country.upper() in get_ring_countries()


def get_countries_by_node():
    ''' Get a dictionary containing the country a node is in for each node. 
        
        @return: a dictionary containing node->country mappings
        @rtype: dictionary
    '''
    result = {}
    countries = get_ring_countries()
    for country in countries:
        nodes = get_ring_nodes(country) 
        for node in nodes:
            result[node] = country

    return result


def get_nodes_by_country():
    ''' Get a dictionary containing all nodes per country.

        @return: a dictonary containing country->list of nodes mappings
        @rtype: dictionary
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
    ''' Get a dictionary containing all nodes per network.

        @return: a dictionary containing network->list of nodes mappings
        @rtype: dictionary
    '''
    result = {}
    nodes = get_ring_nodes()
    for node in nodes:
        if not node[:-2] in result.keys():
            result[node[:-2]] = []
        result[node[:-2]].append(node)
    
    return result


def get_node_country(node):
    ''' Look up in which country a node is

        @param node: the name of the node
        @type node: string

        @return: the country code of the node
        @rtype: string
    '''

    return get_countries_by_node()[node]


def get_node_details(node):
    ''' Get detailed information of a node

        @param node: the name of the node
        @type node: string
        
        @return: a dictionary with detailed info
        @rtype: dictionary
    '''
    global _nodes

    nodes = get_ring_nodes()
    if node in nodes:
        return _nodes[node]
    else:
        return None


def pastebin(text):
    ''' Put text on the NLNOG pastebin
        
        @param text: the text to put on the pastebin
        @type text: string

        @return: the unique pastebin url
        @rtype: string

        @raise RingException: if the paste fails
    '''
    postarray = [
        ("content", text),
        ("mimetype", "text/html"),
        ("ttl", 604800)
    ]
    postdata = urllib.urlencode(postarray)
    try:
        req = urllib2.Request(url=PASTEBIN, data=postdata)   
        result = urllib2.urlopen(req)
        if result.url == PASTEBIN:
            raise RingException("failed to put the text on the pastebin.")
        else:
            return result.url
    except:
        raise RingException("failed to put the text on the pastebin.")
