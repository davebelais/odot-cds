from dataclasses import dataclass, fields
from datetime import date
from decimal import Decimal
from http.client import HTTPResponse
from typing import Optional, Iterable, Tuple, Set, List, Union

from odot_cds import client


@dataclass(unsafe_hash=True, frozen=True)
class CDS501:

    crash_id: int
    rec_typ_cd: Optional[str]
    vhcl_id: Optional[int]
    partic_id: Optional[int]
    partic_dsply_seq_no: Optional[int]
    vhcl_coded_seq_no: Optional[int]
    partic_vhcl_seq_no: Optional[int]
    ser_no: Optional[str]
    crash_mo_no: Optional[str]
    crash_day_no: Optional[str]
    crash_yr_no: Optional[str]
    crash_wk_day_cd: Optional[str]
    crash_hr_no: Optional[str]
    cnty_id: Optional[str]
    city_sect_id: Optional[int]
    urb_area_cd: Optional[int]
    fc_cd: Optional[str]
    nhs_flg: Optional[bool]
    hwy_no: Optional[str]
    hwy_sfx_no: Optional[str]
    rdwy_no: Optional[str]
    hwy_compnt_cd: Optional[str]
    mlge_typ_cd: Optional[str]
    rd_con_no: Optional[str]
    lrs_val: Optional[str]
    lat_deg_no: Optional[int]
    lat_minute_no: Optional[int]
    lat_sec_no: Optional[Decimal]
    longtd_deg_no: Optional[int]
    longtd_minute_no: Optional[int]
    longtd_sec_no: Optional[Decimal]
    specl_jrsdct_id: Optional[str]
    jrsdct_grp_cd: Optional[str]
    agy_st_no: Optional[str]
    isect_agy_st_no: Optional[str]
    isect_seq_no: Optional[int]
    from_isect_dstnc_qty: Optional[int]
    cmpss_dir_cd: Optional[str]
    mp_no: Optional[Decimal]
    post_speed_lmt_val: Optional[str]
    rd_char_cd: Optional[str]
    off_rdwy_flg: Optional[bool]
    isect_typ_cd: Optional[str]
    isect_rel_flg: Optional[bool]
    rndabt_flg: Optional[bool]
    drvwy_rel_flg: Optional[bool]
    ln_qty: Optional[int]
    turng_leg_qty: Optional[int]
    medn_typ_cd: Optional[str]
    impct_loc_cd: Optional[str]
    crash_typ_cd: Optional[str]
    collis_typ_cd: Optional[str]
    crash_svrty_cd: Optional[str]
    wthr_cond_cd: Optional[str]
    rd_surf_cond_cd: Optional[str]
    lgt_cond_cd: Optional[str]
    traf_cntl_device_cd: Optional[str]
    traf_cntl_func_flg: Optional[bool]
    invstg_agy_cd: Optional[str]
    crash_evnt_1_cd: Optional[str]
    crash_evnt_2_cd: Optional[str]
    crash_evnt_3_cd: Optional[str]
    crash_cause_1_cd: Optional[str]
    crash_cause_2_cd: Optional[str]
    crash_cause_3_cd: Optional[str]
    schl_zone_ind: Optional[str]
    wrk_zone_ind: Optional[str]
    alchl_invlv_flg: Optional[bool]
    drug_invlv_flg: Optional[bool]
    crash_speed_invlv_flg: Optional[bool]
    crash_hit_run_flg: Optional[bool]
    pop_rng_cd: Optional[str]
    rd_cntl_cd: Optional[str]
    rte_typ_cd: Optional[str]
    rte_id: Optional[str]
    reg_id: Optional[str]
    dist_id: Optional[str]
    seg_mrk_id: Optional[str]
    seg_pt_lrs_meas: Optional[float]
    unloct_flg: Optional[bool]
    tot_vhcl_cnt: Optional[int]
    tot_fatal_cnt: Optional[int]
    tot_inj_lvl_a_cnt: Optional[int]
    tot_inj_lvl_b_cnt: Optional[int]
    tot_inj_lvl_c_cnt: Optional[int]
    tot_inj_cnt: Optional[int]
    tot_uninjd_age00_04_cnt: Optional[int]
    tot_uninjd_per_cnt: Optional[int]
    tot_ped_cnt: Optional[int]
    tot_ped_fatal_cnt: Optional[int]
    tot_ped_inj_cnt: Optional[int]
    tot_pedcycl_cnt: Optional[int]
    tot_pedcycl_fatal_cnt: Optional[int]
    tot_pedcycl_inj_cnt: Optional[int]
    tot_unknwn_cnt: Optional[int]
    tot_unknwn_fatal_cnt: Optional[int]
    tot_unknwn_inj_cnt: Optional[int]
    tot_occup_cnt: Optional[int]
    tot_per_invlv_cnt: Optional[int]
    tot_sfty_equip_used_qty: Optional[int]
    tot_sfty_equip_unused_qty: Optional[int]
    tot_sfty_equip_use_unknown_qty: Optional[int]
    vhcl_ownshp_cd: Optional[str]
    vhcl_use_cd: Optional[str]
    vhcl_typ_cd: Optional[str]
    emrgcy_vhcl_use_flg: Optional[bool]
    trlr_qty: Optional[int]
    vhcl_mvmnt_cd: Optional[str]
    cmpss_dir_from_cd: Optional[str]
    cmpss_dir_to_cd: Optional[str]
    actn_cd: Optional[str]
    vhcl_cause_1_cd: Optional[str]
    vhcl_cause_2_cd: Optional[str]
    vhcl_cause_3_cd: Optional[str]
    vhcl_evnt_1_cd: Optional[str]
    vhcl_evnt_2_cd: Optional[str]
    vhcl_evnt_3_cd: Optional[str]
    vhcl_speed_flg: Optional[bool]
    vhcl_hit_run_flg: Optional[bool]
    vhcl_sfty_equip_used_qty: Optional[int]
    vhcl_sfty_equip_unused_qty: Optional[int]
    vhcl_sfty_equip_use_unknwn_qty: Optional[int]
    vhcl_occup_cnt: Optional[int]
    strikg_vhcl_flg: Optional[bool]
    partic_typ_cd: Optional[str]
    partic_hit_run_flg: Optional[bool]
    pub_empl_flg: Optional[bool]
    sex_cd: Optional[str]
    age_val: Optional[str]
    drvr_lic_stat_cd: Optional[str]
    drvr_res_stat_cd: Optional[str]
    inj_svrty_cd: Optional[str]
    sfty_equip_use_cd: Optional[str]
    airbag_deploy_ind: Optional[str]
    mvmnt_cd: Optional[str]
    cmpss_dir_from_cd: Optional[str]
    cmpss_dir_to_cd: Optional[str]
    non_motrst_loc_cd: Optional[str]
    actn_cd: Optional[str]
    partic_err_1_cd: Optional[str]
    partic_err_2_cd: Optional[str]
    partic_err_3_cd: Optional[str]
    partic_cause_1_cd: Optional[str]
    partic_cause_2_cd: Optional[str]
    partic_cause_3_cd: Optional[str]
    partic_evnt_1_cd: Optional[str]
    partic_evnt_2_cd: Optional[str]
    partic_evnt_3_cd: Optional[str]
    bac_val: Optional[str]
    alchl_use_rpt_ind: Optional[str]
    drug_use_rpt_ind: Optional[str]
    strikg_partic_flg: Optional[bool]


CDS501_FIELDS: Tuple[object] = fields(CDS501)

CDS501_FIELD_NAMES: Set[str] = set(
    field_.name
    for field_ in CDS501_FIELDS
)


@dataclass(unsafe_hash=True, frozen=True)
class Crash:

    crash_id: int
    ser_no: Optional[str]
    crash_mo_no: Optional[str]
    crash_day_no: Optional[str]
    crash_yr_no: Optional[str]
    crash_wk_day_cd: Optional[str]
    crash_hr_no: Optional[str]
    cnty_id: Optional[str]
    city_sect_id: Optional[int]
    urb_area_cd: Optional[int]
    fc_cd: Optional[str]
    nhs_flg: Optional[bool]
    hwy_no: Optional[str]
    hwy_sfx_no: Optional[str]
    rdwy_no: Optional[str]
    hwy_compnt_cd: Optional[str]
    mlge_typ_cd: Optional[str]
    rd_con_no: Optional[str]
    lrs_val: Optional[str]
    lat_deg_no: Optional[int]
    lat_minute_no: Optional[int]
    lat_sec_no: Optional[Decimal]
    longtd_deg_no: Optional[int]
    longtd_minute_no: Optional[int]
    longtd_sec_no: Optional[Decimal]
    specl_jrsdct_id: Optional[str]
    jrsdct_grp_cd: Optional[str]
    agy_st_no: Optional[str]
    isect_agy_st_no: Optional[str]
    isect_seq_no: Optional[int]
    from_isect_dstnc_qty: Optional[int]
    cmpss_dir_cd: Optional[str]
    mp_no: Optional[Decimal]
    post_speed_lmt_val: Optional[str]
    rd_char_cd: Optional[str]
    off_rdwy_flg: Optional[bool]
    isect_typ_cd: Optional[str]
    isect_rel_flg: Optional[bool]
    rndabt_flg: Optional[bool]
    drvwy_rel_flg: Optional[bool]
    ln_qty: Optional[int]
    turng_leg_qty: Optional[int]
    medn_typ_cd: Optional[str]
    impct_loc_cd: Optional[str]
    crash_typ_cd: Optional[str]
    collis_typ_cd: Optional[str]
    crash_svrty_cd: Optional[str]
    wthr_cond_cd: Optional[str]
    rd_surf_cond_cd: Optional[str]
    lgt_cond_cd: Optional[str]
    traf_cntl_device_cd: Optional[str]
    traf_cntl_func_flg: Optional[bool]
    invstg_agy_cd: Optional[str]
    crash_evnt_1_cd: Optional[str]
    crash_evnt_2_cd: Optional[str]
    crash_evnt_3_cd: Optional[str]
    crash_cause_1_cd: Optional[str]
    crash_cause_2_cd: Optional[str]
    crash_cause_3_cd: Optional[str]
    schl_zone_ind: Optional[str]
    wrk_zone_ind: Optional[str]
    alchl_invlv_flg: Optional[bool]
    drug_invlv_flg: Optional[bool]
    crash_speed_invlv_flg: Optional[bool]
    crash_hit_run_flg: Optional[bool]
    pop_rng_cd: Optional[str]
    rd_cntl_cd: Optional[str]
    rte_typ_cd: Optional[str]
    rte_id: Optional[str]
    reg_id: Optional[str]
    dist_id: Optional[str]
    seg_mrk_id: Optional[str]
    seg_pt_lrs_meas: Optional[float]
    unloct_flg: Optional[bool]
    tot_vhcl_cnt: Optional[int]
    tot_fatal_cnt: Optional[int]
    tot_inj_lvl_a_cnt: Optional[int]
    tot_inj_lvl_b_cnt: Optional[int]
    tot_inj_lvl_c_cnt: Optional[int]
    tot_inj_cnt: Optional[int]
    tot_uninjd_age00_04_cnt: Optional[int]
    tot_uninjd_per_cnt: Optional[int]
    tot_ped_cnt: Optional[int]
    tot_ped_fatal_cnt: Optional[int]
    tot_ped_inj_cnt: Optional[int]
    tot_pedcycl_cnt: Optional[int]
    tot_pedcycl_fatal_cnt: Optional[int]
    tot_pedcycl_inj_cnt: Optional[int]
    tot_unknwn_cnt: Optional[int]
    tot_unknwn_fatal_cnt: Optional[int]
    tot_unknwn_inj_cnt: Optional[int]
    tot_occup_cnt: Optional[int]
    tot_per_invlv_cnt: Optional[int]
    tot_sfty_equip_used_qty: Optional[int]
    tot_sfty_equip_unused_qty: Optional[int]
    tot_sfty_equip_use_unknown_qty: Optional[int]


CRASH_FIELD_NAMES: Set[str] = set(
    field_.name
    for field_ in fields(Crash)
)


@dataclass(unsafe_hash=True, frozen=True)
class Vhcl:

    crash_id: Optional[int]
    vhcl_id: int
    vhcl_coded_seq_no: Optional[int]
    vhcl_ownshp_cd: Optional[str]
    vhcl_use_cd: Optional[str]
    vhcl_typ_cd: Optional[str]
    emrgcy_vhcl_use_flg: Optional[bool]
    trlr_qty: Optional[int]
    vhcl_mvmnt_cd: Optional[str]
    cmpss_dir_from_cd: Optional[str]
    cmpss_dir_to_cd: Optional[str]
    actn_cd: Optional[str]
    vhcl_cause_1_cd: Optional[str]
    vhcl_cause_2_cd: Optional[str]
    vhcl_cause_3_cd: Optional[str]
    vhcl_evnt_1_cd: Optional[str]
    vhcl_evnt_2_cd: Optional[str]
    vhcl_evnt_3_cd: Optional[str]
    vhcl_speed_flg: Optional[bool]
    vhcl_hit_run_flg: Optional[bool]
    vhcl_sfty_equip_used_qty: Optional[int]
    vhcl_sfty_equip_unused_qty: Optional[int]
    vhcl_sfty_equip_use_unknwn_qty: Optional[int]
    vhcl_occup_cnt: Optional[int]
    strikg_vhcl_flg: Optional[bool]


VHCL_FIELD_NAMES: Set[str] = set(
    field_.name
    for field_ in fields(Vhcl)
)


@dataclass(unsafe_hash=True, frozen=True)
class Partic:

    crash_id: Optional[int]
    vhcl_id: Optional[int]
    partic_id: int
    partic_dsply_seq_no: Optional[int]
    vhcl_coded_seq_no: Optional[int]
    partic_vhcl_seq_no: Optional[int]
    partic_typ_cd: Optional[str]
    partic_hit_run_flg: Optional[bool]
    pub_empl_flg: Optional[bool]
    sex_cd: Optional[str]
    age_val: Optional[str]
    drvr_lic_stat_cd: Optional[str]
    drvr_res_stat_cd: Optional[str]
    inj_svrty_cd: Optional[str]
    sfty_equip_use_cd: Optional[str]
    airbag_deploy_ind: Optional[str]
    mvmnt_cd: Optional[str]
    cmpss_dir_from_cd: Optional[str]
    cmpss_dir_to_cd: Optional[str]
    non_motrst_loc_cd: Optional[str]
    actn_cd: Optional[str]
    partic_err_1_cd: Optional[str]
    partic_err_2_cd: Optional[str]
    partic_err_3_cd: Optional[str]
    partic_cause_1_cd: Optional[str]
    partic_cause_2_cd: Optional[str]
    partic_cause_3_cd: Optional[str]
    partic_evnt_1_cd: Optional[str]
    partic_evnt_2_cd: Optional[str]
    partic_evnt_3_cd: Optional[str]
    bac_val: Optional[str]
    alchl_use_rpt_ind: Optional[str]
    drug_use_rpt_ind: Optional[str]
    strikg_partic_flg: Optional[bool]


PARTIC_FIELD_NAMES = set(
    field_.name
    for field_ in fields(Partic)
)


def extract(
    road_type: client.RoadType = client.RoadType.ALL,
    jurisdiction: str = '',
    county: str = '',
    city: str = '',
    street: str = '',
    cross_street: str = '',
    query_type: str = 'All Roads',
    begin_date: date = client.DEFAULT_BEGIN_DATE,
    end_date: date = client.DEFAULT_END_DATE,
    report_format: str = 'Excel Format',
    highway: str = '',
    begin_mile_point: float = 0.0,
    end_mile_point: float = 0.0,
    highway_type: client.HighwayType = client.HighwayType.ALL,
    z_mile_points: bool = True,
    add_mileage: bool = True,
    non_add_mileage: bool = True
) -> Iterable[CDS501]:
    """
    This method yields a series of `CDS501` instances.

    Parameters:

    - road_type (RoadType):

      This indicates the type of roads to retrieve crash data for.

      - RoadType.ALL: Both highways and local roads (default)

      - RoadType.HIGHWAY: State highways

      - RoadType.LOCAL: Local roads

    - jurisdiction (str):

      This applies only if `road_type == RoadType.ALL`.

      - "County": Return all crashes for a specified county.

      - "City": Return all crashes for a specified city.

    - county (str):

      The name or ID of a county. For a complete mapping of county names
      to county IDs, create an instance of `Client` and inspect
      `Client().form_fields.county`.

    - city (str):

      The name or ID of a city. For a complete mapping of city names
      to city IDs, create an instance of `Client` and inspect
      `Client().form_fields.city`.

    - query_type (str):

      The type of roads for which to retrieve crash data.

      If `road_type == RoadType.ALL`, options for this will include:

      - "All Roads" (default)
      - "County Roads"
      - "City Streets"
      - "State Highways"

      If `road_type == RoadType.LOCAL`, options for this will include:

      - "Street Segment & Intersectional" (default)
      - "Specified Streets Not Limited to Intersection"
      - "Intersectional"
      - "Mile-Pointed County Road"

    - report_format (str):

      This parameter does not apply if `extract == client.Extract.CDS501` or
      `extract == client.Extract.CDS510`.

      - "Excel Format" (default)
      - "Print Format"

    - highway (str):

      The number + name of a highway.

    - z_mile_points (bool)

    - add_mileage (bool):

      Include traffic traveling in a direction wherein progress corresponds
      to a numeric increase for mileage markers.

    - non_add_mileage (bool):

      Include traffic traveling in a direction wherein progress corresponds
      to a numeric decrease for mileage markers.

    Additional information about terms used above can be found
    in ODOT's [CDS code manual](
    https://www.oregon.gov/ODOT/Data/documents/CDS_Code_Manual.pdf).
    """
    connection = client.connect()
    response: HTTPResponse = connection.extract(
        extract=client.Extract.CDS501,
        road_type=road_type,
        jurisdiction=jurisdiction,
        county=county,
        city=city,
        street=street,
        cross_street=cross_street,
        query_type=query_type,
        begin_date=begin_date,
        end_date=end_date,
        report_format=report_format,
        highway=highway,
        begin_mile_point=begin_mile_point,
        end_mile_point=end_mile_point,
        highway_type=highway_type,
        z_mile_points=z_mile_points,
        add_mileage=add_mileage,
        non_add_mileage=non_add_mileage
    )


def get_crash_vhcl_partic(
    rows: Iterable[CDS501]
) -> (
    List[Crash],
    List[Vhcl],
    List[Partic]
):
    """
    Given an iterable of `CDS501` instances, return 3 iterables--one of
    `Crash` instances, one of `Vhcl` instances, and one of `Partic` instances.
    """
    crash_rows: List[Crash] = []
    vhcl_rows: List[Vhcl] = []
    partic_rows: List[Partic] = []
    for row in rows:
        if row.rec_typ_cd == '1':
            # Populate `Crash` values
            values: List[Union[str, int, Decimal, float, bool]] = []
            for index in range(len(CDS501_FIELDS)):
                if CDS501_FIELDS.name in CRASH_FIELD_NAMES:
                    values.append(row[index])
            crash_rows.append(Crash(*values))
        elif row.rec_typ_cd == '2':
            # Populate `Vhcl` values
            values: List[Union[str, int, Decimal, float, bool]] = []
            for index in range(len(CDS501_FIELDS)):
                if CDS501_FIELDS.name in CRASH_FIELD_NAMES:
                    values.append(row[index])
            vhcl_rows.append(Vhcl(*values))
        elif row.rec_typ_cd == '3':
            # Populate `Partic` values
            values: List[Union[str, int, Decimal, float, bool]] = []
            for index in range(len(CDS501_FIELDS)):
                if CDS501_FIELDS.name in CRASH_FIELD_NAMES:
                    values.append(row[index])
            partic_rows.append(Partic(*values))
    return crash_rows, vhcl_rows, partic_rows

