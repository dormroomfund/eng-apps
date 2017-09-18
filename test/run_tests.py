#!/usr/bin/env python3.6

import sys, os, base64, subprocess, multiprocessing, json, traceback, functools, requests
from datetime import datetime

HAS_VARS = os.getenv('TRAVIS_SECURE_ENV_VARS', 'false') == 'true'
API_URL = 'https://drf-eng-apps.herokuapp.com'

class TestFailed(Exception):
  pass

def branch():
  return os.getenv('TRAVIS_PULL_REQUEST_BRANCH') or os.getenv('TRAVIS_BRANCH')

def user():
  slug = os.getenv('TRAVIS_PULL_REQUEST_SLUG')
  if not slug:
    return None
  return slug.split('/')[0]

def with_vars(arg):
  default = None if callable(arg) else arg

  def with_vars_wrapper(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
      if not HAS_VARS:
        return default
      return f(*args, **kwargs)
    return wrapper

  return with_vars_wrapper(arg) if callable(arg) else with_vars_wrapper

def fail(s, *args):
  text = s.format(*args)
  print("FATAL: {}".format(text))
  raise TestFailed(text)

def child_fail(s):
  fail('{}\n\n{}', s, traceback.format_exc())

def post_comment(user, ex=None):
  valid = not bool(ex)
  message = str(ex) if ex else ''
  requests.post(API_URL, {'user': user, 'branch': branch(), 'message': message, 'valid': valid})

@with_vars
def write_private_key():
  with open('private.pem', 'wb') as f:
    f.write(base64.b64decode(os.environ['PRIVATE_KEY']))

@with_vars
def remove_private_key():
  os.remove('private.pem')

@with_vars
def hide_private_key():
  del os.environ['PRIVATE_KEY']
  assert not subprocess.run('echo $PRIVATE_KEY', stdout=subprocess.PIPE, shell=True).stdout.strip()

@with_vars
def decrypt_file(infile, outfile):
  subprocess.run([
    'openssl',
    'smime',
    '-decrypt',
    '-binary',
    '-inkey',
    'private.pem',
    '-inform',
    'DEM',
    '-in',
    infile,
    '-out',
    outfile,
  ]).check_returncode()

@with_vars([])
def decrypt_files(application_root):
  write_private_key()
  decrypted = []
  for root, dirs, files in os.walk(application_root):
      for file in files:
        if file.endswith('.enc'):
          infile = os.path.join(root, file)
          outfile = infile[:-4]
          decrypt_file(infile, outfile)
          decrypted.append(outfile)
  remove_private_key()
  return decrypted

def remove_files(files):
  for file in files:
    os.remove(file)

def check_applications():
  if user():
    check_application(user())
    return

  for username in os.listdir('applications'):
    if username.startswith('.'):
      continue
    check_application(username)

def check_application(username):
  root = os.path.join('applications', username)
  time = datetime.utcfromtimestamp(os.path.getmtime(root)).strftime('%B %d, %Y')
  print('\n{} ({})\n---'.format(username, time))
  try:
    _check_application(root)
  except TestFailed as ex:
    print('This application is not valid.')
    post_comment(username, ex)
    exit(1)
  else:
    print('This application is valid!')
    post_comment(username)

def _check_application(root):
  decrypted = decrypt_files(root)
  try:
    start_verify_process(root)
  finally:
    remove_files(decrypted)

def exists(file):
  return os.path.exists(file)

def raise_if_not_exists(file):
  if not exists(file) and (HAS_VARS or not exists('{}.enc'.format(file))):
    fail('{} is required but not found!'.format(file))

def raise_if_empty(file, min_length=100):
  with open(file) as f:
    content = f.read()
  if len(content) < 100:
    fail('{} should be at least {} chars long', file, min_length)

def raise_if_not_executable(file):
  if not os.access(file, os.X_OK):
    fail('{} is not executable', file)

def check_json():
  required_keys = {
    'first_name',
    'last_name',
    'resume',
    'university',
    'grad_year',
    'linkedin',
    'email'
  }
  with open('application.json') as f:
    try:
      application = json.loads(f.read())
    except ValueError:
      fail('invalid JSON in application.json')

  missing = required_keys - set(application.keys())
  if missing:
    fail('missing keys in application.json: {}', missing)

def _verify_application():
  for required in ['application.json', 'essay.md', 'challenge']:
    raise_if_not_exists(required)

  if exists('application.json'):
    check_json()

  if exists('essay.md'):
    raise_if_empty('essay.md')

  index = os.path.join('challenge', 'index.html')
  build = os.path.join('challenge', 'build.sh')

  if exists(build):
    raise_if_not_executable(build)
    result = subprocess.run(build, stdout=subprocess.PIPE, timeout=30)
    if result.returncode != 0:
      fail('{} exited with nonzero status {}', build, result.returncode)
    if not result.stdout:
      fail('{} did not output anything', build)
  elif exists(index):
    raise_if_empty(index)
  elif not any(exists('{}.enc'.format(x)) for x in [index, build]):
    fail('neither {} not {} is present', index, build)

def verify_application(root):
  hide_private_key()
  os.chdir(root)
  try:
    _verify_application()
  except TestFailed:
    raise
  except Exception:
    child_fail('application could not be verified')

def start_verify_process(root):
  pool = multiprocessing.Pool(processes=1, maxtasksperchild=1)
  pool.apply(verify_application, args=(root,))
  pool.close()
  pool.join()

def init():
  if not HAS_VARS:
    print('Warning: Skipping decryption calls (no private key)', file=sys.stderr)
  multiprocessing.set_start_method('spawn')

def run():
  init()
  check_applications()

if __name__ == '__main__':
  run()
