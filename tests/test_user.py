from main_orm import User

def test_user_set_id():
    user = User(id=1, name="Paul Grogan")
    assert user.id == 1

def test_user_set_name():
    user = User(id=1, name="Paul Grogan")
    assert user.name == "Paul Grogan"
