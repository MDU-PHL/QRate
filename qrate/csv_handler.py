import csv

def read_csv(file_path):
    """Read CSV file into a list of dictionaries.
    
    Args:
        file_path: Path to CSV file
        
    Returns:
        List of dictionaries representing QC data rows
    """
    with open(file_path, 'r', newline='') as f:
        reader = csv.DictReader(f)
        return list(reader)

def write_csv(data, file_path):
    """Write list of dictionaries to CSV file.
    
    Args:
        data: List of dictionaries representing QC data rows
        file_path: Output file path
    """
    if not data:
        return
        
    with open(file_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
