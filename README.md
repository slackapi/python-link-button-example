## [Out and back again](https://medium.com/slack-developer-blog/out-and-back-again-6b2f3c84f484)

#### Using link buttons and deep linking for a seamless flow between your service and Slack

![Slack message with link button](https://cdn-images-1.medium.com/max/1600/0*kA5KlFd0uNWcWMMz.)

Slack apps allow teams to get quick tasks done, alongside their other work, without having to context switch into another product or browser window. But not every part of your service needs to be brought into Slack. “Deep work” that takes more than a few minutes — like setting up a project management board, building a wireframe, or creating a metrics dashboard — can sometimes be a better fit for your external service or web app.

Now with [deep linking](https://api.slack.com/docs/deep-linking) and [link buttons](https://api.slack.com/docs/message-attachments#link_buttons) — a new type of button that enables you to link out to an external webpage — you can build a user-friendly flow to guide people from Slack to your external service, then direct them back into a particular message in Slack to continue working. In this tutorial, we’ll show you how to do it.

##### About link buttons

Link buttons are Slack message attachments that look like interactive message buttons, but rather than sending an action event to your app, they link out to an external webpage of your choice. Compared to the previous solution — static hyperlinked text — link buttons UI can promote user engagement. Apps that adopt link buttons in favor of hyperlinked text have seen click-throughs increase by as much as 85%.

Aside from promoting user engagement, link buttons offer a workaround for developers building apps behind a firewall. Features like message buttons, message menus and dialogs can help increase app engagement, but there’s a limitation: you need to add additional webhooks to your application. Because these features require a request URL, some developers — for instance, those running an app on their company’s internal network or a service behind a firewall — were previously blocked from building interactive Slack apps. For developers who have this limitation, link buttons offer an alternative: you can build an interactive app without the overhead of adding additional endpoints.

##### Using link buttons

When someone clicks a link button, they’re taken to your webpage to complete a task. Once that work has been completed, you can use deep linking to bring them back to where they left off the conversation in Slack.
You can break it down into a few steps. We’ll go through each in detail.
1. Have your app post a message with a link button, leading to your external application or website
2. The user loads the website and completes a workflow
3. The user is directed to a “complete” page and the original Slack message is updated. A message permalink is fetched and shown to the user
4. The user clicks back into Slack and resumes the conversation

![Example workflow using link buttons and message permalinks](https://cdn-images-1.medium.com/max/1600/1*FD388dGN2C7jS8cj07JVog.gif)

##### 1. Post a message with a link button leading to your external app

You’ll need to keep a map of the message IDs so you can correlate the message your app posts in Slack with the task you’re giving the user. The simplest way to do this is with a dictionary that contains a reference for each channel and message timestamp:

```
# A dictionary to store `task_id` to message mappings
TASK_IDS = {}
```

Next, have your app post a message with a link button which will take the user out to the pending task. The button should be associated with a unique task, like a ticket number or another unique ID. For this demo, we’ll use `LB-2375`.

```
# Our task ID. This could be a ticket number or any other unique ID
task_id = 'LB-2375'
```

Adding a link button to a message is as simple as adding an attachment containing the URL you went to link to and the text you want on the button.

```
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
```

When the message is posted, Slack’s Web API will return some data about the message (see `res` below) such as the channel, timestamp and message content. We’re going to store the channel and timestamp to the map under the task ID.

```
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
```

##### 2. Guide the user through the task

Now the message is sent to the user, so they can click the link button to be guided to your external app. When they land on your page, you’ll need to grab the task ID from the URL or params, show them the task to be completed, and guide them to a completed state.
For this very simplified demo, we’re going to show the user a form with one action. When the user submits this form, we will direct them to the `/completed` page.

```
# This is where our link button will link to, showing the user a
# task to complete before redirecting them to the `/complete` page
@app.route("/workflow/<task_id>", methods=['GET'])
def test(task_id):

    task_form = """<form method="POST" action="/complete/{}">
                    <input type="submit" value="Do The Thing" />
                </form>""".format(task_id)

    return make_response(task_form, 200)
```

##### 3. Update the message and bring them back to Slack

When the user loads the `/completed` page, you’ll need to update the Slack message containing the link button to show that the task has been completed, and present the user with a link back to their Slack conversation.
To update the Slack message containing the button, reference the channel and timestamp we saved in the map earlier, and call `chat.update`.

```
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
```

Once the message has been updated, fetch the permalink for it…

```
# Get the message permalink to redirect the user back to Slack
res = slack.api_call(
    "chat.getPermalink",
    channel=TASK_IDS[task_id]["channel"],
    message_ts=TASK_IDS[task_id]["ts"]
)
```

…and show the “Return to Slack” link.

```
# Link the user back to the original message
slack_link = "<a href=\"{}\">Return to Slack</a>".format(res['permalink'])

# Redirect the user back to their Slack conversation
return make_response("Task Complete!<br/>" + slack_link, 200)
```

That’s it! 🎉

This simple flow using link buttons and deep linking enables your app’s users to complete “deep work” in your external service, then seamlessly return to where they started in Slack.

To run this example, clone the repository or copy the code from `example.py`, and run:

```
export SLACK_API_TOKEN=”<YOUR SLACK BOT TOKEN>” 
python example.py
```

Need help? Find us in the [Bot Developer Hangout](http://dev4slack.xoxco.com/) [#slack-api channel](https://dev4slack.slack.com/messages/slack-api/), reach out on [Twitter](https://twitter.com/slackapi), or [create an issue](https://github.com/slackapi/python-link-button-example/issues) on GitHub.

