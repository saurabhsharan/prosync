import random
import socket
import threading

class MPDServerConn:
  def __init__(self, host, port):
    self.host = host
    self.port = port
    self.conn = None

  def connect(self):
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

SERVERS = [
  ('localhost', 4007), 
  # ('10.31.83.163', 6667) 
]

server_conns = []

def forward_to_client(client_conn, server_conn):
  while True:
    client_conn.sendall(server_conn.recv(1))

def handle_client(client_socket):
  client_data = ''

  in_command_list = False

  while True:
    c = client_socket.recv(1)

    if not c:
      print "Client closed connection"
      client_socket.close()
      break

    client_data += c

    if client_data[-1] == '\n':
      print "Client executed command: " + client_data
      for server_conn in server_conns:
        server_conn.process_command(client_data)
      client_data = ''

def main():
  for server_host, server_port in SERVERS:
    s = MPDServerConn(server_host, server_port)
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
      threading.Thread(target=forward_to_client,
                       args=(client_socket, server_conns[0].conn)).start()
      handle_client(client_socket)
    finally:
      print "Closing client socket after exception"
      client_socket.close()

if __name__ == '__main__':
  main()
