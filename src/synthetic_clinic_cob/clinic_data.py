from datetime import datetime, timedelta
from uuid import uuid4
from faker import Faker
import pandas as pd


fake = Faker()
def gen_clinic_schedule(num_clinics: int, doctors_per_clinic: int, days: int, 
                        start_hour: int, end_hour: int) -> pd.DataFrame:
    data = []
    start_date = datetime.today()
    specialties = ['Cardiology', 'Dermatology', 'Pediatrics', 'Orthopedics', 
                  'Neurology', 'Oncology', 'General Practice', 'ENT', 'Ophthalmology']
    
    clinics = [{'clinic_id': str(uuid4()), 'clinic_name': fake.company()} 
              for _ in range(num_clinics)]
    
    for clinic in clinics:
        for _ in range(doctors_per_clinic):
            doctor_id = str(uuid4())
            doctor_name = fake.name()
            specialty = fake.random_element(specialties)
            for day_offset in range(days):
                date = start_date + timedelta(days=day_offset)
                for hour in range(start_hour, end_hour):
                    slot = datetime(year=date.year, month=date.month, day=date.day, hour=hour)
                    booked = fake.boolean(chance_of_getting_true=30)
                    data.append({
                        'clinic_id': clinic['clinic_id'],
                        'clinic_name': clinic['clinic_name'],
                        'doctor_id': doctor_id,
                        'doctor_name': doctor_name,
                        'specialty': specialty,
                        'slot_datetime': slot.strftime('%Y-%m-%d %H:%M:%S'),
                        'available': str(not booked),
                        'appointment_id': str(uuid4()) if booked else None,
                        'patient_name': fake.name() if booked else None,
                        'contact_email': fake.email() if booked else None
                    })


    return pd.DataFrame(data)