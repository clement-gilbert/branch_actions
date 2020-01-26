# -*- coding: UTF-8 -*-

# Integrated dependencies
import os
import re
import copy
import time

# External dependencies
import inquirer
from termcolor import colored
from git import Repo, Commit
from github import Github
import slack
from notion.client import NotionClient
from notion.block import TextBlock, TodoBlock, CodeBlock, HeaderBlock, SubheaderBlock, SubsubheaderBlock, BulletedListBlock, QuoteBlock

# Load Config vars
from vars import *









'''
---------------------
Readme
---------------------


Purpose:
---

When they are a lot of repo and a lot of branches to manage,
you have to put the git commands with the name of the branch on it,
checkout, commit, push, create pr, delete branch,
it take time, and you have to list the branches you use

The goal of this script is for each repo to list the branches you work on,
select a branch and then select the action you want to do

At start you create your branch and put params on the branch (feat or fix, scope, NotionID),
all of this params will be used to create the commits,
after this, the script create the branch and save the params

On the nexts launch, it detect the branch and load the params,
you can select another branch and the script will git checkout to the branch


When your on the branch you can do actions :

  - Commit: It ask you the message, and it add the type (feat, fix), the scope, the NotionID

  - Refresh commits on card: It put on the Notion card the commits of this branch with github links

  - Push branch: Push branch on github

  - PR branch: Pull request on github of this branch to the dev_branch, it send a message on slack to ask for merging with the github link

  - Delete branch: Checkout to dev_branch, delete branch, then pull

  - Change state: Can change the state of the branch so you the status of the branch on the file list









Install:
---

Install python3, virtualenv and pip3
python3 -m virtualenv env
source env/bin/activate

pip3 install inquirer
pip3 install termcolor
pip3 install gitpython
pip3 install PyGithub
pip3 install slackclient
pip3 install notion

./branch_action.sh
Create alias so you can launch it from anywhere





Set-Up:
---
Populate vars.py:

  - Put the branch list file path on BRANCH_FILE

  - Populate REPO_LIST:
    - text_name: The name of the repo, will be display on the BRANCH_FILE
    - repo_name: git repo name
    - repo_type: Type of the repo, so the merge request will be sent to a slack channel depending on it [optional]
    - dev_branch: Branch name from where the branches will be created
    - parent_folder_contains: The folder contain this string, used if one repo have multiple projects [optional]
    
 - Put the credentials

 - Fill the other vars



'''


















# --------------------------------------------------------------
# --------------------------------------------------------------


















# ---------------------
# Config Vars 
# ---------------------

BRANCH_STATE_LIST = [
  { "state": "Sleeping branch", "deleted": False },
  { "state": "To merge", "deleted": False },
  { "state": "To recreate for fixes", "deleted": True }
  ]

DEFAULT_STATE = { "state": "", "deleted": False }




# Formater
IS_DELETED_TEXT = "Deleted"
REPO_DELIMITER = " :"
TEXT_DELIMITER = "  -  "
PARAM_DELIMITER = "  |  "
VALUE_DELIMITER = "  =  "
RETURN_LINE = "\n"



# Can have all
COMMIT_REGEX = "[\s\S]*"
SCOPE_REGEX = "[\s\S]*"
NOTIONID_REGEX = "[\s\S]*"

# Can have a-z and -
BRANCH_REGEX = "^([a-z-]+)+$"

# Cannot have : nor -
STATE_REGEX = "^([^:-]+)+$"



# Github
GITHUB_BASE_URL = "https://github.com/{}/".format(GITHUB_ORGANIZATION)



# Notion
NOTION_BASE_URL = "https://www.notion.so/"
NOTION_RETURN_LINE = "\n"
NOTION_LINK = '[{}]({} "{}")'
NOTION_ITALIC = "*{}*"
NOTION_BOLD = "**{}**"
NOTION_ITALIC_BOLD = "***{}***"



# Commit emojis
TYPES_EMOJIS = [
{"display_name": "New feature", "id": "feat", "emoji": ":sparkles:"},
{"display_name": "Bugfix", "id": "bug", "emoji": ":bug:"},

{"display_name": "Critical hotfix", "id": "ambulance", "emoji": ":ambulance:"},
{"display_name": "Merging branches", "id": "twisted_rightwards_arrows", "emoji": ":twisted_rightwards_arrows:"},
{"display_name": "Removing code/filesfiles", "id": "fire", "emoji": ":fire:"},
{"display_name": "Move/renam repository", "id": "truck", "emoji": ":truck:"},
{"display_name": "Code review changes", "id": "ok_hand", "emoji": ":ok_hand:"},

{"display_name": "Refactor code", "id": "hammer", "emoji": ":hammer:"},
{"display_name": "Improve format/structure", "id": "art", "emoji": ":art:"},
{"display_name": "Security", "id": "lock", "emoji": ":lock:"},
{"display_name": "Reverting changes", "id": "rewind", "emoji": ":rewind:"},
{"display_name": "Breaking changes", "id": "boom", "emoji": ":boom:"},
{"display_name": "Tests", "id": "rotating_light", "emoji": ":rotating_light:"},
{"display_name": "Adding a test", "id": "white_check_mark", "emoji": ":white_check_mark:"},
{"display_name": "Make a test pass", "id": "heavy_check_mark", "emoji": ":heavy_check_mark:"},
{"display_name": "Continuous Integration", "id": "green_heart", "emoji": ":green_heart:"},

{"display_name": "General update", "id": "zap", "emoji": ":zap:"},
{"display_name": "Initial commit", "id": "tada", "emoji": ":tada:"},
{"display_name": "Version tag", "id": "bookmark", "emoji": ":bookmark:"},
{"display_name": "Metadata", "id": "card_index", "emoji": ":card_index:"},
{"display_name": "Performance", "id": "racehorse", "emoji": ":racehorse:"},
{"display_name": "Cosmetic", "id": "lipstick", "emoji": ":lipstick:"},
{"display_name": "Upgrading dependencies", "id": "arrow_up", "emoji": ":arrow_up:"},
{"display_name": "Downgrading dependencies", "id": "arrow_down", "emoji": ":arrow_down:"},
{"display_name": "Lint", "id": "shirt", "emoji": ":shirt:"},
{"display_name": "Translation", "id": "alien", "emoji": ":alien:"},
{"display_name": "Text", "id": "memo", "emoji": ":pencil:"},
{"display_name": "Deploying stuff", "id": "rocket", "emoji": ":rocket:"},
{"display_name": "Fixing on MacOS", "id": "apple", "emoji": ":apple:"},
{"display_name": "Fixing on Linux", "id": "penguin", "emoji": ":penguin:"},
{"display_name": "Fixing on Windows", "id": "checkered_flag", "emoji": ":checkered_flag:"},
{"display_name": "Work in progress", "id": "construction", "emoji": ":construction:"},
{"display_name": "Adding CI build system", "id": "construction_worker_man", "emoji": ":construction_worker:"},
{"display_name": "Analytics or tracking code", "id": "chart_with_upwards_trend", "emoji": ":chart_with_upwards_trend:"},
{"display_name": "Removing a dependency", "id": "heavy_minus_sign", "emoji": ":heavy_minus_sign:"},
{"display_name": "Adding a dependency", "id": "heavy_plus_sign", "emoji": ":heavy_plus_sign:"},
{"display_name": "Docker", "id": "whale", "emoji": ":whale:"},
{"display_name": "Configuration files", "id": "wrench", "emoji": ":wrench:"},
{"display_name": "Package.json in JS", "id": "package", "emoji": ":package:"},
{"display_name": "Accessibility", "id": "wheelchair", "emoji": ":wheelchair:"}
]









# ---------------------
# Constants
# ---------------------

# Steps
STEP_CHOOSE_LIST_GENERAL = "STEP_CHOOSE_LIST_GENERAL"
STEP_CHOOSE_LIST_BRANCH = "STEP_CHOOSE_BRANCH"
STEP_SET_BRANCH_NAME = "STEP_SET_BRANCH_NAME"
STEP_SHOW_SUMMARY = "STEP_SHOW_SUMMARY"

STEP_CHOOSE_LIST_ACTIONS = "STEP_CHOOSE_LIST_ACTIONS"

STEP_COMMIT = "STEP_COMMIT"
STEP_ADD_COMMITS_TO_CARD = "STEP_ADD_COMMITS_TO_CARD"
STEP_PUSH_BRANCH = "STEP_ACTIONS"
STEP_PR_BRANCH = "STEP_PR_BRANCH"
STEP_DELETE_BRANCH = "STEP_DELETE_BRANCH"
STEP_CHOOSE_LIST_STATE = "STEP_CHOOSE_LIST_STATE"
STEP_SET_STATE_NAME = "STEP_SET_STATE_NAME"



# Choices
STEP_GENERAL_CHOICES = [
  {"display_text": "Continue", "next_step": STEP_CHOOSE_LIST_ACTIONS},
  {"display_text": "Change branch", "next_step": STEP_CHOOSE_LIST_BRANCH},
  {"display_text": "Branches summary", "next_step": STEP_SHOW_SUMMARY},
]

STEP_ACTIONS_CHOICES = [
  {"display_text": "Commit", "next_step": STEP_COMMIT},
  {"display_text": "Refresh commits on card", "next_step": STEP_ADD_COMMITS_TO_CARD},
  {"display_text": "Push branch", "next_step": STEP_PUSH_BRANCH},
  {"display_text": "PR branch", "next_step": STEP_PR_BRANCH},
  {"display_text": "Delete branch", "next_step": STEP_DELETE_BRANCH},
  {"display_text": "Change state", "next_step": STEP_CHOOSE_LIST_STATE},
  {"display_text": "Main menu", "next_step": STEP_CHOOSE_LIST_GENERAL},
]


# Confirms
GENERAL_MESSAGE_SURE = "Sure? (y)"
GENERAL_MESSAGE_CONTINUE = "Continue? (y)"

MESSAGE_CONFIRM_CREATE_BRANCH = "Create? (y)"
MESSAGE_CONFIRM_DELETE_BRANCH = "Delete? (y)"



# Github
GITHUB_OBJ_GIT = Github(GITHUB_TOKEN)
GITHUB_OBJ_ORG = GITHUB_OBJ_GIT.get_organization(GITHUB_ORGANIZATION)


# Slack
SLACK_OBJ_SLACK = slack.WebClient(token=SLACK_TOKEN)


# Notion
NOTION_OBJ = NotionClient(token_v2=NOTION_TOKEN)









# ---------------------
# Global vars
# ---------------------

_actual_step = None
_actual_repo = None
_actual_repo_details = None
_actual_git_branch = None
_actual_branch = None
_branch_list = []
_actual_repo_branch_list = []









# ---------------------
# Doc
# ---------------------

'''

If branch in branch list: STEP_CHOOSE_LIST_GENERAL else: STEP_CHOOSE_LIST_BRANCH
STEP_CHOOSE_LIST_GENERAL
  STEP_CHOOSE_LIST_BRANCH => STEP_CHOOSE_LIST_ACTIONS
    STEP_SET_BRANCH_NAME => STEP_CHOOSE_LIST_ACTIONS
  STEP_SHOW_SUMMARY => STEP_CHOOSE_LIST_GENERAL

  STEP_CHOOSE_LIST_ACTIONS
    STEP_COMMIT => STEP_CHOOSE_LIST_ACTIONS
    STEP_ADD_COMMITS_TO_CARD => STEP_CHOOSE_LIST_ACTIONS
    STEP_PUSH_BRANCH => STEP_CHOOSE_LIST_ACTIONS
    STEP_PR_BRANCH => STEP_CHOOSE_LIST_ACTIONS
    STEP_DELETE_BRANCH => STEP_CHOOSE_LIST_GENERAL
    STEP_CHOOSE_LIST_STATE => STEP_CHOOSE_LIST_ACTIONS or STEP_CHOOSE_LIST_GENERAL
      STEP_SET_STATE_NAME => STEP_CHOOSE_LIST_ACTIONS or STEP_CHOOSE_LIST_GENERAL




_branch_list model :
{
    "repo":"string",
    "branches":[
        {
            "branch_name":"string",
            "state":"string",
            "is_deleted":"boolean",
            "params":[
                {
                    "key":"string",
                    "value":"string"
                }
            ]
        }
    ]
}




Notion blocks at the bottom of a card:
DividerBlock
ColumnListBlock
ColumnBlock
BasicBlock
TodoBlock
CodeBlock
FactoryBlock
HeaderBlock
SubheaderBlock
SubsubheaderBlock
PageBlock
BulletedListBlock
NumberedListBlock
ToggleBlock
QuoteBlock
TextBlock
EquationBlock


Notion notations
[like this](http://someurl "this title shows up when you hover")
*this is in italic*  and _so is this_
**this is in bold**  and __so is this__
***this is bold and italic***  and ___so is this___
First line\nSecond line


'''


















# ---------------------
# Steps
# ---------------------

def go_step_choose_list_general():
  question_list = []
  switcher = {}
  for choice in STEP_GENERAL_CHOICES :
    question_list.append(choice["display_text"])
    switcher[choice["display_text"]] = choice["next_step"]

  title = "Actual branch: " + _actual_branch
  choice = choose_from_list(question_list, title)
  next_step = switcher.get(choice)

  go_step(next_step)


def go_step_choose_list_branch():
  global _actual_branch
  new_branch = "New branch"
  question_list = []

  for branch in _actual_repo_branch_list:
    question_list.append(branch["branch_name"])

  question_list.append(new_branch)
  title = "Choose branch"
  choice = choose_from_list(question_list, title)

  if choice == new_branch:
    next_step = STEP_SET_BRANCH_NAME
  else :
    next_step = STEP_CHOOSE_LIST_ACTIONS
    _actual_branch = choice
    git_go_branch(_actual_branch)

  go_step(next_step)


def go_step_set_branch_name():
  global _actual_branch

  type_question_list = []
  for emoji in TYPES_EMOJIS:
    type_question_list.append(emoji["display_name"])
  type_question_list.append("")
  type_title = "Choose type"

  branch_name = ask_text("Enter the new branch name", BRANCH_REGEX)
  commit_type_display_name = choose_from_list(type_question_list, type_title)
  commit_scope = ask_text("Enter the scope", SCOPE_REGEX)
  commit_notionID = ask_text("Enter the notionID", NOTIONID_REGEX)


  commit_type = ""
  for emoji in TYPES_EMOJIS:
    if emoji["display_name"] == commit_type:
      commit_type = emoji["id"]

  params = []
  if commit_type != "":
    params.append({"key": "type", "value": commit_type})
  if commit_scope != "":
    params.append({"key": "scope", "value": commit_scope})
  if commit_notionID != "":
    params.append({"key": "notionID", "value": commit_notionID})

  _actual_branch = branch_name
  create_branch(_actual_branch)
  update_branch_state(_actual_branch, DEFAULT_STATE["state"], DEFAULT_STATE["deleted"], params=params)

  go_step(STEP_CHOOSE_LIST_ACTIONS)


def go_step_show_summary():
  text = var_to_txt(_branch_list)
  print(text)
  resp_confirm = ask_confirm("Show summary, Continue?")

  if resp_confirm:
    next_step = STEP_CHOOSE_LIST_GENERAL
  else:
    next_step = STEP_SHOW_SUMMARY

  go_step(next_step)


def go_step_choose_list_actions():
  question_list = []
  switcher = {}
  for choice in STEP_ACTIONS_CHOICES :
    question_list.append(choice["display_text"])
    switcher[choice["display_text"]] = choice["next_step"]

  title = "Action"
  choice = choose_from_list(question_list, title)
  next_step = switcher.get(choice)

  go_step(next_step)


def go_step_commit():
  commit_descr = ask_text("Write the commit description", COMMIT_REGEX)
  is_branch_in_repo_branches_res = is_branch_in_repo_branches(_actual_branch)
  if not is_branch_in_repo_branches_res["is_branch"]:
    go_step(STEP_CHOOSE_LIST_ACTIONS)
  else:
    branch_details = is_branch_in_repo_branches_res["branch"]
    params = []
    if "params" in branch_details:
      params = branch_details["params"]
    commit_message = create_commit_message(commit_descr, params)

    write_before_step()
    print('The commit will be: ' + commit_message)
    resp_confirm = ask_confirm('Continue?')
    if resp_confirm:
      git_commit_res = git_commit(commit_message)
      write_before_step()
      print(git_commit_res)
      ask_press_key("Continue")
      go_step(STEP_CHOOSE_LIST_ACTIONS)
    else:
      go_step(STEP_CHOOSE_LIST_ACTIONS)


def go_step_add_commits_to_card():
  resp_confirm = ask_confirm("Refresh commits on card, Confirm?")

  if resp_confirm:
    res_send_commits_to_card = send_commits_to_card()
    text = ""
    if res_send_commits_to_card["is_error"]:
      text += "Error: "
      text += res_send_commits_to_card["data"]["message"]
    else:
      text += "Card url: "
      text += res_send_commits_to_card["data"]["notion_link"]
    write_before_step()
    print(text)
    ask_press_key("Continue")
    go_step(STEP_CHOOSE_LIST_ACTIONS)
  else:
    go_step(STEP_CHOOSE_LIST_ACTIONS)


def go_step_push_branch():
  resp_confirm = ask_confirm("Push branch, Confirm?")

  if resp_confirm:
    git_push_branch(_actual_branch)
    go_step(STEP_CHOOSE_LIST_ACTIONS)
  else:
    go_step(STEP_CHOOSE_LIST_ACTIONS)


def go_step_pr_branch():
  resp_confirm = ask_confirm("PR branch, Confirm?")

  if resp_confirm:
    do_pr(_actual_branch)
    go_step(STEP_CHOOSE_LIST_ACTIONS)
  else:
    go_step(STEP_CHOOSE_LIST_ACTIONS)


def go_step_delete_branch():
  resp_confirm = ask_confirm("Delete branch, Confirm?")

  if resp_confirm:
    delete_branch(_actual_branch)
    go_step(STEP_CHOOSE_LIST_GENERAL)
  else:
    go_step(STEP_CHOOSE_LIST_ACTIONS)


def go_step_choose_list_state():
  global _actual_branch
  nothing = "Nothing"
  other = "Other"
  question_list = []

  question_list.append(nothing)
  for state in BRANCH_STATE_LIST:
    question_list.append(state["state"])
  question_list.append(other)

  title = "Choose state"
  choice = choose_from_list(question_list, title)

  if choice == other:
    next_step = STEP_SET_STATE_NAME
    go_step(next_step)
  else :
    is_deleted = False

    if choice == nothing:
      choice = ""
    else:
      for state in BRANCH_STATE_LIST:
        if state["state"] == choice:
          is_deleted = state["deleted"]

      update_branch_state(_actual_branch, choice, is_deleted)
      if is_deleted:
        next_step = STEP_CHOOSE_LIST_GENERAL
      else:
        next_step = STEP_CHOOSE_LIST_ACTIONS

      go_step(next_step)


def go_step_set_state_name():
  global _actual_branch

  state = ask_text("Enter the state name:", STATE_REGEX)
  is_deleted = False

  update_branch_state(_actual_branch, state, is_deleted)

  if is_deleted:
    next_step = STEP_CHOOSE_LIST_GENERAL
  else:
    next_step = STEP_CHOOSE_LIST_ACTIONS

  go_step(next_step)









# ---------------------
# Steps dependencies
# ---------------------

def do_pr(in_branch):
  git_push_branch(in_branch)

  repo = _actual_repo_details["repo_name"]
  head = in_branch
  base = _actual_repo_details["dev_branch"]
  title = "Merging " + head + " into " + base
  description = "PR from Clement's script"

  pr = github_create_pull_request(repo, head, base, title, description)
  pr_number = pr.number
  git_pr_link = "https://github.com/qopius/" + _actual_repo_details["repo_name"] + "/pull/" + str(pr_number)

  # Get the slack_user
  slack_user = SLACK_DEFAULT_CHANNEL
  for channel in SLACK_CHANNELS:
    if channel["repo_type"] == _actual_repo_details["repo_type"]:
      slack_user = channel["channel"]

  # Get userID
  userID = slack_display_name_to_id(slack_user)
  slack_channel_id = "@" + userID

  message = "Bot| Please merge " + in_branch + " on " + _actual_repo_details["dev_branch"] + "\n" + git_pr_link
  slack_send_message(slack_channel_id, message)


def delete_branch(in_branch):
  global _actual_repo_branch_list, _actual_branch
  dev_branch = _actual_repo_details["dev_branch"]

  git_go_branch(dev_branch)
  git_delete_branch(in_branch)
  git_pull()

  key = -1
  i = 0
  for branch in _actual_repo_branch_list:
    if branch["branch_name"] == in_branch:
      key = i
    i += 1
  del _actual_repo_branch_list[key]

  _actual_branch = dev_branch
  set_branch_list()


def create_branch(in_branch):

  dev_branch = _actual_repo_details["dev_branch"]
  git_go_branch(dev_branch)

  git_create_branch(in_branch)


def send_commits_to_card():
  res = {
    "is_error": False,
    "data": {}
    }

  # Get notionID
  notionID = None

  is_branch_in_repo_branches_res = is_branch_in_repo_branches(_actual_branch)
  if not is_branch_in_repo_branches_res["is_branch"]:
    res["is_error"] = True
    res["data"]["message"] = "Can't find branch"
    return res

  branch_details = is_branch_in_repo_branches_res["branch"]
  params = []
  if "params" in branch_details:
    params = branch_details["params"]
    for param in params:
      if param["key"] == "notionID":
        notionID = param["value"]

  if notionID == None:
    res["is_error"] = True
    res["data"]["message"] = "Can't find notionID"
    return res

  # Get card's commits
  repo_name = _actual_repo_details["repo_name"]
  branch = _actual_branch
  search = "(N: {} )".format(notionID)
  number = 50

  commits = git_get_lasts_commits(branch, number=number)

  commits_of_cards = []

  for commit in commits:
    if search in commit["message"]:
      commits_of_cards.append(commit)


  # Create text
    # Remove last writes of commits on Notion
  notion_remove_commit_report(notionID)

    # Add header to Notion
  full_txt = ""
  txt = ""
  txt += "Commits of {} from branch {}".format(MY_NAME, branch)
  block_type = "SUB_HEADER"
  notion_add_block(notionID, txt, block_type)
  full_txt += txt + "\n"
  
  for commit in commits_of_cards:
    txt = ""
    short_commit_id = commit["id"][0:8]
    commit_url = "{}{}/commit/{}".format(GITHUB_BASE_URL, repo_name, short_commit_id)
    txt_commit_id = notion_create_link(short_commit_id, commit_url, "Github")
    txt_commit_id = NOTION_BOLD.format(txt_commit_id)
    txt_commit_message = commit["message"].replace(search, "")
    txt += txt_commit_id
    txt += " - "
    txt += commit["time"]
    txt += " - "
    txt += txt_commit_message

    # Add commits to Notion
    block_type = "BULLETED_LIST"
    notion_add_block(notionID, txt, block_type)
    full_txt += txt + "\n"

  txt = ""
  block_type = "TEXT"
  notion_add_block(notionID, txt, block_type)
  
  notion_link = notion_get_card_url(notionID)
  res["data"]["notion_link"] = notion_link
  return res


def notion_remove_commit_report(cardID):
  page = notion_get_card(cardID)
  search_start_header = "Commits of {} from branch ".format(MY_NAME)
  search_start_commit = "**["
  header_found = False

  # Remove header and commits after it
  for child in page.children:
    this_type = type(child)
    this_title = child.title
    if header_found:
      if this_type == BulletedListBlock and this_title.startswith(search_start_commit):
        notion_remove_block(child)
      else:
        header_found = False
    if this_type == SubheaderBlock and this_title.startswith(search_start_header):
      header_found = True
      notion_remove_block(child)


def create_commit_message(commit_descr, params):
  commit_message = ""

  value_type = get_value_of_param("type", params)
  if value_type != False:
    emoji = None
    for type_emoji in TYPES_EMOJIS:
      if value_type == type_emoji["id"]:
        emoji = type_emoji["emoji"]
    if emoji:
      commit_message += emoji + " "

  value_scope = get_value_of_param("scope", params)
  if value_scope != False:
    commit_message += "(" + value_scope + ") "

  commit_message += commit_descr

  value_notionID = get_value_of_param("notionID", params)
  if value_notionID != False:
    commit_message += " (N: " + value_notionID + " )"

  commit_message = commit_message.replace('"', '')
  commit_message = '"' + commit_message + '"'

  return commit_message


def update_branch_state(branch_name, state, is_deleted, params=None):
  global _actual_repo_branch_list

  found_branch = False
  for branch in _actual_repo_branch_list:
    if branch["branch_name"] == branch_name:
      found_branch = True
      branch["state"] = state
      branch["is_deleted"] = is_deleted

      if params != None:
        branch["params"] = params

  if not found_branch:
    new_branch = {
      "branch_name": branch_name,
      "state": state,
      "is_deleted": is_deleted,
      "params": []
      }
    if params != None:
      new_branch["params"] = params
    _actual_repo_branch_list.append(new_branch)

  set_branch_list()









# ---------------------
# File
# ---------------------

def get_branch_list():
  global _branch_list
  f=open(BRANCH_FILE, "r")
  text = f.read()
  f.close()

  _branch_list = txt_to_var(text)


def txt_to_var(text):
  all_branches = []
  actual_repo = None
  first_repo = True
  branches_temp = []
  contents_lines = text.split(RETURN_LINE)

  for line in contents_lines :
    new_repo = False
    for repo in REPO_LIST :
      text_name = repo["text_name"]
      if line == text_name + REPO_DELIMITER :
        if not first_repo :
          all_branches.append( { "repo": actual_repo, "branches": branches_temp } )
          branches_temp = []
        actual_repo = text_name
        new_repo = True
        first_repo = False

    if not new_repo :
      if line != "" :
        line_parts = line.split(TEXT_DELIMITER)
        branch_data = line_parts[-1]
        params_parts = branch_data.split(PARAM_DELIMITER)
        branch_name = params_parts[0]

        # Take params
        params = []
        i = 0
        for params_part in params_parts:
          if i != 0:
            key_value_parts = params_part.split(VALUE_DELIMITER)
            param_item = {
              "key": key_value_parts[0],
              "value": key_value_parts[1]
              }
            params.append(param_item)
          i += 1

        state = None
        is_deleted = False

        if len(line_parts) > 3 :
          error("To many parts in : " + line)
        elif len(line_parts) == 3 :
          del_text = line_parts[1]
          if del_text != IS_DELETED_TEXT :
            error("Delete text is not ok it's " + del_text + " it should be " + IS_DELETED_TEXT + " in line " + line)
          is_deleted = True
          state = line_parts[0]
        elif len(line_parts) == 2 :
          state = line_parts[0]

        branches_temp.append({ "branch_name": branch_name, "state": state, "is_deleted": is_deleted, "params": params })

  all_branches.append( { "repo": actual_repo, "branches": branches_temp } )

  return all_branches


def set_branch_list():
  text = var_to_txt(_branch_list)

  f = open(BRANCH_FILE, "w")
  f.write(text)
  f.close()

  return None


def var_to_txt(branch_list):
  text = ""
  first_repo = True

  for repos in branch_list :
    if not first_repo :
      text += RETURN_LINE + RETURN_LINE
    text += repos["repo"] + REPO_DELIMITER + RETURN_LINE
    first_repo = False

    for branch in repos["branches"] :
      line = ""
      state = branch["state"]
      if state == None :
        state = ""
      line += state + TEXT_DELIMITER
      if branch["is_deleted"] :
        line += IS_DELETED_TEXT + TEXT_DELIMITER
      line += branch["branch_name"]
      if "params" in branch:
        for param in branch["params"]:
          line += PARAM_DELIMITER + param["key"] + VALUE_DELIMITER + param["value"]

      text += line + RETURN_LINE

  return text









# ---------------------
# Git
# ---------------------

def get_repo_info():
  global _actual_repo, _actual_repo_details, _actual_git_branch

  repo = Repo('./', search_parent_directories=True)
  branch_name = repo.active_branch.name
  working_dir = repo.working_dir
  folder_name = os.path.basename(working_dir)
  folder_name_lower = folder_name.lower()

  origin_url = repo.remotes.origin.url
  # Take apiv3 from git@github.com:qopius/apiv3.git
  origin_name = origin_url.split("/")[1].split(".git")[0]

  local_actual_repo = None
  local_actual_repo_details = None

  for repo in REPO_LIST:
    if repo["repo_name"] == origin_name:
      if repo["parent_folder_contains"] == None:
        local_actual_repo = repo["text_name"]
        local_actual_repo_details = repo
      else:
        if repo["parent_folder_contains"] in folder_name_lower:
          local_actual_repo = repo["text_name"]
          local_actual_repo_details = repo


  _actual_repo = local_actual_repo
  _actual_repo_details = local_actual_repo_details
  _actual_git_branch = branch_name

  return None


def git_get_lasts_commits(branch, number = 50):
  repo = Repo('./', search_parent_directories=True)
  commits = list(repo.iter_commits(branch, max_count=number))
  commits_formated = [
    {
    'id': c.hexsha,
    'message': c.message,
    'time': time.strftime("%d/%m/%Y %H:%M:%S GMT", time.localtime(c.committed_date)),
    'timestamp': c.committed_date,
    'author_name': str(c.author),
    'author_email': c.author.email
    }
    for c in commits]

  return commits_formated

  
def get_repo_branches():
  global _actual_repo_branch_list
  repo_branches = []

  for repo in _branch_list:
    if repo["repo"] == _actual_repo:
      repo_branches = repo["branches"]

  _actual_repo_branch_list = repo_branches

  return None


def git_go_branch(branch):
  command = "git checkout " + branch
  launch_command(command)


def git_create_branch(branch):
  command = "git checkout -b " + branch
  launch_command(command)


def git_commit(commit_message):
  command = "git commit -m " + commit_message
  res = launch_command(command)
  return res


def git_push_branch(branch):
  command = "git push origin " + branch
  launch_command(command)

def git_delete_branch(branch):
  command = "git branch -D " + branch
  launch_command(command)


def git_pull():
  command = "git pull"
  launch_command(command)









# ---------------------
# Github
# ---------------------

def github_create_pull_request(repo, head, base, title, description):
  global GITHUB_OBJ_ORG

  if not title:
    title = "Auto-generated pull request."
  if not description:
    description = "Auto-generated pull request."

  r = GITHUB_OBJ_ORG.get_repo(repo)
  p = r.create_pull(head=head, base=base, title=title, body=description)

  return p









# ---------------------
# Slack
# ---------------------

def slack_send_message(channel, message):
  SLACK_OBJ_SLACK.chat_postMessage(
      channel=channel,
      text=message,
      as_user=True
      )


def slack_display_name_to_id(user_display_name):
  users_list = SLACK_OBJ_SLACK.users_list()

  userID = None
  for user in users_list["members"]:
    if user["profile"]["display_name"] == user_display_name:
      userID = user["id"]

  return userID









# ---------------------
# Notion
# ---------------------

def notion_add_block(cardID, text, block_type):
  page = notion_get_card(cardID)

  block_class = None
  if block_type == "TEXT":
    block_class = TextBlock
  elif block_type == "BULLETED_LIST":
    block_class = BulletedListBlock
  elif block_type == "HEADER":
    block_class = HeaderBlock
  elif block_type == "SUB_HEADER":
    block_class = SubheaderBlock
  elif block_type == "SUBSUB_HEADER":
    block_class = SubsubheaderBlock

  if block_class != None:
    newchild = page.children.add_new(block_class, title=text)


def notion_get_card(cardID):
  url = notion_get_card_url(cardID)
  page = NOTION_OBJ.get_block(url)
  return page


def notion_get_card_url(cardID):
  url = NOTION_BASE_URL + cardID
  return url


def notion_create_link(txt, url, hover_txt):
  link_txt = NOTION_LINK.format(txt, url, hover_txt)
  return link_txt


def notion_remove_block(block):
  block.remove()









# ---------------------
# User Interactions
# ---------------------

def choose_from_list(question_list, title):
  questions = [
  inquirer.List('response',
              message = title,
              choices = question_list,
              ),
  ]
  answers = inquirer.prompt(questions)
  choice =  answers["response"]
  return choice

def ask_text(title, regex):
  questions = [
  inquirer.Text('response', message=title,
                validate=lambda _, x: re.match(regex, x),
                )
              ]
  answers = inquirer.prompt(questions)
  value = answers["response"]
  return value


def ask_confirm(title):
  questions = [
      inquirer.Confirm('response',
                    message= title),
  ]

  answers = inquirer.prompt(questions)
  value = answers["response"]
  return value


def ask_press_key(title):
  txt = "[{}] {}: ".format(colored("?", "yellow"), title)
  input(txt)









# ---------------------
# Elementary functions
# ---------------------

def go_step(step):
  global _actual_step, _actual_branch
  _actual_step = step
  switcher = {
    STEP_CHOOSE_LIST_GENERAL: go_step_choose_list_general,
    STEP_CHOOSE_LIST_BRANCH: go_step_choose_list_branch,
    STEP_SET_BRANCH_NAME: go_step_set_branch_name,
    STEP_SHOW_SUMMARY: go_step_show_summary,
    STEP_CHOOSE_LIST_ACTIONS: go_step_choose_list_actions,
    STEP_COMMIT: go_step_commit,
    STEP_ADD_COMMITS_TO_CARD: go_step_add_commits_to_card,
    STEP_PUSH_BRANCH: go_step_push_branch,
    STEP_PR_BRANCH: go_step_pr_branch,
    STEP_DELETE_BRANCH: go_step_delete_branch,
    STEP_CHOOSE_LIST_STATE: go_step_choose_list_state,
    STEP_SET_STATE_NAME: go_step_set_state_name,
      }
  func = switcher.get(step)

  write_before_step()

  # Execute the function
  print(func())


def write_before_step():
  global _actual_branch
  get_repo_info()

  # Display branch details
  state = ""
  is_deleted = False
  res_is_branch = is_branch_in_repo_branches(_actual_branch)
  if res_is_branch["is_branch"]:
    state = res_is_branch["branch"]["state"]
    is_deleted = res_is_branch["branch"]["is_deleted"]

  text = ""
  color = "green"
  if _actual_branch != _actual_git_branch:
    text += "GIT NOT ALIGN - "
    color = "red"
  text += _actual_branch
  if state != "":
    text += " - " + state
  if is_deleted :
    text += " - Deleted"
  text += "\n"

  clear()
  print(colored(text, color))


def is_branch_in_repo_branches(branch_name):
  is_branch = False
  branch_item = None

  for branch in _actual_repo_branch_list:
    if branch["branch_name"] == branch_name:
      is_branch = True
      branch_item = branch

  return {"is_branch": is_branch, "branch": branch_item}


def get_value_of_param(searched_key, params):
  value = False
  for param in params:
    if param["key"] == searched_key:
      value = param["value"]
  return value


def launch_command(command):
  return os.popen(command).read()


def clear():
  os.system('clear')


def error(text):
  print(text)
  exit()









# ---------------------
# Main
# ---------------------

def main():
  global _actual_git_branch, _actual_branch

  get_repo_info()
  _actual_branch = _actual_git_branch
  get_branch_list()
  get_repo_branches()

  res_is_branch = is_branch_in_repo_branches(_actual_branch)
  if res_is_branch["is_branch"]:
    step = STEP_CHOOSE_LIST_GENERAL
  else :
    step = STEP_CHOOSE_LIST_BRANCH
  go_step(step)

  set_branch_list()


# Start script
main()


