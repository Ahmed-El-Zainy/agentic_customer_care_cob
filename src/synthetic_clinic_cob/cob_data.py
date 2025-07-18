from datetime import datetime, timedelta
from uuid import uuid4
from faker import Faker
import pandas as pd

fake = Faker()

def gen_products_manual() -> pd.DataFrame:
    return pd.DataFrame([
        {'product_id': str(uuid4()), 'product_name': 'Analytics Pro', 
         'description': 'Advanced analytics platform for data-driven insights.', 'category': 'Software'},
        {'product_id': str(uuid4()), 'product_name': 'Security Guard', 
         'description': 'Real-time threat detection and cybersecurity suite.', 'category': 'Cybersecurity'},
        {'product_id': str(uuid4()), 'product_name': 'Health Tracker', 
         'description': 'Wearable device monitoring vital signs continuously.', 'category': 'Hardware'},
        {'product_id': str(uuid4()), 'product_name': 'EduMaster', 
         'description': 'E-learning platform with AI-driven tutoring.', 'category': 'Education'},
        {'product_id': str(uuid4()), 'product_name': 'EcoPack', 
         'description': 'Sustainable packaging solutions for businesses.', 'category': 'Sustainability'}
    ])

def gen_marketing_schedule(team_size: int, days: int, start_hour: int, end_hour: int) -> pd.DataFrame:
    data = []
    start_date = datetime.today()
    marketers = [{'marketer_id': str(uuid4()), 'marketer_name': fake.name()} 
                for _ in range(team_size)]
    
    for m in marketers:
        for day_offset in range(days):
            date = start_date + timedelta(days=day_offset)
            for hour in range(start_hour, end_hour):
                slot = datetime(year=date.year, month=date.month, day=date.day, hour=hour, minute=0)
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
    data = []
    for _ in range(n):
        product = products_df.sample(1).iloc[0]
        data.append({
            'customer_id': str(uuid4()), 'name': fake.name(), 'email': fake.email(),
            'phone': fake.phone_number(), 'signup_date': fake.date_between(start_date='-2y', end_date='today').strftime('%Y-%m-%d'),
            'status': fake.random_element(['active', 'inactive', 'pending']), 
            'product_id': product['product_id']
        })
    return pd.DataFrame(data)