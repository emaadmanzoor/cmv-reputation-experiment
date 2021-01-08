#!/usr/bin/env python

import pandas as pd
import numpy as np
import statsmodels.api as sm
import statsmodels.formula.api as smf

import scipy.stats as stats
from scipy.stats import ttest_ind, ttest_rel, t

comments_df = pd.read_parquet("data/cmv/comment_df_2020-12-30-05-14-38_to_2021-01-07-21-24-47.parquet")
comments_df = comments_df[comments_df["immediate"]==True] # only root responses

stratum_effects = []
stratum_weight = []
stratum_vars = []
for stratum in range(1, 8):
  print("Stratum", stratum, end=" ")
  g0 = comments_df[(comments_df["stratum"]==stratum) &
                   (comments_df["group"]==0)]["successful"].values
  g1 = comments_df[(comments_df["stratum"]==stratum) &
                   (comments_df["group"]==1)]["successful"].values

  stratum_effects.append(g1 .mean() - g0.mean())
  stratum_weight.append(len(comments_df[comments_df["stratum"]==stratum])/
                        len(comments_df))

  n1 = len(g1)
  n0 = len(g0)
  var1 = np.var(g1)
  var0 = np.var(g0)
  stratum_vars.append(var1/n1 + var0/n0)

  t, p = ttest_ind(g0, g1, equal_var=False)

  print("success: T", "{:.2f}%".format(g1.mean()*100),
        "C", "{:.2f}%".format(g0.mean()*100),
        "pvalue =", "{:.3f}".format(p))

stratum_effects = np.array(stratum_effects)
stratum_weight = np.array(stratum_weight)

ate = np.sum(stratum_weight * stratum_effects)
blockvar = np.sum(stratum_weight * stratum_weight * stratum_vars)
blockstd = np.sqrt(blockvar)

n = len(comments_df[comments_df["stratum"]>0])
tstat = ate/blockstd
pval = stats.t.sf(np.abs(tstat), n-1)*2
ci = stats.t.interval(0.95, n-1, ate, blockstd)
print(ci)

print("ATE: {:.3f}%".format(ate*100), "std: {:.3f}".format(blockstd),
      "pvalue: {:.3f}".format(pval), "N =", n,
      "succ = {:.3f}%".format(comments_df["successful"].mean() * 100),
      "95% CI: ({:.3f}, {:.3f})".format(ci[0], ci[1]))
