#!/usr/bin/env python3
"""
Generate Synthetic Banking Data

Produces realistic banking datasets for the thesis project:
- customers.parquet: 100K customer records
- loans.parquet: 500K loan records
- transactions/date=YYYY-MM-DD/*.parquet: 10M transaction records (365 partitions)
- fraud_labels.parquet: 50K fraud labels

All data uses fixed seeds (42) for reproducibility.
"""

import numpy as np
import pandas as pd
from faker import Faker
from datetime import datetime, timedelta
from pathlib import Path
import pyarrow as pa
import pyarrow.parquet as pq

# Configuration
DATA_DIR = Path(__file__).parent
N_CUSTOMERS = 100_000
N_LOANS = 500_000
N_TRANSACTIONS = 10_000_000
N_TXN_PER_DAY = N_TRANSACTIONS // 365  # ~27K per day
N_DAYS = 365
N_FRAUD_LABELS = 50_000

FAKE_SEED = 42
RNG_SEED = 42

fake = Faker(locale='en_US')
Faker.seed(FAKE_SEED)
rng = np.random.default_rng(RNG_SEED)


def generate_customers() -> pd.DataFrame:
    """Generate customer records."""
    print("Generating customers.parquet (100K rows)...")

    customer_ids = [f"C-{i:05d}" for i in range(1, N_CUSTOMERS + 1)]
    names = [fake.name() for _ in range(N_CUSTOMERS)]
    dobs = [fake.date_of_birth(minimum_age=18, maximum_age=80) for _ in range(N_CUSTOMERS)]
    cities = [fake.city() for _ in range(N_CUSTOMERS)]
    account_open_dates = [datetime.now().date() - timedelta(days=int(d)) for d in rng.uniform(365, 15*365, N_CUSTOMERS)]
    credit_tiers = rng.choice(['EXCELLENT', 'GOOD', 'FAIR', 'POOR'], N_CUSTOMERS, p=[0.15, 0.35, 0.35, 0.15])
    emails = [fake.email() for _ in range(N_CUSTOMERS)]
    monthly_incomes = np.maximum(0, rng.normal(4500, 2000, N_CUSTOMERS))

    df = pd.DataFrame({
        'customer_id': customer_ids,
        'name': names,
        'dob': dobs,
        'city': cities,
        'account_open_date': account_open_dates,
        'credit_tier': credit_tiers,
        'email': emails,
        'monthly_income': monthly_incomes,
    })

    pq.write_table(pa.Table.from_pandas(df), DATA_DIR / "customers.parquet", compression='snappy')
    print(f"  Wrote {len(df):,} customer records")
    return df


def generate_loans(customers_df: pd.DataFrame) -> pd.DataFrame:
    """Generate loan records. ~5 loans per customer on average."""
    print("Generating loans.parquet (500K rows)...")

    # Randomly sample customer IDs with replacement (Zipf-like distribution)
    customer_ids = rng.choice(customers_df['customer_id'].values, N_LOANS, replace=True)
    loan_ids = [f"L-{i:06d}" for i in range(1, N_LOANS + 1)]
    amounts = rng.lognormal(mean=9.5, sigma=0.7, size=N_LOANS)  # ~10K to 30K
    terms = rng.choice([12, 24, 36, 48, 60, 84, 120], N_LOANS, p=[0.15, 0.20, 0.25, 0.20, 0.12, 0.05, 0.03])
    rates = rng.uniform(3.5, 24.0, N_LOANS)
    statuses = rng.choice(['ACTIVE', 'PAID', 'DEFAULT', 'DELINQUENT'], N_LOANS, p=[0.60, 0.30, 0.05, 0.05])
    purposes = rng.choice(['HOME', 'AUTO', 'PERS', 'EDUC'], N_LOANS, p=[0.40, 0.35, 0.20, 0.05])
    origination_dates = [datetime.now().date() - timedelta(days=int(d)) for d in rng.uniform(10, 5*365, N_LOANS)]
    on_time_payments = (rng.uniform(0, 1, N_LOANS) * terms).astype(int)  # 0 to term payments
    total_payments = (rng.uniform(0.5, 1.1, N_LOANS) * terms).astype(int)  # Simulate some overpayment
    days_past_due = np.where(statuses == 'DELINQUENT', rng.integers(1, 365, N_LOANS), 0)

    df = pd.DataFrame({
        'loan_id': loan_ids,
        'customer_id': customer_ids,
        'amount': amounts,
        'term': terms,
        'rate': rates,
        'status': statuses,
        'purpose': purposes,
        'origination_date': origination_dates,
        'on_time_payments': on_time_payments,
        'total_payments': total_payments,
        'days_past_due': days_past_due,
    })

    pq.write_table(pa.Table.from_pandas(df), DATA_DIR / "loans.parquet", compression='snappy')
    print(f"  Wrote {len(df):,} loan records")
    return df


def generate_transactions(customers_df: pd.DataFrame) -> None:
    """Generate transaction records partitioned by date."""
    print(f"Generating transactions ({N_TRANSACTIONS:,} rows / {N_DAYS} days)...")

    txn_dir = DATA_DIR / "transactions"
    txn_dir.mkdir(exist_ok=True)

    customer_ids_array = customers_df['customer_id'].values
    cities_array = customers_df['city'].values
    # Build city map for geo-baseline lookups
    city_map = dict(zip(customer_ids_array, cities_array))

    txn_id_counter = 0
    merchants = [fake.company() for _ in range(1000)]  # Pre-generate merchants
    mccs = [f"{rng.integers(1000, 9999)}" for _ in range(100)]  # Standard MCCs

    start_date = datetime.now().date() - timedelta(days=N_DAYS - 1)

    for day_idx in range(N_DAYS):
        current_date = start_date + timedelta(days=day_idx)
        txn_ids = [f"T-{txn_id_counter + i:08d}" for i in range(N_TXN_PER_DAY)]
        txn_id_counter += N_TXN_PER_DAY

        # Zipf distribution: some customers transact more
        customer_ids = rng.choice(customer_ids_array, N_TXN_PER_DAY, replace=True)
        amounts = rng.lognormal(mean=5.5, sigma=1.0, size=N_TXN_PER_DAY)  # ~$250 typical
        merchants_sel = rng.choice(merchants, N_TXN_PER_DAY)
        mccs_sel = rng.choice(mccs, N_TXN_PER_DAY)

        # Geographic: 90% home city, 10% anomaly (random city)
        cities = []
        for cid in customer_ids:
            if rng.random() < 0.1:  # 10% geo anomaly
                cities.append(fake.city())
            else:
                cities.append(city_map.get(cid, fake.city()))

        # Channels
        channels = rng.choice(['POS', 'ATM', 'ONL', 'MOB'], N_TXN_PER_DAY, p=[0.50, 0.20, 0.20, 0.10])

        # Timestamps: business hours weighted, but we'll use a simple time distribution
        hours = rng.normal(loc=14, scale=4, size=N_TXN_PER_DAY)  # Most transactions 10 AM - 6 PM
        hours = np.clip(hours, 0, 23).astype(int)
        minutes = rng.integers(0, 60, N_TXN_PER_DAY)
        seconds = rng.integers(0, 60, N_TXN_PER_DAY)
        timestamps = [
            datetime.combine(current_date, datetime.min.time()).replace(hour=h, minute=m, second=s).isoformat()
            for h, m, s in zip(hours, minutes, seconds)
        ]

        df = pd.DataFrame({
            'txn_id': txn_ids,
            'customer_id': customer_ids,
            'amount': amounts,
            'merchant': merchants_sel,
            'mcc': mccs_sel,
            'city': cities,
            'timestamp': timestamps,
            'channel': channels,
            'date': [current_date] * N_TXN_PER_DAY,
        })

        # Write partition
        partition_dir = txn_dir / f"date={current_date}"
        partition_dir.mkdir(exist_ok=True)
        pq.write_table(
            pa.Table.from_pandas(df),
            partition_dir / "part-0000.parquet",
            compression='snappy'
        )

        if (day_idx + 1) % 50 == 0:
            print(f"  Wrote {day_idx + 1} / {N_DAYS} daily partitions ({day_idx + 1} * {N_TXN_PER_DAY:,} rows)")

    print(f"  Total: {N_TRANSACTIONS:,} transaction records across {N_DAYS} partitions")


def generate_fraud_labels() -> None:
    """Generate fraud labels for a sample of transactions."""
    print("Generating fraud_labels.parquet (50K rows)...")

    # For simplicity, generate random txn_ids that "might" exist
    # In a real scenario, these would be sampled from actual txn_ids
    txn_ids = [f"T-{rng.integers(0, N_TRANSACTIONS):08d}" for _ in range(N_FRAUD_LABELS)]
    is_fraud = rng.choice([True, False], N_FRAUD_LABELS, p=[0.15, 0.85])
    fraud_types = rng.choice(['CARD_NOT_PRESENT', 'ACCOUNT_TAKEOVER', 'IDENTITY_THEFT', 'NONE'], N_FRAUD_LABELS)
    detection_methods = rng.choice(['RULE_BASED', 'ML_MODEL', 'MANUAL_REVIEW'], N_FRAUD_LABELS)

    df = pd.DataFrame({
        'txn_id': txn_ids,
        'is_fraud': is_fraud,
        'fraud_type': fraud_types,
        'detection_method': detection_methods,
    })

    pq.write_table(pa.Table.from_pandas(df), DATA_DIR / "fraud_labels.parquet", compression='snappy')
    print(f"  Wrote {len(df):,} fraud label records")


def main():
    """Main data generation flow."""
    print("=" * 70)
    print("Synthetic Data Generation for COBOL + Python Thesis Project")
    print("=" * 70)
    print()

    # Generate each dataset
    customers = generate_customers()
    print()
    generate_loans(customers)
    print()
    generate_transactions(customers)
    print()
    generate_fraud_labels()

    print()
    print("=" * 70)
    print("Data generation complete!")
    print("=" * 70)
    print(f"Output directory: {DATA_DIR.absolute()}")


if __name__ == "__main__":
    main()
