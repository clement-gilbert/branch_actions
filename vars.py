
# ---------------------
# Config Vars Mains
# ---------------------

BRANCH_FILE = "./Branches"

REPO_LIST = [
  { "text_name": "Api", "repo_name": "apiv3", "repo_type": "Api", "dev_branch": "v3_debug", "parent_folder_contains": None }
  ]

MY_NAME = ""

LOADING_CHECKS = True


# Github
# Generate token: https://docs.cachethq.io/docs/github-oauth-token
GITHUB_TOKEN = ""
# From there: https://github.com/GITHUB_ORGANIZATION/repo
GITHUB_ORGANIZATION = "qopius"


# Slack
# Generate token: https://slack.com/intl/en-fr/help/articles/215770388-Create-and-regenerate-API-tokens
SLACK_TOKEN = ""
# Channel to put the merge message
SLACK_DEFAULT_CHANNEL = "Clement"
# Channel depending of the repo_type
SLACK_CHANNELS = [
  {
    "repo_type": "Api",
    "channel": "kevinse",
  },
  {
    "repo_type": "Front",
    "channel": "Clement",
  }
]


# Notion
# Obtain the token_v2 value by inspecting your browser cookies on a logged-in session on Notion.so
# Firefox: Inspect, then Storage, browse to Cookies
# Firefox: Inspect, then Application, browse to Cookies
NOTION_TOKEN = ""

