#!/usr/bin/env python3
"""Build updated high_growth_turnaround US stocks dataset."""
import pandas as pd, numpy as np
from datetime import datetime
from finvizfinance.screener.overview import Overview
import yfinance as yf
from tqdm import tqdm

MIN_SALES_CAGR = 20
MIN_MARKET_CAP = 100
MAX_MARKET_CAP = 100000
TODAY = datetime.utcnow().strftime("%Y-%m-%d")

def query_finviz():
    filters = ["sales5years%3Over20", "cap_smallover", "cap_megaUnder"]
    scr = Overview(); scr.set_filter(filters=filters)
    return scr.screener_view()["Ticker"].tolist()

def fetch_metrics(tk):
    t = yf.Ticker(tk)
    try:
        rev = t.financials.T["Total Revenue"].tail(3) / 1e6
        ni = t.financials.T["Net Income"].tail(3) / 1e6
        ocf = t.cashflow.T["Total Cash From Operating Activities"].iloc[-1] / 1e6
        bs = t.balance_sheet.T
        debt = bs["Total Debt"].iloc[-1] / 1e6
        eq = bs["Total Stockholder Equity"].iloc[-1] / 1e6
        mcap = t.info.get("marketCap", np.nan) / 1e6
    except: return None
    if len(rev)<3 or len(ni)<3: return None
    cagr = ((rev.iloc[-1]/rev.iloc[0])**(1/2)-1)*100 if rev.iloc[0]>0 else np.nan
    ni_cagr = ((abs(ni.iloc[-1])/abs(ni.iloc[0]))**(1/2)-1)*100 if ni.iloc[0]!=0 else np.nan
    sign_change = ni.iloc[0]<0 and ni.iloc[-1]>0
    return {
        "Ticker":tk, "Rev_2022($M)":rev.iloc[0], "Rev_2023($M)":rev.iloc[1], "Rev_2024($M)":rev.iloc[2],
        "NI_2022($M)":ni.iloc[0], "NI_2023($M)":ni.iloc[1], "NI_2024($M)":ni.iloc[2],
        "OCF_2024($M)":ocf, "Debt/Equity":debt/eq if eq!=0 else np.nan,
        "RevCAGR_3y(%)":cagr, "NICAGR_3y(%)":ni_cagr, "NI_sign_change":sign_change, "MarketCap($M)":mcap
    }

def main():
    tickers = query_finviz(); rows = []
    for tk in tqdm(tickers, desc="Pulling data"):
        m = fetch_metrics(tk)
        if m: rows.append(m)
    df = pd.DataFrame(rows)
    df = df[(df["RevCAGR_3y(%)"]>=MIN_SALES_CAGR) & (df["MarketCap($M)"].between(MIN_MARKET_CAP, MAX_MARKET_CAP)) & (
        df["NI_sign_change"] | (df["NI_2024($M)"] > 0) | df["NI_2024($M)"].between(-20, 0))]
    df.to_csv("high_growth_turnaround_us_stocks.csv", index=False)
    df.to_excel("high_growth_turnaround_us_stocks.xlsx", index=False)
    print(f"Saved {len(df)} tickers on {TODAY}")

if __name__ == "__main__": main()
