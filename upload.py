from paramiko import SSHClient
from scp import SCPClient
import sys
SONG_PATH = sys.argv[1]
SERVERS = [("localhost", "~/Desktop/Songs/191")]
for server in SERVERS:
  ssh = SSHClient()
  ssh.load_system_host_keys()
  if server[0] == "localhost":
    continue
  ssh.connect(server[0])
  scp = SCPClient(ssh.get_transport())
  scp.put(SONG_PATH, server[1])
