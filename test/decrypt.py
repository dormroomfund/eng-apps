import sys, os
from common import decrypt_files

if __name__ == '__main__':
  root = os.path.join('applications', sys.argv[1]) if len(sys.argv) > 1 else 'applications'
  print(decrypt_files(root))
