import sys
import os
from crawler import HywepCrawler
from selenium import webdriver
from selenium.common.exceptions import NoSuchDriverException

if __name__ == "__main__":
    id, pw = '', ''

    if len(sys.argv) >= 3:
        id = sys.argv[1]
        pw = sys.argv[2]

    if not id and pw:
        print('사용방법: python main.py [한양인 id] [한양인 pw]')
        sys.exit(0)

    try:
        driver = webdriver.Chrome()
        driver.get("https://hywep.hanyang.ac.kr/index.do")

        # Store the ID of the original window
        original_window = driver.current_window_handle

        crawler = HywepCrawler(driver)

        if crawler.closeOtherWindows(original_window) != "success":
            print("Cannot close other windows")
            sys.exit(-1)

        if crawler.login(id, pw) != "success":
            print("Cannot login")
            sys.exit(-1)

        hywep_kinds = crawler.naigate_organizations()
        if not hywep_kinds:
            print("Nothing to crawl")
            sys.exit(-1)

        print("어떤 항목을 크롤링할까요?")
        for idx, hywep_kind in enumerate(hywep_kinds, 1):
            print(f"{idx:2d}. {hywep_kind}")

        selected_idx = -1
        while True:
            try:
                selected_idx = int(input("번호를 입력하세요: "))
                if selected_idx >= 1 and selected_idx <= len(hywep_kinds):
                    break
            except ValueError:
                pass
            print("잘못된 번호입니다. 다시 입력하세요")
        print(f"{selected_idx}. {hywep_kinds[selected_idx - 1]}를 선택하셨습니다.")

        df = crawler.crawl(selected_idx - 1)

        filename = f"{hywep_kinds[selected_idx - 1]}.xlsx"
        sheet_name = hywep_kinds[selected_idx - 1]
        if len(sheet_name) > 31:
            sheet_name = f"{sheet_name[:28]}..."

        df.to_excel(
            excel_writer=filename,
            sheet_name=sheet_name,
            startrow=1, startcol=1,
            engine='xlsxwriter',
            index=False
        )
        print(f"{filename}으로 저장되었습니다")

    except NoSuchDriverException as e:
        print(f"예상 위치인 {driver_path}에서 Chrome driver를 찾을 수 없습니다")
        sys.exit(-1)