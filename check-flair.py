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

if __name__ == "__main__":
    start_time = time.strftime("%Y-%m-%d-%H-%M-%S") 
    filename = USER_GROUPS_FILENAME + "-" + start_time + ".csv"

    eprint("Starting flair check script, time:", start_time)

    existing_user_flair_text = {}
    existing_user_flair_css_class = {}
    existing_user_delta = {}
    existing_user_stratum = {}
    existing_user_treatment = {}
    
    # retrieve latest user-group-treatment assignments from disk
    filenames = glob.glob("./" + USER_GROUPS_FILENAME + "*.csv")
    filenames = sorted(filenames)
    latest_filename = filenames[-1]
    eprint("\tLatest assignment file:", latest_filename)

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
    
    reddit = praw.Reddit(client_id=CLIENT_ID, client_secret=CLIENT_SECRET,
                         password=PASSWORD, username=USERNAME,
                         user_agent=USER_AGENT)
    subreddit = reddit.subreddit(SUBREDDIT)

    eprint("\tGetting user flairs from Reddit...")
    t0 = time.time()

    to_update = []
    for flair in subreddit.flair(limit=None):
        username = flair["user"].name
        if username == "AutoModerator" or\
           username == "DeltaBot" or\
           username == "centrismhurts998":
            continue

        flair_text = str(flair["flair_text"])
        flair_css_class = str(flair["flair_css_class"])

        if username not in existing_user_treatment:
          eprint("Unseen user:", username)
          continue

        treatment = existing_user_treatment[username]
        if treatment == 1:
          if flair_text != "" and flair_text != "None" and flair_text != "0∆":
            print("Treated user with non-empty flair:", username,
                   flair_text)
            to_update.append(username)

    subreddit.flair.update(to_update, text="")

    eprint("\tDone in", time.time() - t0, "s")

    eprint("Reddit API limits:", reddit.auth.limits)
