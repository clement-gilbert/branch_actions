Purpose:
---

When they are a lot of repo and a lot of branches to manage,
you have to put the git commands with the name of the branch on it,
checkout, commit, push, create pr, delete branch,
it take time, and you have to list the branches you use.

The goal of this script is for each repo to list the branches you work on,
select a branch and then select the action you want to do.

At start you create your branch and put params on the branch (feat or fix, scope, NotionID),
all of this params will be used to create the commits,
after this, the script create the branch and save the params.

On the nexts launch, it detect the branch and load the params,
you can select another branch and the script will git checkout to the branch.


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

Create an env, install the dependencies, run the script:
```
python3 -m virtualenv env
source env/bin/activate

pip3 install inquirer
pip3 install termcolor
pip3 install gitpython
pip3 install PyGithub
pip3 install slackclient
pip3 install notion

 ./branch_action.sh
```

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


