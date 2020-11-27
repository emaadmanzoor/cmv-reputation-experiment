#!/usr/bin/env python

import argparse
import os
import praw
import random
import sys
import time

from params import *

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

def get_user_groups(filename):
    user_group_dict = {}

    if os.path.exists(filename):
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
        for user, group in zip(users, groups):
            f.write(str(timestamp) + " " + user + " " + str(group) + "\n")

    fraction = "{:.2f}".format(sum(groups)/len(groups))
    eprint("Groups assigned at " + str(timestamp) + " treated=" + fraction)

    return user_group_dict

def get_stratum(d):
    if d == 0:
        return 0
    elif d >= 1 and d < 10:
        return 1
    elif d >= 10 and d < 20:
        return 2
    elif d >= 20 and d < 30:
        return 3
    elif d >= 30 and d < 40:
        return 4
    elif d >= 40 and d < 50:
        return 5
    elif d >= 50 and d < 100:
        return 6
    elif d >= 100:
        return 7

if __name__ == "__main__":
    start_time = time.strftime("%Y-%m-%d-%H-%M-%S") 
    filename = USER_GROUPS_FILENAME + "-" + start_time + ".csv"

    eprint("Starting randomization script, time:", start_time)

    reddit = praw.Reddit(client_id=CLIENT_ID, client_secret=CLIENT_SECRET,
                         password=PASSWORD, username=USERNAME,
                         user_agent=USER_AGENT)
    subreddit = reddit.subreddit(SUBREDDIT)

    # Get users assigned to treatment/control groups from disk
    user_group_dict = get_user_groups(USER_GROUPS_FILENAME + "-" +
                                      start_time + ".csv")

    # Get users with flair (deltas > 0) from subreddit
    # Usually takes: 60s
    # Run at 2020.11.25-23-01-22: 19051 flaired users

    eprint("\tGetting user flairs from Reddit...")
    t0 = time.time()

    user_flair_text = {}
    user_flair_css_class = {}
    user_delta = {}
    user_stratum = {}
    for flair in subreddit.flair(limit=None):
        username = flair["user"].name
        if username == "AutoModerator" or\
           username == "DeltaBot" or\
           username == "centrismhurts998":
            continue

        flair_text = str(flair["flair_text"])
        flair_css_class = str(flair["flair_css_class"])
        user_flair_text[username] = flair_text
        user_flair_css_class[username] = flair_css_class

        delta = None
        if flair_text == "None":
             delta = 0
        else:
             delta = int(flair_text[:-1])
        user_delta[username] = delta
        
        stratum = get_stratum(delta)
        user_stratum[username] = stratum

    eprint("\tDone in", time.time() - t0, "s")

    # stratified random sampling
    user_treatment = {}
    for stratum_idx in range(MAX_STRATUM+1):
        users = [u for u, s in user_stratum.items() if s == stratum_idx]  
        
        # simple random sampling within stratum
        random.shuffle(users)
        treated_users = users[:len(users)//2]
        control_users = users[len(users)//2:]

        for user in treated_users:
            user_treatment[user] = 1
        for user in control_users:
            user_treatment[user] = 0

    # write stratum and treatment status to disk
    with open(filename, "w") as f:
        for username in user_flair_text.keys():
           flair_text = user_flair_text[username]
           flair_css_class = user_flair_css_class[username]
           delta = user_delta[username]
           stratum = user_stratum[username]
           treated = user_treatment[username]

           f.write(username + "\t" + flair_text + "\t" + str(delta) + "\t" +
                   str(stratum) + "\t" + flair_css_class + "\t" + str(treated) + "\n")

    eprint("Reddit API limits:", reddit.auth.limits)

    """TODO: move below to sequential randomization script
    # Assign previously-unassigned users to treatment or control
    assigned_users = set(user_group_dict.keys())
    flaired_users = set(user_flair_text.keys())
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

  """
