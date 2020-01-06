import enum
import os
import pandas

DIRECTORY: str = os.path.abspath(os.path.dirname(__file__))


class Dimensions(enum.Enum):
    """
    An enumeration of the dimension tables needed for use with fact tables
    retrieved from ODOT's CDS.
    """

    ACTN: str = 'actn'
    CAUSE: str = 'cause'
    CITY_FIPS_HIST: str = 'city_fips_hist'
    CITY_SECT: str = 'city_sect'
    CMPSS_DRCT: str = 'cmpss_drct'
    CNTY: str = 'cnty'
    COLLIS_TYP: str = 'collis_typ'
    # CRASH: str = 'crash'
    CRASH_HR: str = 'crash_hr'
    CRASH_KEY_XREF: str = 'crash_key_xref'
    CRASH_SVRTY: str = 'crash_svrty'
    CRASH_TYP: str = 'crash_typ'
    DRVR_LIC_STAT: str = 'drvr_lic_stat'
    DRVR_RES_STAT: str = 'drvr_res_stat'
    ERR: str = 'err'
    EVNT: str = 'evnt'
    FUNC_CLASS: str = 'func_class'
    HWY_COMPNT: str = 'hwy_compnt'
    HWY_HIST: str = 'hwy_hist'
    IMPCT_LOC: str = 'impct_loc'
    INJ_SVRTY: str = 'inj_svrty'
    INVSTG_AGY: str = 'invstg_agy'
    ISECT_TYP: str = 'isect_typ'
    JRSDCT_GRP: str = 'jrsdct_grp'
    LGT_COND: str = 'lgt_cond'
    MEDN_TYP: str = 'medn_typ'
    MLGE_TYP: str = 'mlge_typ'
    MVMNT: str = 'mvmnt'
    NON_MOTRST_LOC: str = 'non_motrst_loc'
    # PARTIC: str = 'partic'
    PARTIC_TYP: str = 'partic_typ'
    POP_RNG: str = 'pop_rng'
    RD_CHAR: str = 'rd_char'
    RD_CNTL: str = 'rd_cntl'
    RD_SURF_COND: str = 'rd_surf_cond'
    RDWY: str = 'rdwy'
    RTE: str = 'rte'
    SEX: str = 'sex'
    SFTY_EQUIP_USE: str = 'sfty_equip_use'
    SPECL_JRSDCT: str = 'specl_jrsdct'
    TRAF_CNTL_DEVICE: str = 'traf_cntl_device'
    URB_AREA: str = 'urb_area'
    URB_AREA_FIPS_HIST: str = 'urb_area_fips_hist'
    # VHCL: str = 'vhcl'
    VHCL_OWNSHP: str = 'vhcl_ownshp'
    VHCL_TYP: str = 'vhcl_typ'
    VHCL_USE: str = 'vhcl_use'
    WKDAY: str = 'wkday'
    WTHR_COND: str = 'wthr_cond'


def get_data_frame(
    table: Dimensions
) -> pandas.DataFrame:
    """
    Load an ODOT-CDS table as an instance of `pandas.DataFrame`.
    """
    assert isinstance(table, Dimensions)
    path: str = DIRECTORY + '/{}.pickle'.format(
        table.value.lower()
    )
    try:
        return pandas.read_pickle(path)
    except:
        pass


def _verify_mdbtools_installed():
    """
    Verify that MBPTools has been installed
    """
    if os.name == 'nt':
        raise NotImplementedError(
            'Updating the dimension tables required MDBTools, which is not'
            'available for Windows'
        )


def update() -> None:
    """
    Update the dimension tables
    """
    _verify_mdbtools_installed()
