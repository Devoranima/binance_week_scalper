from updater.server import startServer, debug
from bot.server import startBots
import sys
import argparse



def parseArgs():
  parser = argparse.ArgumentParser(prog='Overseer', description='Manage overseer submodules')
  
  subparsers = parser.add_subparsers(dest="command")

  start = subparsers.add_parser("start", help="start specified server")
  start.add_argument("server_name", help='server name to start', choices=['updater', 'bot'])

  parse = subparsers.add_parser("parse", help='parse fresh candles list from binance')
  parse.add_argument("table", choices=["candles", "tradepairs"])

  update = subparsers.add_parser("update", help="update tradepairs tracking status")
  update.add_argument("tracking_status", help="tracking status to set", choices=["track", "untrack"])
  update.add_argument("tradepairs", help="list of tradepairs to update", nargs='+')


  show = subparsers.add_parser("show", help="output stored tradepairs")
  show.add_argument("-f", "--filter", nargs="?", const="none-filter", help="filter tradepairs", choices=['tracking', 'untracking', 'none-filter'])
  
  args = parser.parse_args()

  return args



def main():
  args = parseArgs()
  match args.command:
    case 'start':
      if args.server_name == 'bot':
        startBots()
      else:
        #startServer()
        debug()
    case _:
      pass
  
  
if __name__ == '__main__':
  main()