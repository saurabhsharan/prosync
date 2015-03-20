#!/usr/bin/env python

import datetime
import os
import pythonPing.ping as ping
import random
import select
import socket
import pyping
import sys
import time
import threading

# Higher values will give more weight to later samples
WEIGHTED_MOVING_AVERAGE_COEFF_ALPHA = 0.4

# The time (in seconds) to sleep for between latency measurements
PAUSE_SECONDS_BETWEEN_LATENCY_SAMPLES = 1

class ServerConn:
  def __init__(self, host, port):
    self.host = host
    self.port = port
    self.approx_latency_ms = float('inf')
    self.conn = None
    self.server_alive = True
    self.recover = False

  def connect(self):
    # self._measure_latency()
    if self.conn:
      return
    self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
      self.conn.connect((self.host, self.port))
    except:
      self.conn = None
      self.approx_latency_ms = float('inf')
      self.server_alive = False

  def close(self):
    if not self.conn:
      return
    self.conn.close()
    self.conn = None

  def process_command(self, command_str):
    if not self.conn or not self.server_alive:
      return
    self.conn.sendall(command_str)

  def _check_server_health(self):
    temp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
      temp_socket.connect((self.host, self.port))
      temp_socket.close()
      if self.server_alive == False:
        self.recover = True
        self.server_alive = True
        print "HEREEE"
        get_status(self)
        print "HERE? :("

    except Exception, e:
      self.server_alive = False

  def _measure_latency(self, num_pings = 10):
    self._check_server_health()
    latencies = []
    if not self.server_alive:
      return
    if self.approx_latency_ms == float('inf'):
      while True:
        delay = ping.Ping(self.host, timeout=1000).do()
        if delay:
          self.approx_latency_ms = delay
          break
    for i in range(num_pings):
      try:
        r = ping.Ping(self.host, timeout=1000).do()
        if r:
          latencies.append(r)
      except socket.error, e:
        if self.conn:
          self.conn.close()
          self.conn = None
        self.server_alive = False
        return
      # r = pyping.ping(self.host)
      # print "Return code of ping = %d" % r.ret_code
      # if r.ret_code != 0:
      #   self.approx_latency_ms = float('inf')
      #   self.server_alive = False
      #   return
    centerOne = min(float(s) for s in latencies)
    centerTwo = max(float(s) for s in latencies)
    # print centerOne
    # print centerTwo
    clusterOne = []
    clusterTwo = []
    for i in range(0, len(latencies)):
      if abs(centerOne - latencies[i]) >= abs(centerTwo - latencies[i]):
        clusterOne.append(latencies[i])
      else:
        clusterTwo.append(latencies[i])
    # print clusterOne
    # print clusterTwo
    if abs(len(clusterTwo) - len(clusterOne)) > (float(3)/4) * (len(latencies)):
      toRemove = clusterOne if (len(clusterTwo) - len(clusterOne) > 0) else clusterTwo
      for i in range(0, len(toRemove)):
        latencies.remove(toRemove[i])
    avg_latency = sum(latencies)/len(latencies)
    self.approx_latency_ms = (WEIGHTED_MOVING_AVERAGE_COEFF_ALPHA * avg_latency) + ((1 - WEIGHTED_MOVING_AVERAGE_COEFF_ALPHA) * self.approx_latency_ms)

SERVERS = [
  ('localhost', 6667),
  ('10.31.83.110', 4007),
  # ('10.31.83.110', 4007)
  # ('10.31.83.176', 6667)
]

server_conns = []
server_conns_lock = threading.Lock()

def forward_to_client(client_conn, server_list, pipe_read_fd):
  print "Starting forward_to_client thread"
  received_data = [""] * len(server_list)
  server_finished = [False] * len(server_list)
  while True:
    read_list, _, _ = select.select(server_list + [pipe_read_fd], [], [])
    read_from_pipe = False
    for r in read_list:
      if r in server_list:
        d = r.recv(5)
        if not d:
          continue
        index = server_list.index(r)
        received_data[index] += d
        if received_data[index] == "OK\n" or received_data[index].find("\nOK\n") != -1 or received_data[index].startswith("OK MPD 0.19.0\n") == True:
          server_finished[index] = True
          if False not in server_finished:
            # for j in range(len(server_list)):
            #   if received_data[index] != received_data[j]:
            #     print "ERROR: Not all servers returned the same response:"
            #     print "Server %d: %r" % (index, received_data[index])
            #     print "Server %d: %r" % (j, received_data[j])
            # print "Sending data back to client: " + received_data[index]
            # raw_input("Press enter to continue ")
            client_conn.sendall(received_data[index])
            received_data = [""] * len(server_list)
            server_finished = [False] * len(server_list)
      elif r == pipe_read_fd:
        print "Read data from pipe"
        read_from_pipe = True
    if read_from_pipe:
      break


def process_response(server_to_recover, server_list):
  index = -1
  received_data = ""
  recovery_status = {}
  counter = 0
  satisfied = False
  while True:
    read_list, _, _ = select.select(server_list, [], [])
    for r in read_list:
      if server_to_recover.conn == r:
        continue
      if r in server_list:
        if index == -1:
          index = server_list.index(r)
        if index != -1:
          if server_list.index(r) != index:
            continue
          d = r.recv(5)
          if not d:
            continue
          received_data += d
          if received_data.find("OK\n") != -1:
            satisfied = True
            for value in received_data.split("\n"):
              split_index = value.find(":")
              if split_index != -1:
                recovery_status[value[0:split_index]] = value[split_index + 1:].strip()
      # elif r == pipe_read_fd:
        # read_from_pipe = True
    if satisfied:
      break
  if recovery_status["state"] == "stop":
    server_to_recover.connect()
    server_to_recover.process_command("stop\n")
  if recovery_status["state"] == "play":
    server_to_recover.connect()
    server_to_recover.process_command("status\n")

    server_to_recover_status_data = ""
    while True:
      d = server_to_recover.conn.recv(5)
      if not d:
        break
      server_to_recover_status_data += d
      if server_to_recover_status_data.find("OK\n") != -1:
        break
    server_to_recover_status_dict = {}
    for value in server_to_recover_status_data.split("\n"):
      split_index = value.find(":")
      if split_index != -1:
        server_to_recover_status_dict[value[0:split_index]] = value[split_index + 1:].strip()

    # print "Status for server that just recovered:"
    # print server_to_recover_status_dict

    a = str(float(recovery_status["elapsed"]) + server_conns[index].approx_latency_ms/2000.0 + server_to_recover.approx_latency_ms/2000.0 - 1.75)
    command = "command_list_ok_begin\nseekid " + "\"" + recovery_status["songid"] + "\" \"" + a + "\"\ncommand_list_end\n"
    # print "Command!" + command
    server_to_recover.process_command(command)
    # send playid recovery_status["songid"]
    # followed by recovery_status["elapsed"] + latency of the other guy/2 + self latency/2
    print recovery_status


def get_status(server_to_recover):
  for server_conn in server_conns:
    server_conn.connect()
  print "Here..."
  t = threading.Thread(target=process_response, args=(server_to_recover, [c.conn for c in server_conns]))
  t.start()
  for curr_conn in server_conns:
    curr_conn.process_command("status\n")
  t.join()
  print "Thread is exiting..."
  for server_conn in server_conns:
    server_conn.close()

def handle_client(client_socket):
  client_data = ''

  for server_conn in server_conns:
    server_conn.connect()

  r, w = os.pipe()

  t = threading.Thread(target=forward_to_client,
                   args=(client_socket, [c.conn for c in server_conns if c.conn], r))
  t.start()

  while True:
    # print "Waiting for data from client"

    c = client_socket.recv(1)

    # print "Got data from client"

    if not c:
      print "Client closed connection"
      break

    client_data += c

    if client_data[-1] == '\n':
      print "Client is about to execute command: " + client_data
      retries = []
      server_conns_lock.acquire()
      for server_conn in server_conns:
        r = ping.Ping(server_conn.host, timeout=1000).do()
        if r > (server_conn.approx_latency_ms * 1.5):
          retries.append(server_conn)
      for retry in retries:
        print "Re-sending ping to %s since previous ping looks like it dropped" % server_conn.host
        ping.Ping(server_conn.host, timeout=1000).do()
      # raw_input("Press enter to continue ")
      server_latencies = sorted([(server_conn.approx_latency_ms, server_conn) for server_conn in server_conns], reverse=True)
      server_conns_lock.release()
      begin = datetime.datetime.now()
      server_latencies[0][1].process_command(client_data)
      print "Processing command with server  " + server_latencies[0][1].host + " " + str(server_latencies[0][0])
      for i in range(1, len(server_latencies)):
        prev_latency = server_latencies[i-1][0]
        latency_diff = server_latencies[i][0] - prev_latency
        while ((datetime.datetime.now() - begin).seconds / 1000.0) < latency_diff:
          pass
        server_latencies[i][1].process_command(client_data)
        print "Processing command with server latency " + server_latencies[i][1].host + " " + str(server_latencies[i][0])
        begin = datetime.datetime.now()
      # for server_conn in server_conns:
        # server_conn.process_command(client_data)
      client_data = ''

  os.write(w, "A")
  t.join()

  for server_conn in server_conns:
    server_conn.close()

def ping_servers():
  while True:
    for server_conn in server_conns:
      server_conns_lock.acquire()
      server_conn._measure_latency(10)
      server_conns_lock.release()
      if server_conn.server_alive:
        print "Server %s is alive, latency is %r" % (server_conn.host, server_conn.approx_latency_ms)
      else:
        print "Server %s is dead" % server_conn.host
      with open("latencies.tsv", "a") as myfile:
        myfile.write("%s\t%r\t%r\n" % (server_conn.host, server_conn.approx_latency_ms if server_conn.server_alive else -1, time.time()))
    time.sleep(PAUSE_SECONDS_BETWEEN_LATENCY_SAMPLES)

def main():
  for server_host, server_port in SERVERS:
    s = ServerConn(server_host, server_port)
    server_conns.append(s)

  create_new_latencies_file = True

  if len(sys.argv) > 1 and sys.argv[1] == "1":
    create_new_latencies_file = False

  if create_new_latencies_file:
    with open("latencies.tsv", "w") as myfile:
      myfile.write("host\tlatency\ttime\n")

  ping_thread = threading.Thread(target=ping_servers)
  ping_thread.start()

  client_listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

  listen_port = random.randrange(2000, 8000)
  while True:
    try:
      client_listen_socket.bind(('', listen_port))
      break
    except:
      listen_port += 1

  print "Listening on port %d" % listen_port

  client_listen_socket.listen(10)

  while True:
    print "Waiting for client to connect to proxy..."
    client_socket, client_address = client_listen_socket.accept()
    print "accept() returned"
    handle_client(client_socket)
    print "Returned from handle_client"
    client_socket.close()

if __name__ == '__main__':
  main()
