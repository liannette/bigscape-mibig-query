#!/usr/bin/env python3
"""
Run BiG-SCAPE query mode and extract distance results
"""
import subprocess
import sqlite3
from pathlib import Path
import csv
import sys
import argparse
import shutil


def setup_input_directory(query_gbk, temp_input_dir):
    """
    Create temporary input directory containing only the query BGC
    """
    print(f"Setting up input directory at {temp_input_dir}")
    
    # Create directory
    temp_input_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy query GBK to input directory
    dest_gbk = temp_input_dir / query_gbk.name
    shutil.copy2(query_gbk, dest_gbk)
    print(f"Copied {query_gbk.name} to input directory")
    
    return temp_input_dir


def setup_database(reference_db, output_dir):
    """
    Copy reference database to output directory so BiG-SCAPE can use it as base
    Database filename matches output directory name
    """
    db_name = f"{output_dir.name}.db"
    target_db = output_dir / db_name
    
    if not reference_db.exists():
        print(f"Reference database not found at {reference_db}")
        print("Proceeding without base database (BiG-SCAPE will create new one)")
        return target_db
    
    print(f"Copying reference database from {reference_db} to {target_db}")
    
    try:
        # Create output directory if it doesn't exist
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy reference to output directory with name matching output dir
        shutil.copy2(reference_db, target_db)
        print("Database copied successfully.")
        
        return target_db
    except Exception as e:
        print(f"Error: Failed to copy reference database: {e}")
        sys.exit(1)


def run_bigscape(input_dir, query_gbk_name, output_dir, pfam_path, mibig_version, cores, quiet=False):
    """Run BiG-SCAPE in query mode"""
    print("\nRunning BiG-SCAPE query...")
    
    # Query GBK path is now in the temp input directory
    query_bgc_path = input_dir / query_gbk_name
    
    cmd = [
        "bigscape", "query",
        "--input-dir", str(input_dir),
        "--query-bgc-path", str(query_bgc_path),
        "--output-dir", str(output_dir),
        "--pfam-path", str(pfam_path),
        "--mibig-version", str(mibig_version),
        "--cores", str(cores)
    ]
    
    if quiet:
        cmd.append("--quiet")
    
    print(f"Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("BiG-SCAPE completed successfully")
        if not quiet and result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"BiG-SCAPE failed with error:\n{e.stderr}")
        return False


def cleanup_input_directory(temp_input_dir):
    """Remove temporary input directory"""
    if temp_input_dir.exists():
        print(f"\nCleaning up temporary input directory: {temp_input_dir}")
        shutil.rmtree(temp_input_dir)
        print("Cleanup complete")


def query_distances(database_path, query_path, output_file):
    """Query the database for distances and save to file"""
    print(f"\nQuerying database: {database_path}")
    
    if not database_path.exists():
        print(f"Database not found at {database_path}")
        return False
    
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            distance.distance,
            gbk_b.path
        FROM distance 
        JOIN bgc_record AS bgc_record_a ON distance.record_a_id = bgc_record_a.id
        JOIN gbk AS gbk_a ON bgc_record_a.gbk_id = gbk_a.id
        JOIN bgc_record AS bgc_record_b ON distance.record_b_id = bgc_record_b.id
        JOIN gbk AS gbk_b ON bgc_record_b.gbk_id = gbk_b.id
        WHERE gbk_a.path = ? AND bgc_record_a.record_type = 'region'
        ORDER BY distance.distance ASC
    """, (query_path,))
    
    distances = [(dist, Path(p).stem) for dist, p in cursor.fetchall()]
    conn.close()
    
    print(f"Found {len(distances)} distance entries")
    
    # Save to file
    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerow(['distance', 'mibig_accession'])
        writer.writerows(distances)
    
    print(f"Results saved to: {output_file}")
    
    # Print top 10
    if distances:
        print("\nTop 10 MIBiG BGCs with lowest distances:")
        for dist, bgc_id in distances[:10]:
            print(f"  {dist:.4f}\t{bgc_id}")
    
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Run BiG-SCAPE query and extract distance results"
    )
    parser.add_argument(
        "-q", "--query-bgc",
        required=True,
        type=Path,
        help="Query BGC file path"
    )
    parser.add_argument(
        "-o", "--output-dir",
        type=Path,
        default=Path("output"),
        help="Output directory for BiG-SCAPE results (database will be named <output-dir-name>.db)"
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
        default=4,
        help="Number of cores to use (default: 4)"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Run BiG-SCAPE in quiet mode"
    )
    parser.add_argument(
        "--skip-bigscape",
        action="store_true",
        help="Skip BiG-SCAPE run and only query existing database"
    )
    parser.add_argument(
        "--keep-input-dir",
        action="store_true",
        help="Keep temporary input directory after run"
    )
    
    args = parser.parse_args()
    
    # Setup temporary input directory
    temp_input_dir = args.output_dir / "query_gbk"
    
    try:
        if not args.skip_bigscape:
            # Create input directory with only the query GBK
            setup_input_directory(args.query_bgc, temp_input_dir)
            
            # Copy reference database to output directory
            reference_db = Path("data/reference_db") / f"mibig_{args.mibig_version}" / f"mibig_{args.mibig_version}.db"
            if reference_db.exists():
                print(f"Using reference database: {reference_db}")
                setup_database(reference_db, args.output_dir)
            else:
                print(f"No reference database found at {reference_db}, BiG-SCAPE will create a new one")

            # Run BiG-SCAPE
            if not run_bigscape(
                temp_input_dir,
                args.query_bgc.name,
                args.output_dir,
                args.pfam_path,
                args.mibig_version,
                args.cores,
                args.quiet
            ):
                print("BiG-SCAPE run failed, exiting")
                sys.exit(1)
        else:
            print("Skipping BiG-SCAPE run")
        
        db_path = args.output_dir / f"{args.output_dir.name}.db"
        
        # Query the database
        query_path_in_db = str(temp_input_dir / args.query_bgc.name)
        
        distances_file = args.output_dir / "distances.tsv"
        if not query_distances(db_path, query_path_in_db, distances_file):
            sys.exit(1)
    
    finally:
        # Cleanup temporary input directory unless --keep-input-dir is set
        if not args.keep_input_dir and not args.skip_bigscape:
            cleanup_input_directory(temp_input_dir)


if __name__ == "__main__":
    main()