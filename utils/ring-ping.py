#! /usr/bin/env python
"""
ring-ping performs a series of pings from various ring nodes and shows the results.
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

import sys, argparse
from operator import itemgetter

try:
    from ringtools import ring, result
except ImportError:
    # ringtools probaly isn't installed yet
    sys.path.append('..')
    from ringtools import ring, result

VERSION="0.1"

def analyzer(result):
    # callback to analyse the results: if the command exited ok
    # we select the average pingtime from the result and add it to the dataset
    if result.get_exitcode() == 0:
        avg = result.get_stdout()[-1].split(" ")[3].split("/")[1]
        result.add_value("avg", float(avg))

def split_args(args):
    result = []
    if args == None:
        return []

    for arg in args:
        x = arg.split(',')
        [ result.append(r.strip()) for r in x ]
    return result


def main():
    parser = argparse.ArgumentParser(
        description="Run ping on the NLNOG ring.",
        epilog="Visit https://ring.nlnog.net for more information",
        formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument(
        "-6", "--ipv6", help="enforce IPv6", 
        action="store_const", dest="ipv6", 
        const=True, default=False)

    parser.add_argument(
        "-c", "--count", 
        help="the number of nodes to ping from", 
        action="store", dest="count", 
        default=10, type=int)
    
    parser.add_argument(
        "-C", "--pingcount", 
        help="the number of ping requests", 
        action="store", dest="pingcount", 
        default=1, type=int)

    parser.add_argument(
        "-e", "--errors", 
        help="detailed error reporting", 
        action="store_const", dest="errors", 
        default=False, const=True)
    
    parser.add_argument(
        "-n", "--include-node", help="include specific node", 
        action="append", dest="in_nodes",
        default=None, metavar="node")
   
    parser.add_argument(
        "-N", "--exclude-node", help="exclude specific node", 
        action="append", dest="ex_nodes", 
        default=None, metavar="node")
    
    parser.add_argument(
        "-o", "--include-country", help="include specific country", 
        action="append", dest="in_countries",
        default=None, metavar="country")

    parser.add_argument(
        "-oo", "--only-country", help="only specific country", 
        action="append", dest="only_countries",
        default=None, metavar="country")

    parser.add_argument(
        "-O", "--exclude-country", help="exclude specific country", 
        action="append", dest="ex_countries",
        default=None, metavar="country")
    
    parser.add_argument(
        "-q", "--quiet", help="quiet mode, print only results", 
        action="store_const", dest="quiet", 
        default=False, const=True)
    
    parser.add_argument(
        "-r", "--country", help="group results by country", 
        action="store_const", dest="country", 
        default=False, const=True)

    parser.add_argument(
        "-t", "--threads", 
        help="the number of concurrent ping threads", 
        action="store", dest="threads", 
        default=25, type=int)

    parser.add_argument(
        "-w", "--include-network", help="include specific network", 
        action="append", dest="in_networks",
        default=None, metavar="network")
    
    parser.add_argument(
        "-ww", "--only-network", help="only specific network", 
        action="append", dest="only_networks",
        default=None, metavar="network")

    parser.add_argument(
        "-W", "--exclude-network", help="exclude specific network", 
        action="append", dest="ex_networks",
        default=None, metavar="network")
    

    parser.add_argument("destination", help="target of the ping command")

    ns = parser.parse_args()

    in_nodes = split_args(ns.in_nodes)
    ex_nodes = split_args(ns.ex_nodes)
    in_countries = split_args(ns.in_countries)
    ex_countries = split_args(ns.ex_countries)
    only_countries = split_args(ns.only_countries)
    in_networks = split_args(ns.in_networks)
    ex_networks = split_args(ns.ex_networks)
    only_networks = split_args(ns.only_networks)

    nodes = ring.pick_nodes(count=ns.count, 
        inc_hosts=in_nodes, ex_hosts=ex_nodes,
        inc_countries=in_countries, ex_countries=ex_countries, 
        only_countries=only_countries, inc_networks=in_networks, 
        ex_networks=ex_networks, only_networks=only_networks)

    if not ns.quiet:
        print "ring-ping v%s written by Teun Vink <teun@teun.tv>\n" % VERSION
        print "pinging %s from %d nodes:" % (ns.destination, len(nodes))

    cmd_result = ring.run_command('ping%s -c%s -q %s' % ("6" if ns.ipv6 else "", ns.pingcount, ns.destination), 
        nodes, max_threads=ns.threads, analyse=analyzer)
    ok = cmd_result.get_successful_results()
    fail = cmd_result.get_failed_results(include_ssh_problems=False)
    conn = cmd_result.get_failed_results(only_ssh_problems=True)

    sort = ok.get_value_sorted("avg")
    cbn = ring.get_countries_by_node()

    if ns.country:
        countries = ring.get_ring_countries()
        countries.sort()
        nbc = ring.get_countries_by_node()
        res = {}
        for (host, val) in sort:
            if res.has_key(nbc[host]):
                res[nbc[host]].append(val)
            else:
                res[nbc[host]] = [val]
        avg = {}
        for country in countries:
            if res.has_key(country):
                avg[country] = sum(res[country])/len(res[country])
        sort = sorted(avg.iteritems(), key=itemgetter(1))
        print "Average ping time per country:"
        for (c, a) in sort:
            print "{0:3s}: {1:6.2f}ms".format(c, a)
    elif not ns.quiet:
        for (host, val) in sort:
            hostname = "%s (%s):" % (host, cbn[host].upper())
            v = "%.2fms" % val
            print "%-28s %8s   " % (hostname, v)

        if len(conn.get_results()) > 0 and ns.errors:
            print "\nconnection failures:"
            for r in conn.get_results():
                hostname = "%s (%s):" % (r.get_hostname(), cbn[r.get_hostname()].upper())
                print "%-28s %s" % (hostname, r.get_ssh_errormsg())

        if len(fail.get_results()) > 0 and ns.errors:
            print "\ncommand execution problems:"
            for r in fail.get_results():
                hostname = "%s (%s):" % (r.get_hostname(), cbn[r.get_hostname()].upper())
                print "%-28s exitcode = %s" % (hostname, r.get_exitcode())
                if r.get_stderr():
                    print ", message: %s" % r.get_stderr()[0]

        print

    print "%d nodes ok (%.2fms avg), %d nodes failed to ping, failed to connect to %d nodes." % (
        len(ok.get_results()),
        ok.get_value_avg("avg"),
        len(fail.get_results()),
        len(conn.get_results()))

if __name__ == "__main__":
    main()
