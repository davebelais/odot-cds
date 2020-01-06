"""
This module provides functionality for programmatically interacting with the
Oregon Department of Transportation's (ODOT's) Crash Data System (CDS). All
functionality in this module corresponds to functionality exposed online at
https://zigzag.odot.state.or.us/. Higher-level functionality for the CDS501
extract can be found in the module `odot_cds.cds501`.
"""
import enum
import functools
import random
from dataclasses import dataclass, fields
from datetime import date
from http.client import HTTPResponse
from http.cookiejar import CookieJar, Cookie
from io import StringIO
from typing import (
    Dict, Optional, Union, Callable, List
)
from urllib.parse import urlencode
from urllib.request import (
    build_opener, HTTPCookieProcessor, OpenerDirector, Request,
    HTTPErrorProcessor
)
from xml.etree import ElementTree
from xml.etree.ElementTree import Element

import lxml.html
import lxml.etree
import sob

HOSTNAME: str = 'zigzag.odot.state.or.us'
TODAY: date = date.today()


def get_last_year_end(today: date = TODAY) -> date:
    return (
        today
        if today.month == 12 and today.day == 31 else
        date(today.year - 1, 12, 31)
    )


def get_year_start(today: date) -> date:
    return date(today.year, 1, 1)


# The default end date is the end of the last complete year
DEFAULT_END_DATE: date = get_last_year_end(TODAY)

# The default start date is the start of the last complete year
DEFAULT_BEGIN_DATE: date = get_year_start(DEFAULT_END_DATE)

_DEFAULT_HEADERS: Dict[str, str] = {
    'Accept': (
        'text/html,application/xhtml+xml,application/xml;q=0.9,'
        'image/webp,image/apng,*/*;q=0.8,application/'
        'signed-exchange;v=b3'
    ),
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'en-US,en;q=0.9',
    'Cache-Control': 'no-cache',
    'Connection': 'keep-alive',
    'Host': 'zigzag.odot.state.or.us',
    'Pragma': 'no-cache',
    'Sec-Fetch-Mode': 'navigate',  # cors
    'Sec-Fetch-Site': 'same-origin',
    'Sec-Fetch-User': '?1',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': (
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_1) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/78.0.3904.108 Safari/537.36'
    )
}


class _NoRedirectHTTPErrorProcessor(HTTPErrorProcessor):
    """
    This error handler does *not* automatically redirect requests, but instead
    returns the original response (including 3xx code)
    """

    def http_response(
        self, request: Request, response: HTTPResponse
    ):
        return response

    https_response = http_response


def _set_request_callback(
    request: Request,
    callback: Callable = print
) -> None:
    """
    Perform a callback on an HTTP request at the time it is submitted
    """
    callback(
        (
            'Request:\n\n'
            '    %s: %s\n\n'
            '    Headers:\n\n        ' % (
                request.get_method(),
                request.get_full_url()
            ) +
            '\n        '.join(
                '%s: %s' % (k, v)
                for k, v in request.header_items()
            )
        ) + (
            (
                '\n\n    Body:\n\n        ' +
                '\n        '.join(
                    str(request.data, encoding='utf-8').split('\n')
                )
            )
            if request.data is not None
            else ''
        ) + '\n'
    )


def _get_element_text(element: Element) -> str:
    """
    Get all text in an element and it's children
    """
    texts: List[str] = [element.text] if element.text else []
    for child in element:
        texts.append(_get_element_text(child))
    if element.tail:
        texts.append(element.tail)
    return ''.join(texts).strip()


def _get_html_element_tree(html: str) -> lxml.etree.ElementTree:
    """
    Get an `ElementTree` from an HTML string
    """
    with StringIO(html) as html_io:
        tree: ElementTree = lxml.etree.parse(
            html_io,
            lxml.html.html_parser
        )
    return tree


def _set_response_callback(
    response: HTTPResponse,
    callback: Callable = print
) -> None:
    """
    Perform a callback on an HTTP response at the time it is read
    """

    def response_read(amt: Optional[int] = None) -> bytes:
        data: bytes = HTTPResponse.read(response, amt)
        callback(
            (
                'Response:\n\n'
                '    URL: %s\n\n'
                '    Status: %s\n\n'
                '    Headers:\n\n        ' % (
                    response.geturl(),
                    response.getcode()
                )
            ) + (
                '\n        '.join(
                    '%s: %s' % (k, v)
                    for k, v in response.headers.items()
                )
            ) + (
                (
                    '\n\n    Body:\n\n        ' +
                    '\n        '.join(
                        str(
                            data,
                            encoding='utf-8',
                            errors='ignore'
                        ).split('\n')
                    )
                )
                if data else
                ''
            ) + '\n'
        )
        return data

    response.read = response_read


def _encode_form_data(data: Dict[str, str]) -> bytes:
    """
    Return
    """
    return bytes(urlencode(data), encoding='utf-8') if data else None


class EmptyResponseError(Exception):

    pass


class InvalidRoadTypeExtractError(Exception):

    pass


class DisabledFormElementError(Exception):

    pass


class _ZigZag:
    """
    This class represents a connection to https://zigzag.odot.state.or.us/
    """

    def __init__(
        self,
        hostname: str = HOSTNAME,
        echo: bool = False
    ) -> None:
        # Initialize private instance attributes
        self._tvc_url: str = ''
        self._base_url: str = ''
        self._portal_home_page: str = ''
        self._tvc_tree: lxml.etree.ElementTree = ''
        self._tvc_default_tree: lxml.etree.ElementTree = ''
        self._main_frame: str = ''
        self._top_frame: str = ''
        self._content_frame: str = ''
        # Initialize public instance attributes
        self.echo: bool = echo
        self.hostname: str = hostname
        # * Store our cookies
        self.cookie_jar: CookieJar = CookieJar()
        # * Build an opener that uses our cookie jar and doesn't follow
        #   redirects
        self.opener: OpenerDirector = build_opener(
            _NoRedirectHTTPErrorProcessor,
            HTTPCookieProcessor(self.cookie_jar),
        )

    def white_list(self, referrer: str) -> None:
        """
        White list a referring URL
        """
        self.request(
            self.domain_root_url + 'InternalSite/?WhlST',
            headers={
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-User': None,
                'Referer': referrer
            }
        ).read()

    def install_and_detect(self, location: str) -> str:
        url: str = self.domain_root_url + location
        self.request(url).read()
        return url

    @property
    def portal_home_page_url(self) -> str:
        return self.base_url + 'SecurezigzagPortalHomePage/'

    def get_portal_home_page(self, referrer: str) -> str:
        return str(
            self.request(
                self.portal_home_page_url,
                headers={
                    'Referer': referrer,
                    'Sec-Fetch-User': None
                }
            ).read(),
            encoding='utf-8'
        )

    @property
    def top_frame_url(self) -> str:
        return self.portal_home_page_url + 'TopFrame.aspx'

    def get_top_frame(self) -> str:
        return str(
            self.request(
                self.top_frame_url,
                headers={
                    'Referer': self.portal_home_page_url,
                    'Sec-Fetch-User': None,
                    'Sec-Fetch-Mode': 'nested-navigate'
                }
            ).read(),
            encoding='utf-8'
        )

    @property
    def content_frame(self) -> str:
        if not self._content_frame:
            self.get_content_frame()
        return self._content_frame

    @property
    def main_frame_url(self) -> str:
        return self.portal_home_page_url + 'MainFrame.aspx'

    def get_main_frame(self) -> str:
        self._main_frame = str(
            self.request(
                self.main_frame_url,
                headers={
                    'Referer': self.portal_home_page_url,
                    'Sec-Fetch-User': None,
                    'Sec-Fetch-Mode': 'nested-navigate'
                }
            ).read(),
            encoding='utf-8'
        )
        return self._main_frame

    @property
    def content_frame_url(self) -> str:
        return self.portal_home_page_url + 'ContentFrame.aspx'

    def get_content_frame(self) -> str:
        self._content_frame = str(
            self.request(
                self.content_frame_url,
                headers={
                    'Referer': self.main_frame_url,
                    'Sec-Fetch-User': None,
                    'Sec-Fetch-Mode': 'nested-navigate'
                }
            ).read(),
            encoding='utf-8'
        )
        return self._content_frame

    @property
    def tvc_url(self) -> str:
        if not self._tvc_url:
            self.get_top_frame()
            self.get_main_frame()
            self.white_list(self.main_frame_url)
            content_frame_tree: lxml.etree.ElementTree = (
                _get_html_element_tree(
                    self.content_frame
                )
            )
            # Find the link labeled "Crash Data System"
            anchor: lxml.etree.Element = next(iter(content_frame_tree.xpath(
                '//a[normalize-space(text())="Crash Data System"]'
            )))
            self._tvc_url = anchor.attrib['href']
        return self._tvc_url

    def get_tvc_default(self, **data: str) -> HTTPResponse:
        return self.request(
            self.tvc_url + 'default.aspx',
            headers={
                'Referer': self.tvc_url,
                'Sec-Fetch-Mode': 'nested-navigate'
            },
            data=data,
            method='POST'
        )

    def get_tvc_default_tree(
        self,
        **data: str
    ) -> str:
        response: HTTPResponse = self.get_tvc_default(**data)
        tvc_default: str = str(
            response.read(),
            encoding='utf-8'
        )
        if not tvc_default:
            raise EmptyResponseError(
                'Failed to retrieve TVC:\n' + str(response.info())
            )
        with StringIO(tvc_default) as tvc_default_io:
            # We set the retrieved tree as the TVC cache because it is now
            # the current state of the form
            self._tvc_tree = lxml.etree.parse(
                tvc_default_io,
                lxml.html.html_parser
            )
            return self._tvc_tree

    def get_tvc(self) -> HTTPResponse:
        return self.request(
            self.tvc_url,
            headers={
                'Referer': self.content_frame_url,
                'Sec-Fetch-Mode': 'cors'
            }
        )

    def get_tvc_tree(self) -> lxml.etree.ElementTree:
        with StringIO(
            str(
                self.get_tvc().read(),
                encoding='utf-8'
            )
        ) as tvc_io:
            self._tvc_tree = lxml.etree.parse(
                tvc_io,
                lxml.html.html_parser
            )
        return self._tvc_tree

    @property
    def tvc_tree(self) -> lxml.etree.ElementTree:
        if not self._tvc_tree:
            self.get_tvc().read()
            self.redirect_to_orig_url(self.tvc_url)
            self.get_tvc_tree()
        return self._tvc_tree

    def redirect_to_orig_url(self, referrer: str) -> str:
        url: str = (
            self.base_url +
            'InternalSite/RedirectToOrigURL.asp?site_name=zigzag&secure=1'
        )
        self.request(
            url,
            headers={
                'Referer': referrer,
                'Sec-Fetch-User': None
            }
        ).read()
        return url

    def validate(self, referrer: str) -> str:
        url: str = self.base_url + 'InternalSite/Validate.asp'
        self.request(
            url,
            headers={
                'Referer': referrer
            }
        ).read()
        return url

    def init_params(self, location: str) -> str:
        """
        Initialize cookies needed to access site resources
        """
        # Init Params
        url: str = self.domain_root_url + location
        response: HTTPResponse = self.request(url)
        response.read()
        # Install and Detect
        install_and_detect_url: str = self.install_and_detect(
            response.headers['Location']
        )
        # White list our signed base-URL
        self.white_list(
            install_and_detect_url
        )
        # End of first page visit
        self.get_portal_home_page(
            referrer=install_and_detect_url
        )
        validate_url: str = self.validate(
            referrer=install_and_detect_url
        )
        self.redirect_to_orig_url(
            referrer=validate_url
        )
        self.get_portal_home_page(
            referrer=validate_url
        )
        self.redirect_to_orig_url(
            referrer=self.portal_home_page_url
        )
        self.get_portal_home_page(
            referrer=self.portal_home_page_url
        )
        return url

    @property
    def domain_root_url(self):
        return 'https://%s/' % self.hostname

    @property
    def base_url(self) -> None:
        """
        Retrieve and cache a base URL for this session using CDS
        """
        if not self._base_url:
            request = Request(self.domain_root_url)
            response: HTTPResponse = self.opener.open(request)
            # The response should be a redirect
            assert response.getcode() == 302
            # Get the base URL from the cookies
            for cookie in self.cookie_jar:  # type: Cookie
                if cookie.path != '/':
                    self._base_url = self.domain_root_url + cookie.path
                    break
            # Parse the location ODOT is attempting to redirect us to
            self.init_params(
                response.headers['Location']
            )
            response.read()
        return self._base_url

    def request(
        self,
        path: str = '',
        data: Optional[
            Union[
                str, Dict,
                sob.model.Model
            ]
        ] = None,
        method: str = 'GET',
        headers: Dict[str, Optional[str]] = {},
        timeout: Optional[int] = None
    ) -> HTTPResponse:
        """
        Parameters:

        - path (str):

          The (absolute or relative) path of the endpoint to which this request
          is being made

        - data (str|dict|sob.model.Object|[sob.model.Object]|None):

          The data to be included in the body of this request

        - headers (dict|None):

          A dictionary of headers

        - timeout (int|None):

          A custom timeout for this request
        """
        assert method in ('GET', 'POST', 'PUT')
        for key, value in _DEFAULT_HEADERS.items():
            if key in headers:
                if headers[key] is None:
                    del headers[key]
            else:
                headers[key] = value
        if '://' in path:
            url: str = path
        else:
            url: str = self.base_url + path
        form_data: Optional[bytes] = None
        if data:
            if method == 'GET':
                url += '?' + urlencode(data)
            else:
                form_data = _encode_form_data(data)
        request: Request = Request(
            url,
            headers=headers,
            data=form_data,
            method=method,
            **(
                {}
                if timeout is None else
                {'timeout': timeout}
            )
        )
        if self.echo:
            _set_request_callback(request, print)
        response: HTTPResponse = self.opener.open(request)
        if self.echo:
            _set_response_callback(response, print)
        return response


class FormField:
    """
    Instances of this class hold information about a form field
    """

    def __init__(
        self,
        tag: str = '',
        type_: str = '',
        name: str = '',
        options: Optional[Dict[str, str]] = None,
        value: str = '',
        disabled: bool = False,
        **kwargs
    ):
        self._value: str = ''
        self.tag: str = tag
        self.type: str = type_
        self.name: str = name
        self.options: Dict[str, str] = options or {}
        if 'type' in kwargs:
            self.type = kwargs['type']
        self.value = value
        self.x: int = 0
        self.y: int = 0
        self.disabled: bool = disabled

    def reset(self) -> None:
        """
        Un-click
        """
        self.x = 0
        self.y = 0
        self.value = ''
        self.disabled = False

    def click(self) -> None:
        """
        The button is 155 x 32 pixels. We assume the average click would be in
        the center of the button, and use gaussian distribution to randomize.
        """
        if self.disabled:
            raise DisabledFormElementError(
                'Apologies, this report is not available for the parameters '
                'you have provided'
            )
        self.x = int(random.gauss(77, 77))
        self.y = int(random.gauss(16, 33))

    @property
    def value(self):
        """
        Return the current value for this form field
        """
        return self._value

    @value.setter
    def value(
        self,
        value: Union[str, date]
    ) -> None:
        """
        Set the current value for this form field
        """
        assert isinstance(value, (str, date))
        if isinstance(value, date):
            value = value.strftime('%m/%d/%y')
        if value and self.options:
            if value in self.options:
                # Get the value corresponding the the provided label
                value = self.options[
                    value
                ]
            else:
                # Ensure the provided value group is a valid option
                # print(self.options)
                if (
                    value not in
                    self.options.values()
                ):
                    raise ValueError(
                        '%s is not a valid value. Valid values include:\n' %
                        repr(value) +
                        '\n'.join(
                            '- %s: %s' % (key, repr(value))
                            for key, value in self.options.items()
                        )
                    )
        self._value = value

    def __repr__(self) -> str:
        return (
            'FormField('
            'tag={tag}, '
            'type={type}, '
            'name={name}, '
            'options={options} ,'
            'value={value},'
            'disabled={disabled}'
            ')'.format(
                tag=repr(self.tag),
                type=repr(self.type),
                name=repr(self.name),
                options=repr(self.options),
                value=repr(self.value),
                disabled=repr(self.disabled)
            )
        )

    def __str__(self) -> str:
        return repr(self)


@dataclass
class FormFields:

    toolkit_script_manager: FormField = FormField(
        tag='input',
        type='hidden',
        name='ctl00_MainBodyContent_ToolkitScriptManager1_HiddenField'
    )
    event_target: FormField = FormField(
        tag='input',
        type='hidden',
        name='__EVENTTARGET'
    )
    event_argument: FormField = FormField(
        tag='input',
        type='hidden',
        name='__EVENTARGUMENT'
    )
    client_state: FormField = FormField(
        tag='input',
        type='hidden',
        name='ctl00_MainBodyContent_MainTabs_ClientState'
    )
    last_focus: FormField = FormField(
        tag='input',
        type='hidden',
        name='__LASTFOCUS'
    )
    view_state: FormField = FormField(
        tag='input',
        type='hidden',
        name='__VIEWSTATE'
    )
    view_state_generator: FormField = FormField(
        tag='input',
        type='hidden',
        name='__VIEWSTATEGENERATOR'
    )
    event_validation: FormField = FormField(
        tag='input',
        type='hidden',
        name='__EVENTVALIDATION'
    )

    # "Highways" tab
    highways_number: FormField = FormField(
        tag='select',
        name='ctl00$MainBodyContent$MainTabs$TabHighways$ddlHwyNo'
    )
    highways_begin_mile_point: FormField = FormField(
        tag='input',
        type='text',
        name='ctl00$MainBodyContent$MainTabs$TabHighways$txtHwyBegMilePoint',
        #value='-999.99'
    )
    highways_end_mile_point: FormField = FormField(
        tag='input',
        type='text',
        name='ctl00$MainBodyContent$MainTabs$TabHighways$txtHwyEndMilePoint',
        #value='999.99'
    )
    highways_all_highways: FormField = FormField(
        tag='input',
        type='checkbox',
        name='ctl00$MainBodyContent$MainTabs$TabHighways$chkHwyAll'
    )
    highways_frontage_roads: FormField = FormField(
        tag='input',
        type='checkbox',
        name='ctl00$MainBodyContent$MainTabs$TabHighways$chkHwyFrontageroads'
    )
    highways_mainline: FormField = FormField(
        tag='input',
        type='checkbox',
        name='ctl00$MainBodyContent$MainTabs$TabHighways$chkHwyMainline'
    )
    highways_connections: FormField = FormField(
        tag='input',
        type='checkbox',
        name='ctl00$MainBodyContent$MainTabs$TabHighways$chkHwyConnections'
    )
    highways_spur: FormField = FormField(
        tag='input',
        type='checkbox',
        name='ctl00$MainBodyContent$MainTabs$TabHighways$chkHwySpur'
    )
    highways_z_mile_points: FormField = FormField(
        tag='input',
        type='checkbox',
        name='ctl00$MainBodyContent$MainTabs$TabHighways$chkHwyZmp'
    )
    highways_add_mileage: FormField = FormField(
        tag='input',
        type='radio',
        name='ctl00$MainBodyContent$MainTabs$TabHighways$rdoHwyAddMlge'
    )
    highways_begin_date: FormField = FormField(
        tag='input',
        type='text',
        name='ctl00$MainBodyContent$MainTabs$TabHighways$txtHwyBegDate'
    )
    highways_end_date: FormField = FormField(
        tag='input',
        type='text',
        name='ctl00$MainBodyContent$MainTabs$TabHighways$txtHwyEndDate'
    )
    highways_format: FormField = FormField(
        tag='input',
        type='radio',
        name='ctl00$MainBodyContent$MainTabs$TabHighways$HwyFormatGroup'
    )
    highways_record_number: FormField = FormField(
        tag='input',
        type='text',
        name='ctl00$MainBodyContent$MainTabs$TabHighways$txtHwyRecordNumber'
    )
    highways_display_instructions: FormField = FormField(
        tag='input',
        type='checkbox',
        name=(
            'ctl00$MainBodyContent$MainTabs$TabHighways$'
            'chkHwyDisplayInstructions'
        )
    )
    # Highway Commands
    highways_command_cds150: FormField = FormField(
        tag='input',
        type='image',
        name='ctl00$MainBodyContent$MainTabs$TabHighways$cmdHwyCDS150'
    )
    highways_command_cds390: FormField = FormField(
        tag='input',
        type='image',
        name='ctl00$MainBodyContent$MainTabs$TabHighways$cmdHwyCDS390'
    )
    highways_command_direction: FormField = FormField(
        tag='input',
        type='image',
        name='ctl00$MainBodyContent$MainTabs$TabHighways$cmdHwyDirection'
    )
    highways_command_cds380: FormField = FormField(
        tag='input',
        type='image',
        name='ctl00$MainBodyContent$MainTabs$TabHighways$cmdHwyCDS380'
    )
    highways_command_rrr: FormField = FormField(
        tag='input',
        type='image',
        name='ctl00$MainBodyContent$MainTabs$TabHighways$cmdHwyRRR'
    )
    highways_command_cds510: FormField = FormField(
        tag='input',
        type='image',
        name='ctl00$MainBodyContent$MainTabs$TabHighways$cmdHwyCDS510'
    )
    highways_command_cds501: FormField = FormField(
        tag='input',
        type='image',
        name='ctl00$MainBodyContent$MainTabs$TabHighways$cmdHwyCDS501'
    )

    # "Local Roads" tab
    local_roads_county: FormField = FormField(
        tag='select',
        name='ctl00$MainBodyContent$MainTabs$TabLocalRoads$ddlLclCounty'
    )
    local_roads_city: FormField = FormField(
        tag='select',
        name='ctl00$MainBodyContent$MainTabs$TabLocalRoads$ddlLclCity'
    )
    local_roads_query_type: FormField = FormField(
        tag='input',
        type='radio',
        name='ctl00$MainBodyContent$MainTabs$TabLocalRoads$LclQueryType'
    )
    local_roads_street: FormField = FormField(
        tag='select',
        name='ctl00$MainBodyContent$MainTabs$TabLocalRoads$ddlLclStreet'
    )
    local_roads_cross_street: FormField = FormField(
        tag='select',
        name='ctl00$MainBodyContent$MainTabs$TabLocalRoads$ddlLclCrossStreet'
    )
    local_roads_begin_mile_point: FormField = FormField(
        tag='input',
        type='text',
        name='ctl00$MainBodyContent$MainTabs$TabLocalRoads$txtLclBegMilePoint'
    )
    local_roads_end_mile_point: FormField = FormField(
        tag='input',
        type='text',
        name='ctl00$MainBodyContent$MainTabs$TabLocalRoads$txtLclEndMilePoint'
    )
    local_roads_begin_date: FormField = FormField(
        tag='input',
        type='text',
        name='ctl00$MainBodyContent$MainTabs$TabLocalRoads$txtLclBegDate'
    )
    local_roads_end_date: FormField = FormField(
        tag='input',
        type='text',
        name='ctl00$MainBodyContent$MainTabs$TabLocalRoads$txtLclEndDate'
    )
    local_roads_format: FormField = FormField(
        tag='input',
        type='radio',
        name='ctl00$MainBodyContent$MainTabs$TabLocalRoads$LclFormatGroup'
    )
    local_roads_record_number: FormField = FormField(
        tag='input',
        type='text',
        name='ctl00$MainBodyContent$MainTabs$TabLocalRoads$txtLclRecordNumber'
    )
    local_roads_display_instructions: FormField = FormField(
        tag='input',
        type='checkbox',
        name=(
            'ctl00$MainBodyContent$MainTabs$TabLocalRoads$'
            'chkLclDisplayInstructions'
        )
    )
    # Local-Roads Commands
    local_roads_command_cds150: FormField = FormField(
        tag='input',
        type='image',
        name='ctl00$MainBodyContent$MainTabs$TabLocalRoads$cmdLclCDS150'
    )
    local_roads_command_cds160: FormField = FormField(
        tag='input',
        type='image',
        name='ctl00$MainBodyContent$MainTabs$TabLocalRoads$cmdLclCDS160'
    )
    local_roads_command_cds390: FormField = FormField(
        tag='input',
        type='image',
        name='ctl00$MainBodyContent$MainTabs$TabLocalRoads$cmdLclCDS390'
    )
    local_roads_command_cds380: FormField = FormField(
        tag='input',
        type='image',
        name='ctl00$MainBodyContent$MainTabs$TabLocalRoads$cmdLclCDS380'
    )
    local_roads_command_cds190b: FormField = FormField(
        tag='input',
        type='image',
        name='ctl00$MainBodyContent$MainTabs$TabLocalRoads$cmdLclCDS190b'
    )
    local_roads_command_cds510: FormField = FormField(
        tag='input',
        type='image',
        name='ctl00$MainBodyContent$MainTabs$TabLocalRoads$cmdLclCDS510'
    )
    local_roads_command_cds501: FormField = FormField(
        tag='input',
        type='image',
        name='ctl00$MainBodyContent$MainTabs$TabLocalRoads$cmdLclCDS501'
    )

    # "All Jurisdictions" tab
    all_roads_jurisdiction: FormField = FormField(
        tag='input',
        type='radio',
        name='ctl00$MainBodyContent$MainTabs$TabAllRoads$SumJurisdictionGroup'
    )
    all_roads_county: FormField = FormField(
        tag='select',
        name='ctl00$MainBodyContent$MainTabs$TabAllRoads$ddlSumCounty'
    )
    all_roads_city: FormField = FormField(
        tag='select',
        name='ctl00$MainBodyContent$MainTabs$TabAllRoads$ddlSumCity'
    )
    all_roads_query_type: FormField = FormField(
        tag='input',
        type='radio',
        name='ctl00$MainBodyContent$MainTabs$TabAllRoads$SumQueryType'
    )
    all_roads_begin_date: FormField = FormField(
        tag='input',
        type='text',
        name='ctl00$MainBodyContent$MainTabs$TabAllRoads$txtSumBegDate'
    )
    all_roads_end_date: FormField = FormField(
        tag='input',
        type='text',
        name='ctl00$MainBodyContent$MainTabs$TabAllRoads$txtSumEndDate'
    )
    all_roads_format: FormField = FormField(
        tag='input',
        type='radio',
        name='ctl00$MainBodyContent$MainTabs$TabAllRoads$SumFormatGroup'
    )
    # All-Roads Commands
    all_roads_command_cds160: FormField = FormField(
        tag='input',
        type='image',
        name='ctl00$MainBodyContent$MainTabs$TabAllRoads$cmdSumCDS160'
    )
    all_roads_command_cds200: FormField = FormField(
        tag='input',
        type='image',
        name='ctl00$MainBodyContent$MainTabs$TabAllRoads$cmdSumCDS200'
    )
    all_roads_command_cds250: FormField = FormField(
        tag='input',
        type='image',
        name='ctl00$MainBodyContent$MainTabs$TabAllRoads$cmdSumCDS250'
    )
    all_roads_command_cds150: FormField = FormField(
        tag='input',
        type='image',
        name='ctl00$MainBodyContent$MainTabs$TabAllRoads$cmdSumCDS150'
    )
    all_roads_command_cds280: FormField = FormField(
        tag='input',
        type='image',
        name='ctl00$MainBodyContent$MainTabs$TabAllRoads$cmdSumCDS280'
    )
    all_roads_command_cds510: FormField = FormField(
        tag='input',
        type='image',
        name='ctl00$MainBodyContent$MainTabs$TabAllRoads$cmdSumCDS510'
    )
    all_roads_command_cds501: FormField = FormField(
        tag='input',
        type='image',
        name='ctl00$MainBodyContent$MainTabs$TabAllRoads$cmdSumCDS501'
    )

    @property
    def data(self) -> Dict[str, str]:
        """
        A dictionary of field names and their values
        """
        data: Dict[str, str] = {}
        for field_ in fields(self):
            form_field: FormField = getattr(self, field_.name)
            if form_field.type == 'image' and form_field.x and form_field.y:
                # If the input is an image, and has been clicked...
                data[form_field.name + '.x'] = str(form_field.x)
                data[form_field.name + '.y'] = str(form_field.y)
            elif (
                # Only include empty strings if the field is a view controller
                form_field.value or
                form_field.name[0] == '_'
            ):
                data[form_field.name] = form_field.value
        return data

    def reset(self, commands_only: bool = False) -> None:
        """
        Reset all form field values
        """
        for field_ in fields(self):
            form_field: FormField = getattr(self, field_.name)
            if form_field.name[0] != '_' and (
                (not commands_only) or
                'command' in form_field.name
            ):
                form_field.reset()


def _inspect_select_field(
    select_element: Element,
    form_field: FormField
) -> None:
    """
    Given an XML `select` element, populate the form field's options
    and current value
    """
    for option_element in select_element:  # type: Element
        value: str = option_element.attrib['value']
        form_field.options[
            option_element.text
        ] = value
        if (
            'selected' in option_element.attrib and
            option_element.attrib['selected'] == 'selected'
        ):
            form_field.value = value


class Extract(enum.Enum):

    CDS501 = enum.auto()
    CDS150 = enum.auto()
    CDS160 = enum.auto()
    CDS190b = enum.auto()
    CDS200 = enum.auto()
    CDS250 = enum.auto()
    CDS280 = enum.auto()
    CDS380 = enum.auto()
    CDS390 = enum.auto()
    CDS510 = enum.auto()
    DIRECTION = enum.auto()
    RRR = enum.auto()

    def __repr__(self):
        return "%s.%s" % (
            self.__class__.__name__, self._name_
        )


class RoadType(enum.Enum):

    ALL = enum.auto()
    HIGHWAY = enum.auto()
    LOCAL = enum.auto()

    def __repr__(self):
        return "%s.%s" % (
            self.__class__.__name__, self._name_
        )


class HighwayType(enum.Enum):

    ALL = enum.auto()
    FRONTAGE_ROAD = enum.auto()
    MAINLINE = enum.auto()
    CONNECTION = enum.auto()

    def __repr__(self):
        return "%s.%s" % (
            self.__class__.__name__, self._name_
        )


class Client:
    """
    This class acts as a client for querying the Oregon Department of
    Transportation (ODOT) Crash Data System (CDS)
    """

    def __init__(
        self,
        hostname: str = HOSTNAME,
        echo: bool = False
    ) -> None:
        self._zig_zag: _ZigZag = _ZigZag(
            hostname=hostname,
            echo=echo
        )
        self._form_fields: Optional[FormFields] = None
        self._highways: Optional[Dict[str, str]] = None
        self._counties_cities_streets: Optional[Dict[str, str]] = None
        self._counties: Optional[Dict[str, str]] = None
        self._cities: Optional[Dict[str, str]] = None

    @property
    def highways(self) -> Dict[str, str]:
        """
        A code -> value mapping for all state highways in Oregon.
        """
        if not self._highways:
            self.reset_form_fields()
            highways = {}
            for key, value in self.form_fields.highways_number.options.items():
                highways[value] = key
            self._highways = highways
            self.form_fields.reset()
        return self._highways

    @property
    def counties(self) -> Dict[str, str]:
        """
        A code -> value mapping for all counties in Oregon.
        """
        if not self._counties:
            self.reset_form_fields()
            counties = {}
            for key, value in (
                self.form_fields.local_roads_county.options.items()
            ):
                counties[value] = key
            self._counties = counties
        return self._counties

    @property
    def cities(self) -> Dict[str, str]:
        """
        A code -> value mapping for all cities in Oregon.
        """
        if not self._cities:
            self.reset_form_fields()
            self.update_form_field(
                'all_roads_jurisdiction',
                'City'
            )
            cities = {}
            for key, value in (
                self.form_fields.all_roads_city.options.items()
            ):
                cities[value] = key
            self._cities = cities
        return self._cities

    def get_streets(self, county: str, city: str) -> Dict[str, str]:
        """
        Get a code -> name mapping for a county/city's streets.

        Parameters:

        - county (str): The county name or code

        - city (str): The city name or code, or "Outside City Limits".
        """
        self.reset_form_fields()
        self.update_form_field(
            'local_roads_county',
            county
        )
        streets: Dict[str, str] = {}
        for section, section_id in (
            self.form_fields.local_roads_city.options.items()
        ):  # type: Tuple[str, str]
            if (
                section.startswith(city) or
                section_id == city
            ):
                self.update_form_field(
                    'local_roads_city',
                    section
                )
                for key, value in (
                    self.form_fields.local_roads_street.options.items()
                ):
                    streets[value] = key
        return streets

    def _get_radio_label(self, id_: str) -> str:
        """
        Get the label for a form input with the given ID
        """
        return _get_element_text(next(iter(
            self._zig_zag.tvc_tree.xpath(
                '//label[@for="%s"]' % id_
            )
        )))

    def _inspect_form_field(
        self,
        form_field: FormField
    ) -> None:
        """
        Inspect a form field to determine the list of valid option values and
        current value
        """
        # Assemble an XPath...
        xpath: str = '//{tag}[@name="{name}"]'.format(
            tag=form_field.tag,
            name=form_field.name
        )
        form_field.options: Dict[str, str] = {}
        form_field.disabled = False
        # Find this field in the TVC form
        for element in (
            self._zig_zag.tvc_tree.xpath(xpath)
        ):  # type: lxml.etree.Element
            # Is the field disabled?
            if 'disabled' in element.attrib and element.attrib[
                'disabled'
            ] == 'disabled':
                form_field.disabled = True
            # Get the valid value options
            if form_field.tag == 'select':
                _inspect_select_field(
                    element,
                    form_field
                )
            elif form_field.tag == 'input' and form_field.type == 'radio':
                label: str = self._get_radio_label(
                    element.attrib['id']
                )
                value: str = element.attrib['value']
                form_field.options[label] = value
                # If this radio button is selected, infer @value for this field
                if (
                    'checked' in element.attrib and
                    element.attrib['checked'] == 'checked'
                ):
                    form_field.value = value
            elif form_field.type == 'checkbox':
                form_field.value = (
                    'on' if (
                        'checked' in element.attrib and
                        element.attrib['checked'] == 'checked'
                    ) else ''
                )
            elif 'value' in element.attrib:
                form_field.value = element.attrib['value']

    @property
    def form_fields(self) -> FormFields:
        """
        An instance of `FormFields` providing details about each field,
        including options
        """
        if not self._form_fields:
            form_fields: FormFields = FormFields()
            self._form_fields = form_fields
            self._inspect_form_fields()
        return self._form_fields

    def _inspect_form_fields(self) -> None:
        """
        Update option values based on current form field selections
        """
        form_fields: FormFields = self.form_fields
        for field_ in fields(self.form_fields):
            form_field: FormField = getattr(
                form_fields,
                field_.name
            )
            # Lookup options for this field, set the value, etc.
            self._inspect_form_field(form_field)

    def update_form_field(
        self,
        attribute_name: str,
        value: Union[str, date, float, int]
    ) -> None:
        """
        Update option values based on current form field selections
        """
        form_field: FormField = getattr(self.form_fields, attribute_name)
        # Convert the value to a string
        if isinstance(value, date):
            value = value.strftime('%m/%d/%y')
        elif value and (not isinstance(value, str)):
            value = str(value)
        # Make sure we are comparing codes, not labels
        if form_field.options and (value in form_field.options):
            value = form_field.options[value]
        # Update the form field, if different from the current value
        if form_field.value != value:
            form_field.value = value
            self._zig_zag.get_tvc_default_tree(**self.form_fields.data)
            self._inspect_form_fields()

    def _validate_input(
        self,
        field_name: str,
        value: str
    ) -> str:
        form_field: FormField = getattr(
            self.form_fields,
            field_name
        )
        if value in form_field.options:
            # Get the value corresponding the the provided label
            value = form_field.options[
                value
            ]
        else:
            # Ensure the provided value group is a valid option
            assert (
                value in
                form_field.options.values()
            )
        return value

    def submit(self) -> HTTPResponse:
        """
        This method submits the form in its current state
        """
        response: HTTPResponse = self._zig_zag.get_tvc_default(
            **self.form_fields.data
        )
        if response.getcode() == 302:
            response.read()
            # The response was a redirect
            response = self._zig_zag.request(
                self._zig_zag.tvc_url + response.headers['Location'],
                headers={
                    'Sec-Fetch-Mode': 'nested-navigate',
                    'Referer': self._zig_zag.tvc_url
                }
            )
        return response

    def _set_all_roads_fields(
        self,
        extract: Extract = Extract.CDS501,
        jurisdiction: str = '',
        county: str = '',
        city: str = '',
        query_type: str = 'rdoSumQueryTypeALL',
        begin_date: date = DEFAULT_BEGIN_DATE,
        end_date: date = DEFAULT_END_DATE
    ) -> None:
        """
        Set fields relevant to the "All Roads" tab
        """
        # Set form fields from parameters
        self.update_form_field('all_roads_jurisdiction', jurisdiction)
        self.update_form_field('all_roads_county', county)
        self.update_form_field('all_roads_city', city)
        self.update_form_field('all_roads_query_type', query_type)
        self.update_form_field('all_roads_begin_date', begin_date)
        self.update_form_field('all_roads_end_date', end_date)
        self.update_form_field('all_roads_format', 'rdoSumReportFormatXLS')
        # "Click" on the extract
        if extract == Extract.CDS150:
            self.form_fields.all_roads_command_cds150.click()
        elif extract == Extract.CDS160:
            self.form_fields.all_roads_command_cds160.click()
        elif extract == Extract.CDS200:
            self.form_fields.all_roads_command_cds200.click()
        elif extract == Extract.CDS250:
            self.form_fields.all_roads_command_cds250.click()
        elif extract == Extract.CDS280:
            self.form_fields.all_roads_command_cds280.click()
        elif extract == Extract.CDS501:
            self.form_fields.all_roads_command_cds501.click()
        elif extract == Extract.CDS510:
            self.form_fields.all_roads_command_cds510.click()
        else:
            raise InvalidRoadTypeExtractError(
                '%s is not a valid extract for "All Roads"' % repr(extract)
            )

    def _set_local_roads_fields(
        self,
        extract: Extract = Extract.CDS501,
        county: str = '',
        city: str = '',
        street: str = '',
        cross_street: str = '',
        query_type: str = 'rdoSumQueryTypeALL',
        begin_mile_point: float = 0.0,
        end_mile_point: float = 0.0,
        begin_date: date = DEFAULT_BEGIN_DATE,
        end_date: date = DEFAULT_END_DATE,
        record_number: int = 0,
        display_instructions: bool = False
    ) -> None:
        # Set form fields from parameters
        self.update_form_field('local_roads_county', county)
        self.update_form_field('local_roads_city', city)
        self.update_form_field('local_roads_query_type', query_type)
        self.update_form_field('local_roads_street', street)
        self.update_form_field('local_roads_cross_street', cross_street)
        self.update_form_field(
            'local_roads_begin_mile_point',
            str(begin_mile_point or '')
        )
        self.update_form_field(
            'local_roads_end_mile_point',
            str(end_mile_point or '')
        )
        self.update_form_field('local_roads_begin_date', begin_date)
        self.update_form_field('local_roads_end_date', end_date)
        self.update_form_field('local_roads_format', 'rdoLclReportFormatXLS')
        self.update_form_field(
            'local_roads_record_number',
            str(record_number or '')
        )
        self.update_form_field(
            'local_roads_display_instructions',
            'on' if display_instructions else ''
        )
        # "Click" on the extract
        if extract == Extract.CDS150:
            self.form_fields.local_roads_command_cds150.click()
        elif extract == Extract.CDS160:
            self.form_fields.local_roads_command_cds160.click()
        elif extract == Extract.CDS380:
            self.form_fields.local_roads_command_cds380.click()
        elif extract == Extract.CDS390:
            self.form_fields.local_roads_command_cds390.click()
        elif extract == Extract.CDS190b:
            self.form_fields.local_roads_command_cds190b.click()
        elif extract == Extract.CDS501:
            self.form_fields.local_roads_command_cds501.click()
        elif extract == Extract.CDS510:
            self.form_fields.local_roads_command_cds510.click()
        else:
            raise InvalidRoadTypeExtractError(
                '%s is not a valid extract for "Local Roads"' % repr(extract)
            )

    def _set_highway_type(
        self,
        highway_type: HighwayType = HighwayType.ALL
    ) -> None:
        if highway_type == HighwayType.ALL:
            self.update_form_field(
                'highways_all_highways',
                'on'
            )
        elif highway_type == HighwayType.CONNECTION:
            self.update_form_field(
                'highways_connections',
                'on'
            )
        elif highway_type == HighwayType.FRONTAGE_ROAD:
            self.update_form_field(
                'highways_frontage_roads',
                'on'
            )
        elif highway_type == HighwayType.MAINLINE:
            self.update_form_field(
                'highways_mainline',
                'on'
            )
        elif highway_type == HighwayType.SPUR:
            self.update_form_field(
                'highways_spur',
                'on'
            )

    def _set_highways_fields(
        self,
        extract: Extract = Extract.CDS501,
        begin_date: date = DEFAULT_BEGIN_DATE,
        end_date: date = DEFAULT_END_DATE,
        highway: str = '',
        begin_mile_point: float = 0.0,
        end_mile_point: float = 0.0,
        highway_type: HighwayType = HighwayType.ALL,
        z_mile_points: bool = True,
        add_mileage: bool = True,
        non_add_mileage: bool = True,
        record_number: int = 0,
        display_instructions: bool = False
    ) -> None:
        # Set form fields from parameters
        self.update_form_field(
            'highways_number',
            highway
        )
        self.update_form_field(
            'highways_begin_mile_point',
            str(
                begin_mile_point or
                # The form field value for the highway is a comma-separated
                # list where the last two are the beginning and end mile
                # points
                self.form_fields.highways_number.value.split(',')[-2]
            )
        )
        self.update_form_field(
            'highways_end_mile_point',
            str(
                end_mile_point or
                # The form field value for the highway is a comma-separated
                # list where the last two are the beginning and end mile
                # points
                self.form_fields.highways_number.value.split(',')[-1]
            )
        )
        self._set_highway_type(highway_type)
        self.update_form_field(
            'highways_z_mile_points',
            'on' if z_mile_points else ''
        )
        self.update_form_field(
            'highways_add_mileage',
            (
                'B'
                if non_add_mileage else
                'Y'
            ) if add_mileage else (
                'N'
                if non_add_mileage else
                ''
            )
        )
        self.update_form_field('highways_begin_date', begin_date)
        self.update_form_field('highways_end_date', end_date)
        self.update_form_field('highways_format', 'rdoHwyReportFormatXLS')
        self.update_form_field(
            'highways_record_number',
            str(record_number or '')
        )
        self.update_form_field(
            'highways_display_instructions',
            'on' if display_instructions else ''
        )
        # "Click" on the extract
        if extract == Extract.CDS150:
            self.form_fields.highways_command_cds150.click()
        elif extract == Extract.DIRECTION:
            self.form_fields.highways_command_direction.click()
        elif extract == Extract.CDS380:
            self.form_fields.highways_command_cds380.click()
        elif extract == Extract.CDS390:
            self.form_fields.highways_command_cds390.click()
        elif extract == Extract.RRR:
            self.form_fields.highways_command_rrr.click()
        elif extract == Extract.CDS501:
            self.form_fields.highways_command_cds501.click()
        elif extract == Extract.CDS510:
            self.form_fields.highways_command_cds510.click()
        else:
            raise InvalidRoadTypeExtractError(
                '%s is not a valid extract for "Highways"' % repr(extract)
            )

    def reset_form_fields(self) -> None:
        """
        This method resets all form fields to their default, and refreshes the
        view state
        """
        self.form_fields.reset()
        self._zig_zag.get_tvc_tree()
        self._inspect_form_fields()

    def extract(
        self,
        road_type: RoadType = RoadType.ALL,
        extract: Extract = Extract.CDS501,
        jurisdiction: str = '',
        county: str = '',
        city: str = '',
        street: str = '',
        cross_street: str = '',
        query_type: str = '',
        begin_date: date = DEFAULT_BEGIN_DATE,
        end_date: date = DEFAULT_END_DATE,
        highway: str = '',
        begin_mile_point: float = 0.0,
        end_mile_point: float = 0.0,
        highway_type: HighwayType = HighwayType.ALL,
        z_mile_points: bool = True,
        add_mileage: bool = True,
        non_add_mileage: bool = True,
        record_number: int = 0,
        display_instructions: bool = False
    ) -> HTTPResponse:
        """
        This method returns an an ODOT-CDS extract or report as an instance
        of `http.client.HTTPResponse`.

        Parameters:

        - road_type (RoadType):

          This indicates the type of roads to retrieve crash data for.

          - RoadType.ALL: Both highways and local roads (default)

          - RoadType.HIGHWAY: State highways

          - RoadType.LOCAL: Local roads

        - extract (Extract):

          This indicates which extract/report to retrieve.

          - Extract.CDS501: CSV

          - Extract.CDS510: MDB

          - Extract.CDS150

          - Extract.CDS160

          - Extract.CDS190b

          - Extract.CDS200

          - Extract.CDS250

          - Extract.CDS280

          - Extract.CDS380

          - Extract.CDS390

          - Extract.CDS501

          - Extract.CDS510

          - Extract.DIRECTION

          - Extract.RRR

        - jurisdiction (str):

          This applies only if `road_type == RoadType.ALL`.

          - "rdoSumJurisdictionCNTY" ("County"):
            Return all crashes for a specified county.

          - "rdoSumJurisdictionCITY" ("City"):
            Return all crashes for a specified city.

        - county (str):

          The name or ID of a county. For a complete dictionary of county IDs
          and names, get `odot_cds.client.Client().counties`.

        - city (str):

          The name or ID of a city. For a complete dictionary of city IDs
          and names, get `odot_cds.client.Client().cities`.

        - street (str):

          Only applicable if `road_type == RoadType.LOCAL`.

          The name or ID of a street. For a complete dictionary of street IDs
          and names for a county and city, call `odot_cds.client.Client(
          ).get_streets()`. For example, to get streets for Portland:

          >>> odot_cds.client.Client().get_streets(
          ...     county='Multnomah',
          ...     city='Portland'
          ... )

        - cross_street (str):

            See `street`

        - query_type (str):

          The type of roads for which to retrieve crash data.

          If `road_type == RoadType.ALL`, options for this will include:

          - "rdoSumQueryTypeALL": All Roads (default)
          - "rdoSumQueryTypeCNTY": County Roads
          - "rdoSumQueryTypeCITY": City Streets
          - "rdoSumQueryTypeSTATE": State Highways

          If `road_type == RoadType.LOCAL`, options for this will include:

          - "rdoLclQueryTypeSI": Street Segment & Intersectional (this is the
            default, unless `city` is "000" or "Outside City Limits")
          - "rdoLclQueryTypeSP": Specified Streets Not Limited to Intersection
          - "rdoLclQueryTypeIN": Intersectional
          - "rdoLclQueryTypeMP": Mile-Pointed County Road (this is the *only*
            option if `city` is "000" (Outside City Limits)

        - highway (str):

          The number + name of a highway. For a dictionary of valid values,
          get `odot_cds.client.Client().highways`.

        - z_mile_points (bool)

        - add_mileage (bool):

          Include traffic traveling in a direction wherein progress corresponds
          to a numeric increase for mileage markers.

        - non_add_mileage (bool):

          Include traffic traveling in a direction wherein progress corresponds
          to a numeric decrease for mileage markers.

        - record_number (int):

          The report will start at this record #, and will include the first
          5000 records following this record. This parameter is only applicable
          if `road_type == RoadType.LOCAL` or `road_type == RoadType.HIGHWAY`.

        - display_instructions (bool):

          Causes instructions to be included in the report. This parameter is
          only applicable if `road_type == RoadType.LOCAL` or
          `road_type == RoadType.HIGHWAY`.

        Additional information about terms used above can be found
        in ODOT's [CDS code manual](
        https://www.oregon.gov/ODOT/Data/documents/CDS_Code_Manual.pdf).
        """
        self.reset_form_fields()
        assert isinstance(extract, Extract)
        # Set a default query type if none is provided
        if not query_type:
            if road_type == RoadType.ALL:
                query_type = 'All Roads'
            elif road_type == RoadType.LOCAL:
                if city in ('000', 'Outside City Limits'):
                    query_type = 'Street Segment & Intersectional'
                else:
                    query_type = 'Mile-Pointed County Road'
        # Form parameters will vary based on the selected "road type" tab
        if road_type == RoadType.ALL:
            self._set_all_roads_fields(
                extract=extract,
                jurisdiction=jurisdiction,
                county=county,
                city=city,
                query_type=query_type,
                begin_date=begin_date,
                end_date=end_date
            )
        elif road_type == RoadType.LOCAL:
            self._set_local_roads_fields(
                extract=extract,
                county=county,
                city=city,
                street=street,
                cross_street=cross_street,
                query_type=query_type,
                begin_mile_point=begin_mile_point,
                end_mile_point=end_mile_point,
                begin_date=begin_date,
                end_date=end_date,
                record_number=record_number,
                display_instructions=display_instructions
            )
        elif road_type == RoadType.HIGHWAY:
            self._set_highways_fields(
                extract=extract,
                begin_date=begin_date,
                end_date=end_date,
                highway=highway,
                begin_mile_point=begin_mile_point,
                end_mile_point=end_mile_point,
                highway_type=highway_type,
                z_mile_points=z_mile_points,
                add_mileage=add_mileage,
                non_add_mileage=non_add_mileage,
                record_number=record_number,
                display_instructions=display_instructions
            )
        # Submit the form
        response = self.submit()
        return response


@functools.lru_cache(maxsize=2)
def connect(echo: bool = False) -> Client:
    """
    Create a new `Client` or connect to an existing (cached) `Client`
    """
    return Client(echo=echo)
