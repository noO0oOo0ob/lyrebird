import json
import re

def filter_flow_details(flow_details, user_request):
    filtered_flows = []
    filter_summary = {
        'total_requests': 0,
        'filtered_count': 0,
        'filter_criteria': []
    }

    # Extract keywords from user request
    keywords = re.findall(r'<<(.+?)>>', user_request)
    
    # Define filter criteria
    resource_extensions = ('.js', '.css', '.png', '.jpg', '.jpeg', '.gif', 
                           '.ico', '.woff', '.woff2', '.ttf', '.eot', '.svg')
    static_folders = ('/static/', '/assets/', '/images/')
    testability_url = 'lyrebird.sankuai.com/api/report/testability'

    for flow in flow_details:
        filter_summary['total_requests'] += 1
        request = flow.get('request', {})
        response = flow.get('response', {})
        path = request.get('path', '')
        response_data = response.get('data', '')
        response_code = response.get('code', 0)

        # Basic filtering
        if path.endswith(resource_extensions):
            continue
        if any(path.startswith(folder) for folder in static_folders):
            continue
        if testability_url in path:
            continue

        # Attempt to parse response data
        try:
            if isinstance(response_data, str):
                response_data = json.loads(response_data)
        except (json.JSONDecodeError, TypeError):
            response_data = {}

        # Keyword filtering
        if keywords:
            if not any(keyword in str(request) or keyword in str(response_data) for keyword in keywords):
                continue

        # Data feature filtering (if applicable)
        if response_code == 200:
            if isinstance(response_data, dict) and ('list' in response_data or 'items' in response_data):
                filtered_flows.append(create_filtered_flow(flow, response_data, request, response))
                continue
            if isinstance(response_data, list) and len(response_data) > 0:
                filtered_flows.append(create_filtered_flow(flow, response_data, request, response))
                continue

        # Smart matching if no keywords were provided
        if not keywords:
            if 'api' in path or 'v1' in path or 'list' in path or 'detail' in path:
                filtered_flows.append(create_filtered_flow(flow, response_data, request, response))

    filter_summary['filtered_count'] = len(filtered_flows)
    return {
        'filtered_flows': filtered_flows,
        'filter_summary': filter_summary
    }

def create_filtered_flow(flow, response_data, request, response):
    return {
        'id': flow.get('id', ''),
        'request_info': {
            'method': request.get('method', ''),
            'path': request.get('path', ''),
            'query': request.get('query', {}),
            'headers': request.get('headers', {})
        },
        'request_data': request,
        'response_data': response,
        'match_reason': 'Matched based on criteria'
    }

flows = [{'id': '3d0c4884-d9e3-4aa0-84fa-01f936f9af62', 'request': {'headers': {'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Connection': 'keep-alive', 'Mitmproxy-Proxy': '::1', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'no-cors', 'Sec-Fetch-Site': 'none', 'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36', 'X-HTTP-Method-Override': 'POST'}, 'host': 'safebrowsing.googleapis.com', 'method': 'GET', 'path': '/v4/threatListUpdates:fetch', 'port': '80', 'query': {'$ct': 'application/x-protobuf', '$req': 'Ch0KDGdvb2dsZWNocm9tZRINMTM0LjAuNjk5OC40NBotCAUQBBofChEIBRAGGAEiAzAwMSiAgAIwARCp2BoaAhgG0CQJxyIEIAEgAigBGiwIEBAEGh4KEQgQEAYYASIDMDAxKICABDABEMIsGgIYBl-tAxkiBCABIAIoARotCAEQBBofChEIARAGGAEiAzAwMSiAgAIwARC4kRAaAhgGUPYRWCIEIAEgAigBGi0IAxAEGh8KEQgDEAYYASIDMDAxKICAAjABENyIEBoCGAaeJE9MIgQgASACKAEaLQgOEAQaHwoRCA4QBhgBIgMwMDEogIAEMAEQzt4HGgIYBvh9eEUiBCABIAIoARotCAcQBBofChEIBxAGGAEiAzAwMSiAgAIwARC61xAaAhgGCVQFeiIEIAEgAigBGiwIARAIGh4KEQgBEAgYASIDMDAxKICABDAEEJk8GgIYBmUU4sciBCABIAIoBBotCA8QBBofChEIDxAGGAEiAzAwMSiAgAIwARDN0AQaAhgG_fhiVSIEIAEgAigBGisICRAEGh0KEQgJEAYYASIDMDAxKICABDABECMaAhgGzi9G7yIEIAEgAigBGiwICBAEGh4KEQgIEAYYASIDMDAxKICABDABEKsYGgIYBiQDR30iBCABIAIoARotCA0QBBofChEIDRAGGAEiAzAwMSiAgAQwARCWvQIaAhgGaIwroyIEIAEgAigBIgIIAQ', 'key': 'AIzaSyDr2UxVnv_U85AbhhY8XSHSIavUW0DC-sY'}, 'scheme': 'https', 'timestamp': 1741515882.031, 'url': 'https://safebrowsing.googleapis.com/v4/threatListUpdates:fetch?$req=Ch0KDGdvb2dsZWNocm9tZRINMTM0LjAuNjk5OC40NBotCAUQBBofChEIBRAGGAEiAzAwMSiAgAIwARCp2BoaAhgG0CQJxyIEIAEgAigBGiwIEBAEGh4KEQgQEAYYASIDMDAxKICABDABEMIsGgIYBl-tAxkiBCABIAIoARotCAEQBBofChEIARAGGAEiAzAwMSiAgAIwARC4kRAaAhgGUPYRWCIEIAEgAigBGi0IAxAEGh8KEQgDEAYYASIDMDAxKICAAjABENyIEBoCGAaeJE9MIgQgASACKAEaLQgOEAQaHwoRCA4QBhgBIgMwMDEogIAEMAEQzt4HGgIYBvh9eEUiBCABIAIoARotCAcQBBofChEIBxAGGAEiAzAwMSiAgAIwARC61xAaAhgGCVQFeiIEIAEgAigBGiwIARAIGh4KEQgBEAgYASIDMDAxKICABDAEEJk8GgIYBmUU4sciBCABIAIoBBotCA8QBBofChEIDxAGGAEiAzAwMSiAgAIwARDN0AQaAhgG_fhiVSIEIAEgAigBGisICRAEGh0KEQgJEAYYASIDMDAxKICABDABECMaAhgGzi9G7yIEIAEgAigBGiwICBAEGh4KEQgIEAYYASIDMDAxKICABDABEKsYGgIYBiQDR30iBCABIAIoARotCA0QBBofChEIDRAGGAEiAzAwMSiAgAQwARCWvQIaAhgGaIwroyIEIAEgAigBIgIIAQ==&$ct=application/x-protobuf&key=AIzaSyDr2UxVnv_U85AbhhY8XSHSIavUW0DC-sY'}, 'response': {'code': 200, 'data': 'CvESCAUQARgEIAEq+w0IAiL2DQjYkd4BEBYYxgQi6Q3U0NcSI+ToBKhEnxvx9zgs00F54osdHM+bUoqD/1+A7Ft/2jI9+/ZnSAjPTszQ6BQn1D05tWN4BhOHF4/+dfP8qmqthuOTceL3pdR2QzVrNupf/JITCMRNz7iiwExEvfsZaZIXNaZ9Njpw8M9eFo0Vd23ZAV0oqG3nbvknbaCO2PJuU1pvyUsx0CW49VKgLhrrGqJsJh9uZMwlLszyAo9BQD6yRHKMmdnPdolAObSBGJNyTpO3uVgor22pcHRIDX46h1plMbY0gG3JDxWycED0s1L9MIFVZDhAsmf9CGkh89icnefRNBOJCxYnA5XJ4WArz2FOlgf+7tXsDlD128l4yQuGek4dATf2vRainEMn1kXAlcEsAVYAdMvey6nhgohdtHN4Hqkcz0JR47WXDaKHy/3YfQwR0JuoP8TQhdbmD27D3LuD2WpNP29TIbyg8qS0687/16owtNKqYhBydEbTncB+S4M+MHBNDOh0I0QJ+Kq+2Bek2DNAV9o+s/5o/ziNbpT6iOli5LllShbUZUrCiw2u6PVMNUAMiCo1cG8QCN20KtUlIfb2yQXp7FzwSComo2tkIrT6+zI1bmCLEIhfQSjbq80Ff3S2jvXsc0RVsNIYRDc5cKotVldc89uQLz5Jd+y3yzLEKpEs9RcTjzUSDy6jr31fWFTCuIfsliauIYOAazReLulyhfBHobhTPrwza92q01nuAgcJnhwZ3r//BNKo2Q77WXtR9HnRY+qdfyGKxOPUI+9vNZh0xreAAumtS+lbvCx5YZKWDQGq6vi2hYOU1/CM/okTSuFW8wZqM3v0c/3aDkonwIeb7ezZWU6TCNakro+o9MbcmVPRJQH0QOgaEf2S1Zg0D97pyYykG4m3wK9/Fz6Kicf7ke1PA3s+V0mGiOdDQ7Q24KYhegCpixkyU6lvvlMNJsYChzwTyg9lerPCDom0EaLbCQmOGKH+aovKdFAKio6iE/fvyAGuF70q61ITmsO3ohAQs6p2ALNLA6VkAM5BqPydPE5lXWsS96Xh7WpRgoq3Bk+u1B4Klso49XT3ZVgoezBGfd4TdtFqwp7B0G2jOZSg//cDsjru8MQ8zzjNM+VHRZgjI+a39OOA6hAFVjOtPOmU63xcheXi7InVAr9/hxNbgalhGpCJZB0RWxudFKSNDX0DblPH/4npGLL1pXYFtMKbSNSQg5IQsOl3a/NXKUF+GGNltT7/d60vHQvKxevr6NVouJnsS/el7XFQtGYxdxVQ67em7pOtn3v84Cn/hf+KDD4gIVi791h7Pc51kZQBdsPI07UeBDaxEmUiHnzdK41FIJ00aRLxh3iFUwe4QTgX3RhKKn/b7MD4IdxyaKQwwAZDD+M/BOsZGc0hkloOingncQALnybsIlcEmpVqALlM/v3Kq8yfBgC/9ouuVhcMMKfHwNnMpWowUiRCO6wZhqusptrBeOkQSMAy6M10/skRId3m2va3rVkqmB+vc0iWePGlKU8uO0Rd2y3ipOKl832UP4NEMgVoo1BJZmBt5/7R5lzSGz+6QNgBieOyy72svpSHXrY69hECKQfeys7a9xbhl+i4yMItpTLHAkzuBZPizPEP5qU9TQMFzVFFT8TNiXRheoRGlFSPwDxknS91S6Sn7izaY3aoo7mJ/XzRNjR4JS+fwewHhCrESYP7OxlclKs581fYVKCTNcm8gR9cHbi3LgAjjruU6C9KwZsCm32PyVDSs1EHrrtoT8VCMzOEFuAnkmQgRF4eQYWmWXRca/i064nnWcFOmSLmYvNfT6kYXHGtzxISLH06FET6n6isYMWJnQx7//4wieyO7FZhwHQbFqPbnJztu9Dci0sttLZuyKuO/2R8mOVQyfiFGI6VXsDQ5UL3kddD9rlkWIYwtQqYD8ZUT+xm2yLFnLT4oF+y9ex4wCBucyte+JfofKIIXbYo6PpVsi9suBUQcgws/xacTd91IjKY2rBNEjwRGXgRs6hu0KQ/waeAXHPHc7Y0pLnrQHkyrdRx43/YIBzGhtKH0UwXUR0cLzYSSEObFWqwRFwM1VD5Hr2ZFXGLsDuDP4C8ubXcTR5NP2II+RtvoWVN7FXgyZYNrJW+AeGZi/dNgNB3eTIFJ2OQY+RhXk2/omz6Fqukb/nSwlBPmK8GtKKyHZbPID1kGeK33y/N5LrIOwLeY3N2UmHTwa9JmIOwmwgXtO0UYV0EXzKUMECFVgb52EVr+9gjoSkNBWq+jVYOmhzwUxeJ4CtbywUdvpdtnOjTklt5LPts1LvzsTx4H+D/lup/8G7JP8FwQnUGHB4Yr8ImEJW0xux6GBdboU9zRRkC0TiiPrQRY+gEQavV8PjGu2B3DQFJplnr/3EENzKjBAgCKp4ECHcQBRjGBCKUBMVf6EWYlZTJWyT1G16YNNEsd52QR4nCb1BTayuFlS97ZWziPvnaP/KoMHfK/ez0k4cTMW1OeMFCz0tO3v9LVxz4GQ8MyGeq4E7NqjGunCaSShj0PA38LGc8lC0SXkR0Ss8bZuVRGc3mdO4TAZHh2BI0De/+IPW1Xcq5PzZIer/ITz6nr1V2A5+gBo4T+9fWQGnpwVsDx3xVvF1eeNpj5Bt/o2dLiTd/0qJWb2nJDCkQIHbx3zG508/0s+2xQLKt8M9XnBYOkr8ySt/5Em0YhQNuzi494yGdGxBaTx8kaxmQc58lv73eVI87V4XNtx04d/V7jpIf/SHYIFt/dUDfdWEBHMDKAmQjItV9kcLpLwQ5GaLbLv4Ziuw1z+LsAykUad1OGIP4CY4LHJCyEjHP61967Tt3lNxAhNASJCeT3VnX3DtDniGeRJZjRAfGSixhxUAOV1wESYUkbR78J4If+W5KlCqw1SbzBr4Fenoycq84WpVlOPSt1WGqRoHqyvZawOWiAuY1c3g78uNfZoqpuK/QzpELvmjdyVEfKHSokRbdPXA01YgQ1VaAVX47cUeW/+8zP1kQFq/kC9yzgvBf04RGTPjfqTFWJ/NusHAlX/vXWI9/SVcVpam9VAtyEa8o/craH1rGmH+sLEIbklNE9zIw2PKoFZM+uPULXaSzs81tBtudXYfic+YxHD9h6VuCfSBbHwI6HwoRCAUQBhgBIgMwMDEogIACMAEQrdgaGgIYBohAspNCIgogEULDyWjltLxbtk9YLfuw3Lzb4nPRHQsSBOyepkENtUMKTAgQEAEYBCABOh4KEQgQEAYYASIDMDAxKICABDABEMIsGgIYBl+tAxlCIgoghGP8wX6BIPVwqrPP5thCUzRzg9+swK6TkUX6M7h60xIKpAEIARABGAQgASo1CAIiMQjLhdYGEBwYCiImHZqg+ZVgTsbbyCxWpdOJzFlCiUAXKkEzp02OQjY3xNs+yoCmnBMyHggCKhoI2BwQCxgKIhFU4HSxbRaORi+RatuVoRGhADofChEIARAGGAEiAzAwMSiAgAIwARC6kRAaAhgGx8guHEIiCiCU8z+BObz54i0p23jY5vprM8trkwkGKPqYk54zUNiSUwreAQgDEAEYBCABKl8IAiJbCMuF1gYQGxgWIlDkaBewvwif2xPIovXQM0y+mR9B/Z8Wx+phBxq6uw1kHCOIaVMsjM1z6CjJ9V50z8bZ+yyCjfF5QpqBJHlrM1qZfwBP8k2vYXzuvVYSI3gnLTIuCAIqKgjWARAKGBYiITDi7Ao2AMx2i7FLDZx/H182XRPLY1EqXDAXzHwtgVZqXTofChEIAxAGGAEiAzAwMSiAgAIwARDeiBAaAhgG9OH83kIiCiCmKuykuRjVCW5uI69eSOdXwO8ZK8na5nDSqOEgCwGeYwpNCA4QARgEIAE6HwoRCA4QBhgBIgMwMDEogIAEMAEQzt4HGgIYBvh9eEVCIgogsZM+qzZndDmBH5YXldwm9QokqSqKVXFSkcmNFvu1uR0KngEIBxABGAQgASoxCAIiLQjLhdYGEBwYCSIiak9AdHa5jjBdaSd+hVdxQQCE2/vWhF6fu9xLLyGiRoNrWDIcCAIqGAiPDhALGAkiD3m5yaZ45+0FiZS2sPelGDofChEIBxAGGAEiAzAwMSiAgAIwARC81xAaAhgGv2QV/EIiCiCu60BEzRPmXjMFGPqmROxkWWfNhJjy79MAw/VBVVFirwpMCAEQBBgIIAE6HgoRCAEQCBgBIgMwMDEogIAEMAQQmTwaAhgGZRTix0IiCiBk94q79p4JSM0ze7XXf3nAsOM5+HxMME9rD8jAaRgJaAqJAQgPEAEYBCABKiMIAiIfCMuF1gYQHBgFIhSfPA5aNc/jxXdYS1iZPOWmVXiUBDIVCAIqEQj+AxAKGAUiCEezHOoXAVsMOh8KEQgPEAYYASIDMDAxKICAAjABEM/QBBoCGAawFQ/ZQiIKIJ+YMNn8Zeu9+f15mIsrhM+nwDd38/3dPiPOZOckdHTfCksICRABGAQgATodChEICRAGGAEiAzAwMSiAgAQwARAjGgIYBs4vRu9CIgogpOOuYm2pCG5DH3tQTIMUxxi+keCfzV6vC31bEMIFOREKTAgIEAEYBCABOh4KEQgIEAYYASIDMDAxKICABDABEKsYGgIYBiQDR31CIgogLX1zYGk8c6deAmy6U4hvdYTZeBrpDuaLPk7XcS75H/MKTQgNEAEYBCABOh8KEQgNEAYYASIDMDAxKICABDABEJa9AhoCGAZojCujQiIKIJMQCIkfV5rnQIjMBnCNEQ9uTh4NqV54752MT1o0FYPPEgkI+A0QgP2QywE=\n', 'headers': {'Age': '479', 'Alt-Svc': 'h3=":443"; ma=2592000,h3-29=":443"; ma=2592000', 'Content-Disposition': 'attachment', 'Content-Length': '3593', 'Content-Type': 'application/x-protobuf', 'Date': 'Sun, 09 Mar 2025 10:16:43 GMT', 'Server': 'scaffolding on HTTPServer2', 'Vary': 'Accept-Encoding', 'X-Content-Type-Options': 'nosniff', 'X-Frame-Options': 'SAMEORIGIN', 'X-XSS-Protection': '0', 'lyrebird': 'proxy'}, 'timestamp': 1741515882.582}}, {'id': '468798e9-3297-4efa-8592-f582e6e7faaa', 'request': {'headers': {'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate', 'Mitmproxy-Proxy': '::1', 'Pragma': 'no-cache', 'Proxy-Connection': 'keep-alive', 'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36'}, 'host': 'clients2.google.com', 'method': 'GET', 'path': '/time/1/current', 'port': '80', 'query': {'cup2hreq': 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855', 'cup2key': '8:1qGF6bq9QacPtLr5eGKTOMZCMMhz8Qz6LtJEIW7UgCI'}, 'scheme': 'http', 'timestamp': 1741515199.098, 'url': 'http://clients2.google.com/time/1/current?cup2key=8:1qGF6bq9QacPtLr5eGKTOMZCMMhz8Qz6LtJEIW7UgCI&cup2hreq=e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'}, 'response': {'code': 200, 'data': 'KV19Jwp7ImN1cnJlbnRfdGltZV9taWxsaXMiOjE3NDE1MTUxOTk0MzcsInNlcnZlcl9ub25jZSI6LTIuNDcyOTY3MzA5NjU3NTc5RS03MH0=\n', 'headers': {'Cache-Control': 'no-cache, no-store, max-age=0, must-revalidate', 'Connection': 'keep-alive', 'Content-Disposition': 'attachment; filename="json.txt"; filename*=UTF-8\'\'json.txt', 'Content-Type': 'application/json; charset=utf-8', 'Cross-Origin-Opener-Policy': 'same-origin', 'Cross-Origin-Resource-Policy': 'same-site', 'Date': 'Sun, 09 Mar 2025 10:13:19 GMT', 'Etag': 'W/"30440220767e85c07b2bd9d520c0d6a407694c50954adee890f8ea9368f0e38df8b9e2e3022051ac07422f232fa72a818b8714c032b9d84b34d8c05922984f2cf161fa9f9052:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"', 'Expires': 'Mon, 01 Jan 1990 00:00:00 GMT', 'Keep-Alive': 'timeout=4', 'Pragma': 'no-cache', 'Proxy-Connection': 'keep-alive', 'Server': 'ESF', 'Vary': 'Sec-Fetch-Dest, Sec-Fetch-Mode, Sec-Fetch-Site', 'X-Content-Type-Options': 'nosniff', 'X-Cup-Server-Proof': '30440220767e85c07b2bd9d520c0d6a407694c50954adee890f8ea9368f0e38df8b9e2e3022051ac07422f232fa72a818b8714c032b9d84b34d8c05922984f2cf161fa9f9052:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855', 'X-Frame-Options': 'SAMEORIGIN', 'X-Xss-Protection': '0', 'lyrebird': 'proxy'}, 'timestamp': 1741515199.558}}, {'id': '0ab5fc21-1bf0-4209-a482-07f4a43c76c5', 'request': {'headers': {'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Connection': 'keep-alive', 'Mitmproxy-Proxy': '::1', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'no-cors', 'Sec-Fetch-Site': 'none', 'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36', 'X-HTTP-Method-Override': 'POST'}, 'host': 'safebrowsing.googleapis.com', 'method': 'GET', 'path': '/v4/threatListUpdates:fetch', 'port': '80', 'query': {'$ct': 'application/x-protobuf', '$req': 'Ch0KDGdvb2dsZWNocm9tZRINMTM0LjAuNjk5OC40NBotCAUQBBofChEIBRAGGAEiAzAwMSiAgAIwARCm2BoaAhgGfwvwsyIEIAEgAigBGiwIEBAEGh4KEQgQEAYYASIDMDAxKICABDABEMIsGgIYBl-tAxkiBCABIAIoARotCAEQBBofChEIARAGGAEiAzAwMSiAgAIwARC3kRAaAhgG5Z5JgSIEIAEgAigBGi0IAxAEGh8KEQgDEAYYASIDMDAxKICAAjABENuIEBoCGAYJbq_1IgQgASACKAEaLQgOEAQaHwoRCA4QBhgBIgMwMDEogIAEMAEQzt4HGgIYBvh9eEUiBCABIAIoARotCAcQBBofChEIBxAGGAEiAzAwMSiAgAIwARC51xAaAhgGY-xWrCIEIAEgAigBGiwIARAIGh4KEQgBEAgYASIDMDAxKICABDAEEJk8GgIYBmUU4sciBCABIAIoBBotCA8QBBofChEIDxAGGAEiAzAwMSiAgAIwARDM0AQaAhgG4UP4RCIEIAEgAigBGisICRAEGh0KEQgJEAYYASIDMDAxKICABDABECMaAhgGzi9G7yIEIAEgAigBGiwICBAEGh4KEQgIEAYYASIDMDAxKICABDABEKsYGgIYBiQDR30iBCABIAIoARotCA0QBBofChEIDRAGGAEiAzAwMSiAgAQwARCWvQIaAhgGaIwroyIEIAEgAigBIgIIAQ', 'key': 'AIzaSyDr2UxVnv_U85AbhhY8XSHSIavUW0DC-sY'}, 'scheme': 'https', 'timestamp': 1741514056.348, 'url': 'https://safebrowsing.googleapis.com/v4/threatListUpdates:fetch?$req=Ch0KDGdvb2dsZWNocm9tZRINMTM0LjAuNjk5OC40NBotCAUQBBofChEIBRAGGAEiAzAwMSiAgAIwARCm2BoaAhgGfwvwsyIEIAEgAigBGiwIEBAEGh4KEQgQEAYYASIDMDAxKICABDABEMIsGgIYBl-tAxkiBCABIAIoARotCAEQBBofChEIARAGGAEiAzAwMSiAgAIwARC3kRAaAhgG5Z5JgSIEIAEgAigBGi0IAxAEGh8KEQgDEAYYASIDMDAxKICAAjABENuIEBoCGAYJbq_1IgQgASACKAEaLQgOEAQaHwoRCA4QBhgBIgMwMDEogIAEMAEQzt4HGgIYBvh9eEUiBCABIAIoARotCAcQBBofChEIBxAGGAEiAzAwMSiAgAIwARC51xAaAhgGY-xWrCIEIAEgAigBGiwIARAIGh4KEQgBEAgYASIDMDAxKICABDAEEJk8GgIYBmUU4sciBCABIAIoBBotCA8QBBofChEIDxAGGAEiAzAwMSiAgAIwARDM0AQaAhgG4UP4RCIEIAEgAigBGisICRAEGh0KEQgJEAYYASIDMDAxKICABDABECMaAhgGzi9G7yIEIAEgAigBGiwICBAEGh4KEQgIEAYYASIDMDAxKICABDABEKsYGgIYBiQDR30iBCABIAIoARotCA0QBBofChEIDRAGGAEiAzAwMSiAgAQwARCWvQIaAhgGaIwroyIEIAEgAigBIgIIAQ==&$ct=application/x-protobuf&key=AIzaSyDr2UxVnv_U85AbhhY8XSHSIavUW0DC-sY'}, 'response': {'code': 200, 'data': {
    "newData": {
        "abStrategy": {
            "ab_group_advertisement_limit": "base",
            "ab_group_b_group_liebiaoPOI_straightline_distance_NEW": "a",
            "ab_group_cuofeng_special_price": "E",
            "ab_group_deal_daodianchitaocan": "c",
            "ab_group_meishi_channel_deal": "a",
            "ab_group_special_card": "",
            "ab_recommend_loading_mechanism": "",
            "lowest_price_ab_key": "show_tag",
            "lowest_price_poi_card_ab_key": "a",
            "off_peak_specials_card": "True",
            "poi_card_deal_num": "2",
            "standard_ab_key": "c",
            "work_meal_card": "True"
        },
        "adsRequestIds": "%7B%22request_id%22%3A%227594677193464929655%22%7D",
        "cardList": {
            "cardInfos": [
                {
                    "cardInfo": {
                        "areaName": "十三陵水库",
                        "avgPrice": 93,
                        "avgScore": 4.9,
                        "cateDinner": True,
                        "cateName": "特色菜",
                        "channel": "food",
                        "ctPoi": "111089410018614686773235396862104668571_a650990090_c0_e3056406926952507964_v7594677193464929655__-1",
                        "distance": "",
                        "extraServiceIcons": [
                            "https://p0.meituan.net/scarlett/14c10e3660cdd1d57620da2884c6e3dd7896.png"
                        ],
                        "frontImg": "https://p0.meituan.net/adunion/1c8691c6bbd31797cc0685609b20575c286938.jpg%40240w_240h_1e_1c_1l%7Cwatermark%3D0",
                        "iUrl": "",
                        "lat": 40.270646,
                        "lng": 116.231411,
                        "name": "鸽子园",
                        "nibBizConsistency": "WfRgPPZ1mw83ZOfZJaiJ7ABlrfql5ZI0MXWvFwFHcBDTndzVIgTkg59E4bD0aGYCk6zMYAvXndP7uqLQi-vg4Ft3VDUEprkEQZ_PlvVqRy85Cmyv4vs3MQcx1uYT4Cu49FWgaa9fvA837LUILpKlGXatkJlt3Qvxzq6_7iThpZDv4k0GqYQ1Uu4IjoPo9OOKiO_sTgRjHFETIClz5TGZwJnYjtYjM0Xb4CKcMSrXACLiV1c8wmyuz5NU9sULvHXEjFjupHlqCrMMGn-zWqfZ0A",
                        "openHours": {
                            "openNextHalfHour": True,
                            "openNow": True
                        },
                        "openStatus": 0,
                        "poiImgExtra": {
                            "topRight": {
                                "icon": "",
                                "tagId": 0,
                                "text": {
                                    "backgroundColor": "",
                                    "borderColor": "",
                                    "color": "",
                                    "content": "广告"
                                }
                            }
                        },
                        "poiid": "650990090",
                        "poiidEncrypt": "qB4r107d78ae07b89cea60b024915d7a711afcbe643598e9791ef29c7529e26evxu5",
                        "preferentialInfo": {
                            "backgroundColor": "#FFF1EC",
                            "morePreferential": "",
                            "poiToDealNum": 8,
                            "preferentials": [
                                [
                                    {
                                        "bestDeal": {
                                            "batchDealNumber": -1,
                                            "price": "2??",
                                            "value": "3??"
                                        },
                                        "dealBackgroundPic": "",
                                        "dealGuideTags": {
                                            "icon": ""
                                        },
                                        "dealId": 1177383324,
                                        "dealImgUrl": "http://p0.meituan.net/w.h/content/952bee593454df6056142a77b0c40804243252.jpg@350_0_900_900a%7C267h_267w_2e_90Q",
                                        "dealSales": "",
                                        "dealTag": [
                                            {
                                                "icon": "",
                                                "text": {
                                                    "backgroundColor": "",
                                                    "borderColor": "",
                                                    "color": "",
                                                    "content": "半年售 54"
                                                },
                                                "type": "sales"
                                            }
                                        ],
                                        "discount": "",
                                        "icon": "https://p0.meituan.net/0.0.o/travelcube/e962ee69a3422d982e86a921779101d32697.png?width=16&height=16",
                                        "isLiveDeal": False,
                                        "isTimeLimitCoupon": False,
                                        "jumpUrl": "imeituan://www.meituan.com/mrn?mrn_biz=meishi&mrn_entry=lingyu-10746&mrn_component=main&source=yinpinxiaochi_pindaoye_liebiao_deal&scene=snack_list&dealId=1177383324&poiId=650990090",
                                        "promotionIconTag": "",
                                        "promotionTag": "",
                                        "saleChannel": "mainScene",
                                        "secondsKillEndTime": 0,
                                        "text": "【午市尝鲜】特色菜4人餐",
                                        "type": 1,
                                        "useRules": [
                                            "周一至周四",
                                            "免预约"
                                        ]
                                    }
                                ],
                                [
                                    {
                                        "bestDeal": {
                                            "batchDealNumber": -1,
                                            "price": "1??",
                                            "value": "1??"
                                        },
                                        "dealBackgroundPic": "",
                                        "dealGuideTags": {
                                            "icon": ""
                                        },
                                        "dealId": 1176899291,
                                        "dealImgUrl": "http://p0.meituan.net/w.h/content/3faeeba6d7a6afe2be781b3e449b39ff161607.jpg@349_0_900_900a%7C267h_267w_2e_90Q",
                                        "dealSales": "",
                                        "dealTag": [
                                            {
                                                "icon": "",
                                                "text": {
                                                    "backgroundColor": "",
                                                    "borderColor": "",
                                                    "color": "",
                                                    "content": "半年售 29"
                                                },
                                                "type": "sales"
                                            }
                                        ],
                                        "discount": "",
                                        "icon": "https://p0.meituan.net/0.0.o/travelcube/e962ee69a3422d982e86a921779101d32697.png?width=16&height=16",
                                        "isLiveDeal": False,
                                        "isTimeLimitCoupon": False,
                                        "jumpUrl": "imeituan://www.meituan.com/mrn?mrn_biz=meishi&mrn_entry=lingyu-10746&mrn_component=main&source=yinpinxiaochi_pindaoye_liebiao_deal&scene=snack_list&dealId=1176899291&poiId=650990090",
                                        "promotionIconTag": "",
                                        "promotionTag": "",
                                        "saleChannel": "mainScene",
                                        "secondsKillEndTime": 0,
                                        "text": "【午市尝鲜】超实惠双人餐",
                                        "type": 1,
                                        "useRules": [
                                            "周一至周四",
                                            "免预约"
                                        ]
                                    }
                                ]
                            ],
                            "textColor": "#FF4B10"
                        },
                        "reportMessage": {
                            "adLx": "{\"accountid\":79952820,\"slotid\":50011,\"ad_request_id\":\"7594677193464929655\",\"launchid\":39832455,\"targetid\":50198605,\"entityid\":650990090,\"entitytype\":1,\"adshopid\":650990090,\"product_id\":\"74\"}",
                            "adsClickUrl": "https://mlog.dianping.com/api/cpv/billing?mbid=3.5&productid=74&priceMode=5&pctr=0.04012029618024826&display_id=50011&bg=0&recalled_match_unit=0&ad_cj=3SBwna1Z6Sjo0LeNdSWCNIBRu2Wy2PFJ2m7YT3oeBO3sjJFDKmkdmFL3jyTNIy8A8IYXDHlrr-MpZ7fFaj99x-e9hitoC7wkNtVJe7Ri70Y3bfHz-tUyVU-Wx6UBIVg1m2dhIhRCfC-gzxDi&ad_ci=3SBwlaxJ5WGggq-ZLSuKKtIH_Djojt5S1zCLR3gJCPuo1NMCKnM2mEKz03DBLCIG-YoBTiUq3egtZrfHcz5qgLP_w38qWZAhPZxDe71m6EAmP6GDnKA7CRvNxaEFYwk&utm_medium=android&discount=1&rankScore=2.9243640899658203&mtlaunch_city_id=1&ecpcLambda=1.62|0.05961127&bu=28&premium=1&category_id=34284&pos=1&freCtrl=False&mtuser_id64=0&adshoptype=226&pcvr=0.05961126891891892&client_version=12.22.200&mtdpid=000000000000079DE9975FBE548D79FB7125FC602382AA168675081685585060&bottomprice=1.0&lat=0.0&user_agent=android&city_id_platform=MT&launch_city_id=2&mtcategory_ids=1&lng=0.0&sver=2&AdExpPath=3-1002-4606,18-817-3805,18-4110-16795,18-4629-18788,3-1222-29278,3-140-565,18-765-3690,18-842-18601,18-4324-17417,18-7729-29220,18-7904-30039,3-4149-17077,18-4693-19053,3-1606-7070,18-7702-29095,18-10317-37494,18-10331-37589,18-6431-24638,3-6495-24893,3-4559-18493,18-1317-5672,3-164-5978,3-296-1803,18-338-2099,3-136-551,18-4363-17597,18-444-2514,3-12-28,18-2836-11523,3-62-31346,18-1595-7035,3-130-33564,18-8257-33579,18-7509-28478,18-7865-29823,18-4397-18062,3-1505-6694,18-4420-17809,3-844-3909,3-1376-5947,18-7594-28613,18-573-2979,18-1513-6675,18-6203-23628,18-1223-5391,3-201-1096,18-7521-28459,3-63-28645,3-414-2388,18-1347-5830,18-4624-18742,3-7518-28584,3-7469-28296,3-4674-18991,18-4628-18786,3-9162-33594,18-1531-24362,18-1543-6830,3-50-100,3-227-1297,18-4514-18471,3-1000-4604,18-1529-6752,18-1549-28363,18-1027-4757,18-7918-30118,3-6278-23977,18-7727-29203,18-293-1778,3-1578-6946,18-4496-18156,18-4623-18728&auctionTag=5|1&floatRatio=50&lite_set_cell=default-cell&bottomfen=100&mtuser_id=0&adsCtrStrategy=FoodMergedCVR&page_city_id=1&entityplat=2&ad_v=2&mtadshop_id=650990090&city_mode=1&is_target_city=1&mtpage_city_id=1&adidx=1&act=2",
                            "adsImpressionUrl": "https://mlog.dianping.com/api/cpv/action?mbid=3.5&productid=74&priceMode=5&pctr=0.04012029618024826&display_id=50011&bg=0&recalled_match_unit=0&ad_cj=3SBwna1Z6Sjo0LeNdSWCNIBRu2Wy2PFJ2m7YT3oeBO3sjJFDKmkdmFL3jyTNIy8A8IYXDHlrr-MpZ7fFaj99x-e9hitoC7wkNtVJe7Ri70Y3bfHz-tUyVU-Wx6UBIVg1m2dhIhRCfC-gzxDi&ad_ci=3SBwlaxJ5WGggq-ZLSuKKtIH_Djojt5S1zCLR3gJCPuo1NMCKnM2mEKz03DBLCIG-YoBTiUq3egtZrfHcz5qgLP_w38qWZAhPZxDe71m6EAmP6GDnKA7CRvNxaEFYwk&utm_medium=android&discount=1&rankScore=2.9243640899658203&mtlaunch_city_id=1&ecpcLambda=1.62|0.05961127&bu=28&premium=1&category_id=34284&pos=1&freCtrl=False&mtuser_id64=0&adshoptype=226&pcvr=0.05961126891891892&client_version=12.22.200&mtdpid=000000000000079DE9975FBE548D79FB7125FC602382AA168675081685585060&bottomprice=1.0&lat=0.0&user_agent=android&city_id_platform=MT&launch_city_id=2&mtcategory_ids=1&lng=0.0&sver=2&AdExpPath=3-1002-4606,18-817-3805,18-4110-16795,18-4629-18788,3-1222-29278,3-140-565,18-765-3690,18-842-18601,18-4324-17417,18-7729-29220,18-7904-30039,3-4149-17077,18-4693-19053,3-1606-7070,18-7702-29095,18-10317-37494,18-10331-37589,18-6431-24638,3-6495-24893,3-4559-18493,18-1317-5672,3-164-5978,3-296-1803,18-338-2099,3-136-551,18-4363-17597,18-444-2514,3-12-28,18-2836-11523,3-62-31346,18-1595-7035,3-130-33564,18-8257-33579,18-7509-28478,18-7865-29823,18-4397-18062,3-1505-6694,18-4420-17809,3-844-3909,3-1376-5947,18-7594-28613,18-573-2979,18-1513-6675,18-6203-23628,18-1223-5391,3-201-1096,18-7521-28459,3-63-28645,3-414-2388,18-1347-5830,18-4624-18742,3-7518-28584,3-7469-28296,3-4674-18991,18-4628-18786,3-9162-33594,18-1531-24362,18-1543-6830,3-50-100,3-227-1297,18-4514-18471,3-1000-4604,18-1529-6752,18-1549-28363,18-1027-4757,18-7918-30118,3-6278-23977,18-7727-29203,18-293-1778,3-1578-6946,18-4496-18156,18-4623-18728&auctionTag=5|1&floatRatio=50&lite_set_cell=default-cell&bottomfen=100&mtuser_id=0&adsCtrStrategy=FoodMergedCVR&page_city_id=1&entityplat=2&ad_v=2&mtadshop_id=650990090&city_mode=1&is_target_city=1&mtpage_city_id=1&adidx=1&act=3"
                        },
                        "reviewNumberDesc": "1837条",
                        "rotationTags": [
                            {
                                "icon": "",
                                "text": {
                                    "backgroundColor": "",
                                    "borderColor": "",
                                    "color": "#666666",
                                    "content": "季售1000+"
                                }
                            },
                            {
                                "icon": "",
                                "text": {
                                    "backgroundColor": "",
                                    "borderColor": "",
                                    "color": "#666666",
                                    "content": "10分钟前有人消费"
                                }
                            }
                        ],
                        "showType": "",
                        "smartTags": [
                            {
                                "icon": "",
                                "jumpUrl": "imeituan://www.meituan.com/web?notitlebar=1&url=https%3A%2F%2Fmobilenext-web.meituan.com%2FrankingList%3FboardType%3D8%26source%3D6%26ci%3D1%26areaId%3D22995%26cateId%3D21533%26districtId%3D0%26notitlebar%3D1%26poiId%3D650990090",
                                "rightIcon": "https://p0.meituan.net/travelcube/fc81086bc7528281c2df4cf25b97a5c3689.png",
                                "tagType": "",
                                "tagid": 431,
                                "text": {
                                    "backgroundColor": "#FFEDDE",
                                    "borderColor": "",
                                    "color": "#8E3C12",
                                    "content": "十三陵水库风味地方菜人气榜第1名"
                                }
                            },
                            {
                                "icon": "",
                                "jumpUrl": "",
                                "rightIcon": "",
                                "tagType": "",
                                "tagid": 2702,
                                "text": {
                                    "backgroundColor": "#F5F5F5",
                                    "borderColor": "",
                                    "color": "#666666",
                                    "content": "187人觉得食材新鲜"
                                }
                            },
                            {
                                "icon": "",
                                "jumpUrl": "",
                                "rightIcon": "",
                                "tagType": "",
                                "tagid": 2711,
                                "text": {
                                    "backgroundColor": "#F4F4F4",
                                    "borderColor": "",
                                    "color": "#666666",
                                    "content": "近期100%好评"
                                }
                            },
                            {
                                "icon": "",
                                "jumpUrl": "",
                                "rightIcon": "",
                                "tagType": "",
                                "tagid": 2752,
                                "text": {
                                    "backgroundColor": "#F4F4F4",
                                    "borderColor": "",
                                    "color": "#666666",
                                    "content": "近1小时43人看过"
                                }
                            },
                            {
                                "icon": "",
                                "jumpUrl": "",
                                "rightIcon": "",
                                "tagType": "",
                                "tagid": 2862,
                                "text": {
                                    "backgroundColor": "#F4F4F4",
                                    "borderColor": "",
                                    "color": "#666666",
                                    "content": "亲子主题餐厅"
                                }
                            },
                            {
                                "icon": "",
                                "jumpUrl": "",
                                "rightIcon": "",
                                "tagType": "",
                                "tagid": 2798,
                                "text": {
                                    "backgroundColor": "#F4F4F4",
                                    "borderColor": "",
                                    "color": "#666666",
                                    "content": "地铁直达"
                                }
                            },
                            {
                                "icon": "",
                                "jumpUrl": "",
                                "rightIcon": "",
                                "tagType": "",
                                "tagid": 2766,
                                "text": {
                                    "backgroundColor": "#F4F4F4",
                                    "borderColor": "",
                                    "color": "#666666",
                                    "content": "有包厢"
                                }
                            },
                            {
                                "icon": "",
                                "jumpUrl": "",
                                "rightIcon": "",
                                "tagType": "",
                                "tagid": 2786,
                                "text": {
                                    "backgroundColor": "#F4F4F4",
                                    "borderColor": "",
                                    "color": "#666666",
                                    "content": "花园餐厅"
                                }
                            },
                            {
                                "icon": "",
                                "jumpUrl": "",
                                "rightIcon": "",
                                "tagType": "",
                                "tagid": 2565,
                                "text": {
                                    "backgroundColor": "#F4F4F4",
                                    "borderColor": "",
                                    "color": "#666666",
                                    "content": "334人推荐秘制烧鸽子"
                                }
                            }
                        ],
                        "styleType": 1,
                        "titleTags": [],
                        "traceData": {
                            "_apimeishi_rerank_report_data": "",
                            "avgPrice": "93.0",
                            "avgScore": "4.9",
                            "clientRerankFeatures": "",
                            "distance": "",
                            "globalIdForFilterBar": "",
                            "sale": "4707"
                        },
                        "typeId": 2055
                    },
                    "type": "adsShop"
                },
                {
                    "cardInfo": {
                        "areaName": "亦庄",
                        "avgPrice": 25,
                        "avgScore": 4.2,
                        "cateDinner": False,
                        "cateName": "西式快餐/汉堡",
                        "channel": "food",
                        "ctPoi": "153724372769088362450865176448515935668_a175384736_c1_e3056406926952507964",
                        "distance": "",
                        "extraServiceIcons": [
                            "https://p0.meituan.net/scarlett/14c10e3660cdd1d57620da2884c6e3dd7896.png",
                            "https://p0.meituan.net/travelcube/683bdf4ca9d8e9a0cf96234ce1a622e011487.png"
                        ],
                        "frontImg": "https://img.meituan.net/content/2c3746cc0ada62551ce08197fdb33d46144693.jpg%40240w_240h_1e_1c_1l%7Cwatermark%3D0",
                        "iUrl": "",
                        "lat": 39.792403,
                        "lng": 116.51299,
                        "name": "汉堡王（大族广场店）",
                        "nibBizConsistency": "WfRgPPZ1mw83ZOfZJaiJ7ABlrfql5ZI0MXWvFwFHcBDTndzVIgTkg59E4bD0aGYCk6zMYAvXndP7uqLQi-vg4JGQdCYtbxi4TAb83xJWk5g5Cmyv4vs3MQcx1uYT4Cu41kuR1Fk0s0kwB6Qd2oxf1S-7QGnyliCwS8cFDAgIAdqQk-1prMBGFu7yS4aF7Wx1iO_sTgRjHFETIClz5TGZwJnYjtYjM0Xb4CKcMSrXACLiV1c8wmyuz5NU9sULvHXE4xm8l-zNBIB7LPDDR6GqDQ",
                        "openHours": {
                            "openNextHalfHour": True,
                            "openNow": True
                        },
                        "openStatus": 0,
                        "poiImgExtra": {},
                        "poiid": "175384736",
                        "poiidEncrypt": "qB4r177f7da406bc9be066b024915d7a711afcbe643598e9791ef29c7529e26evxu5",
                        "preferentialInfo": {
                            "backgroundColor": "#FFF1EC",
                            "morePreferential": "",
                            "poiToDealNum": 82,
                            "preferentials": [
                                [
                                    {
                                        "bestDeal": {
                                            "batchDealNumber": -1,
                                            "price": "3?",
                                            "value": "5?"
                                        },
                                        "dealBackgroundPic": "https://p1.meituan.net/travelcube/e53c4b3c311e60107365db8c07afb73d82643.png",
                                        "dealGuideTags": {
                                            "backgroundUrl": "https://p0.meituan.net/ingee/20f7266f814c61fff6f85ec566314f428678.png",
                                            "icon": "https://p1.meituan.net/96.0/travelcube/fdc237b438185ac20d5695b4b6a87d8b17273.gif?width=12&height=12",
                                            "text": {
                                                "backgroundColor": "",
                                                "borderColor": "",
                                                "color": "#FFFFFF",
                                                "content": "直播专享价"
                                            },
                                            "type": "",
                                            "value": ""
                                        },
                                        "dealId": 1195932379,
                                        "dealImgUrl": "http://p1.meituan.net/w.h/content/51a22ceeb61667afabc986a2af63036d269640.jpg@233_0_720_720a%7C267h_267w_2e_90Q",
                                        "dealSales": "",
                                        "dealTag": [
                                            {
                                                "icon": "",
                                                "text": {
                                                    "backgroundColor": "",
                                                    "borderColor": "",
                                                    "color": "",
                                                    "content": "半年售 4.6万+"
                                                },
                                                "type": "sales"
                                            }
                                        ],
                                        "discount": "",
                                        "icon": "https://p1.meituan.net/travelcube/8af6bd79150bbe7d15ab5e65728f996752939.gif?width=16&height=16",
                                        "isLiveDeal": True,
                                        "isTimeLimitCoupon": False,
                                        "jumpUrl": "imeituan://www.meituan.com/mlivemrn?mrn_biz=hotel&mrn_entry=hotel-mlive&mrn_component=hotel-mlive&isOrganizer=False&type=0&liveId=10190512&page_source=meishi_channel&mrn_min_version=0.0.600&traceMonitorInfo=%7B%22needMetricFields%22%3A%5B%22pageSource%22%2C%22querySource%22%2C%22cat0%22%5D%2C%22querySource%22%3A%22dao_can_toc_poi_page_live_goods_exclusive_price_tag%22%2C%22pageSource%22%3A%22meishi_channel%22%2C%22cat0%22%3A%227200%22%7D&rec_goods_id=1195932379&rec_goods_type=9&rec_goods_id=1195932379&rec_goods_type=9&rec_type=0",
                                        "promotionIconTag": "",
                                        "promotionTag": "直播专享价",
                                        "promotionalGuideTag": {
                                            "icon": "https://p1.meituan.net/travelcube/8af6bd79150bbe7d15ab5e65728f996752939.gif?width=16&height=16",
                                            "text": {
                                                "backgroundColor": "",
                                                "borderColor": "",
                                                "color": "#FF4B10",
                                                "content": "直播专享价"
                                            }
                                        },
                                        "saleChannel": "foodLiveStreaming",
                                        "secondsKillEndTime": 0,
                                        "text": "大嘴安格斯2件套",
                                        "type": 1,
                                        "useRules": [
                                            "周一至周日",
                                            "免预约"
                                        ]
                                    }
                                ],
                                [
                                    {
                                        "bestDeal": {
                                            "batchDealNumber": -1,
                                            "price": "1?",
                                            "value": "2?"
                                        },
                                        "dealBackgroundPic": "",
                                        "dealGuideTags": {
                                            "icon": ""
                                        },
                                        "dealId": 973127259,
                                        "dealImgUrl": "http://p0.meituan.net/w.h/content/cb3eb25b7790180db8a8a2df6e116381297464.jpg@233_0_720_720a%7C267h_267w_2e_90Q",
                                        "dealSales": "",
                                        "dealTag": [
                                            {
                                                "icon": "",
                                                "text": {
                                                    "backgroundColor": "",
                                                    "borderColor": "",
                                                    "color": "",
                                                    "content": "半年售 22万+"
                                                },
                                                "type": "sales"
                                            }
                                        ],
                                        "discount": "",
                                        "icon": "https://p0.meituan.net/0.0.o/travelcube/e962ee69a3422d982e86a921779101d32697.png?width=16&height=16",
                                        "isLiveDeal": False,
                                        "isTimeLimitCoupon": False,
                                        "jumpUrl": "imeituan://www.meituan.com/mrn?mrn_biz=meishi&mrn_entry=lingyu-10746&mrn_component=main&source=yinpinxiaochi_pindaoye_liebiao_deal&scene=snack_list&dealId=973127259&poiId=175384736",
                                        "promotionIconTag": "",
                                        "promotionTag": "",
                                        "saleChannel": "mainScene",
                                        "secondsKillEndTime": 0,
                                        "text": "【1+1】小食随心配",
                                        "type": 1,
                                        "useRules": [
                                            "周一至周日",
                                            "免预约"
                                        ]
                                    }
                                ]
                            ],
                            "textColor": "#FF4B10"
                        },
                        "reviewNumberDesc": "4670条",
                        "rotationTags": [
                            {
                                "icon": "",
                                "text": {
                                    "backgroundColor": "",
                                    "borderColor": "",
                                    "color": "#666666",
                                    "content": "季售6000+"
                                }
                            },
                            {
                                "icon": "",
                                "text": {
                                    "backgroundColor": "",
                                    "borderColor": "",
                                    "color": "#666666",
                                    "content": "4分钟前有人消费"
                                }
                            }
                        ],
                        "showType": "",
                        "smartTags": [
                            {
                                "icon": "https://p0.meituan.net/bizoperate/abd75055f50ab9c7acd63ed05359caa781563.gif?width=48&height=16&left=0&right=0&top=0&bottom=0&isCircle=0",
                                "jumpUrl": "imeituan://www.meituan.com/mlivemrnlist?scenekey=daocan&liveId=10190512&page_source=daocanpoilist",
                                "rightIcon": "",
                                "tagType": "",
                                "tagid": 1949
                            },
                            {
                                "icon": "",
                                "jumpUrl": "",
                                "rightIcon": "",
                                "tagType": "",
                                "tagid": 2718,
                                "text": {
                                    "backgroundColor": "#FFF1EC",
                                    "borderColor": "",
                                    "color": "#FF4B10",
                                    "content": "秒提·在线点"
                                }
                            },
                            {
                                "icon": "",
                                "jumpUrl": "imeituan://www.meituan.com/web?notitlebar=1&url=https%3A%2F%2Fmobilenext-web.meituan.com%2FrankingList%3FboardType%3D8%26source%3D6%26ci%3D1%26areaId%3D4759%26cateId%3D36%26districtId%3D0%26notitlebar%3D1%26poiId%3D175384736",
                                "rightIcon": "https://p0.meituan.net/travelcube/fc81086bc7528281c2df4cf25b97a5c3689.png",
                                "tagType": "",
                                "tagid": 431,
                                "text": {
                                    "backgroundColor": "#FFEDDE",
                                    "borderColor": "",
                                    "color": "#8E3C12",
                                    "content": "亦庄小吃快餐人气榜第2名"
                                }
                            },
                            {
                                "icon": "",
                                "jumpUrl": "",
                                "rightIcon": "",
                                "tagType": "",
                                "tagid": 331,
                                "text": {
                                    "backgroundColor": "#F5F5F5",
                                    "borderColor": "",
                                    "color": "#666666",
                                    "content": "吹爆他家的薯霸王,薯条🍟好好吃"
                                }
                            },
                            {
                                "icon": "",
                                "jumpUrl": "",
                                "rightIcon": "",
                                "tagType": "",
                                "tagid": 340,
                                "text": {
                                    "backgroundColor": "#F5F5F5",
                                    "borderColor": "",
                                    "color": "#666666",
                                    "content": "收录6年"
                                }
                            },
                            {
                                "icon": "",
                                "jumpUrl": "",
                                "rightIcon": "",
                                "tagType": "",
                                "tagid": 2709,
                                "text": {
                                    "backgroundColor": "#F5F5F5",
                                    "borderColor": "",
                                    "color": "#666666",
                                    "content": "回头客3千+"
                                }
                            },
                            {
                                "icon": "",
                                "jumpUrl": "",
                                "rightIcon": "",
                                "tagType": "",
                                "tagid": 2702,
                                "text": {
                                    "backgroundColor": "#F5F5F5",
                                    "borderColor": "",
                                    "color": "#666666",
                                    "content": "555人觉得性价比高"
                                }
                            },
                            {
                                "icon": "",
                                "jumpUrl": "",
                                "rightIcon": "",
                                "tagType": "",
                                "tagid": 2752,
                                "text": {
                                    "backgroundColor": "#F4F4F4",
                                    "borderColor": "",
                                    "color": "#666666",
                                    "content": "近1小时30人看过"
                                }
                            },
                            {
                                "icon": "",
                                "jumpUrl": "",
                                "rightIcon": "",
                                "tagType": "",
                                "tagid": 2565,
                                "text": {
                                    "backgroundColor": "#F4F4F4",
                                    "borderColor": "",
                                    "color": "#666666",
                                    "content": "187人推荐狠霸王牛堡"
                                }
                            }
                        ],
                        "styleType": 1,
                        "titleTags": [],
                        "traceData": {
                            "_apimeishi_rerank_report_data": "",
                            "avgPrice": "25.0",
                            "avgScore": "4.2",
                            "clientRerankFeatures": "{\"ctr\":\"0.13221272826194763\",\"DISTANCE\":\"2.147483647E9\",\"lng\":\"116.51299216836709\",\"userYidiStatus\":\"0\",\"discount\":\"3.5119047\",\"diningType\":\"3.0\",\"AVGPRICE\":\"25.0\",\"IN_SERVICE_TIME\":\"1.0\",\"POIBRANDID\":\"185877.0\",\"TYPEID_LEVEL2\":\"10.0\",\"TYPEID_LEVEL3\":\"1848.0\",\"AVGSCORE\":\"4.2\",\"lat\":\"39.79240083516876\",\"cvr\":\"0.055444471538066864\"}",
                            "distance": "",
                            "globalIdForFilterBar": "",
                            "sale": "6946"
                        },
                        "typeId": 1848
                    },
                    "type": "shop"
                },
                {
                    "cardInfo": {
                        "areaName": "延庆城区",
                        "avgPrice": 101,
                        "avgScore": 4.9,
                        "cateDinner": True,
                        "cateName": "烤肉自助",
                        "channel": "food",
                        "ctPoi": "153724372769088362450865176448515935668_a691517008_c2_e3056406926952507964",
                        "distance": "",
                        "extraServiceIcons": [
                            "https://p0.meituan.net/scarlett/6207fbb6a439a5cb93137721dbd324f27812.png"
                        ],
                        "frontImg": "http://p0.meituan.net/biztone/b1799952fe2b318028ce0b4e7c843936374879.jpg%40240w_240h_1e_1c_1l%7Cwatermark%3D0",
                        "iUrl": "",
                        "lat": 40.461523,
                        "lng": 115.97608,
                        "name": "好伦哥自助餐（延庆航母店）",
                        "nibBizConsistency": "WfRgPPZ1mw83ZOfZJaiJ7ABlrfql5ZI0MXWvFwFHcBDTndzVIgTkg59E4bD0aGYCk6zMYAvXndP7uqLQi-vg4ASLjh7c3FetYJovdG2Tc8Q5Cmyv4vs3MQcx1uYT4Cu4Y34gN5zi1bXRrVendCSIESauAf49mKP8iXu9-TGbnG9OQ2gVTh3rF7pXBtcbEkt7HFAOMHdurYLqaZBnLprv4Roj2Lf0fqT64Rb8_2dqfS3_HOSJhTbf_0uEYZvlAHSYsby5b-6MRVVqB6xkaBThbA",
                        "openHours": {
                            "openNextHalfHour": True,
                            "openNow": True
                        },
                        "openStatus": 0,
                        "poiImgExtra": {
                            "brand": {
                                "icon": None,
                                "jumpUrl": "imeituan://www.meituan.com/web?notitlebar=1&url=https%3A%2F%2Fmobilenext-web.meituan.com%2Fpoimoreinfo%3Fpoiid%3D691517008",
                                "tagId": 348,
                                "text": {
                                    "backgroundColor": "",
                                    "borderColor": "",
                                    "color": "",
                                    "content": "连锁"
                                }
                            }
                        },
                        "poiid": "691517008",
                        "poiidEncrypt": "qB4r107179a20fbf9ce368b024915d7a711afcbe643598e9791ef29c7529e26evxu5",
                        "preferentialInfo": {
                            "backgroundColor": "#FFF1EC",
                            "morePreferential": "",
                            "poiToDealNum": 5,
                            "preferentials": [
                                [
                                    {
                                        "bestDeal": {
                                            "batchDealNumber": -1,
                                            "price": "9?",
                                            "value": "1??"
                                        },
                                        "dealBackgroundPic": "",
                                        "dealGuideTags": {
                                            "icon": ""
                                        },
                                        "dealId": 1229345402,
                                        "dealImgUrl": "http://p0.meituan.net/w.h/content/0a865b575f54f24125d50e4c5e4a6905331318.jpg@350_0_900_900a%7C267h_267w_2e_90Q",
                                        "dealSales": "",
                                        "dealTag": [
                                            {
                                                "icon": "",
                                                "text": {
                                                    "backgroundColor": "",
                                                    "borderColor": "",
                                                    "color": "",
                                                    "content": "半年售 3000+"
                                                },
                                                "type": "sales"
                                            }
                                        ],
                                        "icon": "https://p0.meituan.net/0.0.o/travelcube/e962ee69a3422d982e86a921779101d32697.png?width=16&height=16",
                                        "isLiveDeal": False,
                                        "isTimeLimitCoupon": False,
                                        "jumpUrl": "imeituan://www.meituan.com/mrn?mrn_biz=meishi&mrn_entry=lingyu-10746&mrn_component=main&source=yinpinxiaochi_pindaoye_liebiao_deal&scene=snack_list&dealId=1229345402&poiId=691517008",
                                        "promotionIconTag": "",
                                        "promotionTag": "美团补贴",
                                        "promotionalGuideTag": {
                                            "icon": "https://p1.meituan.net/0.0.o//travelcube/b4527407c5247c3bcfdd9ef2e049ab1b547.png",
                                            "text": {
                                                "backgroundColor": "",
                                                "borderColor": "",
                                                "color": "#FF4B10",
                                                "content": "美团补贴"
                                            }
                                        },
                                        "saleChannel": "mainScene",
                                        "secondsKillEndTime": 0,
                                        "text": "【延庆店·冰雪季】成人单人周末节假日",
                                        "type": 1,
                                        "useRules": [
                                            "周六至周日",
                                            "免预约"
                                        ]
                                    }
                                ],
                                [
                                    {
                                        "bestDeal": {
                                            "batchDealNumber": -1,
                                            "price": "8?",
                                            "value": "1??"
                                        },
                                        "dealBackgroundPic": "",
                                        "dealGuideTags": {
                                            "icon": ""
                                        },
                                        "dealId": 1229339743,
                                        "dealImgUrl": "http://p0.meituan.net/w.h/content/d2ee9694e4c91e30fd5eacbe1b264666317244.jpg@350_0_900_900a%7C267h_267w_2e_90Q",
                                        "dealSales": "",
                                        "dealTag": [
                                            {
                                                "icon": "",
                                                "text": {
                                                    "backgroundColor": "",
                                                    "borderColor": "",
                                                    "color": "",
                                                    "content": "半年售 5000+"
                                                },
                                                "type": "sales"
                                            }
                                        ],
                                        "discount": "",
                                        "icon": "https://p0.meituan.net/0.0.o/travelcube/e962ee69a3422d982e86a921779101d32697.png?width=16&height=16",
                                        "isLiveDeal": False,
                                        "isTimeLimitCoupon": False,
                                        "jumpUrl": "imeituan://www.meituan.com/mrn?mrn_biz=meishi&mrn_entry=lingyu-10746&mrn_component=main&source=yinpinxiaochi_pindaoye_liebiao_deal&scene=snack_list&dealId=1229339743&poiId=691517008",
                                        "promotionIconTag": "",
                                        "promotionTag": "美团补贴",
                                        "promotionalGuideTag": {
                                            "icon": "https://p1.meituan.net/0.0.o//travelcube/b4527407c5247c3bcfdd9ef2e049ab1b547.png",
                                            "text": {
                                                "backgroundColor": "",
                                                "borderColor": "",
                                                "color": "#FF4B10",
                                                "content": "美团补贴"
                                            }
                                        },
                                        "saleChannel": "mainScene",
                                        "secondsKillEndTime": 0,
                                        "text": "【延庆店·冰雪季】单人工作日通用券",
                                        "type": 1,
                                        "useRules": [
                                            "周一至周五",
                                            "免预约"
                                        ]
                                    }
                                ]
                            ],
                            "textColor": "#FF4B10"
                        },
                        "reviewNumberDesc": "2313条",
                        "rotationTags": [
                            {
                                "icon": "",
                                "text": {
                                    "backgroundColor": "",
                                    "borderColor": "",
                                    "color": "#666666",
                                    "content": "季售1.1万+"
                                }
                            },
                            {
                                "icon": "",
                                "text": {
                                    "backgroundColor": "",
                                    "borderColor": "",
                                    "color": "#666666",
                                    "content": "1分钟前有人消费"
                                }
                            }
                        ],
                        "showType": "",
                        "smartTags": [
                            {
                                "icon": "https://p0.meituan.net/bizoperate/abd75055f50ab9c7acd63ed05359caa781563.gif?width=48&height=16&left=0&right=0&top=0&bottom=0&isCircle=0",
                                "jumpUrl": "imeituan://www.meituan.com/mlivemrnlist?scenekey=daocan&liveId=9568324&page_source=daocanpoilist",
                                "rightIcon": "",
                                "tagType": "",
                                "tagid": 1949
                            },
                            {
                                "icon": "",
                                "jumpUrl": "imeituan://www.meituan.com/web?notitlebar=1&url=https%3A%2F%2Fmobilenext-web.meituan.com%2FrankingList%3FboardType%3D10%26source%3D6%26ci%3D1%26areaId%3D0%26cateId%3D40%26districtId%3D2075%26notitlebar%3D1%26poiId%3D691517008",
                                "rightIcon": "https://p0.meituan.net/travelcube/fc81086bc7528281c2df4cf25b97a5c3689.png",
                                "tagType": "",
                                "tagid": 431,
                                "text": {
                                    "backgroundColor": "#FFEDDE",
                                    "borderColor": "",
                                    "color": "#8E3C12",
                                    "content": "延庆区自助餐好评榜第1名"
                                }
                            },
                            {
                                "icon": "",
                                "jumpUrl": "",
                                "rightIcon": "",
                                "tagType": "",
                                "tagid": 2709,
                                "text": {
                                    "backgroundColor": "#F5F5F5",
                                    "borderColor": "",
                                    "color": "#666666",
                                    "content": "回头客1千+"
                                }
                            },
                            {
                                "icon": "",
                                "jumpUrl": "",
                                "rightIcon": "",
                                "tagType": "",
                                "tagid": 2702,
                                "text": {
                                    "backgroundColor": "#F5F5F5",
                                    "borderColor": "",
                                    "color": "#666666",
                                    "content": "186人觉得食材新鲜"
                                }
                            },
                            {
                                "icon": "",
                                "jumpUrl": "",
                                "rightIcon": "",
                                "tagType": "",
                                "tagid": 2711,
                                "text": {
                                    "backgroundColor": "#F4F4F4",
                                    "borderColor": "",
                                    "color": "#666666",
                                    "content": "近期96%好评"
                                }
                            },
                            {
                                "icon": "",
                                "jumpUrl": "",
                                "rightIcon": "",
                                "tagType": "",
                                "tagid": 2752,
                                "text": {
                                    "backgroundColor": "#F4F4F4",
                                    "borderColor": "",
                                    "color": "#666666",
                                    "content": "近1小时38人看过"
                                }
                            },
                            {
                                "icon": "",
                                "jumpUrl": "",
                                "rightIcon": "",
                                "tagType": "",
                                "tagid": 2786,
                                "text": {
                                    "backgroundColor": "#F4F4F4",
                                    "borderColor": "",
                                    "color": "#666666",
                                    "content": "花园餐厅"
                                }
                            },
                            {
                                "icon": "",
                                "jumpUrl": "",
                                "rightIcon": "",
                                "tagType": "",
                                "tagid": 2565,
                                "text": {
                                    "backgroundColor": "#F4F4F4",
                                    "borderColor": "",
                                    "color": "#666666",
                                    "content": "92人推荐榴莲披萨"
                                }
                            }
                        ],
                        "styleType": 1,
                        "titleTags": [],
                        "traceData": {
                            "_apimeishi_rerank_report_data": "",
                            "avgPrice": "101.0",
                            "avgScore": "4.9",
                            "clientRerankFeatures": "{\"ctr\":\"0.22177168726921082\",\"DISTANCE\":\"2.147483647E9\",\"lng\":\"115.9760791389692\",\"userYidiStatus\":\"0\",\"discount\":\"4.573643\",\"diningType\":\"2.0\",\"AVGPRICE\":\"101.0\",\"IN_SERVICE_TIME\":\"1.0\",\"POIBRANDID\":\"187065.0\",\"TYPEID_LEVEL2\":\"202.0\",\"TYPEID_LEVEL3\":\"171.0\",\"AVGSCORE\":\"4.9\",\"lat\":\"40.46152387804835\",\"cvr\":\"0.018652277067303658\"}",
                            "distance": "",
                            "globalIdForFilterBar": "",
                            "sale": "11161"
                        },
                        "typeId": 171
                    },
                    "type": "shop"
                },
                {
                    "cardInfo": {
                        "areaName": "西集",
                        "avgPrice": 0,
                        "avgScore": 0,
                        "cateDinner": True,
                        "cateName": "老北京火锅",
                        "channel": "food",
                        "ctPoi": "111089410018614686773235396862104668571_a964953571_c3_e3056406926952507964_v7594677193464929655__-1",
                        "distance": "",
                        "extraServiceIcons": [],
                        "frontImg": "https://p0.meituan.net/biztone/bac53172dccb1ee0897ef6d9e633d9b0517763.jpg%40240w_240h_1e_1c_1l%7Cwatermark%3D0",
                        "iUrl": "",
                        "lat": 39.815703,
                        "lng": 116.888631,
                        "name": "隆程景泰蓝铜锅",
                        "nibBizConsistency": "WfRgPPZ1mw83ZOfZJaiJ7ABlrfql5ZI0MXWvFwFHcBDTndzVIgTkg59E4bD0aGYCk6zMYAvXndP7uqLQi-vg4J0oOuUHKq3rrQ3ICAySYgY5Cmyv4vs3MQcx1uYT4Cu4W44O1UfLNYLyssVk39KmqN_q-0YWr2LPX-IurGnH1FOEuQmuMZiQ6HDLRJwe5gbyiO_sTgRjHFETIClz5TGZwJnYjtYjM0Xb4CKcMSrXACLiV1c8wmyuz5NU9sULvHXEqGG_a_1ZTdhIg82ebwqDiw",
                        "openHours": {
                            "openNextHalfHour": True,
                            "openNow": True
                        },
                        "openStatus": 0,
                        "poiImgExtra": {
                            "topRight": {
                                "icon": "",
                                "tagId": 0,
                                "text": {
                                    "backgroundColor": "",
                                    "borderColor": "",
                                    "color": "",
                                    "content": "广告"
                                }
                            }
                        },
                        "poiid": "964953571",
                        "poiidEncrypt": "qB4r1f7e7cae0bbb99e461b024915d7a711afcbe643598e9791ef29c7529e26evxu5",
                        "preferentialInfo": {
                            "backgroundColor": "#FFF1EC",
                            "morePreferential": "",
                            "poiToDealNum": 4,
                            "preferentials": [
                                [
                                    {
                                        "bestDeal": {
                                            "batchDealNumber": -1,
                                            "price": "2??",
                                            "value": "3??"
                                        },
                                        "dealBackgroundPic": "",
                                        "dealGuideTags": {
                                            "icon": ""
                                        },
                                        "dealId": 1172979799,
                                        "dealImgUrl": "https://img.meituan.net/w.h/content/2bc55acfee8e312cee4f9aa5c3dc50ee102938.jpg@100_0_600_600a%7C267h_267w_2e_90Q",
                                        "dealSales": "",
                                        "dealTag": [
                                            {
                                                "icon": "",
                                                "text": {
                                                    "backgroundColor": "",
                                                    "borderColor": "",
                                                    "color": "",
                                                    "content": "半年售 1"
                                                },
                                                "type": "sales"
                                            }
                                        ],
                                        "discount": "",
                                        "icon": "https://p0.meituan.net/0.0.o/travelcube/e962ee69a3422d982e86a921779101d32697.png?width=16&height=16",
                                        "isLiveDeal": False,
                                        "isTimeLimitCoupon": False,
                                        "jumpUrl": "imeituan://www.meituan.com/mrn?mrn_biz=meishi&mrn_entry=lingyu-10746&mrn_component=main&source=yinpinxiaochi_pindaoye_liebiao_deal&scene=snack_list&dealId=1172979799&poiId=964953571",
                                        "promotionIconTag": "",
                                        "promotionTag": "",
                                        "saleChannel": "mainScene",
                                        "secondsKillEndTime": 0,
                                        "text": "【爆款】老北京铜锅超值【4人餐】",
                                        "type": 1,
                                        "useRules": [
                                            "周一至周日",
                                            "免预约"
                                        ]
                                    }
                                ],
                                [
                                    {
                                        "bestDeal": {
                                            "batchDealNumber": -1,
                                            "price": "1??",
                                            "value": "1??"
                                        },
                                        "dealBackgroundPic": "",
                                        "dealGuideTags": {
                                            "icon": ""
                                        },
                                        "dealId": 1172977610,
                                        "dealImgUrl": "https://img.meituan.net/w.h/content/2bc55acfee8e312cee4f9aa5c3dc50ee102938.jpg@100_0_600_600a%7C267h_267w_2e_90Q",
                                        "dealSales": "",
                                        "dealTag": [],
                                        "discount": "",
                                        "icon": "https://p0.meituan.net/0.0.o/travelcube/e962ee69a3422d982e86a921779101d32697.png?width=16&height=16",
                                        "isLiveDeal": False,
                                        "isTimeLimitCoupon": False,
                                        "jumpUrl": "imeituan://www.meituan.com/mrn?mrn_biz=meishi&mrn_entry=lingyu-10746&mrn_component=main&source=yinpinxiaochi_pindaoye_liebiao_deal&scene=snack_list&dealId=1172977610&poiId=964953571",
                                        "promotionIconTag": "",
                                        "promotionTag": "",
                                        "saleChannel": "mainScene",
                                        "secondsKillEndTime": 0,
                                        "text": "【超值】老北京铜锅热卖双人餐",
                                        "type": 1,
                                        "useRules": [
                                            "周一至周日",
                                            "免预约"
                                        ]
                                    }
                                ]
                            ],
                            "textColor": "#FF4B10"
                        },
                        "reportMessage": {
                            "adLx": "{\"accountid\":81063545,\"slotid\":50011,\"ad_request_id\":\"7594677193464929655\",\"launchid\":40761032,\"targetid\":53379240,\"entityid\":964953571,\"entitytype\":1,\"adshopid\":964953571,\"product_id\":\"74\"}",
                            "adsClickUrl": "https://mlog.dianping.com/api/cpv/billing?mbid=3.53&productid=74&priceMode=6&pctr=0.06440997868776321&display_id=50011&bg=0&recalled_match_unit=0&ad_cj=8M9dApo4UxO0aqSpvo-JnEyrGAF5o98jSiz-n-4RwogouKhQxEU1Qhfkt_EgZdbN_xJC-IIfR56qxOaBOldskNfpWXr70L1uDWXqqG_i2227OKJeCMyYi7cVsmUxNDJg80fKMcexNDjk7AlA7w&ad_ci=8M9dCpsoX1r8OLy95oaIjRv-W1ok9fA4R3KilO4Gz4k7-_gExk41dAr546Aub9fA9BNB68dLEKiqzb6PJVVrh5C9Gz-vku9CCG6jom_r32q9KfAOeKrtgusQ7jdlNyA3&utm_medium=android&discount=1&rankScore=8.394364356994629&mtlaunch_city_id=1&bu=28&category_id=110&pos=1&freCtrl=False&mtuser_id64=0&adshoptype=226&pcvr=0.010705947035573123&client_version=12.22.200&mtdpid=000000000000079DE9975FBE548D79FB7125FC602382AA168675081685585060&bottomprice=1.0&lat=0.0&user_agent=android&city_id_platform=MT&launch_city_id=2&mtcategory_ids=1&lng=0.0&sver=2&AdExpPath=3-1002-4606,18-817-3805,18-4110-16795,18-4629-18788,3-1222-29278,3-140-565,18-765-3690,18-842-18601,18-4324-17417,18-7729-29220,18-7904-30039,3-4149-17077,18-4693-19053,3-1606-7070,18-7702-29095,18-10317-37494,18-10331-37589,18-6431-24638,3-6495-24893,3-4559-18493,18-1317-5672,3-164-5978,3-296-1803,18-338-2099,3-136-551,18-4363-17597,18-444-2514,3-12-28,18-2836-11523,3-62-31346,18-1595-7035,3-130-33564,18-8257-33579,18-7509-28478,18-7865-29823,18-4397-18062,3-1505-6694,18-4420-17809,3-844-3909,3-1376-5947,18-7594-28613,18-573-2979,18-1513-6675,18-6203-23628,18-1223-5391,3-201-1096,18-7521-28459,3-63-28645,3-414-2388,18-1347-5830,18-4624-18742,3-7518-28584,3-7469-28296,3-4674-18991,18-4628-18786,3-9162-33594,18-1531-24362,18-1543-6830,3-50-100,3-227-1297,18-4514-18471,3-1000-4604,18-1529-6752,18-1549-28363,18-1027-4757,18-7918-30118,3-6278-23977,18-7727-29203,18-293-1778,3-1578-6946,18-4496-18156,18-4623-18728&floatRatio=100&lite_set_cell=default-cell&bottomfen=100&mtuser_id=0&adsCtrStrategy=FoodMergedCVR&page_city_id=1&entityplat=2&ad_v=2&mtadshop_id=964953571&city_mode=1&is_target_city=1&mtpage_city_id=1&adidx=4&act=2",
                            "adsImpressionUrl": "https://mlog.dianping.com/api/cpv/action?mbid=3.53&productid=74&priceMode=6&pctr=0.06440997868776321&display_id=50011&bg=0&recalled_match_unit=0&ad_cj=8M9dApo4UxO0aqSpvo-JnEyrGAF5o98jSiz-n-4RwogouKhQxEU1Qhfkt_EgZdbN_xJC-IIfR56qxOaBOldskNfpWXr70L1uDWXqqG_i2227OKJeCMyYi7cVsmUxNDJg80fKMcexNDjk7AlA7w&ad_ci=8M9dCpsoX1r8OLy95oaIjRv-W1ok9fA4R3KilO4Gz4k7-_gExk41dAr546Aub9fA9BNB68dLEKiqzb6PJVVrh5C9Gz-vku9CCG6jom_r32q9KfAOeKrtgusQ7jdlNyA3&utm_medium=android&discount=1&rankScore=8.394364356994629&mtlaunch_city_id=1&bu=28&category_id=110&pos=1&freCtrl=False&mtuser_id64=0&adshoptype=226&pcvr=0.010705947035573123&client_version=12.22.200&mtdpid=000000000000079DE9975FBE548D79FB7125FC602382AA168675081685585060&bottomprice=1.0&lat=0.0&user_agent=android&city_id_platform=MT&launch_city_id=2&mtcategory_ids=1&lng=0.0&sver=2&AdExpPath=3-1002-4606,18-817-3805,18-4110-16795,18-4629-18788,3-1222-29278,3-140-565,18-765-3690,18-842-18601,18-4324-17417,18-7729-29220,18-7904-30039,3-4149-17077,18-4693-19053,3-1606-7070,18-7702-29095,18-10317-37494,18-10331-37589,18-6431-24638,3-6495-24893,3-4559-18493,18-1317-5672,3-164-5978,3-296-1803,18-338-2099,3-136-551,18-4363-17597,18-444-2514,3-12-28,18-2836-11523,3-62-31346,18-1595-7035,3-130-33564,18-8257-33579,18-7509-28478,18-7865-29823,18-4397-18062,3-1505-6694,18-4420-17809,3-844-3909,3-1376-5947,18-7594-28613,18-573-2979,18-1513-6675,18-6203-23628,18-1223-5391,3-201-1096,18-7521-28459,3-63-28645,3-414-2388,18-1347-5830,18-4624-18742,3-7518-28584,3-7469-28296,3-4674-18991,18-4628-18786,3-9162-33594,18-1531-24362,18-1543-6830,3-50-100,3-227-1297,18-4514-18471,3-1000-4604,18-1529-6752,18-1549-28363,18-1027-4757,18-7918-30118,3-6278-23977,18-7727-29203,18-293-1778,3-1578-6946,18-4496-18156,18-4623-18728&floatRatio=100&lite_set_cell=default-cell&bottomfen=100&mtuser_id=0&adsCtrStrategy=FoodMergedCVR&page_city_id=1&entityplat=2&ad_v=2&mtadshop_id=964953571&city_mode=1&is_target_city=1&mtpage_city_id=1&adidx=4&act=3"
                        },
                        "reviewNumberDesc": "",
                        "rotationTags": [
                            {
                                "icon": "",
                                "text": {
                                    "backgroundColor": "",
                                    "borderColor": "",
                                    "color": "#666666",
                                    "content": "季售1"
                                }
                            }
                        ],
                        "showType": "",
                        "smartTags": [
                            {
                                "icon": "",
                                "jumpUrl": "",
                                "rightIcon": "",
                                "tagType": "",
                                "tagid": 2565,
                                "text": {
                                    "backgroundColor": "#F4F4F4",
                                    "borderColor": "",
                                    "color": "#666666",
                                    "content": "网友推荐品质清汤"
                                }
                            }
                        ],
                        "styleType": 1,
                        "titleTags": [],
                        "traceData": {
                            "_apimeishi_rerank_report_data": "",
                            "avgPrice": "0.0",
                            "avgScore": "0.0",
                            "clientRerankFeatures": "",
                            "distance": "",
                            "globalIdForFilterBar": "",
                            "sale": "1"
                        },
                        "typeId": 239
                    },
                    "type": "adsShop"
                },
                {
                    "cardInfo": {
                        "areaName": "大红门",
                        "avgPrice": 30,
                        "avgScore": 4.9,
                        "cateDinner": True,
                        "cateName": "新疆菜",
                        "channel": "food",
                        "ctPoi": "153724372769088362450865176448515935668_a519090134_c4_e3056406926952507964",
                        "distance": "",
                        "extraServiceIcons": [],
                        "frontImg": "http://p0.meituan.net/biztone/c05ce604097957610cf664c7cef5d48b199661.jpg%40240w_240h_1e_1c_1l%7Cwatermark%3D0",
                        "iUrl": "",
                        "lat": 39.816764,
                        "lng": 116.401344,
                        "name": "伊斯麦尔丝路·新派菜（和义店）",
                        "nibBizConsistency": "WfRgPPZ1mw83ZOfZJaiJ7ABlrfql5ZI0MXWvFwFHcBDTndzVIgTkg59E4bD0aGYCk6zMYAvXndP7uqLQi-vg4MpNsW_jvYt3MqTI52KmZg5brFPjyikhtkYIMt4ovqEBAZmUf4-z6-UGFSqaLSqTAkniUOcz-pGmkIdIQV2bWd06RU5GZ2zlEtsbSoANf1wMiO_sTgRjHFETIClz5TGZwJnYjtYjM0Xb4CKcMSrXACLiV1c8wmyuz5NU9sULvHXExjCtNALN_QB4OHGSA4kAnA",
                        "openHours": {
                            "openNextHalfHour": True,
                            "openNow": True
                        },
                        "openStatus": 0,
                        "poiImgExtra": {
                            "brand": {
                                "icon": None,
                                "jumpUrl": "imeituan://www.meituan.com/web?notitlebar=1&url=https%3A%2F%2Fmobilenext-web.meituan.com%2Fpoimoreinfo%3Fpoiid%3D519090134",
                                "tagId": 348,
                                "text": {
                                    "backgroundColor": "",
                                    "borderColor": "",
                                    "color": "",
                                    "content": "连锁"
                                }
                            }
                        },
                        "poiid": "519090134",
                        "poiidEncrypt": "qB4r137971a707b89de064b024915d7a711afcbe643598e9791ef29c7529e26evxu5",
                        "preferentialInfo": {
                            "backgroundColor": "#FFF1EC",
                            "morePreferential": "",
                            "poiToDealNum": 6,
                            "preferentials": [
                                [
                                    {
                                        "bestDeal": {
                                            "batchDealNumber": -1,
                                            "price": "?",
                                            "value": "1?"
                                        },
                                        "dealBackgroundPic": "",
                                        "dealGuideTags": {
                                            "icon": ""
                                        },
                                        "dealId": 894302312,
                                        "dealImgUrl": "http://p1.meituan.net/w.h/content/d77d8e5638b2b34e829d0a5c665335be303963.jpg@350_0_900_900a%7C267h_267w_2e_90Q",
                                        "dealSales": "",
                                        "dealTag": [
                                            {
                                                "icon": "",
                                                "text": {
                                                    "backgroundColor": "",
                                                    "borderColor": "",
                                                    "color": "",
                                                    "content": "半年售 2.2万+"
                                                },
                                                "type": "sales"
                                            }
                                        ],
                                        "discount": "",
                                        "icon": "https://p0.meituan.net/0.0.o/travelcube/e962ee69a3422d982e86a921779101d32697.png?width=16&height=16",
                                        "isLiveDeal": False,
                                        "isTimeLimitCoupon": False,
                                        "jumpUrl": "imeituan://www.meituan.com/mrn?mrn_biz=meishi&mrn_entry=lingyu-10746&mrn_component=main&source=yinpinxiaochi_pindaoye_liebiao_deal&scene=snack_list&dealId=894302312&poiId=519090134",
                                        "promotionIconTag": "",
                                        "promotionTag": "特惠促销",
                                        "promotionalGuideTag": {
                                            "icon": "https://p1.meituan.net/0.0.o//travelcube/b4527407c5247c3bcfdd9ef2e049ab1b547.png",
                                            "text": {
                                                "backgroundColor": "",
                                                "borderColor": "",
                                                "color": "#FF4B10",
                                                "content": "特惠促销"
                                            }
                                        },
                                        "saleChannel": "mainScene",
                                        "secondsKillEndTime": 0,
                                        "text": "【必点】牛肉面单人餐",
                                        "type": 1,
                                        "useRules": [
                                            "周一至周日",
                                            "免预约"
                                        ]
                                    }
                                ],
                                [
                                    {
                                        "bestDeal": {
                                            "batchDealNumber": -1,
                                            "price": "1?",
                                            "value": "2?"
                                        },
                                        "dealBackgroundPic": "",
                                        "dealGuideTags": {
                                            "icon": ""
                                        },
                                        "dealId": 1166787408,
                                        "dealImgUrl": "http://p0.meituan.net/w.h/deal/58c5df090d6301def8b1c7b0019e88a5237824.jpg@349_0_900_900a%7C267h_267w_2e_90Q",
                                        "dealSales": "",
                                        "dealTag": [
                                            {
                                                "icon": "",
                                                "text": {
                                                    "backgroundColor": "",
                                                    "borderColor": "",
                                                    "color": "",
                                                    "content": "半年售 1000+"
                                                },
                                                "type": "sales"
                                            }
                                        ],
                                        "icon": "https://p0.meituan.net/0.0.o/travelcube/e962ee69a3422d982e86a921779101d32697.png?width=16&height=16",
                                        "isLiveDeal": False,
                                        "isTimeLimitCoupon": False,
                                        "jumpUrl": "imeituan://www.meituan.com/mrn?mrn_biz=meishi&mrn_entry=lingyu-10746&mrn_component=main&source=yinpinxiaochi_pindaoye_liebiao_deal&scene=snack_list&dealId=1166787408&poiId=519090134",
                                        "promotionIconTag": "",
                                        "promotionTag": "",
                                        "saleChannel": "mainScene",
                                        "secondsKillEndTime": 0,
                                        "text": "【地道新疆味】特色包包菜炒馕",
                                        "type": 1,
                                        "useRules": [
                                            "周一至周日",
                                            "免预约"
                                        ]
                                    }
                                ]
                            ],
                            "textColor": "#FF4B10"
                        },
                        "reviewNumberDesc": "3409条",
                        "rotationTags": [
                            {
                                "icon": "",
                                "text": {
                                    "backgroundColor": "",
                                    "borderColor": "",
                                    "color": "#666666",
                                    "content": "季售6000+"
                                }
                            },
                            {
                                "icon": "",
                                "text": {
                                    "backgroundColor": "",
                                    "borderColor": "",
                                    "color": "#666666",
                                    "content": "30分钟前有人消费"
                                }
                            }
                        ],
                        "showType": "",
                        "smartTags": [
                            {
                                "icon": "",
                                "jumpUrl": "imeituan://www.meituan.com/web?notitlebar=1&url=https%3A%2F%2Fmobilenext-web.meituan.com%2FrankingList%3FboardType%3D8%26source%3D6%26ci%3D1%26areaId%3D9597%26cateId%3D21533%26districtId%3D0%26notitlebar%3D1%26poiId%3D519090134",
                                "rightIcon": "https://p0.meituan.net/travelcube/fc81086bc7528281c2df4cf25b97a5c3689.png",
                                "tagType": "",
                                "tagid": 431,
                                "text": {
                                    "backgroundColor": "#FFEDDE",
                                    "borderColor": "",
                                    "color": "#8E3C12",
                                    "content": "大红门风味地方菜人气榜第1名"
                                }
                            },
                            {
                                "icon": "",
                                "jumpUrl": "",
                                "rightIcon": "",
                                "tagType": "",
                                "tagid": 331,
                                "text": {
                                    "backgroundColor": "#F5F5F5",
                                    "borderColor": "",
                                    "color": "#666666",
                                    "content": "异域风情浓厚"
                                }
                            },
                            {
                                "icon": "",
                                "jumpUrl": "",
                                "rightIcon": "",
                                "tagType": "",
                                "tagid": 2709,
                                "text": {
                                    "backgroundColor": "#F5F5F5",
                                    "borderColor": "",
                                    "color": "#666666",
                                    "content": "回头客1千+"
                                }
                            },
                            {
                                "icon": "",
                                "jumpUrl": "",
                                "rightIcon": "",
                                "tagType": "",
                                "tagid": 2702,
                                "text": {
                                    "backgroundColor": "#F5F5F5",
                                    "borderColor": "",
                                    "color": "#666666",
                                    "content": "285人觉得口味地道"
                                }
                            },
                            {
                                "icon": "",
                                "jumpUrl": "",
                                "rightIcon": "",
                                "tagType": "",
                                "tagid": 2711,
                                "text": {
                                    "backgroundColor": "#F4F4F4",
                                    "borderColor": "",
                                    "color": "#666666",
                                    "content": "近期94%好评"
                                }
                            },
                            {
                                "icon": "",
                                "jumpUrl": "",
                                "rightIcon": "",
                                "tagType": "",
                                "tagid": 2687,
                                "text": {
                                    "backgroundColor": "#F5F5F5",
                                    "borderColor": "",
                                    "color": "#666666",
                                    "content": "30分钟前有人消费"
                                }
                            },
                            {
                                "icon": "",
                                "jumpUrl": "",
                                "rightIcon": "",
                                "tagType": "",
                                "tagid": 2798,
                                "text": {
                                    "backgroundColor": "#F4F4F4",
                                    "borderColor": "",
                                    "color": "#666666",
                                    "content": "地铁直达"
                                }
                            },
                            {
                                "icon": "",
                                "jumpUrl": "",
                                "rightIcon": "",
                                "tagType": "",
                                "tagid": 2766,
                                "text": {
                                    "backgroundColor": "#F4F4F4",
                                    "borderColor": "",
                                    "color": "#666666",
                                    "content": "有包厢"
                                }
                            },
                            {
                                "icon": "",
                                "jumpUrl": "",
                                "rightIcon": "",
                                "tagType": "",
                                "tagid": 2565,
                                "text": {
                                    "backgroundColor": "#F4F4F4",
                                    "borderColor": "",
                                    "color": "#666666",
                                    "content": "2578人推荐牛肉拉面"
                                }
                            }
                        ],
                        "styleType": 1,
                        "titleTags": [],
                        "traceData": {
                            "_apimeishi_rerank_report_data": "",
                            "avgPrice": "30.0",
                            "avgScore": "4.9",
                            "clientRerankFeatures": "{\"ctr\":\"0.17635931074619293\",\"DISTANCE\":\"2.147483647E9\",\"lng\":\"116.40134561050341\",\"userYidiStatus\":\"0\",\"discount\":\"6.0\",\"diningType\":\"2.0\",\"AVGPRICE\":\"30.0\",\"IN_SERVICE_TIME\":\"1.0\",\"POIBRANDID\":\"951900.0\",\"TYPEID_LEVEL2\":\"235.0\",\"AVGSCORE\":\"4.9\",\"lat\":\"39.816763001033294\",\"cvr\":\"0.024571897462010384\"}",
                            "distance": "",
                            "globalIdForFilterBar": "",
                            "sale": "6924"
                        },
                        "typeId": 235
                    },
                    "type": "shop"
                },
                {
                    "cardInfo": [
                        {
                            "adMark": "",
                            "adQueryId": "53788997-6ac4-4b54-81de-ac5318c4977b--5016661899222081730",
                            "clickUrl": "",
                            "id": "659160",
                            "imgUrl": "https://p1.meituan.net/linglong/66335db1a29252dc14e167a386ec1f53140843.jpg",
                            "impUrl": "",
                            "index": 0,
                            "rank": 0,
                            "rankTrace": "-999",
                            "thirdPartyClickUrls": [],
                            "thirdPartyImpUrls": [],
                            "type": 21,
                            "url": "imeituan://www.meituan.com/web?url=https%3A%2F%2Fmaker.meituan.com%2Fpage%2Fbe19312dac91abdf%2F393%3FpageId%3D8627%26cateringsrc%3Dzn_mtapp_dc_banner_5_zhongtong5"
                        },
                        {
                            "adMark": "",
                            "adQueryId": "53788997-6ac4-4b54-81de-ac5318c4977b--5016661899222081730",
                            "clickUrl": "",
                            "id": "657497",
                            "imgUrl": "https://p0.meituan.net/linglong/bf2f5d775b4f7c7512429a4152fbb31f243365.jpg",
                            "impUrl": "",
                            "index": 0,
                            "rank": 0,
                            "rankTrace": "-999",
                            "thirdPartyClickUrls": [],
                            "thirdPartyImpUrls": [],
                            "type": 21,
                            "url": "imeituan://www.meituan.com/web?url=https%3A%2F%2Fcube.meituan.com%2Fcube%2Fblock%2Ff6edf5f84050%2F323080%2Findex.html%3Fcateringsrc%3Dzn_mtapp_dc_banner_1_SDmeishizhongtong%26resourceV2%3D657497"
                        },
                        {
                            "adMark": "",
                            "adQueryId": "53788997-6ac4-4b54-81de-ac5318c4977b--5016661899222081730",
                            "clickUrl": "",
                            "id": "657192",
                            "imgUrl": "https://p0.meituan.net/linglong/c5bc471f8a9fc3142b72f4fdb405b455278847.png",
                            "impUrl": "",
                            "index": 0,
                            "rank": 0,
                            "rankTrace": "-999",
                            "thirdPartyClickUrls": [],
                            "thirdPartyImpUrls": [],
                            "type": 21,
                            "url": "imeituan://www.meituan.com/web?url=https%3A%2F%2Fcube.meituan.com%2Fcube%2Fblock%2Ff6156cc7f608e95f33bd8b5998cbc7cb%2F331993%2Findex.html%3Fcateringsrc%3Dzn_mtapp_dc_banner_5_wangyuyi0420250303"
                        }
                    ],
                    "type": "adsBanner"
                },
                {
                    "cardInfo": {
                        "areaName": "十三陵水库",
                        "avgPrice": 86,
                        "avgScore": 4.3,
                        "cateDinner": True,
                        "cateName": "家常菜",
                        "channel": "food",
                        "ctPoi": "111089410018614686773235396862104668571_a188676210_c5_e3056406926952507964_v7594677193464929655__-1",
                        "distance": "",
                        "extraServiceIcons": [],
                        "frontImg": "https://p0.meituan.net/adunion/1dc0a2f42045794969495bb543c55c2b278214.jpg%40240w_240h_1e_1c_1l%7Cwatermark%3D0",
                        "iUrl": "",
                        "lat": 40.273683,
                        "lng": 116.216203,
                        "name": "海棠小馆",
                        "nibBizConsistency": "WfRgPPZ1mw83ZOfZJaiJ7ABlrfql5ZI0MXWvFwFHcBDTndzVIgTkg59E4bD0aGYCk6zMYAvXndP7uqLQi-vg4DgMPjiKm6UBK1V03oDTTAJbrFPjyikhtkYIMt4ovqEBBw3PsToeNmo9yHGjSUmkeL5KGlstejsomFqCzLEBJd8t1yh0RZlsmALgs-25VuaIHFAOMHdurYLqaZBnLprv4Roj2Lf0fqT64Rb8_2dqfS3_HOSJhTbf_0uEYZvlAHSYDZrEYttA0_sS5lCq_AQgmA",
                        "openHours": {
                            "openNextHalfHour": True,
                            "openNow": True
                        },
                        "openStatus": 0,
                        "poiImgExtra": {
                            "topRight": {
                                "icon": "",
                                "tagId": 0,
                                "text": {
                                    "backgroundColor": "",
                                    "borderColor": "",
                                    "color": "",
                                    "content": "广告"
                                }
                            }
                        },
                        "poiid": "188676210",
                        "poiidEncrypt": "qB4r177070a109be9ee260b024915d7a711afcbe643598e9791ef29c7529e26evxu5",
                        "preferentialInfo": {
                            "backgroundColor": "#FFF1EC",
                            "morePreferential": "",
                            "poiToDealNum": 8,
                            "preferentials": [
                                [
                                    {
                                        "bestDeal": {
                                            "batchDealNumber": -1,
                                            "price": "1??",
                                            "value": "2??"
                                        },
                                        "dealBackgroundPic": "",
                                        "dealGuideTags": {
                                            "icon": ""
                                        },
                                        "dealId": 671220764,
                                        "dealImgUrl": "http://p1.meituan.net/w.h/deal/4122a426ebd4ce471c17a4be35c59fdf381699.jpg@271_0_699_699a%7C267h_267w_2e_90Q",
                                        "dealSales": "",
                                        "dealTag": [
                                            {
                                                "icon": "",
                                                "text": {
                                                    "backgroundColor": "",
                                                    "borderColor": "",
                                                    "color": "",
                                                    "content": "半年售 100+"
                                                },
                                                "type": "sales"
                                            }
                                        ],
                                        "discount": "",
                                        "icon": "https://p0.meituan.net/0.0.o/travelcube/e962ee69a3422d982e86a921779101d32697.png?width=16&height=16",
                                        "isLiveDeal": False,
                                        "isTimeLimitCoupon": False,
                                        "jumpUrl": "imeituan://www.meituan.com/mrn?mrn_biz=meishi&mrn_entry=lingyu-10746&mrn_component=main&source=yinpinxiaochi_pindaoye_liebiao_deal&scene=snack_list&dealId=671220764&poiId=188676210",
                                        "promotionIconTag": "",
                                        "promotionTag": "",
                                        "saleChannel": "mainScene",
                                        "secondsKillEndTime": 0,
                                        "text": "侉炖水库鱼双人餐",
                                        "type": 1,
                                        "useRules": [
                                            "周一至周日",
                                            "免预约"
                                        ]
                                    }
                                ],
                                [
                                    {
                                        "bestDeal": {
                                            "batchDealNumber": -1,
                                            "price": "3??",
                                            "value": "5??"
                                        },
                                        "dealBackgroundPic": "",
                                        "dealGuideTags": {
                                            "icon": ""
                                        },
                                        "dealId": 734587129,
                                        "dealImgUrl": "http://p1.meituan.net/w.h/deal/e8bdd4ac84177e312eb0a12bd83e2b99342850.jpg@272_0_698_698a%7C267h_267w_2e_90Q",
                                        "dealSales": "",
                                        "dealTag": [
                                            {
                                                "icon": "",
                                                "text": {
                                                    "backgroundColor": "",
                                                    "borderColor": "",
                                                    "color": "",
                                                    "content": "半年售 12"
                                                },
                                                "type": "sales"
                                            }
                                        ],
                                        "discount": "",
                                        "icon": "https://p0.meituan.net/0.0.o/travelcube/e962ee69a3422d982e86a921779101d32697.png?width=16&height=16",
                                        "isLiveDeal": False,
                                        "isTimeLimitCoupon": False,
                                        "jumpUrl": "imeituan://www.meituan.com/mrn?mrn_biz=meishi&mrn_entry=lingyu-10746&mrn_component=main&source=yinpinxiaochi_pindaoye_liebiao_deal&scene=snack_list&dealId=734587129&poiId=188676210",
                                        "promotionIconTag": "",
                                        "promotionTag": "",
                                        "saleChannel": "mainScene",
                                        "secondsKillEndTime": 0,
                                        "text": "【人气】热菜5-6人餐",
                                        "type": 1,
                                        "useRules": [
                                            "周一至周日",
                                            "免预约"
                                        ]
                                    }
                                ]
                            ],
                            "textColor": "#FF4B10"
                        },
                        "reportMessage": {
                            "adLx": "{\"accountid\":73688767,\"slotid\":50011,\"ad_request_id\":\"7594677193464929655\",\"launchid\":24699735,\"targetid\":10393519,\"entityid\":188676210,\"entitytype\":1,\"adshopid\":188676210,\"product_id\":\"74\"}",
                            "adsClickUrl": "https://mlog.dianping.com/api/cpv/billing?mbid=1.95&productid=74&priceMode=5&pctr=0.044780392199754715&display_id=50011&bg=0&recalled_match_unit=0&ad_cj=c1pa-cafX74bgqTBNfFgxgoCvj5mlUmeWpLzEz8hWwrpyorOnTHAano57TeEM50L1YhkWh5nGUlPvPqk9D_XP5JWUHcYbMBQYvB_4xg3K4NCPUVPZtCWPyecnxFZTCBeJRLyZBg2wEJ4AIoahQ&ad_ci=c1pa8cePU_dT0LzVbf5l1lJf-mU8w2aFV8ynHDg2WQr-jtKanzrAXGckuWKJMZwA1o5rTl0yTn9PtaKo6zHWKNUCEjJMLpJ8Z_s26Rg-L4RELBcfFrbjNnqXl0FcSDYP&utm_medium=android&discount=1&rankScore=-0.40819549560546875&mtlaunch_city_id=1&ecpcLambda=1.3|0.011184864&bu=28&category_id=1783&pos=1&freCtrl=False&mtuser_id64=0&adshoptype=226&pcvr=0.011184863803680981&client_version=12.22.200&mtdpid=000000000000079DE9975FBE548D79FB7125FC602382AA168675081685585060&bottomprice=1.0&lat=0.0&user_agent=android&city_id_platform=MT&launch_city_id=2&mtcategory_ids=1&lng=0.0&sver=2&AdExpPath=3-1002-4606,18-817-3805,18-4110-16795,18-4629-18788,3-1222-29278,3-140-565,18-765-3690,18-842-18601,18-4324-17417,18-7729-29220,18-7904-30039,3-4149-17077,18-4693-19053,3-1606-7070,18-7702-29095,18-10317-37494,18-10331-37589,18-6431-24638,3-6495-24893,3-4559-18493,18-1317-5672,3-164-5978,3-296-1803,18-338-2099,3-136-551,18-4363-17597,18-444-2514,3-12-28,18-2836-11523,3-62-31346,18-1595-7035,3-130-33564,18-8257-33579,18-7509-28478,18-7865-29823,18-4397-18062,3-1505-6694,18-4420-17809,3-844-3909,3-1376-5947,18-7594-28613,18-573-2979,18-1513-6675,18-6203-23628,18-1223-5391,3-201-1096,18-7521-28459,3-63-28645,3-414-2388,18-1347-5830,18-4624-18742,3-7518-28584,3-7469-28296,3-4674-18991,18-4628-18786,3-9162-33594,18-1531-24362,18-1543-6830,3-50-100,3-227-1297,18-4514-18471,3-1000-4604,18-1529-6752,18-1549-28363,18-1027-4757,18-7918-30118,3-6278-23977,18-7727-29203,18-293-1778,3-1578-6946,18-4496-18156,18-4623-18728&auctionTag=5|0&floatRatio=30&lite_set_cell=default-cell&bottomfen=100&mtuser_id=0&adsCtrStrategy=FoodMergedCVR&page_city_id=1&entityplat=2&ad_v=2&mtadshop_id=188676210&city_mode=1&is_target_city=1&mtpage_city_id=1&adidx=7&act=2",
                            "adsImpressionUrl": "https://mlog.dianping.com/api/cpv/action?mbid=1.95&productid=74&priceMode=5&pctr=0.044780392199754715&display_id=50011&bg=0&recalled_match_unit=0&ad_cj=c1pa-cafX74bgqTBNfFgxgoCvj5mlUmeWpLzEz8hWwrpyorOnTHAano57TeEM50L1YhkWh5nGUlPvPqk9D_XP5JWUHcYbMBQYvB_4xg3K4NCPUVPZtCWPyecnxFZTCBeJRLyZBg2wEJ4AIoahQ&ad_ci=c1pa8cePU_dT0LzVbf5l1lJf-mU8w2aFV8ynHDg2WQr-jtKanzrAXGckuWKJMZwA1o5rTl0yTn9PtaKo6zHWKNUCEjJMLpJ8Z_s26Rg-L4RELBcfFrbjNnqXl0FcSDYP&utm_medium=android&discount=1&rankScore=-0.40819549560546875&mtlaunch_city_id=1&ecpcLambda=1.3|0.011184864&bu=28&category_id=1783&pos=1&freCtrl=False&mtuser_id64=0&adshoptype=226&pcvr=0.011184863803680981&client_version=12.22.200&mtdpid=000000000000079DE9975FBE548D79FB7125FC602382AA168675081685585060&bottomprice=1.0&lat=0.0&user_agent=android&city_id_platform=MT&launch_city_id=2&mtcategory_ids=1&lng=0.0&sver=2&AdExpPath=3-1002-4606,18-817-3805,18-4110-16795,18-4629-18788,3-1222-29278,3-140-565,18-765-3690,18-842-18601,18-4324-17417,18-7729-29220,18-7904-30039,3-4149-17077,18-4693-19053,3-1606-7070,18-7702-29095,18-10317-37494,18-10331-37589,18-6431-24638,3-6495-24893,3-4559-18493,18-1317-5672,3-164-5978,3-296-1803,18-338-2099,3-136-551,18-4363-17597,18-444-2514,3-12-28,18-2836-11523,3-62-31346,18-1595-7035,3-130-33564,18-8257-33579,18-7509-28478,18-7865-29823,18-4397-18062,3-1505-6694,18-4420-17809,3-844-3909,3-1376-5947,18-7594-28613,18-573-2979,18-1513-6675,18-6203-23628,18-1223-5391,3-201-1096,18-7521-28459,3-63-28645,3-414-2388,18-1347-5830,18-4624-18742,3-7518-28584,3-7469-28296,3-4674-18991,18-4628-18786,3-9162-33594,18-1531-24362,18-1543-6830,3-50-100,3-227-1297,18-4514-18471,3-1000-4604,18-1529-6752,18-1549-28363,18-1027-4757,18-7918-30118,3-6278-23977,18-7727-29203,18-293-1778,3-1578-6946,18-4496-18156,18-4623-18728&auctionTag=5|0&floatRatio=30&lite_set_cell=default-cell&bottomfen=100&mtuser_id=0&adsCtrStrategy=FoodMergedCVR&page_city_id=1&entityplat=2&ad_v=2&mtadshop_id=188676210&city_mode=1&is_target_city=1&mtpage_city_id=1&adidx=7&act=3"
                        },
                        "reviewNumberDesc": "1188条",
                        "rotationTags": [
                            {
                                "icon": "",
                                "text": {
                                    "backgroundColor": "",
                                    "borderColor": "",
                                    "color": "#666666",
                                    "content": "季售100+"
                                }
                            },
                            {
                                "icon": "",
                                "text": {
                                    "backgroundColor": "",
                                    "borderColor": "",
                                    "color": "#666666",
                                    "content": "今日有人消费"
                                }
                            }
                        ],
                        "showType": "",
                        "smartTags": [
                            {
                                "icon": "",
                                "jumpUrl": "imeituan://www.meituan.com/web?notitlebar=1&url=https%3A%2F%2Fmobilenext-web.meituan.com%2FrankingList%3FboardType%3D8%26source%3D6%26ci%3D1%26areaId%3D22995%26cateId%3D21533%26districtId%3D0%26notitlebar%3D1%26poiId%3D188676210",
                                "rightIcon": "https://p0.meituan.net/travelcube/fc81086bc7528281c2df4cf25b97a5c3689.png",
                                "tagType": "",
                                "tagid": 431,
                                "text": {
                                    "backgroundColor": "#FFEDDE",
                                    "borderColor": "",
                                    "color": "#8E3C12",
                                    "content": "十三陵水库风味地方菜人气榜第3名"
                                }
                            },
                            {
                                "icon": "",
                                "jumpUrl": "",
                                "rightIcon": "",
                                "tagType": "",
                                "tagid": 331,
                                "text": {
                                    "backgroundColor": "#F5F5F5",
                                    "borderColor": "",
                                    "color": "#666666",
                                    "content": "「葱花饼」刚出锅的特别好吃😋"
                                }
                            },
                            {
                                "icon": "",
                                "jumpUrl": "",
                                "rightIcon": "",
                                "tagType": "",
                                "tagid": 340,
                                "text": {
                                    "backgroundColor": "#F5F5F5",
                                    "borderColor": "",
                                    "color": "#666666",
                                    "content": "收录6年"
                                }
                            },
                            {
                                "icon": "",
                                "jumpUrl": "",
                                "rightIcon": "",
                                "tagType": "",
                                "tagid": 2702,
                                "text": {
                                    "backgroundColor": "#F5F5F5",
                                    "borderColor": "",
                                    "color": "#666666",
                                    "content": "148人觉得分量足"
                                }
                            },
                            {
                                "icon": "",
                                "jumpUrl": "",
                                "rightIcon": "",
                                "tagType": "",
                                "tagid": 2687,
                                "text": {
                                    "backgroundColor": "#F5F5F5",
                                    "borderColor": "",
                                    "color": "#666666",
                                    "content": "今日有人消费"
                                }
                            },
                            {
                                "icon": "",
                                "jumpUrl": "",
                                "rightIcon": "",
                                "tagType": "",
                                "tagid": 2766,
                                "text": {
                                    "backgroundColor": "#F4F4F4",
                                    "borderColor": "",
                                    "color": "#666666",
                                    "content": "有包厢"
                                }
                            },
                            {
                                "icon": "",
                                "jumpUrl": "",
                                "rightIcon": "",
                                "tagType": "",
                                "tagid": 2565,
                                "text": {
                                    "backgroundColor": "#F4F4F4",
                                    "borderColor": "",
                                    "color": "#666666",
                                    "content": "246人推荐挎炖水库鱼"
                                }
                            }
                        ],
                        "styleType": 1,
                        "titleTags": [],
                        "traceData": {
                            "_apimeishi_rerank_report_data": "",
                            "avgPrice": "86.0",
                            "avgScore": "4.3",
                            "clientRerankFeatures": "",
                            "distance": "",
                            "globalIdForFilterBar": "",
                            "sale": "201"
                        },
                        "typeId": 2045
                    },
                    "type": "adsShop"
                },
                {
                    "cardInfo": {
                        "areaName": "",
                        "avgPrice": 87,
                        "avgScore": 4.7,
                        "cateDinner": True,
                        "cateName": "烤肉自助",
                        "channel": "food",
                        "ctPoi": "153724372769088362450865176448515935668_a1757778462_c6_e3056406926952507964",
                        "distance": "",
                        "extraServiceIcons": [
                            "https://p0.meituan.net/scarlett/14c10e3660cdd1d57620da2884c6e3dd7896.png"
                        ],
                        "frontImg": "https://img.meituan.net/content/90305d202877554fff2446829bfefc6f1189654.png%40240w_240h_1e_1c_1l%7Cwatermark%3D0",
                        "iUrl": "",
                        "lat": 39.904838,
                        "lng": 116.735173,
                        "name": "玫瑰花园自助烤肉（通州万象汇店）",
                        "nibBizConsistency": "WfRgPPZ1mw83ZOfZJaiJ7ABlrfql5ZI0MXWvFwFHcBDTndzVIgTkg59E4bD0aGYCk6zMYAvXndP7uqLQi-vg4Cw3kjHPV5kEsb9zF4dEaNVbrFPjyikhtkYIMt4ovqEBHjaeWwH5GXEbb8i9KGEfRfVk2CU_OVga_nUkhO7938X8T2KlFY_vhZlT2bCFUgzEztTKWUtHzxCRoCJl92pLtA",
                        "openHours": {
                            "openNextHalfHour": True,
                            "openNow": True
                        },
                        "openStatus": 0,
                        "poiImgExtra": {},
                        "poiid": "1757778462",
                        "poiidEncrypt": "qB4r177f7da009bf94e766a137925e736b0ee8e63d7690a26106e19c742bf23161vxu5",
                        "preferentialInfo": {
                            "backgroundColor": "#FFF1EC",
                            "morePreferential": "",
                            "poiToDealNum": 1,
                            "preferentials": [
                                [
                                    {
                                        "bestDeal": {
                                            "batchDealNumber": -1,
                                            "price": "9?",
                                            "value": "1??"
                                        },
                                        "dealBackgroundPic": "",
                                        "dealGuideTags": {
                                            "icon": ""
                                        },
                                        "dealId": 920994697,
                                        "dealImgUrl": "http://p1.meituan.net/w.h/deal/46b178b70f0e502f509b1c747d000b8b149843.jpg@350_0_900_900a%7C267h_267w_2e_90Q",
                                        "dealSales": "",
                                        "dealTag": [
                                            {
                                                "icon": "",
                                                "text": {
                                                    "backgroundColor": "",
                                                    "borderColor": "",
                                                    "color": "",
                                                    "content": "半年售 5.6万+"
                                                },
                                                "type": "sales"
                                            }
                                        ],
                                        "discount": "",
                                        "icon": "https://p0.meituan.net/0.0.o/travelcube/e962ee69a3422d982e86a921779101d32697.png?width=16&height=16",
                                        "isLiveDeal": False,
                                        "isTimeLimitCoupon": False,
                                        "jumpUrl": "imeituan://www.meituan.com/mrn?mrn_biz=meishi&mrn_entry=lingyu-10746&mrn_component=main&source=yinpinxiaochi_pindaoye_liebiao_deal&scene=snack_list&dealId=920994697&poiId=1757778462",
                                        "promotionIconTag": "",
                                        "promotionTag": "",
                                        "saleChannel": "mainScene",
                                        "secondsKillEndTime": 0,
                                        "text": "【女神节】单人自助烤肉",
                                        "type": 1,
                                        "useRules": [
                                            "周一至周日",
                                            "免预约"
                                        ]
                                    }
                                ]
                            ],
                            "textColor": "#FF4B10"
                        },
                        "reviewNumberDesc": "3839条",
                        "rotationTags": [
                            {
                                "icon": "",
                                "text": {
                                    "backgroundColor": "",
                                    "borderColor": "",
                                    "color": "#666666",
                                    "content": "季售3.7万+"
                                }
                            },
                            {
                                "icon": "",
                                "text": {
                                    "backgroundColor": "",
                                    "borderColor": "",
                                    "color": "#666666",
                                    "content": "4分钟前有人消费"
                                }
                            }
                        ],
                        "showType": "",
                        "smartTags": [
                            {
                                "icon": "https://p0.meituan.net/bizoperate/abd75055f50ab9c7acd63ed05359caa781563.gif?width=48&height=16&left=0&right=0&top=0&bottom=0&isCircle=0",
                                "jumpUrl": "imeituan://www.meituan.com/mlivemrnlist?scenekey=daocan&liveId=9981608&page_source=daocanpoilist",
                                "rightIcon": "",
                                "tagType": "",
                                "tagid": 1949
                            },
                            {
                                "icon": "https://p0.meituan.net/ingee/ff7c2a26962470092a35490803af3a759791.png?width=84&height=32&left=0&right=0&top=0&bottom=0&isCircle=0",
                                "jumpUrl": "imeituan://www.meituan.com/mrn?mrn_biz=meishi&mrn_entry=lingyu-307&mrn_component=main&chooseCityId=1&source=6&ci=1&areaId=0&cateId=10000&districtId=0&notitlebar=1&poiId=1757778462",
                                "rightIcon": "https://p0.meituan.net/ingee/13c5be5bb368121439f40cca9324bdcd581.png",
                                "tagType": "",
                                "tagid": 1121,
                                "text": {
                                    "backgroundColor": "#FFEDDE",
                                    "borderColor": "",
                                    "color": "#8E3C12",
                                    "content": "北京排队榜上榜餐厅"
                                }
                            },
                            {
                                "icon": "",
                                "jumpUrl": "imeituan://www.meituan.com/web?notitlebar=1&url=https%3A%2F%2Fmobilenext-web.meituan.com%2FrankingList%3FboardType%3D8%26source%3D6%26ci%3D1%26areaId%3D0%26cateId%3D40%26districtId%3D4751%26notitlebar%3D1%26poiId%3D1757778462",
                                "rightIcon": "https://p0.meituan.net/travelcube/fc81086bc7528281c2df4cf25b97a5c3689.png",
                                "tagType": "",
                                "tagid": 431,
                                "text": {
                                    "backgroundColor": "#FFEDDE",
                                    "borderColor": "",
                                    "color": "#8E3C12",
                                    "content": "通州区自助餐人气榜第1名"
                                }
                            },
                            {
                                "icon": "",
                                "jumpUrl": "",
                                "rightIcon": "",
                                "tagType": "",
                                "tagid": 2709,
                                "text": {
                                    "backgroundColor": "#F5F5F5",
                                    "borderColor": "",
                                    "color": "#666666",
                                    "content": "回头客3千+"
                                }
                            },
                            {
                                "icon": "",
                                "jumpUrl": "",
                                "rightIcon": "",
                                "tagType": "",
                                "tagid": 2702,
                                "text": {
                                    "backgroundColor": "#F5F5F5",
                                    "borderColor": "",
                                    "color": "#666666",
                                    "content": "576人觉得食材新鲜"
                                }
                            },
                            {
                                "icon": "",
                                "jumpUrl": "",
                                "rightIcon": "",
                                "tagType": "",
                                "tagid": 2752,
                                "text": {
                                    "backgroundColor": "#F4F4F4",
                                    "borderColor": "",
                                    "color": "#666666",
                                    "content": "近1小时128人看过"
                                }
                            },
                            {
                                "icon": "",
                                "jumpUrl": "",
                                "rightIcon": "",
                                "tagType": "",
                                "tagid": 2565,
                                "text": {
                                    "backgroundColor": "#F4F4F4",
                                    "borderColor": "",
                                    "color": "#666666",
                                    "content": "401人推荐小料"
                                }
                            }
                        ],
                        "styleType": 1,
                        "titleTags": [],
                        "traceData": {
                            "_apimeishi_rerank_report_data": "",
                            "avgPrice": "87.0",
                            "avgScore": "4.7",
                            "clientRerankFeatures": "{\"ctr\":\"0.19470544159412384\",\"DISTANCE\":\"2.147483647E9\",\"lng\":\"116.73517374595293\",\"userYidiStatus\":\"0\",\"discount\":\"5.1685395\",\"diningType\":\"2.0\",\"AVGPRICE\":\"87.0\",\"IN_SERVICE_TIME\":\"1.0\",\"POIBRANDID\":\"342650.0\",\"TYPEID_LEVEL2\":\"202.0\",\"TYPEID_LEVEL3\":\"171.0\",\"AVGSCORE\":\"4.7\",\"lat\":\"39.9048380748032\",\"cvr\":\"0.016815196722745895\"}",
                            "distance": "",
                            "globalIdForFilterBar": "",
                            "sale": "37383"
                        },
                        "typeId": 171
                    },
                    "type": "shop"
                },
                {
                    "cardInfo": {
                        "areaName": "西直门/动物园",
                        "avgPrice": 24,
                        "avgScore": 4.1,
                        "cateDinner": False,
                        "cateName": "西式快餐/汉堡",
                        "channel": "food",
                        "ctPoi": "153724372769088362450865176448515935668_a6903169_c7_e3056406926952507964",
                        "distance": "",
                        "extraServiceIcons": [
                            "https://p0.meituan.net/scarlett/14c10e3660cdd1d57620da2884c6e3dd7896.png",
                            "https://p0.meituan.net/travelcube/683bdf4ca9d8e9a0cf96234ce1a622e011487.png"
                        ],
                        "frontImg": "https://img.meituan.net/content/2c3746cc0ada62551ce08197fdb33d46144693.jpg%40240w_240h_1e_1c_1l%7Cwatermark%3D0",
                        "iUrl": "",
                        "lat": 39.941343,
                        "lng": 116.352517,
                        "name": "汉堡王（西直门凯德MALL店）",
                        "nibBizConsistency": "WfRgPPZ1mw83ZOfZJaiJ7ABlrfql5ZI0MXWvFwFHcBDTndzVIgTkg59E4bD0aGYCk6zMYAvXndP7uqLQi-vg4JGQdCYtbxi4TAb83xJWk5g5Cmyv4vs3MQcx1uYT4Cu41kuR1Fk0s0kwB6Qd2oxf1S-7QGnyliCwS8cFDAgIAdqQk-1prMBGFu7yS4aF7Wx1iO_sTgRjHFETIClz5TGZwJnYjtYjM0Xb4CKcMSrXACLiV1c8wmyuz5NU9sULvHXE4xm8l-zNBIB7LPDDR6GqDQ",
                        "openHours": {
                            "openNextHalfHour": True,
                            "openNow": True
                        },
                        "openStatus": 0,
                        "poiImgExtra": {},
                        "poiid": "6903169",
                        "poiidEncrypt": "qB4r107178a40fbe95f060a0249b4e747156fda42f76cbe9720df39f6766vxu5",
                        "preferentialInfo": {
                            "backgroundColor": "#FFF1EC",
                            "morePreferential": "",
                            "poiToDealNum": 84,
                            "preferentials": [
                                [
                                    {
                                        "bestDeal": {
                                            "batchDealNumber": -1,
                                            "price": "3?",
                                            "value": "5?"
                                        },
                                        "dealBackgroundPic": "https://p1.meituan.net/travelcube/e53c4b3c311e60107365db8c07afb73d82643.png",
                                        "dealGuideTags": {
                                            "backgroundUrl": "https://p0.meituan.net/ingee/20f7266f814c61fff6f85ec566314f428678.png",
                                            "icon": "https://p1.meituan.net/96.0/travelcube/fdc237b438185ac20d5695b4b6a87d8b17273.gif?width=12&height=12",
                                            "text": {
                                                "backgroundColor": "",
                                                "borderColor": "",
                                                "color": "#FFFFFF",
                                                "content": "直播专享价"
                                            },
                                            "type": "",
                                            "value": ""
                                        },
                                        "dealId": 1195932379,
                                        "dealImgUrl": "http://p1.meituan.net/w.h/content/51a22ceeb61667afabc986a2af63036d269640.jpg@233_0_720_720a%7C267h_267w_2e_90Q",
                                        "dealSales": "",
                                        "dealTag": [
                                            {
                                                "icon": "",
                                                "text": {
                                                    "backgroundColor": "",
                                                    "borderColor": "",
                                                    "color": "",
                                                    "content": "半年售 4.6万+"
                                                },
                                                "type": "sales"
                                            }
                                        ],
                                        "discount": "",
                                        "icon": "https://p1.meituan.net/travelcube/8af6bd79150bbe7d15ab5e65728f996752939.gif?width=16&height=16",
                                        "isLiveDeal": True,
                                        "isTimeLimitCoupon": False,
                                        "jumpUrl": "imeituan://www.meituan.com/mlivemrn?mrn_biz=hotel&mrn_entry=hotel-mlive&mrn_component=hotel-mlive&isOrganizer=False&type=0&liveId=10190512&page_source=meishi_channel&mrn_min_version=0.0.600&traceMonitorInfo=%7B%22needMetricFields%22%3A%5B%22pageSource%22%2C%22querySource%22%2C%22cat0%22%5D%2C%22querySource%22%3A%22dao_can_toc_poi_page_live_goods_exclusive_price_tag%22%2C%22pageSource%22%3A%22meishi_channel%22%2C%22cat0%22%3A%227200%22%7D&rec_goods_id=1195932379&rec_goods_type=9&rec_goods_id=1195932379&rec_goods_type=9&rec_type=0",
                                        "promotionIconTag": "",
                                        "promotionTag": "直播专享价",
                                        "promotionalGuideTag": {
                                            "icon": "https://p1.meituan.net/travelcube/8af6bd79150bbe7d15ab5e65728f996752939.gif?width=16&height=16",
                                            "text": {
                                                "backgroundColor": "",
                                                "borderColor": "",
                                                "color": "#FF4B10",
                                                "content": "直播专享价"
                                            }
                                        },
                                        "saleChannel": "foodLiveStreaming",
                                        "secondsKillEndTime": 0,
                                        "text": "大嘴安格斯2件套",
                                        "type": 1,
                                        "useRules": [
                                            "周一至周日",
                                            "免预约"
                                        ]
                                    }
                                ],
                                [
                                    {
                                        "bestDeal": {
                                            "batchDealNumber": -1,
                                            "price": "1?",
                                            "value": "2?"
                                        },
                                        "dealBackgroundPic": "",
                                        "dealGuideTags": {
                                            "icon": ""
                                        },
                                        "dealId": 973127259,
                                        "dealImgUrl": "http://p0.meituan.net/w.h/content/cb3eb25b7790180db8a8a2df6e116381297464.jpg@233_0_720_720a%7C267h_267w_2e_90Q",
                                        "dealSales": "",
                                        "dealTag": [
                                            {
                                                "icon": "",
                                                "text": {
                                                    "backgroundColor": "",
                                                    "borderColor": "",
                                                    "color": "",
                                                    "content": "半年售 22万+"
                                                },
                                                "type": "sales"
                                            }
                                        ],
                                        "discount": "",
                                        "icon": "https://p0.meituan.net/0.0.o/travelcube/e962ee69a3422d982e86a921779101d32697.png?width=16&height=16",
                                        "isLiveDeal": False,
                                        "isTimeLimitCoupon": False,
                                        "jumpUrl": "imeituan://www.meituan.com/mrn?mrn_biz=meishi&mrn_entry=lingyu-10746&mrn_component=main&source=yinpinxiaochi_pindaoye_liebiao_deal&scene=snack_list&dealId=973127259&poiId=6903169",
                                        "promotionIconTag": "",
                                        "promotionTag": "",
                                        "saleChannel": "mainScene",
                                        "secondsKillEndTime": 0,
                                        "text": "【1+1】小食随心配",
                                        "type": 1,
                                        "useRules": [
                                            "周一至周日",
                                            "免预约"
                                        ]
                                    }
                                ]
                            ],
                            "textColor": "#FF4B10"
                        },
                        "reviewNumberDesc": "1.2万条",
                        "rotationTags": [
                            {
                                "icon": "",
                                "text": {
                                    "backgroundColor": "",
                                    "borderColor": "",
                                    "color": "#666666",
                                    "content": "季售1.1万+"
                                }
                            },
                            {
                                "icon": "",
                                "text": {
                                    "backgroundColor": "",
                                    "borderColor": "",
                                    "color": "#666666",
                                    "content": "2分钟前有人消费"
                                }
                            }
                        ],
                        "showType": "",
                        "smartTags": [
                            {
                                "icon": "https://p0.meituan.net/bizoperate/abd75055f50ab9c7acd63ed05359caa781563.gif?width=48&height=16&left=0&right=0&top=0&bottom=0&isCircle=0",
                                "jumpUrl": "imeituan://www.meituan.com/mlivemrnlist?scenekey=daocan&liveId=10190512&page_source=daocanpoilist",
                                "rightIcon": "",
                                "tagType": "",
                                "tagid": 1949
                            },
                            {
                                "icon": "",
                                "jumpUrl": "",
                                "rightIcon": "",
                                "tagType": "",
                                "tagid": 2718,
                                "text": {
                                    "backgroundColor": "#FFF1EC",
                                    "borderColor": "",
                                    "color": "#FF4B10",
                                    "content": "秒提·在线点"
                                }
                            },
                            {
                                "icon": "",
                                "jumpUrl": "imeituan://www.meituan.com/web?notitlebar=1&url=https%3A%2F%2Fmobilenext-web.meituan.com%2FrankingList%3FboardType%3D8%26source%3D6%26ci%3D1%26areaId%3D685%26cateId%3D36%26districtId%3D0%26notitlebar%3D1%26poiId%3D6903169",
                                "rightIcon": "https://p0.meituan.net/travelcube/fc81086bc7528281c2df4cf25b97a5c3689.png",
                                "tagType": "",
                                "tagid": 431,
                                "text": {
                                    "backgroundColor": "#FFEDDE",
                                    "borderColor": "",
                                    "color": "#8E3C12",
                                    "content": "西直门/动物园小吃快餐人气榜第1名"
                                }
                            },
                            {
                                "icon": "",
                                "jumpUrl": "",
                                "rightIcon": "",
                                "tagType": "",
                                "tagid": 331,
                                "text": {
                                    "backgroundColor": "#F5F5F5",
                                    "borderColor": "",
                                    "color": "#666666",
                                    "content": "天椒皇堡，好吃不贵，汉堡控必点"
                                }
                            },
                            {
                                "icon": "",
                                "jumpUrl": "",
                                "rightIcon": "",
                                "tagType": "",
                                "tagid": 340,
                                "text": {
                                    "backgroundColor": "#F5F5F5",
                                    "borderColor": "",
                                    "color": "#666666",
                                    "content": "收录11年"
                                }
                            },
                            {
                                "icon": "",
                                "jumpUrl": "",
                                "rightIcon": "",
                                "tagType": "",
                                "tagid": 2710,
                                "text": {
                                    "backgroundColor": "#F4F4F4",
                                    "borderColor": "",
                                    "color": "#666666",
                                    "content": "收藏2千+"
                                }
                            },
                            {
                                "icon": "",
                                "jumpUrl": "",
                                "rightIcon": "",
                                "tagType": "",
                                "tagid": 2709,
                                "text": {
                                    "backgroundColor": "#F5F5F5",
                                    "borderColor": "",
                                    "color": "#666666",
                                    "content": "回头客1万+"
                                }
                            },
                            {
                                "icon": "",
                                "jumpUrl": "",
                                "rightIcon": "",
                                "tagType": "",
                                "tagid": 2702,
                                "text": {
                                    "backgroundColor": "#F5F5F5",
                                    "borderColor": "",
                                    "color": "#666666",
                                    "content": "909人觉得性价比高"
                                }
                            },
                            {
                                "icon": "",
                                "jumpUrl": "",
                                "rightIcon": "",
                                "tagType": "",
                                "tagid": 2752,
                                "text": {
                                    "backgroundColor": "#F4F4F4",
                                    "borderColor": "",
                                    "color": "#666666",
                                    "content": "近1小时58人看过"
                                }
                            },
                            {
                                "icon": "",
                                "jumpUrl": "",
                                "rightIcon": "",
                                "tagType": "",
                                "tagid": 2565,
                                "text": {
                                    "backgroundColor": "#F4F4F4",
                                    "borderColor": "",
                                    "color": "#666666",
                                    "content": "445人推荐狠霸王牛堡"
                                }
                            }
                        ],
                        "styleType": 1,
                        "titleTags": [],
                        "traceData": {
                            "_apimeishi_rerank_report_data": "",
                            "avgPrice": "24.0",
                            "avgScore": "4.1",
                            "clientRerankFeatures": "{\"ctr\":\"0.14554345607757568\",\"DISTANCE\":\"2.147483647E9\",\"lng\":\"116.35251814636945\",\"userYidiStatus\":\"0\",\"discount\":\"3.5119047\",\"diningType\":\"3.0\",\"AVGPRICE\":\"24.0\",\"IN_SERVICE_TIME\":\"1.0\",\"POIBRANDID\":\"185877.0\",\"TYPEID_LEVEL2\":\"10.0\",\"TYPEID_LEVEL3\":\"1848.0\",\"AVGSCORE\":\"4.1\",\"lat\":\"39.94134121655367\",\"cvr\":\"0.04795384407043457\"}",
                            "distance": "",
                            "globalIdForFilterBar": "",
                            "sale": "11644"
                        },
                        "typeId": 1848
                    },
                    "type": "shop"
                },
                {
                    "cardInfo": {
                        "areaName": "回龙观",
                        "avgPrice": 0,
                        "avgScore": 4.3,
                        "cateDinner": True,
                        "cateName": "烤鱼",
                        "channel": "food",
                        "ctPoi": "111089410018614686773235396862104668571_a876139901_c8_e3056406926952507964_v7594677193464929655__-1",
                        "distance": "",
                        "extraServiceIcons": [],
                        "frontImg": "https://p0.meituan.net/adunion/61e330320d6f4256105d101e6a2191b1269911.jpg%40240w_240h_1e_1c_1l%7Cwatermark%3D0",
                        "iUrl": "",
                        "lat": 40.079711,
                        "lng": 116.322493,
                        "name": "巴蜀金钩钓·烤鱼·精品川湘菜",
                        "nibBizConsistency": "WfRgPPZ1mw83ZOfZJaiJ7ABlrfql5ZI0MXWvFwFHcBDTndzVIgTkg59E4bD0aGYCk6zMYAvXndP7uqLQi-vg4GYjGTfQsOZM4NtsamC-HEg5Cmyv4vs3MQcx1uYT4Cu4a8YcSRxfJVU82iJHmp1II0ePDenCmI2-kjpuvPRBUkHIWxslZWPS9o7D3FZvdep_9HVsWaYtnjoctHSKLdWU0pQ-Q-7e_98y5sNaY7LgBx4",
                        "openHours": {
                            "openNextHalfHour": True,
                            "openNow": True
                        },
                        "openStatus": 0,
                        "poiImgExtra": {
                            "brand": {
                                "icon": None,
                                "jumpUrl": "",
                                "tagId": 1070
                            },
                            "topRight": {
                                "icon": "",
                                "tagId": 0,
                                "text": {
                                    "backgroundColor": "",
                                    "borderColor": "",
                                    "color": "",
                                    "content": "广告"
                                }
                            }
                        },
                        "poiid": "876139901",
                        "poiidEncrypt": "qB4r1e7f7ea60db195e361b024915d7a711afcbe643598e9791ef29c7529e26evxu5",
                        "preferentialInfo": {
                            "backgroundColor": "#FFF1EC",
                            "morePreferential": "",
                            "poiToDealNum": 1,
                            "preferentials": [
                                [
                                    {
                                        "bestDeal": {
                                            "batchDealNumber": 0,
                                            "price": "9?"
                                        },
                                        "dealBackgroundPic": "",
                                        "dealGuideTags": {
                                            "backgroundUrl": "https://p0.meituan.net/ingee/08f68188f871b45f3deaa9f3eec7be485995.png",
                                            "icon": "",
                                            "text": {
                                                "backgroundColor": "",
                                                "borderColor": "",
                                                "color": "#FFFFFF",
                                                "content": "新品"
                                            },
                                            "type": "",
                                            "value": ""
                                        },
                                        "dealId": 1279307798,
                                        "dealImgUrl": "https://p0.meituan.net/travelcube/571eee54492525f0507c6be4380fb0e22252.png",
                                        "dealTag": [
                                            {
                                                "icon": "",
                                                "text": {
                                                    "backgroundColor": "",
                                                    "borderColor": "",
                                                    "color": "",
                                                    "content": "半年售 200+"
                                                },
                                                "type": "sales"
                                            }
                                        ],
                                        "icon": "https://p0.meituan.net/0.0.o/travelcube/06e4fea268df35c32200a7ca90c8df812818.png",
                                        "isLiveDeal": False,
                                        "jumpUrl": "imeituan://www.meituan.com/mrn?mrn_biz=meishi&mrn_entry=lingyu-10746&mrn_component=main&source=yinpinxiaochi_pindaoye_liebiao_deal&scene=snack_list&dealId=1279307798&poiId=876139901",
                                        "promotionTag": "",
                                        "saleChannel": "mainScene",
                                        "secondsKillEndTime": 0,
                                        "text": "100元代金券",
                                        "type": 2,
                                        "useRules": [
                                            "周一至周日",
                                            "免预约"
                                        ]
                                    }
                                ]
                            ],
                            "textColor": "#FF4B10"
                        },
                        "reportMessage": {
                            "adLx": "{\"accountid\":80970389,\"slotid\":50011,\"ad_request_id\":\"7594677193464929655\",\"launchid\":40717140,\"targetid\":53206526,\"entityid\":876139901,\"entitytype\":1,\"adshopid\":876139901,\"product_id\":\"74\"}",
                            "adsClickUrl": "https://mlog.dianping.com/api/cpv/billing?mbid=1.46&productid=74&priceMode=6&pctr=0.025581149384379387&display_id=50011&bg=0&recalled_match_unit=0&ad_cj=nJ5dYLcRKbmIgDaUfVIhRlN7VnXutwfYGcHe_y6MKnVhpL33nfn9coFDWBobRBLUqGoirNFLbDkiTZGCC7PXrTu4ww0fPV5Tdsr74bNoSEPpbzTU_sd5VAt51ktrgbhoifxAQEt2hKv_q_Ev4A&ad_ci=nJ5daLYBJfDA0i6AJVsgVwMoFCmx4SjDFJ-D9SqTLHl-4O2jn_L9RJxeDEsVThXUrGsts5MfOw8iRMmOFLDVunzsgUhLfwx_c8Gy67NhTETvfmaEjqEMXQR-ikQ7jPw8&utm_medium=android&discount=1&rankScore=-9.30006217956543&mtlaunch_city_id=1&bu=28&category_id=102&pos=1&freCtrl=False&mtuser_id64=0&adshoptype=226&pcvr=0.026928538219895284&client_version=12.22.200&mtdpid=000000000000079DE9975FBE548D79FB7125FC602382AA168675081685585060&bottomprice=0.7300000190734863&lat=0.0&user_agent=android&city_id_platform=MT&launch_city_id=2&mtcategory_ids=1&lng=0.0&sver=2&AdExpPath=3-1002-4606,18-817-3805,18-4110-16795,18-4629-18788,3-1222-29278,3-140-565,18-765-3690,18-842-18601,18-4324-17417,18-7729-29220,18-7904-30039,3-4149-17077,18-4693-19053,3-1606-7070,18-7702-29095,18-10317-37494,18-10331-37589,18-6431-24638,3-6495-24893,3-4559-18493,18-1317-5672,3-164-5978,3-296-1803,18-338-2099,3-136-551,18-4363-17597,18-444-2514,3-12-28,18-2836-11523,3-62-31346,18-1595-7035,3-130-33564,18-8257-33579,18-7509-28478,18-7865-29823,18-4397-18062,3-1505-6694,18-4420-17809,3-844-3909,3-1376-5947,18-7594-28613,18-573-2979,18-1513-6675,18-6203-23628,18-1223-5391,3-201-1096,18-7521-28459,3-63-28645,3-414-2388,18-1347-5830,18-4624-18742,3-7518-28584,3-7469-28296,3-4674-18991,18-4628-18786,3-9162-33594,18-1531-24362,18-1543-6830,3-50-100,3-227-1297,18-4514-18471,3-1000-4604,18-1529-6752,18-1549-28363,18-1027-4757,18-7918-30118,3-6278-23977,18-7727-29203,18-293-1778,3-1578-6946,18-4496-18156,18-4623-18728&floatRatio=100&lite_set_cell=default-cell&bottomfen=73&mtuser_id=0&adsCtrStrategy=FoodMergedCVR&page_city_id=1&entityplat=2&ad_v=2&mtadshop_id=876139901&city_mode=1&is_target_city=1&mtpage_city_id=1&adidx=10&act=2",
                            "adsImpressionUrl": "https://mlog.dianping.com/api/cpv/action?mbid=1.46&productid=74&priceMode=6&pctr=0.025581149384379387&display_id=50011&bg=0&recalled_match_unit=0&ad_cj=nJ5dYLcRKbmIgDaUfVIhRlN7VnXutwfYGcHe_y6MKnVhpL33nfn9coFDWBobRBLUqGoirNFLbDkiTZGCC7PXrTu4ww0fPV5Tdsr74bNoSEPpbzTU_sd5VAt51ktrgbhoifxAQEt2hKv_q_Ev4A&ad_ci=nJ5daLYBJfDA0i6AJVsgVwMoFCmx4SjDFJ-D9SqTLHl-4O2jn_L9RJxeDEsVThXUrGsts5MfOw8iRMmOFLDVunzsgUhLfwx_c8Gy67NhTETvfmaEjqEMXQR-ikQ7jPw8&utm_medium=android&discount=1&rankScore=-9.30006217956543&mtlaunch_city_id=1&bu=28&category_id=102&pos=1&freCtrl=False&mtuser_id64=0&adshoptype=226&pcvr=0.026928538219895284&client_version=12.22.200&mtdpid=000000000000079DE9975FBE548D79FB7125FC602382AA168675081685585060&bottomprice=0.7300000190734863&lat=0.0&user_agent=android&city_id_platform=MT&launch_city_id=2&mtcategory_ids=1&lng=0.0&sver=2&AdExpPath=3-1002-4606,18-817-3805,18-4110-16795,18-4629-18788,3-1222-29278,3-140-565,18-765-3690,18-842-18601,18-4324-17417,18-7729-29220,18-7904-30039,3-4149-17077,18-4693-19053,3-1606-7070,18-7702-29095,18-10317-37494,18-10331-37589,18-6431-24638,3-6495-24893,3-4559-18493,18-1317-5672,3-164-5978,3-296-1803,18-338-2099,3-136-551,18-4363-17597,18-444-2514,3-12-28,18-2836-11523,3-62-31346,18-1595-7035,3-130-33564,18-8257-33579,18-7509-28478,18-7865-29823,18-4397-18062,3-1505-6694,18-4420-17809,3-844-3909,3-1376-5947,18-7594-28613,18-573-2979,18-1513-6675,18-6203-23628,18-1223-5391,3-201-1096,18-7521-28459,3-63-28645,3-414-2388,18-1347-5830,18-4624-18742,3-7518-28584,3-7469-28296,3-4674-18991,18-4628-18786,3-9162-33594,18-1531-24362,18-1543-6830,3-50-100,3-227-1297,18-4514-18471,3-1000-4604,18-1529-6752,18-1549-28363,18-1027-4757,18-7918-30118,3-6278-23977,18-7727-29203,18-293-1778,3-1578-6946,18-4496-18156,18-4623-18728&floatRatio=100&lite_set_cell=default-cell&bottomfen=73&mtuser_id=0&adsCtrStrategy=FoodMergedCVR&page_city_id=1&entityplat=2&ad_v=2&mtadshop_id=876139901&city_mode=1&is_target_city=1&mtpage_city_id=1&adidx=10&act=3"
                        },
                        "reviewNumberDesc": "66条",
                        "rotationTags": [
                            {
                                "icon": "",
                                "text": {
                                    "backgroundColor": "",
                                    "borderColor": "",
                                    "color": "#666666",
                                    "content": "季售100+"
                                }
                            },
                            {
                                "icon": "",
                                "text": {
                                    "backgroundColor": "",
                                    "borderColor": "",
                                    "color": "#666666",
                                    "content": "10分钟前有人消费"
                                }
                            }
                        ],
                        "showType": "",
                        "smartTags": [
                            {
                                "icon": "",
                                "jumpUrl": "",
                                "rightIcon": "",
                                "tagType": "",
                                "tagid": 2687,
                                "text": {
                                    "backgroundColor": "#F5F5F5",
                                    "borderColor": "",
                                    "color": "#666666",
                                    "content": "10分钟前有人消费"
                                }
                            },
                            {
                                "icon": "",
                                "jumpUrl": "",
                                "rightIcon": "",
                                "tagType": "",
                                "tagid": 2766,
                                "text": {
                                    "backgroundColor": "#F4F4F4",
                                    "borderColor": "",
                                    "color": "#666666",
                                    "content": "有包厢"
                                }
                            },
                            {
                                "icon": "",
                                "jumpUrl": "",
                                "rightIcon": "",
                                "tagType": "",
                                "tagid": 2565,
                                "text": {
                                    "backgroundColor": "#F4F4F4",
                                    "borderColor": "",
                                    "color": "#666666",
                                    "content": "网友推荐剑门关辣子鸡"
                                }
                            }
                        ],
                        "styleType": 1,
                        "titleTags": [],
                        "traceData": {
                            "_apimeishi_rerank_report_data": "",
                            "avgPrice": "0.0",
                            "avgScore": "4.3",
                            "clientRerankFeatures": "",
                            "distance": "",
                            "globalIdForFilterBar": "",
                            "sale": "253"
                        },
                        "typeId": 2032
                    },
                    "type": "adsShop"
                }
            ],
            "poiCount": 10,
            "totalCount": 800
        },
        "globalId": "39ea27799f594f2a906ac378862c87f7",
        "notification": "",
        "picassoViews": [],
        "queryId": "D460ED02-3DA2-40E2-937A-B638FBAFB7A3",
        "requestId": "3056406926952507964"
    }
}, 'headers': {'Age': '259', 'Alt-Svc': 'h3=":443"; ma=2592000,h3-29=":443"; ma=2592000', 'Content-Disposition': 'attachment', 'Content-Length': '3455', 'Content-Type': 'application/x-protobuf', 'Date': 'Sun, 09 Mar 2025 09:49:57 GMT', 'Server': 'scaffolding on HTTPServer2', 'Vary': 'Accept-Encoding', 'X-Content-Type-Options': 'nosniff', 'X-Frame-Options': 'SAMEORIGIN', 'X-XSS-Protection': '0', 'lyrebird': 'proxy'}, 'timestamp': 1741514056.89}}]

def main():
    
    # 分析流量详情
    results = filter_flow_details(flows, '帮我找到页面中用于展示商品的请求,请求中包含餐饮商家信息或套餐信息')
    
    # 打印分析结果
    print(results)

if __name__ == '__main__':
    main()