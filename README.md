# BiG-SCAPE MIBiG Query

Automated pipeline for running BiG-SCAPE in query mode to find similar BGCs in MIBiG.

## Overview

This tool simplifies the process of finding MIBiG BGCs similar to a query BGC:

1. **One-time setup [Optional]**: Generate a reference database containing MIBiG BGCs
2. **Per query**: Run BiG-SCAPE to compare your query against MIBiG and extract ranked distance results

**Why use this tool?** BiG-SCAPE requires some manual setup (input directories, database management). This wrapper automates that workflow and extracts clean distance rankings.


## Installation

### 1. Install BiG-SCAPE 2

Install BiG-SCAPE 2 via conda/mamba:

```bash
# Create a new conda environment
conda create -n bigscape -c conda-forge -c bioconda bigscape 
conda activate bigscape
```

**Alternative installation methods:**
- Follow the official [BiG-SCAPE documentation](https://github.com/medema-group/BiG-SCAPE)

### 2. Download Pfam Database

Download the Pfam database:

```bash
# Create a directory for the database
mkdir -p data/pfam
cd data/pfam

# Download Pfam-A.hmm (latest version, ~500 MB compressed)
wget http://ftp.ebi.ac.uk/pub/databases/Pfam/current_release/Pfam-A.hmm.gz

# Decompress (~2 GB uncompressed)
gunzip Pfam-A.hmm.gz

cd ../..
```
**What is Pfam?** A database of protein domain families. BiG-SCAPE uses these domains to compare BGC similarity.

### 3. Clone This Repository

```bash
git clone https://github.com/liannette/bigscape-mibig-query
cd bigscape-mibig-query
```


## Quick Start

### Step 1: Generate Reference Database [Optional but Recommended]

Create a database containing all MIBiG BGCs to speed up subsequent queries.

**This step is optional but recommended if you plan to run multiple queries.** 
Without it, BiG-SCAPE will download and process MIBiG for each query.

```bash
python generate_reference_db.py
```

**What this does:**
- BiG-SCAPE downloads MIBiG, detects domains, and stores everything in a SQLite database
- On first run, BiG-SCAPE will also prepare (press) the Pfam database using `hmmpress`. 
If the .hmm file has already been pressed and the pressed files are included in the 
same folder as the Pfam .hmm file, BiG-SCAPE will also use these pressed files. 

**Arguments:**
- `-o, --output`: Path where the reference database will be saved (default: data/reference_db)
- `-p, --pfam-path`: Path to your Pfam-A.hmm file (default: data/pfam/Pfam-A.hmm)
- `-m, --mibig-version`: MIBiG version (default: 4.0)
- `-c, --cores`: Number of CPU cores to use (default: 1)
- `--quiet`: Suppress BiG-SCAPE output

### Step 2: Run a Query

Query a query BGC against the reference database:

```bash
python run_bigscape_query.py --query-bgc my_bgc.gbk
```

**What this does:**
1. Copies the reference database to the output directory (if available)
2. Runs BiG-SCAPE in query mode (compares query BGC vs all MIBiG)
3. Extracts distance results from the database
4. Exports ranked results to TSV

**Arguments:**
- `-q, --query-gbk`: Path to your query BGC GenBank file
- `-o, --output-dir`: Output directory (database will be named `<dirname>.db`)
- `-p, --pfam-path`: Path to Pfam-A.hmm file
- `-r, --reference-db`: Path to the reference database
- `-m, --mibig-version`: MIBiG version (default: 4.0)
- `-c, --cores`: Number of CPU cores (default: 4)
- `--quiet`: Run BiG-SCAPE in quiet mode
- `--skip-bigscape`: Only query existing database, skip BiG-SCAPE run
- `--keep-input-dir`: Keep temporary input directory for debugging

## Output

### Files Generated

1. **Database**: `<output-dir>/<output-dir-name>.db`
   - SQLite database with BiG-SCAPE results
   - Contains BGC records and distance calculations
   
2. **Distance Results**: `distances.tsv`
   - Tab-separated values file
   - Sorted by distance (most similar first)

### Output Format

The TSV file contains two columns:

```tsv
distance	mibig_accession
0.0234	BGC0001234
0.0456	BGC0005678
0.0891	BGC0002345
...
```

- `distance`: BiG-SCAPE distance metric (lower = more similar)
- `mibig_accession`: MIBiG identifier (filename stem from GenBank file)

**What is BiG-SCAPE distance?** A composite metric combining:
- Domain sequence similarity (DSS)
- Domain organization (Jaccard index)
- Synteny/gene order (Adjacency index)



## File Structure

```
.
├── generate_reference_db.py    # Script to create reference database
├── run_bigscape_query.py       # Main query script
├── README.md                   # This file
├── data/
│   ├── pfam/
│   │   ├── Pfam-A.hmm          # Pfam database (need to be downloaded)
│   │   └── Pfam-A.hmm.h3*      # HMMER index files (created during first run)
│   └── reference_db
│       └── mibig_4.0.db        # Reference database of MIBiG BGCs (if generated)
└── output/
    └── distances.tsv           # Distances between query BGC and MIBiG BGCs
    ├── output.db               # Output database
    └── query_gbk/              # Temporary (usually deleted)
```


## Why Generate a Reference Database?

**The reference database is optional but highly recommended for performance:**

- **Without reference DB**: Each query would need to download MIBiG, detect all domains, and perform comparisons from scratch
- **With reference DB**: Domain detection for MIBiG is done once; subsequent queries only process your query BGC

**For multiple queries**, the reference database approach saves significant time after the initial setup.


## Citation

If you use this tool in your research, please cite:

[BiG-SCAPE 2.0 and BiG-SLiCE 2.0: scalable, accurate and interactive sequence clustering of metabolic gene clusters](https://doi.org/10.1038/s41467-026-68733-5)
