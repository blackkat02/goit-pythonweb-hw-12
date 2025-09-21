import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.database.models import ContactsModel
from src.repository.contacts import ContactRepository
from src.schemas.contacts import ContactCreate, ContactUpdate
from datetime import date, timedelta
from typing import List, Optional

# Mock objects to simulate the database session and contact data
@pytest.fixture
def mock_session():
    return AsyncMock()

@pytest.fixture
def contact_data():
    return {
        "id": 1,
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe@example.com",
        "phone_number": "1234567890",
        "birthday": date(1990, 5, 15),
        "other_info": "Some info",
        "user_id": 1
    }

# Unit tests for the ContactRepository class
@pytest.mark.asyncio
async def test_create_contact(mock_session, contact_data):
    """Test the create_contact method."""
    repo = ContactRepository(mock_session)
    contact_create = ContactCreate(**contact_data)
    
    mock_session.add = MagicMock()
    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock()
    
    expected_contact = ContactsModel(**contact_data)
    
    new_contact = await repo.create_contact(contact_create, contact_data["user_id"])
    
    mock_session.add.assert_called_once()
    mock_session.commit.assert_awaited_once()
    mock_session.refresh.assert_awaited_once()
    
    assert new_contact.first_name == expected_contact.first_name
    assert new_contact.email == expected_contact.email
    assert new_contact.user_id == expected_contact.user_id

@pytest.mark.asyncio
async def test_get_contacts(mock_session, contact_data):
    """Test the get_contacts method."""
    repo = ContactRepository(mock_session)
    
    mock_contacts = [ContactsModel(**contact_data)]
    
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = mock_contacts
    mock_session.execute.return_value = mock_result
    
    contacts = await repo.get_contacts(user_id=1, skip=0, limit=10)
    
    mock_session.execute.assert_awaited_once()
    assert contacts == mock_contacts

@pytest.mark.asyncio
async def test_get_contact_by_id_found(mock_session, contact_data):
    """Test get_contact_by_id when the contact is found."""
    repo = ContactRepository(mock_session)
    mock_contact = ContactsModel(**contact_data)
    
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = mock_contact
    mock_session.execute.return_value = mock_result
    
    contact = await repo.get_contact_by_id(contact_id=1, user_id=1)
    
    assert contact == mock_contact
    assert contact.first_name == "John"

@pytest.mark.asyncio
async def test_get_contact_by_id_not_found(mock_session):
    """Test get_contact_by_id when the contact is not found."""
    repo = ContactRepository(mock_session)
    
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = None
    mock_session.execute.return_value = mock_result
    
    contact = await repo.get_contact_by_id(contact_id=999, user_id=1)
    
    assert contact is None

@pytest.mark.asyncio
async def test_update_contact(mock_session, contact_data):
    """Test the update_contact method."""
    repo = ContactRepository(mock_session)
    
    existing_contact = ContactsModel(**contact_data)
    update_data = ContactUpdate(first_name="Jane", email="jane.doe@example.com")
    
    mock_session.get.return_value = existing_contact
    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock()
    
    updated_contact = await repo.update_contact(contact_id=1, body=update_data, user_id=1)
    
    mock_session.commit.assert_awaited_once()
    mock_session.refresh.assert_awaited_once()
    assert updated_contact.first_name == "Jane"
    assert updated_contact.email == "jane.doe@example.com"
    assert updated_contact.last_name == "Doe"

@pytest.mark.asyncio
async def test_update_contact_not_found(mock_session, contact_data):
    """Test update_contact when the contact is not found."""
    repo = ContactRepository(mock_session)
    
    mock_session.get.return_value = None
    update_data = ContactUpdate(**contact_data)
    
    updated_contact = await repo.update_contact(contact_id=999, body=update_data, user_id=1)
    
    mock_session.get.assert_awaited_once()
    assert updated_contact is None
    mock_session.commit.assert_not_awaited()

@pytest.mark.asyncio
async def test_delete_contact(mock_session, contact_data):
    """Test the delete_contact method."""
    repo = ContactRepository(mock_session)
    
    existing_contact = ContactsModel(**contact_data)
    
    mock_session.get.return_value = existing_contact
    mock_session.delete = AsyncMock()
    mock_session.commit = AsyncMock()
    
    deleted_contact = await repo.delete_contact(contact_id=1, user_id=1)
    
    mock_session.get.assert_awaited_once()
    mock_session.delete.assert_awaited_once()
    mock_session.commit.assert_awaited_once()
    assert deleted_contact == existing_contact

@pytest.mark.asyncio
async def test_delete_contact_not_found(mock_session):
    """Test delete_contact when the contact is not found."""
    repo = ContactRepository(mock_session)
    
    mock_session.get.return_value = None
    
    deleted_contact = await repo.delete_contact(contact_id=999, user_id=1)
    
    mock_session.get.assert_awaited_once()
    assert deleted_contact is None
    mock_session.delete.assert_not_awaited()

@pytest.mark.asyncio
async def test_search_contacts_repo(mock_session, contact_data):
    """Test the search_contacts_repo method."""
    repo = ContactRepository(mock_session)
    
    mock_contacts = [ContactsModel(**contact_data)]
    
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = mock_contacts
    mock_session.execute.return_value = mock_result

    filters = {"first_name": "john"}
    found_contacts = await repo.search_contacts_repo(filters, user_id=1)
    
    assert found_contacts == mock_contacts
    assert len(found_contacts) == 1
    assert found_contacts[0].first_name == "John"

@pytest.mark.asyncio
@patch('src.repository.contacts.date')
async def test_get_contacts_upcoming_birthdays_within_month(mock_date, mock_session):
    """Test upcoming birthdays within the same month."""
    repo = ContactRepository(mock_session)
    
    mock_today = date(2025, 5, 10)
    mock_date.today.return_value = mock_today

    mock_contacts = [
        ContactsModel(birthday=date(1995, 5, 15), user_id=1),
        ContactsModel(birthday=date(2000, 5, 17), user_id=1),
    ]
    
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = mock_contacts
    mock_session.execute.return_value = mock_result
    
    contacts = await repo.get_contacts_upcoming_birthdays(user_id=1)
    
    assert len(contacts) == 2

@pytest.mark.asyncio
@patch('src.repository.contacts.date')
async def test_get_contacts_upcoming_birthdays_across_months(mock_date, mock_session):
    """Test upcoming birthdays that cross a month boundary."""
    repo = ContactRepository(mock_session)
    
    mock_today = date(2025, 12, 30)
    mock_date.today.return_value = mock_today

    mock_contacts = [
        ContactsModel(birthday=date(1995, 12, 31), user_id=1),
        ContactsModel(birthday=date(2000, 1, 3), user_id=1),
    ]

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = mock_contacts
    mock_session.execute.return_value = mock_result
    
    contacts = await repo.get_contacts_upcoming_birthdays(user_id=1)
    
    assert len(contacts) == 2