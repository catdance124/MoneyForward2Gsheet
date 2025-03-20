import configparser
import sys
import re
import time
import json
import shutil
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
import pandas as pd
import numpy as np
from my_logging import get_my_logger
logger = get_my_logger(__name__)


# GLOBALS
# dir names
ROOT_CSV_DIR = Path('../csv');              ROOT_CSV_DIR  .mkdir(exist_ok=True)
CONCAT_CSV_DIR = ROOT_CSV_DIR / 'concat';   CONCAT_CSV_DIR.mkdir(exist_ok=True)
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
    password : str
        ログイン用パスワード
    csv_dir : Path
        ユーザごとのcsvを保持するルートディレクトリ
    portfolio_dir : Path
        ユーザごとのportfolioに関するcsvを保持するディレクトリ
    history_dir : Path
        ユーザごとのhistoryに関するcsvを保持するディレクトリ
    download_dir : Path
        csvをダウンロードする際に一時保存するディレクトリ
    driver : WebDriver
        seleniumが利用するwebdriver
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
        self.password = password
        self.csv_dir = ROOT_CSV_DIR / email;                self.csv_dir      .mkdir(exist_ok=True)
        self.portfolio_dir = self.csv_dir / 'portfolio';    self.portfolio_dir.mkdir(exist_ok=True)
        self.history_dir = self.csv_dir / 'history';        self.history_dir  .mkdir(exist_ok=True)
        self.download_dir = Path('../download');            self.download_dir .mkdir(exist_ok=True)
        options = webdriver.ChromeOptions()
        options.add_experimental_option('prefs', {
            'download.default_directory': str(self.download_dir.resolve()), 
            'intl.accept_languages': 'ja'
        })
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--lang=ja-JP')
        options.binary_location = "/usr/bin/chromium"
        self.driver = webdriver.Chrome(options=options)
    
    def close(self) -> None:
        """
        webdriverの終了処理を行う。
        """
        self.driver.quit()
        shutil.rmtree(self.download_dir)

    def login(self) -> None:
        """
        MoneyForwardのログイン処理を実施する
        """
        login_url = 'https://moneyforward.com/sign_in'
        self.driver.get(login_url)
        email_input = self.driver.find_element(By.NAME, 'mfid_user[email]')
        email_input.clear()
        email_input.send_keys(self.email)
        email_input.submit()
        time.sleep(3)
        password_input = self.driver.find_element(By.NAME, 'mfid_user[password]')
        password_input.clear()
        password_input.send_keys(self.password)
        password_input.submit()

    def refresh_valuation_profit_and_loss(self, asset_id: str) -> None:
        """
        ローカルの各assetの資産内訳（損益）を最新状態にする

        Parameters
        ----------
        asset_id : str
            html要素の特定に利用するasset_id
        """
        save_path = self.portfolio_dir / f'{asset_id}.csv'
        portfolio_url = 'https://moneyforward.com/bs/portfolio'
        self.driver.get(portfolio_url)
        tables = self.driver.find_elements(By.XPATH, f'//*[@id="{asset_id}"]//table')
        if len(tables) == 0:
            logger.debug(f"no portfolio elements: {asset_id}")
            save_path.unlink(missing_ok=True)
            return
        table = tables[0]
        ths = [th.text for th in table.find_elements(By.XPATH, 'thead//th')]
        trs = table.find_elements(By.XPATH, 'tbody/tr')
        tds = [[td.text for td in tr.find_elements(By.XPATH, 'td')] for tr in trs]
        df = pd.DataFrame(tds, columns=ths)
        df = df.replace(',', '', regex=True).replace('円', '', regex=True)
        df.to_csv(save_path, encoding='utf-8', index=False)
        logger.info(f"Downloaded {save_path}")

    def download_history(self) -> None:
        """
        各月の資産推移を取得する
        """
        history_url = 'https://moneyforward.com/bs/history'
        self.driver.get(history_url)
        anchors = self.driver.find_elements(By.XPATH, '//*[@id="bs-history"]/*/table/tbody/tr/td/a')
        # download previous month csv
        for anchor in anchors:
            href = anchor.get_attribute('href')
            if not 'monthly' in href:
                continue
            month = re.search(r'\d{4}-\d{2}-\d{2}', href).group()
            save_path = self.history_dir / f'{month}.csv'
            if save_path.exists():
                continue
            month_csv = f'https://moneyforward.com/bs/history/list/{month}/monthly/csv'
            self._download_csv(month_csv, save_path)
        # download this month csv
        save_path = self.history_dir / 'this_month.csv'
        save_path.unlink(missing_ok=True)
        this_month_csv = 'https://moneyforward.com/bs/history/csv'
        self._download_csv(this_month_csv, save_path)
        # create concatenated csv
        self._concat_csv()
    
    def reload_accounts(self, reload_wait_time: int = 60) -> None:
        """
        登録されている金融機関の情報を更新する

        Parameters
        ----------
        reload_wait_time: int
            更新ボタン押下後に待機する秒数
        """
        accounts_url = 'https://moneyforward.com/accounts'
        self.driver.get(accounts_url)
        reload_btns = self.driver.find_elements(By.XPATH, '//input[@data-disable-with="更新"]')
        for reload_btn in reload_btns:
            reload_btn.click()
        time.sleep(reload_wait_time)
        trs = self.driver.find_elements(By.XPATH, '//tr[@id]')
        for tr in trs:
            acount_name = tr.find_element(By.XPATH, 'td[@class="service"]/a[starts-with(@href, "/accounts")]').text
            last_obtained_time = tr.find_element(By.XPATH, 'td[@class="created"]/p[last()]').text
            logger.info(f"Last obtained date: {last_obtained_time} | {acount_name}")

    def _download_csv(self, url: str, save_path: Path) -> None:
        """
        指定URLのファイルをダウンロードする

        Parameters
        ----------
        url: str
            保存したいファイルのURL
        save_path : Path
            保存先のパス
        """
        self.driver.get(url)
        self._rename_latest_csv(save_path)
        logger.info(f"Downloaded {save_path}")

    def _rename_latest_csv(self, new_path: Path) -> None:
        """
        ダウンロードディレクトリの最新ファイルをリネームし再配置する
        同時に文字コード変換も実施する

        Parameters
        ----------
        new_path : Path
            新しく保存したいパス
        """
        def _convert_shiftJIS_to_utf8(cp932_csv, utf8_csv):
            with open(cp932_csv, encoding='cp932',errors='replace') as fin:
                with open(utf8_csv, 'w', encoding='utf-8',errors='replace') as fout:
                    fout.write(fin.read())
        time.sleep(2)
        download_files = self.download_dir.glob('*')
        latest_csv = max(download_files, key=lambda p: p.stat().st_ctime)
        _convert_shiftJIS_to_utf8(latest_csv, new_path)
        latest_csv.unlink(missing_ok=True)
    
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
    config_ini = configparser.ConfigParser()
    config_ini.read('config.ini', encoding='utf-8')
    emails = json.loads(config_ini.get('MONEYFORWARD','Email'))
    passwords = json.loads(config_ini.get('MONEYFORWARD','Password'))
    assets = [dict(config_ini.items(section)) for section in config_ini.sections() if 'asset_' in section]
    reload_wait_time = int(config_ini.get('MONEYFORWARD','Reload_wait_time'))
    
    # download each files
    for email, password in zip(emails, passwords):
        mf = Moneyforward(email=email, password=password)
        try:
            mf.login()
            mf.reload_accounts(reload_wait_time)
            mf.download_history()
            for asset_id in [asset['id'] for asset in assets]:
                mf.refresh_valuation_profit_and_loss(asset_id)
            mf.calc_profit_and_loss(assets)
        except Exception as e:
            logger.error(e)
            sys.exit(1)
        finally:
            mf.close()
    
    # concat each files
    new_all_history_wpl = concat_each_account_files(assets)
    new_all_history_wpl.reset_index(inplace=True)

    # generate result csv
    all_history_wpl_csv_path = ROOT_CSV_DIR / ALL_HISTORY_WPL_CSV
    old_all_history_wpl = pd.read_csv(all_history_wpl_csv_path, encoding='utf-8', sep=',') if all_history_wpl_csv_path.exists() else new_all_history_wpl
    df_merged_newer = my_set_index(pd.merge(new_all_history_wpl, old_all_history_wpl, how='outer')).sort_index(axis='columns')
    df_merged_older = my_set_index(pd.merge(old_all_history_wpl, new_all_history_wpl, how='outer')).sort_index(axis='columns')
    # newerの損益値が0の場合はolderの値を採用
    for asset in assets:
        column_name = asset['column_name']
        if column_name == '':
            continue
        df_merged_newer[column_name] = np.where(df_merged_newer[column_name] == 0, df_merged_older[column_name], df_merged_newer[column_name])
    df_merged_newer.to_csv(all_history_wpl_csv_path, encoding='utf-8')


if __name__ == '__main__':
    main()
