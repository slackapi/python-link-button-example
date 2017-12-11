from flask import Flask, request, make_response, redirect
from slackclient import SlackClient
from random import randint
import os

# Our app's Slack Client
SLACK_BOT_TOKEN = os.environ["SLACK_API_TOKEN"]
slack = SlackClient(SLACK_BOT_TOKEN)

# A dictionary to store `task_id` to message mappings
TASK_IDS = {}

# Our app's webserver
app = Flask(__name__)


# Our task ID. This could be a ticket number or any other unique ID
task_id = 'LB-2375'

# Attachment JSON containing our link button
# For this demo app, The task ID should be the last segment of the URL
attach_json = [
    {
        "fallback": "Upgrade your Slack client to use messages like these.",
        "color": "#CC0000",
        "actions": [
            {
                "type": "button",
                "text": ":red_circle:   Complete Task: " + task_id,
                "url": "https://roach.ngrok.io/workflow/" + task_id,
            }
        ]
    }
]

# Post the message to Slack, storing the result as `res`
res = slack.api_call(
    "chat.postMessage",
    channel="#link-buttons",
    text="Let's get started!",
    attachments=attach_json
)

# Store the message `ts` and `channel`, so we can request the message
# permalink later when the user clicks the link button
TASK_IDS[task_id] = {
    'channel': res['channel'],
    'ts': res['message']['ts']
}


# This is where our link button will link to, showing the user a
# task to complete before redirecting them to the `/complete` page
@app.route("/workflow/<task_id>", methods=['GET'])
def test(task_id):

    task_form = """<form method="POST" action="/complete/{}">
                    <input type="submit" value="Do The Thing" />
                </form>""".format(task_id)

    return make_response(task_form, 200)


@app.route("/complete/<task_id>", methods=['POST'])
def complete(task_id):
    """
    This is where your app's business logic would live.
    Once the task has been complete, the user will be directed to this `/complete`
    page, which shows a link back to their Slack conversation
    """

    # When this page loads, we update the original Slack message to show that
    # the pending task has been completed
    attach_json = [
        {
            "fallback": "Upgrade your Slack client to use messages like these.",
            "color": "#36a64f",
            "text": ":white_check_mark:   *Completed Task: {}*".format(task_id),
            "mrkdwn_in": ["text"]
        }
    ]
    res = slack.api_call(
        "chat.update",
        channel=TASK_IDS[task_id]["channel"],
        ts=TASK_IDS[task_id]["ts"],
        text="Task Complete!",
        attachments=attach_json
    )

    # Get the message permalink to redirect the user back to Slack
    res = slack.api_call(
        "chat.getPermalink",
        channel=TASK_IDS[task_id]["channel"],
        message_ts=TASK_IDS[task_id]["ts"]
    )

    # Link the user back to the original message
    slack_link = "<a href=\"{}\">Return to Slack</a>".format(res['permalink'])

    # Redirect the user back to their Slack conversation
    return make_response("Task Complete!<br/>" + slack_link, 200)


# Start our webserver
app.run(port=3000)
