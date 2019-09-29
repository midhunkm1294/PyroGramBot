"""Update UserBot code
Syntax: .update"""

from pyrogram import Client, Filters

import git
import os

from pyrobot import MAX_MESSAGE_LENGTH, COMMAND_HAND_LER, HEROKU_API_KEY


# -- Constants -- #
IS_SELECTED_DIFFERENT_BRANCH = (
    "looks like a custom branch {branch_name} "
    "is being used:\n"
    "in this case, Updater is unable to identify the branch to be updated."
    "please check out to an official branch, and re-start the updater."
)
OFFICIAL_UPSTREAM_REPO = "https://github.com/SpEcHiDe/PyroGramUserBot"
BOT_IS_UP_TO_DATE = "the userbot is up-to-date."
NEW_BOT_UP_DATE_FOUND = (
    "new update found for {branch_name}\n"
    "chagelog: {changelog}\n"
    "updating ..."
)
NEW_UP_DATE_FOUND = (
    "new update found for {branch_name}\n"
    "updating ..."
)
REPO_REMOTE_NAME = "tmp_upstream_remote"
IFFUCI_ACTIVE_BRANCH_NAME = "master"
DIFF_MARKER = "HEAD..upstream/{branch_name}"
NO_HEROKU_APP_CFGD = "no heroku application found, but a key given? 😕 "
HEROKU_GIT_REF_SPEC = "HEAD:refs/heads/master"
RESTARTING_APP = "re-starting heroku application"
# -- Constants End -- #


@Client.on_message(Filters.command("update", COMMAND_HAND_LER)  & Filters.me)
async def updater(client, message):
    try:
        repo = git.Repo()
    except git.exc.InvalidGitRepositoryError as e:
        print(e)
        repo = Repo.init()
        origin = repo.create_remote(REPO_REMOTE_NAME, OFFICIAL_UPSTREAM_REPO)
        origin.fetch()
        repo.create_head(IFFUCI_ACTIVE_BRANCH_NAME, origin.refs.master)
        repo.heads.master.checkout(True)

    active_branch_name = repo.active_branch.name
    if active_branch_name != IFFUCI_ACTIVE_BRANCH_NAME:
        await message.edit(IS_SELECTED_DIFFERENT_BRANCH.format(
            branch_name=active_branch_name
        ))
        return False

    try:
        repo.create_remote(REPO_REMOTE_NAME, OFFICIAL_UPSTREAM_REPO)
    except Exception as e:
        print(e)
        pass

    tmp_upstream_remote = repo.remote(REPO_REMOTE_NAME)
    tmp_upstream_remote.fetch(active_branch_name)

    changelog = generate_change_log(repo, DIFF_MARKER)

    if not changelog:
        await message.edit(BOT_IS_UP_TO_DATE)
        return False

    message_one = NEW_BOT_UP_DATE_FOUND.format(
        branch_name=active_branch_name,
        changelog=changelog
    )
    message_two = NEW_UP_DATE_FOUND.format(
        branch_name=active_branch_name
    )

    if len(message_one) > MAX_MESSAGE_LENGTH:
        with open("change.log", "w+", encoding="utf8") as out_file:
            out_file.write(str(message_one))
        await client.send_document(
            chat_id=message.chat.id,
            document="change.log",
            caption=message_two,
            disable_notification=True,
            reply_to_message_id=message.message_id
        )
        os.remove("change.log")
    else:
        await message.reply(message_one)

    tmp_upstream_remote.fetch(active_branch_name)
    repo.git.reset("--hard", "FETCH_HEAD")

    if HEROKU_API_KEY is not None:
        import heroku3
        heroku = heroku3.from_key(HEROKU_API_KEY)
        heroku_applications = heroku.apps()
        if len(heroku_applications) >= 1:
            # assuming there will be only one heroku application
            # created per account 🙃
            # possibly, ignore premium Heroku users
            heroku_app = heroku_applications[0]
            heroku_git_url = heroku_app.git_url.replace(
                "https://",
                "https://api:" + key + "@"
            )
            if "heroku" in repo.remotes:
                remote = repo.remote("heroku")
                remote.set_url(heroku_git_url)
            else:
                remote = repo.create_remote("heroku", heroku_git_url)
            remote.push(refspec=HEROKU_GIT_REF_SPEC)
        else:
            await message.reply(NO_HEROKU_APP_CFGD)

    await message.edit(RESTARTING_APP)
    await client.restart()


def generate_change_log(git_repo, diff_marker):
    out_put_str = ""
    d_form = "%d/%m/%y"
    for repo_change in git_repo.iter_commits(diff_marker):
        out_put_str += f"•[{repo_change.committed_datetime.strftime(d_form)}]: {repo_change.summary} <{repo_change.author}>\n"
    return out_put_str