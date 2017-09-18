import sys
from run_tests import decrypt_files

if __name__ == '__main__':
  print(decrypt_files('applications/{}'.format(sys.argv[1])))
