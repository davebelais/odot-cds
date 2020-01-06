"""
This module tests the functionality of the CDS client `odot_cds.client.Client`.
"""
import enum
import random
import sys
import warnings
from datetime import date, timedelta
from functools import update_wrapper
from http.client import HTTPResponse
from time import sleep
from traceback import format_exception
from typing import Optional, Callable, Any, Sequence, Tuple, Iterable

import pandas

from odot_cds import client, cds501


class Echo(enum.Enum):
    """
    This is an enumeration of options describing how much to echo when tests
    are run
    """

    ALL: int = 2
    MINIMAL: int = 1
    NONE: int = 0


ECHO: Echo = Echo.MINIMAL


def get_exception_text() -> str:
    """
    When called within an exception, this function returns a text
    representation of the error matching what is found in
    `traceback.print_exception`, but is returned as a string value rather than
    printing.
    """
    return ''.join(format_exception(*sys.exc_info()))


class InvalidFileTypeError(Exception):

    pass


def retry(
    exception_types: Sequence[type] = (Exception,),
    number_of_attempts: int = 3,
    echo: Echo = ECHO
) -> Callable:
    """
    This is a decorator function which causes a function to be executed
    multiple times if the indicated exceptions are encountered (although
    raising any other exceptions)

    Parameters:

    - exception_types ([type])

      The types of exceptions for which additional attempts should be
      permitted (up to `number_of_attempts` times)

    - number_of_attempts (int):

      The number of time the function should be attempted

    - echo (Echo):

      If `echo != Echo.NONE`, prints the number of failed attempts if
      applicable
    """

    def decorating_function(user_function: Callable) -> Callable:

        def wrapper(*args, **kwargs) -> Callable:
            error: Optional[Exception] = None
            return_value: Any = None
            number_of_failed_attempts: int = 0
            for i in range(number_of_attempts):
                try:
                    return_value = user_function(*args, **kwargs)
                    error = None
                    break
                except exception_types as e:
                    if echo != Echo.NONE:
                        warnings.warn(get_exception_text())
                    number_of_failed_attempts += 1
                    error = e
                    # Exponential backoff
                    if i < (number_of_attempts - 1):
                        sleep(2**i)
            if error is not None:
                raise error
            if (echo != Echo.NONE) and number_of_failed_attempts:
                print(
                    '(success preceded by %s failed attempts)' %
                    str(number_of_failed_attempts)
                )
            return return_value

        return update_wrapper(wrapper, user_function)

    return decorating_function


def verify_magic_bytes(
    response: HTTPResponse,
    extension: str
) -> None:
    """
    Verify that the data in the provided HTTP response has the correct Magic
    Bytes for the provided file name extension
    """
    assert isinstance(response, HTTPResponse)
    if extension == 'xls':
        magic_bytes: bytes = b'\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1'
    elif extension == 'mdb':
        magic_bytes: bytes = b'\x00\x01\x00\x00Standard Jet DB\x00\x01\x00\x00'
    else:
        return
    data: bytes = response.read(len(magic_bytes))
    if not data:
        raise client.EmptyResponseError(
            'No records found:\n' + str(response.info())
        )
    elif data != magic_bytes:
        data += response.read()
        try:
            data_representation: str = str(data, encoding='utf-8')
        except UnicodeDecodeError:
            data_representation: str = repr(data)
        raise InvalidFileTypeError(
            '%s\n%s' % (
                response.info(),
                data_representation
            )
        )


def represent_parameters(multiline: bool = False, **parameters) -> str:
    return (
        '(\n%s\n)'
        if multiline else
        '(%s)'
    ) % (
        (
            ',\n'
            if multiline else
            ', '
        ).join(
            (
                '    %s=%s'
                if multiline else
                '%s=%s'
            ) % (key, repr(value))
            for key, value in parameters.items()
        )
    )


def validate_get_data_frames(*args, **kwargs) -> None:
    crashes_data_frame, vehicles_data_frame, participants_data_frame = (
        cds501.get_data_frames(
            *args,
            **kwargs
        )
    )
    assert isinstance(crashes_data_frame, pandas.DataFrame)
    assert isinstance(vehicles_data_frame, pandas.DataFrame)
    assert isinstance(participants_data_frame, pandas.DataFrame)


def validate_cds501(response: HTTPResponse) -> None:
    """
    Validate a CDS501 extract
    """
    # Collect the CDS501 iterable into a `tuple`
    cds501_rows: Tuple[cds501.CDS501] = tuple(cds501.read(response))
    # Check to ensure the CDS501 tuple is not empty
    if cds501_rows:
        assert isinstance(cds501_rows[0], cds501.CDS501)
        # Validate data frames obtained directly from an extract
        validate_get_data_frames(
            cds501_rows
        )
        # Validate data frames obtained from a split
        crashes, vehicles, participants = cds501.split(cds501_rows)
        assert isinstance(crashes[0], cds501.Crash)
        assert isinstance(vehicles[0], cds501.Vhcl)
        assert isinstance(participants[0], cds501.Partic)
        validate_get_data_frames(
            (crashes, vehicles, participants)
        )
    else:
        warnings.warn(
            'No records found:\n' + str(response.info())
        )


@retry(
    exception_types=(InvalidFileTypeError, client.EmptyResponseError),
    number_of_attempts=10,
    echo=ECHO
)
def extract_and_validate(
    echo: bool = ECHO,
    **parameters
) -> None:
    """
    Perform an extract with the given parameters and validate that the correct
    type of response was received
    """
    # Print the function call to be performed
    print(
        'client.Client().extract' +
        represent_parameters(**parameters)
    )
    try:
        # CDS occasionally (but infrequently) returns an empty result or an
        # HTML page instead of the file--so we retry 10 times to make sure
        # it's an issue with the client/request and not with the server
        response: HTTPResponse = client.connect(
            echo=True if ECHO.value >= Echo.ALL.value else False
        ).extract(**parameters)
        if parameters['extract'] == client.Extract.CDS501:
            validate_cds501(response)
        elif parameters['extract'] == client.Extract.CDS510:
            verify_magic_bytes(response, 'mdb')
        else:
            verify_magic_bytes(response, 'xls')
    except client.DisabledFormElementError:
        # This indicates the report is not available for the parameters
        # selected--this is a valid response, so we don't raise an error
        if echo != Echo.ALL:
            warnings.warn(get_exception_text())
    except client.InvalidRoadTypeExtractError:
        # This indicates the extract/report is not available for the
        # indicated road type
        if echo == Echo.ALL:
            warnings.warn(get_exception_text())
    # Sleep for a random period of time between 1 and 3 seconds, in order to
    # avoid overburdening the server with requests
    precision: int = 100
    sleep(random.randrange(1 * precision, 3 * precision)/precision)


class ExtractsTest:
    """
    This class holds form data while field values are manipulated and options
    retrieved in order to construct parameter sets to test
    """

    def __init__(self):
        # Create a client to hold parameter values and provide form field
        # options
        self.connection: client.Client = client.connect(
            echo=True if ECHO == Echo.ALL else False
        )

    def __call__(self):
        # Determine the date range
        end_date: date = client.get_last_year_end()
        begin_date: date = end_date - timedelta(days=7)
        parameters: dict = dict(
            begin_date=begin_date,
            end_date=end_date
        )
        for road_type in client.RoadType:
            parameters['road_type'] = road_type
            if road_type == client.RoadType.ALL:
                self.extract_all_roads(**parameters)
            elif road_type == client.RoadType.HIGHWAY:
                self.extract_highways(**parameters)
            else:
                self.extract_local_roads(**parameters)

    def extract(self, **parameters) -> None:
        """
        Perform each applicable extract/report for a set of parameters
        """
        for extract in client.Extract:
            parameters.update(extract=extract)
            extract_and_validate(**parameters)

    def extract_all_roads_county(
        self,
        **parameters
    ) -> None:
        counties: Tuple[str] = tuple(
            self.connection.form_fields.all_roads_county.options.values()
        )
        # Choose a county at random
        parameters.update(
            county=random.choice(counties)
        )
        self.connection.update_form_field(
            'all_roads_county',
            parameters['county']
        )
        self.extract_all_roads_query_types(**parameters)

    def extract_all_roads_city(
        self,
        **parameters
    ) -> None:
        cities: Tuple[str] = tuple(
            self.connection.form_fields.all_roads_city.options.values()
        )
        if cities:
            # Choose a city at random
            parameters.update(
                city=random.choice(cities)
            )
            self.extract_all_roads_query_types(**parameters)
        else:
            raise RuntimeError(
                'No cities found for the following set of parameters: ' +
                represent_parameters(multiline=True, **parameters)
            )

    def extract_all_roads_query_types(
        self,
        **parameters
    ) -> None:
        for query_type in (
            'rdoSumQueryTypeALL',  # All Roads
            'rdoSumQueryTypeCNTY',  # County Roads
            'rdoSumQueryTypeCITY',  # "City Streets",
            'rdoSumQueryTypeSTATE',  # State Highways
        ):
            parameters.update(query_type=query_type)
            self.extract(**parameters)

    def extract_local_roads_streets(
        self,
        **parameters
    ) -> None:
        # If a query type is specified, set it so that the correct street
        # options are populated
        if 'query_type' in parameters:
            # Update the form to reflect the indicated query type
            self.connection.update_form_field(
                'local_roads_query_type',
                parameters['query_type']
            )
        else:
            # Retrieve the default query type
            parameters[
                'query_type'
            ] = self.connection.form_fields.local_roads_query_type.value
        # Set the city/section, so that the street options get updated
        self.connection.update_form_field(
            'local_roads_city',
            parameters['city']
        )
        streets: Tuple[str] = tuple(
            self.connection.form_fields.local_roads_street.options.values()
        )
        if streets:
            # Choose a street at random
            parameters.update(
                street=random.choice(streets)
            )
        else:
            raise RuntimeError(
                'No streets found for the following set of parameters: ' +
                represent_parameters(multiline=True, **parameters)
            )
        if parameters['query_type'] in (
            'opnLclSPQuery',
            'opnLclINQuery',
        ):
            if streets:
                # Set the street, so that the `cross_street` options get
                # updated
                self.connection.update_form_field(
                    'local_roads_street',
                    parameters['street']
                )
                cross_streets: Tuple[str] = tuple(
                    (
                        self.connection.form_fields.local_roads_cross_street
                    ).options.values()
                )
                if cross_streets:
                    # Choose a cross-street at random
                    parameters.update(
                        cross_street=random.choice(cross_streets)
                    )
        self.extract(**parameters)

    def extract_local_roads_query_types(
        self,
        **parameters
    ) -> None:
        if parameters['city'] == '000':
            query_types = (
                'rdoLclQueryTypeMP',  # Mile-Pointed County Road
            )
        else:
            query_types = (
                # Street Segment & Intersectional
                'rdoLclQueryTypeSI',
                # Specified Streets Not Limited to Intersection
                'rdoLclQueryTypeSP',
                # Intersectional
                'rdoLclQueryTypeIN'
            )
        for query_type in query_types:
            parameters.update(query_type=query_type)
            self.extract_local_roads_streets(**parameters)

    def extract_local_roads_county(
        self,
        **parameters
    ) -> None:
        # Choose a county at random
        parameters.update(
            county=random.choice(
                tuple(self.connection.counties.values())
            )
        )
        self.extract_all_roads_query_types(**parameters)

    def extract_all_roads(
        self,
        **parameters
    ) -> None:
        parameters.update(jurisdiction='rdoSumJurisdictionCNTY')
        self.connection.update_form_field(
            'all_roads_jurisdiction',
            'rdoSumJurisdictionCNTY'
        )
        self.extract_all_roads_county(**parameters)
        parameters.update(jurisdiction='rdoSumJurisdictionCITY')
        self.connection.update_form_field(
            'all_roads_jurisdiction',
            'rdoSumJurisdictionCITY'
        )
        self.extract_all_roads_city(**parameters)

    def extract_highways_mileage(
        self,
        **parameters
    ) -> None:
        for non_add_mileage, add_mileage in (
            (True, True),
            (True, False),
            (False, True)
        ):
            parameters['non_add_mileage'] = non_add_mileage
            parameters['add_mileage'] = add_mileage
            self.extract_highways_z_mile_points(**parameters)

    def extract_highways_z_mile_points(
        self,
        **parameters
    ) -> None:
        for z_mile_points in (
            True,
            False
        ):
            parameters['z_mile_points'] = z_mile_points
            self.extract(**parameters)

    def extract_highways(
        self,
        **parameters
    ) -> None:
        # Choose a highways segment and type at random
        parameters['highway'] = random.choice(
            tuple(self.connection.highways.keys())
        )
        parameters['highway_type'] = random.choice(
            tuple(client.HighwayType)
        )
        self.extract_highways_mileage(**parameters)

    def extract_local_roads(
        self,
        **parameters
    ) -> None:
        counties: Tuple[str] = tuple(
            self.connection.form_fields.local_roads_county.options.values()
        )
        cities: Tuple[str] = tuple()
        # Some counties may not have any cities with local roads--so we repeat
        # until `cities` is a non-empty tuple (usually this will only require
        # one iteration, however)
        while not cities:
            # Choose a county at random
            parameters.update(
                county=random.choice(counties)
            )
            # Set the county, so that the city/section options get updated
            self.connection.update_form_field(
                'local_roads_county',
                parameters['county']
            )
            cities: Tuple[str] = tuple(
                self.connection.form_fields.local_roads_city.options.values()
            )
            if cities:
                # Choose a city/section at random
                parameters.update(
                    city=random.choice(cities)
                )
                # Set the city/section, so that the street options get updated
                self.connection.update_form_field(
                    'local_roads_city',
                    parameters['city']
                )
                self.extract_local_roads_query_types(**parameters)


def test_extracts():
    """
    This function constructs multiple sets of parameters to pass to
    `odot_cds.client.Client().extract()`, and validates the results returned
    for each.
    """
    extracts_test: ExtractsTest = ExtractsTest()
    extracts_test()


def test_disabled_form_element_error():
    connection: client.Client = client.connect(
        echo=True if ECHO == Echo.ALL else False
    )


if __name__ == '__main__':
    # from odot_cds.client import *
    # import datetime
    # extract_and_validate(
    #     begin_date=datetime.date(2018, 12, 24), end_date=datetime.date(2018, 12, 31), road_type=RoadType.HIGHWAY, highway='171,-0.01,49.97', highway_type=HighwayType.FRONTAGE_ROAD, non_add_mileage=True, add_mileage=True, z_mile_points=True, extract=Extract.CDS501
    # )
    test_extracts()