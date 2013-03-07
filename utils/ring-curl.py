#! /usr/bin/env python
"""
ring-curl performs a series of curl requests from various ring nodes and shows the results.
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
from BeautifulSoup import BeautifulSoup
from curlerr import CURL_ERRORS

try:
    from ringtools import ring, result
except ImportError:
    # ringtools probaly isn't installed yet
    sys.path.append('..')
    from ringtools import ring, result


VERSION = "0.1"
AGENT = "ring-curl.py - http://ring.nlnog.net"


def analyzer(result):
    # callback to analyse the results: if the command exited ok
    # we select the average pingtime from the result and add it to the dataset
    if result.get_exitcode() == 0 and len(result.get_stdout()) > 0:
        stdout = result.get_stdout()
        result.add_value('HTTP-code', stdout[0])

        i = 1 # first line was the HTTP-code
        while stdout[i].strip() != "":
            if ":" in stdout[i]:
                x = stdout[i].split(': ', 2)
                result.add_value(x[0].strip(), x[1].strip())
            i += 1
        try:
            soup = BeautifulSoup("\n".join(stdout[i:]))
            result.add_value('title', soup.title.string if soup.title else '<<none>>')
        except:
            pass


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
        description="Run curl requests on the NLNOG ring.",
        epilog="Visit https://ring.nlnog.net for more information",
        formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument(
        "-6", "--ipv6", help="enforce IPv6",
        action="store_const", dest="ipv6",
        const=True, default=False)

    parser.add_argument(
        "-c", "--count",
        help="the number of nodes to do requests from",
        action="store", dest="count",
        default=10, type=int)
    
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

    parser.add_argument("destination", help="target URL")

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
        print "ring-curl v%s written by Teun Vink <teun@teun.tv>\n" % VERSION
        print "opening URL '%s' from %d nodes:" % (ns.destination, len(nodes))

    cmd = 'curl --connect-timeout 15 -L -i -A "%s" -s %s' % (AGENT, ns.destination)
    cmd_result = ring.run_command(cmd, nodes, analyse=analyzer)

    s_res = cmd_result.get_successful_results()
    s_res_t = s_res.get_value_sorted('runtime')
    s_res_h = s_res.get_value('HTTP-code')
    fail = cmd_result.get_failed_results(include_ssh_problems=False)
    conn = cmd_result.get_failed_results(only_ssh_problems=True)

    cbn = ring.get_countries_by_node()

    if not ns.quiet:
        for (host, val) in s_res_t:
            hostname = "%s (%s):" % (host, cbn[host].upper())
            v = "%.2fs" % val
            print "%-28s %8s  %s" % (hostname, v, s_res_h[host])

        if len(conn.get_results()) > 0 and ns.errors:
            print "\nconnection failures:"
            for r in conn.get_results():
                hostname = "%s (%s):" % (r.get_hostname(), cbn[r.get_hostname()].upper())
                print "%-28s %s" % (hostname, r.get_ssh_errormsg())

        if len(fail.get_results()) > 0 and ns.errors:
            print "\ncommand execution problems:"
            for r in fail.get_results():
                hostname = "%s (%s):" % (r.get_hostname(), cbn[r.get_hostname()].upper())
                print "%-28s exitcode %s: %s" % (hostname, r.get_exitcode(), CURL_ERRORS.get(r.get_exitcode(), "unknown"))

        print

    print "%d nodes succeeded, %d nodes failed to retrieve the URL, failed to connect to %d nodes." % (
        len(s_res.get_results()),
        len(fail.get_results()),
        len(conn.get_results()))

if __name__ == "__main__":
    main()
