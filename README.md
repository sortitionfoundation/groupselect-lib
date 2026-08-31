# Python package groupselect

This package contains a library of basic functions for selecting groups.

This package is used by [groupselect-app](https://github.com/sortitionfoundation/groupselect-app/). This package is based on [numpy](https://numpy.org/) and can be directly interfaced to [pandas](https://pandas.pydata.org/).

## Purpose
This software can be used to divide participants of a deliberative process into smaller groups (e.g. 100 participants into 20 groups of 5 each). The software allows for maximisation of diversity across specified fields (e.g. equal number of men/women per group), "clustering" across specified fields (e.g. put all with the need for translation into one group), maximisation of number of meetings between participants and manual group allocations (e.g. force one person to be in a specific group).

The library is recommended when developing new algorithms. End users, who simply seek to execute the software, are referred to the [GroupSelect App](https://github.com/sortitionfoundation/groupselect-app/), which is a stand-alone desktop application for Windows, Mac, and Linux).

## Authors
The legacy algorithm was developed by P.C. Verpoort in 2020. The DREAM algorithm was developed by J. Barrett and K. Gal in 2024. Some generic wrapping functions were developed by P.C. Verpoort in 2024. The HERMES algorithm was developed by M. Cowie in 2026.

## License
The GroupSelect Library is free software and is made available under an [MIT licence](https://opensource.org/license/mit).
