from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from time import sleep
import os
import argparse
import json
import time
from PIL import Image
from io import BytesIO
import pytesseract
import base64
import shutil
import smtplib
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr
import io
import sys
from functools import partial
from datetime import datetime, timedelta, timezone

username = None
password = None
mail_user = None
mail_pass = None

def login(driver):
    try:
        driver.get("https://www.easonfans.com/FORUM/member.php?mod=logging&action=login")

        verify_img = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CLASS_NAME, "verifyimg"))
        )

        img_url = verify_img.get_attribute("src")
        base64_data = img_url.split(',')[1]
        image_data = base64.b64decode(base64_data)
        image = Image.open(BytesIO(image_data))

        code = pytesseract.image_to_string(image)
        time.sleep(0.5)

        input_box = driver.find_element(By.ID, "intext")
        input_box.send_keys(code)

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "username"))
        )
        driver.find_element(By.NAME, "username").send_keys(username)
        driver.find_element(By.NAME, "password").send_keys(password)
        driver.find_element(By.NAME, "loginsubmit").click()

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "umLogin"))
        )
        print("登录成功！")
        return True
    except Exception as e:
        print(f"登录过程中出现错误")
        return False

def signin(driver):
    driver.get("https://www.easonfans.com/forum/plugin.php?id=dsu_paulsign:sign")
    
    try:
        badge_element = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, "fwin_badgewin_7ree"))
        )
        if badge_element:
            print("徽章弹窗出现，准备领取徽章。")
            driver.get("https://www.easonfans.com/forum/plugin.php?id=badge_7ree:badge_7ree&code=1")
            button = driver.find_element("css selector", 'a[href*="plugin.php?id=badge_7ree"]')
            before_click_content = driver.page_source
            button.click()
            WebDriverWait(driver, 5).until(EC.staleness_of(badge_element))
            after_click_content = driver.page_source
            if before_click_content != after_click_content:
                print("徽章领取成功！")
            else:
                print("徽章领取失败。")
    except TimeoutException:
        print("没有徽章弹窗。")
    
    driver.get("https://www.easonfans.com/forum/plugin.php?id=dsu_paulsign:sign")
    
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//h1[contains(text(), '您今天已经签到过了或者签到时间还未开始')]"))
        )
        print("今天已签到或签到未开始。")
    except TimeoutException:
        try:
            WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//a[@onclick=\"showWindow('qwindow', 'qiandao', 'post', '0');return false\"]"))
            )
            driver.find_element(By.ID, "kx").click()
            driver.find_element(By.CSS_SELECTOR, "input[type='radio'][name='qdmode'][value='3']").click()
            driver.find_element(By.XPATH, "//a[@onclick=\"showWindow('qwindow', 'qiandao', 'post', '0');return false\"]").click()

            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//h1[contains(text(), '您今天已经签到过了或者签到时间还未开始')]"))
                )
                print("签到成功！")
            except TimeoutException:
                print("签到失败。")
        except Exception as e:
            print(f"签到过程中出现错误。")

def check_free_lottery(driver):
    driver.get("https://www.easonfans.com/forum/plugin.php?id=gplayconstellation:front")
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//span[contains(text(), '今日剩余免费次数：0次')]"))
        )
        return False
    except:
        return True

def lottery(driver):
    if not check_free_lottery(driver):
        print("今天已免费抽奖。")
        return

    try:
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "pointlevel"))
        ).click()
        print("开始免费抽奖。")
        sleep(5)
        if not check_free_lottery(driver):
            print("免费抽奖成功！")
        else:
            print("免费抽奖失败。")
    except Exception as e:
        print(f"抽奖过程中出现错误。")

def getMoney(driver):
    driver.get("https://www.easonfans.com/forum/home.php?mod=spacecp&ac=credit&showcredit=1")
    try:
        money_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//li[@class='xi1 cl']"))
        )
        money_text = money_element.text
        money_amount = [int(s) for s in money_text.split() if s.isdigit()][0]
        return money_amount
    except Exception as e:
        print(f"获取金钱失败。")
        return 0
    
def sendEmail(msg):
    sender = receiver = mail_user
    message = MIMEText(msg, 'plain', 'utf-8')
    message['From'] = formataddr(("Daily mission Assitance", sender))
    message['To'] = formataddr(("Tanner", receiver))
    message['Subject'] = Header('签到脚本运行报告', 'utf-8')
    try:
        server=smtplib.SMTP_SSL("smtp.qq.com", 465)
        server.login(mail_user,mail_pass)  
        server.sendmail(sender,[receiver],message.as_string())
        print ("邮件发送成功。")
        server.quit()
    except smtplib.SMTPException as e:
        print(f"邮件发送失败。")

def capture_output(func):
    buffer = io.StringIO()
    sys.stdout = buffer
    func()
    sys.stdout = sys.__stdout__
    return buffer.getvalue()
    
def merge(headless: bool, local: bool, chromedriver_path: str):
    global username, password
    chrome_options = webdriver.ChromeOptions()
    if headless:
        chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    
    service = Service(executable_path=chromedriver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)

    beijing_tz = timezone(timedelta(hours=8))
    now_str = datetime.now(beijing_tz).strftime("%Y-%m-%d %H:%M:%S")
    print(f"=== Script for {username} started at {now_str} {'locally' if local else 'remotely'} ===")

    login_success = False
    while not login_success:
        login_success = login(driver)
        if not login_success:
            print("重新尝试登录...")
            sleep(5)
            
    initial_money = getMoney(driver)
    signin(driver)
    lottery(driver)
    final_money = getMoney(driver)
    print(f"金钱变化：{initial_money} -> {final_money}。")
    driver.quit()

def main():
    global username, password, mail_user, mail_pass

    parser = argparse.ArgumentParser()
    parser.add_argument('--local', action='store_true')
    parser.add_argument('--headless', action='store_true')
    args = parser.parse_args()

    try:
        if args.local:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            linux_driver_dir = os.path.join(base_dir, "chromedriver-linux64")
            win_driver_dir = os.path.join(base_dir, "chromedriver-win64")

            if os.path.exists(linux_driver_dir):
                chromedriver_path = os.path.join(linux_driver_dir, "chromedriver")
            elif os.path.exists(win_driver_dir):
                chromedriver_path = os.path.join(win_driver_dir, "chromedriver.exe")
            else:
                raise FileNotFoundError("未找到 chromedriver 路径")
            
            config_path = os.path.join(base_dir, "config.json")
            with open(config_path, 'r') as f:
                config = json.load(f)
            username = config['USERNAME']
            password = config['PASSWORD']
            mail_user = config['MAIL_USERNAME']
            mail_pass = config['MAIL_PASSWORD']
        else:
            chromedriver_path = shutil.which("chromedriver")
            username = os.environ['USERNAME']
            password = os.environ['PASSWORD']
            mail_user = os.environ['MAIL_USERNAME']
            mail_pass = os.environ['MAIL_PASSWORD']
    except KeyError as e:
        raise Exception(f"Missing required configuration: {e}")

    merge_fn = partial(merge, headless=args.headless, local=args.local, chromedriver_path=chromedriver_path)
    output_message = capture_output(merge_fn)
    sendEmail(output_message)

if __name__ == '__main__':
    main()
