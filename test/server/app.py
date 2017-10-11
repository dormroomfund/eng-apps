import os, markdown
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_basicauth import BasicAuth
from github import Github
from ..application import Applications

app = Flask(__name__)
app.config['BASIC_AUTH_USERNAME'] = os.getenv('BASIC_AUTH_USERNAME')
app.config['BASIC_AUTH_PASSWORD'] = os.getenv('BASIC_AUTH_PASSWORD')

basic_auth = BasicAuth(app)
github = Github(os.getenv('GH_TOKEN'))

def valid():
  return request.values['valid'].lower() == 'true'

def full_pr_message(valid, message):
  if valid:
    return "Your application is valid so far! :sunglasses:\n\nIf you have encrypted files, I'll check those for errors after @{} merges your application.".format(os.getenv('GH_ADMIN'))
  else:
    return 'Your application is invalid! The reason is: **{}**'.format(message)

def create_issue_comment(repo, user):
  title = "Invalid Application: {}".format(user)
  valid_message = 'Thanks @{}, your application has been fixed!'.format(user)
  invalid_message = 'Hey @{}, {}'.format(user, full_pr_message(False, request.values['message']))
  try:
    issue = filter(lambda x: not x.get('pull_request'), repo.get_issues(mentioned=github.get_user(user)))[0]
  except IndexError:
    if not valid():
      repo.create_issue(title, invalid_message, labels=['application-invalid'])
  else:
    if valid():
      issue.create_comment(valid_message)
      issue.edit(state='closed')
    else:
      comments = list(issue.get_comments())
      body = comments[-1].body if comments else issue.body
      if body != invalid_message:
        issue.create_comment(invalid_message)

def create_pr_comment(pr):
  message = full_pr_message(valid(), request.values.get('message'))
  comments = list(filter(lambda x: x.user.login == os.getenv('GH_USER'), pr.get_issue_comments()))
  if comments and comments[-1].body == message:
    return
  else:
    pr.create_issue_comment(message)

@app.route('/', methods=['POST'])
def api():
  repo = github.get_repo(os.getenv('GH_REPO'))
  user = request.values['user']
  try:
    pr = repo.get_pulls(head='{}:{}'.format(user, request.values['branch']))[0]
  except IndexError:
    create_issue_comment(repo, user)
  else:
    create_pr_comment(pr)

  return jsonify({'error': None})

@app.route('/applications')
@basic_auth.required
def admin():
  applications = sorted(Applications(), key=lambda x: x.submitted_raw)
  return render_template('admin.html', applications=applications)

@app.route('/applications/<path:path>')
@basic_auth.required
def file(path):
  return send_from_directory(os.path.join('..', '..', 'applications'), path)

@app.route('/md2html/applications/<path:path>')
@basic_auth.required
def md2html_file(path):
  with open(os.path.join('applications', path)) as f:
    html = markdown.markdown(f.read())
  return render_template('echo.html', path=path, html=html)
