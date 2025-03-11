import csv
import random
import pandas as pd

# Sample Kulim addresses, postal codes, and towns
taman = {
    'Taman Selasih': 'Lorong Selasih', 'Taman Mutiara': 'Lorong Mutiara', 'Taman Mahsuri': 'Lorong Mahsuri',
    'Taman Kulim Heights': 'Lorong Kulim Heights', 'Taman Murni': 'Lorong Murni',
    'Taman Seri Mahkota': 'Lorong Seri Mahkota', 'Taman Desa Aman': 'Lorong Desa Aman',
    'Taman Putra': 'Lorong Putra', 'Taman Sawi': 'Lorong Sawi', 'Taman Kucai': 'Lorong Kucai',
    'Taman Bersatu': 'Lorong Bersatu', 'Taman Cengal': 'Lorong Cengal', 'Taman Melur': 'Lorong Melur',
    'Taman Jati': 'Lorong Jati', 'Taman Rambai': 'Lorong Rambai', 'Taman Kenanga': 'Lorong Kenanga',
    'Taman Dahlia': 'Lorong Dahlia', 'Taman Teratai': 'Lorong Teratai', 'Taman Mawar': 'Lorong Mawar',
    'Taman Melati': 'Lorong Melati', 'Taman Anggerik': 'Lorong Anggerik', 'Taman Kemuning': 'Lorong Kemuning',
    'Taman Bakawali': 'Lorong Bakawali', 'Taman Seroja': 'Lorong Seroja', 'Taman Kekwa': 'Lorong Kekwa',
    'Taman Melati Indah': 'Lorong Melati Indah', 'Taman Sri Kulim': 'Lorong Sri Kulim',
    'Taman Kulim Utama': 'Lorong Kulim Utama', 'Taman Kulim Perdana': 'Lorong Kulim Perdana',
    'Taman Kulim Jaya': 'Lorong Kulim Jaya', 'Taman Kulim Maju': 'Lorong Kulim Maju',
    'Taman Kulim Bestari': 'Lorong Kulim Bestari', 'Taman Kulim Ria': 'Lorong Kulim Ria',
    'Taman Kulim Damai': 'Lorong Kulim Damai', 'Taman Kulim Sentosa': 'Lorong Kulim Sentosa',
    'Taman Kulim Makmur': 'Lorong Kulim Makmur', 'Taman Kulim Sejahtera': 'Lorong Kulim Sejahtera',
    'Taman Kulim Mesra': 'Lorong Kulim Mesra', 'Taman Kulim Bahagia': 'Lorong Kulim Bahagia',
    'Taman Kulim Aman': 'Lorong Kulim Aman', 'Taman Kulim Permai': 'Lorong Kulim Permai',
    'Taman Kulim Harmoni': 'Lorong Kulim Harmoni', 'Taman Kulim Ceria': 'Lorong Kulim Ceria',
}

kulim_postcodes = {
    "09000": "Kulim", "09010": "Lunas", "09050": "Sungai Kob", "09080": "Padang Serai", "09090": "Kulim HiTech"
}

# Generate random addresses for 100 rows
random_addresses = [
    {
        "id": i,  # Add an ID column for proper merging
        "alamat_rumah": f"No. {random.randint(1, 150)}, {taman[taman_name]} {random.randint(1, 20)}, {taman_name}",
        "poskod": (postcode := random.choice(list(kulim_postcodes.keys()))),  # Pick a postcode and store it
        "bandar": kulim_postcodes[postcode],  # Get the corresponding town
        "daerah": "Kulim"
    }
    for i in range(100)
    if (taman_name := random.choice(list(taman.keys())))  # Select a Taman
]

df_alamat = pd.DataFrame(random_addresses)

# Read the CSV file
guru_details = pd.read_csv('Data/Guru-sample.csv')
sekolah = pd.read_csv('Data/sekolah.csv')
sekolah['poskod_sekolah'] = sekolah['poskod_sekolah'].astype(str).str.zfill(5)
list_sekolah = sekolah['Nama_Sekolah'].unique().tolist()

# Add an ID column to match with df_alamat
guru_details['id'] = guru_details.index

# Merge DataFrames using 'id'
df_guru_details = pd.merge(guru_details, df_alamat, on='id', how='left')

# Assign a random school from 'list_sekolah' if not empty, otherwise "Tiada Data"
df_guru_details['nama_sekolah'] = df_guru_details.apply(lambda x: random.choice(list_sekolah) if list_sekolah else "Tiada Data", axis=1)

# Merge with sekolah.csv to get school poskod & bandar
df_guru_details = df_guru_details.merge(
    sekolah[['Nama_Sekolah', 'poskod_sekolah', 'bandar_sekolah', 'alamat_sekolah', 'email_sekolah']],
    left_on='nama_sekolah', right_on='Nama_Sekolah',
    how='left'
)

# Drop the duplicate 'Nama_Sekolah' column after merging
df_guru_details.drop(columns=['Nama_Sekolah'], inplace=True)


# Display the first 5 rows
print(df_guru_details.head())

# Save to CSV
df_guru_details.to_csv('Data/guru_details.csv', index=False, quoting=csv.QUOTE_STRINGS)
