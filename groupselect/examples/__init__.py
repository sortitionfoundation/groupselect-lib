from pathlib import Path

try:
    import pandas as pd

    HAS_PANDAS: bool = True
except ImportError:
    pd = None
    HAS_PANDAS: bool = False


DATA_DIR = Path(__file__).parent / "data"


if HAS_PANDAS:
    example_data_np = {}
    example_data_pd = {}
    for file in DATA_DIR.glob("*.csv"):
        basename = file.stem
        example_data_pd[basename] = pd.read_csv(file)
        example_data_pd[basename].set_index(
            "ID" if "ID" in example_data_pd[basename] else "name",
            inplace=True,
        )
        example_data_np[basename] = (
            example_data_pd[basename]
            .astype("category")
            .apply(lambda col: col.cat.codes)
            .to_numpy()
        )
else:
    # TODO: Load example data when pandas is not available.
    example_data_np = {}
