"""Admin-only endpoints for managing people (the tracked entities)."""
import csv
import io

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..deps import require_admin
from ..models import Person
from ..schemas import PersonCreate, PersonOut, PersonUpdate

router = APIRouter(prefix="/api/people", tags=["people"])


async def get_person_or_404(person_id: int, db: AsyncSession) -> Person:
    person = await db.get(Person, person_id)
    if person is None:
        raise HTTPException(status_code=404, detail="Person not found")
    return person


@router.get("", response_model=list[PersonOut])
async def list_people(
    search: str | None = None,
    group: str | None = None,
    include_inactive: bool = False,
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    _: Person = Depends(require_admin),
):
    """List people, optionally filtered by search text or group."""
    query = select(Person).order_by(Person.full_name)
    if search:
        like = f"%{search}%"
        query = query.where(
            or_(Person.full_name.ilike(like), Person.email.ilike(like))
        )
    if group:
        query = query.where(Person.group_name == group)
    if not include_inactive:
        query = query.where(Person.is_active.is_(True))
    query = query.limit(min(limit, 500)).offset(max(offset, 0))
    result = await db.execute(query)
    return list(result.scalars().all())


@router.get("/groups", response_model=list[str])
async def list_groups(db: AsyncSession = Depends(get_db), _: Person = Depends(require_admin)):
    """Distinct group names (departments/classes) for filtering."""
    result = await db.execute(select(Person.group_name).distinct())
    return [g for (g,) in result.all() if g]


@router.post("", response_model=PersonOut, status_code=status.HTTP_201_CREATED)
async def create_person(
    data: PersonCreate,
    db: AsyncSession = Depends(get_db),
    _: Person = Depends(require_admin),
):
    person = Person(**data.model_dump())
    db.add(person)
    await db.commit()
    await db.refresh(person)
    return person


@router.patch("/{person_id}", response_model=PersonOut)
async def update_person(
    person_id: int,
    data: PersonUpdate,
    db: AsyncSession = Depends(get_db),
    _: Person = Depends(require_admin),
):
    person = await get_person_or_404(person_id, db)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(person, field, value)
    await db.commit()
    await db.refresh(person)
    return person


@router.delete("/{person_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_person(
    person_id: int,
    db: AsyncSession = Depends(get_db),
    _: Person = Depends(require_admin),
):
    person = await get_person_or_404(person_id, db)
    await db.delete(person)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=409, detail="Cannot delete: person has attendance records"
        )


@router.post("/import", response_model=dict)
async def import_people_csv(
    file: UploadFile,
    db: AsyncSession = Depends(get_db),
    _: Person = Depends(require_admin),
):
    """Bulk import people from a CSV file.

    Expected columns: full_name, email (optional), group_name (optional)
    """
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="File must be a .csv file")

    content = await file.read()
    text = content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))

    created = 0
    skipped = 0
    errors = []

    for i, row in enumerate(reader, start=2):
        full_name = row.get("full_name", "").strip()
        if not full_name:
            errors.append(f"Row {i}: missing full_name")
            skipped += 1
            continue

        email = row.get("email", "").strip() or None
        group_name = row.get("group_name", "").strip() or None

        # Check for duplicate email
        if email:
            exists = (
                await db.execute(select(Person).where(Person.email == email))
            ).scalar_one_or_none()
            if exists:
                errors.append(f"Row {i}: email '{email}' already exists")
                skipped += 1
                continue

        person = Person(full_name=full_name, email=email, group_name=group_name)
        db.add(person)
        created += 1

    await db.commit()
    return {"created": created, "skipped": skipped, "errors": errors}
