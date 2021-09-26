import configparser
import re
from pathlib import Path
from selenium import webdriver


class Moneyforward():
    """
    docstring:hogehoge
    後で書く
    """
    def __init__(self, driver_path="../bin/chromedriver.exe"):
        csv_dir = Path("../csv")
        csv_dir.mkdir(exist_ok=True)
        options = webdriver.ChromeOptions()
        options.add_experimental_option("prefs", {"download.default_directory": str(csv_dir.resolve()) })
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
        for elem in elems:
            href = elem.get_attribute("href")
            if "monthly" in href:
                month = re.search(r'\d{4}-\d{2}-\d{2}', href).group()
                month_csv = f"https://moneyforward.com/bs/history/list/{month}/monthly/csv"
                self.driver.get(month_csv)
        this_month_csv = "https://moneyforward.com/bs/history/csv"
        self.driver.get(this_month_csv)


if __name__ == "__main__":
    config_ini = configparser.ConfigParser()
    config_ini.read('config.ini', encoding='utf-8')
    email = config_ini.get('MONEYFORWARD', 'Email')
    password = config_ini.get('MONEYFORWARD', 'Password')
    try:
        mf = Moneyforward()
        mf.login(email=email, password=password)
        mf.download_history()
    except ValueError:
        print("ERROR")