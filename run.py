"""
Copyright (c) 2015 Red Hat, Inc
All rights reserved.

This software may be modified and distributed under the terms
of the MIT license. See the LICENSE file for details.
"""

import os
import ssl
import shutil
import urllib2
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

        self.ssl_envs = { k: os.getenv(k, "") for k in [
            "AMQ_KEYSTORE_TRUSTSTORE_DIR", "AMQ_KEYSTORE", "AMQ_TRUSTSTORE",
            "AMQ_TRUSTSTORE_PASSWORD", "AMQ_KEYSTORE_PASSWORD"
        ]}
        self.ssl_enabled = all(self.ssl_envs.values())

    def teardown(self):
        with open(self.config_file, "w") as fh:
            self.config.writexml(fh)

    def configure(self):
        """
        Aggregate method that calls all configure_* methods in sequence.
        """
        self.configure_authentication()
        self.configure_SSL()
        self.configure_storeUsage()
        self.configure_destinations()
        self.configure_transport_options()
        self.configure_mesh()
        self.check_view_endpoints_permission()

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
        envs = self.ssl_envs

        if self.ssl_enabled:
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

    def configure_storeUsage(self):
        su = os.getenv("AMQ_STORAGE_USAGE_LIMIT", "100 gb")
        for node in self.config.getElementsByTagName("storeUsage"):
            if node.attributes and node.getAttribute("limit"):
                node.setAttribute("limit", su)

    def configure_destinations(self):
        queues = filter(None, os.getenv("AMQ_QUEUES", "").split(","))
        topics = filter(None, os.getenv("AMQ_TOPICS", "").split(","))

        if len(queues) > 0 or len(topics) > 0:
            d = self.config.createElement("destinations")

            for queue in queues:
                q = self.config.createElement("queue")
                q.setAttribute("physicalName", queue)
                d.appendChild(q)

            for topic in topics:
                t = self.config.createElement("topic")
                t.setAttribute("physicalName", topic)
                d.appendChild(t)

            b = self.config.getElementsByTagName("broker")[0]
            b.appendChild(d)

    def configure_transport_options(self):
        transports = os.getenv("AMQ_TRANSPORTS", "openwire,mqtt,amqp,stomp").split(",")
        maxConnections = os.getenv("AMQ_MAX_CONNECTIONS", "1000")
        maxFrameSize = os.getenv("AMQ_FRAME_SIZE", "104857600")

        # only partially evaluated here; proto and port expanded later
        uri = "{{proto}}://0.0.0.0:{{port}}?maximumConnections={maxConnections}&amp;wireFormat.maxFrameSize={maxFrameSize}".format(maxConnections=maxConnections, maxFrameSize=maxFrameSize)

        # port and protocol values for different transports
        data = {
            "openwire": [ "tcp",   "61616", "ssl",      "61617" ],
            "mqtt":     [ "mqtt",  "1883",  "mqtt+ssl", "8883"  ],
            "amqp":     [ "amqp",  "5672",  "amqp+ssl", "5671"  ],
            "stomp":    [ "stomp", "61613", "stomp+ssl","61612" ],
        }

        if len(transports) > 0:
            t = self.config.createElement("transportConnectors")

            for transport in transports:
                tc = self.config.createElement("transportConnector")
                tc.setAttribute("name", transport)

                if self.ssl_enabled:
                    tc_ssl = self.config.createElement("transportConnector")
                    tc_ssl.setAttribute("name","ssl")

                if transport in data:
                        proto,port,sslproto,sslport = data[transport]
                        tc.setAttribute("uri", uri.format(proto=proto,port=port))
                        if self.ssl_enabled:
                            tc_ssl.setAttribute("uri", uri.format(proto=sslproto,port=sslport))
                else:
                    self.logger.error("Unknown transport type '{}'".format(transport))
                    continue

                t.appendChild(tc)
                if self.ssl_enabled:
                    t.appendChild(tc_ssl)

            b = self.config.getElementsByTagName("broker")[0]
            b.appendChild(t)

    def configure_mesh(self):
        serviceName = os.getenv("AMQ_MESH_SERVICE_NAME", "")
        username = os.getenv("AMQ_USER", "")
        password = os.getenv("AMQ_PASSWORD", "")
        discoveryType = os.getenv("AMQ_MESH_DISCOVERY_TYPE", "dns")

        if serviceName:
            nc = self.config.createElement("networkConnector")
            nc.setAttribute("uri", "{}://{}:61616/?transportType=tcp".format(discoveryType,serviceName))
            nc.setAttribute("messageTTL", "-1")
            nc.setAttribute("consumerTTL", "1")

            if username and password:
                nc.setAttribute("userName", username)
                nc.setAttribute("password", password)

            # networkConnectors within broker
            b = self.config.getElementsByTagName("broker")[0]
            ncs = b.getElementsByTagName("networkConnectors")[0]
            ncs.appendChild(nc)

    def check_view_endpoints_permission(self):
        if os.getenv("AMQ_MESH_DISCOVERY_TYPE", "") != "kube":
            return

        namespace = os.getenv("AMQ_MESH_SERVICE_NAMESPACE", "")
        servicename = os.getenv("AMQ_MESH_SERVICE_NAME", "")

        if not (namespace and servicename):
            self.logger.error("WARNING: Environment variables AMQ_MESH_SERVICE_NAMESPACE and AMQ_MESH_SERVICE_NAME both need to be defined when using AMQ_MESH_DISCOVERY_TYPE=\"kube\". Mesh will be unavailable. Please refer to the documentation for configuration.")
            return

        url="https://{}:{}/api/v1/namespaces/{}/endpoints/{}".format(
            os.getenv("KUBERNETES_SERVICE_HOST", "kubernetes.default.svc"),
            os.getenv("KUBERNETES_SERVICE_PORT", "443"),
            namespace, servicename
        )
        auth="Authorization: Bearer "
        with open("/var/run/secrets/kubernetes.io/serviceaccount/token") as fh:
            auth += fh.read()

        request = urllib2.Request(url)
        request.add_header("Authorization", auth)

        # this is faithful to the shell impl, but I'd like to look at checking certs as a TODO
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        result = urllib2.urlopen(request, context=ctx)
        code=result.getcode()

        if code == 200:
            self.logger.info("Service account has sufficient permissions to view endpoints in kubernetes (HTTP {}). Mesh will be available.".format(code))
        elif code == 403:
            self.logger.warning("Service account has insufficient permissions to view endpoints in kubernetes (HTTP {}). Mesh will be unavailable. Please refer to the documentation for configuration.".format(code))
        else:
            self.logger.warning("Service account unable to test permissions to view endpoints in kubernetes (HTTP {}). Mesh will be unavailable. Please refer to the documentation for configuration.".format(code))
