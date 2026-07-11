"""設定の読み込み。

- 秘匿値: .env(gitignore 済み)に置く。MF_SBI_EMAILS / MF_SBI_PASSWORDS(JSON 配列)
  と SPREADSHEET_KEY。コミットされる config.ini には秘匿値を書かない
- その他: config.ini(ワークシート名・asset マッピング・更新待ち時間)
- パス: 実行時のカレントディレクトリをプロジェクトルートとして解決する
"""

from __future__ import annotations

import configparser
import json
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# 生成される csv のファイル名(旧実装からの互換を維持する)
ALL_HISTORY_CSV = 'all_history.csv'
ALL_HISTORY_WPL_CSV = 'all_history_with_profit_and_loss.csv'


@dataclass(frozen=True)
class Account:
    """マネーフォワードのログインアカウント。"""
    email: str
    password: str


@dataclass(frozen=True)
class Asset:
    """資産クラスの設定(config.ini の [asset_*] セクション)。"""
    id: str            # /bs/portfolio の明細セクション要素 id(例 portfolio_det_eq)
    column_name: str   # 集約 csv に追加する損益カラム名(空なら損益計算対象外)
    sheet_name: str    # 転記先のワークシート名


@dataclass(frozen=True)
class Settings:
    """実行時設定。"""
    accounts: list[Account]
    reload_wait_time: int
    spreadsheet_key: str
    worksheet_name: str
    assets: list[Asset]
    root_dir: Path

    @property
    def csv_dir(self) -> Path:
        return self.root_dir / 'csv'

    @property
    def concat_csv_dir(self) -> Path:
        return self.csv_dir / 'concat'

    @property
    def session_dir(self) -> Path:
        return self.root_dir / '.session'

    @property
    def log_dir(self) -> Path:
        return self.root_dir / 'log'

    @property
    def client_secret_path(self) -> Path:
        return self.root_dir / 'client_secret.json'


def load_settings(root_dir: Path | None = None) -> Settings:
    """プロジェクトルート(既定: カレントディレクトリ)から設定を構築する。"""
    root = (root_dir or Path.cwd()).resolve()
    load_dotenv(root / '.env')
    emails = json.loads(os.environ['MF_SBI_EMAILS'])
    passwords = json.loads(os.environ['MF_SBI_PASSWORDS'])
    accounts = [Account(email=e, password=p) for e, p in zip(emails, passwords)]

    ini = configparser.ConfigParser()
    ini.read(root / 'config.ini', encoding='utf-8')
    assets = [Asset(**dict(ini.items(section))) for section in ini.sections() if section.startswith('asset_')]
    return Settings(
        accounts=accounts,
        reload_wait_time=ini.getint('MONEYFORWARD', 'Reload_wait_time'),
        spreadsheet_key=os.environ['SPREADSHEET_KEY'],
        worksheet_name=ini.get('SPREAD_SHEET', 'Worksheet_name'),
        assets=assets,
        root_dir=root,
    )
