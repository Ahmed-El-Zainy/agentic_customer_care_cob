from datetime import datetime, timedelta
from uuid import uuid4
from faker import Faker
import pandas as pd
import sys
import os

# Add the parent directories to the path for custom logger import
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(os.path.dirname(SCRIPT_DIR)))

# # Try to import custom logger, fall back to standard logging if not available
try:
    from logger.custom_logger import CustomLoggerTracker
    logger_tracker = CustomLoggerTracker()
    logger = logger_tracker.get_logger("clinic_data")
    logger.info("Logger start at synthetic_data (COB Company Data)")

    # Except if fail to import custom logger we can add the basic logger
except ImportError:
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("clinic_data")
    logger.info("Using standard logger - custom logger not available")

fake = Faker()


def gen_products_manual() -> pd.DataFrame:
    """Generate predefined COB products with detailed descriptions and outputs."""
    return pd.DataFrame([
        {
            'product_id': str(uuid4()), 
            'product_name': 'Authorizations', 
            'description': 'COB Solution streamlines insurance authorizations so you can focus on delivering quality care. Verify patient info fast through secure chat, while our team collects service details and submits timely requests. Stay connected, track approvals in real time, and get daily tips to boost your revenue and efficiency—all from one easy platform.', 
            "output": """   1. Verify Patient Info through secure chat
                            2. Service Details Collection via shared EMR or provider inputs
                            3. Submit Authorization Requests on time to avoid delays
                            4. Stay Connected through live chat for real-time updates
                            5. Follow Up on approvals to reduce delays
                            6. Track Approvals through platform or EMR system
                            7. Get Recommendations with daily tips to improve financial performance""",
            'category': 'Software'
        },


        {
            'product_id': str(uuid4()), 
            'product_name': 'Benefits Verification', 
            'description': 'COB Solution makes benefits verification easy and accurate, helping providers maximize reimbursement and reduce billing errors. Collect patient demographics and insurance info through HIPAA-compliant chat, snap and verify ID and cards for fast confirmation, and document coverage details. Stay connected with live chat, share verified info, and get daily insights to boost financial results.', 
            "output": """   1. Collect Info via HIPAA-compliant chat
                            2. Snap and Verify patient ID and insurance card
                            3. Document Coverage including deductibles and patient responsibilities
                            4. Stay Connected through live chat support
                            5. Share Details with providers for service planning
                            6. Get Insights with daily financial performance tips""",
            'category': 'Software',
        },

        {
            'product_id': str(uuid4()), 
            'product_name': 'Medical Auditing', 
            'description': '''COB Solution simplifies medical auditing for physical therapists, ensuring compliance and maximizing reimbursement. We gather billing data, review documentation for accuracy, and audit claims for discrepancies. Receive actionable recommendations and detailed reports to optimize your practice's financial performance and security, helping you focus on patient care''', 
            "output": """   1. Data collection of billing records claims and payment details
                            2. Documentation review of SOAP notes ICD-10 and CPT coding
                            3. Claim review to find undercoding overcoding or missing info
                            4. Error Identification that affects revenue or compliance
                            5. Actionable Recommendations to improve accuracy and efficiency
                            6. Comprehensive Reporting with insights to boost financial performance""",
            'category': 'Software'
        },

        {
            'product_id': str(uuid4()), 
            'product_name': 'Medical Billing and Denial Management', 
            'description': 'Our comprehensive Medical Auditing and Documentation Service, where precision meets compliance ensures that your healthcare practice operates seamlessly, adhering to the highest standards in documentation accuracy and regulatory compliance. Our service is meticulously crafted to conduct thorough audits of medical records and documentation practices, facilitating optimal compliance, improved patient care, and financial integrity.', 
            "output": """   1. Information gathering as well as reviewing and verifying patient and provider details
                            2. Claim Generation based on services and codes
                            3. Claim Scrubbing to ensure error-free submissions
                            4. Daily Claims Submission for faster reimbursements
                            5. Posting Insurance Responses on shared platform
                            6. Insurance Response Analysis to detect denials or patterns
                            7. Follow-Up and Collection on denied or underpaid claims
                            8. Payment Posting and resolving Outstanding Balances
                            9. Monthly Reports with claim status payments and key metrics""",
            'category': 'Software'
        }
    ])


def gen_marketing_schedule(team_size: int, days: int, start_hour: int = 9, end_hour: int = 17) -> pd.DataFrame:
    """
    Generate marketing team schedule with availability slots.
    
    Args:
        team_size: Number of marketers
        days: Number of days to generate schedule for
        start_hour: Starting hour for work day (default 9 AM)
        end_hour: Ending hour for work day (default 5 PM)
    """
    data = []
    start_date = datetime.today()
    marketers = [
        {
            'marketer_id': str(uuid4()), 
            'marketer_name': fake.name()
        } 
        for _ in range(team_size)
    ]
    
    for m in marketers:
        for day_offset in range(days):
            date = start_date + timedelta(days=day_offset)
            for hour in range(start_hour, end_hour):
                slot = datetime(
                    year=date.year, 
                    month=date.month, 
                    day=date.day, 
                    hour=hour, 
                    minute=0
                )
                available = fake.boolean(chance_of_getting_true=70)
                data.append({
                    'marketer_id': m['marketer_id'],
                    'marketer_name': m['marketer_name'],
                    'slot_datetime': slot.strftime('%Y-%m-%d %H:%M:%S'),
                    'available': str(available),
                    'appointment_id': None,
                    'customer_id': None
                })
    
    return pd.DataFrame(data)


def gen_cob_customers(n: int, products_df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate COB customer data.
    
    Args:
        n: Number of customers to generate
        products_df: DataFrame containing product information
    """
    data = []
    for _ in range(n):
        product = products_df.sample(1).iloc[0]
        data.append({
            'customer_id': str(uuid4()), 
            'name': fake.name(), 
            'email': fake.email(),
            'phone': fake.phone_number(), 
            'signup_date': fake.date_between(
                start_date='-2y', 
                end_date='today'
            ).strftime('%Y-%m-%d'),
            'status': fake.random_element(['active', 'inactive', 'pending']), 
            'product_id': product['product_id']
        })
    
    return pd.DataFrame(data)


def save_data_to_csv(dataframe: pd.DataFrame, filename: str, output_dir: str = "assets/data") -> None:
    """Save DataFrame to CSV file in specified directory."""
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, filename)
    dataframe.to_csv(filepath, index=False)
    logger.info(f"Data saved to {filepath}")


def main():
    """Main function to generate and save all COB company data."""
    logger.info("Starting COB company data generation...")
    
    # Generate products
    products_df = gen_products_manual()
    logger.info(f"Generated {len(products_df)} products")
    
    # Generate marketing schedule (5 marketers, 30 days)
    marketing_schedule_df = gen_marketing_schedule(team_size=5, days=30)
    logger.info(f"Generated {len(marketing_schedule_df)} marketing schedule slots")
    
    # Generate customers (100 customers)
    customers_df = gen_cob_customers(n=100, products_df=products_df)
    logger.info(f"Generated {len(customers_df)} customers")
    
    # Save all data to CSV files
    save_data_to_csv(products_df, "products.csv")
    save_data_to_csv(marketing_schedule_df, "marketing_schedule.csv")
    save_data_to_csv(customers_df, "customers.csv")
    
    logger.info("COB company data generation completed successfully!")
    
    # Display sample data
    print("\n=== SAMPLE PRODUCTS ===")
    print(products_df[['product_name', 'category']].to_string())
    
    print(f"\n=== MARKETING SCHEDULE SAMPLE ===")
    print(marketing_schedule_df.head(10).to_string())
    
    print(f"\n=== CUSTOMERS SAMPLE ===")
    print(customers_df.head(10)[['name', 'email', 'status']].to_string())


if __name__ == "__main__":
    main()