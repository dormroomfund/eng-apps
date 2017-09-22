#!/usr/bin/env python3.6

import sys, os, stat, subprocess, multiprocessing, json, traceback, requests, tempfile, re, random, psutil
from datetime import datetime
from common import decrypt_files, remove_files, hide_private_key

HAS_VARS = os.getenv('TRAVIS_SECURE_ENV_VARS', 'false') == 'true'
API_URL = 'https://drf-eng-apps.herokuapp.com'
URL_REGEX = re.compile(r'^(?:(?:https?|ftp|file)://)(?:\S+(?::\S*)?@)?(?:(?:[1-9]\d?|1\d\d|2[01]\d|22[0-3])(?:\.(?:1?\d{1,2}|2[0-4]\d|25[0-5])){2}(?:\.(?:[1-9]\d?|1\d\d|2[0-4]\d|25[0-4]))|(?:(?:[a-z\u00a1-\uffff0-9]+-?)*[a-z\u00a1-\uffff0-9]+)(?:\.(?:[a-z\u00a1-\uffff0-9]+-?)*[a-z\u00a1-\uffff0-9]+)*(?:\.(?:[a-z\u00a1-\uffff]{2,})))(?::\d{2,5})?(?:/[^\s]*)?$')

class TestFailed(Exception):
  pass

def branch():
  return os.getenv('TRAVIS_PULL_REQUEST_BRANCH') or os.getenv('TRAVIS_BRANCH')

def is_pr():
  return bool(os.getenv('TRAVIS_PULL_REQUEST_SLUG'))

def user():
  slug = os.getenv('TRAVIS_PULL_REQUEST_SLUG')
  if not slug:
    return None
  return slug.split('/')[0]

def kill_children(port):
  subprocess.run('lsof -Pti :{} | xargs kill'.format(port), shell=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
  for child in psutil.Process().children(recursive=True):
    child.kill()

def fail(s, *args):
  text = s.format(*args)
  print("FATAL: {}".format(text))
  raise TestFailed(text)

def warn(s, *args):
  print('WARN: {}'.format(s.format(*args)), file=sys.stderr)

def child_fail(s):
  fail('{}\n\n{}', s, traceback.format_exc())

def post_comment(user, ex=None):
  valid = not bool(ex)
  message = str(ex) if ex else ''
  requests.post(API_URL, {'user': user, 'branch': branch(), 'message': message, 'valid': valid})

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
  try:
    if not exists(root):
      fail('could not find application directory for `{}`'.format(username))
    time = datetime.utcfromtimestamp(os.path.getmtime(root)).strftime('%B %d, %Y')
    print('\n{} ({})\n---'.format(username, time))
    _check_application(root)
  except TestFailed as ex:
    print('This application is not valid.')
    post_comment(username, ex)
    if is_pr():
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

def fix_if_not_executable(file):
  if not os.access(file, os.X_OK):
    warn('{} is not executable, fixing...', file)
    os.chmod(file, os.stat(file).st_mode | stat.S_IEXEC)

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
  build = os.path.join('challenge', 'run.sh')

  if exists(build):
    fix_if_not_executable(build)
    try:
      with tempfile.TemporaryFile() as f:
        result = subprocess.run(build, timeout=1, stdout=f, stderr=f, shell=True)
        f.seek(0)
        output = f.read().decode('utf-8')
    except OSError as e:
      if e.errno == 8:
        fail('{} is missing a shebang', build)
      else:
        raise
    except subprocess.TimeoutExpired:
      fail('{} timed out after 10 seconds - if you are starting a server, make sure you background it and print a URL', build)
    if result.returncode != 0:
      fail('{} exited with nonzero status {}\n\n output: \n\n {}', build, result.returncode, output)
    if not output:
      fail('{} did not output anything', build)
    if not URL_REGEX.match(output):
      fail('{} did not output a URL with scheme http, https, ftp, or file\n\n output: \n\n {}', build, output)
  elif exists(index):
    raise_if_empty(index)
  elif not any(exists('{}.enc'.format(x)) for x in [index, build]):
    fail('neither {} not {} is present', index, build)

def verify_application(root):
  os.environ['PORT'] = str(random.randint(3000, 8000))
  hide_private_key()
  os.chdir(root)
  try:
    _verify_application()
  except TestFailed:
    raise
  except Exception:
    child_fail('application could not be verified')
  finally:
    kill_children(os.environ['PORT'])

def start_verify_process(root):
  pool = multiprocessing.Pool(processes=1, maxtasksperchild=1)
  pool.apply(verify_application, args=(root,))
  pool.close()
  pool.join()

def init():
  if not HAS_VARS:
    warn('Skipping decryption calls (no private key)')
  multiprocessing.set_start_method('spawn')

def run():
  init()
  check_applications()

if __name__ == '__main__':
  run()
