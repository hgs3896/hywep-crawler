import pandas as pd
import logging

from data_preprocess import preprocess_dataframe
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, NoAlertPresentException
from selenium.webdriver.common.keys import Keys

logging.basicConfig(filename="hywep_crawler.log", level=logging.INFO)

class HywepCrawler:
    def __init__(self, driver):
        self.driver = driver

    def closeOtherWindows(self, original_window):
        # Wait for the new window or tab
        # WebDriverWait(driver, 3).until(EC.number_of_windows_to_be(2))

        # Loop through until we find a new window handle
        for window_handle in self.driver.window_handles:
            if window_handle != original_window:
                self.driver.switch_to.window(window_handle)
                self.driver.close()
                self.driver.switch_to.window(original_window)

        return "success"

    def login(self, id, pw):
        WebDriverWait(self.driver, 3).until(EC.presence_of_element_located((By.CSS_SELECTOR, "#wrap > div.visual_area.main_visual > div:nth-child(1) > div > div > div.cnt.on > form > a > button")))
        btn_to_login_page = self.driver.find_element(By.CSS_SELECTOR, "#wrap > div.visual_area.main_visual > div:nth-child(1) > div > div > div.cnt.on > form > a > button")

        if not btn_to_login_page:
            return "cannot access to login page"

        btn_to_login_page.click()

        user_id = self.driver.find_element(By.CSS_SELECTOR, "#uid")
        user_pw = self.driver.find_element(By.CSS_SELECTOR, "#upw")
        login_btn = self.driver.find_element(By.CSS_SELECTOR, "#login_btn")

        if not user_id:
            print("ID 입력란을 찾을 수 없습니다")
            return "user_id not found"
        if not user_pw:
            print("PW 입력란을 찾을 수 없습니다")
            return "password is empty"
        if not login_btn:
            print("로그인 버튼을 찾을 수 없습니다")
            return "login_btn not found"

        user_id.send_keys(id)
        user_pw.send_keys(pw)
        login_btn.click()

        try:
            self.driver.switch_to.alert.accept()
        except NoAlertPresentException:
            pass

        return "success"

    def naigate_organizations(self):
        WebDriverWait(self.driver, 1).until(EC.presence_of_element_located((By.CSS_SELECTOR, "#navWrapper > li:nth-child(2) > a")))

        # 실습기관 조회/실습 신청 클릭
        self.driver.find_element(By.CSS_SELECTOR, "#navWrapper > li:nth-child(2) > a").click()
        # 실습 기간 목록 아이템
        hywep_list = self.driver.find_elements(By.CSS_SELECTOR, "#mainForm > div.tabs > ul > li")

        hywep_kinds = [item.text.strip().replace("\n", " ") for item in hywep_list]

        return hywep_kinds

    def crawl(self, idx):
        WebDriverWait(self.driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "#mainForm > div.tabs > ul > li")))
        hywep_period = self.driver.find_elements(By.CSS_SELECTOR, "#mainForm > div.tabs > ul > li")[idx]
        hywep_period.click()

        table_col_info = self.driver.find_elements(
            By.CSS_SELECTOR,
            "#contents > div > div.table_area.table_size.long_t > table > thead > tr > th"
        )
        table_col_names = [item.text.strip().replace("\n", " ") for item in table_col_info]

        homepage_col_idx = table_col_names.index("홈페이지")
        df = pd.DataFrame(columns=table_col_names)

        row_cnt = 1

        while True:
            try:
                # logging.info("현재 페이지 탐색중")
                # current_page = self.driver.find_element(
                #     By.CSS_SELECTOR, "#contents > div > div.table_area.table_size.long_t > div > a.on")
                # logging.info("현재 페이지 존재함")

                WebDriverWait(self.driver, 1).until(EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, "#contents > div > div.table_area.table_size.long_t > table > tbody > tr")))

                table_rows = self.driver.find_elements(
                    By.CSS_SELECTOR, "#contents > div > div.table_area.table_size.long_t > table > tbody > tr")
                
                for row in table_rows:
                    record = []
                    for col_idx, col in enumerate(row.find_elements(By.CSS_SELECTOR, "td")):
                        if col_idx >= len(table_col_info):
                            break

                        if col_idx == homepage_col_idx:
                            try:
                                a_tag = col.find_element(By.TAG_NAME, "a")
                                homepage_address = a_tag.get_attribute("onclick")
                                l = homepage_address.find("'")
                                r = homepage_address.rfind("'")
                                record.append(homepage_address[l+1:r])
                            except NoSuchElementException:
                                record.append("")
                        else:
                            record.append(col.text.strip().replace("\n", " "))
                    record[0] = row_cnt
                    df.loc[row_cnt] = record
                    row_cnt += 1

                logging.info("다음 페이지 탐색중")
                try:
                    next_page_btn = self.driver.find_element(
                        By.CSS_SELECTOR, "#contents > div > div.table_area.table_size.long_t > div > a.on + a")
                except NoSuchElementException:
                    logging.info(f"[다음 페이지를 찾을 수 없음]")
                    break
                logging.info("다음 페이지 존재함")
                next_page_btn.send_keys(Keys.ENTER)
                logging.info("다음 페이지 누름")

            except Exception as e:
                logging.error(f"[에러 발생] {e}")
                break

            logging.info(f"[크롤링 종료]")

        logging.info(f"[크롤링한 데이터 전처리 시작]")
        df = preprocess_dataframe(df)
        logging.info(f"[크롤링한 데이터 전처리 완료]")
        return df