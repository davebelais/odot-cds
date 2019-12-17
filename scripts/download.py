#!/usr/bin/env python3

"""
This script will download source data from ODOT's public FTP
"""
import base64
import ftplib
import functools
import os
import socket
import sys
from traceback import format_exception
from typing import Optional, Tuple, Iterable, List
from urllib.parse import urlparse
from warnings import warn

SOURCES_DIRECTORY = os.path.abspath(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
) + '/sources'
ODOT_FTP_HOST = 'ftp.odot.state.or.us'
TRANSPORTATION_SAFETY_GIS_DIRECTORY = '/tdb/trandata/GIS_data/Safety'


def _get_proxy_url(url: Optional[str] = None) -> Optional[str]:
    """
    Return a proxy URL. Check for a proxy environment variable
    """
    if not url:
        for key in (
            'FTP_PROXY',
            'ftp_proxy',
            'HTTP_PROXY',
            'http_proxy'
        ):
            if key in os.environ:
                url: str = os.environ[key]
                break
    if url and ('://' not in url):
        url = 'http://' + url
    return url


@functools.lru_cache()
def _get_socket(
    hostname: str = '',
    port: int = 0,
    timeout: int = -999
) -> Optional[socket.socket]:
    """
    Get a socket
    """
    if timeout == -999:
        connection = socket.create_connection(
            (hostname, port)
        )
    else:
        connection = socket.create_connection(
            (hostname, port),
            timeout=timeout
        )
    return connection


@functools.lru_cache()
def _get_proxy_socket(
    proxy: str,
    hostname: str = '',
    port: int = 22,
    timeout: int = -999
) -> Optional[socket.socket]:
    """
    Get a socket connected through a proxy
    """
    parse_result = urlparse(proxy)
    # Connect to the proxy
    connection = _get_socket(
        hostname=parse_result.hostname,
        port=parse_result.port,
        timeout=timeout
    )
    # Connect to the FTP
    connection_string = (
        (
            'CONNECT %(hostname)s:%(port)s HTTP/1.1\r\n'
            'Host: %(hostname)s:%(port)s\r\n'
        ) % {
            'hostname': hostname,
            'port': port
        }
    )
    if parse_result.username or parse_result.password:
        connection_string += (
            'Proxy-Authorization: Basic %s\r\n' % str(
                base64.b64encode(
                    bytes(
                        '%s:%s' % (
                            parse_result.username or '',
                            parse_result.password or ''
                        ),
                        'utf-8'
                    )
                ),
                'utf-8'
            )
        )
    connection_string += '\r\n'
    connection.send(bytes(connection_string, encoding='UTF-8'))
    response: str = b''
    while not response.endswith(b'\r\n\r\n'):
        response += connection.recv(4096)
    # If the response is not "200"--raise an error
    if not response.split()[1] == b'200':
        raise socket.error(response)
    return connection


def get_socket(
    hostname: str = '',
    port: int = 22,
    proxy: str = '',
    timeout: int = -999
) -> Optional[socket.socket]:
    """
    Retrieve a socket connection
    """
    proxy = _get_proxy_url(proxy)
    if proxy:
        connection = _get_proxy_socket(
            proxy=proxy,
            hostname=hostname,
            port=port,
            timeout=timeout
        )
    else:
        if timeout == -999:
            connection = socket.create_connection(
                (hostname, port)
            )
        else:
            connection = socket.create_connection(
                (hostname, port),
                timeout=timeout
            )
    return connection


class FTP(ftplib.FTP):
    """
    This class adds support for proxies to `ftplib.FTP`, and adds a "walk"
    and "download" method.
    """

    port: int = 21

    def __init__(self, *args, **kwargs) -> None:
        self.proxy: Optional[str] = kwargs.pop('proxy', None)
        super().__init__(*args, **kwargs)

    def connect(
        self,
        host: str = '',
        port: int = 0,
        timeout: int = -999,
        source_address: Optional[Tuple[str, int]] = None
    ):
        """
        This method overrides `ftplib.FTP.connect()` in order to facilitate
        use of a proxy
        """
        if host != '':
            self.host = host
        if port > 0:
            self.port = port
        if timeout != -999:
            self.timeout = timeout
        socket = get_socket(
            hostname=self.host,
            port=self.port,
            proxy=self.proxy,
            timeout=self.timeout
        )
        if source_address is not None:
            self.source_address = source_address
            socket.bind(self.source_address)
        self.sock = socket
        self.af = self.sock.family
        self.debugging = True
        self.file = self.sock.makefile('r', encoding=self.encoding)
        self.welcome = self.getresp()
        return self.welcome

    def list(self, *args):
        '''
        Return a list of files in a given directory (default the current).
        '''
        cmd = 'LIST'
        for arg in args:
            cmd = cmd + (' ' + arg)
        files = []
        self.retrlines(cmd, files.append)
        return files

    def walk(
        self,
        directory_path: str = '.'
    ) -> Iterable[Tuple[str, List[str], List[str]]]:
        """
        Behaves similarly to `os.walk`, but for an FTP directory
        """
        files: List[str] = []
        directories: List[str] = []
        # Get the result of an FTP "LIST" command
        list_results: List[str, ...] = self.list(directory_path)
        # Get the result of an FTP "NLST" (name list) command
        for index, path in enumerate(self.nlst(directory_path)):
            if '<DIR>' in list_results[index]:
                directories.append(path)
            else:
                files.append(path)
        yield (directory_path, tuple(directories), tuple(files))
        for directory in directories:
            for result in self.walk(directory):
                yield result

    def download(self, source_path: str, target_path: str) -> None:
        # Create the parent directory if it does not exist
        target_directory_path = os.path.dirname(target_path)
        os.makedirs(target_directory_path, exist_ok=True)
        # Write the data
        with open(target_path, 'wb') as target_file:
            self.retrbinary(
                'RETR ' + source_path,
                callback=target_file.write
            )


def download_safety_data(
    host: str = ODOT_FTP_HOST,
    source_directory: str = TRANSPORTATION_SAFETY_GIS_DIRECTORY,
    target_directory: str = SOURCES_DIRECTORY,
    proxy: str = '',
    overwrite: bool = False
) -> None:
    """
    This function will download safety tables files from the FTP *if they do
    not already exist in the target directory*.
    """
    # Connect to the FTP
    ftp: Optional[FTP] = None
    while ftp is None:
        try:
            ftp = FTP(
                host=host,
                proxy=proxy
            )
        except (TimeoutError, EOFError):
            warn(''.join(format_exception(*sys.exc_info())))
    ftp.login()
    walker: Optional[Iterable[Tuple]] = None
    while walker is None:
        try:
            walker = ftp.walk(source_directory)
        except TimeoutError:
            warn(''.join(format_exception(*sys.exc_info())))
    for root, directories, files in walker:
        for source_file_path in files:
            target_file_path = target_directory + source_file_path
            if overwrite:
                try:
                    os.remove(target_file_path)
                except FileNotFoundError:
                    pass
            while not os.path.exists(target_file_path):
                try:
                    print(source_file_path)
                    ftp.download(
                        source_file_path,
                        target_file_path
                    )
                except TimeoutError:
                    warn(''.join(format_exception(*sys.exc_info())))


if __name__ == '__main__':
    download_safety_data(overwrite=True)



