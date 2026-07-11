"""集約済み csv の Google スプレッドシートへの転記。"""

from __future__ import annotations

import csv
import logging
from pathlib import Path

import gspread

from .config import ALL_HISTORY_WPL_CSV, Settings

logger = logging.getLogger(__name__)


def update_sheet(workbook: gspread.Spreadsheet, worksheet_name: str, csv_path: Path) -> None:
    """ワークシートを csv の内容で置き換える(なければ作成する)。"""
    if worksheet_name not in [worksheet.title for worksheet in workbook.worksheets()]:
        workbook.add_worksheet(title=worksheet_name, rows=50, cols=50)
    ws = workbook.worksheet(worksheet_name)
    ws.clear()
    with open(csv_path, encoding='utf-8') as f:
        values = list(csv.reader(f))
    workbook.values_update(
        worksheet_name,
        params={'valueInputOption': 'USER_ENTERED'},
        body={'values': values},
    )


def export_all(settings: Settings) -> None:
    """資産クラス別シートと資産推移シートを更新する。"""
    gc = gspread.service_account(filename=settings.client_secret_path)
    workbook = gc.open_by_key(settings.spreadsheet_key)

    for asset in settings.assets:
        csv_path = settings.concat_csv_dir / f'{asset.id}.csv'
        if not csv_path.exists():
            continue
        update_sheet(workbook, asset.sheet_name, csv_path)
        logger.info(f"{asset.sheet_name}: {csv_path}")

    csv_path = settings.csv_dir / ALL_HISTORY_WPL_CSV
    update_sheet(workbook, settings.worksheet_name, csv_path)
    logger.info(f"{settings.worksheet_name}: {csv_path}")
