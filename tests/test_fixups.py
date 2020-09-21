#!/usr/bin/env python3
from grp import getgrgid
from logging import getLogger, DEBUG
from os import readlink, listdir, lstat
from os.path import basename, dirname, exists, islink
from pwd import getpwuid
from stat import filemode, S_IMODE, S_ISLNK, S_ISREG
from tempfile import TemporaryDirectory
from time import localtime, strftime
from unittest import TestCase
from zipfile import ZipFile
import index


class TestFixups(TestCase):
    def setUp(self):
        self.log = getLogger()
        self.log.setLevel(DEBUG)
        self.config_test = TemporaryDirectory()
        self.config_dir = self.config_test.name
        self.log.info("Using temporary directory %s", self.config_dir)
        with ZipFile(f"{dirname(__file__)}/fixtest.zip", "r") as z:
            z.extractall(self.config_dir)

    def list_dir(self, dirname: str) -> None:
        self.log.info("Contents of %s", dirname)
        cur_year = localtime().tm_year
        results = []

        for filename in listdir(dirname):
            s = lstat(f"{dirname}/{filename}")
            if S_ISLNK(s.st_mode):
                target = readlink(f"{dirname}/{filename}")
                filename = f"{filename} -> {target}"
            
            mod_time = localtime(s.st_mtime)
            if mod_time.tm_year == cur_year:
                mod_time_str = strftime("%b %d %H:%M", mod_time)
            else:
                mod_time_str = strftime("%b %d  %Y", mod_time)

            results.append((
                filemode(s.st_mode), str(s.st_nlink), uid_to_username(s.st_uid), gid_to_groupname(s.st_gid), mod_time_str,
                filename))
        
        col_size = [max([len(el[i]) for el in results]) for i in range(6)]
        for line in results:
            self.log.info(
                "%*s %*s %*s %*s %*s %s", col_size[0], line[0], col_size[1], line[1], col_size[2], line[2], col_size[3], line[3],
                col_size[4], line[4], line[5])

    def test_fixup(self):
        index.fixup_config_dir(self.config_dir)
        archive = f"{self.config_dir}/archive"
        live = f"{self.config_dir}/live"
        try:
            self.assertTrue(islink(f"{live}/test1.kanga.org/cert.pem"))
            self.assertTrue(islink(f"{live}/test1.kanga.org/chain.pem"))
            self.assertTrue(islink(f"{live}/test1.kanga.org/fullchain.pem"))
            self.assertTrue(islink(f"{live}/test1.kanga.org/privkey.pem"))
            self.assertEqual(readlink(f"{live}/test1.kanga.org/cert.pem"), "../../archive/test1.kanga.org/cert1.pem")
            self.assertEqual(readlink(f"{live}/test1.kanga.org/chain.pem"), "../../archive/test1.kanga.org/chain1.pem")
            self.assertEqual(readlink(f"{live}/test1.kanga.org/fullchain.pem"), "../../archive/test1.kanga.org/fullchain1.pem")
            self.assertEqual(readlink(f"{live}/test1.kanga.org/privkey.pem"), "../../archive/test1.kanga.org/privkey1.pem")
        except:
            self.list_dir(f"{live}/test1.kanga.org")
            raise
        self.assertFalse(exists(f"{archive}/test1.kanga.org-0001"))
        self.assertFalse(exists(f"{archive}/test1.kanga.org-0002"))
        self.assertFalse(exists(f"{archive}/test1.kanga.org-0003"))
        self.assertFalse(exists(f"{archive}/test1.kanga.org-0004"))
        self.assertFalse(exists(f"{archive}/test1.kanga.org-0005"))
        self.assertFalse(exists(f"{archive}/test1.kanga.org-0006"))

        s = lstat(f"{archive}/test1.kanga.org/cert1.pem")
        self.assertTrue(S_ISREG(s.st_mode))
        self.assertEqual(S_IMODE(s.st_mode), 0o644)

        s = lstat(f"{archive}/test1.kanga.org/chain1.pem")
        self.assertTrue(S_ISREG(s.st_mode))
        self.assertEqual(S_IMODE(s.st_mode), 0o644)

        s = lstat(f"{archive}/test1.kanga.org/fullchain1.pem")
        self.assertTrue(S_ISREG(s.st_mode))
        self.assertEqual(S_IMODE(s.st_mode), 0o644)

        s = lstat(f"{archive}/test1.kanga.org/privkey1.pem")
        self.assertTrue(S_ISREG(s.st_mode))
        self.assertEqual(S_IMODE(s.st_mode), 0o600)


def uid_to_username(uid: int) -> str:
    try:
        return getpwuid(uid).pw_name
    except KeyError:
        return str(uid)

def gid_to_groupname(gid: int) -> str:
    try:
        return getgrgid(gid).gr_name
    except KeyError:
        return str(gid)