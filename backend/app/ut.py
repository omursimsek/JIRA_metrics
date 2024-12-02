import unittest as ut
from datetime import datetime, timedelta

# Constants for the tests
TURKISH_HOLIDAYS = ["2024-01-01", "2024-04-23", "2024-05-01"]
WORKING_HOURS_START = 7  # Start of the working day
WORKING_HOURS_END = 16  # End of the working day
LUNCH_START = 10  # Lunch break starts
LUNCH_END = 11  # Lunch break ends

# The function to be tested
def calculate_working_hours(start_time, end_time):
    if not start_time or not end_time:
        return 0

    holidays = [datetime.strptime(date, "%Y-%m-%d").date() for date in TURKISH_HOLIDAYS]
    total_hours = 0
    current = start_time
    print(f'start_time: {start_time}')
    print(f'end_time: {end_time}')
    print(f'current: {current}')
    print(f'current < end_time {current < end_time}')
    while current < end_time:
        if current.weekday() < 5 and current.date() not in holidays:  # Weekday and not a holiday
            start_of_day = current.replace(hour=WORKING_HOURS_START, minute=0, second=0, microsecond=0)
            end_of_day = current.replace(hour=WORKING_HOURS_END, minute=0, second=0, microsecond=0)
            lunch_start = current.replace(hour=LUNCH_START, minute=0, second=0, microsecond=0)
            lunch_end = current.replace(hour=LUNCH_END, minute=0, second=0, microsecond=0)

            print(f'current < start_of_day {current < start_of_day}')
            if current < start_of_day:
                current = start_of_day

            print(f'current < end_of_day {current >= end_of_day}')
            if current >= end_of_day:
                current += timedelta(days=1)
                current = current.replace(hour=WORKING_HOURS_START, minute=0, second=0, microsecond=0)
                continue

            effective_end_time = min(end_of_day, end_time)

            print(f'current < lunch_start {current < lunch_start}')
            if current < lunch_start:  # Before lunch
                total_hours += (min(lunch_start, effective_end_time) - current).total_seconds() / 3600.0
                current = min(effective_end_time, lunch_end)  # Skip to after lunch if necessary

            if current >= lunch_end:  # After lunch
                total_hours += (effective_end_time - max(current, lunch_end)).total_seconds() / 3600.0

        current += timedelta(days=1)
        current = current.replace(hour=WORKING_HOURS_START, minute=0, second=0, microsecond=0)
        print(f'total hours: {total_hours}');
        print(f'current: {current}')
        print(f'end_time: {end_time}')

    return total_hours

# Unit test class
class TestCalculateWorkingHours(ut.TestCase):
    def test_same_day_full_day(self):
        start_time = datetime(2024, 10, 30, 7, 31)
        end_time = datetime(2024, 10, 30, 8, 2)
        print(calculate_working_hours(start_time, end_time))
        self.assertAlmostEqual(calculate_working_hours(start_time, end_time), 8.0)

    # def test_same_day_partial_day(self):
    #     start_time = datetime(2024, 11, 1, 10, 0)
    #     end_time = datetime(2024, 11, 1, 15, 0)
    #     self.assertAlmostEqual(calculate_working_hours(start_time, end_time), 4.0)

    # def test_lunch_break_excluded(self):
    #     start_time = datetime(2024, 11, 1, 11, 0)
    #     end_time = datetime(2024, 11, 1, 14, 0)
    #     self.assertAlmostEqual(calculate_working_hours(start_time, end_time), 2.0)

    # def test_weekend_excluded(self):
    #     start_time = datetime(2024, 11, 2, 9, 0)  # Saturday
    #     end_time = datetime(2024, 11, 2, 18, 0)
    #     self.assertEqual(calculate_working_hours(start_time, end_time), 0)

    # def test_holiday_excluded(self):
    #     start_time = datetime(2024, 4, 23, 9, 0)  # Holiday
    #     end_time = datetime(2024, 4, 23, 18, 0)
    #     self.assertEqual(calculate_working_hours(start_time, end_time), 0)

    # def test_multiple_days(self):
    #     start_time = datetime(2024, 11, 1, 15, 0)  # Friday
    #     end_time = datetime(2024, 11, 4, 12, 0)  # Monday
    #     self.assertAlmostEqual(calculate_working_hours(start_time, end_time), 9.0)

    # def test_cross_lunch_period(self):
    #     start_time = datetime(2024, 11, 1, 11, 30)
    #     end_time = datetime(2024, 11, 1, 13, 30)
    #     self.assertAlmostEqual(calculate_working_hours(start_time, end_time), 1.0)

if __name__ == "__main__":
    ut.main()
