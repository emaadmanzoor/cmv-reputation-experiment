#!/usr/bin/env python

import glob
import numpy as np
import pandas as pd
import scipy.stats as stats
import statsmodels.api as sm
import statsmodels.formula.api as smf

from scipy.stats import ttest_ind, ttest_rel, t

comment_df_files = sorted(glob.glob("data/cmv/comment_df_*.parquet"))
comment_df_file = comment_df_files[-1]
print("Most recent comment file:", comment_df_file)

comments_df = pd.read_parquet(comment_df_file)
comments_df = comments_df[comments_df["immediate"]==True] # only root responses

N = len(comments_df[comments_df["stratum"]>0])
success_rate = comments_df[comments_df["stratum"]>0]["successful"].mean()
print("No. of root level responses by flaired users:", N,
      "success rate = {:.3f}%".format(success_rate * 100))

stratum_effects = []
stratum_weight = []
stratum_vars = []
for stratum in range(1, 8):
  print("\tStratum", stratum, end=" ")

  stratum_df = comments_df[comments_df["stratum"]==stratum]
  stratum_g0 = stratum_df[stratum_df["group"]==0]["successful"].values
  stratum_g1 = stratum_df[stratum_df["group"]==1]["successful"].values
  stratum_effects.append(stratum_g1.mean() - stratum_g0.mean())

  n = len(stratum_df)
  stratum_weight.append(n/N)
  
  n0 = len(stratum_g0)
  n1 = len(stratum_g1)
  var1 = np.var(stratum_g1)
  var0 = np.var(stratum_g0)
  stratum_vars.append(var1/n1 + var0/n0)

  t, p = ttest_ind(stratum_g0, stratum_g1, equal_var=False)

  print("success: T", "{:.2f}%".format(stratum_g1.mean()*100),
        "C", "{:.2f}%".format(stratum_g0.mean()*100),
        "n", n,
        "pvalue =", "{:.3f}".format(p))

stratum_effects = np.array(stratum_effects)
stratum_weight = np.array(stratum_weight)

ate = np.sum(stratum_weight * stratum_effects)
blockvar = np.sum(stratum_weight * stratum_weight * stratum_vars)
blockstd = np.sqrt(blockvar)
tstat = ate/blockstd
pval = stats.t.sf(np.abs(tstat), n-1)*2
ci = stats.t.interval(0.95, n-1, ate, blockstd)

print("ATE: {:.3f}pp".format(ate*100), "std: {:.3f}".format(blockstd),
      "pvalue: {:.3f}".format(pval),
      "95% CI: ({:.3f}pp, {:.3f}pp)".format(ci[0]*100, ci[1]*100))
