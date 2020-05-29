import numpy as np
import netCDF4 as nc
import yaml


def make_mohid_statistics(nc_file, output):
    mohid_dict = {"test": 5}
    mohid_output = nc.Dataset(nc_file)

    mohid_dict["minimum beaching hour"] = "%.4g" % np.min(
        np.ma.masked_equal(mohid_output.variables["Beaching_Time"][:], 0)
    )

    mohid_dict["volume beached"] = "%.9g" % np.sum(
        mohid_output.variables["Beaching_Volume"][-1, :]
    )

    count, bins = np.histogram(
        np.ma.compressed(
            np.ma.masked_equal(mohid_output.variables["Beaching_Time"][:], 0)
        ),
        bins=np.arange(0, 168, 12),
    )
    mohid_dict["beaching hour mode"] = "%.4g" % bins[np.argmax(count)]

    del mohid_dict["test"]

    with open(output, "w") as outfile:
        yaml.dump(mohid_dict, outfile, default_flow_style=False)


make_mohid_statistics(
    "/ocean/vdo/MIDOSS/results/winds/Lagrangian_AKNS_crude-3_TP_low-3.nc",
    "/ocean/vdo/MIDOSS/mohid_statisitcs.yaml",
)
