from src.server import updateTradepairs, getTradepairs, switchTradepairsTrakingStatus, startRoutine
import sys
import argparse



def parseArgs():
  parser = argparse.ArgumentParser(prog='Overseer', description='Manage overseer submodules')
  
  subparsers = parser.add_subparsers(dest="command")

  start = subparsers.add_parser("start", help="start specified server")
  start.add_argument("-s", "--server_name", nargs='?', help='server name to start', choices=['updater', 'bot'])

  parse = subparsers.add_parser("parse_tradepairs", help='parse tradepairs list from binance')

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
      startRoutine(args.server_name)
    case 'show':
      getTradepairs(args.filter)
    case 'update':
      switchTradepairsTrakingStatus(args.tracking_status == 'track', args.tradepairs)
    case 'parse':
      updateTradepairs()
      pass
  
  
if __name__ == '__main__':
  main()