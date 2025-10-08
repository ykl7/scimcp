"""
Copyright © 2025 The Johns Hopkins University Applied Physics Laboratory LLC

This material may be only be used, modified, or reproduced by or for the U.S.
Government pursuant to the license rights granted under the clauses at DFARS
252.227‐7013/7014 or FAR  52.227‐14. For any other permission, please contact
the Office of Technology Transfer at JHU/APL: Telephone: 443‐778‐2792.

NO WARRANTY, NO LIABILITY. THIS MATERIAL IS PROVIDED “AS IS.” JHU/APL MAKES NO
REPRESENTATION OR WARRANTY WITH RESPECT TO THE PERFORMANCE OF THE MATERIALS,
INCLUDING THEIR SAFETY, EFFECTIVENESS, OR COMMERCIAL VIABILITY, AND DISCLAIMS ALL
WARRANTIES IN THE MATERIAL, WHETHER EXPRESS OR IMPLIED, INCLUDING (BUT NOT
LIMITED TO) ANY AND ALL IMPLIED WARRANTIES OF PERFORMANCE, MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE, AND NON‐INFRINGEMENT OF INTELLECTUAL
PROPERTY OR OTHER THIRD PARTY RIGHTS. ANY USER OF THE MATERIAL ASSUMES THE
ENTIRE RISK AND LIABILITY FOR USING THE MATERIAL. IN NO EVENT SHALL JHU/APL BE
LIABLE TO ANY USER OF THE MATERIAL FOR ANY ACTUAL, INDIRECT, CONSEQUENTIAL,
SPECIAL OR OTHER DAMAGES ARISING FROM THE USE OF, OR INABILITY TO USE, THE
MATERIAL, INCLUDING, BUT NOT LIMITED TO, ANY DAMAGES FOR LOST PROFITS.
"""
import argparse
import json
import sys

from krippendorff import alpha as kripp_alpha
import numpy as np
import pandas as pd
from scipy.stats import pearsonr
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    cohen_kappa_score,
    mean_absolute_error,
)
from tabulate import tabulate


def is_whole_number(x):
    """
    Returns True if the input x is a whole number (integer or float with no decimal part); False otherwise.

    :param x: number value (float or int)
    :return: boolean
    """
    return isinstance(x, int) or (isinstance(x, float) and x.is_integer())


def load_submission_metadata(submission_path):
    """
    Loads submission metadata from the first line of a JSONL file.
    :param submission_path:
    :return: team <str>, run_id <str>
    """
    with open(submission_path, "r", encoding="utf-8") as f:
        try:
            first_record = json.loads(f.readline())
        except (IOError, ValueError) as e:
            raise IOError(
                f"Error reading first line of submission file {submission_path}: {e}"
            )

    if "team" not in first_record or "run_id" not in first_record:
        raise KeyError(
            f"'team' or 'run_id' not found in submission record: {first_record.keys()}"
        )

    return first_record["team"], first_record["run_id"]


def load_dataframe(path, label, verbose=False):
    """
    Load JSONL into DataFrame and validate required columns.
    Currently, pull only feasibility Likert scores and give them the provided label.
    Returns DataFrame with ['problem_id', label] where label is the renamed likert_score.

    :param path: path to JSONL file
    :param label: renamed likert score
    :param verbose: boolean
    :return: DataFrame
    """
    try:
        df = pd.read_json(path, lines=True, encoding="utf-8")
    except ValueError as e:
        raise IOError(f"Error reading JSONL file {path}: {e}")

    required = {"problem_id", "likert_score"}

    if not required.issubset(df.columns):
        missing = required - set(df.columns)
        raise ValueError(f"Missing fields {missing} in {path}")

    df = df[["problem_id", "likert_score"]].copy()
    df = df.rename(columns={"likert_score": label})

    # validate by checking for integer values, that is, whole numbers
    # integers expressed as floats are ok (e.g., 3.0)
    whole_mask = df[label].map(is_whole_number)
    bad_count = (~whole_mask).sum()

    if bad_count > 0:
        raise ValueError(f"{bad_count} non-whole-number Likert score found in {path}.")

    # also check explicitly for nans just in case
    nan_mask = np.isnan(df[label])

    if nan_mask.any():
        raise ValueError(f"{label} contains NaN values in {path}.")

    # cast to float for computation later
    df[label] = df[label].astype(float)

    if verbose:
        print(
            f"[load_dataframe] Successfully loaded DataFrame from {path} containing {len(df)} rows."
        )

    return df


def evaluate_feasibility(gold_scores, sys_scores, verbose=False):
    """
    Compute agreement metrics between two numeric arrays.
    Returns dict of metric_name -> score.

    :param gold_scores: numeric array of gold scores
    :param sys_scores: numeric array of system assessments
    :param verbose: boolean
    :return: dict: metric_name -> numeric score
    """
    metrics = {}

    # Krippendorff's alpha (interval)
    data = np.vstack([gold_scores, sys_scores])
    try:
        metrics["krippendorff_alpha"] = kripp_alpha(
            data, level_of_measurement="interval"
        )
    except ValueError:
        print(
            "Error computing Krippendorff alpha; setting it to 0. Check for small sample size or constant input.",
            file=sys.stderr,
        )
        metrics["krippendorff_alpha"] = 0

    # Quadratic-weighted Cohen's kappa
    metrics["quadratic_cohen_kappa"] = cohen_kappa_score(
        gold_scores, sys_scores, weights="quadratic"
    )

    # Pearson correlation coefficient
    metrics["pearson"], _ = pearsonr(gold_scores, sys_scores)

    # Mean Absolute Error
    metrics["mean_absolute_error"] = mean_absolute_error(gold_scores, sys_scores)

    # Accuracy
    metrics["accuracy"] = accuracy_score(gold_scores, sys_scores)

    # Balanced Accuracy
    metrics["balanced_accuracy"] = balanced_accuracy_score(gold_scores, sys_scores)

    # Accuracy if only looking at the sign
    metrics["sign_accuracy"] = accuracy_score(np.sign(gold_scores), np.sign(sys_scores))

    if verbose:
        for m in metrics:
            print(f"[evaluate_feasibility] {m} = {metrics[m]:.4f}")

    return metrics

def parse_time_column(series):
    return pd.to_numeric(series.astype(str).str.replace("s", "").str.strip(), errors='coerce')


def prepare_eval(gold_path, sys_path, verbose=False):
    """
    Load a submitted run and the gold standard and prepare an evaluation dict
    :param gold_path: path to the gold standard jsonl
    :param sys_path: path to the submission jsonl (containing one run only)
    :param verbose: boolean, enable logging
    :return: dict of metric_name -> score as well as metadata keys
    """
    # load metadata
    # team, run_id = load_submission_metadata(sys_path)
    team, run_id = "SciFy-UMBC-SBU-UT",0

    if verbose:
        print(f"[prepare_eval] Processing run {run_id} from team {team}.")

    df_gold = load_dataframe(gold_path, label="likert_gold", verbose=verbose)
    df_sys = load_dataframe(sys_path, label="likert_sub", verbose=verbose)

    if verbose:
        print(
            f"[prepare_eval] Gold contains {len(df_gold)} rows; submission contains {len(df_sys)} rows."
        )

    # align on problem_id in case of mismatched ordering
    df = pd.merge(df_gold, df_sys, on="problem_id", how="inner")

    if verbose:
        print(f"[prepare_eval] After merging on 'problem_id': {len(df)} rows.")

        if len(df) != len(df_gold):
            print("[prepare_eval] WARNING: unable to match some rows from gold")

        if len(df) != len(df_sys):
            print("[prepare_eval] WARNING: unable to match some rows from system")

    if df.empty:
        raise ValueError("No matching problem_ids between gold and submission.")

    metrics = evaluate_feasibility(
        df["likert_gold"].values, df["likert_sub"].values, verbose=verbose
    )

    try:
        df_with_wallclock = pd.read_json(sys_path, lines=True, encoding="utf-8")
    except ValueError as e:
        raise IOError(f"Error reading JSONL file {sys_path}: {e}")
    if "wall_clock_time" in df_with_wallclock.columns or "claim_process_time" in df_with_wallclock.columns:
        if "wall_clock_time" in df_with_wallclock.columns:
            times = parse_time_column(df_with_wallclock["wall_clock_time"]).dropna().values
        elif "claim_process_time" in df_with_wallclock.columns:
            times = parse_time_column(df_with_wallclock["claim_process_time"]).dropna().values
        if times.size == 0:
            raise ValueError(f"No valid timing values for team {team}, run {run_id}")

        metrics["wallclock"] = {
            "min": float(np.min(times)),
            "mean": float(np.mean(times)),
            "max": float(np.max(times)),
            "std_dev": float(np.std(times))  # population std dev
        }

    else:
        raise ValueError(
            f"Missing 'wall_clock_time' or 'claim_process_time' column for team: {team}, run: {run_id}."
        )
    
    # add in metadata
    output_dict = {"team": team, "run_id": run_id, **metrics}

    return output_dict


def main():
    parser = argparse.ArgumentParser(
        description="Compute agreement metrics between a submission and gold standard."
    )
    parser.add_argument("-i", "--input", required=True, help="Submission JSONL file")
    parser.add_argument("-g", "--gold", required=True, help="Gold standard JSONL file")
    parser.add_argument("-o", "--output", help="Output JSON file path")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    args = parser.parse_args()

    # evaluation logic
    evaluation_results = prepare_eval(args.gold, args.input, args.verbose)

    if args.output:
        # write results to JSON
        try:
            with open(args.output, "w") as f:
                json.dump(evaluation_results, f, indent=2)
        except IOError as e:
            raise IOError(f"Error writing output file {args.output}: {e}")

        print(f"[main] Results written to {args.output}")
    else:
        # Print the ASCII table
        headers = list(evaluation_results.keys())
        row = list(evaluation_results.values())
        print(tabulate([row], headers=headers, floatfmt=".4f"))


if __name__ == "__main__":
    main()