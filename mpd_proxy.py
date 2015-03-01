#!/usr/bin/env python

import datetime
import os
import pyping
import random
import select
import socket
import sys
import time
import threading

# Higher values will give more weight to later samples
WEIGHTED_MOVING_AVERAGE_COEFF_ALPHA = 0.2

# The time (in seconds) to sleep for between latency measurements
PAUSE_SECONDS_BETWEEN_LATENCY_SAMPLES = 1

class ServerConn:
  def __init__(self, host, port):
    self.host = host
    self.port = port
    self.approx_latency_ms = float('inf')
    self.conn = None
    self.server_alive = True

  def connect(self):
    # self._measure_latency()
    self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
      self.conn.connect((self.host, self.port))
    except:
      self.approx_latency_ms = float('inf')
      self.server_alive = False

  def close(self):
    if not self.conn:
      return
    self.conn.close()
    self.conn = None

  def process_command(self, command_str):
    if not self.conn:
      return
    self.conn.sendall(command_str)

  def _check_server_health(self):
    temp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
      temp_socket.connect((self.host, self.port))
      temp_socket.close()
      self.server_alive = True
    except Exception, e:
      self.server_alive = False

  def _measure_latency(self, num_pings = 10):
    self._check_server_health()

    if not self.server_alive:
      return
    if self.approx_latency_ms == float('inf'):
      self.approx_latency_ms = float(pyping.ping(self.host).avg_rtt)
    for i in range(num_pings):
      r = pyping.ping(self.host)
      print "Return code of ping = %d" % r.ret_code
      if r.ret_code != 0:
        self.approx_latency_ms = float('inf')
        self.server_alive = False
        return
      latency_sample = float(r.avg_rtt)
      self.approx_latency_ms = (WEIGHTED_MOVING_AVERAGE_COEFF_ALPHA * latency_sample) + ((1 - WEIGHTED_MOVING_AVERAGE_COEFF_ALPHA) * self.approx_latency_ms)

SERVERS = [
  ('localhost', 4007),
  ('10.31.86.217', 6667)
]

server_conns = []
server_conns_lock = threading.Lock()

def forward_to_client(client_conn, server_list, pipe_read_fd):
  print "Starting forward_to_client thread"
  received_data = [""] * len(server_list)
  num_servers_remaining = len(server_list)
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
        if received_data[index][-1] == '\n':
          num_servers_remaining -= 1
          if num_servers_remaining == 0:
            for j in range(len(server_list)):
              if received_data[index] != received_data[j]:
                print "ERROR: Not all servers returned the same response:"
                print "Server %d: %r" % (index, received_data[index])
                print "Server %d: %r" % (j, received_data[j])
            print "Sending data back to client: " + received_data[index]
            # raw_input("Press enter to continue ")
            client_conn.sendall(received_data[index])
            received_data = [""] * len(server_list)
            num_servers_remaining = len(server_list)
      elif r == pipe_read_fd:
        print "Read data from pipe"
        read_from_pipe = True
    if read_from_pipe:
      break

def handle_client(client_socket):
  client_data = ''

  for server_conn in server_conns:
    server_conn.connect()

  r, w = os.pipe()

  t = threading.Thread(target=forward_to_client,
                   args=(client_socket, [c.conn for c in server_conns], r))
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
      # raw_input("Press enter to continue ")
      server_conns_lock.acquire()
      server_latencies = sorted([(server_conn.approx_latency_ms, server_conn) for server_conn in server_conns], reverse=True)
      server_conns_lock.release()
      begin = datetime.datetime.now()
      server_latencies[0][1].process_command(client_data)
      for i in range(1, len(server_latencies)):
        prev_latency = server_latencies[i-1][0]
        latency_diff = server_latencies[i][0] - prev_latency
        while ((datetime.datetime.now() - begin).seconds / 1000.0) < latency_diff:
          pass
        server_latencies[i][1].process_command(client_data)
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
      server_conn._measure_latency(3)
      server_conns_lock.release()
      if server_conn.server_alive:
        print "Server %s is alive, latency is %r" % (server_conn.host, server_conn.approx_latency_ms)
      else:
        print "Server %s is dead" % server_conn.host
    time.sleep(PAUSE_SECONDS_BETWEEN_LATENCY_SAMPLES)

def main():
  for server_host, server_port in SERVERS:
    s = ServerConn(server_host, server_port)
    server_conns.append(s)

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
