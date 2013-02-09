#! /usr/bin/env python
"""
Results of commands performed on the ring.
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

import operator
from exception import RingException

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
        self.ssh_errormsg = None
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
            return "<results for node %s. ssh_result: %s, ssh_errmsg: '%s', exitcode: %s, values: %s>" % (
                self.hostname, self.ssh_result, self.ssh_errormsg, self.exitcode, 
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


    def get_result(self, node):
        for r in self.results:
            if r.get_hostname() == node:
                return r

        # nothing found
        raise RingException("Result for node %s not found in resultset." % node)


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
            if e > 0 and not only_ssh_problems:
                results.append(result)
            elif s > 0 and include_ssh_problems:
                results.append(result)

        return NodeResultSet(results)

    
    def count_results(self):
        return len(self.results)


    def get_value(self, name):
        result = {}
        for r in self.results:
            result[r.get_hostname()] = r.get_value(name)
        return result


    def get_value_sorted(self, name, reverse=False):
        '''return a sorted list of (host, value) tuples for variable 'name'
        '''
        return sorted(self.get_value(name).iteritems(), key=operator.itemgetter(1), reverse=reverse)


    def get_value_avg(self, name):
        tot = 0
        count = 0
        for v in self.results:
            val = v.get_value(name)
            if isinstance(val, int) or isinstance(val, float):
                tot += val
                count += 1
            else:
                raise RingException("Cannot calculate average over non-numeric values.")

        return tot/count if count > 0 else 0


    def get_value_grouped(self, name, sort_by_hostcount=False):
        '''Get a list of tuples (value, hosts) for variable 'name',
           optionally sorted by the number of hosts per value.
        '''
        rev = {}
        res = self.get_value(name)

        for host in res:
            if res[host] in rev.keys():
                rev[res[host]].append(host)
            else:
                rev[res[host]] = [host]
        if sort_by_hostcount:
            return [(s, rev[s]) for s in sorted(rev.keys(), key=lambda l: len(rev[l]))]
        else:
            return sorted(rev.iteritems(), key=operator.itemgetter(1))


    def __repr__(self):
        return "<result set for: %s>" % ", ".join(self.get_hostnames())
