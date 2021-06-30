import ast
import pathlib
import re
import urllib.parse

import fastapi
import fastapi.templating
import lxml.html
import requests


class Session:
    def __init__(self) -> None:
        self.session = requests.Session()

    scheme = 'https'
    netloc = 'gra206.aca.ntu.edu.tw'
    path = '/classrm/index.php/acarm/'
    params = ''
    query = ''
    fragment = ''
    base = urllib.parse.urlunparse(urllib.parse.ParseResult(scheme, netloc, path, params, query, fragment))

    def webcr_use_new(self, SYearDDL, BuildingDDL, RoomDDL, SelectButton='查詢'):
        query = {
            'SYearDDL': SYearDDL,
            'BuildingDDL': BuildingDDL,
            'RoomDDL': RoomDDL,
            'SelectButton': SelectButton,
        }
        response = self.response('webcr-use-new', query)
        response.raise_for_status()
        m = re.search(r'var timeDT = (.*?);', response.text)
        assert m is not None
        return ast.literal_eval(m.groups()[0])

    def get_classroom_by_building(self, building=None):
        query = {}
        if building is not None:
            query['building'] = building
        response = self.response('get-classroom-by-building', query)
        response.raise_for_status()
        return response.json()

    def webcr_use_new_default_options(self):
        response = self.response('webcr-use-new', {})
        html = lxml.html.document_fromstring(response.text)
        SYearDDL = html.xpath('//*[@id="SYearDDL"]/option')
        SYearDDL = [(option.get('value'), option.text_content()) for option in SYearDDL]
        BuildingDDL = html.xpath('//*[@id="BuildingDDL"]/option')
        BuildingDDL = [(option.get('value'), option.text_content()) for option in BuildingDDL]
        return {'SYearDDL': SYearDDL, 'BuildingDDL': BuildingDDL}

    def response(self, url, query):
        url = urllib.parse.urljoin(self.base, url)
        parse_result = list(urllib.parse.urlparse(url))
        query = urllib.parse.urlencode(query)
        parse_result[4] = query
        url = urllib.parse.urlunparse(parse_result)
        response = self.session.get(url)
        return response


app = fastapi.FastAPI()

session = Session()

templates = fastapi.templating.Jinja2Templates(directory=str(pathlib.Path(__file__).parent / 'templates'))


@app.get('/', response_class=fastapi.responses.HTMLResponse)
def read_root(request: fastapi.Request):
    return templates.TemplateResponse('index.html', {
        'request': request,
        **session.webcr_use_new_default_options(),
    })


@app.get('/get-classroom-by-building')
def get_classroom_by_building(building=None):
    return session.get_classroom_by_building(building)


@app.get('/webcr-use-new')
def webcr_use_new(SYearDDL, BuildingDDL, RoomDDL, SelectButton='查詢'):
    return session.webcr_use_new(SYearDDL, BuildingDDL, RoomDDL, SelectButton)


session.webcr_use_new_default_options()
