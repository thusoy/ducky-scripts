#!/bin/sh

### BEGIN INIT INFO
# Provides:         ssh-tunnel
# Required-Start:   $remote_fs $syslog
# Required-Stop:    $remote_fs $syslog
# Default-Start:    2 3 4 5
# Default-Stop:
# Short-Description:    SSH tunnel installed by bootstrap rubber-ducky script
### END INIT INFO

NAME=ssh-tunnel
DAEMON=/usr/bin/ssh
DAEMON_ARGS="{{ ssh_user }}@{{ ssh_target }} \
    -i /home/pi/.ssh/id_rsa \
    -N \
    -R 127.0.0.1:2223:127.0.0.1:22 \
    -o BatchMode=yes"{% if no_strict_checking -%} \
    -o StrictHostKeyChecking=no \
    -o UserKnownHostsFile=/dev/null
    {%- endif -%}
DESC="SSH tunnel"
PIDFILE=/var/run/$NAME.pid

. /lib/lsb/init-functions

do_start() {
    start-stop-daemon --status --quiet --pidfile $PIDFILE
    status=$?
    case "$status" in
        0)
            log_action_msg "$DESC already running."
            return 1
            ;;
        1)
            log_warning_msg "$DESC is not running, but pidfile exists. Will try to start."
            ;;
        # 3 means not running, just start as normal
        4)
            log_warning_msg "Could not determine status of $DESC, will try to start."
            ;;
    esac
    log_daemon_msg "Starting $DESC" $NAME
    start-stop-daemon --start --quiet --background --pidfile $PIDFILE \
        --make-pidfile --exec $DAEMON -- $DAEMON_ARGS
    retval=$?
    log_end_msg $retval
    return $retval
}

do_stop() {
    start-stop-daemon --status --quiet --pidfile $PIDFILE
    status=$?
    case "$status" in
        # 0 means running, continue shutdown as normal
        1)
            log_warning_msg "$DESC is already stopped, but pidfile still exists."
            return 1
            ;;
        3)
            log_action_msg "$DESC already stopped."
            return 1
            ;;
        4)
            log_warning_msg "Could not determine status of $DESC, will try to stop."
            ;;
    esac
    log_daemon_msg "Stopping $DESC" $NAME
    start-stop-daemon --stop --quiet --retry TERM/30/KILL/5 \
        --pidfile $PIDFILE --remove-pidfile
    retval=$?
    log_end_msg $retval
    return $retval
}

do_restart() {
    log_action_msg "Restarting $DESC" "$NAME"
    do_stop
    case "$?" in
        0|1) do_start ;;
    esac
}

case "$1" in
    start)
        do_start
        ;;
    stop)
        do_stop
        ;;
    restart|force-reload)
        do_restart
        ;;
    *)
        log_action_msg "Usage: /etc/init.d/ssh {start|stop|restart|force-reload}" || true
        exit 1
esac
