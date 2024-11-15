#!/usr/bin/env python3

import unittest
import os
import sys
import io
import shutil
from unittest import mock
from unittest import TestCase
from contextlib import contextmanager
from pathlib import Path

# import from parent dir
PROJECT_DIR = Path(__file__).absolute().parent
sys.path.insert(0, PROJECT_DIR.parent.as_posix())
import fastdiff
ROOT_PATH = PROJECT_DIR / 'root'
ROOT_DIR = ROOT_PATH.as_posix()

# Usage:
# > test_fastdiff.py
# > test_fastdiff.py TestFastdiff.test_clean
class TestFastdiff(unittest.TestCase):
    def setUp(self):
        os.makedirs(ROOT_DIR, exist_ok=True)
        shutil.rmtree(ROOT_DIR)
        os.makedirs(ROOT_DIR, exist_ok=True)
        
    def test_diff_recursively(self):
        print('======= test_diff_recursively ===')
        dir1 = self._createDir(ROOT_DIR, 'dir1')
        dir1_a = self._createDir(dir1, 'a')
        dir1_a_a = self._createDir(dir1_a, 'a')
        dir1_a_only1 = self._createDir(dir1_a, 'only1')
        dir1_b = self._createDir(dir1, 'b')
        self._createFiles(dir1, 'file-root.txt')
        self._createFiles(dir1_a, 'file-a-a.txt', 'file-a-only1.txt')
        self._createFiles(dir1_a_a, 'file-a-a-a.txt', 'file-a-a-only1.txt')
        self._createFiles(dir1_b, 'file-b-a.txt')
        
        dir2 = self._createDir(ROOT_DIR, 'dir2')
        dir2_a = self._createDir(dir2, 'a')
        dir2_a_a = self._createDir(dir2_a, 'a')
        dir2_b = self._createDir(dir2, 'b')
        self._createFiles(dir2, 'file-root.txt')
        self._createFiles(dir2_a, 'file-a-a.txt')
        self._createFiles(dir2_a_a, 'file-a-a-a.txt')
        self._createFiles(dir2_b, 'file-b-a.txt', 'file-b-only2.txt')
        
        with self.captured_output() as (out, err):
            fastdiff.main(['-r', dir1, dir2])
        output = out.getvalue().strip()
        print(output)
        lines = output.splitlines()
        self.assertEqual(4, len(lines))
        self.assertEqual(lines[0], f'Only in {dir1}: {os.path.join("a", "a", "file-a-a-only1.txt")}')
        self.assertEqual(lines[1], f'Only in {dir1}: {os.path.join("a", "only1")}')
        self.assertEqual(lines[2], f'Only in {dir1}: {os.path.join("a", "file-a-only1.txt")}')
        self.assertEqual(lines[3], f'Only in {dir2}: {os.path.join("b", "file-b-only2.txt")}')
        
    def test_diff(self):
        print('======= test_diff ===')
        dir1 = self._createDir(ROOT_DIR, 'dir1')
        dir1_a = self._createDir(dir1, 'a')
        dir1_only1 = self._createDir(dir1, 'folder-only1')
        self._createFiles(dir1, 'file-a-only1.txt', 'file-c.txt')
        self._createFiles(dir1_a, 'file-a-a-ignored.txt')
        self._createFiles(dir1_only1, 'file-a-ignored.txt')
        
        dir2 = self._createDir(ROOT_DIR, 'dir2')
        dir2_a = self._createDir(dir2, 'a')
        self._createFiles(dir2, 'file-b-only2.txt', 'file-c.txt', 'file-d-only2.txt')
        self._createFiles(dir2_a, 'file-a-a-ignore2.txt')

        with self.captured_output() as (out, err):
            fastdiff.main([dir1, dir2])
        output = out.getvalue().strip()
        print(output)
        lines = output.splitlines()
        self.assertEqual(4, len(lines))
        self.assertEqual(lines[0], f'Only in {dir1}: folder-only1')
        self.assertEqual(lines[1], f'Only in {dir1}: file-a-only1.txt')
        self.assertEqual(lines[2], f'Only in {dir2}: file-b-only2.txt')
        self.assertEqual(lines[3], f'Only in {dir2}: file-d-only2.txt')

    def test_diff_size(self):
        print('======= test_diff_size ===')
        dir1 = self._createDir(ROOT_DIR, 'dir1')
        self._createFiles(dir1, 'file-a.txt', content='A')
        self._createFiles(dir1, 'file-b.txt')

        dir2 = self._createDir(ROOT_DIR, 'dir2')
        self._createFiles(dir2, 'file-a.txt', content='BBB')
        self._createFiles(dir2, 'file-b.txt')

        with self.captured_output() as (out, err):
            fastdiff.main([dir1, dir2])
        output = out.getvalue().strip()
        print(output)
        lines = output.splitlines()
        self.assertEqual(1, len(lines))
        self.assertEqual(lines[0], 'different file size: 1 | 3: file-a.txt')
        
    def test_diff_link(self):
        print('======= test_diff_link ===')
        if os.name == 'nt':
            print('skipped on Windows')
            return
        dir1 = self._createDir(ROOT_DIR, 'dir1')
        self._createFiles(dir1, 'file-a.txt', 'file-link.txt')

        dir2 = self._createDir(ROOT_DIR, 'dir2')
        self._createFiles(dir2, 'file-a.txt')
        os.symlink(str(Path(dir2, 'file-a.txt')), str(Path(dir2, 'file-link.txt')))
        
        with self.captured_output() as (out, err):
            fastdiff.main([dir1, dir2])
        output = out.getvalue().strip()
        print(output)
        lines = output.splitlines()
        self.assertEqual(1, len(lines))
        self.assertEqual(lines[0], 'different file type: file | link: file-link.txt')

    def test_diff_link_broken(self):
        print('======= test_diff_link_broken ===')
        if os.name == 'nt':
            print('skipped on Windows')
            return
        dir1 = self._createDir(ROOT_DIR, 'dir1')
        self._createFiles(dir1, 'file-a.txt', 'file-c.txt')
        dir1_file_a = str(Path(dir1, 'file-a.txt'))
        os.symlink(dir1_file_a, str(Path(dir1, 'file-link.txt')))

        dir2 = self._createDir(ROOT_DIR, 'dir2')
        self._createFiles(dir2, 'file-a.txt', 'file-c.txt')
        dir2_file_a = str(Path(dir2, 'file-a.txt'))
        os.symlink(dir2_file_a, str(Path(dir2, 'file-link.txt')))
        os.remove(dir2_file_a)
        
        with self.captured_output() as (out, err):
            fastdiff.main([dir1, dir2])
        output = out.getvalue().strip()
        print(output)
        lines = output.splitlines()
        self.assertEqual(2, len(lines))
        self.assertEqual(lines[0], f'Only in {dir1}: file-a.txt')
        self.assertTrue('Error:' in lines[1])
        self.assertTrue('file-link.txt' in lines[1])

    def test_clean(self):
        shutil.rmtree(ROOT_DIR)

    @contextmanager
    def captured_output(self):
        new_out, new_err = io.StringIO(), io.StringIO()
        old_out, old_err = sys.stdout, sys.stderr
        try:
            sys.stdout, sys.stderr = new_out, new_err
            yield sys.stdout, sys.stderr
        finally:
            sys.stdout, sys.stderr = old_out, old_err
    
    def _createDir(self, *folders):
        dir = str(Path(*folders))
        os.makedirs(dir, exist_ok=True)
        return dir
        
    def _createFiles(self, dir, *files, content=None):
        for file in files:
            filePath = os.path.join(dir, file)
            with open(filePath, 'x') as f:
                f.write(file if content is None else content)

if __name__ == '__main__':
    unittest.main()
