import configparser
from selenium import webdriver


class Moneyforward():
    """
    docstring:hogehoge
    後で書く
    """
    def __init__(self, driver_path="../bin/chromedriver.exe"):
        self.driver = webdriver.Chrome(driver_path)

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


if __name__ == "__main__":
    config_ini = configparser.ConfigParser()
    config_ini.read('config.ini', encoding='utf-8')
    email = config_ini.get('MONEYFORWARD', 'Email')
    password = config_ini.get('MONEYFORWARD', 'Password')

    try:
        mf = Moneyforward()
        mf.login(email=email, password=password)
    except ValueError:
        print("ERROR")