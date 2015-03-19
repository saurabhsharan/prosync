#!/usr/bin/env python

import os
import sys

SERVERS_FILENAME = 'mpd_servers'

def read_servers_file(filename):
  result = []
  f = open(filename)
  for line in f:
    line2 = line.strip()
    if line2:
      ip_address, user, dest_directory = line2.split()
      result.append((ip_address, user, dest_directory))
  return result

def main(song_filename):
  servers_info = read_servers_file(SERVERS_FILENAME)

  for ip_address, user, dest_directory in servers_info:
    scp_command = "scp %s %s@%s:%s" % (song_filename, user, ip_address, dest_directory)
    print scp_command
    # raw_input()
    os.system(scp_command)

if __name__ == '__main__':
  if len(sys.argv) < 2:
    print "Usage: ./mpd-upload.py path-to-music-file"
    sys.exit(1)

  song_filename = sys.argv[1]
  main(song_filename)
