import configparser
import re
import time
from pathlib import Path
from selenium import webdriver
import pandas as pd


class Moneyforward():
    """
    docstring:hogehoge
    後で書く
    """
    def __init__(self, driver_path):
        self.csv_dir = Path("../csv")
        self.csv_dir.mkdir(exist_ok=True)
        options = webdriver.ChromeOptions()
        options.add_experimental_option("prefs", {"download.default_directory": str(self.csv_dir.resolve()) })
        options.add_argument('--no-sandbox')
        self.driver = webdriver.Chrome(executable_path=driver_path, options=options)

    def login(self, email, password):
        login_url = "https://moneyforward.com/sign_in"
        self.driver.get(login_url)
        self.driver.find_element_by_link_text("メールアドレスでログイン").click()
        elem = self.driver.find_element_by_name("mfid_user[email]")
        elem.clear()
        elem.send_keys(email)
        elem.submit()
        elem = self.driver.find_element_by_name("mfid_user[password]")
        elem.clear()
        elem.send_keys(password)
        elem.submit()

    def download_history(self):
        history_url = "https://moneyforward.com/bs/history"
        self.driver.get(history_url)
        elems = self.driver.find_elements_by_xpath('//*[@id="bs-history"]/*/table/tbody/tr/td/a')
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
        # download this month csv
        this_month_csv = "https://moneyforward.com/bs/history/csv"
        save_path = Path(self.csv_dir/"this_month.csv")
        if save_path.exists():
            save_path.unlink()
        self.driver.get(this_month_csv)
        self._rename_latest_file(save_path)
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
        df_concat.sort_index(inplace=True)
        df_concat.fillna(0, inplace=True)
        df_concat.to_csv(Path(self.csv_dir/'all.csv'), encoding="shift-jis")



if __name__ == "__main__":
    config_ini = configparser.ConfigParser()
    config_ini.read('config.ini', encoding='utf-8')
    email = config_ini.get('MONEYFORWARD', 'Email')
    password = config_ini.get('MONEYFORWARD', 'Password')
    driver_path = config_ini.get('CHROME_DRIVER', 'Path')
    try:
        mf = Moneyforward(driver_path=driver_path)
        mf.login(email=email, password=password)
        mf.download_history()
    except ValueError:
        print("ERROR")