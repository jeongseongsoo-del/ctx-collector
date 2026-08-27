import re
from typing import Any, Dict

from bs4 import BeautifulSoup


def parse_spec_from_html(html: str) -> Dict[str, Any]:
    soup = BeautifulSoup(html, "html.parser")
    result: Dict[str, Any] = {}

    for row in soup.find_all("tr"):
        tds = row.find_all("td")
        if len(tds) >= 2:
            key = re.sub(r"\s+", "", tds[0].get_text())
            value = ""
            buttons = tds[1].find_all("button")
            if buttons:
                for btn in buttons:
                    if btn.get("data-active") == "Y":
                        value = re.sub(r"\s+", "", btn.get_text())
                        break
            else:
                value = re.sub(r"\s+", "", tds[1].get_text())
            result[key] = value
    return result


def parse_table_trs(html: str) -> Dict[str, Any]:
    soup = BeautifulSoup(html, "html.parser")
    result: Dict[str, Any] = {}

    for row in soup.find_all("tr"):
        tds = row.find_all("td")
        if len(tds) >= 2:
            key = re.sub(r"\s+", "", tds[0].get_text())
            value_text = re.sub(r"\s+", "", tds[1].get_text()).replace("￦", "").replace(",", "")
            try:
                value = int(value_text)
            except ValueError:
                value = value_text
            result[key] = value
    return result


def clean_html_for_detail_page(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(["style", "script"]):
        tag.decompose()

    for hr in soup.find_all("hr"):
        hr.replace_with(soup.new_tag("div", style="border-top:1px solid #ccc;margin:20px 0;"))

    cleaned_html = re.sub(r"\s+", " ", str(soup)).strip()
    return cleaned_html
