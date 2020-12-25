#!/usr/bin/env python

import argparse
import glob
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

if __name__ == "__main__":
    start_time = time.strftime("%Y-%m-%d-%H-%M-%S") 
    filename = USER_GROUPS_FILENAME + "-" + start_time + ".csv"

    eprint("Starting randomization script, time:", start_time)

    ap = argparse.ArgumentParser()
    ap.add_argument("--update", required=False, action="store_true")
    args = ap.parse_args()

    existing_user_flair_text = {}
    existing_user_flair_css_class = {}
    existing_user_delta = {}
    existing_user_stratum = {}
    existing_user_treatment = {}
    if args.update:
      # retrieve latest user-group-treatment assignments from disk
      filenames = glob.glob("./" + USER_GROUPS_FILENAME + "*.csv")
      filenames = sorted(filenames)
      latest_filename = filenames[-1]
      eprint("\tRunning in update mode, file:", latest_filename)

      with open(latest_filename, "r") as f:
        for line in f:
          line = line.strip()

          username, flair_text, delta, stratum, flair_css_class, treated =\
            line.split("\t")

          existing_user_flair_text[username] = flair_text
          existing_user_flair_css_class[username] = flair_css_class
          existing_user_delta[username] = int(delta)
          existing_user_stratum[username] = int(stratum)
          existing_user_treatment[username] = int(treated)
    
    num_treated_bin0 = sum([1 for u, t in existing_user_treatment.items()
                            if t==1 and existing_user_stratum[u]==0])
    num_control_bin0 = sum([1 for u, t in existing_user_treatment.items()
                           if t==0 and existing_user_stratum[u]==0])
    num_treated_bin1 = sum([1 for u, t in existing_user_treatment.items()
                            if t==1 and existing_user_stratum[u]==1])
    num_control_bin1 = sum([1 for u, t in existing_user_treatment.items()
                           if t==0 and existing_user_stratum[u]==1])

    # Get users with flair (deltas > 0) from subreddit
    # Usually takes: 60s
    # Run at 2020.11.25-23-01-22: 19051 flaired users
    reddit = praw.Reddit(client_id=CLIENT_ID, client_secret=CLIENT_SECRET,
                         password=PASSWORD, username=USERNAME,
                         user_agent=USER_AGENT)
    subreddit = reddit.subreddit(SUBREDDIT)

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
        if flair_text == "None" or flair_text == '':
             delta = 0
        else:
             delta = int(flair_text[:-1])
        user_delta[username] = delta

        stratum = get_stratum(delta)
        user_stratum[username] = stratum

    eprint("\tDone in", time.time() - t0, "s")

    user_treatment = {}
    if not args.update:
      # first time treatment assignment
      for stratum_idx in range(MAX_STRATUM+1):
          users = [u for u, s in user_stratum.items() if s == stratum_idx]  
          if len(users) == 0:
            continue
          
          # simple random sampling within stratum
          random.shuffle(users)
          treated_users = users[:len(users)//2]
          control_users = users[len(users)//2:]

          for user in treated_users:
              user_treatment[user] = 1
          for user in control_users:
              user_treatment[user] = 0
    else:
      # only update treatment assignment for unseen users
      current_users = user_flair_text.keys()
      existing_users = existing_user_flair_text.keys()
      new_users = current_users - existing_users
      eprint("\tNew users:", len(new_users))

      for username in new_users:
        new_user_delta = user_delta[username]
        new_user_stratum = user_stratum[username]

        if new_user_stratum == 0: # bin 0

          if num_treated_bin0 < num_control_bin0:
            user_treatment[username] = 1 # assign to treatment
            num_treated_bin0 += 1
          elif num_treated_bin0 > num_control_bin0:
            user_treatment[username] = 0 # assign to control
            num_control_bin0 += 1
          else: # num_treated_bin0 = num_control_bin0
            treatment = random.randint(0, 1)
            user_treatment[username] = treatment
            if treatment == 0:
              num_control_bin0 += 1
            else:
              num_treated_bin0 += 1

        elif new_user_stratum > 0: # bin 1
          if new_user_stratum > 1:
            eprint("\tWarning: new user with stratum:", new_user_stratum,
                   username)

          if num_treated_bin1 < num_control_bin1:
            user_treatment[username] = 1 # assign to treatment
            num_treated_bin1 += 1
          elif num_treated_bin1 > num_control_bin1:
            user_treatment[username] = 0 # assign to control
            num_control_bin1 += 1
          else: # num_treated_bin1 = num_control_bin1
            treatment = random.randint(0, 1)
            user_treatment[username] = treatment
            if treatment == 0:
              num_control_bin1 += 1
            else:
              num_treated_bin1 += 1

    # write stratum and treatment status to disk
    if not args.update:
      with open(filename, "w") as f: # create new file
          for username in user_flair_text.keys():
             flair_text = user_flair_text[username]
             flair_css_class = user_flair_css_class[username]
             delta = user_delta[username]
             stratum = user_stratum[username]
             treated = user_treatment[username]

             f.write(username + "\t" + flair_text + "\t" + str(delta) + "\t" +
                     str(stratum) + "\t" + flair_css_class + "\t" + str(treated) + "\n")
    else:
      with open(filename, "w") as f:
          # first write existing users
          for username in existing_user_flair_text.keys():
             treated = existing_user_treatment[username] # existing
             stratum = existing_user_stratum[username] # existing
             flair_text = existing_user_flair_text[username] # existing
             flair_css_class = existing_user_flair_css_class[username] # existing
             delta = existing_user_delta[username] # existing

             f.write(username + "\t" + flair_text + "\t" + str(delta) + "\t" +
                     str(stratum) + "\t" + flair_css_class + "\t" + str(treated) + "\n")

          # then write new users
          for username in user_treatment.keys():
              treated = user_treatment[username] # new
              stratum = user_stratum[username] # new
              flair_text = user_flair_text[username] # new
              flair_css_class = user_flair_css_class[username] # new
              delta = user_delta[username] # new
             
              f.write(username + "\t" + flair_text + "\t" + str(delta) + "\t" +
                      str(stratum) + "\t" + flair_css_class + "\t" + str(treated) + "\n")

    eprint("Reddit API limits:", reddit.auth.limits)

    """TODO: move below to sequential randomization script
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
