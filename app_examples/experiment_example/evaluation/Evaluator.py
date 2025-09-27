import pandas as pd
import numpy as np
from typing import Optional

class Evaluator:
    def __init__(self, filepath: Optional[str] = None, df: Optional[pd.DataFrame] = None):
        if filepath:
            self.df = pd.read_csv(filepath, header=1)
        elif df is not None:
            self.df = df
        else:
            raise ValueError("Provide either filepath or DataFrame")

        # ensure timestamp is float
        self.df["event_timestamp"] = self.df["event_timestamp"].astype(float)

    def get_pairwise(self):
        """
        Returns a DataFrame where each row is a matched observed/imputed event.
        """
        observed = self.df[self.df["partition"] == "observed"].copy()
        imputed = self.df[self.df["partition"] == "imputed"].copy()

        # merge on stream_id + timestamp, merge this on a specific ID thats gonna get propogated
        paired = pd.merge(
            observed,
            imputed,
            on=["stream_id", "event_id"],
            suffixes=("_obs", "_imp"),
        )
        return paired

    def compute_basic_metrics(self):
        paired = self.get_pairwise()

        gt = paired["extras_obs"].apply(lambda x: eval(x).get("ground_truth") if isinstance(x, str) else np.nan)
        preds = paired["value_imp"]

        mae = np.mean(np.abs(preds - gt))
        rmse = np.sqrt(np.mean((preds - gt) ** 2))

        return {"MAE": mae, "RMSE": rmse, "count": len(paired)}

    def run_statistical_tests(self):
        from scipy.stats import ttest_rel, wilcoxon

        paired = self.get_pairwise()
        print(paired)
        gt = paired["extras_obs"].apply(lambda x: eval(x).get("ground_truth") if isinstance(x, str) else np.nan)
        preds = paired["value_imp"]

        errors = preds - gt

        ttest = ttest_rel(preds, gt, nan_policy="omit")
        wilcoxon_test = wilcoxon(errors, zero_method="wilcox", correction=True)

        return {"t-test": ttest, "wilcoxon": wilcoxon_test}
