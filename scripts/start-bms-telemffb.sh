#!/usr/bin/env bash
# Start native TelemFFB and its Wine BMS telemetry forwarder.
set -u

usage() {
    cat <<'USAGE'
Usage: start-bms-telemffb.sh [--bms-launcher /path/to/start-bms.sh] [--exit-with-bms] [--port PORT]

Set WINEPREFIX to the prefix used by BMS (default: ~/.wine).
The optional launcher is started separately; closing TelemFFB does not close BMS.
With --exit-with-bms, the launcher must stay running until BMS exits.
USAGE
}

launcher=
port=34382
exit_with_bms=false
while (($#)); do
    case "$1" in
        --bms-launcher|--port)
            if (($# < 2)); then
                echo "Missing value for $1" >&2
                exit 2
            fi
            if [[ $1 == --bms-launcher ]]; then launcher=$2; else port=$2; fi
            shift 2
            ;;
        -h|--help) usage; exit 0 ;;
        --exit-with-bms) exit_with_bms=true; shift ;;
        *) echo "Unknown option: $1" >&2; usage >&2; exit 2 ;;
    esac
done
if [[ $exit_with_bms == true && -z $launcher ]]; then
    echo "--exit-with-bms requires --bms-launcher." >&2
    exit 2
fi
if [[ ! $port =~ ^[0-9]{1,5}$ ]] || ((10#$port < 1 || 10#$port > 65535)); then
    echo "Port must be between 1 and 65535." >&2
    exit 2
fi
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd) || exit 1
if [[ ! -x $root/.venv/bin/python ]]; then
    echo "Linux Python environment not found at $root/.venv. See the README setup instructions." >&2
    exit 1
fi
if ! command -v wine >/dev/null 2>&1; then
    echo "Wine not found in PATH." >&2
    exit 1
fi
if [[ -n $launcher && ! -x $launcher ]]; then
    echo "BMS launcher is not an executable file: $launcher" >&2
    exit 1
fi
export WINEPREFIX=${WINEPREFIX:-$HOME/.wine}
cd -- "$root" || exit 1
forwarder_pid=
app_pid=
cleanup() {
    if [[ -n $forwarder_pid ]]; then
        kill "$forwarder_pid" 2>/dev/null || true
        wait "$forwarder_pid" 2>/dev/null || true
    fi
}
on_signal() {
    if [[ -n $app_pid ]]; then kill "$app_pid" 2>/dev/null || true; fi
    exit 130
}
trap cleanup EXIT
trap on_signal INT TERM

echo "Starting BMS telemetry forwarder (Wine prefix: $WINEPREFIX, UDP port: $port)"
wine python.exe -m wine.bms_udp_forwarder --port "$port" &
forwarder_pid=$!
echo "Starting TelemFFB"
"$root/.venv/bin/python" "$root/main.py" &
app_pid=$!
if [[ -n $launcher ]]; then
    echo "Starting BMS: $launcher"
    "$launcher" &
    launcher_pid=$!
fi
if [[ $exit_with_bms == true ]]; then
    finished=
    wait -n -p finished "$app_pid" "$launcher_pid"
    status=$?
    if [[ $finished == "$launcher_pid" ]]; then
        echo "BMS launcher exited; stopping TelemFFB."
        kill -TERM "$app_pid" 2>/dev/null || true
        wait "$app_pid" 2>/dev/null || true
        exit "$status"
    fi
else
    wait "$app_pid"
    status=$?
fi
if ((status != 0)); then
    echo "TelemFFB exited with status $status." >&2
fi
exit "$status"
