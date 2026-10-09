# Motor Insurance Analytics

An end-to-end analytics solution for a motor insurance company that
ingests raw operational data, validates it, cleans it, performs EDA and
KPI analysis, generates business insights, and exposes the results via a
Streamlit dashboard. The application is containerized with Docker and
deployable to AWS EC2 via Amazon ECR.

## Business Scenario

You are a Data / Business Analyst for a motor insurance company. The
company manages customers, policies, vehicles, claims, and claim
payments. Management wants to understand policy activity, premium
collection, claim behavior, claim severity, settlement performance,
customer patterns, and operational risk indicators.

## Business Problem

- How many policies are active, expired, cancelled, renewed?
- Which policy types generate the most premium?
- How many claims are approved, rejected, pending?
- What is total / average claim amount?
- Which vehicle types / regions generate more claims?
- Which customer segments generate higher claim values?
- What is average settlement time?
- How does premium compare with claim cost?
- Which policy types have higher claim ratios?

## Objectives

- Convert raw data into validated, cleaned, business-ready data
- Perform EDA and statistical analysis
- Calculate insurance KPIs
- Identify patterns and convert them into insights
- Build a Streamlit dashboard
- Test with pytest, add logging
- Containerize with Docker
- Deploy to AWS EC2 via Amazon ECR

## Technology Stack

- Python 3.11
- pandas, numpy
- matplotlib, seaborn
- streamlit
- pytest
- Docker
- AWS ECR, IAM, EC2

## Data Model and Table Relationships

| Table | Primary Key | Relationships | Purpose |
|-------|-------------|---------------|---------|
| customers | customer_id | customer_id → policies | Customer profile |
| vehicles | vehicle_id | vehicle_id → policies | Vehicle attributes |
| policies | policy_id | customer_id, vehicle_id | Policy & premium |
| claims | claim_id | policy_id, customer_id | Claim event |
| payments | payment_id | claim_id, policy_id | Settlement |

## Project Structure
