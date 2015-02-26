#!/usr/bin/env python

import datetime
import os
import pyping
import random
import select
import socket
import sys
import threading

WEIGHTED_MOVING_AVERAGE_COEFF_ALPHA = 0.2

class ServerConn:
  def __init__(self, host, port):
    self.host = host
    self.port = port
    self.approx_latency_ms = float('inf')
    self.conn = None

  def connect(self):
    # self._measure_latency()
    self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.conn.connect((self.host, self.port))

  def close(self):
    if not self.conn:
      return
    self.conn.close()
    self.conn = None

  def process_command(self, command_str):
    if not self.conn:
      return
    self.conn.sendall(command_str)

  def _measure_latency(self):
    if self.approx_latency_ms == float('inf'):
      self.approx_latency_ms = float(pyping.ping(self.host).avg_rtt)
    for i in range(10):
      latency_sample = float(pyping.ping(self.host).avg_rtt)
      self.approx_latency_ms = (WEIGHTED_MOVING_AVERAGE_COEFF_ALPHA * latency_sample) + ((1 - WEIGHTED_MOVING_AVERAGE_COEFF_ALPHA) * self.approx_latency_ms)

SERVERS = [
  ('localhost', 4007), 
  # ('10.34.134.122', 6667) 
]

server_conns = []

def forward_to_client(client_conn, server_conn, pipe_read_fd):
  # print "Starting forward_to_client thread"
  while True:
    rlist, _, _ = select.select([server_conn, pipe_read_fd], [], [])
    read_from_pipe = False
    for r in rlist:
      if r == server_conn:
        d = server_conn.recv(5)
        print "Read", len(d), "bytes of data from server:"
        print d
        print
        if not d:
          break
        client_conn.sendall(d)
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
                   args=(client_socket, server_conns[0].conn, r))
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
      print "Client executed command: " + client_data
      # server_latencies = sorted([(server_conn.approx_latency_ms, server_conn) for server_conn in server_conns], reverse=True)
      # begin = datetime.datetime.now()
      # server_latencies[0][1].process_command(client_data)
      # for i in range(1, len(server_latencies)):
        # break
        # prev_latency = server_latencies[i-1][0]
        # latency_diff = server_latencies[i][0] - prev_latency
        # while ((datetime.datetime.now() - begin).seconds / 1000.0) < latency_diff:
          # pass
        # begin = datetime.datetime.now()
        # server_latencies[i][1].process_command(client_data)
      for server_conn in server_conns:
        server_conn.process_command(client_data)
      client_data = ''

  os.write(w, "A")
  t.join()

  for server_conn in server_conns:
    server_conn.close()

def main():
  for server_host, server_port in SERVERS:
    s = ServerConn(server_host, server_port)
    # s.connect()
    server_conns.append(s)

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

    try:
      # print "a"
      client_socket, client_address = client_listen_socket.accept()
      print "accept() returned"
      # print "b"
      # print "c"
      # client_socket.sendall("OK MPD 0.19.8\n")
      # print "d"
      # print "New thread =", t
      # print "e"
      handle_client(client_socket)
      # print "f"
      print "Returned from handle_client"
    # except:
      # print "Received exception: " + sys.exc_info()[0]
    finally:
      # os.write(w, "A")
      # t.join()
      # print "t exited"
      client_socket.close()
      print
      print
      print
      print

if __name__ == '__main__':
  main()
