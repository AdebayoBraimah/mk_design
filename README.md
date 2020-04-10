# mk_design

Handy tool to quickly and efficient create design matrices that are compatible with `FSL` style for group stats.

```
usage: mk_design.py [-h] -i FILE -o PREFIX [--rm-list STR] [--ret-list STR]
                    [--ret-cols STR] [--keep-nan] [--sep SEP]

Creates FSL compatible design matrices (as text files). Writes corresponding
inclusion and exclusion lists.

optional arguments:
  -h, --help            show this help message and exit

Required Argument(s):
  -i FILE, --in FILE    Input TSV of CSV group design file with headers. Input
                        file must have a subject ID column as the first column
                        header.
  -o PREFIX, --out PREFIX
                        Output prefix

Optional Argument(s):
  --rm-list STR         File or comma separated strings of subjects to remove.
  --ret-list STR        File or comma separated strings of subjects to retain.
  --ret-cols STR        File or comma separated strings of column indices to
                        retain in design matrix (e.g. "1,2,3", index count
                        starts at 0).

Expert Option(s):
  --keep-nan            Keeps subjects with NaNs (missing data) from the
                        specified covariates (from '--ret-cols') in the design
                        matrix [default: False].
  --sep SEP             Separator string to use, valid separators/delimitors
                        include: tabs, commas, or spaces.
 ```
