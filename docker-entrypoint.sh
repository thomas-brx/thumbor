#!/bin/sh

if [ ! -f /home/thumbor/thumbor.conf ]; then
  envtpl /home/thumbor/thumbor.conf.tpl  --allow-missing --keep-template
fi

# If log level is defined we configure it, else use default log_level = info
if [ -n "$LOG_LEVEL" ]; then
    LOG_PARAMETER="-l $LOG_LEVEL"
fi

# Check if thumbor port is defined -> (default port 80)
if [ -z ${THUMBOR_PORT+x} ]; then
    THUMBOR_PORT=80
fi

# Check if thumbor port is defined -> (default port 80)
if [ -z ${THUMBOR_NUM_PROCESSES+x} ]; then
    THUMBOR_NUM_PROCESSES=1
fi

if [ "$1" = 'thumbor' ]; then
    echo "---> Starting thumbor"
    exec thumbor --port=$THUMBOR_PORT --conf=/home/thumbor/thumbor.conf $LOG_PARAMETERS --processes=$THUMBOR_NUM_PROCESSES --app tc_core.app.App
fi

exec "$@"
