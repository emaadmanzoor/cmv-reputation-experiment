#!/usr/bin/env python

import glob
import praw
import sys
import time

from params import *

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

if __name__ == "__main__":
    eprint("Starting flair revert script")
    eprint("WARNING: Modifies CMV!")

    existing_user_flair_text = {}
    existing_user_flair_css_class = {}
    existing_user_delta = {}
    existing_user_stratum = {}
    existing_user_treatment = {}

    # retrieve latest user-group-treatment assignments from disk
    filenames = glob.glob("./" + USER_GROUPS_FILENAME + "*.csv")
    for filename in filenames:
      with open(filename, "r") as f:
        for line in f:
          line = line.strip()

          username, flair_text, delta, stratum, flair_css_class, treated =\
            line.split("\t")

          if treated == 0:
            continue
          if flair_text == "":
            continue
          if delta == 0:
            continue

          if not username in existing_user_flair_text:
            existing_user_flair_text[username] = flair_text
            existing_user_flair_css_class[username] = flair_css_class
            existing_user_delta[username] = int(delta)
            existing_user_stratum[username] = int(stratum)
            existing_user_treatment[username] = int(treated)
          else:
            if int(delta) > existing_user_delta[username]:
              existing_user_flair_text[username] = flair_text
              existing_user_flair_css_class[username] = flair_css_class
              existing_user_delta[username] = int(delta)
              existing_user_stratum[username] = int(stratum)
              existing_user_treatment[username] = int(treated)

    reddit = praw.Reddit(client_id=CLIENT_ID, client_secret=CLIENT_SECRET,
                         password=PASSWORD, username=USERNAME,
                         user_agent=USER_AGENT)
    subreddit = reddit.subreddit(SUBREDDIT)

    t = time.time()
    eprint("\tUpdating user flairs on Reddit...")
    for username in existing_user_treatment.keys():
      if username != "entsnack":
        continue

      treatment = existing_user_treatment[username]
      css_class = existing_user_flair_css_class[username]
      flair_text = existing_user_flair_text[username]

      assert flair_text != ""
      
      eprint("\t\tReverting flair for treated user:", username)
      subreddit.flair.set(redditor=username, text=flair_text,
                          css_class=css_class)

    eprint("\tDone in:", time.time() - t, "s.")
    eprint("Reddit API limits:", reddit.auth.limits)
