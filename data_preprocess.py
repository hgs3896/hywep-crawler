import re
regrex = re.compile("[월주]?/[\d,]+")

def parse_int(x):
    return int("".join([c for c in x if c.isdigit()]))

def convert_to_monthly_wage(wage_info):
    wage_info = wage_info.strip()

    if regrex.match(wage_info):
        if wage_info[0] == "주":
            return int(30 * parse_int(wage_info) / 7)
        else:
            return parse_int(wage_info)
    else:
        return 0

def preprocess_dataframe(df):
    labels_to_exclude = ["실습신청"]
    labels = [label for label in df.columns if label not in labels_to_exclude]
    df = df[labels]

    df.loc[:, "기관지원금"] = df["기관지원금"].apply(convert_to_monthly_wage)

    df = df.fillna("없음").convert_dtypes()
    df.sort_values(by=['실습기관 진행상태', '기관지원금'], ascending=[False, False], inplace=True)

    df.rename(columns={"기관지원금":"월 기관지원금(원)"}, inplace=True)
    return df