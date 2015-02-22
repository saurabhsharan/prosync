#!/usr/bin/env python

import datetime
import pyping
import random
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
  ('10.34.134.122', 6667) 
]

server_conns = []

# kill_thread = False

def forward_to_client(client_conn, server_conn):
  # try:
    # while not kill_thread:
  while True:
    d = server_conn.recv(1)
      # if not d:
        # break
    client_conn.sendall(d)
  # except:
    # pass
  # finally:
    # print "Exiting background thread"

def handle_client(client_socket):
  client_data = ''

  while True:
    c = client_socket.recv(1)

    if not c:
      print "Client closed connection"
      break

    client_data += c

    if client_data[-1] == '\n':
      print "Client executed command: " + client_data
      server_latencies = sorted([(server_conn.approx_latency_ms, server_conn) for server_conn in server_conns], reverse=True)
      begin = datetime.datetime.now()
      # server_latencies[0][1].process_command(client_data)
      for i in range(1, len(server_latencies)):
        break
        prev_latency = server_latencies[i-1][0]
        latency_diff = server_latencies[i][0] - prev_latency
        while ((datetime.datetime.now() - begin).seconds / 1000.0) < latency_diff:
          pass
        begin = datetime.datetime.now()
        server_latencies[i][1].process_command(client_data)
      for latency, server_conn in server_latencies:
        server_conn.process_command(client_data)
      client_data = ''

def main():
  for server_host, server_port in SERVERS:
    s = ServerConn(server_host, server_port)
    s.connect()
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
      client_socket, client_address = client_listen_socket.accept()
      print "accept() returned"
      # client_socket.settimeout(2.5)
      t = threading.Thread(target=forward_to_client,
                       args=(client_socket, server_conns[0].conn))
      t.start()
      handle_client(client_socket)
    except:
      print "Received exception: " + sys.exc_info()[0]
    finally:
      # kill_thread = True
      t.join()
      # kill_thread = False
      client_socket.close()

if __name__ == '__main__':
  main()
