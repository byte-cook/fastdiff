#!/usr/bin/env python3

import os
import argparse
from pathlib import Path
import logging
import traceback
from stat import *

def compareFolder(args, relPath=""):
    """Compares two folders."""
    dir1 = os.path.join(args.dir1, relPath)
    dir2 = os.path.join(args.dir2, relPath)
    logging.debug(f'Comparing {dir1} and {dir2}')
    folders1, files1 = _getFolderAndFiles(dir1)
    folders2, files2 = _getFolderAndFiles(dir2)
    
    allFolders = sorted(folders1.union(folders2)) if not args.skipFolders else []
    for folder in allFolders:
        subRelPath = os.path.join(relPath, folder)
        logging.debug(f'Checking folder {subRelPath}...')
        
        inDir1 = folder in folders1
        inDir2 = folder in folders2
        if inDir1: folders1.remove(folder)
        if inDir2: folders2.remove(folder)
        
        if inDir1 and inDir2:
            pass
        elif inDir1:
            _printMessage(subRelPath, f'Only in {args.dir1}')
        elif inDir2:
            _printMessage(subRelPath, f'Only in {args.dir2}')
        
        if args.recursive:
            compareFolder(args, relPath=subRelPath)
    
    allFiles = sorted(files1.union(files2))
    for file in allFiles:
        subRelPath = os.path.join(relPath, file)
        logging.debug(f'Checking file {subRelPath}...')
        
        inDir1 = file in files1
        inDir2 = file in files2
        if inDir1: files1.remove(file)
        if inDir2: files2.remove(file)
        
        if inDir1 and inDir2:
            _compareFiles(args, subRelPath)
        elif inDir1:
            _printMessage(subRelPath, f'Only in {args.dir1}')
        elif inDir2:
            _printMessage(subRelPath, f'Only in {args.dir2}')

def _compareFiles(args, relPath):
    """Compares two files."""
    if args.namesOnly:
        return
    try:
        file1 = Path(args.dir1, relPath)
        file2 = Path(args.dir2, relPath)
        
        # 1. don't follow symlinks
        isLink = _compareFileStats(file1, file2, relPath, follow_symlinks=False)
        if isLink and not args.noDereference:
            # 2. follow symlinks
            _compareFileStats(file1, file2, relPath, follow_symlinks=True)
    except Exception as e: 
        print(f'Error: {e}')
        return False

def _compareFileStats(file1, file2, relPath, follow_symlinks):
    """Compares two files by file type and size."""
    stat1 = os.stat(file1, follow_symlinks=follow_symlinks)
    stat2 = os.stat(file2, follow_symlinks=follow_symlinks)
    # file type
    isLink1 = S_ISLNK(stat1.st_mode)
    isLink2 = S_ISLNK(stat2.st_mode)
    if isLink1 != isLink2:
        _printMessage(relPath, f'different file type: {"link" if isLink1 else "file"} | {"link" if isLink2 else "file"}')
        return False
    # file size
    size1 = stat1.st_size
    size2 = stat2.st_size
    if size1 != size2:
        _printMessage(relPath, f'different file size: {size1} | {size2}')
        return False
    
    return isLink1 or isLink2
        
def _getFolderAndFiles(dir):
    """Returns all folders and files of the given directory as sets."""
    listdir = os.listdir(dir) if os.path.exists(dir) else []
    folders = {f for f in listdir if os.path.isdir(os.path.join(dir, f))}
    files = {f for f in listdir if not os.path.isdir(os.path.join(dir, f))}
    logging.debug(f'{dir}: {files} + {folders}')
    return (folders, files)

def _printMessage(relPath, msg):
    print(f'{msg}: {relPath}')

def _checkDir(dir):
    if not os.path.exists(dir):
        print(f'{dir} does not exist')
        exit(1)
    if not os.path.isdir(dir):
        print(f'{dir} is not a directory')
        exit(1)

def main(argv=None):
    try:
        parser = argparse.ArgumentParser(description='Compares two directories to determine if they contain the same files. The files are only compared by size to ensure fast execution.')
        parser.add_argument('--debug', action='store_true', help='activate DEBUG logging')
        parser.add_argument('--skip-folders', dest='skipFolders', action='store_true', help='skip folders')
        parser.add_argument('--names-only', dest='namesOnly', action='store_true', help='only compare names, ignoring file type and size')
        parser.add_argument('--no-dereference', dest='noDereference', action='store_true', help='don\'t follow symbolic links')
        parser.add_argument('-r', '--recursive', action='store_true', help='perform command recursively')
        parser.add_argument('dir1', metavar='dir1', help='the first directory to compare')
        parser.add_argument('dir2', metavar='dir2', help='the second directory to compare')
        args = parser.parse_args(argv)
        
        # init logging
        level = logging.DEBUG if args.debug else logging.WARNING
        logging.basicConfig(format='%(levelname)s: %(message)s', level=level, force=True)
        
        _checkDir(args.dir1)
        _checkDir(args.dir2)
        
        compareFolder(args)
        
    except Exception as e:
        print(e)
        logging.debug(type(e))
        if args.debug:
            traceback.print_exc()
        exit(1)

if __name__ == '__main__':
    main()
