import random
from datetime import date, timedelta
from http.client import HTTPResponse

from odot_cds import client


def _verify_magic_bytes(
    response: HTTPResponse,
    extension: str
) -> None:
    """
    Verify that the response has the correct Magic Bytes for the file type
    """
    if extension == 'pdf':
        assert response.read(4) == b'%PDF-'
    elif extension in ('xls', 'mdb'):
        assert response.read(8) == b'\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1'


def _extract_and_validate(
    **parameters
) -> None:
    """
    Perform an extract with the given parameters and validate that the correct
    type of response was received
    """
    connection: client.Client = client.connect(echo=False)
    response: HTTPResponse = connection.extract(**parameters)
    print(
        'odot_cds.client.Client().extract(**%s)' %
        repr(parameters)
    )
    if parameters['extract'] == client.Extract.CDS501:
        # CDS501 is text (a CSV), so verify the content can be interpreted as
        # UTF-8 without throwing an error
        str(
            response.read(),
            encoding='utf-8'
        )
    elif parameters['extract'] == client.Extract.CDS510:
        _verify_magic_bytes(response, 'mdb')
    else:
        if parameters['report_format'] in (
            'Print Format', 'rdoHwyReportFormatPDF'
        ):
            _verify_magic_bytes(response, 'pdf')
        else:
            _verify_magic_bytes(response, 'xls')



def _extract_report_formats(
    **parameters
) -> None:
    if parameters['export'] in (
        client.Export.CDS501,
        client.Export.CDS510
    ):
        _extract_and_validate(**parameters)
    else:
        for report_format in ('Excel Format', 'Print Format'):
            parameters.update(report_format=report_format)
            _extract_and_validate(**parameters)


def _extract_all_roads_county(
    **parameters
) -> None:
    connection: client.Client = client.Client(echo=False)
    # Choose a county at random
    parameters.update(
        county=random.choice(
            tuple(connection.counties.values())
        )
    )
    _extract_all_roads_query_types(**parameters)


def _extract_all_roads_city(
    **parameters
) -> None:
    connection: client.Client = client.connect(echo=False)
    # Choose a city at random
    parameters.update(
        city=random.choice(
            tuple(connection.cities.keys())
        )
    )
    _extract_all_roads_query_types(**parameters)


def _extract_all_roads_query_types(
    **parameters
) -> None:
    for query_type in (
        "All Roads",
        "County Roads",
        "City Streets",
        "State Highways"
    ):
        parameters.update(query_type=query_type)
        _extract_report_formats(**parameters)


def _extract_local_roads_streets(
    **parameters
) -> None:
    connection: client.Client = client.connect(echo=False)
    # If a query type is specified, set it so that the correct street options
    # are populated
    if 'query_type' in parameters:
        connection.update_form_field(
            'local_roads_query_type',
            parameters['query_type']
        )
    # Set the city/section, so that the street options get updated
    connection.update_form_field(
        'local_roads_city',
        parameters['city']
    )
    # Choose a street at random
    parameters.update(
        street=random.choice(
            tuple(
                connection.form_fields.local_roads_street.options.keys()
            )
        )
    )
    if parameters['query_type'] in (
        'opnLclSPQuery', 'Specified Streets Not Limited to Intersection',
        'opnLclINQuery', 'Intersectional'
    ):
        # Set the street, so that the `cross_street` options get updated
        connection.update_form_field(
            'local_roads_street',
            parameters['street']
        )
        # Choose a cross-street at random
        parameters.update(
            cross_street=random.choice(
                tuple(
                    (
                        connection.form_fields.local_roads_cross_street
                    ).options.keys()
                )
            )
        )
    _extract_report_formats(**parameters)


def _extract_local_roads_query_types(
    **parameters
) -> None:
    if parameters['city'] in ('000', 'Outside City Limits'):
        query_types = (
            "Mile-Pointed County Road",
        )
    else:
        query_types = (
            "Street Segment & Intersectional",
            "Specified Streets Not Limited to Intersection",
            "Intersectional"
        )
    for query_type in query_types:
        parameters.update(query_type=query_type)
        _extract_local_roads_streets(**parameters)


def _extract_local_roads_county(
    **parameters
) -> None:
    connection: client.Client = client.Client(echo=False)
    # Choose a county at random
    parameters.update(
        county=random.choice(
            tuple(connection.counties.values())
        )
    )
    _extract_all_roads_query_types(**parameters)


def _extract_all_roads(
    **parameters
) -> None:
    for jurisdiction in ('County', 'City'):
        parameters.update(jurisdiction=jurisdiction)
        if jurisdiction == 'County':
            _extract_all_roads_county(**parameters)
        else:
            _extract_all_roads_city(**parameters)


def _extract_highways_mileage(
    **parameters
) -> None:
    for non_add_mileage, add_mileage in (
        (True, True),
        (True, False),
        (False, True)
    ):
        parameters.update['non_add_mileage'] = non_add_mileage
        parameters.update['add_mileage'] = add_mileage
        _extract_highways_z_mile_points(**parameters)


def _extract_highways_z_mile_points(
    **parameters
) -> None:
    for z_mile_points in (
        True,
        False
    ):
        parameters.update['z_mile_points'] = z_mile_points
        _extract_report_formats(**parameters)


def _extract_highways(
    **parameters
) -> None:
    connection: client.Client = client.connect(echo=False)
    # Choose a highways segment and type at random
    parameters['highway'] = random.choice(
        tuple(
            connection.highways.keys()
        )
    )
    parameters['highway_type'] = random.choice(
        tuple(
            client.HighwayType
        )
    )
    _extract_highways_mileage(**parameters)


def _extract_local_roads(
    **parameters
) -> None:
    connection: client.Client = client.connect(echo=False)
    # Set the county, so that the city/section options get updated
    connection.update_form_field(
        'local_roads_county',
        parameters['county']
    )
    # Choose a city/section at random
    parameters.update(
        city=random.choice(
            tuple(
                connection.form_fields.local_roads_city.options.keys()
            )
        )
    )
    _extract_local_roads_query_types(**parameters)


def test_extract():
    """
    Retrieve and validate an export for the last week of last year, for
    multiple parameter sets representing the breadth of possible report/extract
    configurations
    """
    end_date: date = client.get_last_year_end()
    begin_date: date = end_date - timedelta(days=7)
    parameters: dict = dict(
        begin_date=begin_date,
        end_date=end_date
    )
    for road_type in client.RoadType:
        parameters.update(road_type=road_type)
        for extract in client.Extract:
            parameters.update(extract=extract)
            if road_type == client.RoadType.ALL:
                _extract_all_roads(**parameters)
            elif road_type == client.RoadType.HIGHWAY:
                _extract_highways(**parameters)
            else:
                _extract_local_roads(**parameters)


if __name__ == '__main__':
    test_extract()