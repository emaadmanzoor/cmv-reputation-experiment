import argparse
import numpy as np
import pprint
import praw
import sys
import time
import traceback 

from params import *
from tqdm import tqdm

def eprint(*args, **kwargs):
  print(*args, file=sys.stderr, **kwargs)
  sys.stderr.flush()

if __name__ == "__main__":
  ap = argparse.ArgumentParser()
  ap.add_argument("--filename", required=True)
  args = ap.parse_args()
  
  user_flair_group_filename = args.filename
  timestamp = "-".join(user_flair_group_filename.split("-")[1:])
  user_redditstats_filename = "user_reddit_stats-" + timestamp

  # read user/flair/treatment assignment file
  users = []
  deltas = []
  strata = []
  treatments = []
  with open(user_flair_group_filename, "r") as f:
    for line in f:
      user, flair, delta, stratum, css, treatment = line.strip().split("\t")
      users.append(user)
      deltas.append(int(delta))
      strata.append(int(stratum))
      treatments.append(int(treatment))
  deltas = np.array(deltas)
  strata = np.array(strata)
  treatments = np.array(treatments)

  reddit = praw.Reddit(client_id=CLIENT_ID, client_secret=CLIENT_SECRET,
                       password=PASSWORD, username=USERNAME,
                       user_agent=USER_AGENT)

  # username, comment karma, link karma, created_utc, verified, mod
  with open(user_redditstats_filename, "w") as f:
    for idx, user in tqdm(enumerate(users), total=len(users)):
      retry = True
      retry_num = 0
      while retry:
        try:
          time.sleep(0.1)

          redditor = reddit.redditor(user)
          treated = treatments[idx]
          stratum = strata[idx]

          if getattr(redditor, "is_suspended", False):
            retry = False
            continue

          f.write(user + "\t" + str(treated) + "\t" + str(stratum) + "\t" +
                  str(redditor.comment_karma) + "\t" + str(redditor.link_karma) + "\t" +
                  str(redditor.created_utc) + "\t" + str(redditor.has_verified_email) + "\t" + str(redditor.is_mod) + "\t" +
                  str(redditor.is_gold) + "\n")
          f.flush()

          retry = False
         
        except Exception as e:
          eprint("Failure with user:", user, "Retries:", retry_num, "Error:", e) 
          traceback.print_exc()
          retry_num += 1

          if retry_num > 5:
            eprint("Exceeded 5 retries, ignoring user:", user)
            retry = False

          time.sleep(1)
          
  eprint("Reddit API limits:", reddit.auth.limits)
