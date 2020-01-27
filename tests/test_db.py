import pytest


class MockLimit(object):
    """
    Class to provide mocked returns for a max number of times.

    During instantiation, define the `mockreturn`. This is the value
    that will be initially returned by `mocking_func`.
    On every of these returns, the `mock_count` of the instance is
    increased. If the `mock_count` reaches the `mock_count_max` limit,
    then `mocking_func` will not return `mockreturn` anymore.
    Rather, the return value of `mocking_func` is defined by the return
    value of the `fallback_func`.

    Say you wish to mock the return of function `foo.bar` to be `baz`
    for 3 times. After you received the mock value 3 times, you wish
    to actually get the original functionality of `foo` back, then you
    set the `fallback_func` to be `foo.bar`.

    To get the above example, you would set it up like so:
    ```
    import foo
    foo_bar_mocker = MockLimit("baz", 3, foo.bar)
    monkeypatch.setattr(foo, "bar", foo_bar_mocker.mocking_func)
    ```

    """

    def __init__(self, mockreturn, mock_count_max, fallback_func):
        self.mock_count_max = mock_count_max
        self.mock_count = 0
        self.mockreturn = mockreturn
        self.fallback_func = fallback_func

    def mocking_func(self, *args, **kwargs):
        """
        Return mockreturn or fallback_func return depending on count.

        """

        if self.mock_count < self.mock_count_max:
            self.mock_count += 1
            return self.mockreturn
        return self.fallback_func()


@pytest.fixture
def table_connection():
    from short.db import DynamoTable
    table_connection_for_testing = DynamoTable("testing", local=True)

    yield table_connection_for_testing

    table_connection_for_testing.table.delete()


@pytest.fixture
def mock_random_string(monkeypatch):
    # Define the replacement function
    def mockreturn(*args, **kwargs):
        return "m0ck"
    # Replace the function
    from short import db
    monkeypatch.setattr(db, "random_string", mockreturn)


@pytest.fixture
def example_entry(table_connection):
    return table_connection.save_long_url("http://example.com")


class TestSaveMethod(object):
    def test_returns_dict(self, table_connection):
        response = table_connection.save_long_url("http://example.com")

        assert isinstance(response, dict)

    def test_returned_dict_keys(self, table_connection):
        response = table_connection.save_long_url("http://example.com")

        assert "short" in response.keys()
        assert "long_url" in response.keys()

    def test_value_of_short(self, table_connection):
        response = table_connection.save_long_url("http://example.com")

        short_value = response["short"]
        assert isinstance(short_value, str)
        assert len(short_value) == 4

    def test_saving_same_long_twice_yields_same_short(self, table_connection):
        response_1 = table_connection.save_long_url("http://example.com")
        short_1 = response_1["short"]

        response_2 = table_connection.save_long_url("http://example.com")
        short_2 = response_2["short"]

        assert short_1 == short_2

    def test_saving_different_long_leads_to_different_shorts(
        self,
        table_connection,
    ):
        response_1 = table_connection.save_long_url("http://example.com")
        short_1 = response_1["short"]

        response_2 = table_connection.save_long_url("http://otherexample.com")
        short_2 = response_2["short"]

        assert short_1 != short_2

    def test_trailing_newlines_are_stipped_from_long_url(
        self,
        table_connection,
    ):
        response = table_connection.save_long_url("http://example.com\n")

        assert response["long_url"] == "http://example.com"

    def test_mocking_the_random_short_to_a_fixed_value(
        self,
        table_connection,
        mock_random_string,
    ):
        """Test that mocking of random short works."""
        response = table_connection.save_long_url("http://example.com")

        assert response["short"] == "m0ck"
        assert response["long_url"] == "http://example.com"

    def test_mocking_random_string_2_of_3_times(
        self,
        table_connection,
        monkeypatch,
    ):
        from short import db
        random_mocker = MockLimit("m0ck", 2, db.random_string)
        monkeypatch.setattr(db, "random_string", random_mocker.mocking_func)

        response1 = table_connection.save_long_url("http://example1.com")
        response2 = table_connection.save_long_url("http://example2.com")
        response3 = table_connection.save_long_url("http://example3.com")

        assert response1["short"] == "m0ck"
        assert response2["short"] == "m0ck"
        assert response3["short"] != "m0ck"


class TestGetShortOfLongMethod(object):
    def test_finds_short_for_given_long_url(
        self,
        table_connection,
        example_entry,
    ):
        short = table_connection.get_short_of_long("http://example.com")

        assert short == example_entry["short"]


class TestGetLongFromShortMethod(object):
    def test_finds_saved_long_from_given_short(
        self,
        table_connection,
        example_entry,
    ):
        long_url = table_connection.get_long_from_short(example_entry["short"])

        assert long_url == example_entry["long_url"]
