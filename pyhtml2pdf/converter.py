import json
import base64
import io
from typing import Union, TypedDict

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.expected_conditions import staleness_of
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

from .compressor import __compress


class PrintOptions(TypedDict):
    landscape: bool
    displayHeaderFooter: bool
    printBackground: bool
    scale: float
    paperWidth: float
    paperHeight: float
    marginTop: float
    marginBottom: float
    marginLeft: float
    marginRight: float
    pageRanges: str
    ignoreInvalidPageRanges: bool
    preferCSSPageSize: bool


def convert(
    source: Union[str, io.BytesIO],
    target: Union[str, io.BytesIO],
    timeout: int = 2,
    compress: bool = False,
    power: int = 0,
    install_driver: bool = True,
    print_options: PrintOptions = {},
):
    """
    Convert a given html file or website into PDF

    :param str source: source html file or website link or html content or a BytesIO object
    :param str | BytesIO target: target location to save the PDF, can be a path or a BytesIO object
    :param int timeout: timeout in seconds. Default value is set to 2 seconds
    :param bool compress: whether PDF is compressed or not. Default value is False
    :param int power: power of the compression. Default value is 0. This can be 0: default, 1: prepress, 2: printer, 3: ebook, 4: screen
    :param bool install_driver: whether or not to install using ChromeDriverManager. Default value is True
    :param PrintOptions print_options: A dictionary containing options for the printing of the PDF, conforming to the types specified in the PrintOptions TypedDict.
    """

    result = __get_pdf_from_html(
        source, timeout, install_driver, print_options)

    if compress:
        __compress(result, target, power)
    else:
        if type(target) == io.BytesIO:
            return target.write(result)
        with open(target, "wb") as file:
            file.write(result)


def __send_devtools(driver, cmd, params={}):
    resource = "/session/%s/chromium/send_command_and_get_result" % driver.session_id
    url = driver.command_executor._url + resource
    body = json.dumps({"cmd": cmd, "params": params})
    response = driver.command_executor._request("POST", url, body)

    if not response:
        raise Exception(response.get("value"))

    return response.get("value")


def __get_pdf_from_html(
    source: Union[str, io.BytesIO], timeout: int, install_driver: bool, print_options: dict
):
    webdriver_options = Options()
    webdriver_prefs = {}
    driver = None

    webdriver_options.add_argument("--headless")
    webdriver_options.add_argument("--disable-gpu")
    webdriver_options.add_argument("--no-sandbox")
    webdriver_options.add_argument("--disable-dev-shm-usage")
    webdriver_options.experimental_options["prefs"] = webdriver_prefs

    webdriver_prefs["profile.default_content_settings"] = {"images": 2}

    if install_driver:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=webdriver_options)
    else:
        driver = webdriver.Chrome(options=webdriver_options)

    
    # Detect the type of source and create data url if needed
    if type(source) == io.BytesIO:
        encoded_content = base64.b64encode(source.getvalue()).decode('utf-8')
        path = f'data:text/html;base64,{encoded_content}'
    if not source.startswith('http') and not source.startswith('file'):
        encoded_content = base64.b64encode(source.encode('utf-8')).decode('utf-8')
        path = f'data:text/html;base64,{encoded_content}'
    else:
        path = source

    driver.get(path)

    try:
        WebDriverWait(driver, timeout).until(
            staleness_of(driver.find_element(by=By.TAG_NAME, value="html"))
        )
    except TimeoutException:
        calculated_print_options = {
            "landscape": False,
            "displayHeaderFooter": False,
            "printBackground": True,
            "preferCSSPageSize": True,
        }
        calculated_print_options.update(print_options)
        result = __send_devtools(
            driver, "Page.printToPDF", calculated_print_options)
        return base64.b64decode(result["data"])
    finally:
        driver.quit()
