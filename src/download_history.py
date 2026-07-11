import calendar
import configparser
import contextlib
import json
import os
import re
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
from dotenv import load_dotenv
from mf_sbi_client import Config, RefreshError, open_client

from my_logging import get_my_logger
logger = get_my_logger(__name__)


# GLOBALS
# dir names
ROOT_CSV_DIR = Path('../csv');              ROOT_CSV_DIR  .mkdir(exist_ok=True)
CONCAT_CSV_DIR = ROOT_CSV_DIR / 'concat';   CONCAT_CSV_DIR.mkdir(exist_ok=True)
SESSION_DIR = Path('../.session')
# csv names
ALL_HISTORY_CSV = 'all_history.csv'
ALL_HISTORY_WPL_CSV = 'all_history_with_profit_and_loss.csv'


class Moneyforward():
    """
    Moneyforwardから各種情報を取得する

    Attributes
    ----------
    email : str
        ログイン用メールアドレス
    csv_dir : Path
        ユーザごとのcsvを保持するルートディレクトリ
    portfolio_dir : Path
        ユーザごとのportfolioに関するcsvを保持するディレクトリ
    history_dir : Path
        ユーザごとのhistoryに関するcsvを保持するディレクトリ
    client : MfSbiClient
        mf-sbi-client のHTTPクライアント
    """
    def __init__(self, email: str, password: str) -> None:
        """
        Parameters
        ----------
        email : str
            ログイン用メールアドレス
        password : str
            ログイン用パスワード
        """
        self.email = email
        self.csv_dir = ROOT_CSV_DIR / email;                self.csv_dir      .mkdir(exist_ok=True)
        self.portfolio_dir = self.csv_dir / 'portfolio';    self.portfolio_dir.mkdir(exist_ok=True)
        self.history_dir = self.csv_dir / 'history';        self.history_dir  .mkdir(exist_ok=True)
        (SESSION_DIR / email).mkdir(parents=True, exist_ok=True)
        self._stack = contextlib.ExitStack()
        self.client = self._stack.enter_context(open_client(
            Config(email=email, password=password),
            cookies_path=SESSION_DIR / email / 'cookies.json',
        ))

    def close(self) -> None:
        """
        HTTPクライアントの終了処理を行う。
        """
        self._stack.close()

    def login(self) -> None:
        """
        MoneyForwardのログイン処理を実施する
        """
        self.client.ensure_login()

    def refresh_valuation_profit_and_loss(self, asset_ids: list) -> None:
        """
        ローカルの各assetの資産内訳（損益）を最新状態にする

        Parameters
        ----------
        asset_ids : list of str
            html要素の特定に利用するasset_idのリスト
        """
        details = self.client.get_portfolio_details()
        for asset_id in asset_ids:
            save_path = self.portfolio_dir / f'{asset_id}.csv'
            rows = details.get(asset_id, [])
            if not rows:
                logger.debug(f"no portfolio elements: {asset_id}")
                save_path.unlink(missing_ok=True)
                continue
            df = pd.DataFrame(rows)
            df = df.replace(',', '', regex=True).replace('円', '', regex=True)
            df.to_csv(save_path, encoding='utf-8', index=False)
            logger.info(f"Downloaded {save_path}")

    def download_history(self) -> None:
        """
        各月の資産推移を取得する
        """
        # download previous month csv
        for point in self.client.get_asset_history():
            if not point.is_monthly:
                continue
            # 月次行の日付テキストは「YYYY-MM月末」形式
            matched = re.match(r'(\d{4})-(\d{2})', point.date)
            if matched is None:
                logger.warning(f"unexpected monthly date format: {point.date}")
                continue
            year, month = int(matched.group(1)), int(matched.group(2))
            month_end = date(year, month, calendar.monthrange(year, month)[1])
            save_path = self.history_dir / f'{month_end:%Y-%m-%d}.csv'
            if save_path.exists():
                continue
            save_path.write_text(self.client.get_monthly_asset_history_csv(month_end), encoding='utf-8')
            logger.info(f"Downloaded {save_path}")
        # download this month csv
        save_path = self.history_dir / 'this_month.csv'
        save_path.unlink(missing_ok=True)
        save_path.write_text(self.client.get_asset_history_csv(), encoding='utf-8')
        logger.info(f"Downloaded {save_path}")
        # create concatenated csv
        self._concat_csv()

    def reload_accounts(self, reload_wait_time: int = 60) -> None:
        """
        登録されている金融機関の情報を更新する

        Parameters
        ----------
        reload_wait_time: int
            更新完了を待機する最大秒数
        """
        self.client.refresh_all_accounts(dry_run=False)
        try:
            accounts = self.client.wait_refresh(timeout=reload_wait_time)
        except RefreshError as e:
            # 旧実装は固定時間待って続行していたため、タイムアウトしても処理は継続する
            logger.warning(f"reload timeout: {e}")
            accounts = self.client.list_accounts()
        for account in accounts:
            logger.info(f"Last obtained date: {account.last_updated} | {account.name}")

    def _concat_csv(self) -> None:
        """
        ダウンロードした各月の資産推移を結合する
        """
        csv_list = sorted(self.history_dir.glob('*.csv'))
        df_list = []
        for csv_path in csv_list:
            df = pd.read_csv(csv_path, encoding='utf-8', sep=',')
            df_list.append(df)
        df_concat = pd.concat(df_list)
        df_concat = my_set_index(df_concat)
        df_concat = df_concat.add_prefix(':')
        df_concat.to_csv(self.csv_dir / ALL_HISTORY_CSV, encoding='utf-8')

    def calc_profit_and_loss(self, assets: list) -> None:
        """
        資産推移と資産内訳（損益）を結合

        Parameters
        ----------
        assets : list of dict
            各assetのidとカラム名を含む辞書のリスト
        """
        df_all_org = pd.read_csv(self.csv_dir / ALL_HISTORY_CSV, encoding='utf-8', sep=',')
        csv_path = self.csv_dir / ALL_HISTORY_WPL_CSV
        df_all_with_profit_and_loss = pd.read_csv(csv_path, encoding='utf-8', sep=',') if csv_path.exists() else df_all_org
        df_merged = pd.merge(df_all_org, df_all_with_profit_and_loss, how='left')
        df_merged = my_set_index(df_merged)
        portfolio_sets = [[asset['column_name'], self.portfolio_dir / f"{asset['id']}.csv"] for asset in assets if asset['column_name'] != '']
        for column_name, asset_csv_path in portfolio_sets:
            if not asset_csv_path.exists():
                continue
            target_column_name = '評価損益'
            df_tmp = pd.read_csv(asset_csv_path, encoding='utf-8', sep=',')
            df_tmp = df_tmp.dropna(subset=[target_column_name])
            profit_and_loss = df_tmp[target_column_name].sum()
            if not column_name in df_merged.columns:
                df_merged[column_name] = 0
            df_merged.at[df_merged.index[0], column_name] = profit_and_loss
        df_merged.to_csv(csv_path, encoding='utf-8')


def my_set_index(df: pd.DataFrame) -> pd.DataFrame:
    """
    DataFrameの基本的なインデックス登録処理をまとめたもの

    Parameters
    ----------
    df : pd.DataFrame
        target_column_nameをカラムに持つDataFrame

    Returns
    -------
    df : pd.DataFrame
        各種処理を適用したDataFrame
    """
    target_column_name = '日付'
    df.drop_duplicates(subset=target_column_name, inplace=True)
    df.set_index(target_column_name, inplace=True)
    df.sort_index(ascending=False, inplace=True)
    df.fillna(0, inplace=True)
    return df

def concat_each_account_files(assets: list) -> pd.DataFrame:
    """
    複数アカウントから取得された資産推移と資産内訳（損益）を結合する

    Parameters
    ----------
    assets : list of dict
        各assetのidを含む辞書のリスト

    Returns
    -------
    df_concat : pd.DataFrame
        各アカウント、各月、各assetの資産内訳（損益）を結合したDataFrame
    """
    ## asset files
    for asset in assets:
        df_list = []
        for asset_csv_path in ROOT_CSV_DIR.glob(f"*/portfolio/{asset['id']}.csv"):
            df = pd.read_csv(asset_csv_path, encoding='utf-8', sep=',')
            df_list.append(df)
        df_concat = pd.concat(df_list)
        df_concat.to_csv(CONCAT_CSV_DIR / f"{asset['id']}.csv", encoding='utf-8', index=False)
    ## history files
    df_concat = None
    for csv_path in ROOT_CSV_DIR.glob(f'*[!concat]/{ALL_HISTORY_WPL_CSV}'):
        df = pd.read_csv(csv_path, encoding='utf-8', sep=',')
        df = my_set_index(df)
        df_concat = df_concat.add(df, fill_value=0) if df_concat is not None else df
    df_concat.sort_index(inplace=True, ascending=False)
    df_concat.to_csv(CONCAT_CSV_DIR / ALL_HISTORY_WPL_CSV, encoding='utf-8')
    return df_concat


def main() -> None:
    load_dotenv('../.env')
    emails = json.loads(os.environ['MF_SBI_EMAILS'])
    passwords = json.loads(os.environ['MF_SBI_PASSWORDS'])
    config_ini = configparser.ConfigParser()
    config_ini.read('config.ini', encoding='utf-8')
    assets = [dict(config_ini.items(section)) for section in config_ini.sections() if 'asset_' in section]
    reload_wait_time = int(config_ini.get('MONEYFORWARD','Reload_wait_time'))

    # download each files
    for email, password in zip(emails, passwords):
        mf = Moneyforward(email=email, password=password)
        try:
            mf.login()
            mf.reload_accounts(reload_wait_time)
            mf.download_history()
            mf.refresh_valuation_profit_and_loss([asset['id'] for asset in assets])
            mf.calc_profit_and_loss(assets)
        except Exception as e:
            logger.error(e)
            sys.exit(1)
        finally:
            mf.close()

    # concat each files
    new_all_history_wpl = concat_each_account_files(assets)

    # generate result csv
    all_history_wpl_csv_path = ROOT_CSV_DIR / ALL_HISTORY_WPL_CSV
    old_all_history_wpl = my_set_index(pd.read_csv(all_history_wpl_csv_path, encoding='utf-8', sep=',')) if all_history_wpl_csv_path.exists() else new_all_history_wpl
    # 日付indexで整合を取り、既存日付はnewer優先・newerに無い日付/列はolderで補完する
    df_merged = new_all_history_wpl.combine_first(old_all_history_wpl)
    df_merged.fillna(0, inplace=True)
    df_merged.sort_index(ascending=False, inplace=True)
    df_merged = df_merged.sort_index(axis='columns')
    # newerの損益値が0の場合はolderの値を採用
    for asset in assets:
        column_name = asset['column_name']
        if column_name == '' or column_name not in old_all_history_wpl.columns:
            continue
        older_values = old_all_history_wpl[column_name].reindex(df_merged.index).fillna(0)
        df_merged[column_name] = np.where(df_merged[column_name] == 0, older_values, df_merged[column_name])
    df_merged.to_csv(all_history_wpl_csv_path, encoding='utf-8')


if __name__ == '__main__':
    main()
