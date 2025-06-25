exit(1)

# list running
pgrep -f speak_server.py
4140


# kill the service. option 1
kill 4140


# kill the service. option 2
pkill -f speak_server.py

# start
python3 ~/projects/py/speak_server/speak_server.py &



