import pandas as pd
import numpy as np
import ast
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


def evaluate_imputation(csv_path: str, output_path: str = "app/data/results/imputation_eval.csv"):
    df = pd.read_csv(csv_path)

    if "extras" in df.columns:
        try:
            df["extras"] = df["extras"].apply(
                lambda x: ast.literal_eval(x) if isinstance(x, str) and x.strip() else {}
            )
            df["ground_truth"] = df["extras"].apply(lambda d: d.get("ground_truth"))
        except Exception as e:
            df["ground_truth"] = np.nan
    elif "ground_truth" not in df.columns:
        return None

    results = []

    # Group by stream_id
    for stream_id, group in df.groupby("stream_id"):
        imputed = group[group["partition"] == "imputed"]

        if imputed.empty:
            continue

        y_true = imputed["ground_truth"].values
        y_pred = imputed["value"].values

        mask = ~pd.isna(y_true)
        y_true = y_true[mask]
        y_pred = y_pred[mask]

        if len(y_true) == 0:
            continue

        mae = mean_absolute_error(y_true, y_pred)
        mse = mean_squared_error(y_true, y_pred)
        rmse = np.sqrt(mse)
        r2 = r2_score(y_true, y_pred)

        results.append({
            "stream_id": stream_id,
            "count": len(y_true),
            "MAE": mae,
            "RMSE": rmse,
            "R2": r2
        })


    results_df = pd.DataFrame(results)
    results_df.to_csv(output_path, index=False)

    return results_df


if __name__ == "__main__":
    results = evaluate_imputation("app/data/logs/test.csv")
    if results is not None:
        print(results)
