"""コマンドラインエントリポイント。

プロジェクトルート(config.ini / .env / client_secret.json のある場所)で実行する:

    uv run mf2gs            # download + export
    uv run mf2gs download   # 取得と集約のみ
    uv run mf2gs export     # シート転記のみ
"""

from __future__ import annotations

import argparse
import logging
import sys

from .config import Settings, load_settings
from .download import download_all
from .export import export_all

logger = logging.getLogger(__name__)


def setup_logging(settings: Settings) -> None:
    """コンソール(INFO)とログファイル(log/log、INFO)に出力する。"""
    settings.log_dir.mkdir(exist_ok=True)
    file_handler = logging.FileHandler(settings.log_dir / 'log')
    file_handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] [%(name)s] %(message)s'))
    logging.basicConfig(level=logging.INFO, handlers=[logging.StreamHandler(), file_handler])
    # HTTPクライアントの低レベルログは冗長なので抑制する
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('httpcore').setLevel(logging.WARNING)


def main() -> None:
    parser = argparse.ArgumentParser(prog='mf2gs', description=__doc__)
    parser.add_argument('command', nargs='?', choices=['download', 'export'],
                        help='省略時は download と export を続けて実行する')
    args = parser.parse_args()

    settings = load_settings()
    setup_logging(settings)
    logger.info(f"START SCRIPT {'='*10}")
    try:
        if args.command in (None, 'download'):
            download_all(settings)
        if args.command in (None, 'export'):
            export_all(settings)
    except Exception as e:
        logger.exception(e)
        sys.exit(1)
    logger.info(f"END SCRIPT {'='*10}")


if __name__ == '__main__':
    main()
