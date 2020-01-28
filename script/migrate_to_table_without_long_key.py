"""
Because the previous table schema contained the `long_url` as the sort key,
the table would accept the same `short` with different `long_url`.

That could lead to lookup issues, because I can not safely assume that
there is only one entry per short key. Handling short key in the app is
possible but does not prevent the entry duplication in a concurrency safe
fashion. Meaning, if I handle the prevention of short key duplication on the
app level, then I lookup all the existing short keys and try to generate one
that does not exist. I would then write the item with the generated short key.
In the time between the lookup and the write, another process could write the
key that I had selected. This is unlikely, but generally possible. Preventing
key duplication on the database level is a much more stable solution.

To allow the prevention of duplicate short keys, I need to be sure that each
short key really only exists once. This is only possible when I have only one
hash key. If I also define the long_url as the sort key, the database will not
raise an issue, because it generates the primary key from the combination
of the hash and the sort key. This would allow the same short (hash) key to
exist with different `long_url` (sort) keys.

The purpose of this script is to migrate the existing data from the table with
two keys (hash and sort) to a new table with only one key (hash).
"""

from boto3.dynamodb.conditions import Attr

from short.db import DynamoTable


# First, I copy the existing data to a new table with a different name (intermediate).
# original_table_connection = DynamoTable(with_range_key=True)
# original_response = original_table_connection.table.scan()
# original_items = original_response["Items"]

intermediate_table_connection = DynamoTable(
    table_name="intermediate",
    with_range_key=True,
)
# for item in original_items:
#     print(f"Writing item to intermediate table: {item}")
#     intermediate_table_connection.table.put_item(
#         Item=item,
#         ConditionExpression=Attr("short").not_exists(),
#     )

# Then I delete the original table with the two keys.
# original_table_connection.table.delete()

# Grab the data from the intermediate table
intermediate_response = intermediate_table_connection.table.scan()
intermediate_items = intermediate_response["Items"]


# Then I generate a new table with the original name, this time only with one
# key. Then I copy the data from the intermediate table to the new table with
# the correct format.
fixed_table_connection = DynamoTable()
for item in intermediate_items:
    print(f"Writing item to fixed table: {item}")
    fixed_table_connection.table.put_item(
        Item=item,
        ConditionExpression=Attr("short").not_exists(),
    )


# Then delete the intermediate table. This will be done manually to avoid loss of data




