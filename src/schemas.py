"""
CreditSense Pydantic Schemas.
Defines the structured output format for the Data Structuring Node.
These schemas ensure consistent, validated data extraction from credit reports.
"""

from typing import Optional
from pydantic import BaseModel, Field


class PersonalInfo(BaseModel):
    """Personal information extracted from the credit report."""
    full_name: str = Field(description="Full name as it appears on the report")
    date_of_birth: Optional[str] = Field(default=None, description="Date of birth (MM/DD/YYYY)")
    current_address: Optional[str] = Field(default=None, description="Current residential address")
    previous_address: Optional[str] = Field(default=None, description="Previous residential address")
    employer: Optional[str] = Field(default=None, description="Current employer name")
    ssn_last_four: Optional[str] = Field(default=None, description="Last 4 digits of SSN (masked)")


class CreditScore(BaseModel):
    """Credit score information."""
    score: int = Field(description="FICO credit score (300-850)")
    score_model: Optional[str] = Field(default=None, description="Score model used (e.g., FICO Score 8)")
    score_range: Optional[str] = Field(default=None, description="Score range (e.g., 300-850)")
    risk_level: Optional[str] = Field(default=None, description="Risk classification (Excellent/Good/Fair/Poor)")
    score_date: Optional[str] = Field(default=None, description="Date the score was generated")
    key_factors: list[str] = Field(default_factory=list, description="Key factors affecting the score")


class Account(BaseModel):
    """Individual credit account details."""
    account_name: str = Field(description="Creditor/account name (e.g., Chase Visa Platinum)")
    account_number_masked: Optional[str] = Field(default=None, description="Masked account number (e.g., XXXX-4521)")
    account_type: str = Field(description="Account type (e.g., Revolving Credit Card, Installment Loan)")
    date_opened: Optional[str] = Field(default=None, description="Date the account was opened")
    credit_limit: Optional[float] = Field(default=None, description="Credit limit in USD")
    current_balance: Optional[float] = Field(default=None, description="Current balance in USD")
    monthly_payment: Optional[float] = Field(default=None, description="Monthly payment amount in USD")
    payment_status: str = Field(description="Payment status (e.g., Current, 30 Days Late)")
    high_balance: Optional[float] = Field(default=None, description="Highest balance ever recorded in USD")
    account_status: str = Field(description="Account status (e.g., Open/Current, Closed)")
    date_closed: Optional[str] = Field(default=None, description="Date closed, if applicable")
    last_reported: Optional[str] = Field(default=None, description="Last date reported to bureau")


class Inquiry(BaseModel):
    """Hard credit inquiry record."""
    date: str = Field(description="Date of the inquiry")
    creditor: str = Field(description="Name of the creditor that pulled the report")
    inquiry_type: str = Field(description="Type of inquiry (e.g., Credit Card, Auto Loan)")


class AccountSummary(BaseModel):
    """Aggregated account summary statistics."""
    total_accounts: int = Field(description="Total number of accounts")
    open_accounts: int = Field(description="Number of open accounts")
    closed_accounts: int = Field(description="Number of closed accounts")
    total_balance: float = Field(description="Total balance across all accounts in USD")
    total_credit_limit: float = Field(description="Total credit limit across all accounts in USD")
    overall_utilization: float = Field(description="Overall credit utilization percentage (0-100)")
    oldest_account_date: Optional[str] = Field(default=None, description="Date of oldest account")
    average_account_age: Optional[str] = Field(default=None, description="Average age of accounts")
    on_time_payment_percentage: Optional[float] = Field(default=None, description="Percentage of on-time payments")
    total_late_payments: int = Field(default=0, description="Total number of late payments")
    hard_inquiries_count: int = Field(default=0, description="Number of hard inquiries in last 24 months")


class CreditReportData(BaseModel):
    """Complete structured credit report data — the output of the Data Structuring Node."""
    report_bureau: Optional[str] = Field(default=None, description="Credit bureau (Experian, TransUnion, Equifax)")
    report_date: Optional[str] = Field(default=None, description="Date of the report")
    report_number: Optional[str] = Field(default=None, description="Report reference number")
    personal_info: PersonalInfo
    credit_score: CreditScore
    accounts: list[Account] = Field(default_factory=list, description="List of credit accounts")
    inquiries: list[Inquiry] = Field(default_factory=list, description="List of hard credit inquiries")
    public_records: list[str] = Field(default_factory=list, description="Public records (bankruptcies, liens, etc.)")
    collections: list[str] = Field(default_factory=list, description="Collection accounts")
    account_summary: AccountSummary
