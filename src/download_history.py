import configparser
import re
import time
import json
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import numpy as np
from my_logging import get_my_logger
logger = get_my_logger(__name__)

root_csv_dir = Path("../csv")

class Moneyforward():
    """
    Moneyforwardから各種情報を取得する
    - download_history
        - 資産推移を取得
    - get_valuation_profit_and_loss
        - 資産内訳（損益）を取得
    - calc_profit_and_loss
        - 資産推移と資産内訳（損益）を結合
    """
    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.csv_dir = root_csv_dir / email
        self.csv_dir.mkdir(exist_ok=True, parents=True)
        self.portfolio_dir = self.csv_dir / 'portfolio'
        self.portfolio_dir.mkdir(exist_ok=True)
        self.download_dir = Path("../download")
        self.download_dir.mkdir(exist_ok=True)
        options = webdriver.ChromeOptions()
        options.add_experimental_option("prefs", {"download.default_directory": str(self.download_dir.resolve())})
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        self.driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)
    
    def close(self):
        self.driver.quit()

    def login(self):
        login_url = "https://moneyforward.com/sign_in"
        self.driver.get(login_url)
        self.driver.find_element(By.LINK_TEXT, "メールアドレスでログイン").click()
        elem = self.driver.find_element(By.NAME, "mfid_user[email]")
        elem.clear()
        elem.send_keys(self.email)
        elem.submit()
        time.sleep(3)
        elem = self.driver.find_element(By.NAME, "mfid_user[password]")
        elem.clear()
        elem.send_keys(self.password)
        elem.submit()
    
    def get_valuation_profit_and_loss_multiple(self, asset_id_list):
        for asset_id in asset_id_list:
            self.get_valuation_profit_and_loss(asset_id)

    def get_valuation_profit_and_loss(self, asset_id):
        portfolio_url = "https://moneyforward.com/bs/portfolio"
        self.driver.get(portfolio_url)
        elems = self.driver.find_elements(By.XPATH, f'//*[@id="{asset_id}"]//table')
        if len(elems) == 0:
            logger.info(f"no portfolio elements: {asset_id}")
            return
        elem = elems[0]
        ths = [th.text for th in elem.find_elements(By.XPATH, "thead//th")]
        trs = elem.find_elements(By.XPATH, "tbody/tr")
        tds = [[td.text for td in tr.find_elements(By.XPATH, "td")] for tr in trs]
        df = pd.DataFrame(tds, columns=ths)
        save_path = self.portfolio_dir / f'{asset_id}.csv'
        df.to_csv(save_path, encoding="utf-8", index=False)
        logger.info(f"Downloaded {save_path}")

    def download_history(self):
        history_url = "https://moneyforward.com/bs/history"
        self.driver.get(history_url)
        elems = self.driver.find_elements(By.XPATH, '//*[@id="bs-history"]/*/table/tbody/tr/td/a')
        # download previous month csv
        for elem in elems:
            href = elem.get_attribute("href")
            if "monthly" in href:
                month = re.search(r'\d{4}-\d{2}-\d{2}', href).group()
                save_path = self.csv_dir / f"{month}.csv"
                if not save_path.exists():
                    month_csv = f"https://moneyforward.com/bs/history/list/{month}/monthly/csv"
                    self.driver.get(month_csv)
                    self._rename_latest_file(save_path)
                    logger.info(f"Downloaded {save_path}")
        # download this month csv
        this_month_csv = "https://moneyforward.com/bs/history/csv"
        save_path = self.csv_dir / "this_month.csv"
        if save_path.exists():
            save_path.unlink()
        self.driver.get(this_month_csv)
        self._rename_latest_file(save_path)
        logger.info(f"Downloaded {save_path}")
        # create concatenated csv -> all.csv
        self._concat_csv()

    def _rename_latest_file(self, new_path):
        def _convert_shiftJIS_to_utf8(cp932_csv, utf8_csv):
            with open(cp932_csv, encoding='cp932',errors='replace') as fin:
                with open(utf8_csv, 'w', encoding='utf-8',errors='replace') as fout:
                    fout.write(fin.read())
        time.sleep(2)
        download_files = self.download_dir.glob('*')
        latest_csv = max(download_files, key=lambda p: p.stat().st_ctime)
        _convert_shiftJIS_to_utf8(latest_csv, new_path)
        latest_csv.unlink()
    
    def _concat_csv(self):
        csv_list = sorted(self.csv_dir.glob('*[!all].csv'))
        df_list = []
        for csv_path in csv_list:
            df = pd.read_csv(csv_path, encoding="utf-8", sep=',')
            df_list.append(df)
        df_concat = pd.concat(df_list)
        df_concat.drop_duplicates(subset='日付', inplace=True)
        df_concat.set_index('日付', inplace=True)
        df_concat.sort_index(inplace=True, ascending=False)
        df_concat.fillna(0, inplace=True)
        df_concat = df_concat.add_prefix(':')
        df_concat.to_csv(self.csv_dir / 'all.csv', encoding="utf-8")

    def calc_profit_and_loss(self, assets):
        df_all_org = pd.read_csv(self.csv_dir / "all.csv", encoding="utf-8", sep=',')
        csv_path = self.portfolio_dir / "portfolio_all.csv"
        if csv_path.exists():
            df_merged = pd.read_csv(csv_path, encoding="utf-8", sep=',')
        else:
            df_merged = df_all_org
        df_merged = pd.merge(df_all_org, df_merged, how='left')
        df_merged.drop_duplicates(subset='日付', inplace=True)
        df_merged.set_index('日付', inplace=True)
        portfolio_sets = [[asset['column_name'], self.portfolio_dir / f"{asset['id']}.csv"] for asset in assets if asset['column_name'] != '']
        for portfolio_set in portfolio_sets:
            column_name, portfolio_csv_path = portfolio_set
            if not portfolio_csv_path.exists():
                continue
            df_tmp = pd.read_csv(portfolio_csv_path, encoding="utf-8", sep=',')
            df_tmp = df_tmp.dropna(subset=['評価損益'])
            df_tmp['評価損益'] = df_tmp['評価損益'].apply(lambda x: x.strip('円') if '円' in x else x).str.replace(',','').astype(np.int)
            profit_and_loss = df_tmp['評価損益'].sum()
            if not column_name in df_merged.columns:
                df_merged[column_name] = 0
            df_merged.at[df_merged.index[0], column_name] = profit_and_loss
        df_merged.to_csv(csv_path, encoding="utf-8")


def concat_files(assets):
    concat_csv_dir = root_csv_dir / "concat"
    concat_csv_dir.mkdir(exist_ok=True, parents=True)
    ## asset files
    for asset in assets:
        df_list = []
        for asset_csv_path in root_csv_dir.glob(f"*/portfolio/{asset['id']}.csv"):
            df = pd.read_csv(asset_csv_path, encoding="utf-8", sep=',')
            df_list.append(df)
        df_concat = pd.concat(df_list)
        df_concat.to_csv(concat_csv_dir / f"{asset['id']}.csv", encoding="utf-8", index=False)
    ## history files
    output_path = concat_csv_dir / "portfolio_all.csv"
    df_concat = None
    for portfolio_all_csv_path in root_csv_dir.glob(f"*/portfolio/portfolio_all.csv"):
        df = pd.read_csv(portfolio_all_csv_path, encoding="utf-8", sep=',')
        df.set_index('日付', inplace=True)
        df_concat = df_concat.add(df, fill_value=0) if df_concat is not None else df
    df_concat.sort_index(inplace=True, ascending=False)
    df_concat.to_csv(output_path, encoding="utf-8")
    return output_path


def main():
    config_ini = configparser.ConfigParser()
    config_ini.read('config.ini', encoding='utf-8')
    emails = json.loads(config_ini.get("MONEYFORWARD","Email"))
    passwords = json.loads(config_ini.get("MONEYFORWARD","Password"))
    assets = [dict(config_ini.items(section)) for section in config_ini.sections() if "asset_" in section]
    
    # download each files
    for email, password in zip(emails, passwords):
        mf = Moneyforward(email=email, password=password)
        try:
            mf.login()
            mf.download_history()
            mf.get_valuation_profit_and_loss_multiple(asset_id_list=[asset['id'] for asset in assets])
            mf.calc_profit_and_loss(assets)
        finally:
            mf.close()
    
    # concat each files
    new_portfolio_all_csv_path = concat_files(assets)
    new_portfolio_all = pd.read_csv(new_portfolio_all_csv_path, encoding="utf-8", sep=',')

    # generate result csv
    portfolio_all_csv_path = root_csv_dir / "portfolio_all.csv"
    if portfolio_all_csv_path.exists():
        portfolio_all = pd.read_csv(portfolio_all_csv_path, encoding="utf-8", sep=',')
    else:
        portfolio_all = new_portfolio_all
    portfolio_all = pd.merge(new_portfolio_all, portfolio_all, how='outer')
    portfolio_all.drop_duplicates(subset='日付', inplace=True)
    portfolio_all.set_index('日付', inplace=True)
    portfolio_all.sort_index(inplace=True, axis='columns')
    portfolio_all.sort_index(inplace=True, ascending=False)
    portfolio_all.to_csv(portfolio_all_csv_path, encoding="utf-8")


if __name__ == "__main__":
    main()
