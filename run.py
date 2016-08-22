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
    """
    with open(fname) as f:
        contents = f.read()

    if oldstr not in contents:
        return

    with open(fname,'w') as f:
        contents = contents.replace(oldstr,newstr)
        f.write(contents)

class Run(Module):

    def configure_authentication(self):
        # XXX: belongs in __init__
        amq_home = os.getenv("AMQ_HOME")
        # XXX: we need to modify openshift-users.properties here, temporarily, because
        # the existing/legacy shell scripts that run *afterwards* copy it over the
        # eventual location (same for activemq.xml)
        self.users_file = "{}/conf/openshift-users.properties".format(amq_home)
        self.config_file = "{}/conf/openshift-activemq.xml".format(amq_home)

        if "AMQ_USER" in os.environ and "AMQ_PASSWORD" in os.environ:
            username = os.getenv("AMQ_USER")
            password = os.getenv("AMQ_PASSWORD")
            sed("##### AUTHENTICATION #####", "{}={}".format(username,password), self.users_file)
            authentication="<jaasAuthenticationPlugin configuration=\"activemq\" />"
        else:
            authentication="<jaasAuthenticationPlugin configuration=\"activemq-guest\" />"

        sed("<!-- ##### AUTHENTICATION ##### -->", authentication, self.config_file)
