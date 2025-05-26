import csv


def read_csv_data(csv_file):
    """
    Read data from the CSV file
    """
    data = []
    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    
    print(f"Read {len(data)} records from {csv_file}")
    return data