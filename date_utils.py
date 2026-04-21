import random
from datetime import date, timedelta


def random_date(min_str, max_str):
    min_date = date.fromisoformat(min_str)
    max_date = date.fromisoformat(max_str)
    delta = (max_date - min_date).days
    return min_date + timedelta(days=random.randint(0, delta))
