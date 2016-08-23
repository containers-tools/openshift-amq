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

    def configure_SSL(self):
        envs = { k: os.getenv(k) or "" for k in [
            "AMQ_KEYSTORE_TRUSTSTORE_DIR", "AMQ_KEYSTORE", "AMQ_TRUSTSTORE",
            "AMQ_TRUSTSTORE_PASSWORD", "AMQ_KEYSTORE_PASSWORD"
        ]}

        if all(envs.values()):
            keyStorePath = os.path.join(envs['AMQ_KEYSTORE_TRUSTSTORE_DIR'], envs['AMQ_KEYSTORE'])
            trustStorePath = os.path.join(envs['AMQ_KEYSTORE_TRUSTSTORE_DIR'], envs['AMQ_TRUSTSTORE'])

            e1 = self.config.createElement("sslContext")
            e2 = self.config.createElement("sslContext")
            e2.setAttribute("keyStore", "file:{}".format(keyStorePath))
            e2.setAttribute("trustStore", "file:{}".format(trustStorePath))
            e2.setAttribute("keyStorePassword", envs['AMQ_KEYSTORE_PASSWORD'])
            e2.setAttribute("trustStorePassword", envs['AMQ_TRUSTSTORE_PASSWORD'])

            p = self.config.getElementsByTagName("broker")[0]
            e1.appendChild(e2)
            p.appendChild(e1)

        elif any(envs.values()):
            self.logger.error("WARNING! Partial ssl configuration, the ssl context WILL NOT be configured.")
