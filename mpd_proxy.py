import random
import socket
import threading

class Connection:
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

class ServerConn(Connection):
  def process_command(self, command_str):
    if not self.conn:
      return
    self.conn.sendall(command_str)

class ClientConn(Connection):
  pass

SERVERS = [
  ('localhost', 4007), 
  # ('10.31.83.163', 6667) 
]

server_conns = []

kill_thread = False

def forward_to_client(client_conn, server_conn):
  try:
    while not kill_thread:
      d = server_conn.recv(1)
      if not d:
        break
      client_conn.sendall(d)
  except:
    pass
  finally:
    print "Exiting background thread"

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
      for server_conn in server_conns:
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
      client_socket.settimeout(2.5)
      t = threading.Thread(target=forward_to_client,
                       args=(client_socket, server_conns[0].conn))
      t.start()
      handle_client(client_socket)
    except:
      print "Received exception: " + sys.exc_info()[0]
    finally:
      kill_thread = True
      t.join()
      kill_thread = False
      client_socket.close()

  print "?????????????"

if __name__ == '__main__':
  main()
