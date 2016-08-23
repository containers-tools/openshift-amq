"""
Copyright (c) 2015 Red Hat, Inc
All rights reserved.

This software may be modified and distributed under the terms
of the MIT license. See the LICENSE file for details.
"""

import os
import shutil
import xml.dom.minidom

from cct.module import Module

class Run(Module):

    def setup(self):
        amq_home = os.getenv("AMQ_HOME")
        # XXX: we need to modify openshift-users.properties here, temporarily, because
        # the existing/legacy shell scripts that run *afterwards* copy it over the
        # eventual location (same for activemq.xml)
        self.users_file = "{}/conf/openshift-users.properties".format(amq_home)
        self.config_file = "{}/conf/openshift-activemq.xml".format(amq_home)
        self.config = xml.dom.minidom.parse(self.config_file)

    def teardown(self):
        with open(self.config_file, "w") as fh:
            self.config.writexml(fh)

    def configure_authentication(self):
        e = self.config.createElement("jaasAuthenticationPlugin")

        if "AMQ_USER" in os.environ and "AMQ_PASSWORD" in os.environ:
            with open(self.users_file,"a") as fh:
                username = os.getenv("AMQ_USER")
                password = os.getenv("AMQ_PASSWORD")
                fh.write("{}={}\n".format(username,password))

            e.setAttribute("configuration", "activemq")
        else:
            e.setAttribute("configuration", "activemq-guest")

        p = self.config.getElementsByTagName("plugins")[0]
        p.appendChild(e)
