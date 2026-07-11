"""マネーフォワード for 住信SBIネット銀行 からの資産データ取得。

通信は mf-sbi-client(httpx + BeautifulSoup)に委譲し、このモジュールは
取得結果を csv として保存するところまでを担う。
"""

from __future__ import annotations

import calendar
import contextlib
import logging
import re
from datetime import date
from pathlib import Path

import pandas as pd
from mf_sbi_client import Config, MfSbiClient, RefreshError, open_client

from .aggregate import concat_each_account_files, concat_history, merge_profit_and_loss, merge_with_previous_result
from .config import ALL_HISTORY_CSV, Account, Settings

logger = logging.getLogger(__name__)

# 月次行の日付テキストは「YYYY-MM月末」形式
_MONTHLY_DATE_RE = re.compile(r'(\d{4})-(\d{2})')


class Moneyforward(contextlib.AbstractContextManager):
    """1アカウント分の取得処理。with 文で利用する。"""

    def __init__(self, account: Account, settings: Settings) -> None:
        self.csv_dir = settings.csv_dir / account.email
        self.portfolio_dir = self.csv_dir / 'portfolio'
        self.history_dir = self.csv_dir / 'history'
        for directory in (self.csv_dir, self.portfolio_dir, self.history_dir):
            directory.mkdir(parents=True, exist_ok=True)
        session_dir = settings.session_dir / account.email
        session_dir.mkdir(parents=True, exist_ok=True)
        self._stack = contextlib.ExitStack()
        self.client: MfSbiClient = self._stack.enter_context(open_client(
            Config(email=account.email, password=account.password),
            cookies_path=session_dir / 'cookies.json',
        ))

    def __exit__(self, *exc_info) -> None:
        self._stack.close()

    def login(self) -> None:
        """ログインする(キャッシュ済みセッションがあれば再利用)。"""
        self.client.ensure_login()

    def reload_accounts(self, reload_wait_time: int) -> None:
        """連携金融機関の情報を更新し、完了を待つ。

        タイムアウトしても処理は継続する(旧実装は固定時間待って続行していた)。
        """
        self.client.refresh_all_accounts(dry_run=False)
        try:
            accounts = self.client.wait_refresh(timeout=reload_wait_time)
        except RefreshError as e:
            logger.warning(f"reload timeout: {e}")
            accounts = self.client.list_accounts()
        for account in accounts:
            logger.info(f"Last obtained date: {account.last_updated} | {account.name}")

    def download_history(self) -> None:
        """各月の資産推移 csv を取得し、結合 csv を作る。"""
        for point in self.client.get_asset_history():
            if not point.is_monthly:
                continue
            matched = _MONTHLY_DATE_RE.match(point.date)
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
        save_path = self.history_dir / 'this_month.csv'
        save_path.unlink(missing_ok=True)
        save_path.write_text(self.client.get_asset_history_csv(), encoding='utf-8')
        logger.info(f"Downloaded {save_path}")
        concat_history(self.history_dir, self.csv_dir / ALL_HISTORY_CSV)

    def download_portfolio(self, asset_ids: list[str]) -> None:
        """資産クラス別の保有明細を取得して csv 化する(金額は数値化する)。"""
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


def download_all(settings: Settings) -> None:
    """全アカウントの資産データを取得し、最終成果物の csv まで集約する。"""
    settings.concat_csv_dir.mkdir(parents=True, exist_ok=True)
    for account in settings.accounts:
        with Moneyforward(account, settings) as mf:
            mf.login()
            mf.reload_accounts(settings.reload_wait_time)
            mf.download_history()
            mf.download_portfolio([asset.id for asset in settings.assets])
            merge_profit_and_loss(mf.csv_dir, mf.portfolio_dir, settings.assets)
    new_all_history_wpl = concat_each_account_files(settings)
    merge_with_previous_result(new_all_history_wpl, settings)
