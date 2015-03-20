Prosync: the MPD Proxy
=========

Overview
---------------
Prosync is an MPD proxy that accurately synchronizes commands over a cluster of MPD servers from a single MPC client. The key insight was to make it frictionless to integrate with existing systems, and therefore we focused on making the proxy independent of the client and the servers, and is only dependent in a few cases on the MPD protocol.

Running Prosync
---------------
1. Download Prosync by cloning this [repository](https://github.com/gshubham/cs191)

2. Make a file called `mpd_servers`, which should contain the tuple `(server IP address, port, name of user on the server [optional], music directory on the server [optional])` separated by newlines.

A sample `mpd_servers` file could look like the following:

`
localhost 6667 gshubham ~/Desktop/Music/ \n
10.31.87.33 3000 saurabh ~/CS191/Music/
`

2. Run 'sudo ./mpd_proxy mpd_servers` and the proxy will start up.

3. You can now issue commands from the client to the port that the proxy is listening on! Enjoy!

Optional

4. We also support simple music file uploads to the MPD servers. The optional arguments in `mpd_servers` are meant for this purpose. In order to upload a given song to all the MPD servers and add it to their database, you can run ` sudo ./mpd_upload.py <path-to-file-name-to-be-uploaded> mpd_servers`, followed by `mpc --port <proxy-port> update` to update all the MPD music databases.

5. We also worked on generating visualizations of latencies from the proxy to all the servers. To view the visualization when the proxy is running, just start a simple python HTTP server `python SimpleHTTPServer &` in the Prosync directory and visit `localhost:8000/graph.html` in your web browser!  


Fault tolerance
---------------
If the proxy dies, the servers will continue to play the song as if the proxy never died. When the proxy comes back up, it will re-connect to the servers and re-measure the latency to each server. While the proxy is down, the client will be un-able to communicate with the servers.

If a server dies, the proxy will detect this and stop sending messages to that server. When the server comes back up, the proxy will send a message to that server to start playing the same song that the other servers are playing. For this to happen, the proxy will need to keep track of which song is currently playing and the last message sent to each server.
