#!/bin/sh

OPENSHIFT_CONFIG_FILE=$AMQ_HOME/conf/openshift-activemq.xml
CONFIG_FILE=$AMQ_HOME/conf/activemq.xml
OPENSHIFT_LOGIN_FILE=$AMQ_HOME/conf/openshift-login.config
LOGIN_FILE=$AMQ_HOME/conf/login.config
OPENSHIFT_USERS_FILE=$AMQ_HOME/conf/openshift-users.properties
USERS_FILE=$AMQ_HOME/conf/users.properties

function checkViewEndpointsPermission() {
    if [ "${AMQ_MESH_DISCOVERY_TYPE}" = "kube" ]; then
        if [ -n "${AMQ_MESH_SERVICE_NAMESPACE+_}" ] && [ -n "${AMQ_MESH_SERVICE_NAME+_}" ]; then
            endpointsUrl="https://${KUBERNETES_SERVICE_HOST:-kubernetes.default.svc}:${KUBERNETES_SERVICE_PORT:-443}/api/v1/namespaces/${AMQ_MESH_SERVICE_NAMESPACE}/endpoints/${AMQ_MESH_SERVICE_NAME}"
            endpointsAuth="Authorization: Bearer $(cat /var/run/secrets/kubernetes.io/serviceaccount/token)"
            endpointsCode=$(curl -s -o /dev/null -w "%{http_code}" -G -k -H "${endpointsAuth}" ${endpointsUrl})
            if [ "${endpointsCode}" = "200" ]; then
                echo "Service account has sufficient permissions to view endpoints in kubernetes (HTTP ${endpointsCode}). Mesh will be available."
            elif [ "${endpointsCode}" = "403" ]; then
                >&2 echo "WARNING: Service account has insufficient permissions to view endpoints in kubernetes (HTTP ${endpointsCode}). Mesh will be unavailable. Please refer to the documentation for configuration."
            else
                >&2 echo "WARNING: Service account unable to test permissions to view endpoints in kubernetes (HTTP ${endpointsCode}). Mesh will be unavailable. Please refer to the documentation for configuration."
            fi
        else
            >&2 echo "WARNING: Environment variables AMQ_MESH_SERVICE_NAMESPACE and AMQ_MESH_SERVICE_NAME both need to be defined when using AMQ_MESH_DISCOVERY_TYPE=\"kube\". Mesh will be unavailable. Please refer to the documentation for configuration."
        fi
    fi
}

cp "${OPENSHIFT_CONFIG_FILE}" "${CONFIG_FILE}"
cp "${OPENSHIFT_LOGIN_FILE}" "${LOGIN_FILE}"
cp "${OPENSHIFT_USERS_FILE}" "${USERS_FILE}"

checkViewEndpointsPermission
