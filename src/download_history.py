import configparser
import re
import time
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from subprocess import CREATE_NO_WINDOW
import pandas as pd


class Moneyforward():
    """
    docstring:hogehoge
    後で書く
    """
    def __init__(self):
        self.csv_dir = Path("../csv")
        self.csv_dir.mkdir(exist_ok=True)
        options = webdriver.ChromeOptions()
        options.add_experimental_option("prefs", {"download.default_directory": str(self.csv_dir.resolve())})
        options.add_argument("--no-sandbox")
        service = Service(ChromeDriverManager().install())
        service.creationflags = CREATE_NO_WINDOW
        self.driver = webdriver.Chrome(service=service, options=options)
    
    def close(self):
        self.driver.quit()

    def login(self, email, password):
        login_url = "https://moneyforward.com/sign_in"
        self.driver.get(login_url)
        self.driver.find_element(By.LINK_TEXT, "メールアドレスでログイン").click()
        elem = self.driver.find_element(By.NAME, "mfid_user[email]")
        elem.clear()
        elem.send_keys(email)
        elem.submit()
        time.sleep(3)
        elem = self.driver.find_element(By.NAME, "mfid_user[password]")
        elem.clear()
        elem.send_keys(password)
        elem.submit()
    
    def get_valuation_profit_and_loss_multiple(self, asset_id_list):
        for asset_id in asset_id_list:
            self.get_valuation_profit_and_loss(asset_id)

    def get_valuation_profit_and_loss(self, asset_id):
        portfolio_url = "https://moneyforward.com/bs/portfolio"
        self.driver.get(portfolio_url)
        elems = self.driver.find_elements(By.XPATH, f'//*[@id="{asset_id}"]//table')
        if len(elems) == 0:
            raise "no portfolio elements"
        elem = elems[0]
        ths = [th.text for th in elem.find_elements(By.XPATH, "thead//th")]
        trs = elem.find_elements(By.XPATH, "tbody/tr")
        tds = [[td.text for td in tr.find_elements(By.XPATH, "td")] for tr in trs]
        df = pd.DataFrame(tds, columns=ths)
        portfolio_dir = Path(self.csv_dir/'portfolio')
        portfolio_dir.mkdir(exist_ok=True)
        save_path = Path(portfolio_dir/f'{asset_id}.csv')
        df.to_csv(save_path, encoding="shift-jis")
        print(f"Downloaded {save_path}")

    def download_history(self):
        history_url = "https://moneyforward.com/bs/history"
        self.driver.get(history_url)
        elems = self.driver.find_elements(By.XPATH, '//*[@id="bs-history"]/*/table/tbody/tr/td/a')
        # download previous month csv
        for elem in elems:
            href = elem.get_attribute("href")
            if "monthly" in href:
                month = re.search(r'\d{4}-\d{2}-\d{2}', href).group()
                save_path = Path(self.csv_dir/f"{month}.csv")
                if not save_path.exists():
                    month_csv = f"https://moneyforward.com/bs/history/list/{month}/monthly/csv"
                    self.driver.get(month_csv)
                    self._rename_latest_file(save_path)
                    print(f"Downloaded {save_path}")
        # download this month csv
        this_month_csv = "https://moneyforward.com/bs/history/csv"
        save_path = Path(self.csv_dir/"this_month.csv")
        if save_path.exists():
            save_path.unlink()
        self.driver.get(this_month_csv)
        self._rename_latest_file(save_path)
        print(f"Downloaded {save_path}")
        # create concatenated csv -> all.csv
        self._concat_csv()

    def _rename_latest_file(self, new_path):
        time.sleep(2)
        csv_list = self.csv_dir.glob('*[!all].csv')
        latest_csv = max(csv_list, key=lambda p: p.stat().st_ctime)
        latest_csv.rename(new_path)
    
    def _concat_csv(self):
        csv_list = sorted(self.csv_dir.glob('*[!all].csv'))
        df_list = []
        for csv_path in csv_list:
            df = pd.read_csv(csv_path, encoding="shift-jis", sep=',')
            df_list.append(df)
        df_concat = pd.concat(df_list)
        df_concat.drop_duplicates(subset='日付', inplace=True)
        df_concat.set_index('日付', inplace=True)
        df_concat.sort_index(inplace=True, ascending=False)
        df_concat.fillna(0, inplace=True)
        df_concat.to_csv(Path(self.csv_dir/'all.csv'), encoding="shift-jis")


def main():
    config_ini = configparser.ConfigParser()
    config_ini.read('config.ini', encoding='utf-8')
    email = config_ini.get('MONEYFORWARD', 'Email')
    password = config_ini.get('MONEYFORWARD', 'Password')
    assets = [dict(config_ini.items(section)) for section in config_ini.sections() if "asset_" in section]
    
    mf = Moneyforward()
    try:
        mf.login(email=email, password=password)
        mf.download_history()
        mf.get_valuation_profit_and_loss_multiple(asset_id_list=[asset['id'] for asset in assets])
    finally:
        mf.close()

if __name__ == "__main__":
    main()
