#!/usr/bin/env python3
import datetime
import json

def generate_schedule():
    """Generate class schedule grid for Winter 2026"""
    start_date = datetime.date(2026, 1, 7)
    end_date = datetime.date(2026, 4, 15)
    
    holidays = [
        datetime.date(2026, 1, 19),  # MLK Day
        datetime.date(2026, 2, 16),  # Presidents' Day
        datetime.date(2026, 3, 20)   # No Classes Day
    ]
    
    special_days = {
        datetime.date(2026, 2, 17): "Monday schedule (no Tuesday classes)"
    }
    
    schedule = []
    current_date = start_date
    week_num = 1
    week_schedule = {"week": week_num, "mon": "", "tue": "", "wed": "", "thu": "", "fri": "", "notes": ""}
    
    while current_date <= end_date:
        if current_date.weekday() in [5, 6]:  # Skip weekends
            current_date += datetime.timedelta(days=1)
            continue
        
        date_str = current_date.strftime("%b %d")
        weekday = current_date.weekday()
        
        # Check for holidays
        if current_date in holidays:
            date_str += " (No Class)"
            note = "Holiday"
        elif current_date in special_days:
            note = special_days[current_date]
        else:
            note = ""
        
        # Add to week schedule
        if weekday == 0: week_schedule["mon"] = date_str
        if weekday == 1: week_schedule["tue"] = date_str
        if weekday == 2: week_schedule["wed"] = date_str
        if weekday == 3: week_schedule["thu"] = date_str
        if weekday == 4: week_schedule["fri"] = date_str
        
        # Add note
        if note:
            if week_schedule["notes"]:
                week_schedule["notes"] += "; " + note
            else:
                week_schedule["notes"] = note
        
        current_date += datetime.timedelta(days=1)
        
        # Start new week after Friday
        if weekday == 4 and current_date <= end_date:
            schedule.append(week_schedule)
            week_num += 1
            week_schedule = {"week": week_num, "mon": "", "tue": "", "wed": "", "thu": "", "fri": "", "notes": ""}
    
    # Add final week
    if any(week_schedule.values()):
        schedule.append(week_schedule)
    
    return schedule

def main():
    """Generate and save schedule grid"""
    print("Generating MATH 451 Winter 2026 schedule grid...")
    schedule = generate_schedule()
    
    # Save to JSON file
    with open("schedule_grid.json", "w") as f:
        json.dump(schedule, f, indent=2)
    
    print(f"Generated {len(schedule)} weeks of schedule data")
    print("Schedule grid saved to schedule_grid.json")
    
    # Print summary
    total_classes = 0
    for week in schedule:
        week_classes = sum(1 for day in ['mon', 'tue', 'wed', 'thu', 'fri'] if week[day] and '(No Class)' not in week[day])
        total_classes += week_classes
    
    print(f"Total class meetings: {total_classes}")
    
    return schedule

if __name__ == "__main__":
    main()
