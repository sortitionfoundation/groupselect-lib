import pandas as pd

from groupselect.examples import example_data_pd


# def test_100i_4j_3k_3d_data():
#     df = example_data_pd['100i_4j_3k_3d_data']
#     for fields in ({'age': 'diversify', 'gender': 'diversify'},
#                    {'gender': 'diversify', 'age': 'diversify'},
#                    {'age': 'diversify', 'gender': 'diversify',
#                     'region': 'diversify', 'nation': 'diversify'}):
#         for n_part_per_group in (3 * [6], 4 * [8],):
#             res = df.groupselect.allocate(
#                 fields=fields,
#                 n_part_per_group=n_part_per_group,
#             )
#             with pd.option_context('display.max_rows', None, 'display.max_columns', None):
#                 print(res)


def test_philipps_example_data():
    df = example_data_pd["philipps_example_data"]
    for fields in (  # {'age': 'diversify', 'gender': 'diversify'},
        # {'gender': 'diversify', 'age': 'diversify'},
        # {'age': 'diversify', 'gender': 'diversify',
        # 'region': 'diversify', 'ethnicity': 'diversify',
        # 'education': 'diversify'},
        {
            "age": "diversify",
            "gender": "diversify",
            "photo consent": "cluster",
        },
    ):
        for n_part_per_group in (
            3 * [6],
            4 * [8],
        ):
            res = df.groupselect.allocate(
                fields=fields,
                n_part_per_group=n_part_per_group,
            )
            with pd.option_context(
                "display.max_rows", None, "display.max_columns", None
            ):
                print(res)
