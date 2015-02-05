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

SERVERS = [('localhost', 4007)]

server_conns = []

LISTEN_PORT = 3458

def main():
  for server_host, server_port in SERVERS:
    s = MPDServerConn(server_host, server_port)
    s.connect()
    server_conns.append(s)

  print 'Listening on port %d' % LISTEN_PORT

  client_listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  client_listen_socket.bind(('', LISTEN_PORT))
  client_listen_socket.listen(10)

  while True:
    print 'Waiting for client to connect to proxy...'

    try:
      client_socket, client_address = client_listen_socket.accept()

      client_socket.sendall("OK MPD 0.19.8\n")

      client_data = ''

      while True:
        print "Waiting for data from client..."
        client_data += client_socket.recv(1)

        if client_data.find('\n') != -1:
          for server_conn in server_conns:
            server_conn.process_command(client_data[:(client_data.find('\n') + 1)])
          break
    finally:
      print "Closing client socket after exception"
      client_socket.close()

if __name__ == '__main__':
  main()
