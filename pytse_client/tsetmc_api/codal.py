from dataclasses import dataclass
from typing import Any

from pytse_client.tsetmc_api._convert import number_text_to_float


@dataclass(frozen=True, slots=True)
class CodalPublisher:
    # end of the fiscal year as "MM/DD", e.g. "12/29"
    financial_year: str | None
    id: int | None = None
    symbol: str | None = None
    display_symbol: str | None = None
    name: str | None = None
    isic: str | None = None
    reporting_type: str | None = None
    executive_manager: str | None = None
    financial_manager: str | None = None
    address: str | None = None
    office_address: str | None = None
    share_office_address: str | None = None
    tel_no: str | None = None
    fax_no: str | None = None
    website: str | None = None
    email: str | None = None
    activity_subject: str | None = None
    state: str | None = None
    state_name: str | None = None
    company_type: str | None = None
    company_type1: str | None = None
    inspector: str | None = None
    auditor_name: str | None = None
    insp_listed_capitalector: str | None = None
    # million rial
    listed_capital: int | None = None
    company_id: str | None = None
    national_code: str | None = None
    management_group: str | None = None
    en_management_group: str | None = None
    en_name: str | None = None
    en_displayed_symbol: str | None = None
    en_activity_subject: str | None = None
    en_address: str | None = None
    en_office_address: str | None = None
    en_share_office_address: str | None = None
    en_executive_manager: str | None = None
    en_financial_manager: str | None = None
    en_inspector: str | None = None


def parse_codal_publisher(data: Any) -> CodalPublisher | None:
    publisher = data.get("codalPublisher")
    if not publisher:
        return None
    listed_capital = number_text_to_float(publisher.get("listedCapital"))
    return CodalPublisher(
        financial_year=publisher["financialYear"],
        id=publisher.get("id"),
        symbol=publisher.get("symbol"),
        display_symbol=publisher.get("displaySymbol"),
        name=publisher.get("name"),
        isic=publisher.get("isic"),
        reporting_type=publisher.get("reportingType"),
        executive_manager=publisher.get("executiveManager"),
        financial_manager=publisher.get("financialManager"),
        address=publisher.get("address"),
        office_address=publisher.get("officeAddress"),
        share_office_address=publisher.get("shareOfficeAddress"),
        tel_no=publisher.get("telNo"),
        fax_no=publisher.get("faxNo"),
        website=publisher.get("website"),
        email=publisher.get("email"),
        activity_subject=publisher.get("activitySubject"),
        state=publisher.get("state"),
        state_name=publisher.get("stateName"),
        company_type=publisher.get("companyType"),
        company_type1=publisher.get("companyType1"),
        inspector=publisher.get("inspector"),
        auditor_name=publisher.get("auditorName"),
        insp_listed_capitalector=publisher.get("inspListedCapitalector"),
        listed_capital=(
            int(listed_capital) if listed_capital is not None else None
        ),
        company_id=publisher.get("companyId"),
        national_code=publisher.get("nationalCode"),
        management_group=publisher.get("managementGroup"),
        en_management_group=publisher.get("enManagementGroup"),
        en_name=publisher.get("enName"),
        en_displayed_symbol=publisher.get("enDisplayedSymbol"),
        en_activity_subject=publisher.get("enActivitySubject"),
        en_address=publisher.get("enAddress"),
        en_office_address=publisher.get("enOfficeAddress"),
        en_share_office_address=publisher.get("enShareOfficeAddress"),
        en_executive_manager=publisher.get("enExecutiveManager"),
        en_financial_manager=publisher.get("enFinancialManager"),
        en_inspector=publisher.get("enInspector"),
    )
