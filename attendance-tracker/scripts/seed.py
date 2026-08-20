"""Seed the database with an admin user, sample people and demo records.

Usage:
    python -m scripts.seed

Credentials created by default:
    admin / admin123  (administrator account)
    rahul / user123   (regular user, linked to person "Rahul Sharma")
"""
import asyncio
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select

from app.config import settings
from app.database import Base, SessionLocal, engine
from app.models import AttendanceRecord, Holiday, Person, Shift, ShiftAssignment, User
from app.security import hash_password

TZ = ZoneInfo(settings.app_timezone)

SAMPLE_PEOPLE = [
    {"full_name": "Rahul Sharma", "email": "rahul.sharma@techcorp.com", "group_name": "Engineering"},
    {"full_name": "Neha Patel", "email": "neha.patel@techcorp.com", "group_name": "Engineering"},
    {"full_name": "Amit Kumar", "email": "amit.kumar@techcorp.com", "group_name": "Engineering"},
    {"full_name": "Sneha Reddy", "email": "sneha.reddy@techcorp.com", "group_name": "Design"},
    {"full_name": "Vikram Singh", "email": "vikram.singh@techcorp.com", "group_name": "Design"},
    {"full_name": "Pooja Gupta", "email": "pooja.gupta@techcorp.com", "group_name": "Marketing"},
    {"full_name": "Sanjay Menon", "email": "sanjay.menon@techcorp.com", "group_name": "Marketing"},
    {"full_name": "Divya Joshi", "email": "divya.joshi@techcorp.com", "group_name": "HR"},
    {"full_name": "Karthik Nair", "email": "karthik.nair@techcorp.com", "group_name": "Finance"},
    {"full_name": "Meera Iyer", "email": "meera.iyer@techcorp.com", "group_name": "Finance"},
]


async def main() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with SessionLocal() as db:
        # --- Admin user ---
        exists = (await db.execute(select(User).where(User.username == "admin"))).scalar_one_or_none()
        if exists is None:
            db.add(
                User(
                    username="admin",
                    email="admin@techcorp.com",
                    full_name="System Administrator",
                    hashed_password=hash_password("admin123"),
                    role="admin",
                )
            )
            print("Created admin / admin123")

        # --- Sample people ---
        person_ids = []
        for p in SAMPLE_PEOPLE:
            exists = (
                await db.execute(select(Person).where(Person.email == p["email"]))
            ).scalar_one_or_none()
            if exists is None:
                person = Person(**p)
                db.add(person)
                await db.flush()
                person_ids.append(person.id)
                print(f"Created person: {p['full_name']}")
            else:
                person_ids.append(exists.id)

        # --- A regular user linked to the first person ---
        exists = (await db.execute(select(User).where(User.username == "rahul"))).scalar_one_or_none()
        if exists is None and person_ids:
            db.add(
                User(
                    username="rahul",
                    email="rahul.sharma@techcorp.com",
                    full_name="Rahul Sharma",
                    hashed_password=hash_password("user123"),
                    role="user",
                    person_id=person_ids[0],
                )
            )
            print("Created user rahul / user123 (linked to Rahul Sharma)")

        await db.commit()

        # --- Demo attendance for the last 14 days ---
        people = list((await db.execute(select(Person))).scalars().all())
        today = date.today()
        created = 0
        import random
        random.seed(42)  # For reproducible results

        for person in people:
            for offset in range(1, 15):
                day = today - timedelta(days=offset)
                if day.weekday() >= 5:  # skip weekends
                    continue
                exists = (
                    await db.execute(
                        select(AttendanceRecord).where(
                            AttendanceRecord.person_id == person.id,
                            AttendanceRecord.date == day,
                        )
                    )
                ).scalar_one_or_none()
                if exists is not None:
                    continue

                base = datetime(day.year, day.month, day.day, tzinfo=TZ)

                # Realistic attendance patterns
                rand_val = random.random()
                if rand_val < 0.08:  # 8% chance of being absent
                    status = "absent"
                    check_in = None
                    check_out = None
                elif rand_val < 0.15:  # 7% chance of half day
                    status = "half_day"
                    check_in = base + timedelta(hours=9, minutes=random.randint(0, 30))
                    check_out = base + timedelta(hours=13, minutes=random.randint(0, 30))
                else:  # 85% chance of present
                    status = "present"
                    # Varied check-in times: 8:30 AM to 9:30 AM
                    check_in = base + timedelta(
                        hours=8,
                        minutes=30 + random.randint(0, 60)
                    )
                    # Check-out between 5:30 PM and 7:00 PM
                    check_out = base + timedelta(
                        hours=17,
                        minutes=30 + random.randint(0, 90)
                    )

                db.add(
                    AttendanceRecord(
                        person_id=person.id,
                        date=day,
                        check_in=check_in,
                        check_out=check_out,
                        status=status,
                    )
                )
                created += 1
        if created:
            await db.commit()
            print(f"Created {created} demo attendance records (past 14 working days)")

        # --- Sample holidays ---
        holidays_data = [
            {"name": "Independence Day", "date": date(today.year, 8, 15), "description": "National holiday"},
            {"name": "Gandhi Jayanti", "date": date(today.year, 10, 2), "description": "National holiday"},
            {"name": "Diwali", "date": date(today.year, 10, 20), "description": "Festival of lights"},
            {"name": "Christmas", "date": date(today.year, 12, 25), "description": "Christmas Day"},
        ]
        for h in holidays_data:
            exists = (await db.execute(select(Holiday).where(Holiday.date == h["date"]))).scalar_one_or_none()
            if exists is None:
                db.add(Holiday(**h))
                print(f"Created holiday: {h['name']}")
        await db.flush()

        # --- Sample shifts ---
        shifts_data = [
            {"name": "Morning Shift", "start_time": datetime.strptime("09:00", "%H:%M").time(), "end_time": datetime.strptime("17:00", "%H:%M").time()},
            {"name": "Evening Shift", "start_time": datetime.strptime("14:00", "%H:%M").time(), "end_time": datetime.strptime("22:00", "%H:%M").time()},
            {"name": "Night Shift", "start_time": datetime.strptime("22:00", "%H:%M").time(), "end_time": datetime.strptime("06:00", "%H:%M").time()},
        ]
        shift_ids = []
        for s in shifts_data:
            exists = (await db.execute(select(Shift).where(Shift.name == s["name"]))).scalar_one_or_none()
            if exists is None:
                shift = Shift(**s)
                db.add(shift)
                await db.flush()
                shift_ids.append(shift.id)
                print(f"Created shift: {s['name']}")
            else:
                shift_ids.append(exists.id)

        # --- Assign first 3 people to Morning Shift ---
        if shift_ids and person_ids:
            for pid in person_ids[:3]:
                exists = (
                    await db.execute(
                        select(ShiftAssignment).where(
                            ShiftAssignment.person_id == pid,
                            ShiftAssignment.start_date == date(today.year, 1, 1),
                        )
                    )
                ).scalar_one_or_none()
                if exists is None:
                    db.add(
                        ShiftAssignment(
                            person_id=pid,
                            shift_id=shift_ids[0],
                            start_date=date(today.year, 1, 1),
                            end_date=date(today.year, 12, 31),
                        )
                    )
                    print(f"Assigned person {pid} to Morning Shift")
        await db.commit()

    await engine.dispose()
    print("Seeding complete.")


if __name__ == "__main__":
    asyncio.run(main())
