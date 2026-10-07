# Data sources and transformations

## Heart Disease

Andras Janosi, William Steinbrunn, Matthias Pfisterer, and Robert Detrano
(1989). Heart Disease. UCI Machine Learning Repository.
https://doi.org/10.24432/C52P4X

Source: https://archive.ics.uci.edu/dataset/45/heart+disease
License: Creative Commons Attribution 4.0 International (CC BY 4.0),
https://creativecommons.org/licenses/by/4.0/ .

The derived `processed/heart.npz` uses four processed site files. It retains
seven predictors, removes records missing those predictors, binarizes disease
status at greater than zero, and reserves 20% of each site for defining common
numeric tertiles. The retained inference rows are 243, 235, 94, and 113.

## Wine Quality

Paulo Cortez, A. Cerdeira, Fernando Almeida, T. Matos, and J. Reis (2009).
Wine Quality. UCI Machine Learning Repository.
https://doi.org/10.24432/C56S3T

Source: https://archive.ics.uci.edu/dataset/186/wine+quality
License: Creative Commons Attribution 4.0 International (CC BY 4.0),
https://creativecommons.org/licenses/by/4.0/ .

The derived `processed/wine.npz` removes exact duplicate full records within
red and white wine separately, binarizes quality at six or higher, and uses
independent 20% design subsets to define common tertiles for 11 predictors.
Inference matrices contain 1,088 red and 3,169 white wine observations.

## American Community Survey

U.S. Census Bureau. 2018 ACS 1-Year Public Use Microdata Sample (person files).
Documentation: https://www.census.gov/programs-surveys/acs/microdata/documentation.2018.html
Original downloads and SHA-256 digests: `sources.json`.

The derived `processed/acs.npz` uses California, Florida, Georgia, New York,
and Texas. Eligibility requires housing-unit membership (RELP < 16), age
25 through 64, positive usual weekly work hours, and observed personal income.
Within a household, the smallest eligible SPORDER is retained. A fixed sample
of 10,000 households per state is split 20%/80% for design and inference.
The outcome is personal income above $50,000. Seven attributes produce 27
common literals. Inference includes 8,000 records per state. The analysis is
unweighted and describes the benchmark records; population estimation would
require the survey design and weights. U.S. Census federal statistical data
are public-use material; attribution to the Census Bureau is retained.

## Benchmark release

The transformations and harmonized source organization were created by
Cemil Emre Yavas and Lei Chen in 2026. Source attribution and the original
CC BY 4.0 terms apply to UCI-derived matrices. The software is MIT licensed.
`processed/*.json` records feature meanings, interval boundaries, source
sizes, outcome definitions, and the common design seed. Infinite interval
endpoints are represented by the strings `-inf` and `inf`.
