Prosync: the MPD Proxy
=========

Overview
---------------
Prosync is an MPD proxy that accurately synchronizes commands over a cluster of MPD servers from a single MPC client. The key insight was to make it frictionless to integrate with existing systems, and therefore we focused on making the proxy independent of the client and the servers, and is only dependent in a few cases on the MPD protocol. Thus, Prosync works with any MPD client and any set of MPD servers.


Running Prosync
---------------
1. Download Prosync by cloning this [repository](https://github.com/gshubham/cs191)

2. Make a file called `mpd_servers`, which should contain the tuple `(server IP address:port, name of user on the server [optional], music directory on the server [optional])` separated by newlines.

A sample `mpd_servers` file could look like the following:

`
localhost:6667 gshubham ~/Desktop/Music/
`

`
10.31.87.33:3000 saurabh ~/CS191/Music/
`

3. Run `sudo ./mpd_proxy mpd_servers` and the proxy will start up.

4. You can now issue commands from the client to the port that the proxy is listening on! Enjoy!

Optional

5. We also support simple music file uploads to the MPD servers. The optional arguments in `mpd_servers` are meant for this purpose. In order to upload a given song to all the MPD servers and add it to their database, you can run ` sudo ./mpd_upload.py <path-to-file-name-to-be-uploaded> mpd_servers`, followed by `mpc --port <proxy-port> update` to update all the MPD music databases.

6. We also worked on generating visualizations of latencies from the proxy to all the servers. To view the visualization when the proxy is running, just start a simple python HTTP server `python SimpleHTTPServer &` in the Prosync directory and visit `localhost:8000/graph.html` in your web browser!  


Problem
---------------
As decribed above, the MPD Proxy sits in front all the MPD servers, each of which is connected to an amplifier/speaker setup in a different room. Traditionally, the MPC client would either have to use very expensive hardware which was hard to integrate with, to send a command to all the servers at the same time. 
We want to provide the client the ability to achieve a similar goal but with a very simple lightweight software solution. Hence, Prosync! 


Implementation
---------------
We used Python 2.7.1 for our implementation. We also used Javascript/CSS/HTML and d3.js for basic visualizations of latencies and packet loss. 

The big question we were faced with when implementing Prosync was how to accurately synchronize commands over a cluster of MPD servers, given that we can't make any changes to them? (For example, we couldn't use the concept of a true timestamp, and have everyone sync to that)

Hence to do the synchronization, the main problem involved accurately finding latencies from the MPD servers to the proxy.

The main file, `mpd_proxy.py`, has two purposes: 
1. handle requests from client to server, and responses from server to client
2. have a consistent and accurate state of latency from the proxy to each of the MPD servers.

We accomplish (2) by just having a separate thread in `mpd_proxy.py` that calculates the latency for every server by calling `ping` on every server 10 times/second. Please see the Latency Measurements section for more details on how we average the latency from these 10 observations/second.

For (1), the main thread listens for the client and forwards any commands it receives from the client to the servers discounted by the appropriate latencies. We have a background thread for each command that is issued to the proxy from the client. This thread is responsible for collecting the responses from the servers and sending a copy back to the client, once the fastest of the servers responds.

In case a server dies and comes back up, we have another thread that is launched to handle fault tolerance cases. Please see the Fault Tolerance section for more details.

Latency Measurements
-----------------------------
We used three main methods to have a consistent state of latency from any one server to the proxy at a given time.

Exponentially Weighted Moving Average: We use this to update the latency from a given MPD server to the proxy, by discounting latencies that have been calculated earlier exponentially more than recent measurements. For example, if we're trying to calculate the latency between two machines at t=5 seconds, we want to discount its latency at t=1 second much more than the latency at t=4, since t=4 will have a more accurate state of what the current latency is.

K-Means Clustering: In a Wi-Fi network, we know that we have about 10% packet loss, and thus the latency on an average for every 10th packet will be very high, but that is an outlier and not a good measurement to add to our average. To take care of this case, for each of the 10 pings that we calculate per second for a server, we classify the pings into two sets (centroids being the smallest and the largest values in the 10 pings), and throw one set away if the difference in the sizes of the two sets is greater than an emperically determined threshold. For example,

If our measurements were (1, 1, 1, 1, 1, 10, 1, 1, 1, 9), we don't want to count (9, 10) in our measurement for our average. Running K-means with centroids (1, 10) will allow us to detect these outliers and remove them.


Correlation of packet loss: Even after calculating an accurate latency, the probability that the latency at the time the command is issued is not in the neighborhood of the calculated latency is significant. This is because a packet loss could happen on the packet that contains the MPD command. To reduce this probability, we took advantage of the coorelation in packet loss. We know that packet losses are usually correleated, that is if a packet is lost, it is very likely that the next packet will be lost too. Hence before sending out an MPD command, we first send a ping packet. If the ping packet is lost, we send another ping packet back-to-back and follow that upby a request. This significantly reduces the probability of a packet loss and thereby, the MPD command adheres to the calculated latency.

Fault tolerance
---------------
We have two failure cases:

If the proxy dies, the servers will continue to play the song as if the proxy never died. When the proxy comes back up, it will re-connect to the servers and re-measure the latency to each server. While the proxy is down, the client will be un-able to communicate with the servers.

If a server dies, the proxy will detect this (within a second due to ping requests) and stop sending messages to that server. When the server comes back up, the proxy will first request the status of all the other live servers, and then communicate that status to the proxy that just came back up and has stale state.

Visualizations
--------------- 
Since we were initially having trouble correlating packet loss with the latency measurements and how it eas affecting them, we decided to do a real-time visualizations of how the latencies of all servers vary over time. We used d3.js to a simple line plot in javascript. The proxy logs all the latencies every second to `latencies.tsv` and we redraw the line chart every 500 milliseconds with the new data.


Development
--------------- 
While developing, we were running Prosync on two Macbook Pros, with one laptop running the proxy, an MPD server, and the client. The other laptop only ran the MPD server. 
