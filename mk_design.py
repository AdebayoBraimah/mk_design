#!/usr/bin/env python3

# Define usage
"""
Applies pre-computed (affine) linear and non-linear transforms to 4D EP (bold) image data in parallel.
Additional options include the ability to resample the image back to its native voxel size and/or native
space dimensions (in the case a native space image is provided).
This script at minimum requires that FSL be installed and added to system path.
Image resampling options required that MIRTK be installed and added to the system path.
Usage:
  reg4D.py [options | expert options] [required arguments]
Required arguments
    -i,--in INPUT       Input 4D file
    -o,--out PREFIX     Output prefix for transformed 4D file
    -r,--ref IMAGE      Reference image that corresponds to the transform(s) or
                        target space to be resampled/interpolated to
Options:
    --ref-tar IMAGE     Reference (target) image to resample to post-transform
                        (usually the native space image) - behaves best with
                        linear transfroms.
    -TR,--TR FLOAT      Repetition time (TR) of the input 4D EPI. If this value is not
                        specified, it will then be read from the nifti header [default: infer]
    -n,--num-jobs INT   Number of jobs to run in parallel. Default behavior is to use the
                        max number of cores available [default: infer]
Expert Options:
    -d,--dim CMD        (Command) Dimension to split and concatenate along the 4D image
                        (valid options: "-x", "-y", "-z", "t", "-tr") [default: -tr]
    -w,--warp IMAGE     FSL-style non-linear warp field file to reference image
    --warp-app CMD      (Command) Warp field treatment and application
                        (valid options: "relative", "absolute") [default: "relative"]
    --premat MAT        FSL-style pre-transform linear transformation matrix
    --postmat MAT       FSL-style post-transform linear transformation matrix
    --resamp-vox        Resample voxel-size to reference target image (if '--ref-tar' option is not
                        used then image voxel-size is resampled back to native voxel-size)
    --resamp-dim        Resample image dimension to reference target image (if '--ref-tar' option is not
                        used then image dimensions are resampled back to native dimensions)
    -m,--mask IMAGE     Binary mask image file in reference space to use for applying transform(s)
    --interp CMD        Interpolation method, options include: "nn","trilinear","sinc","spline"
    --padding-size INT  Extrapolates outside original volume by n voxels
    --use-qform         Use s/qforms of ref_vol and nii_file images
                        - NOTE: no other transorms can be applied with this option
    --data-type CMD     Force output data type (valid options: "char" "short" "int" "float" "double")
    --super-sampling    Intermediary supersampling of output. [default: False]
    --super-level CMD   Level of intermediary supersampling, a for 'automatic' or integer level.
                        Only used when '--super-sampling' option is enabled. [default: 2]
    --no-parallel       Do not apply linear/non-linear transforms in parallel.
                        NOT RECOMMENDED for 4D neuroimage EPIs greater than 300 frames (TRs) or
                        for use with non-linear transforms as FSL's applywarp has to read the entire
                        timeseries into memory.
    -v,--verbose        Enable verbose output [default: False]
    -h,--help           Prints help message, then exits.
    --version           Prints version, then exits.
NOTE: '--resamp-dim' and '--resamp-vox' options require MIRTK to be installed if these options are specified.
"""

# Import packages/modules
import pandas as pd
import os

# Import packages and modules for argument parsing
from docopt import docopt

# Define functions

def find_delim(in_file, verbose=False):
    '''
    Inspects input file or string for some known delimiter (e.g. ',','\t' etc.)
    and returns the returns the delimiter used to separate enteries in the
    input file or string.

    Arguments:
        in_file (file or string): Input file or string. If the input file does not exist, it is assumed to be a string.
        verbose (boolean): Enable verbose output
    Returns:
        delim (string): The delmiter used in the input file or string.
    '''

    if os.path.exists(in_file):
        with open(in_file, 'r') as file:
            lines = file.readlines()

            if '.tsv' in in_file:
                delim = "\t"
                if verbose:
                    print("Input file is a tsv")
            elif '.csv' in in_file:
                delim = ","
                if verbose:
                    print("Input file is a csv")
            elif ',' in lines[0]:
                delim = ","
                if verbose:
                    print("Input file is a csv")
            elif '\t' in lines[0]:
                delim = "\t"
                if verbose:
                    print("Input file is a tsv")
            elif '\n' in lines[0]:
                delim = "\n"
                if verbose:
                    print("Input file uses newline separators exclusively")
            else:
                delim = " "
                # print("Unrecognized delimiter from input file")

            file.close()
    else:
        if "," in in_file:
            delim = ","
        elif "\t" in in_file:
            delim = "\t"
        elif ":" in in_file:
            delim = ":"
        elif ";" in in_file:
            delim = ";"
        else:
            delim = " "
            # print("Unrecognized delimiter from input string")

    return delim


def mk_df(in_file, verbose=False):
    '''
    Creates a (pandas) dataframe from an input file.

    Arguments:
        in_file (file): Input file.
        verbose (boolean): Enable verbose output
    Returns:
        df (dataframe): Output dataframe
    '''

    delim = find_delim(in_file=in_file, verbose=verbose)
    df = pd.read_csv(in_file, sep=delim)

    col_names = list(df.columns)
    df.sort_values(by=col_names[0], axis=0, inplace=True, ascending=True, kind='quicksort')

    return df


def rm_sub(df, rm_list):
    '''
    Removes a list of subjects from some dataframe. Note that this
    change is done in-place.

    Arguments:
        df (dataframe): Input dataframe.
        rm_list (list): List of subjects to remove from dataframe
    Returns:
        df (dataframe): Output dataframe with subjects in list removed
    '''

    col_names = list(df.columns)

    if len(rm_list) != 0:
        for r in rm_list:
            df.drop(df[df[col_names[0]] == r].index, inplace=True)

    return df


def keep_columns(df, kp_list=[], rm_nan=True):
    '''
    Creates an output dataframe that contains only the specified column
    indices (e.g. numerical index starting at 0 and not the column names).
    The output dataframe will also drop subjects that contain NaNs for all
    covariates of interest.

    Arguments:
        df (dataframe): Input dataframe.
        kp_list (list): List of df column name indices to be kept. The indices should follow that of the input TSV or CSV file.
        rm_nan (boolean): Drops subjects that contain NaNs
    Returns:
        df_2 (dataframe): Output dataframe with only the selected columns remaining.
    '''

    # Create column list
    col_names = list(df.columns)

    # Init keep-cols list
    kp_cols = list()
    kp_cols.insert(0, col_names[0])

    # Check for empty input list
    if len(kp_list) == 0:
        kp_list = range(1, len(col_names), 1)

    # Create list of columns to keep
    for idx in kp_list:
        kp_cols.append(col_names[idx])

    # Create new dataframe
    df_2 = df[kp_cols].copy()

    # Exclude subjects with NaNs
    if rm_nan:
        df_2.dropna(subset=kp_cols, inplace=True)

    return df_2


def subs_retain(df, subs_keep=[]):
    '''
    Creates a copy of dataframe that only includes a list of subjects.

    Arguments:
        df (dataframe): Input dataframe.
        subs_keep (list): List of subjects to create the dataframe from
    Returns:
        df_keep (dataframe): Output dataframe with subjects in list
    '''

    col_names = list(df.columns)
    df_keep = pd.DataFrame({col_names[0]: []})

    if len(subs_keep) != 0:
        for sub in subs_keep:
            df_keep = df_keep.append(df.loc[df[col_names[0]] == sub], sort=True)
    else:
        df_keep = df

    return df_keep


def mk_adj_sub_list(df, rm_list=[], keep_list=[]):
    '''
    Creates an adjusted subject inclusion (keep_list) and exclusion (rm_list)
    lists using some input dataframe. The input rm_list is updated to
    reflect subjects removed from the design matrix as a result of
    manual exclusion or missing data.

    Arguments:
        df (dataframe): Input dataframe.
        rm_list (list): List of subjects to remove.
        keep_list (list): List of subjects to retain.
    Returns:
        rm_list_adj (list): Adjusted rm_list that lists all excluded subjects.
        keep_list_adj (list): Adjusted keep_list that list all the included subjects.
    '''

    # Create list from dataframe subject IDs
    col_names = list(df.columns)
    all_subs = df[col_names[0]].to_list()

    # Create sets from lists
    all_subs_set = set(all_subs)
    subs_keep_set = set(keep_list)
    rm_list_set = set(rm_list)

    if len(rm_list) != 0 and len(keep_list) != 0:
        rm_list_set.update(all_subs_set.difference(subs_keep_set))
    elif len(rm_list) != 0:
        subs_keep_set.update(all_subs_set.difference(rm_list_set))
        rm_list_set.update(all_subs_set.difference(subs_keep_set))

    rm_list_adj = list(rm_list_set)
    keep_list_adj = list(subs_keep_set)

    return rm_list_adj, keep_list_adj


def list_to_file(in_list, out_file):
    '''
    Writes some input list to some file.

    Arguments:
        in_list (list): List of subjects.
        out_file (file): Output filename.
    Returns:
        out_file (file): Output file.
    '''

    # Write list to file
    with open(out_file, "w") as f:
        for sub in in_list:
            f.write("%s\n" % sub)
        f.close()

    return out_file


def file_to_list(file):
    '''
    Reads a file into a list, assuming the file is separated by newline
    characters.

    Arguments:
        file (file): Input file to be read.
    Returns:
        lines (list): List from input file.
    '''

    # Read file into list
    with open(file, "r") as f:
        lines = f.read().splitlines()
        f.close()

    lines.sort()

    return lines


def parse_str_list(string):
    '''
    Parses a file or string into a list.

    Arguments:
        string (file or string): Input file or string to be read.
    Returns:
        sub_list (list): List of subjects from file or string.
    '''

    delim = find_delim(in_file=string)
    in_list = string.split(sep=delim)
    in_list.sort()

    if len(in_list) == 1:
        if os.path.exists(string):
            sub_list = file_to_list(file=string)
        else:
            sub_list = in_list
    elif len(in_list) > 1:
        sub_list = in_list

    return sub_list


def write_design(df, out_file, sep=" "):
    '''
    Writes an output design matrix from an input dataframe. Output
    values for floats will be written with three decimal places of
    floating point precision.

    Arguments:
        df (dataframe): Input dataframe
        out_file (file): Output filename
        sep (string): Separator
    Returns:
        out_file (file): Output design
    '''

    # Create column list
    col_names = list(df.columns)
    out_cols = list()

    # Create secondary dataframe without subject ID column
    for idx in range(1, len(col_names), 1):
        out_cols.append(col_names[idx])

    df_out = df[out_cols].copy()

    # df_out.to_csv(out_file,sep=sep,header=False,index=False,na_rep="NaN",float_format='%g')
    df_out.to_csv(out_file, sep=sep, header=False, index=False, na_rep="NaN", float_format='%.3f')

    # return out_file, df_out
    return out_file


def demean_col(df, col_indices=[]):
    '''
    Demeans column indices of a dataframe. NOTE: The column or columns
    can only contain numeric values. Non-numeric values will cause
    errors, and exceptions to be thrown.

    Arguments
        df (dataframe): Input dataframe
        col_indices (list): List of column numerical indices to demean
    Returns
        df_demean (dataframe): Output dataframe with demeaned columns from the input list
    '''

    # Create column list
    col_names = list(df.columns)

    # Copy dataframe
    df_demean = df.copy()

    for i in col_indices:
        df_demean[col_names[i]] = df_demean[col_names[i]].sub(df_demean[col_names[i]].mean())

    return df_demean


def mk_design(in_file, prefix, rm_list="", ret_list="", kp_col_list="", rm_nan=True, sep=" "):
    '''
    Writes output design matrix in addition to inclusion and exclusion lists
    for the given input file (which could be a TSV or CSV). The output design
    matrix is written without headers, row indices, and subject IDs. The input
    file must contain the subject IDs in the first column.

    Arguments:
        in_file (file): Input file with header titles, subject IDs, and covariates
        prefix (string): Output file prefix.
        rm_list (file or string): File or comma separated strings of subjects to remove.
        ret_list (file or string): File or comma separated strings of subjects to retain.
        kp_col_list (file or string): File or comma separated strings of column indices to retain in design matrix (e.g. "1,2,3", index count starts at 0).
        rm_nan (boolean): Remove subjects with NaNs in the specified covariates (from kp_col_list) from the design matrix.
        sep (string): Separator string to use, valid separators/delimitors include: "," and "\t".
    Returns:
        out_mat (file): Output design matrix
        out_rm (file): Subject exclusion file
        out_keep (file): Subject inclusion file
    '''

    # Create initial dataframe
    df_init = mk_df(in_file=in_file)

    # Create input lists from input strings
    if len(rm_list) > 1:
        rm_list = parse_str_list(string=rm_list)
    if len(ret_list) > 1:
        ret_list = parse_str_list(string=ret_list)
    if len(kp_col_list) > 1:
        kp_col_list = parse_str_list(kp_col_list)
        kp_col_list = [int(i) for i in kp_col_list]

    # Create updated dataframe
    df_keep = subs_retain(df=df_init, subs_keep=ret_list)
    df_rm = rm_sub(df=df_keep, rm_list=rm_list)
    df = keep_columns(df=df_rm, kp_list=kp_col_list, rm_nan=rm_nan)

    # Update inclusion and exclusion lists
    [rm_list, ret_list] = mk_adj_sub_list(df=df, rm_list=rm_list, keep_list=ret_list)

    # Write output files
    out_mat = prefix + ".mat"
    out_rm = prefix + ".exclude.txt"
    out_keep = prefix + ".include.txt"

    out_mat = write_design(df=df, out_file=out_mat, sep=sep)
    out_rm = list_to_file(in_list=rm_list, out_file=out_rm)
    out_keep = list_to_file(in_list=ret_list, out_file=out_keep)

    return out_mat, out_rm, out_keep

if __name__ == '__main__':

    # Parse arguments
    args = docopt(__doc__, help=True, version='mk_design.py v0.0.1', options_first=False)
    # print(args)
