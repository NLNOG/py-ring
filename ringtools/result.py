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
        """ Create a new NodeResult object containing results of 
            execution of a command on a node.

            @param hostname: the name of the node
            @type hostname: string

            @param ssh_result: the result of the SSH connection
            (L{SSH_OK}, L{SSH_TIMEOUT} or L{SSH_ERROR})
            @type ssh_result: integer

            @param exitcode: the Linux exitcode of the command 
            @type exitcode: integer

            @param stdout: the data printed by the command to stdout
            @type stdout: list of strings

            @param stderr: the data printed by the command to stderr
            @type stderr: list of strings
        """
        self.hostname = hostname
        self.ssh_result = ssh_result
        self.ssh_errormsg = None
        self.exitcode = exitcode
        self.stdout = stdout
        self.stderr = stderr
        self.values = {}


    def get_hostname(self):
        """ Get the hostname of this result. 

            @return: the hostname
            @rtype: string
        """
        return self.hostname


    def set_hostname(self, hostname):
        """ Set the hostname.
            
            @param hostname: name of the host
            @type hostname: string
        """
        self.hostname = hostname


    def get_ssh_result(self):
        """ Get the result SSH connection.

            @return: the result of the SSH connection
            (L{SSH_OK}, L{SSH_TIMEOUT} or L{SSH_ERROR})
            @rtype: integer
        """
        return self.ssh_result


    def set_ssh_result(self, ssh_result):
        """ Set the result of the SSH connection.

            @param ssh_result: the result of the SSH connection
            (L{SSH_OK}, L{SSH_TIMEOUT} or L{SSH_ERROR})
            @type ssh_result: integer
        """
        self.ssh_result = ssh_result


    def get_ssh_errormsg(self):
        """ Get the SSH error message.

            @return: the last SSH error message
            @rtype: string
        """
        return self.ssh_errormsg


    def set_ssh_errormsg(self, ssh_errormsg):
        """ Set the SSH error message.

            @param ssh_errormsg: the SSH error message
            @param ssh_errormsg: string
        """
        self.ssh_errormsg = ssh_errormsg


    def get_exitcode(self):
        """ Get the exitcode of the process executed.

            @return: the exitcode
            @rtype: integer
        """
        return self.exitcode


    def set_exitcode(self, exitcode):
        """ Set the exitcode of the process executed.

            @param exitcode: the exitcode
            @type exitcode: integer
        """
        self.exitcode = exitcode


    def get_stdout(self):
        """ Get the stdout process output.

            @return: the stdout output
            @rtype: list of strings
        """
        return self.stdout


    def set_stdout(self, stdout):
        """ Set the stdout process output.

            @param stdout: the stdout output
            @type stdout: list of strings
        """
        self.stdout = stdout


    def get_stderr(self):
        """ Get the stderr process output.

            @return: the stderr output
            @rtype: list of strings
        """
        return self.stderr


    def set_stderr(self, stderr):
        """ Set the stderr process output.

            @param stderr: the stdout output
            @type stderr: list of strings
        """
        self.stderr = stderr


    def add_value(self, name, value):
        """ Add a name/value pair to the result dictionary.
        
            @param name: name of the pair
            @type name: string

            @param value: value of the pair
            @type value: any
        """
        self.values[name] = value


    def get_value(self, name):
        """ Retrieve a value from the result dictionary.

            @param name: name of the value to retrieve
            @type name: string

            @return: the value stored in the result dictionary
            or None if not available.
        """
        return self.values.get(name, None)


    def get_values(self):
        """ Get all values from the result dictionary.

            @return: the entire result dictionary
            @rtype: dictionary
        """
        return self.values


    def __repr__(self):
        """ Fancy textual representation of the object.

            @return: textual representation of the object.
            @rtype: string
        """
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
        """ Create a new object. Optionally add data.

            @param results: results to be added
            @type results: list of L{NodeResult} objects
        """
        self.results = []
        self.append(results)


    def append(self, results):
        """ Add one or more values to the result set.

            @param results: the L{NodeResult} object(s) to be added
            @type results: L{NodeResult} or list of L{NodeResult} objects
        """
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
        """ Get the names of all hosts with results in the result set.

            @return: a list of all hostnames
            @rtype: list of strings
        """
        return [r.get_hostname() for r in self.results]


    def get_result(self, node):
        """ Get the results for a specific node in the result set.

            @param node: name of the node for which results are wanted
            @type node: string

            @return: result data for requested node
            @rtype: L{NodeResult} object

            @raise RingException: if the node doesn't exist
        """
        for r in self.results:
            if r.get_hostname() == node:
                return r

        # nothing found
        raise RingException("Result for node %s not found in resultset." % node)


    def get_results(self):
        """ Get all available results.

            @return: all available results in the result set
            @rtype: list of L{NodeResult} objects
        """
        return self.results


    def get_successful_results(self):
        """ Get all successful results, meaning the SSH connection
            was made and the command executed with exitcode 0.

            @return: all results with exitcode 0
            @rtype: a L{NodeResultSet} containing these results
        """
        results = []
        for result in self.results:
            if result.get_ssh_result() == NodeResult.SSH_OK and result.get_exitcode() == 0:
                results.append(result)
        return NodeResultSet(results)
    

    def get_failed_results(self, include_ssh_problems = True, only_ssh_problems = False):
        """ Get the nodes in the rsult set which failed to run a command correctly.

            @param include_ssh_problems: flag to indicate if SSH connection
            problems should be included (I{True}) or not (I{False}).
            @type include_ssh_problems: Boolean

            @param only_ssh_problems: list only nodes which failed their SSH
            connection or not.
            @type only_ssh_problems: Boolean

            @return: the requested results
            @rtype: a {NodeResultSet} containing the requested results
        """
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
        """ Count the number of results in the result set.

            @return: the number of results
            @rtype: integer
        """
        return len(self.results)


    def get_value(self, name):
        """ Get a value from all results in the result set.

            @param name: the name of the value to lookup
            @type name: string

            @return: a dictionary with for each host the
            requested value
            @rtype: dictionary
        """
        result = {}
        for r in self.results:
            result[r.get_hostname()] = r.get_value(name)
        return result


    def get_value_sorted(self, name, reverse=False):
        """ Get a value from all results in the result set,
            sort the output by value.

            @param name: the name of the value to lookup
            @type name: string

            @param reverse: do reverse sorting
            @type reverse: boolean

            @return: the sorted result for all hosts
            @rtype: a list of (hostname, value) tuples
        """
        return sorted(self.get_value(name).iteritems(), key=operator.itemgetter(1), reverse=reverse)


    def get_value_avg(self, name):
        """ Get the average value for a value stored in
            the results in the result set. This only
            works if the values are numerical.

            @param name: the name of the value to lookup
            @type name: string

            @return: the average value
            @rtype: float

            @raise RingException: if there are non-numerical
            values.
        """
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
        """ Get the values for a specific result value from all
            result sets, group the output by value. 

            This function can be used to find all hosts with
            identical values. 

            @param name: the name of the value to lookup
            @type name: string

            @param sort_by_hostcount: sort the output based
            on the number of hosts for a given value
            @type sort_by_hostcount: boolean

            @return: a list (optionally sorted) list containing
            per value the corresponding hosts.
            @rtype: list of (value, list of strings) tuples
        """
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
        """ Fancy textual representation of the object.

            @return: textual representation
            @rtype: string
        """
        return "<result set for: %s>" % ", ".join(self.get_hostnames())
