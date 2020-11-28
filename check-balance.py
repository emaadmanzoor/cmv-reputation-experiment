import argparse
import numpy as np
import sys
import time

from params import *
from scipy.stats import ttest_ind, ttest_ind_from_stats

def eprint(*args, **kwargs):
  print(*args, file=sys.stderr, **kwargs)

def print_balance(desc, treatment_mean, treatment_std,
                  control_mean, control_std, tstat, pvalue):
  eprint("\t", desc, end="")
  eprint("\tT =", "{:.3f}".format(treatment_mean), "+/-",
                  "{:.3f}".format(treatment_std), end="")
  eprint("\tC =", "{:.3f}".format(control_mean), "+/-",
                  "{:.3f}".format(control_std), end="")
  eprint("\tt =", "{:.3f}".format(tstat), end=", ")
  eprint("p =", "{:.3f}".format(pvalue))

if __name__ == "__main__":
  ap = argparse.ArgumentParser()
  ap.add_argument("--filename", required=True)
  args = ap.parse_args()
  
  user_flair_group_filename = args.filename
  timestamp = "-".join(user_flair_group_filename.split("-")[1:])
  balance_filename = "balance-" + timestamp
  user_redditstats_filename = "user_reddit_stats-" + timestamp
  user_cmvstats_filename = "user_cmv_stats-" + timestamp
  
  # read user Reddit statistics file
  strata = []
  treatments = []
  comment_karmas = []
  link_karmas = []
  verifieds = []
  mods = []
  golds = []
  ages = []
  non_suspended_users = []
  with open(user_redditstats_filename, "r") as f:
    for line in f:
      user, treatment, stratum, comment_karma, link_karma, created_utc,\
          verified, mod, gold = line.strip().split("\t")

      strata.append(int(stratum))
      treatments.append(int(treatment))
      comment_karmas.append(int(comment_karma))
      link_karmas.append(int(link_karma))
      verifieds.append(int(verified == "True"))
      mods.append(int(mod == "True"))
      golds.append(int(gold == "True"))
      non_suspended_users.append(user)

      created_utc = float(created_utc)
      age = time.time() - created_utc
      age = age / 86400 # account age in days
      ages.append(age)

  strata = np.array(strata)
  treatments = np.array(treatments)
  comment_karmas = np.array(comment_karmas)
  link_karmas = np.array(link_karmas)
  verifieds = np.array(verifieds)
  mods = np.array(mods)
  golds = np.array(golds)
  ages = np.array(ages)
  non_suspended_users = set(non_suspended_users)

  num_treated = np.sum(treatments)
  num_control = len(treatments) - num_treated
  eprint("Balance check filename:", balance_filename)
  eprint("\tNumber of users:", len(treatments))
  eprint("\tStratum statistics:")
  for i in range(MAX_STRATUM+1):
    eprint("\t\t", i, "N =", sum([1 for s in strata if s == i]),
           "\tT =", "{:.2f}".format(np.mean(treatments[strata==i])))


  mean_comment_karma_t = np.mean(comment_karmas[treatments==1])
  mean_link_karma_t = np.mean(link_karmas[treatments==1])
  mean_verified_t = np.mean(verifieds[treatments==1])
  mean_mod_t = np.mean(mods[treatments==1])
  mean_gold_t = np.mean(golds[treatments==1])
  mean_age_t = np.mean(ages[treatments==1])
  
  std_comment_karma_t = np.std(comment_karmas[treatments==1])
  std_link_karma_t = np.std(link_karmas[treatments==1])
  std_verified_t = np.std(verifieds[treatments==1])
  std_mod_t = np.std(mods[treatments==1])
  std_gold_t = np.std(golds[treatments==1])
  std_age_t = np.std(ages[treatments==1])
  
  mean_comment_karma_c = np.mean(comment_karmas[treatments==0])
  mean_link_karma_c = np.mean(link_karmas[treatments==0])
  mean_verified_c = np.mean(verifieds[treatments==0])
  mean_mod_c = np.mean(mods[treatments==0])
  mean_gold_c = np.mean(golds[treatments==0])
  mean_age_c = np.mean(ages[treatments==0])
  
  std_comment_karma_c = np.std(comment_karmas[treatments==0])
  std_link_karma_c = np.std(link_karmas[treatments==0])
  std_verified_c = np.std(verifieds[treatments==0])
  std_mod_c = np.std(mods[treatments==0])
  std_gold_c = np.std(golds[treatments==0])
  std_age_c = np.std(ages[treatments==0])
  
  tstat_comment, pvalue_comment = ttest_ind(comment_karmas[treatments==1],
                                            comment_karmas[treatments==0])
  tstat_link, pvalue_link = ttest_ind(link_karmas[treatments==1],
                                      link_karmas[treatments==0])
  tstat_ver, pvalue_ver = ttest_ind(verifieds[treatments==1],
                                    verifieds[treatments==0])
  tstat_mod, pvalue_mod = ttest_ind(mods[treatments==1],
                                    mods[treatments==0])
  tstat_gold, pvalue_gold = ttest_ind(golds[treatments==1],
                                      golds[treatments==0])
  tstat_age, pvalue_age = ttest_ind(ages[treatments==1],
                                    ages[treatments==0])

  print_balance("Comm", mean_comment_karma_t, std_comment_karma_t,
                mean_comment_karma_c, std_comment_karma_c,
                tstat_comment, pvalue_comment)
  print_balance("Link", mean_link_karma_t, std_link_karma_t,
                mean_link_karma_c, std_link_karma_c,
                tstat_link, pvalue_link)
  print_balance("Ver", mean_verified_t, std_verified_t,
                mean_verified_c, std_verified_c,
                tstat_ver, pvalue_ver)
  print_balance("Mod", mean_mod_t, std_mod_t,
                mean_mod_c, std_mod_c,
                tstat_mod, pvalue_mod)
  print_balance("Gold", mean_gold_t, std_gold_t,
                mean_gold_c, std_gold_c,
                tstat_gold, pvalue_gold)
  print_balance("Age", mean_age_t, std_age_t,
                mean_age_c, std_age_c,
                tstat_age, pvalue_age)

  # read user/flair/treatment assignment file
  deltas = []
  strata = []
  treatments = []
  user_treatment_map = {}
  user_stratum_map = {}
  with open(user_flair_group_filename, "r") as f:
    for line in f:
      user, flair, delta, stratum, css, treatment = line.strip().split("\t")
      if user not in non_suspended_users:
        continue # ignore suspended users
      deltas.append(int(delta))
      strata.append(int(stratum))
      treatments.append(int(treatment))
      user_treatment_map[user] = int(treatment)
      user_stratum_map[user] = int(stratum)
  deltas = np.array(deltas)
  strata = np.array(strata)
  treatments = np.array(treatments)

  num_treated = np.sum(treatments)
  num_control = len(treatments) - num_treated
  
  mean_deltas_t = np.mean(deltas[treatments==1])
  std_deltas_t = np.std(deltas[treatments==1])
  mean_deltas_c = np.mean(deltas[treatments==0])
  std_deltas_c = np.std(deltas[treatments==0])
  tstat, pvalue = ttest_ind(deltas[treatments==1], deltas[treatments==0])

  print_balance("Deltas", mean_deltas_t, std_deltas_t,
                mean_deltas_c, std_deltas_c, tstat, pvalue)
