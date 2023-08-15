import pytest
import os
import hashlib
import json
import gzip
import requests
from urllib.parse import quote


curPath = os.path.abspath(os.path.dirname(__file__))
test_word = "你好,世界!Hello,world!"

def test_img_data(lyrebird, mock_server):
    with open(f"{curPath}/assets/1.png", "rb") as f:
        data = f.read()
    r = requests.post(url=lyrebird.uri_mock + mock_server.api_post, data=data)
    assert r.text == hashlib.md5(mock_server.api_post.encode() + data).hexdigest()


def test_img_file(lyrebird, mock_server):
    files = {'file': ('1.png', open(f'{curPath}/assets/1.png', 'rb'), 'image/jpg')}
    r = requests.post(url=lyrebird.uri_mock + mock_server.api_post, files=files)
    with open(f'{curPath}/assets/1.png', 'rb') as f:
        data = f.read()
    assert r.text == hashlib.md5(mock_server.api_post.encode() + data).hexdigest()


def test_json(lyrebird, mock_server):
    data = json.dumps({"name": {"12": 123}}, ensure_ascii=False)
    headers = {"Content-Type": "application/json"}
    r = requests.post(url=lyrebird.uri_mock + mock_server.api_post, data=data, headers=headers)
    assert r.text == hashlib.md5(mock_server.api_post.encode() + data.encode()).hexdigest()


def test_javascript(lyrebird, mock_server):
    data = "(function(){\n    var name = 'Lyrebird';\n  })();"
    headers = {"Content-Type": "application/javascript"}
    r = requests.post(url=lyrebird.uri_mock + mock_server.api_post, data=data, headers=headers)
    assert r.text == hashlib.md5(mock_server.api_post.encode() + data.encode()).hexdigest()


def test_text(lyrebird, mock_server):
    data = "asdasdasd"
    headers = {"Content-Type": "text/plain"}
    r = requests.post(url=lyrebird.uri_mock + mock_server.api_post, data=data, headers=headers)
    assert r.text == hashlib.md5(mock_server.api_post.encode() + data.encode()).hexdigest()


def test_form(lyrebird, mock_server):
    data = 'z=9&a=1&a=2&b=1'
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    r = requests.post(url=lyrebird.uri_mock + mock_server.api_post, data=data, headers=headers)
    assert r.text == hashlib.md5(mock_server.api_post.encode() + data.encode()).hexdigest()


def test_json_gzip(lyrebird, mock_server):
    data = {"a": 1}
    ziped_data = gzip.compress(json.dumps(data, ensure_ascii=False).encode())
    headers = {"Content-Type": "application/json", "Content-Encoding": "gzip"}
    r = requests.post(url=lyrebird.uri_mock + mock_server.api_post, data=ziped_data, headers=headers)
    assert r.text == hashlib.md5(mock_server.api_post.encode() + ziped_data).hexdigest()


def test_lb_proxy_protocol_target_in_path(lyrebird, mock_server):
    r = requests.get(url=lyrebird.uri_extra_mock + mock_server.api_status)
    assert r.text == 'OK'


def test_lb_proxy_protocol_target_in_header(lyrebird, mock_server):
    headers = {
        'MKScheme': 'http',
        'MKOriginHost': '127.0.0.1',
        'MKOriginPort': '5000'
    }
    r = requests.get(url=lyrebird.uri_extra_mock + 'status', headers=headers)
    assert r.text == 'OK'


def test_lb_proxy_protocol_target_in_query(lyrebird, mock_server):
    r = requests.get(url=lyrebird.uri_extra_mock + f'?proxy={quote(mock_server.api_status, safe="")}')
    assert r.text == 'OK'


def test_lb_proxy_protocol_target_in_query_2(lyrebird, mock_server):
    host = quote(f'127.0.0.1:{mock_server.port}')
    path = quote('/status')
    r = requests.get(url=lyrebird.uri_extra_mock + f'?proxyscheme=http&proxyhost={host}&proxypath={path}&a=1')
    assert r.text == 'OK'


def test_api_flow_decode(lyrebird, mock_server):
    url_ori = mock_server.api_param + f'?param={test_word}'
    url_encode = mock_server.api_param + f'?param={quote(test_word)}'
    requests.get(url=lyrebird.uri_mock + url_encode)
    request_id = requests.get(url=lyrebird.uri_flow).json()[0]['id']
    r = requests.get(url=lyrebird.uri_flow + f'/{request_id}?is_decode=true').json()
    param = r['data']['request']['query']['param']
    url = r['data']['request']['url']
    assert param == test_word
    assert url == url_ori


def test_api_flow_not_decode(lyrebird, mock_server):
    url_encode = mock_server.api_param + f'?param={quote(test_word)}'
    requests.get(url=lyrebird.uri_mock + url_encode)
    request_id = requests.get(url=lyrebird.uri_flow).json()[0]['id']
    r = requests.get(url=lyrebird.uri_flow + f'/{request_id}?is_decode=false').json()
    param = r['data']['request']['query']['param']
    url = r['data']['request']['url']
    assert param == quote(test_word)
    assert url == url_encode


def test_api_flow_default_not_decode(lyrebird, mock_server):
    url_encode = mock_server.api_param + f'?param={quote(test_word)}'
    requests.get(url=lyrebird.uri_mock + url_encode)
    request_id = requests.get(url=lyrebird.uri_flow).json()[0]['id']
    r = requests.get(url=lyrebird.uri_flow + f'/{request_id}').json()
    param = r['data']['request']['query']['param']
    url = r['data']['request']['url']
    assert param == quote(test_word)
    assert url == url_encode


def test_api_flow_ori(lyrebird, mock_server):
    encode_word = test_word.encode('unicode_escape').decode()
    requests.post(url=lyrebird.uri_mock + mock_server.api_encoder_decoder, data={'word':encode_word})
    request_id = requests.get(url=lyrebird.uri_flow).json()[0]['id']
    r = requests.get(url=lyrebird.uri_flow + f'/{request_id}?is_origin=true').json()
    word = r['data']['request']['data']['word']
    assert word == encode_word


def test_api_flow_not_ori(lyrebird, mock_server):
    encode_word = test_word.encode('unicode_escape').decode()
    requests.post(url=lyrebird.uri_mock + mock_server.api_encoder_decoder, data={'word':encode_word})
    request_id = requests.get(url=lyrebird.uri_flow).json()[0]['id']
    r = requests.get(url=lyrebird.uri_flow + f'/{request_id}?is_origin=false').json()
    word = r['data']['request']['data']['word']
    assert word == test_word


def test_api_flow_default_not_ori(lyrebird, mock_server):
    encode_word = test_word.encode('unicode_escape').decode()
    requests.post(url=lyrebird.uri_mock + mock_server.api_encoder_decoder, data={'word':encode_word})
    request_id = requests.get(url=lyrebird.uri_flow).json()[0]['id']
    r = requests.get(url=lyrebird.uri_flow + f'/{request_id}').json()
    word = r['data']['request']['data']['word']
    assert word == test_word


def test_api_flow_decode_and_ori(lyrebird, mock_server):
    url_ori = mock_server.api_encoder_decoder + f'?param={test_word}'
    url_encode = mock_server.api_encoder_decoder + f'?param={quote(test_word)}'
    encode_word = test_word.encode('unicode_escape').decode()
    requests.post(url=lyrebird.uri_mock + url_encode, data={'word':encode_word})
    request_id = requests.get(url=lyrebird.uri_flow).json()[0]['id']
    r = requests.get(url=lyrebird.uri_flow + f'/{request_id}?is_origin=true&is_decode=true').json()
    word = r['data']['request']['data']['word']
    param = r['data']['request']['query']['param']
    url = r['data']['request']['url']
    assert param == test_word
    assert url == url_ori
    assert word == encode_word
