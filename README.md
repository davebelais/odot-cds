# Oregon Department of Transportation - Crash Data System

This package provides a client interface for extracting and parsing data from 
the [Oregon Department of Transportation's (ODOT's) Crash Data System (CDS)](
https://zigzag.odot.state.or.us).

Modules:

- [odot_cds.client](#odot-cds-client)
- [odot_cds.cds501](#odot-cds-cds501)

## <a name="odot-cds-client">odot_cds.client</a>

### Connecting to CDS

```python
from odot_cds.client import Client

client: Client = Client()
```

Optional `odot_cds.client.Client` parameters:

- hostname (str): This is the hostname for the CDS web server. In most cases 
  this parameter should not be necessary, as the default 
  "zigzag.odot.state.or.us" is the correct value for public access.
  
- echo (bool): If `True`, HTTP requests and responses will be printed. The
  default is `False`.
  
 ### Retrieving an extract or report from CDS

In the following example we retrieve a "CDS501" extract. This extract is the 
most appropriate if you wish to collect complete data sets for any given period
of time, however you can only retrieve data for one county or city per/request,
and only for up to 3 months at a time. If you want to collect data for all of 
Oregon--you can iterate through `odot_cds.client.Client().counties`, and pass
these values to the `county` parameter (making sure to set 
`jurisdiction='rdoSumJurisdictionCNTY'`).
```python
from odot_cds.client import Client, RoadType, Extract
from http.client import HTTPResponse
from datetime import date

# Connect to CDS
client: Client = Client()

# Retrieve a CDS501 extract for all of Multnomah county, during the month of 
# December, 2019.
response: HTTPResponse = client.extract(
    begin_date=date(2019, 12, 1),
    end_date=date(2019, 12, 31),
    road_type=RoadType.ALL,
    extract=Extract.CDS501,
    jurisdiction='rdoSumJurisdictionCNTY',
    county='Multnomah',
)
```

Parameters for `odot_cds.client.Client().extract()`:

- begin_date (datetime.date):
  The first day for which to retrieve records.

- end_date (datetime.date):
  The last day for which to retrieve records.

- road_type (RoadType):
  This indicates the type of roads to retrieve crash data for.

  - RoadType.ALL: Both highways and local roads (default)
  - RoadType.HIGHWAY: State highways
  - RoadType.LOCAL: Local roads

- extract (Extract):
  This indicates which extract/report to retrieve.

  - Extract.CDS150: "Summary by Year" (XLS)
  - Extract.CDS160: "Summary by Injury Severity" (XLS)
  - Extract.CDS190b: "Time/day of week" (XLS)
  - Extract.CDS200: "County Summary" (XLS)
  - Extract.CDS250: "City Summary" (XLS)
  - Extract.CDS280: "Summary by Month" (XLS)
  - Extract.CDS380: "Comprehensive PRC-11x17" (XLS)
  - Extract.CDS390: "Crash Location" (XLS)
  - Extract.CDS501: "Data Extract" (CSV)
  - Extract.CDS510: "Decode DB" (MDB)
  - Extract.DIRECTION: "Vehicle Direction" (XLS)
  - Extract.RRR: "Characteristics" (XLS)
  
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
  See `street`.

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


## <a name="odot-cds-cds501">odot_cds.cds501</a>

This module provides functions for parsing a CDS501 extract retrieved from CDS
using `odot_cds.client.Client().extract()`.

### Parse Crash, Vehicle, and Participant Data from a CDS501 `HTTPResponse`

The following example retrieves a CDS501 extract and parses that extract into
data frames corresponding to a fact table in the CDS510 "Decode" database.
```python
from odot_cds import cds501
from odot_cds.client import Client, RoadType, Extract
from http.client import HTTPResponse
from datetime import date

# Connect to CDS
client: Client = Client()

# Retrieve a CDS501 extract for all of Multnomah county, during the month of 
# December, 2019.
response: HTTPResponse = client.extract(
    begin_date=date(2019, 12, 1),
    end_date=date(2019, 12, 31),
    road_type=RoadType.ALL,
    extract=Extract.CDS501,
    jurisdiction='rdoSumJurisdictionCNTY',
    county='Multnomah',
)

# Parse a CDS501 response as 3 data frames: "crash", "vhcl", and "partic". 
# Each of these data frames corresponds to a fact table in the CDS510 "Decode"
# database.
crash_data_frame, vhcl_data_frame, partic_data_frame = cds501.get_data_frames(
    response
)
```

Additional functions available in this module are:
- read: This function will take a CDS501 `HTTPResponse` and return an iterable 
  of `odot_cds.cds501.CDS501` dataclass instances.
- split: This function will take a CDS501 `HTTPResponse` and return 3 lists:
  - A `list` of `odot_cds.cds501.Partic` dataclass instances
  - A `list` of `odot_cds.cds501.Vhcl` dataclass instances
  - A `list` of `odot_cds.cds501.Partic` dataclass instances.
