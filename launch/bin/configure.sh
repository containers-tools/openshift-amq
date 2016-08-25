#!/bin/sh

OPENSHIFT_CONFIG_FILE=$AMQ_HOME/conf/openshift-activemq.xml
CONFIG_FILE=$AMQ_HOME/conf/activemq.xml
OPENSHIFT_LOGIN_FILE=$AMQ_HOME/conf/openshift-login.config
LOGIN_FILE=$AMQ_HOME/conf/login.config
OPENSHIFT_USERS_FILE=$AMQ_HOME/conf/openshift-users.properties
USERS_FILE=$AMQ_HOME/conf/users.properties

cp "${OPENSHIFT_CONFIG_FILE}" "${CONFIG_FILE}"
cp "${OPENSHIFT_LOGIN_FILE}" "${LOGIN_FILE}"
cp "${OPENSHIFT_USERS_FILE}" "${USERS_FILE}"
