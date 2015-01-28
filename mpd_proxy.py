import socket

SERVERS = [('localhost', 8888)]

server_conns = []

def process_command(command_str):
  for server_conn in server_conns:
    server_conn.sendall(command_str)

def main():
  for server in SERVERS:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(server)
    server_conns.append(s)
  
  s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  s.bind(('', 7777))
  s.listen(10)
  
  print 'Waiting for client to connect to proxy...'
  
  conn, address = s.accept()
  
  client_data = ''
  
  while True:
    client_data += conn.recv()
    if client_data.find('\n') != -1:
      process_command(client_data[:(client_data.find('\n') + 1)])
      client_data = client_data[(client_data.find('\n') + 1):]
    

if __name__ == '__main__':
  main()
