# Helper function to validate the date of birth
from datetime import date


def validate_birthday(dob: str):
    try:
        dob_date = date.fromisoformat(dob)  # Convert string to date object
    except ValueError:
        return None, "Invalid date format. Please use YYYY-MM-DD."

    # Ensure the date of birth is not today or in the future
    if dob_date >= date.today():
        return None, "Date of birth cannot be today or in the future."

    # Ensure the teacher is at least 1 year old
    if dob_date > date.today().replace(year=date.today().year - 1):  # Check if age > 1 year
        return None, "Age must be greater than 1 year."

    return dob_date, None  # Valid date and no error
