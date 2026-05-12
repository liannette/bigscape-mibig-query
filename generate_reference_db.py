#!/usr/bin/env python3
"""
Generate an empty BiG-SCAPE backup database for use as a reference
"""
import subprocess
import sqlite3
from pathlib import Path
import sys
import argparse
import shutil
import tempfile


def create_empty_gbk(output_path):
    """
    Create a minimal empty GenBank file for database initialization
    """
    minimal_gbk = """LOCUS       EMPTY                      1 bp    DNA     linear       01-JAN-2024
DEFINITION  Empty placeholder for database initialization.
ACCESSION   EMPTY
VERSION     EMPTY.1
KEYWORDS    .
SOURCE      .
  ORGANISM  .
            .
FEATURES             Location/Qualifiers
ORIGIN      
        1 a
//
"""
    with open(output_path, 'w') as f:
        f.write(minimal_gbk)
    print(f"Created empty GenBank file: {output_path}")


def clean_empty_entry(database_path):
    """
    Remove the empty placeholder entry from the database
    """
    print("Cleaning empty placeholder entry from database...")
    try:
        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()
        
        # Delete empty.gbk entries
        cursor.execute("DELETE FROM gbk WHERE path LIKE '%empty.gbk%'")
        cursor.execute("DELETE FROM bgc_record WHERE gbk_id NOT IN (SELECT id FROM gbk)")
        cursor.execute("DELETE FROM distance")
        
        conn.commit()
        conn.close()
        print("Empty entry cleaned successfully")
    except Exception as e:
        print(f"Warning: Failed to clean empty entry: {e}")


def generate_backup_database(output_path, pfam_path, mibig_version, cores, quiet=False):
    """
    Generate a new backup database using BiG-SCAPE with an empty GenBank file
    """
    output_path = Path(output_path) / f"mibig_{mibig_version}"
    print(f"\nGenerating new backup database at: {output_path}")
    output_path.mkdir(parents=True, exist_ok=True)

    # Create temporary directory for the operation
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        
        # Create empty GenBank file
        empty_gbk = temp_dir_path / "empty.gbk"
        create_empty_gbk(empty_gbk)
        
        # Create temporary input directory
        temp_input = temp_dir_path / "input"
        temp_input.mkdir()
        shutil.copy2(empty_gbk, temp_input / "empty.gbk")
        
        # Run BiG-SCAPE to generate database
        print("Running BiG-SCAPE to initialize database...")
        cmd = [
            "bigscape", "query",
            "--input-dir", str(temp_input),
            "--query-bgc-path", str(temp_input / "empty.gbk"),
            "--output-dir", str(output_path),
            "--pfam-path", str(pfam_path),
            "--mibig-version", str(mibig_version),
            "--force-gbk",
            "--cores", str(cores)
        ]
        
        if quiet:
            cmd.append("--quiet")
        
        print(f"Command: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            print("Database initialization completed")
            if not quiet and result.stdout:
               print(result.stdout)
            
            generated_db = output_path / f"mibig_{mibig_version}.db"
            if generated_db.exists():
                print(f"Backup database created successfully at: {generated_db}")
                
                # Clean up the empty entry from the database
                clean_empty_entry(generated_db)

                return True
            else:
                print("Error: Database file was not created")
                return False
                
        except subprocess.CalledProcessError as e:
            print(f"BiG-SCAPE failed with error:\n{e.stderr}")
            return False
        

def main():
    parser = argparse.ArgumentParser(
        description="Generate an BiG-SCAPE database containing only mibig entries (for use as a reference in similarity searches)"
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        default=Path("data/reference_db"),
        help="Output dir for the backup database (e.g., data/mibig_db)"
    )
    parser.add_argument(
        "-p", "--pfam-path",
        type=Path,
        default=Path("data/pfam/Pfam-A.hmm"),
        help="Path to Pfam-A.hmm file"
    )
    parser.add_argument(
        "-m", "--mibig-version",
        type=float,
        default=4.0,
        help="MIBiG version (default: 4.0)"
    )
    parser.add_argument(
        "-c", "--cores",
        type=int,
        default=1,
        help="Number of cores to use (default: 1)"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Run in quiet mode"
    )
    
    args = parser.parse_args()
    
    # Check if output file already exists
    if args.output.exists():
        response = input(f"File {args.output} already exists. Overwrite? [y/N]: ")
        if response.lower() != 'y':
            print("Aborted")
            sys.exit(0)
    
    # Generate backup database
    if generate_backup_database(
        args.output,
        args.pfam_path,
        args.mibig_version,
        args.cores,
        args.quiet
    ):
        print("\n✓ Backup database generation completed successfully")
        print(f"\nYou can now use this database with run_bigscape_query.py:")
        print(f"  python run_bigscape_query.py -b {args.output} ...")
        sys.exit(0)
    else:
        print("\n✗ Backup database generation failed")
        sys.exit(1)


if __name__ == "__main__":
    main()