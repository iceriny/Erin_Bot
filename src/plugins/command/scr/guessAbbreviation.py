import requests
import re


def get_abbreviation(word: str) -> list[str]:
    url = "https://lab.magiconch.com/api/nbnhhsh/guess"
    # headers = {
    #     'origin': 'https://lab.magiconch.com',
    #     'referer': 'https://lab.magiconch.com/nbnhhsh/',
    #     'user-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.163 Safari/537.36',
    # }
    body = {
        "text": word,
    }
    response = requests.post(url, data=body, timeout=5)
    if response.status_code == 200:
        response_list = response.json()
        if len(response_list) == 0:
            return [f"没有找到缩写{word}"]
        guess_result_list: list[str] = response_list[0].get("trans", [])
        return guess_result_list
    else:
        return [f"获取缩写失败，状态码：{response.status_code}"]


class AbbreviationCommandParser:
    def __init__(self, message: str) -> None:
        abbreviation_list: list[str] = re.findall(r"[A-Za-z0-9]+", message, re.I)
        self.abbreviations: dict[str, list[str]] = {abbreviation:[] for abbreviation in abbreviation_list}
        self.str_list = re.split(r"([A-Za-z0-9]+)", message, re.I)
        self.__get_abbreviations_trans()

    def __get_abbreviations_trans(self):
        for abbreviation in self.abbreviations.keys():
            self.abbreviations[abbreviation] += get_abbreviation(abbreviation)


    def __str__(self) -> str:
        result = ""
        for string in self.str_list:
            if string in self.abbreviations.keys():
                result += f"{string}{self.abbreviations[string]}"
            else:
                result += string
        return result
    def __repr__(self) -> str:
        return f"<AbbreviationCommandParser abbreviation_list={self.abbreviations} str_list={self.str_list}>"
