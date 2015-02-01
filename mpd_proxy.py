import socket

class MPDServerConn:
  def __init__(self, host, port):
    self.host = host
    self.port = port

  def connect(self):
    self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.conn.connect((self.host, self.port))

  def process_command(command_str):
    self.conn.sendall(command_str)

SERVERS = [('localhost', 8888)]

server_conns = []

def main():
  for server in SERVERS:
    s = MPDServerConn(server[0], server[1])
    s.connect()
    server_conns.append(s)

  client_listen_socket = socket.socket(socket.AF_INET, sock.SOCK_STREAM)
  client_listen_socket.bind(('', 7777))
  client_listen_socket.listen(10)

  while True:
    print 'Waiting for client to connect to proxy...'

    client_socket, client_address = client_listen_socket.accept()

    client_data = ''

    while True:
      client_data += conn.recv()
      if client_data.find('\n') != -1:
        # process_command(client_data[:(client_data.find('\n') + 1)])
        for server_conn in server_conns:
          server_conn.process_command(client_data[:(client_data.find('\n') + 1)])
      break
        # client_data = client_data[(client_data.find('\n') + 1):]

    client_socket.close()

if __name__ == '__main__':
  main()
