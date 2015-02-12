MPD Proxy
=========

Fault tolerance
---------------
If the proxy dies, the servers will continue to play the song as if the proxy never died. When the proxy comes back up, it will re-connect to the servers and re-measure the latency to each server. While the proxy is down, the client will be un-able to communicate with the servers.

If a server dies, the proxy will detect this and stop sending messages to that server. When the server comes back up, the proxy will send a message to that server to start playing the same song that the other servers are playing. For this to happen, the proxy will need to keep track of which song is currently playing and the last message sent to each server.
