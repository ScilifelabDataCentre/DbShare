"Run all tests."

import unittest

import dbshare.test.base
from dbshare.test.root import Root
from dbshare.test.user import User
from dbshare.test.dbs import Dbs
from dbshare.test.db import Db
from dbshare.test.table import Table
from dbshare.test.query import Query
from dbshare.test.view import View


if __name__ == '__main__':
    dbshare.test.base.read_config()
    unittest.main()
