"""
Synthetic Data Generation for Vault Digital Bank.
Generates realistic Users, Accounts, and Transactions data
"""

from faker import Faker
from datetime import datetime, timedelta
import random
import csv

from typing import List, Dict, Optional
from decimal import Decimal, ROUND_DOWN

fake = Faker()

# Transcation categories for realistic spending patterns
TRANSACTION_CATEGORIES = [
    "Food & Dining",
    "Groceries",
    "Shopping",
    "Transportation",
    "Bills & Utilities",
    "Entertainment",
    "Healthcare",
    "Travel",
    "Gas & Fuel",
    "Coffee Shops",
    "Restaurants",
    "Online Services",
    "ATM Withdrawal",
    "Transfer",
    "Salary",
    "Investment",
]

# Merchant names by category
MERCHANT_BY_CATEGORY = {
    "Food & Dining": ["McDonald's", "Burger King", "Taco Bell", "Pizza Hut", "Subway"],
    "Groceries": ["Walmart", "Target", "Kroger", "Whole Foods", "Safeway"],
    "Shopping": ["Amazon", "eBay", "Best Buy", "Home Depot", "Costco"],
    "Transportation": ["Uber", "Lyft", "Metro Transit", "Delta Airlines", "Amtrak"],
    "Bills & Utilities": ["Electric Company", "Water Department", "Internet Provider", "Phone Company"],
    "Entertainment": ["Netflix", "Spotify", "Movie Theater", "Concert Venue"],
    "Healthcare": ["CVS Pharmacy", "Walgreens", "Hospital", "Dental Office"],
    "Travel": ["Airbnb", "Booking.com", "Hilton", "Marriott"],
    "Gas & Fuel": ["Shell", "Exxon", "BP", "Chevron"],
    "Coffee Shops": ["Starbucks", "Dunkin'", "Local Coffee Shop", "Peet's Coffee"],
    "Restaurants": ["Olive Garden", "Red Lobster", "Outback Steakhouse", "Local Restaurant"],
    "Online Services": ["Adobe", "Microsoft", "Google Cloud", "AWS"],
    "ATM Withdrawal": ["ATM - Bank of America", "ATM - Chase", "ATM - Wells Fargo"],
    "Transfer": ["Internal Transfer", "Zelle", "Venmo", "PayPal"],
    "Salary": ["Employer Payroll", "Direct Deposit"],
    "Investment": ["Fidelity", "Vanguard", "Charles Schwab"],
}


class SyntheticDataGenerator:
    def __init__(self, seed: Optional[int] = None):
        """Initialize generator with optional seed for reproducibility"""
        if seed:
            Faker.seed(seed)
            random.seed(seed)

        self.fake = Faker()
        self.user_id_counter = 1
        self.account_id_counter = 1
        self.transaction_id_counter = 1

    def generate_users(self, num_users: int = 10000) -> List[Dict]:
        users = []
        
        for _ in range(num_users):
            # Risk Score: 0.0 (low risk) to 1.0 (high risk)
            risk_distribution = random.choices(
                [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
                weights = [20, 25, 20, 15, 10, 5, 3, 1, 1, 1],  # Most users are low risk
            )[0]

            # Create user profile
            user = {
                "user_id": self.user_id_counter,
                "name": self.fake.name(),
                "email": self.fake.email(),
                "phone": self.fake.phone_number(),
                "address": self.fake.address(),
                "city": self.fake.city(),
                "state": self.fake.state(),
                "risk_score": round(risk_distribution, 2)
            }
            users.append(user)
            self.user_id_counter += 1

        return users

    
    def generate_accounts(self, users: List[Dict], accounts_per_user: tuple = (1, 3)) -> List[Dict]:
        """
        Args:
            users: List of user dictionaries
            accounts_per_user: Tuple of (min, max) accounts per user
        
        Returns:
            List of account dictionaries with: account_id, user_id, balance, type
        """
        
        accounts = []
        account_types = ["checking", "savings"]

        for user in users:
            # Each user gets 1-3 accounts (mix of checking and savings)
            num_accounts = random.randint(accounts_per_user[0], accounts_per_user[1])

            for i in range(num_accounts):
                account_type = random.choice(account_types)

                if account_type == "checking":
                    balance = random.choices(
                        [random.uniform(0, 1000),
                        random.uniform(1000, 5000),
                        random.uniform(5000, 10000),
                        random.uniform(10000, 50000)],
                        weights = [10, 40, 35, 15]
                    )[0]
                else:
                    # Savings
                    balance = random.choices(
                        [random.uniform(100, 1000),
                        random.uniform(1000, 5000),
                        random.uniform(5000, 25000),
                        random.uniform(25000, 200000)],
                        weights = [5, 30, 50, 15]
                    )[0]
                
                account = {
                    "account_id": self.account_id_counter,
                    "user_id": user["user_id"],
                    "balance": round(balance, 2),
                    "type": account_type
                }

                accounts.append(account)
                self.account_id_counter += 1

        return accounts

    def generate_transactions(
        self,
        accounts: List[Dict],
        transactions_per_account: tuple = (10, 200),
        start_date: datetime = None,
        end_date: datetime = None
    ) -> List[Dict]:
        """
        Generate transactions for accounts

        Args:
            accounts: List of account dictionaries
            transactions_per_account: Tuple of (min, max) transactions per account
            start_date: Start date for transactions (defaults to 1 year ago)
            end_date: End date for transactions (defaults to today)
        
        Returns:
            List of transaction dictionaries with: transaction_id, account_id, amount, category, merchant, timestamp
        """
        transactions = []
        
        if start_date is None:
            start_date = datetime.now() - timedelta(days=365)
        
        if end_date is None:
            end_date = datetime.now()

        transactions = []

        for account in accounts:
            num_transactions = random.randint(transactions_per_account[0], transactions_per_account[1])

            # Track running balance for each account
            running_balance = account["balance"]
            
            # Generate transactions dates (more recent = more transactions)
            transaction_dates = sorted([
                self.fake.date_time_between(start_date, end_date)
                for _ in range(num_transactions)
            ])

            for trans_date in transaction_dates:
                category = random.choice(TRANSACTION_CATEGORIES)
                merchant = random.choice(MERCHANT_BY_CATEGORY.get(category, ["Generic Merchant"]))

                # Amount based on category
                if category in ["Salary", "Investment"]:
                    # Large positive amounts
                    amount = random.uniform(1000, 10000)
                elif category == "Transfer":
                    # Can be positive or negative
                    amount = random.uniform(-5000, 5000)
                elif category == "ATM Withdrawal":
                    # Negative, typically $20-$500
                    amount = -random.uniform(20, 500)
                elif category in ["Bills & Utilities", "Rent"]:
                    # Negative, typically $50-$500
                    amount = -random.uniform(50, 500)
                elif category in ["Groceries", "Food & Dining"]:
                    # Negative, typically $10-$200
                    amount = -random.uniform(10, 200)
                else:
                    # Other categories: $5-$500
                    amount = random.uniform(-500, 500)
                    if random.random() > 0.3:  # 70% are negative (spending)
                        amount = -abs(amount)

                if running_balance + amount < -1000.0:
                    amount = -(running_balance + 1000)  # Adjust to prevent overdraft

                running_balance += amount
                amount = round(amount, 2)

                transaction = {
                    "transaction_id": self.transaction_id_counter,
                    "account_id": account["account_id"],
                    "amount": amount,
                    "category": category,
                    "merchant": merchant,
                    "timestamp": trans_date.isoformat(),
                    "running_balance": round(running_balance, 2)
                }

                transactions.append(transaction)
                self.transaction_id_counter += 1

        return transactions

    def save_to_csv(self, data: List[Dict], filename: str):
        if not data:
            return
        
        with open(filename, 'w', newline = '', encoding = 'utf-8') as csvfile:
            fieldnames = data[0].keys()
            writer = csv.DictWriter(csvfile, fieldnames = fieldnames)
            writer.writeheader()
            writer.writerows(data)
        
        print(f"Saved {len(data)} records to {filename}")

    def generate_all(
        self,
        num_users: int = 10000,
        save_to_files: bool = True,
        output_dir: str = 'data/synthetic'
    ) -> tuple:
        """
        Generate all data and save to CSV files

        Args:
            num_users: Number of users to generate
            save_to_files: Whether to save data to CSV files
            output_dir: Directory to save CSV files
        
        Returns:
            Tuple of (users, accounts, transactions)
        """

        print (f"Generating {num_users} users...")
        users = self.generate_users(num_users)

        print(f"Generating accounts for {len(users)} users...")
        accounts = self.generate_accounts(users)
        
        print(f"Generating transactions for {len(accounts)} accounts...")
        transactions = self.generate_transactions(accounts)

        if save_to_files:
            import os
            os.makedirs(output_dir, exist_ok = True)

            self.save_to_csv(users, os.path.join(output_dir, "users.csv"))
            self.save_to_csv(accounts, os.path.join(output_dir, "accounts.csv"))
            self.save_to_csv(transactions, os.path.join(output_dir, "transactions.csv"))

        print(f"\nGeneration complete!")
        print(f"  Users: {len(users)}")
        print(f"  Accounts: {len(accounts)}")
        print(f"  Transactions: {len(transactions)}")

        return users, accounts, transactions

def main():
    import argparse
    parser = argparse.ArgumentParser(description = "Synthetic Data Generation for Vault Digital Bank")
    parser.add_argument("--users", type = int, default = 10000, help = "Number of users to generate")
    parser.add_argument("--seed", type = int, default = 53, help = "Random seed for reproducibility")
    parser.add_argument("--output_dir", type = str, default = "data/synthetic", help = "Output directory")

    args = parser.parse_args()

    generator = SyntheticDataGenerator(args.seed)
    users, accounts, transactions = generator.generate_all(
        num_users = args.users,
        output_dir=args.output_dir
    )

    return users, accounts, transactions


if __name__ == "__main__":
    main()