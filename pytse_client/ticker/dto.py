from dataclasses import dataclass


@dataclass
class InstrumentInfo:
    eps: dict
    sector: dict
    static_threshold: dict
    min_week: float
    max_week: float
    min_year: float
    max_year: float
    q_tot_tran5_j_avg: float
    k_aj_cap_val_cps_idx: str
    d_even: float
    top_inst: float
    fara_desc: str
    contract_size: float
    nav: float
    under_supervision: float
    c_val_mne: str
    l_val18: str
    c_soc_csac: str
    l_soc30: str
    y_mar_nsc: str
    y_val: str
    ins_code: str
    l_val30: str
    l_val18_afc: str
    flow: float
    c_isin: str
    z_titad: float
    base_vol: float
    instrument_id: str
    cgr_val_cot: str
    c_com_val: str
    last_date: float
    source_id: float
    flow_title: str
    cgr_val_cot_title: str
