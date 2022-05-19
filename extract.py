#!/usr/bin/env python

import os
import re
import glob
from numpy import save
import pandas as pd


latest_prs_cols = [
    "user",
    "Bench 5RM",
    "Bench 1RM",
    "Squat 5RM",
    "Squat 1RM",
    "Deadlift 5RM",
    "Deadlift 1RM",
    "Powerlift Total",
]


def save_seaborn_plot(pr_df, png_file):
    import seaborn as sns

    sns.set(style="darkgrid")
    g = sns.FacetGrid(
        pr_df,
        col="exercise",
        row="user",
        hue="reps",
        sharex=True,
        sharey=True,
        margin_titles=True,
    )
    g.map(sns.lineplot, "date", "weight", marker="o")
    g.set_titles("{col_name}")
    g.set(xlabel="Date", ylabel="Weight")
    g.add_legend()
    g.set_xticklabels(rotation=45)
    g.savefig(png_file)


def transpose_tbl(tbl):
    return [list(x) for x in zip(*tbl)]


def save_plotly_fig(pr_df, latest_pr_tbl, html_file):
    import plotly.express as px
    import plotly as plt
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    fig = make_subplots(
        rows=2,
        cols=1,
        vertical_spacing=0.03,
        # specs=[[{"type": "table"}], [{"type": "xy"}]],
    )
    tbl_fig = go.Figure(
        data=[
            go.Table(
                header=dict(
                    values=latest_prs_cols,
                    line_color="darkslategray",
                    fill_color="lightskyblue",
                    align="left",
                ),
                cells=dict(
                    values=transpose_tbl(latest_pr_tbl),
                    line_color="darkslategray",
                    fill_color="lightcyan",
                    align="left",
                ),
            )
        ],
        layout_title_text="Latest PRs",
    )

    # fig.update_layout(width=500, height=300)
    fig = px.line(
        pr_df,
        x="date",
        y="weight",
        color="reps",
        symbol="reps",
        facet_row="user",
        facet_col="exercise",
        # line_dash="user",
        title="PR Evolution",
    )
    fig.for_each_annotation(
        lambda a: a.update(
            text="<b>" + a.text.split("=")[1] + "</b>", font=dict(size=18)
        )
    )
    # fig.for_each_trace(lambda t: t.update(name=t.name.split("=")[1]))

    # fig.update_layout(
    #     # xaxis={'side': 'top'},
    #     yaxis={"side": "right"}
    # )
    html = f"""<html><head><title>Powerlifting PRs</title></head><body>
    <div>
    {plt.io.to_html(fig, full_html=False)}
    </div>
    <div>
    {plt.io.to_html(tbl_fig, full_html=False)}
    </div>
     </body></html>"""
    with open(html_file, "w") as fd:
        fd.write(html)


def get_prs_from_strong_exports():
    main_exercises = ["Bench Press", "Squat", "Deadlift"]
    # os.chdir(os.path.expanduser("~"))
    # os.chdir("iCloud/StrongWorkouts")
    prs = {}
    users = {}
    pr_cols = ["user", "date", "exercise", "weight", "reps"]
    pr_rows = []
    latest_pr_1 = {}
    latest_pr_5 = {}
    for file in sorted(glob.glob("*/strong.csv")):
        user = re.match(r"(.*)/", file).group(1)
        users[user] = 1
        df = pd.read_csv(file, sep=",")
        for i, row in df.iterrows():
            # print(row)
            exercise = row["Exercise Name"]
            exercise = exercise.replace(" (Barbell)", "")
            date = row["Date"]
            reps = row["Reps"]
            if reps >= 5:
                reps = 5
            elif reps >= 1:
                reps = 1
            else:
                raise ValueError(f"Invalid rep count: {reps} in row {row}")
            wt = round(row["Weight"])
            old_pr = prs.get((user, exercise, reps), 0)
            if exercise in main_exercises and wt > old_pr:
                pr_rows.append([user, pd.to_datetime(date), exercise, wt, reps])
                # print(f"{user} PR! {date[:10]} {exercise} {reps} {wt}")
                prs[(user, exercise, reps)] = wt
                if reps == 1:
                    latest_pr_1[(user, exercise)] = wt
                elif reps == 5:
                    latest_pr_5[(user, exercise)] = wt
    ex_ = main_exercises
    latest_pr_tbl = [
        [
            user,
            latest_pr_5.get((user, ex_[0]), 0),
            latest_pr_1.get((user, ex_[0]), 0),
            latest_pr_5.get((user, ex_[1]), 0),
            latest_pr_1.get((user, ex_[1]), 0),
            latest_pr_5.get((user, ex_[2]), 0),
            latest_pr_1.get((user, ex_[2]), 0),
            latest_pr_1.get((user, ex_[0]), 0)
            + latest_pr_1.get((user, ex_[1]), 0)
            + latest_pr_1.get((user, ex_[2]), 0),
        ]
        for user in users.keys()
    ]
    # print(latest_pr_tbl)
    return pd.DataFrame(pr_rows, columns=pr_cols), latest_pr_tbl


#
# Main
#
pr_df, latest_pr_tbl = get_prs_from_strong_exports()
save_plotly_fig(pr_df, latest_pr_tbl, "prs.html")
save_seaborn_plot(pr_df, "prs.png")
