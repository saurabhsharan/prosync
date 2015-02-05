import random
import socket

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

  # reads upto \n
  def read(self):
    read_data = ''

    while True:
      read_data += self.conn.recv(1)
      if read_data[-1] == '\n':
        return read_data

SERVERS = [
  ('localhost', 4007), 
  # ('10.31.83.163', 6667) 
]

server_conns = []

def read_until_newline(conn):
  read_data = ''
  while True:
    read_data += conn.recv(1)
    if read_data[-1] == '\n':
      return read_data

def handle_client(client_socket):
  ok_message = server_conns[0].read()
  client_socket.sendall(ok_message)

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

      if client_data[:-1] == 'command_list_ok_begin':
        in_command_list = True
      elif client_data[:-1] == 'command_list_ok_end':
        in_command_list = False

      if not in_command_list:
        server_response = server_conns[0].read()
        print "Server responded with: " + server_response
        client_socket.sendall(server_response)

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

  client_listen_socket.listen(10)

  print "Listening on port %d" % listen_port

  while True:
    print "Waiting for client to connect to proxy..."

    try:
      client_socket, client_address = client_listen_socket.accept()
      handle_client(client_socket)
    finally:
      print "Closing client socket after exception"
      client_socket.close()

if __name__ == '__main__':
  main()
