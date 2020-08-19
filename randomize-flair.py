#!/usr/bin/env python

import argparse
import praw
import random
import sys
import time

from params import *

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

def get_user_groups(filename):
    user_group_dict = {}
    with open(filename, "r") as f:
        for line in f:
            timestamp, username, group = line.strip().split(" ")
            user_group_dict[username] = group
    return user_group_dict

def set_user_groups(users, filename):
    if not isinstance(users, list):
        users = [users]
    eprint("Assigning groups for", str(len(users)), "user(s)")

    groups = random.choices([0, 1], k=len(users)) 
    user_group_dict = {user: group for user, group in zip(users, groups)}

    timestamp = int(time.time()) 
    with open(filename, "a") as f:
        for user, group zip(users, groups):
            f.write(str(timestamp) + " " + user + " " + str(group) + "\n")

    fraction = "{:.2f}".format(sum(groups)/len(groups))
    eprint("Groups assigned at " + str(timestamp) + " treated=" + fraction)

    return user_group_dict

if __name__ == "__main__":
    reddit = praw.Reddit(client_id=CLIENT_ID, client_secret=CLIENT_SECRET,
                         password=PASSWORD, username=USERNAME)
    subreddit = reddit.subreddit(SUBREDDIT)

    # Get users assigned to treatment/control groups from disk
    user_group_dict = get_user_groups(USER_GROUPS_FILENAME)

    # Get users with flair (deltas > 0) from subreddit
    users_with_flair = {}
    for flair in subreddit.flair(limit=None):
        username = flair["user"].name
        flair_text = flair["flair_text"]
        users_with_flair[username] = flair_text

    # Assign previously-unassigned users to treatment or control
    assigned_users = set(user_group_dict.keys())
    flaired_users = set(users_with_flair.keys())
    unassigned_users = flaired_users - assigned_users
    new_user_group_dict = set_user_groups(unassigned_users, USER_GROUPS_FILENAME)

    # Update flair template of all users:
    # - hide flair for users in treatment group
    # - no change for users in control group
    merged_user_group_dict = {**user_group_dict, **new_users_with_flair}
    for user, group in merged_user_group_dict:
        if group == 0:
            continue

        flair_template = FLAIR_HIDING_TEMPLATE_ID
        flair_text = users_with_flair[user]
        subreddit.flair.set(redditor=user, flair_text=flair_text,
                            flair_template_id=flair_templaete_id)

    eprint("Reddit API limits:", reddit.auth.limits)
