#!/usr/bin/env python

# Utility script to copy a song file to a list of MPD servers.

import os
import sys

def read_servers_file(filename):
  result = []
  f = open(filename)
  for line in f:
    line2 = line.strip()
    if line2:
      ip_address_port, user, dest_directory = line2.split()
      result.append((ip_address_port.split(":")[0], user, dest_directory))
  return result

def main(song_filename, servers_filename):
  servers_info = read_servers_file(servers_filename)

  for ip_address, user, dest_directory in servers_info:
    scp_command = "scp %s %s@%s:%s" % (song_filename, user, ip_address, dest_directory)
    print scp_command
    os.system(scp_command)

if __name__ == '__main__':
  if len(sys.argv) < 3:
    print "Usage: ./mpd-upload.py path-to-music-file path-to-mpd-servers-file"
    sys.exit(1)

  song_filename = sys.argv[1]
  servers_filename = sys.argv[2]
  main(song_filename, servers_filename)
