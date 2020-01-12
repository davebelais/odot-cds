"""
This module tests the functionality of the CDS client `odot_cds.client.Client`.
"""
import enum
import random
import sys
import warnings
from copy import copy
from datetime import date, timedelta
from functools import update_wrapper
from http.client import HTTPResponse
from time import sleep
from traceback import format_exception
from typing import Optional, Callable, Any, Sequence, Tuple, List, Iterable

import pandas

from odot_cds import client, cds501

# The following constants determine how long to wait between HTTP requests
# (a wait is necessary in order to avoid server errors)
MINIMUM_REQUEST_BUFFER: float = 1.0
MAXIMUM_REQUEST_BUFFER: float = 3.0


class Echo(enum.Enum):
    """
    This is an enumeration of options describing how much to echo when tests
    are run
    """

    ALL: int = 2
    MINIMAL: int = 1
    NONE: int = 0


# The following constant determines how much information to print, by default,
# when performing tests
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
                    if echo == Echo.ALL:
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


def validate_cds501_get_data_frames(*args, **kwargs) -> None:
    """
    Verify that data frames are returned without error when this data set is
    passed to `odot_cds.cds501.get_data_frames`
    """
    crashes_data_frame, vehicles_data_frame, participants_data_frame = (
        cds501.get_data_frames(
            *args,
            **kwargs
        )
    )
    assert isinstance(crashes_data_frame, pandas.DataFrame)
    assert isinstance(vehicles_data_frame, pandas.DataFrame)
    assert isinstance(participants_data_frame, pandas.DataFrame)


def validate_cds501_read(response: HTTPResponse) -> None:
    """
    Validate a CDS501 extract
    """
    # Only validate if there is at least one row in the response
    if int(response.headers['Content-Length']):
        # Collect the CDS501 iterable into a `tuple`
        cds501_rows: Tuple[cds501.CDS501] = tuple(cds501.read(response))
        # Check to ensure the CDS501 tuple is not empty
        if cds501_rows:
            assert isinstance(cds501_rows[0], cds501.CDS501)
            # Validate data frames obtained directly from an extract
            validate_cds501_get_data_frames(
                cds501_rows
            )
            # Validate data frames obtained from a split
            crashes, vehicles, participants = cds501.split(cds501_rows)
            assert isinstance(crashes[0], cds501.Crash)
            assert isinstance(vehicles[0], cds501.Vhcl)
            assert isinstance(participants[0], cds501.Partic)
            validate_cds501_get_data_frames(
                (crashes, vehicles, participants)
            )
        else:
            raise ValueError(
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
            validate_cds501_read(response)
        elif parameters['extract'] == client.Extract.CDS510:
            verify_magic_bytes(response, 'mdb')
        else:
            verify_magic_bytes(response, 'xls')
    except client.DisabledFormElementError:
        # This indicates the report is not available for the parameters
        # selected--this is a valid response, so we don't raise an error
        if echo == Echo.ALL:
            warnings.warn(get_exception_text())
    except client.InvalidRoadTypeExtractError:
        # This indicates the extract/report is not available for the
        # indicated road type
        if echo == Echo.ALL:
            warnings.warn(get_exception_text())


class ExtractParameterSets:
    """
    This class as an iterable object wherein each item is a set of parameters
    for passing to `extract_and_validate` (which will in turn pass the same
    parameters to `client.Client().extract`)
    """

    def __init__(self):
        # Create a client to hold parameter values and provide form field
        # options
        self.connection: client.Client = client.connect(
            echo=True if ECHO == Echo.ALL else False
        )

    def __iter__(self) -> Iterable[dict]:
        """
        Yield dictionaries representing each set of parameters to test
        """
        # Determine the date range
        end_date: date = client.get_last_year_end()
        begin_date: date = end_date - timedelta(days=7)
        parameters: dict = dict(
            begin_date=begin_date,
            end_date=end_date
        )
        parameter_sets: List[dict] = []
        for road_type in client.RoadType:
            parameters['road_type'] = road_type
            if road_type == client.RoadType.ALL:
                parameter_sets += self.get_all_roads_parameters(**parameters)
            elif road_type == client.RoadType.HIGHWAY:
                parameter_sets += self.get_highways_parameters(**parameters)
            else:
                parameter_sets += self.get_local_roads_parameters(**parameters)
        for parameter_set in parameter_sets:
            yield parameter_set

    def get_extract_parameters(self, **parameters) -> List[dict]:
        """
        Perform each applicable extract/report for a set of parameters
        """
        parameter_sets: List[dict] = []
        for extract in client.Extract:
            parameters.update(extract=extract)
            parameter_sets.append(copy(parameters))
        return parameter_sets

    def get_all_roads_county_parameters(
        self,
        **parameters
    ) -> List[dict]:
        """
        Populate parameter sets with a randomly selected county
        """
        counties: Tuple[str] = tuple(
            value
            for key, value in (
                self.connection.form_fields.all_roads_county.options.items()
            )
            if (
                'Multnomah' in key or
                'Washington' in key or
                'Clackamas' in key or
                'Lane' in key
            )
        )
        assert len(counties) == 4
        # Choose a county at random
        parameters.update(
            county=random.choice(counties)
        )
        self.connection.update_form_field(
            'all_roads_county',
            parameters['county']
        )
        return self.get_all_roads_query_types_parameters(**parameters)

    def get_all_roads_city_parameters(
        self,
        **parameters
    ) -> List[dict]:
        """
        Populate parameter sets with a randomly selected city
        """
        cities: Tuple[str] = tuple(
            self.connection.form_fields.all_roads_city.options.values()
        )
        if cities:
            # Choose a city at random
            parameters.update(
                city=random.choice(cities)
            )
            return self.get_all_roads_query_types_parameters(**parameters)
        else:
            raise RuntimeError(
                'No cities found for the following set of parameters: ' +
                represent_parameters(multiline=True, **parameters)
            )

    def get_all_roads_query_types_parameters(
        self,
        **parameters
    ) -> List[dict]:
        """
        Populate a query type at random
        """
        parameter_sets: List[dict] = []
        query_type: str = random.choice([
            'rdoSumQueryTypeALL',  # All Roads
            'rdoSumQueryTypeCNTY',  # County Roads
            'rdoSumQueryTypeCITY',  # "City Streets",
            'rdoSumQueryTypeSTATE',  # State Highways
        ])
        parameters.update(query_type=query_type)
        parameter_sets += self.get_extract_parameters(**parameters)
        return parameter_sets

    def get_local_roads_streets_parameters(
        self,
        **parameters
    ) -> List[dict]:
        """
        Populate parameter sets with a randomly selected `street`
        """
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
        return self.get_extract_parameters(**parameters)

    def get_local_roads_query_types_parameters(
        self,
        **parameters
    ) -> List[dict]:
        """
        Populate a query type at random
        """
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
        parameter_sets: List[dict] = []
        query_type: str = random.choice(query_types)
        parameters.update(query_type=query_type)
        parameter_sets += self.get_local_roads_streets_parameters(
            **parameters
        )
        return parameter_sets

    def get_all_roads_parameters(
        self,
        **parameters
    ) -> List[dict]:
        """
        Populate parameter sets with one randomly selected county, and one
        randomly selected city
        """
        parameters.update(jurisdiction='rdoSumJurisdictionCNTY')
        self.connection.update_form_field(
            'all_roads_jurisdiction',
            'rdoSumJurisdictionCNTY'
        )
        parameter_sets: List[dict] = self.get_all_roads_county_parameters(
            **parameters
        )
        parameters.update(jurisdiction='rdoSumJurisdictionCITY')
        self.connection.update_form_field(
            'all_roads_jurisdiction',
            'rdoSumJurisdictionCITY'
        )
        parameter_sets += self.get_all_roads_city_parameters(**parameters)
        return parameter_sets

    def get_highways_mileage_parameters(
        self,
        **parameters
    ) -> List[dict]:
        """
        Add parameter sets for each possible combination of `add_mileage` and
        `non_add_mileage` values
        """
        parameter_sets: List[dict] = []
        # Always include a fully inclusive request
        add_mileage_options: List[Tuple[bool, bool]] = list([
            (True, True)
        ])
        # Randomly select either add-mileage or non-add-mileage as a second
        # option
        add_mileage_options.append(random.choice([
            (True, False),
            (False, True)
        ]))
        for non_add_mileage, add_mileage in add_mileage_options:
            parameters['non_add_mileage'] = non_add_mileage
            parameters['add_mileage'] = add_mileage
            parameter_sets += self.get_highways_z_mile_points_parameters(
                **parameters
            )
        return parameter_sets

    def get_highways_z_mile_points_parameters(
        self,
        **parameters
    ) -> List[dict]:
        parameter_sets: List[dict] = []
        for z_mile_points in (
            True,
            False
        ):
            parameters['z_mile_points'] = z_mile_points
            parameter_sets += self.get_extract_parameters(**parameters)
        return parameter_sets

    def get_highways_parameters(
        self,
        **parameters
    ) -> List[dict]:
        """
        Populate a `highway` and `highway_type` parameter at random
        """
        parameters['highway'] = random.choice(
            tuple(self.connection.highways.keys())
        )
        parameters['highway_type'] = random.choice(
            tuple(client.HighwayType)
        )
        return self.get_highways_mileage_parameters(**parameters)

    def get_local_roads_parameters(
        self,
        **parameters
    ) -> List[dict]:
        """
        Populate a `county` and `city` parameter, randomly selecting from the
        4 most populous counties
        """
        counties: Tuple[str] = tuple(
            value
            for key, value in (
                self.connection.form_fields.local_roads_county.options.items()
            )
            if (
                'Multnomah' in key or
                'Washington' in key or
                'Clackamas' in key or
                'Lane' in key
            )
        )
        assert len(counties) == 4
        cities: Tuple[str] = tuple()
        parameter_sets: List[dict] = []
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
                parameter_sets += self.get_local_roads_query_types_parameters(
                    **parameters
                )
        return parameter_sets


def buffer_request() -> None:
    """
    Sleep for a random period of time between 1 and 3 seconds, in order to
    avoid overburdening the server with requests
    """
    precision: int = 100
    sleep(random.randrange(
        MINIMUM_REQUEST_BUFFER * precision,
        MAXIMUM_REQUEST_BUFFER * precision) / precision
    )


def test_extracts():
    """
    This function constructs multiple sets of parameters to pass to
    `odot_cds.client.Client().extract()`, and validates the results returned
    for each.
    """
    for parameters in ExtractParameterSets():
        extract_and_validate(**parameters)
        buffer_request()


if __name__ == '__main__':
    test_extracts()
