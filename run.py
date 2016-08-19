"""
Copyright (c) 2015 Red Hat, Inc
All rights reserved.

This software may be modified and distributed under the terms
of the MIT license. See the LICENSE file for details.
"""

import os
import shutil

from cct.module import Module


def sed(oldstr, newstr, fname):
    """
    Temporary implementation of something like sed(1), for use in
    converting shell script functionality into this module.

    No regexp functionality yet, not needed for what has been converted
    over.
    """
    contents = open(fname,'r').read()
    contents = contents.replace(oldstr,newstr)
    with open(fname,'w') as fh:
        fh.write(contents)

# XXX: odd to put a Run inside install.py
class Run(Module):
    def __init__(self):
        amq_home = os.getenv("AMQ_HOME")
        self.users_file = "{}/conf/users.properties".format(amq_home)
        self.config_file = "{}/conf/activemq.xml".format(amq_home)

    def configure_authentication(self):
        if "username" in os.environ and "password" in os.environ:
            username = os.getenv("username")
            password = os.getenv("password")
            sed("##### AUTHENTICATION #####", "{}={}".format(username,password), self.users_file)
            authentication="<jaasAuthenticationPlugin configuration=\"activemq\" />"
        else:
            authentication="<jaasAuthenticationPlugin configuration=\"activemq-guest\" />"
    sed("##### AUTHENTICATION #####", authentication, self.config_file)

    def run_amq(self):
        self.logger.debug("CCT runtime script running!")
        # and now CCT will run the docker CMD, which is still the launch shell
        # script, but we can gradually move more code from that to here, and
        # then perhaps CMD should be $AMQ_HOME/bin/activemq console directly?
        # (inherited from standalone image)
        pass
