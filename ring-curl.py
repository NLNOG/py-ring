#! /usr/bin/env python

import ringtools
from BeautifulSoup import BeautifulSoup

AGENT = "ring-curl v0.1"
URL = "http://www.bokhard.nl"

hosts = ringtools.pick_hosts(5)
print "picked: %s" % ", ".join(hosts)
command = 'curl -L -A \'%s\' -i -s %s' % (AGENT, URL)

result = ringtools.run_command(command, hosts)
print "succesful results:"
for res in result.get_successful_results().get_results():
    out = res.get_stdout()
    res.add_value('HTTP-code', out[0])
    i = 0
    for r in out[1:]:
        if ":" in r:
            x = r.split(': ', 2)
            res.add_value(x[0].strip(), x[1].strip())

        if r.strip() == "":
            break
        i += 1
    soup = BeautifulSoup("\n".join(out[i:]))
    if soup.title:
        res.add_value('title', soup.title.string)

s = result.get_successful_results().get_value_sorted('Date')
for k in s:
    print "%s: %s" % k


print "command failed:"
for res in result.get_failed_results(False).get_results():
    print "  %25s: %s" % (res.get_hostname(), '\n'.join(res.get_stderr()))

print "connection problems:"
for res in result.get_failed_results(True, True).get_results():
    print "  %25s: %s" % (res.get_hostname(), repr(res.get_ssh_errormsg()))

