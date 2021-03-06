#!/usr/bin/env python

import glob
import praw
import sys
import time

from params import *

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

if __name__ == "__main__":
    eprint("Starting flair update script")
    eprint("WARNING: Modifies CMV!")

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


    treated_users = []
    for username in existing_user_treatment.keys():
      treatment = existing_user_treatment[username]
      delta = existing_user_delta[username]
      css_class = existing_user_flair_css_class[username]
      flair_text = existing_user_flair_text[username]

      if delta == 0: # no point treating users with no flair
        continue

      if flair_text == "": # no point treating users with no flair
        continue

      if treatment == 0: # control group user
        continue

      treated_users.append(username)

    eprint("\tUpdating flair for", len(treated_users), "users...")

    t = time.time()
    res = subreddit.flair.update(treated_users, text="")
    for status in res:
      username = status["status"].split(" ")[-1]
      ok = status["ok"]
      if not ok:
        eprint("Error updating flair for:", username)

    eprint("\tDone in:", time.time() - t, "s.")
    eprint("Reddit API limits:", reddit.auth.limits)
