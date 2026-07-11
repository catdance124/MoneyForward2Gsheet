"""ダウンロード済み csv の集約(pandas 処理)。

csv のファイル形式・ディレクトリ構成は旧実装からの互換を維持する:
- csv/<email>/history/*.csv           月次・今月の資産推移(サービスの CSV を UTF-8 化したもの)
- csv/<email>/portfolio/<asset>.csv   資産クラス別の保有明細(数値化済み)
- csv/<email>/all_history.csv         資産推移の結合(カラムに ':' プレフィックス)
- csv/<email>/all_history_with_profit_and_loss.csv  損益カラムを付与した集約
- csv/concat/*                        複数アカウントの合算
- csv/all_history_with_profit_and_loss.csv          最終成果物
"""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pandas as pd

from .config import ALL_HISTORY_CSV, ALL_HISTORY_WPL_CSV, Asset, Settings

logger = logging.getLogger(__name__)


def set_date_index(df: pd.DataFrame) -> pd.DataFrame:
    """日付カラムの重複を除去して降順の index にし、欠損を 0 埋めする。"""
    target_column_name = '日付'
    df.drop_duplicates(subset=target_column_name, inplace=True)
    df.set_index(target_column_name, inplace=True)
    df.sort_index(ascending=False, inplace=True)
    df.fillna(0, inplace=True)
    return df


def concat_history(history_dir: Path, save_path: Path) -> None:
    """各月の資産推移 csv を1つに結合する。"""
    df_list = [pd.read_csv(csv_path, encoding='utf-8') for csv_path in sorted(history_dir.glob('*.csv'))]
    df_concat = set_date_index(pd.concat(df_list))
    df_concat = df_concat.add_prefix(':')
    df_concat.to_csv(save_path, encoding='utf-8')


def merge_profit_and_loss(csv_dir: Path, portfolio_dir: Path, assets: list[Asset]) -> None:
    """資産推移(all_history.csv)に資産クラスごとの損益カラムを付与する。

    損益はポートフォリオ明細の「評価損益」列の合計を最新日の行にのみ入れる。
    過去日の損益は既存の集約 csv から引き継ぐ。
    """
    df_all_org = pd.read_csv(csv_dir / ALL_HISTORY_CSV, encoding='utf-8')
    csv_path = csv_dir / ALL_HISTORY_WPL_CSV
    df_all_with_profit_and_loss = pd.read_csv(csv_path, encoding='utf-8') if csv_path.exists() else df_all_org
    df_merged = pd.merge(df_all_org, df_all_with_profit_and_loss, how='left')
    df_merged = set_date_index(df_merged)
    for asset in assets:
        if asset.column_name == '':
            continue
        asset_csv_path = portfolio_dir / f'{asset.id}.csv'
        if not asset_csv_path.exists():
            continue
        target_column_name = '評価損益'
        df_tmp = pd.read_csv(asset_csv_path, encoding='utf-8')
        df_tmp = df_tmp.dropna(subset=[target_column_name])
        profit_and_loss = df_tmp[target_column_name].sum()
        if asset.column_name not in df_merged.columns:
            df_merged[asset.column_name] = 0
        df_merged.at[df_merged.index[0], asset.column_name] = profit_and_loss
    df_merged.to_csv(csv_path, encoding='utf-8')


def concat_each_account_files(settings: Settings) -> pd.DataFrame:
    """複数アカウントの資産推移・損益を合算して csv/concat/ に書き出す。"""
    ## asset files
    for asset in settings.assets:
        df_list = []
        for asset_csv_path in settings.csv_dir.glob(f'*/portfolio/{asset.id}.csv'):
            df_list.append(pd.read_csv(asset_csv_path, encoding='utf-8'))
        df_concat = pd.concat(df_list)
        df_concat.to_csv(settings.concat_csv_dir / f'{asset.id}.csv', encoding='utf-8', index=False)
    ## history files
    df_concat = None
    for csv_path in settings.csv_dir.glob(f'*[!concat]/{ALL_HISTORY_WPL_CSV}'):
        df = set_date_index(pd.read_csv(csv_path, encoding='utf-8'))
        df_concat = df_concat.add(df, fill_value=0) if df_concat is not None else df
    df_concat.sort_index(inplace=True, ascending=False)
    df_concat.to_csv(settings.concat_csv_dir / ALL_HISTORY_WPL_CSV, encoding='utf-8')
    return df_concat


def merge_with_previous_result(new_all_history_wpl: pd.DataFrame, settings: Settings) -> None:
    """今回の集約結果を既存の最終成果物とマージして書き出す。

    日付 index で整合を取り、既存日付は newer 優先・newer に無い日付/列は older で
    補完する。損益は取得失敗時に 0 になるため、newer が 0 の日は older の値を採用する。
    (行順に依存する merge は pandas 2 の outer merge がキーを辞書順ソートするため使わない)
    """
    csv_path = settings.csv_dir / ALL_HISTORY_WPL_CSV
    old_all_history_wpl = set_date_index(pd.read_csv(csv_path, encoding='utf-8')) if csv_path.exists() else new_all_history_wpl
    df_merged = new_all_history_wpl.combine_first(old_all_history_wpl)
    df_merged.fillna(0, inplace=True)
    df_merged.sort_index(ascending=False, inplace=True)
    df_merged = df_merged.sort_index(axis='columns')
    for asset in settings.assets:
        if asset.column_name == '' or asset.column_name not in old_all_history_wpl.columns:
            continue
        older_values = old_all_history_wpl[asset.column_name].reindex(df_merged.index).fillna(0)
        df_merged[asset.column_name] = np.where(df_merged[asset.column_name] == 0, older_values, df_merged[asset.column_name])
    df_merged.to_csv(csv_path, encoding='utf-8')
